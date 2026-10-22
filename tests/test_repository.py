"""Repository hygiene: frozen source data, no machine paths, a complete step table."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys

from conftest import ROOT


def test_source_data_checksums():
    manifest = (ROOT / "02_data/SOURCE_DATA_SHA256SUMS.txt").read_text().splitlines()
    assert len(manifest) == 15
    for line in manifest:
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name


def test_no_script_points_at_a_local_drive():
    pattern = re.compile(r"[A-Z]:\\\\|Downloads\\\\DemandIQ")
    offenders = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.py")
                 if ".venv" not in p.parts and pattern.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


def load_runner():
    spec = importlib.util.spec_from_file_location("run_pipeline", ROOT / "04_scripts/run_pipeline.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def test_step_table_points_at_real_scripts_and_outputs():
    runner = load_runner()
    for step in runner.STEPS:
        if step.script:
            assert (ROOT / step.script).exists(), step.key
        if step.kind == "exact":
            assert runner.output_files(step), f"{step.key} has no committed outputs"
    blocked = {s.key for s in runner.STEPS if s.kind == "blocked"}
    assert blocked == {"step3", "step4a", "step4b_1", "step4c_1", "step4c_3"}
