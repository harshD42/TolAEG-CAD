# Literature Corpus

111 papers, every arXiv ID resolved and every PDF verified to match its claimed title.

PDFs are gitignored (~1 GB). Reproduce exactly with:

    bash scripts/fetch_literature.sh
    python scripts/verify_literature.py

## Papers that most shape the design

| ID | Why it matters |
|---|---|
| `2607.05123` | **ASSEMCAD** App. H.5 already states the CD surface-area bias. Partial scoop; must cite early. |
| `2605.28579` | **MUSE** benchmarks assemblability — but with a VLM rubric, not tolerances. Our nearest competitor. |
| `2605.07807` | **CADTestBench** — deterministic executable checks; geometry/topology only. |
| `2302.02913` | **Beyond Statistical Similarity** — canonical "similarity is the wrong target" position paper. |
| `1509.08763` | **Polytope tolerance analysis** (politopix) — the one real GD&T-aware assemblability tool. |
| `2601.06334` | **KAN tolerance-aware DFM** — the only ML work treating tolerances as first-class. |
| `2605.10873` | **CADBench** — documents that CD protocols are inconsistent across the field. |
| `1905.03678` | **Tatarchenko et al.** — the precedent that standard 3D metrics measure the wrong thing. |


## CAD generation: B-rep and parametric  (4)

- `2110.10863` deep-generative-engineering-design-review
- `2401.15563` brepgen
- `2503.13110` dtgbrepgen
- `2504.14257` hola-brep

## CAD generation: LLM / program synthesis  (17)

- `2411.04954` cad-mllm
- `2412.14042` cad-recode
- `2505.06507` text-to-cadquery
- `2505.14646` cad-coder-mit
- `2505.19713` cad-coder-beihang
- `2505.22914` cadrille
- `2508.10201` brepler
- `2512.06328` recad
- `2601.09428` draw-it-like-euclid
- `2602.03045` clarify-before-you-draw
- `2603.04337` pointer-cad
- `2603.05607` dreamcad
- `2603.11831` llm-brep-grounding
- `2604.10992` articad
- `2604.24479` zero-to-cad
- `2606.31252` embodied-cad
- `2607.05123` assemcad

## Foundational datasets / surveys  (3)

- `2105.09492` deepcad
- `2409.17106` text2cad
- `2505.08137` llm4cad-survey

## CAD benchmarks  (5)

- `2602.19171` histcad
- `2605.10865` benchcad
- `2605.10873` cadbench
- `2605.18430` text2cad-bench
- `2606.11152` p3d-bench

## CAD feedback loops / self-correction  (5)

- `2505.17702` seek-cad
- `2505.22304` cadreview
- `2506.00568` creft-cad
- `2512.23333` cme-cad
- `2605.17448` self-improving-cad-fea

## VLM spatial reasoning  (15)

- `2503.19707` mind-the-gap-spatial
- `2504.20648` spare
- `2506.21458` mindcube
- `2507.07610` spatialviz-bench
- `2507.11932` hyperphantasia
- `2510.08531` spatialladder
- `2510.16688` minimal-sufficiency-spatial
- `2511.22659` geometrically-constrained-agent
- `2512.08860` tri-bench
- `2601.07695` smooth-operator-rlvr-spatial
- `2602.07082` mosaicthinker
- `2602.19357` mentalblackboard
- `2603.07751` 3viewsense
- `2604.17385` spatialimaginer
- `2607.02853` prior-bias-uml

## Engineering drawings / document intelligence  (4)

- `2411.03707` florence2-engineering-drawing-gdt
- `2501.12751` patent-figure-classification
- `2601.04819` aecv-bench
- `2606.03410` enginuity

## DFM / tolerance / manufacturability  (3)

- `2601.06334` kan-tolerance-aware-dfm
- `2603.13102` bendfm-sheet-metal
- `2607.21850` scale-drv-fixing

## Super-resolution / spectral bias  (11)

- `2203.15402` pinn-experimental-fluid
- `2408.13716` freqinr
- `2412.09116` pde-loss-partial-observation
- `2502.00472` binned-spectral-power-loss
- `2503.04665` inr-video-image-sr
- `2505.15222` continuous-representation-overview
- `2506.07813` self-cascaded-diffusion-assr
- `2509.24868` drift-net
- `2512.04699` omniscalesr
- `2601.20878` log-focal-frequency-loss
- `2602.04695` turbulence-teaches-equivariance

## Test-time compute / verifiers  (10)

- `2504.00406` verifiagent
- `2504.04718` t1-tool-integrated-verification
- `2504.14047` think-deep-think-fast
- `2505.14479` neurosymbolic-euclidean-geometry
- `2506.16043` dynscaling
- `2508.00013` program-synthesis-paradigms
- `2509.22101` think-right-not-more
- `2603.22492` tiny-inference-latent-verifiers
- `2603.25681` self-improvement-llm-overview
- `2604.00510` adaptive-parallel-mcts

## Synthetic / procedural data  (34)

- `1509.08763` tolerance-analysis-polytopes
- `1904.06559` physics-informed-tolerance-allocation
- `2010.02392` fusion360-gallery
- `2105.12238` automate
- `2111.12772` joinable
- `2302.02913` beyond-statistical-similarity
- `2402.17695` geometric-dl-cad-survey
- `2406.11824` infinigen-indoors
- `2412.13810` cad-assistant
- `2503.05887` matchmaker
- `2504.02812` bop-challenge-2024
- `2506.17374` drawings-to-decisions
- `2507.09792` cadmium
- `2507.15365` david-synthetic
- `2508.00830` bike-bench
- `2511.05308` rethinking-pointcloud-metrics
- `2511.06194` nurbgen
- `2511.22171` brepgpt
- `2512.03018` autobrep
- `2601.12641` step-llm
- `2602.18296` context-aware-gdt-mapping
- `2603.09925` cd-structural-failure-optimization
- `2604.04925` simpleproc
- `2605.01171` cadfit
- `2605.01925` cadfs
- `2605.07807` cadtestbench
- `2605.28579` muse-assemblable-benchmark
- `2606.05058` unicad
- `2606.17696` fllumaone
- `2606.31579` dualbrep
- `2607.01205` linkify
- `2607.08891` ortho2cad
- `2607.11339` hiercad
- `2607.21928` tg-diff
