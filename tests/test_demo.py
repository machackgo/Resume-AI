import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_runs_end_to_end(tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / "examples" / "run_demo.py"), "--out", str(tmp_path / "out")],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "attempt 1: INVALID" in r.stdout and "attempt 2: OK" in r.stdout
    assert "refused by trigger" in r.stdout
    assert (tmp_path / "out" / "packages" / "FT001" / "Alex_Rivera_Globex_AppliedAIEngineer_Resume.docx").exists()
