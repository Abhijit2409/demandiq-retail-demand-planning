#!/usr/bin/env python3
"""
DemandIQ Step 2 — Historical Weather Pull
Primary source: Open-Meteo Historical Weather API
Model: ERA5 (consistent historical reanalysis)
Window: 2021-07-01 through 2026-06-30

Outputs:
  data/weather_daily.csv
  data/weather_weekly.csv

No API key required for non-commercial/open usage under provider terms.
"""

from __future__ import annotations
import csv
import json
import math
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGION_FILE = ROOT / "demandiq_weather_regions.csv"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

START_DATE = "2021-07-01"
END_DATE = "2026-06-30"
MODEL = "era5"
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARS = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
]

# Transparent feature thresholds. These are project assumptions, not public facts.
RAIN_DAY_MM = 1.0
SNOW_DAY_CM = 1.0
COLD_DAY_MEAN_C = 5.0
HIGH_WIND_KMH = 40.0

def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())

def get_json(url: str, retries: int = 4) -> dict:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DemandIQ-Portfolio/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.load(resp)
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Request failed after {retries} attempts: {last}")

def build_url(row: dict) -> str:
    params = {
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": ",".join(DAILY_VARS),
        "timezone": row["timezone"],
        "models": MODEL,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)

def safe_float(v):
    if v is None or v == "":
        return None
    return float(v)

def load_regions():
    with REGION_FILE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

def pull_daily():
    daily_rows = []
    for r in load_regions():
        url = build_url(r)
        print(f"Pulling {r['region_id']} — {r['proxy_city']}")
        payload = get_json(url)
        d = payload["daily"]
        n = len(d["time"])
        for i in range(n):
            row = {
                "date": d["time"][i],
                "region_id": r["region_id"],
                "proxy_city": r["proxy_city"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "timezone": r["timezone"],
                "source": "Open-Meteo Historical Weather API",
                "model": MODEL.upper(),
            }
            for var in DAILY_VARS:
                row[var] = d[var][i]
            daily_rows.append(row)
    return daily_rows

def write_daily(rows):
    path = DATA_DIR / "weather_daily.csv"
    fields = [
        "date","region_id","proxy_city","latitude","longitude","timezone","source","model",
        *DAILY_VARS
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path

def aggregate_weekly(daily_rows):
    buckets = defaultdict(list)
    for r in daily_rows:
        d = date.fromisoformat(r["date"])
        wk = monday_of(d).isoformat()
        buckets[(wk, r["region_id"])].append(r)

    weekly = []
    for (wk, region_id), rows in sorted(buckets.items()):
        def vals(col):
            return [safe_float(x[col]) for x in rows if safe_float(x[col]) is not None]

        tmean = vals("temperature_2m_mean")
        tmax = vals("temperature_2m_max")
        tmin = vals("temperature_2m_min")
        rain = vals("rain_sum")
        snow = vals("snowfall_sum")
        precip = vals("precipitation_sum")
        phours = vals("precipitation_hours")
        wmax = vals("wind_speed_10m_max")
        gust = vals("wind_gusts_10m_max")

        rain_days = sum(1 for x in rain if x >= RAIN_DAY_MM)
        snow_days = sum(1 for x in snow if x >= SNOW_DAY_CM)
        cold_days = sum(1 for x in tmean if x <= COLD_DAY_MEAN_C)
        high_wind_days = sum(1 for x in wmax if x >= HIGH_WIND_KMH)

        # Day-level wet+cold interaction
        wet_cold_days = 0
        for x in rows:
            tm = safe_float(x["temperature_2m_mean"])
            rn = safe_float(x["rain_sum"])
            if tm is not None and rn is not None and tm <= COLD_DAY_MEAN_C and rn >= RAIN_DAY_MM:
                wet_cold_days += 1

        first = rows[0]
        weekly.append({
            "week_start": wk,
            "region_id": region_id,
            "proxy_city": first["proxy_city"],
            "avg_temp_c": round(sum(tmean)/len(tmean), 3) if tmean else None,
            "min_temp_c": round(min(tmin), 3) if tmin else None,
            "max_temp_c": round(max(tmax), 3) if tmax else None,
            "rain_mm": round(sum(rain), 3) if rain else None,
            "rain_days": rain_days,
            "snow_cm": round(sum(snow), 3) if snow else None,
            "snow_days": snow_days,
            "precipitation_mm": round(sum(precip), 3) if precip else None,
            "precipitation_hours": round(sum(phours), 3) if phours else None,
            "max_wind_kmh": round(max(wmax), 3) if wmax else None,
            "max_gust_kmh": round(max(gust), 3) if gust else None,
            "high_wind_days": high_wind_days,
            "cold_days_lt5c": cold_days,
            "wet_cold_days": wet_cold_days,
            "days_in_week": len(rows),
            "source": "Open-Meteo Historical Weather API",
            "model": MODEL.upper(),
        })
    return weekly

def write_weekly(rows):
    path = DATA_DIR / "weather_weekly.csv"
    fields = [
        "week_start","region_id","proxy_city",
        "avg_temp_c","min_temp_c","max_temp_c",
        "rain_mm","rain_days","snow_cm","snow_days",
        "precipitation_mm","precipitation_hours",
        "max_wind_kmh","max_gust_kmh","high_wind_days",
        "cold_days_lt5c","wet_cold_days","days_in_week",
        "source","model"
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path

if __name__ == "__main__":
    daily = pull_daily()
    dpath = write_daily(daily)
    weekly = aggregate_weekly(daily)
    wpath = write_weekly(weekly)
    print(f"Done. Daily rows: {len(daily):,} -> {dpath}")
    print(f"Done. Weekly rows: {len(weekly):,} -> {wpath}")
