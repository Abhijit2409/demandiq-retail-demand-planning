#!/usr/bin/env python3

"""
DemandIQ Step 2 — Historical Weather Pull
Primary source: Open-Meteo Historical Weather API
Model: ERA5 historical reanalysis

Window:
    2021-07-01 through 2026-06-30

Governed DemandIQ regions:
    9 regions

Outputs:
    data/weather_daily.csv
    data/weather_weekly.csv

Important:
    - Existing region cache files are reused.
    - Only missing regions, such as US_MIDWEST / Chicago,
      should require a new API request.
    - weather_weekly.csv includes partial boundary weeks.
      The downstream weather-feature script trims the dataset
      to the governed 260 Monday weeks:
      2021-07-05 through 2026-06-22.
"""

from __future__ import annotations

import csv
import json
import random
import time
import urllib.parse
import urllib.request

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError


# ============================================================
# 1. PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# IMPORTANT FIX:
# Use the governed 9-region file including Chicago.
# ------------------------------------------------------------

REGION_FILE = (
    DATA_DIR
    / "demandiq_weather_regions_with_chicago.csv"
)


CACHE_DIR = ROOT / "cache"

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. GOVERNED WEATHER WINDOW
# ============================================================

START_DATE = "2021-07-01"

END_DATE = "2026-06-30"

MODEL = "era5"


BASE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


# ============================================================
# 3. EXPECTED PROJECT STRUCTURE
# ============================================================

EXPECTED_REGIONS = 9

EXPECTED_DAILY_ROWS_PER_REGION = 1826

EXPECTED_DAILY_ROWS = (
    EXPECTED_REGIONS
    * EXPECTED_DAILY_ROWS_PER_REGION
)

# The raw weekly aggregation includes:
#
#   2021-06-28 partial week
#   ...
#   2026-06-29 partial week
#
# Therefore raw weather_weekly contains 262 weeks per region.
# The feature pipeline later trims this to 260 governed weeks.

EXPECTED_RAW_WEEKLY_WEEKS_PER_REGION = 262

EXPECTED_RAW_WEEKLY_ROWS = (
    EXPECTED_REGIONS
    * EXPECTED_RAW_WEEKLY_WEEKS_PER_REGION
)


EXPECTED_REGION_SET = {

    "CA_PNW",
    "CA_PRAIRIE",
    "CA_ON",
    "CA_QC",

    "US_PNW",
    "US_NE",
    "US_MIDWEST",
    "US_MTN",
    "US_WEST"

}


# ============================================================
# 4. RATE-LIMIT / RESILIENCE SETTINGS
# ============================================================

REQUEST_DELAY_SECONDS = 8

MAX_RETRIES = 8

BACKOFF_BASE_SECONDS = 10

BACKOFF_MAX_SECONDS = 180


# ============================================================
# 5. DAILY VARIABLES
# ============================================================

DAILY_VARS = [

    "temperature_2m_mean",

    "temperature_2m_max",

    "temperature_2m_min",

    "precipitation_sum",

    "rain_sum",

    "snowfall_sum",

    "precipitation_hours",

    "wind_speed_10m_max",

    "wind_gusts_10m_max"

]


# ============================================================
# 6. TRANSPARENT PROJECT THRESHOLDS
#
# These are DemandIQ modelling assumptions,
# not claims about Arc'teryx internal definitions.
# ============================================================

RAIN_DAY_MM = 1.0

SNOW_DAY_CM = 1.0

COLD_DAY_MEAN_C = 5.0

HIGH_WIND_KMH = 40.0


# ============================================================
# 7. HELPERS
# ============================================================

def monday_of(
    d: date
) -> date:

    return (
        d
        - timedelta(
            days=d.weekday()
        )
    )


def safe_float(
    value
):

    if (
        value is None
        or
        value == ""
    ):

        return None

    return float(
        value
    )


# ============================================================
# 8. HTTP REQUEST WITH RETRIES
# ============================================================

def get_json(
    url: str,
    retries: int = MAX_RETRIES
) -> dict:

    """
    Fetch Open-Meteo JSON with retry logic.

    Handles:
        - HTTP 429
        - temporary 5xx errors
        - network / timeout errors
    """

    last_error = None


    for attempt in range(
        retries
    ):

        try:

            request = urllib.request.Request(

                url,

                headers={
                    "User-Agent":
                        "DemandIQ-Portfolio/1.0",

                    "Accept":
                        "application/json"
                }

            )


            with urllib.request.urlopen(

                request,

                timeout=120

            ) as response:

                return json.load(
                    response
                )


        except HTTPError as error:

            last_error = error


            # ----------------------------------------------
            # Rate-limit handling
            # ----------------------------------------------

            if error.code == 429:

                retry_after = (
                    error.headers.get(
                        "Retry-After"
                    )
                )


                if retry_after:

                    try:

                        wait = float(
                            retry_after
                        )

                    except ValueError:

                        wait = None

                else:

                    wait = None


                if wait is None:

                    wait = min(

                        BACKOFF_MAX_SECONDS,

                        (
                            BACKOFF_BASE_SECONDS
                            * (2 ** attempt)
                        )

                        + random.uniform(
                            0,
                            5
                        )

                    )


                print(

                    f"  HTTP 429 rate limit. "
                    f"Waiting {wait:.1f}s "
                    f"(attempt "
                    f"{attempt + 1}/{retries})..."

                )


                time.sleep(
                    wait
                )

                continue


            # ----------------------------------------------
            # Temporary server errors
            # ----------------------------------------------

            if (
                500
                <= error.code
                < 600
            ):

                wait = min(

                    BACKOFF_MAX_SECONDS,

                    (
                        BACKOFF_BASE_SECONDS
                        * (2 ** attempt)
                    )

                    + random.uniform(
                        0,
                        5
                    )

                )


                print(

                    f"  HTTP {error.code}. "
                    f"Waiting {wait:.1f}s "
                    f"(attempt "
                    f"{attempt + 1}/{retries})..."

                )


                time.sleep(
                    wait
                )

                continue


            raise


        except (
            URLError,
            TimeoutError,
            ConnectionError
        ) as error:

            last_error = error


            wait = min(

                BACKOFF_MAX_SECONDS,

                (
                    BACKOFF_BASE_SECONDS
                    * (2 ** attempt)
                )

                + random.uniform(
                    0,
                    5
                )

            )


            print(

                f"  Network error: {error}. "
                f"Waiting {wait:.1f}s "
                f"(attempt "
                f"{attempt + 1}/{retries})..."

            )


            time.sleep(
                wait
            )


    raise RuntimeError(

        "Request failed after "
        f"{retries} attempts: "
        f"{last_error}"

    )


# ============================================================
# 9. BUILD OPEN-METEO URL
# ============================================================

def build_url(
    row: dict
) -> str:

    params = {

        "latitude":
            row["latitude"],

        "longitude":
            row["longitude"],

        "start_date":
            START_DATE,

        "end_date":
            END_DATE,

        "daily":
            ",".join(
                DAILY_VARS
            ),

        "timezone":
            row["timezone"],

        "models":
            MODEL,

        "temperature_unit":
            "celsius",

        "wind_speed_unit":
            "kmh",

        "precipitation_unit":
            "mm"

    }


    return (

        BASE_URL

        + "?"

        + urllib.parse.urlencode(
            params
        )

    )


# ============================================================
# 10. LOAD AND VALIDATE REGION CONFIG
# ============================================================

def load_regions():

    if not REGION_FILE.exists():

        raise FileNotFoundError(

            "\n9-region configuration file "
            "was not found:\n"
            f"{REGION_FILE}"

        )


    with REGION_FILE.open(
        encoding="utf-8-sig"
    ) as file:

        regions = list(
            csv.DictReader(
                file
            )
        )


    region_ids = {

        row[
            "region_id"
        ]

        for row in regions

    }


    print("\n" + "=" * 78)

    print(
        "REGION CONFIG QA"
    )

    print("=" * 78)


    print(
        "Region file:",
        REGION_FILE
    )


    print(
        "Rows:",
        len(
            regions
        )
    )


    print(
        "Regions:"
    )


    for row in regions:

        print(

            " -",
            row[
                "region_id"
            ],

            "→",

            row[
                "proxy_city"
            ]

        )


    region_count_pass = (

        len(
            regions
        )

        ==

        EXPECTED_REGIONS

    )


    region_set_pass = (

        region_ids

        ==

        EXPECTED_REGION_SET

    )


    duplicate_region_pass = (

        len(
            region_ids
        )

        ==

        len(
            regions
        )

    )


    print(
        "\nExactly 9 regions:",
        "PASS"
        if region_count_pass
        else "FAIL"
    )


    print(
        "Exact governed region set:",
        "PASS"
        if region_set_pass
        else "FAIL"
    )


    print(
        "No duplicate region IDs:",
        "PASS"
        if duplicate_region_pass
        else "FAIL"
    )


    if not all(
        [
            region_count_pass,
            region_set_pass,
            duplicate_region_pass
        ]
    ):

        missing = sorted(

            EXPECTED_REGION_SET
            - region_ids

        )


        extra = sorted(

            region_ids
            - EXPECTED_REGION_SET

        )


        print(
            "Missing:",
            missing
        )


        print(
            "Extra:",
            extra
        )


        raise ValueError(

            "Region configuration QA failed."

        )


    return regions


# ============================================================
# 11. DAILY WEATHER PULL
# ============================================================

def pull_daily():

    """
    Pull each governed region one at a time.

    Existing cached JSON is reused.

    Because the first 8 regions are already cached,
    the expected new network request should be:

        US_MIDWEST → Chicago, IL
    """

    daily_rows = []


    regions = (
        load_regions()
    )


    print("\n" + "=" * 78)

    print(
        "HISTORICAL WEATHER PULL"
    )

    print("=" * 78)


    for index, region in enumerate(

        regions,

        start=1

    ):


        cache_file = (

            CACHE_DIR

            / (

                f"{region['region_id']}_"
                f"{START_DATE}_"
                f"{END_DATE}_"
                f"{MODEL}.json"

            )

        )


        print(

            f"\n[{index}/{len(regions)}] "
            f"{region['region_id']} — "
            f"{region['proxy_city']}"

        )


        if cache_file.exists():


            print(
                "  Using cached response."
            )


            payload = json.loads(

                cache_file.read_text(
                    encoding="utf-8"
                )

            )


        else:


            print(
                "  Cache not found."
            )


            print(
                "  Downloading from "
                "Open-Meteo..."
            )


            url = build_url(
                region
            )


            payload = get_json(
                url
            )


            cache_file.write_text(

                json.dumps(
                    payload
                ),

                encoding="utf-8"

            )


            print(
                "  Downloaded and cached."
            )


            if index < len(
                regions
            ):

                wait = (

                    REQUEST_DELAY_SECONDS

                    + random.uniform(
                        0,
                        3
                    )

                )


                print(

                    f"  Pausing "
                    f"{wait:.1f}s "
                    "before next region..."

                )


                time.sleep(
                    wait
                )


        # ----------------------------------------------------
        # API payload validation
        # ----------------------------------------------------

        if "daily" not in payload:

            raise RuntimeError(

                "No daily data returned for "
                f"{region['region_id']}:\n"
                f"{payload}"

            )


        daily = (
            payload[
                "daily"
            ]
        )


        number_of_days = len(

            daily[
                "time"
            ]

        )


        if (
            number_of_days
            !=
            EXPECTED_DAILY_ROWS_PER_REGION
        ):

            print(

                "  WARNING: "
                f"Expected "
                f"{EXPECTED_DAILY_ROWS_PER_REGION} "
                "daily observations, got "
                f"{number_of_days}."

            )


        for i in range(
            number_of_days
        ):


            row = {

                "date":
                    daily[
                        "time"
                    ][i],

                "region_id":
                    region[
                        "region_id"
                    ],

                "proxy_city":
                    region[
                        "proxy_city"
                    ],

                "latitude":
                    region[
                        "latitude"
                    ],

                "longitude":
                    region[
                        "longitude"
                    ],

                "timezone":
                    region[
                        "timezone"
                    ],

                "source":
                    (
                        "Open-Meteo Historical "
                        "Weather API"
                    ),

                "model":
                    MODEL.upper()

            }


            for variable in DAILY_VARS:

                row[
                    variable
                ] = (
                    daily[
                        variable
                    ][i]
                )


            daily_rows.append(
                row
            )


    return daily_rows


# ============================================================
# 12. WRITE DAILY DATA
# ============================================================

def write_daily(
    rows
):

    path = (
        DATA_DIR
        / "weather_daily.csv"
    )


    fields = [

        "date",

        "region_id",

        "proxy_city",

        "latitude",

        "longitude",

        "timezone",

        "source",

        "model",

        *DAILY_VARS

    ]


    with path.open(

        "w",

        newline="",

        encoding="utf-8"

    ) as file:


        writer = csv.DictWriter(

            file,

            fieldnames=fields

        )


        writer.writeheader()


        writer.writerows(
            rows
        )


    return path


# ============================================================
# 13. AGGREGATE DAILY → WEEKLY
# ============================================================

def aggregate_weekly(
    daily_rows
):

    buckets = defaultdict(
        list
    )


    for row in daily_rows:


        current_date = (
            date.fromisoformat(
                row[
                    "date"
                ]
            )
        )


        week_start = (
            monday_of(
                current_date
            )
            .isoformat()
        )


        buckets[

            (
                week_start,
                row[
                    "region_id"
                ]
            )

        ].append(
            row
        )


    weekly_rows = []


    for (
        week_start,
        region_id
    ), rows in sorted(
        buckets.items()
    ):


        def values(
            column
        ):

            return [

                safe_float(
                    item[
                        column
                    ]
                )

                for item in rows

                if safe_float(
                    item[
                        column
                    ]
                )
                is not None

            ]


        tmean = values(
            "temperature_2m_mean"
        )


        tmax = values(
            "temperature_2m_max"
        )


        tmin = values(
            "temperature_2m_min"
        )


        rain = values(
            "rain_sum"
        )


        snow = values(
            "snowfall_sum"
        )


        precipitation = values(
            "precipitation_sum"
        )


        precipitation_hours = values(
            "precipitation_hours"
        )


        maximum_wind = values(
            "wind_speed_10m_max"
        )


        maximum_gust = values(
            "wind_gusts_10m_max"
        )


        # ----------------------------------------------------
        # Weekly event counts
        # ----------------------------------------------------

        rain_days = sum(

            1

            for value in rain

            if value >= RAIN_DAY_MM

        )


        snow_days = sum(

            1

            for value in snow

            if value >= SNOW_DAY_CM

        )


        cold_days = sum(

            1

            for value in tmean

            if value <= COLD_DAY_MEAN_C

        )


        high_wind_days = sum(

            1

            for value in maximum_wind

            if value >= HIGH_WIND_KMH

        )


        # ----------------------------------------------------
        # Daily wet + cold interaction
        # ----------------------------------------------------

        wet_cold_days = 0


        for item in rows:


            temperature = safe_float(

                item[
                    "temperature_2m_mean"
                ]

            )


            daily_rain = safe_float(

                item[
                    "rain_sum"
                ]

            )


            if (

                temperature
                is not None

                and

                daily_rain
                is not None

                and

                temperature
                <=
                COLD_DAY_MEAN_C

                and

                daily_rain
                >=
                RAIN_DAY_MM

            ):

                wet_cold_days += 1


        first = rows[0]


        weekly_rows.append(

            {

                "week_start":
                    week_start,

                "region_id":
                    region_id,

                "proxy_city":
                    first[
                        "proxy_city"
                    ],

                "avg_temp_c":
                    round(
                        sum(tmean)
                        / len(tmean),
                        3
                    )
                    if tmean
                    else None,

                "min_temp_c":
                    round(
                        min(tmin),
                        3
                    )
                    if tmin
                    else None,

                "max_temp_c":
                    round(
                        max(tmax),
                        3
                    )
                    if tmax
                    else None,

                "rain_mm":
                    round(
                        sum(rain),
                        3
                    )
                    if rain
                    else None,

                "rain_days":
                    rain_days,

                "snow_cm":
                    round(
                        sum(snow),
                        3
                    )
                    if snow
                    else None,

                "snow_days":
                    snow_days,

                "precipitation_mm":
                    round(
                        sum(
                            precipitation
                        ),
                        3
                    )
                    if precipitation
                    else None,

                "precipitation_hours":
                    round(
                        sum(
                            precipitation_hours
                        ),
                        3
                    )
                    if precipitation_hours
                    else None,

                "max_wind_kmh":
                    round(
                        max(
                            maximum_wind
                        ),
                        3
                    )
                    if maximum_wind
                    else None,

                "max_gust_kmh":
                    round(
                        max(
                            maximum_gust
                        ),
                        3
                    )
                    if maximum_gust
                    else None,

                "high_wind_days":
                    high_wind_days,

                "cold_days_lt5c":
                    cold_days,

                "wet_cold_days":
                    wet_cold_days,

                "days_in_week":
                    len(
                        rows
                    ),

                "source":
                    (
                        "Open-Meteo Historical "
                        "Weather API"
                    ),

                "model":
                    MODEL.upper()

            }

        )


    return weekly_rows


# ============================================================
# 14. WRITE WEEKLY DATA
# ============================================================

def write_weekly(
    rows
):

    path = (
        DATA_DIR
        / "weather_weekly.csv"
    )


    fields = [

        "week_start",

        "region_id",

        "proxy_city",

        "avg_temp_c",

        "min_temp_c",

        "max_temp_c",

        "rain_mm",

        "rain_days",

        "snow_cm",

        "snow_days",

        "precipitation_mm",

        "precipitation_hours",

        "max_wind_kmh",

        "max_gust_kmh",

        "high_wind_days",

        "cold_days_lt5c",

        "wet_cold_days",

        "days_in_week",

        "source",

        "model"

    ]


    with path.open(

        "w",

        newline="",

        encoding="utf-8"

    ) as file:


        writer = csv.DictWriter(

            file,

            fieldnames=fields

        )


        writer.writeheader()


        writer.writerows(
            rows
        )


    return path


# ============================================================
# 15. OUTPUT QA
# ============================================================

def run_output_qa(
    daily_rows,
    weekly_rows
):

    print("\n" + "=" * 78)

    print(
        "WEATHER OUTPUT QA"
    )

    print("=" * 78)


    daily_regions = {

        row[
            "region_id"
        ]

        for row in daily_rows

    }


    weekly_regions = {

        row[
            "region_id"
        ]

        for row in weekly_rows

    }


    daily_row_pass = (

        len(
            daily_rows
        )

        ==

        EXPECTED_DAILY_ROWS

    )


    weekly_row_pass = (

        len(
            weekly_rows
        )

        ==

        EXPECTED_RAW_WEEKLY_ROWS

    )


    daily_region_pass = (

        daily_regions
        ==
        EXPECTED_REGION_SET

    )


    weekly_region_pass = (

        weekly_regions
        ==
        EXPECTED_REGION_SET

    )


    weekly_unique_grain = (

        len(
            {
                (
                    row[
                        "week_start"
                    ],
                    row[
                        "region_id"
                    ]
                )

                for row in weekly_rows
            }
        )

        ==

        len(
            weekly_rows
        )

    )


    checks = {

        f"Daily rows = "
        f"{EXPECTED_DAILY_ROWS:,}":
            daily_row_pass,

        f"Raw weekly rows = "
        f"{EXPECTED_RAW_WEEKLY_ROWS:,}":
            weekly_row_pass,

        "Daily contains exact 9 regions":
            daily_region_pass,

        "Weekly contains exact 9 regions":
            weekly_region_pass,

        "Weekly Region × Week grain unique":
            weekly_unique_grain

    }


    for name, passed in checks.items():

        print(

            f"{name}:",
            "PASS"
            if passed
            else "FAIL"

        )


    overall_pass = all(
        checks.values()
    )


    print("\n" + "-" * 78)


    print(

        "OVERALL WEATHER PULL STATUS:",

        "PASS"
        if overall_pass
        else "FAIL"

    )


    print("-" * 78)


    if not overall_pass:

        raise RuntimeError(

            "Weather pull completed, but "
            "output QA failed."

        )


# ============================================================
# 16. MAIN
# ============================================================

if __name__ == "__main__":


    print("\n" + "=" * 78)

    print(
        "DEMANDIQ WEATHER PULL — "
        "9-REGION GOVERNED VERSION"
    )

    print("=" * 78)


    print(
        "Region config:",
        REGION_FILE
    )


    print(
        "Cache directory:",
        CACHE_DIR
    )


    print(
        "Output directory:",
        DATA_DIR
    )


    # --------------------------------------------------------
    # Pull / reuse cached daily data
    # --------------------------------------------------------

    daily_rows = (
        pull_daily()
    )


    daily_path = (
        write_daily(
            daily_rows
        )
    )


    # --------------------------------------------------------
    # Aggregate daily → raw weekly
    # --------------------------------------------------------

    weekly_rows = (

        aggregate_weekly(
            daily_rows
        )

    )


    weekly_path = (

        write_weekly(
            weekly_rows
        )

    )


    # --------------------------------------------------------
    # QA
    # --------------------------------------------------------

    run_output_qa(

        daily_rows,

        weekly_rows

    )


    print("\n" + "=" * 78)

    print(
        "FILES WRITTEN"
    )

    print("=" * 78)


    print(

        f"Daily rows: "
        f"{len(daily_rows):,}"
    )


    print(
        daily_path
    )


    print(

        f"\nRaw weekly rows: "
        f"{len(weekly_rows):,}"
    )


    print(
        weekly_path
    )


    print(

        "\nNext: run "
        "weather_features_weekly.py "
        "to create the governed "
        "260-week feature table."

    )