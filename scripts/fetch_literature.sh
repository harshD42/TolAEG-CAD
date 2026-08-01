#!/usr/bin/env bash
# Fetch the literature corpus from arXiv into papers/literature/.
# Verifies each download is a real PDF; logs anything that fails to resolve.
#
# Usage: bash scripts/fetch_literature.sh
#
# IDs are grouped by topic. A failure here is informative: it means the citation
# could not be verified and must not enter the paper.

set -u

OUT="papers/literature"
LOG="papers/literature/_fetch_log.txt"
mkdir -p "$OUT"
: > "$LOG"

# id|slug
PAPERS=(
# --- CAD generation: B-rep and parametric ---
"2401.15563|brepgen"
"2504.14257|hola-brep"
"2503.13110|dtgbrepgen"
"2110.10863|deep-generative-engineering-design-review"

# --- CAD generation: LLM / program synthesis ---
# NOTE: two distinct papers are both titled "CAD-Coder". Do not conflate them.
#   2505.14646 = Doris et al. (MIT), open-source VLM, code+weights released.
#   2505.19713 = Guan et al. (Beihang), text-to-CAD with CoT + geometric reward.
"2505.14646|cad-coder-mit"
"2505.19713|cad-coder-beihang"
"2412.14042|cad-recode"
"2505.22914|cadrille"
"2505.06507|text-to-cadquery"
"2411.04954|cad-mllm"
"2512.06328|recad"
"2603.05607|dreamcad"
"2603.04337|pointer-cad"
"2601.09428|draw-it-like-euclid"
"2508.10201|brepler"
"2606.31252|embodied-cad"
"2604.24479|zero-to-cad"
"2603.11831|llm-brep-grounding"
"2604.10992|articad"
"2607.05123|assemcad"
"2602.03045|clarify-before-you-draw"

# --- Foundational datasets / surveys ---
"2105.09492|deepcad"
"2409.17106|text2cad"
"2505.08137|llm4cad-survey"

# --- CAD benchmarks ---
"2605.18430|text2cad-bench"
"2605.10873|cadbench"
"2605.10865|benchcad"
"2606.11152|p3d-bench"
"2602.19171|histcad"

# --- CAD feedback loops / self-correction ---
"2605.17448|self-improving-cad-fea"
"2505.22304|cadreview"
"2505.17702|seek-cad"
"2512.23333|cme-cad"
"2506.00568|creft-cad"

# --- VLM spatial reasoning ---
"2512.08860|tri-bench"
"2603.07751|3viewsense"
"2510.16688|minimal-sufficiency-spatial"
"2510.08531|spatialladder"
"2604.17385|spatialimaginer"
"2602.07082|mosaicthinker"
"2504.20648|spare"
"2507.07610|spatialviz-bench"
"2506.21458|mindcube"
"2602.19357|mentalblackboard"
"2507.11932|hyperphantasia"
"2511.22659|geometrically-constrained-agent"
"2503.19707|mind-the-gap-spatial"
"2601.07695|smooth-operator-rlvr-spatial"
"2607.02853|prior-bias-uml"

# --- Engineering drawings / document intelligence ---
"2601.04819|aecv-bench"
"2606.03410|enginuity"
"2501.12751|patent-figure-classification"
"2411.03707|florence2-engineering-drawing-gdt"

# --- DFM / tolerance / manufacturability ---
"2603.13102|bendfm-sheet-metal"
"2601.06334|kan-tolerance-aware-dfm"
"2607.21850|scale-drv-fixing"

# --- Super-resolution / spectral bias ---
"2502.00472|binned-spectral-power-loss"
"2601.20878|log-focal-frequency-loss"
"2408.13716|freqinr"
"2503.04665|inr-video-image-sr"
"2505.15222|continuous-representation-overview"
"2512.04699|omniscalesr"
"2506.07813|self-cascaded-diffusion-assr"
"2509.24868|drift-net"
"2412.09116|pde-loss-partial-observation"
"2602.04695|turbulence-teaches-equivariance"
"2203.15402|pinn-experimental-fluid"

# --- Test-time compute / verifiers ---
"2504.04718|t1-tool-integrated-verification"
"2603.22492|tiny-inference-latent-verifiers"
"2504.00406|verifiagent"
"2603.25681|self-improvement-llm-overview"
"2604.00510|adaptive-parallel-mcts"
"2509.22101|think-right-not-more"
"2506.16043|dynscaling"
"2504.14047|think-deep-think-fast"
"2505.14479|neurosymbolic-euclidean-geometry"
"2508.00013|program-synthesis-paradigms"

# --- Synthetic / procedural data ---
"2406.11824|infinigen-indoors"
"2604.04925|simpleproc"
"2507.15365|david-synthetic"
"2504.02812|bop-challenge-2024"
)

ok=0; fail=0
for entry in "${PAPERS[@]}"; do
  id="${entry%%|*}"
  slug="${entry##*|}"
  dest="$OUT/${id}_${slug}.pdf"

  if [ -s "$dest" ] && head -c 4 "$dest" | grep -q '%PDF'; then
    echo "CACHED  $id  $slug" | tee -a "$LOG"
    ok=$((ok+1))
    continue
  fi

  code=$(curl -sL -w '%{http_code}' -o "$dest" \
         -A 'tolcad-litreview/0.1 (academic use)' \
         --max-time 90 --retry 2 --retry-delay 2 \
         "https://arxiv.org/pdf/${id}")

  if [ "$code" = "200" ] && [ -s "$dest" ] && head -c 4 "$dest" | grep -q '%PDF'; then
    size=$(wc -c < "$dest")
    echo "OK      $id  $slug  (${size} bytes)" | tee -a "$LOG"
    ok=$((ok+1))
  else
    rm -f "$dest"
    echo "FAIL    $id  $slug  (http $code) -- CITATION UNVERIFIED" | tee -a "$LOG"
    fail=$((fail+1))
  fi
done

echo "" | tee -a "$LOG"
echo "downloaded=$ok  failed=$fail  total=${#PAPERS[@]}" | tee -a "$LOG"
