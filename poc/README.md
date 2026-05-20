# POC — Face swap model benchmark via FaceFusion CLI

> _Last reviewed: 2026-05-20_
> _Status: POC — not yet validated. Goal: pick the best commercial-friendly swap model before writing a custom node._

This folder benchmarks every face-swap model FaceFusion supports against a fixed source face + target scene, so we can compare quality side-by-side and pick a winner for [Phase 2 — custom node](../README.md#phase-2-plan-not-yet-started).

## Inputs (vendored — no external dependencies)

- `inputs/jarda_832x1216.png` — source face (recognizable real face for fidelity testing)
- `inputs/shattered-0-noswap.png` — target scene (the "shattered crystals" scene from the Designeo workflows repo, generated with no face swap applied, so the swap step is the only variable)

Both were copied from [`stable-diffusion-comfy-workflows/comfyui-workflows/`](https://git.designeo.cz/internal/stable-diffusion-comfy-workflows/) — regenerate the target via `face-preservation/face-swap/shattered-0-noswap.json` if needed.

## Models under test

Primary (the point of the POC):

| Model | Resolution | License | Notes |
|---|---|---|---|
| `ghost_1_256` | 256 | Apache 2.0 | Sber AI variant 1 |
| `ghost_2_256` | 256 | Apache 2.0 | Sber AI variant 2 |
| `ghost_3_256` | 256 | Apache 2.0 | Sber AI variant 3 |

Full sweep (run with `--extras`) — every other model FaceFusion supports natively:

| Model | Resolution | License | Why include |
|---|---|---|---|
| `inswapper_128_fp16` | 128 | InsightFace research (non-com) | Baseline — known-good quality reference |
| `hyperswap_1a/1b/1c_256` | 256 | OpenRAIL-AS (FaceFusion Labs) | Validate hyperswap actually works in FaceFusion (vs broken in ReActor) |
| `blendswap_256` | 256 | Verify per-release | Newer alternative worth a look |
| `uniface_256` | 256 | Verify per-release | Same |
| `simswap_256` | 256 | Research-only (ECCV 2020) | Quality reference even if non-commercial |
| `simswap_unofficial_512` | 512 | Unofficial community retrain | Higher-res SimSwap variant |
| `hififace_unofficial_256` | 256 | Unofficial community retrain | Different swap architecture |

With `--extras` we cover all 13 swap models FaceFusion ships — full landscape comparison in one run.

## Install FaceFusion (on the dev server with GPU)

Two paths. Pick one.

### Option A — Docker (recommended, isolated)

```bash
ssh bryanthings@10.0.4.94
docker pull facefusion/facefusion:latest
docker run --rm --gpus all \
  -v $(pwd):/work -w /work \
  facefusion/facefusion:latest \
  python facefusion.py --help
```

First swap run will download the requested swap model + restorer on demand.

### Option B — pip (needs Python 3.10+ and CUDA already configured)

```bash
ssh bryanthings@10.0.4.94
python3 -m venv ~/ai/facefusion-venv
source ~/ai/facefusion-venv/bin/activate
pip install facefusion onnxruntime-gpu
facefusion --help
```

## Running

```bash
# clone this repo on the dev server first:
git clone https://github.com/magiak/comfyui-faceswap.git
cd comfyui-faceswap/poc

# Default: GHOST 1/2/3 with GFPGAN restorer
python run-ghost-poc.py

# Single model
python run-ghost-poc.py ghost_2_256

# Skip face restoration (see raw swap quality)
python run-ghost-poc.py --restorer none

# Full sweep — all 13 FaceFusion swap models
python run-ghost-poc.py --extras
```

If you're using Docker, point the script at it:

```bash
python run-ghost-poc.py --facefusion-cmd "docker run --rm --gpus all -v $(pwd):/work -w /work facefusion/facefusion:latest python facefusion.py"
```

## Expected outputs

In `outputs/`:

- `ghost_poc_ghost_1_256_gfpgan_1_4.png`
- `ghost_poc_ghost_2_256_gfpgan_1_4.png`
- `ghost_poc_ghost_3_256_gfpgan_1_4.png`
- (plus extras / restorer variants depending on flags)

Outputs are gitignored. Sync interesting comparisons back to the workflows repo (`face-preservation/face-swap-facefusion/`) for archive / write-up if useful.

## What to look for in the comparison

| Criterion | What good looks like |
|---|---|
| **Identity fidelity** | Recognizably Jarda. Compared side-by-side with the inswapper+codeformer reference, it shouldn't lose detail (eye shape, jaw line, distinctive features). |
| **Seam blending** | No visible mask edge around the face. Skin tone matches the surrounding scene. |
| **Lighting match** | Highlights/shadows on the face direction-consistent with the scene. |
| **Resolution** | 256px buffer (vs inswapper 128) should mean visibly sharper face detail. |
| **Artifacts** | No double-eyebrows, ghosted features, color banding. |

## Next steps depending on result

- **GHOST 2/3 looks comparable or better than inswapper+codeformer:** implement Phase 2 — write a thin ComfyUI custom node that loads `ghost_2_256.onnx` directly (no FaceFusion runtime dependency). Drop in here as `nodes.py`.
- **GHOST quality is mediocre but hyperswap works:** prioritize hyperswap (`hyperswap_1a/1b/1c_256.onnx`) in the custom node instead. OpenRAIL-AS is fine for our consent-based use case.
- **Both look worse than inswapper:** pivot back to identity-guided (InstantID / PuLID) and accept the InsightFace detection gray area, or get an InsightFace commercial license.

## License notes on the swap models

- **GHOST** ([ai-forever/ghost](https://github.com/ai-forever/ghost)) — Apache 2.0. ✅ Verified from [LICENSE file](https://github.com/ai-forever/ghost/blob/main/LICENSE).
- **Hyperswap** (`facefusion/hyperswap`) — OpenRAIL-AS. ✅ Commercial OK with behavioral use restrictions you must propagate downstream.
- **InSwapper** — InsightFace research-only.
- **BlendSwap, UniFace, HifiFace, ReSwapper, SimSwap** — verify each release's license individually before production use. Included here only for quality comparison.
