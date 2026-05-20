# comfyui-faceswap

ComfyUI custom node for **commercial-friendly face swap**, plus a POC harness for benchmarking the underlying ONNX swap models.

> _Status: POC stage. No usable ComfyUI nodes exposed yet — that's the next milestone after we pick a swap model._

## Why this repo exists

The de-facto face swap node for ComfyUI ([Gourieff/ComfyUI-ReActor](https://github.com/Gourieff/ComfyUI-ReActor)) ships with `inswapper_128` (InsightFace, **non-commercial**) as its only practically-working model. Its OpenRAIL-AS hyperswap support is broken upstream and has been since 2026-04-23.

This repo's plan:

1. **Phase 1 — POC** (where we are now): use [FaceFusion CLI](https://docs.facefusion.io/) as a sidecar to benchmark every face-swap model FaceFusion supports (13 models) against our reference scene, so we can pick the best **Apache 2.0** (GHOST) or **OpenRAIL-AS** (hyperswap) candidate.
2. **Phase 2 — Custom node**: implement a thin ComfyUI node that loads the winning ONNX model directly via `onnxruntime` — no FaceFusion dependency, no ReActor brokenness.

The corresponding research lives in [`stable-diffusion-comfy-workflows/comfyui-workflows/face-preservation/`](https://git.designeo.cz/internal/stable-diffusion-comfy-workflows/) (Designeo internal) — see its `README.md` for the full model landscape and license analysis.

## Repo layout

```
comfyui-faceswap/
├── __init__.py             # placeholder so ComfyUI loads the folder without error
├── pyproject.toml          # python metadata, prepares for ComfyUI Registry (cnr) submission
├── requirements.txt        # runtime deps for the future custom node
└── poc/
    ├── README.md           # POC docs: install FaceFusion + run benchmark
    ├── run-ghost-poc.py    # benchmark script — wraps `facefusion headless-run`
    ├── inputs/             # vendored test images for self-contained runs
    └── outputs/            # gitignored
```

## Quick start (POC)

```bash
git clone https://github.com/magiak/comfyui-faceswap.git
cd comfyui-faceswap/poc
# Install FaceFusion separately (see poc/README.md), then:
python3 run-ghost-poc.py            # GHOST 1/2/3 with GFPGAN restorer
python3 run-ghost-poc.py --extras   # all 13 FaceFusion swap models
```

See [`poc/README.md`](poc/README.md) for full details.

## License

Apache 2.0 — matches the license of the GHOST swap models we're building around and keeps downstream commercial use unobstructed.

## Phase 2 plan (not yet started)

A ComfyUI node `FaceSwap` with inputs:

- `target_image` (IMAGE)
- `source_image` (IMAGE)
- `model` (combo: ghost_1_256 / ghost_2_256 / ghost_3_256 / hyperswap_1a_256 / …)
- `face_restore_model` (optional, combo)
- `source_face_index` / `target_face_index` (int)
- `face_detector` (combo: choose an Apache-licensed detector to avoid the InsightFace gray area)

Drops in as a sibling to ReActor's node, but with a commercial-clean default and no broken hyperswap.
