"""
GHOST face-swap POC via FaceFusion CLI.

Apache 2.0 alternative to the non-commercial inswapper that ReActor uses today.
Runs FaceFusion headless against the vendored shattered-0-noswap.png target +
jarda_832x1216.png source so outputs sit next to comparable inswapper results
generated separately in the workflows repo.

See README.md (parent + this folder) for install context.

Usage (use `python3` on Linux servers where `python` isn't symlinked):
  python3 run-ghost-poc.py                      # GHOST 1/2/3 with GFPGAN restorer
  python3 run-ghost-poc.py ghost_2_256          # single model
  python3 run-ghost-poc.py --restorer none      # skip face restoration
  python3 run-ghost-poc.py --extras             # full sweep — every other FaceFusion-supported model

Expects `facefusion` on PATH. If you're running from source, point at facefusion.py
AND pass --facefusion-dir so the subprocess runs from inside the FaceFusion repo
(otherwise processor plugins don't get discovered and you'll see
"invalid choice: 'face_swapper' (choose from )" errors):

  python3 run-ghost-poc.py --extras \
    --facefusion-cmd "python3 /home/USER/facefusion-src/facefusion.py" \
    --facefusion-dir /home/USER/facefusion-src
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"
SOURCE = INPUTS / "jarda_832x1216.png"
TARGET = INPUTS / "shattered-0-noswap.png"

# Apache 2.0 — the whole point of this POC
GHOST_MODELS = ["ghost_1_256", "ghost_2_256", "ghost_3_256"]

# Full sweep — every other model FaceFusion supports natively, for quality comparison.
# License grouping for context:
#   OpenRAIL-AS (commercial OK with use restrictions): hyperswap_*
#   InsightFace research (non-com): inswapper_128_fp16
#   Research / academic (non-com): simswap_256
#   Unofficial community retrains (verify per-release): simswap_unofficial_512, hififace_unofficial_256
#   Verify per-release: blendswap_256, uniface_256
EXTRA_MODELS = [
    "inswapper_128_fp16",       # non-com baseline reference
    "hyperswap_1a_256",         # OpenRAIL-AS (FaceFusion Labs)
    "hyperswap_1b_256",
    "hyperswap_1c_256",
    "blendswap_256",
    "uniface_256",
    "simswap_256",              # ECCV 2020 research
    "simswap_unofficial_512",   # community retrain
    "hififace_unofficial_256",  # community retrain
]

RESTORER_CHOICES = ["none", "gfpgan_1.4", "codeformer", "gpen_bfr_256", "gpen_bfr_512"]


def run_one(facefusion_cmd: str, facefusion_dir: str | None, execution_provider: str,
            model: str, restorer: str, out: Path) -> None:
    processors = ["face_swapper"]
    if restorer != "none":
        processors.append("face_enhancer")

    cmd = shlex.split(facefusion_cmd) + [
        "headless-run",
        "--source-paths", str(SOURCE),
        "--target-path", str(TARGET),
        "--output-path", str(out),
        "--processors", *processors,
        "--face-swapper-model", model,
        "--execution-providers", execution_provider,
    ]
    if restorer != "none":
        cmd.extend(["--face-enhancer-model", restorer])

    print(f"[{model}] running:", " ".join(shlex.quote(c) for c in cmd))
    t0 = time.time()
    subprocess.run(cmd, check=True, cwd=facefusion_dir)
    print(f"[{model}] -> {out.name}  ({time.time() - t0:.1f}s)")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("model", nargs="?", default=None,
                    help=f"Single swap model (default: run {', '.join(GHOST_MODELS)})")
    ap.add_argument("--restorer", default="gfpgan_1.4", choices=RESTORER_CHOICES,
                    help="Face enhancer model (default: gfpgan_1.4). 'none' skips restoration.")
    ap.add_argument("--extras", action="store_true",
                    help=f"Also run: {', '.join(EXTRA_MODELS)}")
    ap.add_argument("--facefusion-cmd", default="facefusion",
                    help="How to invoke FaceFusion. Default: 'facefusion'. Override for Docker / from-source install.")
    ap.add_argument("--facefusion-dir", default=None,
                    help="cwd for the FaceFusion subprocess. REQUIRED when running from source so processor plugins discover correctly.")
    ap.add_argument("--execution-provider", default="cuda",
                    choices=["cuda", "tensorrt", "cpu", "directml", "coreml"],
                    help="Execution provider for onnxruntime (default: cuda).")
    args = ap.parse_args()

    if not SOURCE.exists():
        sys.exit(f"source not found: {SOURCE}")
    if not TARGET.exists():
        sys.exit(f"target not found: {TARGET}")
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    if args.model:
        models = [args.model]
    else:
        models = list(GHOST_MODELS)
        if args.extras:
            models.extend(EXTRA_MODELS)

    restore_tag = "norestore" if args.restorer == "none" else args.restorer.replace(".", "_")

    failures = 0
    for m in models:
        out = OUTPUTS / f"ghost_poc_{m}_{restore_tag}.png"
        try:
            run_one(args.facefusion_cmd, args.facefusion_dir, args.execution_provider,
                    m, args.restorer, out)
        except subprocess.CalledProcessError as e:
            print(f"[{m}] FAILED with exit code {e.returncode}")
            failures += 1
        except FileNotFoundError:
            sys.exit(
                f"facefusion command not found: {args.facefusion_cmd!r}\n"
                f"Install FaceFusion or pass --facefusion-cmd. See README.md."
            )

    print(f"\nDone. Outputs in {OUTPUTS}  ({failures} failed)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
