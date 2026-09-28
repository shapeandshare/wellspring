"""Blue's audit (weight-diff MRI + probe sweep) over a handover directory only (R-6)."""

import subprocess
import sys
from pathlib import Path

FT_DIR = Path(__file__).resolve().parent


def run_audit(base: Path, handover_dir: Path, wordlist: Path | None, out_dir: Path) -> dict[str, str]:
    handover_dir, out_dir = Path(handover_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    variants = sorted(str(p) for p in handover_dir.iterdir() if (p / "config.json").is_file())
    subprocess.run([sys.executable, str(FT_DIR / "weight_diff.py"), "--base", str(base),
                    "--variants", *variants, "--out", str(out_dir / "mri")], check=True)
    blue_json = out_dir / "blue.json"
    cmd = [sys.executable, str(FT_DIR / "probe.py"), "sweep", "--models", str(handover_dir),
           "--json", str(blue_json)]
    if wordlist and Path(wordlist).is_file():
        cmd += ["--wordlist", str(wordlist)]
    subprocess.run(cmd, check=True)
    return {"mri_scores": str(out_dir / "mri" / "scores.json"), "blue_json": str(blue_json)}
