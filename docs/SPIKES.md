# tolcad — Spike Register

**What a spike is, in this project.** A spike is a question that can only be settled by *running
an experiment*. Not by reasoning, not by reading the code more carefully, and not by writing the
feature and seeing what happens. If a sufficiently careful reader could derive the answer from
what is already in the repo, it is a task and it belongs in a plan, not here.

**Why this file exists.** So that work can resume cold, on another machine, by someone who was not
in the room. Every entry carries the command to run, the observation to make, and what to do if
the answer is bad. Nothing here depends on a transcript.

**Provenance rule.** Canonical numbers live in
`docs/superpowers/specs/2026-08-01-ledger-reconciliation.md`, cited throughout as **[LR §n]**.
Everything under `.superpowers/sdd/` is a contemporaneous ledger containing many SUPERSEDED
figures — read it for narrative, never for numbers. Two companions:
`docs/superpowers/specs/2026-08-01-observation-assignment.md` (the stopping criterion, worked) and
`docs/STATE-OF-PLAY.md` (what is built, what is blocked).

**Measured state this register was written against** — branch `main` @ `30eb333`, tree clean:
428 tests pass; `python scripts/gate_a.py` exits **1** with 7 PASS (5 measured, 2 attested) /
0 FAIL / 3 SKIP; CI green on ubuntu and windows; `scripts/check_suite_integrity.py` exits **1**
because the mutation score reads 100.00 against a 95.89 ± 0.50 pin.

---

## The ordering rule

**Open spikes are sorted by the reach of what a bad answer forecloses, ties broken by
irreversibility.** In descending order:

1. **Band 1 — a bad answer makes a *frozen, pre-registered* threshold unmeetable, and the repair
   expires at the Phase 3.5 pre-registration timestamp.** Highest, because the fallback has a
   deadline. After the timestamp no threshold may be revised (`CLAUDE.md`, design spec §7).
2. **Band 2 — blocks all of Phase 4–5 execution, and the decisive form of Band 1.** You cannot
   measure whether a baseline runs on hardware you have never started a container on.
3. **Band 3 — blocks a scheduled work item *and* a number the pre-registration will publish**, but
   is re-measurable at any time.
4. **Band 4 — attached to a Gate A row that may never close.** The resolution is a framing
   decision as much as an experiment; the experiment produces the decision brief.
5. **Band 5 — blocks nothing currently scheduled.** Kept so the work is not rediscovered, and
   because two of them expire at the freeze as well.

Within a band, entries are ordered by descending known risk.

**IDs are assigned in document order and are never reused.** They are *not* chronological — a
RESOLVED spike with a high ID may have been settled weeks before an OPEN one with a low ID. Cite
by ID.

**Status vocabulary.** `OPEN` · `RESOLVED` (carries the answer and its provenance) · `SUPERSEDED`
(the question was overtaken; the entry says by what).

---

## Index

| ID | Title | Status | Band |
|---|---|---|---|
| S-01 | Do at least eight of the nine named baselines actually run? | OPEN | 1 |
| S-02 | HoLa — released weights, or only an HF Space? | OPEN | 1 |
| S-03 | DeepCAD — does its 2021 dependency set build against sm_89? | OPEN | 1 |
| S-04 | BrepGen — can its OCCT bindings coexist with our OCP stack? | OPEN | 1 |
| S-05 | DTGBrepGen — same binding question, plus are weights public? | OPEN | 1 |
| S-06 | Text2CAD — runnable, and how is a text baseline given the reference? | OPEN | 1 |
| S-07 | CAD-Recode — runnable, and who fixes the point-sampling recipe? | OPEN | 1 |
| S-08 | cadrille — runnable, and which modality do we commit to? | OPEN | 1 |
| S-09 | CAD-Coder/MIT — runnable, and is it the MIT one? | OPEN | 1 |
| S-10 | Text-to-CadQuery — does its emitted code execute under CadQuery 2.8? | OPEN | 1 |
| S-11 | RHEL host — Docker or podman, rootful or rootless? | OPEN | 2 |
| S-12 | RHEL host — does NVIDIA Container Toolkit passthrough work? | OPEN | 2 |
| S-13 | RHEL host — does SELinux block the volume mounts? | OPEN | 2 |
| S-14 | Windows/WSL2 host — does the four-way ablation farm work? | OPEN | 2 |
| S-15 | One container image for sm_89 and sm_120, or two? | OPEN | 2 |
| S-16 | Why does the mutation score read 100.00%? | OPEN | 3 |
| S-17 | What is the B7 k-sweep on the repaired twelve-mate instrument? | OPEN | 3 |
| S-18 | Does Gate A's N=100k convergence guarantee transfer to Phase 4? | OPEN | 3 |
| S-19 | How much of the mutation kill count is behavioural? | OPEN | 3 |
| S-20 | Is the set of NIST "decidable cases" non-empty? | OPEN | 4 |
| S-21 | Can Gate A ever exit 0 as §7 is currently frozen? | OPEN | 4 |
| S-22 | Can a third party verify the fresh-clone receipt? | OPEN | 4 |
| S-23 | Can AutoMate's BREP assemblies be ingested and labelled? | OPEN | 4 |
| S-24 | What does Phase 4 actually cost? | OPEN | 5 |
| S-25 | What does one adversarial-review checkpoint cost? | OPEN | 5 |
| S-26 | Is the "no such dataset" survey result reproducible from a logged procedure? | OPEN | 5 |
| S-27 | How many published numbers have no guard watched failing? | OPEN | 5 |
| S-28 | Will `numpy==2.4.1` still install for a reviewer in 2027? | OPEN | 5 |
| S-29 | Which of the ~30 deferred minors are still live at `30eb333`? | OPEN | 5 |
| S-30 | Does the NIST AP242 suite contain assemblies? | RESOLVED — no | — |
| S-31 | Does any public dataset pair GD&T with assemblability ground truth? | RESOLVED — no | — |
| S-32 | Does OCCT read `nist_ftc_06` as 47 / 27 / 59? | RESOLVED — yes, exactly | — |
| S-33 | Does resizing a numpy `choice()` tuple perturb the corpus? | RESOLVED — no | — |
| S-34 | Does the `.gitattributes` binary rule survive a fresh clone? | RESOLVED — yes | — |
| S-35 | Is the reliability mate repair unique? | RESOLVED — no | — |
| S-36 | Do the ISO 273 grades move any Tier 1 verdict or the ladder? | RESOLVED — no | — |
| S-37 | Is H7/h6's verdict decided by sampling noise? | RESOLVED — yes | — |
| S-38 | Is the ISO-fit boolean fixed by the shaft letter at every size? | RESOLVED — yes | — |
| S-39 | Does a one-sided floor silently detach from the tree? | RESOLVED — yes | — |
| S-40 | Does a per-file Layer 2 test command measure anything? | RESOLVED — no | — |
| S-41 | Which mutation tool runs natively on Windows? | RESOLVED — cosmic-ray | — |
| S-42 | Is anything under `.superpowers/` untracked-and-unignored? | SUPERSEDED | — |
| S-43 | How many Layer 2 survivors are untriaged? | SUPERSEDED | — |
| S-44 | Is the Gate A reliability mean 0.9982 at `tested=11`? | SUPERSEDED | — |

**29 OPEN · 12 RESOLVED · 3 SUPERSEDED.**

---

## Resume cold: the first three commands

1. `git log --oneline -1` — confirm `30eb333` or note the delta.
2. `python -m pytest -q` — expect 428 passed, tree clean afterwards.
3. `python scripts/gate_a.py` — expect exit 1, 7 PASS (5 measured, 2 attested) / 0 FAIL / 3 SKIP.

Do **not** run `pytest` concurrently with `scripts/gate_a.py` or
`scripts/check_suite_integrity.py`. The declared-mutation layer writes to `src/` transiently and
holds `.mutation-in-progress`; readers exit 2 rather than measure a mutated checker (`CLAUDE.md`).

---

# Band 1 — the frozen-threshold spikes, whose fallback expires at the freeze

**Read this before the nine entries below, because it is the reason they are spikes and not
tasks.** Design spec line 178–181 names **nine** baselines. Gate C's frozen criterion (design spec
§7, Gate C) requires the mechanism effect to hold "across **≥ 6 of the ≥ 8** baseline models", and
Gate B/D depend on the same set. **Nine listed, eight required — there is exactly one spare.** The
spec's phrase is "Runnable, verified code+weights", but that verification was a literature-review
judgement made from paper text and repository READMEs on 2026-07-31. **Nothing has been executed.**
`harness/`, `metrics/` and `analysis/` do not exist; `src/` contains only the checker and the
generator.

So the question "does model X run?" is not a task with a known answer and an unknown duration. It
is a spike with an unknown *answer*, and two bad answers exhaust the margin. The close-out plan
schedules the audit at ~1 day and explicitly defers it
(`docs/superpowers/plans/2026-08-01-closeout.md:1084`): *"it must happen before pre-registration:
Gate C's frozen '≥6 of ≥8 baseline models' is unmeetable if fewer than eight actually run, and that
is unrecoverable after the freeze."*

---

### S-01 — Do at least eight of the nine named baselines actually run?

**The question.** Of the nine models at design spec line 178–181, how many can be brought to the
point of emitting geometry or CadQuery source for one held-out input, on one of our two
workstations, using only publicly obtainable code and weights? The answer is an integer 0–9.

**Why it is unknown.** Nobody has tried. The "verified code+weights" claim in the spec is a reading
of repositories, not an execution of them. ROUND-0 F8 says so plainly
(`.superpowers/closeout/ROUND-0-architect-plan.md:27`): *"Phase 4 has essentially no
infrastructure. `metrics/`, `harness/`, `analysis/` do not exist. A5 is one line hiding three
unbuilt subsystems plus ≥8 baseline integrations."* The same document's "risk the architect did not
solve" section declines to estimate it and warns against extrapolating from the checker's velocity.

**The experiment that resolves it.** For each of the nine: clone the repository at a pinned commit,
build the environment, obtain the weights, run the published inference command on one input, and
record the artifact. Log per model — repo URL + commit SHA, weights URL + SHA-256, licence,
environment recipe, wall-clock, output path. Roll up to an integer and compare it against 8.

**Cheapest decisive form — ~20 minutes, before any environment work.** A paper-only pass. For each
of the nine, open the repository and answer three yes/no questions: (a) is there an inference entry
point in the repo, (b) is there a weights artifact reachable without a request form or an email,
(c) does the licence permit evaluation use and publication of results. Any model failing (b) or (c)
is out regardless of toolchain. That alone can drop the count below eight, which is the only answer
that changes the plan. Spend the day on environments only after this.

**What it blocks.** Gate C's frozen ≥8 criterion; Phase 4 (E1–E5) and therefore Gates B and D; and
the Phase 3.5 pre-registration, which must not be timestamped while the count is unknown.

**Cost.** 20 min cheapest · ~1 engineer-day full, assuming a working GPU host (S-11…S-15).

**If the answer is bad.** *Before the freeze* there are two options: (i) recruit substitutes — the
spec already allows "Plus prompted frontier VLMs emitting CadQuery", which are cheap and reliably
runnable, and `papers/literature/` holds four unassessed candidates (CAD-MLLM 2411.04954,
CAD-Assistant 2412.13810, SeekCAD 2505.17702, CADReview 2505.22304); (ii) revise "≥8" downward *in
the pre-registration, before it is posted*, with the reason recorded — permitted only because it is
pre-data. **After the timestamp neither is available and Gate C is unmeetable.**
⚠ **PROJECT RISK — the fallback expires.** See the risk register.

**Status: OPEN.**

---

### S-02 — HoLa (2504.14257): released weights, or only a Hugging Face Space?

**The question.** Can HoLa be run locally from public artifacts, or is the only public access a
hosted Space?

**Why it is unknown.** The design spec annotates it *"HoLa (2504.14257, HF Space)"* — the only one
of the nine tagged with its distribution channel rather than "code+weights". A Space is an
inference endpoint. It may wrap weights that were never released, and it cannot be driven at
thousands-of-assemblies scale inside our harness regardless.

**The experiment that resolves it.** Open the Space's `Files and versions` tab and its `app.py`. If
`app.py` downloads a checkpoint from a public model repository at startup, the weights *are* public
and the Space is only a UI. If the checkpoint is baked into private storage or the Space is gated,
local running is impossible.

**Cheapest decisive form — ~10 minutes.** That one page. It settles "weights public: yes/no"
without an environment, a GPU, or a download.

**What it blocks.** S-01, and one of the eight required slots.

**Cost.** 10 min cheapest · 2–4 h to a first local run once weights are confirmed.

**If the answer is bad.** HoLa becomes the spare, spent. Eight remain — but *only* if every other
one of the eight runs. This is the entry that converts any second failure into an S-01 escalation.
A fallback exists and it is the last one.

**Status: OPEN.**

---

### S-03 — DeepCAD (2105.09492): does its 2021 dependency set build against sm_89?

**The question.** Can DeepCAD's pinned PyTorch/CUDA generation be built and run on an RTX A6000 Ada
(compute capability **sm_89**)? If not, does the oldest PyTorch that *does* ship sm_89 kernels
reproduce DeepCAD's published behaviour on a fixed seed?

**Why it is unknown.** DeepCAD predates both target GPUs by four years. Ada needs CUDA 11.8+/12.x;
a 2021 pin (PyTorch 1.x against CUDA 10.2 or 11.1) has no sm_89 kernels compiled in and will either
fail to build or silently fall back to CPU. Nobody has attempted the build; nothing in any ledger
records a GPU having been used at all (see Band 2).

**The experiment that resolves it.** On the RHEL host, build DeepCAD's environment as pinned; run
`torch.cuda.get_device_capability()` and the published inference script on one input. If the pinned
stack fails, retry on the oldest PyTorch wheel carrying sm_89 kernels and diff outputs against any
released sample at a fixed seed.

**Cheapest decisive form — ~20 minutes, no GPU needed.** Read DeepCAD's `environment.yml` /
`requirements.txt`, extract the torch and CUDA pins, and check them against the published PyTorch
wheel/architecture matrix for sm_89. If the pinned torch has no sm_89 build, "not as pinned" is
established without touching hardware, and the spike narrows to "does it run on a newer torch",
which is a different and smaller experiment.

**What it blocks.** S-01 and one slot. DeepCAD costs more than a slot if lost: design spec §0 quotes
three separate published validity figures for it (46.1% / 50.82% / 58.10%), so it is the model the
metric-critique literature is most comparable against.

**Cost.** 20 min cheapest · 0.5–1 day for the port.

**If the answer is bad.** Run DeepCAD CPU-only over a reduced sample. Generative CAD inference at
hundreds of samples is slow on CPU but not impossible, and E1–E5 do not require the full corpus per
model if the sample is pre-registered. Fallback exists.

**Status: OPEN.**

---

### S-04 — BrepGen (2401.15563): can its OCCT bindings coexist with our OCP stack?

**The question.** Does BrepGen install and run with a B-rep toolkit binding that can coexist with —
or be cleanly isolated from — the OCP 7.x that `tolcad.gen` already requires via `cadquery>=2.8`?

**Why it is unknown.** BrepGen post-processes to B-rep and needs OCCT bindings. Two binding families
exist, `pythonocc-core` and `OCP`, and they ship different, conflicting copies of the OCCT shared
libraries. Our own environment was spiked and verified for CadQuery 2.8.0 + OCP
(`.superpowers/sdd/2026-08-01-procedural-generator/progress.md:11`) — but never alongside a second
binding family. Nobody has attempted a combined or containerised install.

**The experiment that resolves it.** Create a *separate* environment for BrepGen, install its
requirements, run inference on one input, and confirm the harness can move geometry across the
process boundary as STEP rather than as live Python objects.

**Cheapest decisive form — ~15 minutes, and it may dissolve the spike.** Read BrepGen's requirements
for `pythonocc-core` vs `cadquery`/`OCP`, then **decide the harness contract**. If the harness only
ever exchanges STEP files on disk, the binding conflict is a non-issue by construction and both this
spike and S-05 close as "isolate, do not reconcile". Make that architectural decision once, first.

**What it blocks.** S-01 and one slot; and the `harness/` design, because file-based versus
in-process exchange is a choice made once for all nine models.

**Cost.** 15 min cheapest · 0.5 day full.

**If the answer is bad.** Run BrepGen in its own container or conda environment and exchange STEP on
disk. Cheap, standard, and it is the design we should probably adopt anyway. Fallback exists.

**Status: OPEN.**

---

### S-05 — DTGBrepGen (2503.13110): same binding question, plus are the weights public?

**The question.** Does DTGBrepGen install and run, and are its checkpoints publicly downloadable
without a request?

**Why it is unknown.** It inherits S-04's OCCT binding hazard, and being recent it carries S-02's
weights-availability hazard as well. Neither has been checked.

**The experiment that resolves it.** As S-04, plus the weights check from S-02.

**Cheapest decisive form — ~15 minutes.** The weights check first (it is binary and cheap); the
binding question is answered for free once S-04's harness contract is decided.

**What it blocks.** S-01 and one slot.

**Cost.** 15 min cheapest · 0.5 day full.

**If the answer is bad.** Isolation handles the bindings. Absent weights make this the second spent
slot, which is the escalation trigger in S-01. Fallback exists but consumes the margin.

**Status: OPEN.**

---

### S-06 — Text2CAD (2409.17106): runnable, and how is a text baseline given the reference?

**The question.** Two parts, both determinate. (a) Does Text2CAD run from public code and weights?
(b) Can a *single deterministic rule* derive its text prompt from a `SpecAssembly` sidecar, so the
same rule serves every text-conditioned baseline unchanged?

**Why it is unknown.** (a) has not been attempted. (b) is a gap in the frozen methodology, not an
oversight in the code: design spec §4.2 commits that "the tolerance schema belongs to the reference
design, not to the prediction", but says nothing about how a *text*-conditioned model is handed the
same reference. Three of the nine (Text2CAD, Text-to-CadQuery, CAD-Coder) are text-conditioned and
four are not. **If the prompt is authored per model, we are measuring our prompt engineering.**

**The experiment that resolves it.** Run inference once. Separately, write one prompt-derivation
function from a sidecar and apply it, unmodified, to all three text baselines; check that none needs
a special case.

**Cheapest decisive form — ~30 minutes, no model run.** Take one existing generated sidecar and
hand-write the prompt-derivation rule for it. If one deterministic rule plausibly serves all three,
the protocol question closes and only runnability remains.

**What it blocks.** S-01 and one slot; and Gate D's "baselines reproduce CADBench unified-protocol
numbers", which presumes a protocol we have not written down for text inputs.

**Cost.** 30 min cheapest · 0.5 day full.

**If the answer is bad.** Unrunnable → one slot lost. No single prompt rule → report the
text-conditioned models as a separate stratum with the prompt rule published verbatim. That is a
disclosure under §8's reporting rules, not a blocker. Fallback exists.

**Status: OPEN.**

---

### S-07 — CAD-Recode (2412.14042): runnable, and who fixes the point-sampling recipe?

**The question.** Does CAD-Recode run from public code and weights, and can our STEP exports be
converted to its expected input *deterministically*, by a recipe we pin rather than one we improvise
per model?

**Why it is unknown.** CAD-Recode maps a point cloud to CadQuery. Our reference geometry is STEP.
Sampling points from a B-rep is a *choice* — density, seed, surface versus volume, normalisation —
and that choice sits inside the measurement. Nobody has fixed it, and the same choice is shared with
S-08.

**The experiment that resolves it.** Sample a point cloud from one of our STEP exports, run
inference, and record the sampling recipe as a pinned function with its own test, in the same style
as `scripts/measure_ladder.py`'s `LADDER_RECIPE`.

**Cheapest decisive form — ~20 minutes.** Confirm the repo carries weights, then read what point
count and normalisation its inference script expects. That determines whether the sampling recipe is
even a free parameter for us or is dictated by the model.

**What it blocks.** S-01 and one slot; and the reference-geometry-to-model-input converter shared
with cadrille.

**Cost.** 20 min cheapest · 0.5 day full.

**If the answer is bad.** Drop it, or feed the meshes the generator already produces and disclose the
tessellation parameters. Fallback exists.

**Status: OPEN.**

---

### S-08 — cadrille (2505.22914): runnable, and which modality do we commit to?

**The question.** Does cadrille run from public code and weights, and which of its input modalities
(point cloud / image / text) do we commit to — once, pre-registered?

**Why it is unknown.** Not attempted. Being multi-modal it inherits both S-06's prompt question and
S-07's sampling question, and a per-experiment modality choice would be a free parameter chosen
after seeing results.

**The experiment that resolves it.** As S-07; and record the chosen modality in the pre-registration
with the reason, before any run against the research corpus.

**Cheapest decisive form — ~20 minutes.** Weights check plus a read of the inference entry point to
see which modality is best supported. Pick that one and pin it.

**What it blocks.** S-01 and one slot.

**Cost.** 20 min cheapest · 0.5 day full.

**If the answer is bad.** One slot lost. Fallback exists.

**Status: OPEN.**

---

### S-09 — CAD-Coder/MIT (2505.14646): runnable, and is the artifact the MIT one?

**The question.** Does the MIT CAD-Coder run from public code and weights — and is the repository we
would use the one behind arXiv **2505.14646**, not Beihang's **2505.19713**?

**Why it is unknown.** The design spec's own note (lines 183–184) warns that two distinct papers
share the title and says "Do not conflate". Both PDFs are in `papers/literature/`
(`2505.14646_cad-coder-mit.pdf`, `2505.19713_cad-coder-beihang.pdf`). Nobody has checked which paper
any given hub repository or checkpoint belongs to.

**The experiment that resolves it.** Run inference; and independently verify that the repository's
README arXiv link resolves to 2505.14646.

**Cheapest decisive form — ~10 minutes.** Open the README and read the arXiv ID. This is cheap and
it is the highest-consequence ten minutes in Band 1: a mis-identification silently substitutes a
different model into a *pre-registered* baseline list. That is a correctness failure, not a slot
failure, and it would be undetectable in the results.

**What it blocks.** S-01 and one slot; and the integrity of the pre-registered baseline list.

**Cost.** 10 min cheapest · 0.5 day full.

**If the answer is bad.** Beihang's CAD-Coder is itself a legitimate candidate — but it must be
*named as such* in the pre-registration, not swapped in silently. That option exists only before the
timestamp.

**Status: OPEN.**

---

### S-10 — Text-to-CadQuery (2505.06507): does its emitted code execute under CadQuery 2.8?

**The question.** Does it run from public code and weights, and do its emitted CadQuery programs
*execute* under our pinned CadQuery 2.8?

**Why it is unknown.** Not attempted. Emitting CadQuery source is not the same as emitting CadQuery
source that runs — that gap *is* the validity metric the literature reports at 46–58% for DeepCAD.
Worse, the execution harness that turns emitted code into geometry does not exist, and its sandbox
and timeout policy is unwritten. §8 rule 4 forbids dropping failed generations and requires
worst-case metric values instead, which means the harness must return a **typed failure** for every
program, never an exception that a caller can swallow.

**The experiment that resolves it.** Run inference on ten inputs; execute each emitted program under
CadQuery 2.8; record the validity rate and a failure taxonomy.

**Cheapest decisive form — ~30 minutes, no model run.** Take ten CadQuery programs from the paper's
own released sample outputs or its qualitative appendix and execute them under CadQuery 2.8. That
measures the version-compatibility risk — the part most likely to bite — with no weights and no GPU.

**What it blocks.** S-01 and one slot; and the design of the code-execution harness shared with
CAD-Coder, cadrille and the frontier-VLM baselines.

**Cost.** 30 min cheapest · 0.5 day full.

**If the answer is bad.** Version-pin CadQuery per baseline inside that baseline's own container, and
disclose the per-model version in the results table. Fallback exists.

**Status: OPEN.**

---

# Band 2 — the GPU and toolchain spikes

**Read this before the five entries below.** The deployment target is **2× 4-GPU workstations with
RTX A6000 Ada, sm_89** — one RHEL host, one Windows host running Docker under WSL2. The development
laptop has an **RTX 5060, sm_120 (Blackwell), 8 GB**, which needs CUDA 12.8+ / PyTorch 2.7+ —
*newer* than Ada requires. **A container proven on the laptop's GPU is therefore not evidence about
the workstation.** The implication runs one way only, and it is easy to get backwards.

The whole corpus — every spec, plan, ledger and close-out round — mentions this hardware **exactly
once**, at design spec line 200: *"Primary: RHEL box, 4× A6000 Ada. Ablation farm: Windows/WSL box,
4 concurrent single-GPU configs."* A grep across `.superpowers/` for docker, podman, WSL2, SELinux,
RHEL, CUDA, sm_89, sm_120, A6000 or NVIDIA Container Toolkit returns **zero hits**. That line is an
assertion of intent with no recorded verification behind it. The toolchain is not "assumed working";
it has never been described. Everything in Band 2 is five to fifteen minutes of work that nobody has
done.

---

### S-11 — RHEL host: Docker or podman, rootful or rootless?

**The question.** On the RHEL workstation, which container runtime is installed, is the daemon
rootful, and can the account we will use start containers without a sysadmin?

**Why it is unknown.** Nobody has logged in and looked. See the Band 2 preamble.

**The experiment that resolves it.** On the host: `podman info`, `docker info`,
`systemctl is-active docker`, `id`, `getent group docker`. Record which succeed and paste the output
into this entry.

**Cheapest decisive form — ~5 minutes.** Those five commands, once. There is no cheaper version and
no reason it has not been done.

**What it blocks.** The decisive form of every Band 1 spike; Phase 4; Phase 5.

**Cost.** 5 min.

**If the answer is bad** (rootless podman only, no Docker): rootless podman with NVIDIA CDI works,
but device generation and the run flags are a different recipe from Docker's `--gpus all`, and every
per-baseline README assumes Docker. Fallback exists; it is a day of setup, not a wall.

**Status: OPEN.**

---

### S-12 — RHEL host: does NVIDIA Container Toolkit GPU passthrough work?

**The question.** Does a container on the RHEL host see all four A6000 Ada GPUs, and does a PyTorch
build inside it report compute capability `(8, 9)` for each?

**Why it is unknown.** Never attempted. Driver version, toolkit installation and runtime registration
are three separate things, and any one can be missing on a host that otherwise looks healthy from
the shell.

**The experiment that resolves it.**
`podman run --rm --device nvidia.com/gpu=all <cuda-image> nvidia-smi` (or
`docker run --rm --gpus all …`), then a PyTorch image running
`torch.cuda.device_count()` and `torch.cuda.get_device_capability(i)` for each device.

**Cheapest decisive form — ~10 minutes.** The `nvidia-smi`-in-a-container one-liner. Four A6000 Ada
rows closes the passthrough question; the capability check is two further minutes and closes sm_89.

**What it blocks.** All of Phase 4 and Phase 5; S-01's full form.

**Cost.** 10 min, plus up to a day if the toolkit must be installed.

**If the answer is bad.** Run on bare metal with conda environments instead of containers. Ugly, and
it costs per-baseline reproducibility — but Gate D's fresh-clone criterion is about *our* repo, not
the baselines, so it is survivable and must simply be disclosed. Fallback exists.

**Status: OPEN.**

---

### S-13 — RHEL host: does SELinux block the volume mounts?

**The question.** With SELinux enforcing, can a container read the corpus directory and write
results to a host path without `:z`/`:Z` relabelling — and if relabelling is required, is it safe on
the paths we intend to mount?

**Why it is unknown.** RHEL ships SELinux enforcing by default and nobody has mounted anything.

**The experiment that resolves it.** `getenforce`; then a container with `-v $PWD/data:/data:ro` and
`-v $PWD/out:/out`, reading one file and writing one file. On denial, `ausearch -m avc -ts recent`,
then retry with `:Z`.

**Cheapest decisive form — ~10 minutes, or free.** `getenforce` plus a single mount-and-touch
container run — and **bundle it into S-12's container invocation**, which costs nothing extra.

**What it blocks.** Phase 4 corpus I/O and result collection. Not the model computation itself.

**Cost.** 10 min standalone, 0 bundled.

**If the answer is bad.** `:Z` relabelling, or `--security-opt label=disable` on a dedicated scratch
path. ⚠ **Named hazard:** `:Z` *relabels the host directory in place*. Never apply it to a directory
containing the git repository or the NIST data. Fallback exists with a footgun attached.

**Status: OPEN.**

---

### S-14 — Windows/WSL2 host: does the four-way ablation farm work?

**The question.** On the Windows workstation, does Docker under WSL2 expose all four A6000 Ada GPUs,
and can four single-GPU containers run concurrently without cross-talk, as design spec §6's ablation
farm assumes?

**Why it is unknown.** Never attempted. WSL2 GPU passthrough works through the Windows driver's
`/usr/lib/wsl/lib` shim, which is a *different* mechanism from the Linux NVIDIA Container Toolkit;
multi-GPU device selection under WSL2 has historically been the weaker path. Separately, this repo
already has one measured instance of a tool that refuses to run natively on Windows and directs to
WSL (S-41), so platform assumptions here have a track record of being wrong.

**The experiment that resolves it.** Inside the WSL2 distro: `nvidia-smi`. Then launch four
containers each pinned to a different device (`--gpus '"device=N"'` or `CUDA_VISIBLE_DEVICES`) and
confirm four distinct GPU UUIDs and four independent memory allocations.

**Cheapest decisive form — ~15 minutes.** `nvidia-smi` inside WSL2, then one container with
`--gpus all` printing `torch.cuda.device_count()`. If it prints 4, the farm design stands and the
pinning detail is routine.

**What it blocks.** Phase 5 ablations only. It does **not** block Phase 4 if S-11/S-12 are green,
which is why it sits below them.

**Cost.** 15 min.

**If the answer is bad.** Run ablations serially on the RHEL host. That costs wall-clock, not
validity — §6 says ablations are embarrassingly parallel, which also means they are trivially
serialisable. Fallback exists.

**Status: OPEN.**

---

### S-15 — One container image for sm_89 and sm_120, or two?

**The question.** Does a single image satisfy both the A6000 Ada workstations (sm_89) and the RTX
5060 laptop (sm_120, 8 GB), or must the laptop run a separate, newer image?

**Why it is unknown.** The constraint is asymmetric and nobody has stated which direction our images
will be built to. sm_120 requires CUDA 12.8+ / PyTorch 2.7+, which is *newer* than sm_89 requires.
So an image built for the laptop will generally also run on the workstation — but **an image proven
on the laptop is not evidence the workstation is configured**, and an image built to an *older* pin
(S-03's DeepCAD case) may run on the workstation and not on the laptop at all.

**The experiment that resolves it.** Build one image on CUDA 12.8 / PyTorch 2.7 and run
`torch.cuda.get_device_capability()` on both hosts. Then, separately, take the oldest pin any
baseline requires (S-03) and check whether it runs on either.

**Cheapest decisive form — ~20 minutes.** One image, two `docker run` invocations, two printed
capability tuples. **Do this before building any per-baseline environment** — it decides whether
laptop iteration means anything at all, and therefore whether S-02…S-10 can begin before a
workstation is reachable.

**What it blocks.** The credibility of any "it works on my laptop" result; the environment recipe
S-02…S-10 will be measured in.

**Cost.** 20 min, assuming S-11/S-12/S-14 are green.

**If the answer is bad** (two images needed): maintain two tags and state in the README which GPU
each targets. A second, independent hazard hides here: the laptop's **8 GB** may be below several
baselines' inference footprint regardless of architecture, in which case the laptop is not a
baseline development target at all and only the workstations are. That does not stop the project,
but it raises S-11's priority from "cheap" to "first". Fallback exists.

**Status: OPEN.**

---

# Band 3 — blocks a scheduled item and a published number

---

### S-16 — Why does the mutation score read 100.00%?

**The question.** Layer 2's mutation score over the six core modules measures **100.00%** against a
pin of **95.89 ± 0.50** [LR §1, "mutation score"], so `scripts/check_suite_integrity.py` exits 1.
Exactly one of three things is true. **(a)** The *instrument* is broken and the number is not a
mutation score at all. **(b)** The score is real but the enumerated survivor set is stale or
mis-scoped, so the two figures were never measurements of the same tree. **(c)** The tree genuinely
improved and every previously-surviving mutant is now killed. Which?

**Why it is unknown.** **The last time anyone *enumerated* a survivor set was run 3** [LR §1,
"untriaged survivors"]: 93.85% = 610/650, i.e. 40 survivors, of which 19 are documented equivalents,
leaving **21 untriaged**. Commit `380d36a` then killed nine mutants. Every figure recorded since is
arithmetic over a score, not an enumeration — which is [LR §1]'s stated finding and the reason P1.5
is a *re-measurement* rather than a new control. And there is an arithmetic objection to (c) that
nothing has answered: **19 documented equivalent mutants cannot be killed by definition.** An
equivalent mutant is semantically identical to the original, so no test can distinguish it. A
genuine 100.00% requires those 19 rulings to have been wrong. That is possible — the SI-4 round
already corrected nine mislabellings, four "equivalent" that were live and five "killed" that did
not kill — but it is a strong claim and nothing has tested it. [LR §1] is explicit: the 100.00% is
*"Recorded, not believed"*, and **DO NOT RE-PIN**.

**Leading hypothesis — recorded so the experiment is aimed rather than exploratory, and explicitly
NOT yet verified.** Layer 2's test command in `cosmic-ray.toml` is plain
`python -m pytest tests/test_{types,y14_5,iso286,montecarlo,checker,reliability}.py -x -q …`, and
`scripts/check_suite_integrity.py:200-203` runs `cosmic-ray init/exec` with `cwd=REPO_ROOT` — so
cosmic-ray mutates `src/tolcad/<module>.py` **in place in the working tree**. Since commit
`d7285f9`, `tests/conftest.py` installs a **session-scoped autouse** finalizer that fails the run
if `git status --porcelain src/ tests/fixtures/` is non-empty. During every mutant's test command
`src/` is, by construction, dirty. If that finalizer fires, **every mutant is recorded as killed
regardless of its semantics and the score is 100.00% by construction.** The timeline is consistent:
`MUTATION_MEASURED = 95.89` was the architect's end-to-end run, taken from the feature branch
*before* `d7285f9` landed (the close-out plan's Task 2 records 95.89 as already-measured input and
forbids re-running the layer), while the 100.00% observation is Task 6's run at `05d4dae`, after it.
`git merge-base --is-ancestor d7285f9 062316e` returns true. If this hypothesis holds, the pin has
not detached at all — the instrument stopped measuring.

**The experiment that resolves it.** Run one module's session and read the *per-mutant* outcomes
rather than the aggregate: `cosmic-ray init` + `exec` + `cr-report --show-output` against
`src/tolcad/types.py` alone, then search a single mutant's captured test output for
`THE SUITE LEFT TRACKED FILES MODIFIED`. Its presence proves (a) outright. Its absence, together
with a genuine per-mutant kill reason, moves the question to (b)/(c), and the answer is then P1.5 in
full: enumerate the survivor set, rule on each survivor (killed by a new test, or recorded
equivalent), and only then re-pin.

**Cheapest decisive form — ~5 minutes, and it does not need cosmic-ray.** Reproduce the *condition*,
not the run. In a **scratch clone** — never the working tree; see the concurrency rule in
`CLAUDE.md` — append a no-op comment to `src/tolcad/types.py` so the tree is dirty, then run the
Layer 2 test command exactly as `cosmic-ray.toml` spells it. If it exits non-zero with the
finalizer's message against a behaviourally unchanged file, the instrument is confirmed broken and
every number from that run is void. **Do this before committing 1.5 serialised days to P1.5** — it
may reduce P1.5 from "re-triage 21 survivors" to "fix the test command and re-measure".
If confirmed, the fix is a small scoping change to the Layer 2 test command (an opt-out env var read
by the finalizer, or a scoped conftest). **Do not apply it inside this spike**: it edits `tests/`,
which P1.5 serialises.

**Method notes any re-run must respect.** Set `PYTHONDONTWRITEBYTECODE=1` and clear `__pycache__`
before hand-verifying any mutant — a `-` → `%` mutation preserves file size, so a same-second
rewrite can be served from a stale `.pyc` and report a **false kill**. This has already bitten once
(`.superpowers/sdd/2026-08-01-suite-integrity/progress.md:284-287`). And the denominator is
`killed / (total − incompetent)` aggregated over six modules, not `killed / total`: 468 of 1,118
jobs are INCOMPETENT and cannot execute [LR §1 records 75.4% as an error found and corrected, not a
result].

**What it blocks.** P1.5 (1.5 **serialised** days during which nothing may edit `src/` *or*
`tests/`); any re-pin of `MUTATION_MEASURED`; a clean `check_suite_integrity` exit; and through
those, the pre-registration's Layer 2 disclosure, since the mutation score is a number the
pre-registration publishes. S-19 depends on it entirely.

**Cost.** 5 min cheapest (scratch clone) · one full Layer 2 run is estimated at **~5 min** in the
suite-integrity ledger and **~25 min** in ROUND-0 F12 — *those two estimates contradict each other
and neither has been re-timed*, so budget 30 min · 1.5 serialised days for P1.5 in full.

**If the answer is bad.** Each branch has a fallback. **(a)** instrument broken → fix the test
command, re-measure, re-pin with the reason recorded in the constant's comment; the 95.89 pin stands
until a valid measurement replaces it. **(b)** stale or mis-scoped → re-enumerate; that is P1.5 as
already planned. **(c)** genuinely 100.00% → re-pin *upward*, record why per O-C, and re-audit the
19 equivalence rulings, because a 100% score over a set containing equivalents is self-contradictory.
In no branch is re-pinning permitted before the enumeration. Fallback exists in all three.

**Status: OPEN.**

---

### S-17 — What is the B7 k-sweep on the repaired twelve-mate instrument?

**The question.** With the reliability mate set repaired to `tested=12, excluded=0` under
construction rule D-D, at what perturbation multiple *k* does Gate A's reliability criterion begin
to catch a degraded checker?

**Why it is unknown.** The published sweep was measured on the **eleven**-mate instrument
(`.superpowers/closeout/ROUND-2-architect-revised.md:118-125`): k=1.0 → 0.9982; k=1.5 → 0.9791,
the largest unambiguously *not* caught; k=2.0 → 0.9518 with a CI straddling 0.95, indeterminate;
k=2.5 → 0.9264, the smallest unambiguously caught; k=3.0 → 0.9068. The disclosed bound is
*"reliably detects ≥2.5×; reliably fails to detect ≤1.5×; indeterminate at 2×"*. Restoring the
twelfth mate **tightened** the instrument: [LR §1, reliability] records that k=2 now *fails* at
0.9392 where it previously passed at 0.9518. One point of the new sweep is known; four are not.
[LR §1] states plainly that *"the k-sweep must be re-measured before it enters the
pre-registration."*

**The experiment that resolves it.** Re-run the sweep at k ∈ {1.0, 1.5, 2.0, 2.5, 3.0} against the
repaired `_RELIABILITY_MATES`, over the same 200 pre-registered seeds and 10,000 bootstrap
resamples, and re-state the bound **with CIs** — R6 requires a CI wherever the quantity is
stochastic.

**Cheapest decisive form — ~15 minutes.** Only two points decide the bound *as published*: the
largest k unambiguously not caught, and the smallest unambiguously caught. Measure **k=1.5 and
k=2.5 first**. If 1.5 is still not caught and 2.5 is caught, the bound's shape is unchanged and only
the indeterminate midpoint moved; the remaining three points are presentation, not finding.

**What it blocks.** The pre-registration's B7 disclosure, and the C1 instance map, which must record
Gate A's headroom instance as **PARTIAL with a numeric bound** rather than CAUGHT.

**Cost.** 15 min cheapest · ~1 h for the full sweep with CIs. Must not run concurrently with
`pytest` — the mutation lock will refuse.

**If the answer is bad.** A wider bound is a disclosure, not a blocker: R6 requires disclosure with a
measured bound and a wide honest bound is publishable. The one outcome with teeth is discovering the
criterion cannot catch even k=3 — that would reopen historical instance 4 as a "metric that cannot
fail" rather than an improved one. Fallback then: keep the frozen 0.95 threshold and publish the
headroom as a stated limitation, exactly as B7 already does. Fallback exists.

**Status: OPEN.**

---

### S-18 — Does Gate A's N=100k convergence guarantee transfer to Phase 4?

**The question.** `check()` defaults to `n=10_000` for `iso_fit`, while Gate A's frozen convergence
criterion is measured at **N=100k** (design spec §7, corrected pre-data at 2026-07-31a). At what n
does a Tier 2 yield stabilise to within ±0.5% across 5 seeds *for our corpus*, and will Phase 4
callers hit the default?

**Why it is unknown.** It was flagged during Phase 2 and deferred:
`.superpowers/sdd/2026-07-31-functional-checker/progress.md:37` — *"minor (deferred, FLAG TO FINAL
REVIEW): `check()` defaults n=10_000 for iso_fit, but Gate A stability needs N=100_000 … a Phase 3/4
caller relying on the default would silently get a non-Gate-A-stable yield."* It was never closed,
and Phase 4's calling code does not exist yet, so nobody can inspect the call sites. The convergence
was measured for Gate A's own mate set, not for the sampled corpus.

**The experiment that resolves it.** Sweep n ∈ {10k, 25k, 50k, 100k} over ~20 corpus `iso_fit` mates
× 5 seeds; record the yield range per n; find the smallest n meeting ±0.5%. Then grep every Phase 4
call site (once it exists) for a `check()` invocation that omits `n`.

**Cheapest decisive form — ~20 minutes.** The two-point version: measure the 5-seed range at n=10k
and at n=100k over 20 mates. If 10k already meets ±0.5% for our corpus, the hazard is theoretical and
the entry closes as a documentation note. If it does not, the answer is "Phase 4 must always pass
`n=100_000` explicitly", and that becomes a harness invariant with a test.

**What it blocks.** Nothing today. It blocks the *transferability* of a frozen Gate A criterion into
Phase 4 — every Tier 2 verdict in E1–E5 must carry the same convergence guarantee Gate A certified,
or the gate certifies an instrument the experiments do not use.

**Cost.** 20 min cheapest · 1–2 h for the full sweep.

**If the answer is bad** (10k is not stable): make `n` a required argument at the harness boundary,
or raise the default. Both are code changes in `checker.py`, which is checker core — so they need a
declared-mutation entry and a watched-failing guard under R1. Fallback exists and is small.

**Status: OPEN.**

---

### S-19 — How much of the mutation kill count is behavioural rather than table pinning?

**The question.** Of the mutants killed in `iso286.py`, what fraction are killed by a *behavioural*
assertion (a computed relationship) versus by a test that pins a published table cell?
`.superpowers/BLOCKERS.md:58-60` records **~84% mechanical**. Is that right, and does it hold for the
other five core modules?

**Why it is unknown.** The ~84% figure appears with no recorded derivation, and the headline it
qualifies ("252 kills", corrected to 256 killed / 19 equivalent) predates the current tree. Nobody
has classified kills per module.

**The experiment that resolves it.** From a Layer 2 session database, join each killed mutant to the
test that killed it and classify that test as table-pinning or behavioural. Report per module.

**Cheapest decisive form — ~30 minutes.** Do not classify all of them. Take the `iso286` session
alone and classify a random sample of 30 kills. Thirty comfortably distinguishes "≈84%" from "≈50%",
and `iso286` is the module the claim was made about.

**What it blocks.** Nothing scheduled. It bounds an honesty claim: the mutation score is offered as
evidence of suite strength, and if most kills are table pinning then the evidence is weaker than the
number implies. **Depends on S-16** — a broken instrument makes every kill uninformative, so do not
start this until S-16 is answered.

**Cost.** 30 min cheapest · 2–3 h full.

**If the answer is bad** (mostly mechanical): disclose it in one sentence in the pre-registration and
let the number stand as what it is. Fallback exists and is free.

**Status: OPEN.**

---

# Band 4 — Gate A's unclearable criteria

---

### S-20 — Is the set of NIST "decidable cases" non-empty?

**The question.** Gate A criterion 2 is frozen at *"Agreement with NIST MBE PMI conformance suite
(FTC/CTC parts): 100% on decidable cases; all others root-caused."* How many of NIST's published PMI
annotations are cases our Tier 1 / Tier 2 checker can return a verdict on? If the answer is zero, the
criterion is satisfied by an empty denominator — a metric that cannot fail, which is this project's
documented dominant failure mode.

**Why it is unknown.** What is settled: all 17 AP242 files in `data/nist_pmi/` contain **zero**
`NEXT_ASSEMBLY_USAGE_OCCURRENCE` entries (S-30), so they are single parts with no mates. NIST
publishes PMI **annotation semantics** — 11 cases, 421 annotations
(`.superpowers/closeout/ROUND-1-qa-critique.md:134-139`) — and our reader currently extracts
*counts*, not feature-control-frame contents (47/27/59 on `ftc_06`, 21/6/11 on the committed
`ctc_01` fixture). ROUND-1's objection is exact: *"'Decidable case', the predicate in the FROZEN §7
threshold, is defined nowhere; with it undefined a zero-case denominator trivially satisfies '100% on
decidable cases'."* Human decision D-A chose "split the criterion, and state the limitation", but
**the definition of a decidable case has still not been fixed, and ROUND-0 line 111 requires it be
fixed BEFORE any case is inspected.** Inspecting first and defining after is how a threshold gets
fitted to data.

⚠ **A trap that must not be walked into.** NIST's download page states in prose that FTC 07/08/09/10
fit together and CTC 02/04 do. ROUND-1 lines 140–145: that is design intent, not published ground
truth, and it is *uniformly positive* — six cases, all True, zero negatives. A ground-truth column
derived from it *"would be cleared perfectly by a checker hard-coded to `return True`. Worse than no
oracle: it manufactures a Gate A PASS that discriminates nothing."* The architect recommended against
this route explicitly, under time pressure especially.

**The experiment that resolves it.** (1) Write down and commit the definition of "decidable case",
**before looking**. (2) Extract FCF *contents* (not counts) from one FTC/CTC part via
`XCAFDoc_DimTolTool`. (3) Count how many extracted annotations fall inside the committed definition.
The answer is an integer.

**Cheapest decisive form — ~45 minutes, of which step 1 is free.** Commit the definition in one
paragraph, then run the existing reader against `nist_ftc_06_asme1_ap242-e2.stp` with an FCF
accessor instead of the counter, and tally by annotation type against the definition. One file
settles whether the number is plausibly zero.

**What it blocks.** Gate A criterion 2 (a SKIP) → `gate_a.py` exiting 0 → Gate D's first criterion.

**Cost.** 45 min cheapest · 1–2 days for a full extraction plus a verdict CSV across the 17 files.

**If the answer is bad (zero decidable cases).** Three framing options exist and **none of them is an
experiment**, which is why this spike's real deliverable is a decision brief. (i) D-A option 3 —
state the limitation. Honest, and it does *not* make Gate A PASS; see S-21. (ii) **AutoMate
(2105.12238)** BREP assemblies as *geometry* with our tolerance schema layered on top, recorded in
the close-out plan (lines 1106–1112) as the natural Phase 4 generalisation. It answers the "two
synthetic plates with holes in a line" criticism but **does not solve oracle independence** — the
verdicts would still be ours plus TolAnalyst, and AutoMate states outright that there is no ground
truth. See S-23. (iii) Reframe the paper as **SolidWorks-oriented**, making TolAnalyst the primary
oracle and accepting licence-gated reproduction. That trades Gate A clearability for a reproducibility
liability; design spec §4.3's hard constraint currently forbids it, and D-B rejected it as *forced,
not chosen*, on the grounds that inverting it "would make their access a reproducibility liability
instead of a credibility asset". Fallbacks exist; all three are editorial.

**Status: OPEN.**

---

### S-21 — Can Gate A ever exit 0 as §7 is currently frozen?

**The question.** Is there any reachable state of the world in which `python scripts/gate_a.py`
exits 0 *without* amending design spec §7? Determinate, by enumeration of the ten rows.

**Why it is unknown.** Nobody has enumerated it. Two of the three SKIPs are governed by human
decisions — D-A (NIST split) and D-B (TolAnalyst supplementary, not blocking) — that are **settled
and recorded in the close-out plan but never written into the frozen §7 table**. The third
(fresh-clone) needs the P2.3 receipt, designed but unbuilt. Meanwhile Gate D's first criterion is
"Gate A | Pass", and `scripts/gate_a.py:4` states: *"Exits 0 only when every criterion passes. A
skipped criterion is not a pass."* ROUND-1 lines 146–148 composed the two findings and reached the
conclusion nobody has since acted on: *"TolAnalyst is licence-gated; NIST has no ground truth. Gate
A, marked blocking, is currently unclearable by any route — blocking Gate D, blocking Paper 2."*

**The experiment that resolves it.** Read every `record()` call in `scripts/gate_a.py`; for each row
that can return `None`, write down the precise artifact whose existence flips it. There are three: a
NIST expected-verdict CSV at `NIST_EXPECTED`, a TolAnalyst export at `TOLANALYST_EXPORT`, and a
fresh-clone receipt. Then ask, per artifact, whether it is producible under §4.3's licence-free
constraint.

**Cheapest decisive form — ~20 minutes.** The enumeration above. It is a reading exercise rather than
a run, and it produces exactly the decision brief the human needs in order to file D-A and D-B.

**What it blocks.** Gate D entirely, and therefore Paper 2.

**Cost.** 20 min.

**If the answer is "no".** The fallback is a **pre-data amendment** to §7, which is permitted — D-E
already ruled to file five amendments, of which 2026-08-01f and 01g are filed and three remain
(the NIST operationalisation, the TolAnalyst optionality, and the suite-integrity §8 C1 amendment).
But that amendment is a human decision about a frozen document, and the project's own rule is that
changing a threshold after seeing data invalidates the result. **It must be filed before the
pre-registration timestamp.**
⚠ **PROJECT RISK — after the timestamp there is no fallback at all.** Gate D becomes structurally
unclearable and the paper ships with a blocking gate open. See the risk register.

**Status: OPEN.**

---

### S-22 — Can a third party verify the fresh-clone receipt?

**The question.** Can the P2.3 receipt be made checkable by a reader with no access beyond the public
remote — for example by resolving the printed Actions run URL through the GitHub REST API and reading
back its `head_sha` and `conclusion`?

**Why it is unknown.** The receipt design is settled as an **ancestor-of-HEAD plus clean-diff-paths
self-report**, and ROUND-2 line 154 concedes the ceiling and invites a better proposal:
*"ancestor+clean-paths prevents staleness, not forgery. 'If you disagree, say what enforcement you
would accept.'"* Nobody has checked whether the Actions API makes the claim independently verifiable.

**The experiment that resolves it.** `gh api repos/harshD42/TolAEG-CAD/actions/runs/<id>` — or an
unauthenticated `curl` against the same endpoint — for the CI run that is already green, and confirm
the response carries `head_sha`, `conclusion` and `status` for a public repository without a token.

**Cheapest decisive form — ~10 minutes.** One unauthenticated `curl` against the existing run.

**What it blocks.** Gate A criterion 7 (the third SKIP) — at the level of *honesty* rather than
mechanism. The SKIP can be flipped by a self-report today; whether it *should* be is the question.

**Cost.** 10 min.

**If the answer is bad** (API unusable unauthenticated, or run retention expires before publication):
disclose the receipt as a self-report in the same sentence as B4's registry-deletion ruling, exactly
as ROUND-2 already specifies. Fallback exists and is already written down.

**Status: OPEN.**

---

### S-23 — Can AutoMate's BREP assemblies be ingested and labelled by our checker?

**The question.** Can AutoMate (2105.12238) B-rep assemblies be read, have our tolerance schema
applied on top, and produce Tier 1/Tier 2 verdicts — at what yield, and with what fraction rejected
as un-schematisable?

**Why it is unknown.** It has never been tried. The idea is recorded in the close-out plan
(lines 1106–1112) as *"the natural generalisation step"* and nowhere else; there is no run behind it,
and AutoMate does not appear anywhere in `.superpowers/`. AutoMate is the only public source in the
111-paper survey with real, large-scale BREP *assemblies* — but it states outright that *"there is no
ground truth"* and its mating labels are design intent (S-31).

**The experiment that resolves it.** Take ten AutoMate assemblies; read them through OCCT; identify
hole/fastener pairs; apply our tolerance schema; run `check()`; record how many produce a verdict and
how many are rejected, with reasons.

**Cheapest decisive form — ~1 hour.** One assembly, by hand. The question that decides feasibility is
narrow: *can a hole/fastener pair be identified from the B-rep automatically, or does it need human
annotation?* If it needs human annotation, this is not a Phase 4 extension at any scale and the entry
closes negative for a fraction of the cost.

**What it blocks.** Nothing scheduled. It is the answer to a *reviewer's* question — "your geometry is
two synthetic plates with holes in a line" — and it is much better to have measured it than to be
asked. It is also S-20's option (ii).

**Cost.** 1 h cheapest · several days for a real ingestion path, unestimated.

**If the answer is bad.** State the corpus limitation and cite the procedural generator's
justification, which is already strong (S-31: no public dataset has all three of assemblies,
tolerances and assemblability). Fallback exists and costs nothing. Note that even a *good* answer
does not solve oracle independence — the verdicts would still be ours.

**Status: OPEN.**

---

# Band 5 — blocks nothing currently scheduled

---

### S-24 — What does Phase 4 actually cost?

**The question.** How many engineer-days and GPU-hours does Phase 4 — corpus generation, `metrics/`,
`harness/`, `analysis/`, ≥8 baselines, E1–E5 — actually take?

**Why it is unknown.** It was never estimated, deliberately. ROUND-2 line 160 lists *"Phase 4 remains
unestimated"* as one of four places the architect invited attack, and ROUND-0 line 117–119 refuses to
estimate it and warns against extrapolating from the checker's velocity: *"the checker is 1,586 lines
of pure numpy with exact answers; baseline integration is neither."*

**The experiment that resolves it.** Generate a pilot. Sample 20 assemblies at each difficulty, build
them through `tolcad.gen.build`, export STEP, and time it; then run one baseline over those 20 and
time that. Extrapolate with the corpus size the pre-registration will freeze.

**Cheapest decisive form — ~30 minutes.** The generator half only — no GPU, no baseline.
`sample_assembly` + `build` + `export` over 20 seeds, timed. That fixes the half entirely under our
control and surfaces any build failures before Phase 4 depends on them.
⚠ **Constraint:** design spec §12 forbids generating a research corpus before pre-registration. A
timed pilot written to a scratch directory and deleted is a measurement sweep, not a corpus — the
pre-registration-prep plan already permits "measurement sweeps that write nothing". Keep it that way
and say so in the log.

**What it blocks.** Nothing mechanically. It blocks *planning*: a phase with no estimate cannot be
scheduled against a PhD-application calendar.

**Cost.** 30 min cheapest · half a day for the full pilot including one baseline.

**If the answer is bad** (Phase 4 is far larger than assumed): reduce corpus size, or reduce the
baseline count to the frozen minimum of eight. **Both are pre-registration decisions and expire at
the timestamp.** Fallback exists pre-freeze only — a secondary instance of S-01's pattern.

**Status: OPEN.**

---

### S-25 — What does one adversarial-review checkpoint cost?

**The question.** How long does one O-D checkpoint take end to end, including the response?

**Why it is unknown.** ROUND-2 line 159 flags it directly: *"N-11 has NO COST ESTIMATE, and it is the
highest-leverage item."* QA's figure — 0.75–1 day per checkpoint plus 0.25 for the response, three
checkpoints, ~3 review-days — is an estimate that was never measured. The evidence for its leverage
*is* measured and is the strongest evidence in the project: **zero of the historical instances were
found by the three-layer machinery; ten were found by an adversarial reader over a diff.** One pass
of this control found a false statement inside a frozen document.

**The experiment that resolves it.** Run one. Schedule the pre-pre-registration checkpoint, hand a
reader who did not write it the design spec §7 plus the two 2026-08-01 specs, and time both the
review and the response.

**Cheapest decisive form — ~2 hours.** There is no cheaper *kind*, because the duty cycle is the
whole point, but it can be **scoped**: review one artifact — the §7 correction log alone — rather
than the corpus, and extrapolate per-page.

**What it blocks.** Nothing mechanically. It is the only control the project's own evidence says
works, and the only one with no budget line.

**Cost.** 2 h scoped · ~3 review-days for all three checkpoints, non-overlapping with engineering.

**If the answer is bad** (it costs more than three days): it remains the highest-leverage item. The
fallback is to cut *checkpoints*, not the control — and to record in the pre-registration which
checkpoint was cut and why. Fallback exists.

**Status: OPEN.**

---

### S-26 — Is the "no such dataset" survey result reproducible from a logged procedure?

**The question.** The close-out plan states, as a survey result over the 111-paper corpus, that **no
public dataset pairs GD&T tolerances with assemblability ground truth** (S-31). Can that negative
result be reproduced by a third party from a logged, re-runnable search procedure?

**Why it is unknown.** The *conclusion* is recorded, with a five-row evidence table
(`docs/superpowers/plans/2026-08-01-closeout.md:1095-1104`). The *procedure* is not: there is no
recorded query, inclusion rule or per-paper verdict anywhere in `.superpowers/` or `docs/`. Under
Gate D's own rule — every claim traceable to a logged experiment run — that is an **Unencoded** claim,
the same shape as the 39-cell IT table check run once in a shell, and the only shape no layer can
catch (observation-assignment spec §4).

**The experiment that resolves it.** Re-run the search with the query written down first: enumerate
`papers/literature/INDEX.md` (111 entries, PDFs gitignored and reproducible via the fetch command in
that file), apply a stated three-column inclusion test (assemblies / GD&T tolerances / assemblability
ground truth), and commit the per-paper verdicts as a CSV alongside the existing table.

**Cheapest decisive form — ~30 minutes.** Do not re-read 111 papers. Write down the inclusion rule,
then classify from titles and the existing INDEX annotations, flagging only the ~10 genuine
candidates for a full read. The published claim is a *negative*, so it survives as long as no
candidate is missed — and the candidate set is small and already named.

**What it blocks.** Nothing mechanically. It converts a headline limitation claim from "stated" to
"traceable", which is Gate D's criterion 7.

**Cost.** 30 min cheapest · half a day for a full logged sweep.

**If the answer is bad** (a dataset is found that has all three): that is a *good* problem — it
becomes the evaluation corpus and strengthens the paper. What it costs is the generator's
justification, which then has to be re-argued on difficulty control and seed reproducibility rather
than on necessity. Fallback exists.

**Status: OPEN.**

---

### S-27 — How many published numbers have no guard watched failing?

**The question.** R1 requires that *every published number has a named guard watched failing, with
recorded output, via a registry entry*. How many published numbers are in violation today?

**Why it is unknown.** The suite-integrity design spec §9 left it open and it was never closed:
*"Nothing forces a new guard to be registered — a future test protecting a new published number could
be added without an entry, and no layer would notice. Options are a naming convention checked by a
lint, or accepting that the registry covers the frozen set and is extended deliberately. Deferred to
the plan."* Nobody has taken the inventory, and the answer changes every commit.

**The experiment that resolves it.** List every number the pre-registration will publish — [LR §1]'s
six contested quantities, plus the Gate A rows, the four ladder counts, the corpus digest and the two
integrity pins — and for each, find the `tests/mutation_registry.py` entry that has been watched
failing. Count the ones with none.

**Cheapest decisive form — ~20 minutes.** Work [LR §1]'s six contested quantities only against
`REGISTRY`. Those are the numbers the pre-registration is most exposed on, and they are already
enumerated for you.

**What it blocks.** R1's coverage claim. Nothing scheduled.

**Cost.** 20 min cheapest · 1–2 h full.

**If the answer is bad.** Add the missing entries, or state in the pre-registration which published
numbers are unguarded and why. Fallback exists.

**Status: OPEN.**

---

### S-28 — Will `numpy==2.4.1` still install for a reviewer in 2027?

**The question.** Does the pinned `numpy==2.4.1` wheel install on the Python versions a reviewer will
plausibly have in 2027, and if not, does the difficulty ladder reproduce on the nearest available
version?

**Why it is unknown.** ROUND-0 F3 identified the underlying hazard and it was closed by *decision*,
not by measurement: *"The frozen ladder is numpy-version-dependent … NEP 19 guarantees stream
stability only for legacy `RandomState`, not `Generator`. Reproduces today; nothing makes it reproduce
for a reviewer in 2027."* D-C ruled **pin `numpy==2.4.1`, do not switch to `RandomState`**, and the
architect *"HOLDS LOOSELY"* (ROUND-2 line 83). Nobody has tested the pin against a newer interpreter.
The exposure is concrete: the four ladder counts (31/159, 99/301, 239/452, 421/609) and the corpus
digest `c035c2d9…` are pinned two-sided in `tests/gen/test_ladder_pin.py` and go into the
pre-registration verbatim.

**The experiment that resolves it.** Create clean virtualenvs on Python 3.13 and on the newest
interpreter available, `pip install numpy==2.4.1` in each, and run
`python -m pytest tests/gen/test_ladder_pin.py`. Then repeat with the newest numpy and record whether
the counts move.

**Cheapest decisive form — ~20 minutes.** The two installs and one test run. The forward-looking half
cannot be measured today at all; what *can* be measured is whether the counts are stable across the
current numpy minor, which bounds the risk.

**What it blocks.** Nothing today. Gate D's reproducibility criterion ("fresh clone → headline
numbers, exact for deterministic") in the future.

**Cost.** 20 min.

**If the answer is bad** (the pin becomes uninstallable, or the counts move on a newer numpy): publish
the ladder as *counts plus the exact environment*, and ship the corpus digest so a reviewer can detect
a stream change rather than silently reproduce a different corpus — which is precisely what the digest
was built for. A containerised reproduction recipe is the stronger fallback and costs a Dockerfile.
Fallback exists.

**Status: OPEN.**

---

### S-29 — Which of the ~30 deferred minors are still live at `30eb333`?

**The question.** Five ledgers carry roughly thirty items marked "minor (deferred)" or "PARKED". Seven
were escalated and fixed before merge; the rest were never closed. How many are still live against the
current tree?

**Why it is unknown.** They were deferred against trees that have since changed substantially — the
Phase 3.5 branches, the ISO 273 work and the whole close-out plan all landed afterwards. Nobody has
re-checked them. The inventories are at
`.superpowers/sdd/2026-07-31-functional-checker/progress.md:11-54` (fifteen minors, of which line 65
records *"7 deferred minors escalated to FIX BEFORE MERGE"* — **eight were not**),
`.superpowers/sdd/2026-08-01-procedural-generator/progress.md:311-340`,
`.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:296-320` (R-b…R-f, all parked),
`.superpowers/sdd/2026-08-01-iso273-traceability/progress.md:295-350` (R-2, R-3, R-5, R-6, R-7 parked)
and `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:98-106, 331-340`.

**The experiment that resolves it.** Most of these are inspections and belong in a plan, not here.
**Three are genuinely experiment-shaped** and are the reason this entry is a spike:

- *"no test for `position_tol` exceeding MMC (behaviour correct, just unverified)"* — functional-checker
  `progress.md:15`. The behaviour has never been executed at that input. One test run settles it.
- **R-2** (iso273 `progress.md:301-307`) — *"If `y14_5` or `checker._feature` ever read `.lmc` or
  `.min_size`, `-0.1` reaches a verdict and the test stays green."* Whether any current path reads
  them is settled by running with an instrumented accessor, not by grepping.
- **R-7** (iso273 `progress.md:324-325`) — the fastener `lower_dev = -0.1` **is published**: it
  round-trips into the sidecar fastener dict, so the number is visible in the frozen benchmark data.
  Confirm by reading one exported sidecar, then decide whether it is disclosed or changed **before**
  the freeze.

**Cheapest decisive form — ~45 minutes.** Those three only. Sweep the remaining ~27 as a plan item.

**What it blocks.** Nothing. R-7 touches the frozen benchmark data and therefore expires at the
timestamp; the other two do not.

**Cost.** 45 min for the three · half a day for the full sweep.

**If the answer is bad.** Each is individually small and each was already ruled non-blocking once. The
one to watch is R-7, because a published constant cannot be changed after the freeze — only disclosed.
Fallback exists.

**Status: OPEN.**

---

# Resolved spikes

Recorded so nobody redoes the work. Each carries its answer and its provenance.

---

### S-30 — Does the NIST AP242 suite contain assemblies?

**Answer: NO.** All **17** AP242 files in `data/nist_pmi/` contain **zero**
`NEXT_ASSEMBLY_USAGE_OCCURRENCE` entries. They are single parts.

**Consequence.** TolAnalyst analyses assemblies, so it cannot supply the missing assemblability
ground-truth column either — the two Gate A oracles fail for *independent* reasons and the failure is
structural, not a backlog item. This measurement is what settled human decision **D-A** (split the
criterion: NIST becomes a PMI-*extraction* oracle, and state the limitation).

**Provenance.** `docs/superpowers/plans/2026-08-01-closeout.md:15` and the survey table at line 1097;
`.superpowers/sdd/2026-08-01-closeout/progress.md:15-18` — *"Settled by measurement, not preference."*

**Status: RESOLVED.** Feeds S-20, S-21, S-23.

---

### S-31 — Does any public dataset pair GD&T tolerances with assemblability ground truth?

**Answer: NO.** A survey of the 111-paper corpus found none. Assemblies exist, tolerances exist and
assemblability judgments exist — **no public dataset has all three.**

| Source | Assemblies | GD&T tolerances | Assemblability ground truth |
|---|---|---|---|
| NIST MBE PMI suite | ✗ (S-30) | ✓ semantic PMI | ✗ |
| AutoMate 2105.12238 | ✓ "first large scale dataset of BREP CAD assemblies" | ✗ | ✗ — states outright there is no ground truth; mating is design intent |
| MUSE 2605.28579 | ✓ | ✗ | ✓ but a VLM rubric, not arithmetic |
| ASSEMCAD / ASSEMBENCH 2607.05123 | ✓ curated | ✗ — "tolerance" occurs twice, once as a mesh epsilon | ✗ |
| politopix 1509.08763 | GD&T polytopes | ✓ | academic, unmaintained |

**This is evidence, not an admission** — it is what justifies building a generator, and it belongs in
the pre-registration's limitations section as a survey result rather than left for a reviewer to
wonder about.

**Provenance.** `docs/superpowers/plans/2026-08-01-closeout.md:1088-1104`;
`papers/literature/INDEX.md` (111 papers, every arXiv ID resolved, every PDF title-verified).

**Status: RESOLVED.** Its *procedure* is not logged — see S-26.

---

### S-32 — Does OCCT read `nist_ftc_06` as 47 dimensions / 27 geometric tolerances / 59 datums?

**Answer: YES, exactly.** Reading `nist_ftc_06_asme1_ap242-e2.stp` with `SetGDTMode(True)` then
`Transfer(doc)` and querying `XCAFDoc_DocumentTool.DimTolTool_s` yields **47 / 27 / 59**. No
discrepancy against the published figures.

**Why it needed a run.** The counts were asserted in a test before the data existed, and the ledger
flagged them as unverified through three separate reports until `data/nist_pmi/` was fetched and the
assertion actually executed. That is a spike closing cleanly and it is the model for the rest of this
file.

**Also measured, and now the committed fresh-clone positive control:**
`nist_ctc_01_asme1_ap242-e1.stp`, 396,445 bytes, reads as exactly **21 / 6 / 11**, no OCCT warnings.

**Provenance.** `docs/superpowers/plans/2026-08-01-procedural-generator.md:25-26, 930, 953-959`;
`.superpowers/sdd/2026-08-01-procedural-generator/progress.md:71-75`.

**Status: RESOLVED.** Note the limit: this validates the *reader*, not the *decision* — which is
exactly S-20's problem.

---

### S-33 — Does resizing a numpy `choice()` tuple perturb the corpus?

**Answer: NO — and the brief predicted the opposite, which is why it was measured.** Dropping H7/h6
took `rng.choice(SUPPORTED_FITS)` from four entries to three. The Tier 1 failure rate over seeds 0–199
came back **bit-identical** at all four difficulties (19.5 / 32.9 / 52.9 / 69.1%), and both ladder
guard tests passed with no band widened.

**The mechanism, traced rather than assumed.** `Generator.choice` over a tiny array is one
bounded-integer draw (Lemire's algorithm) from the PCG64 bit stream. For small *n* the rejection
probability is astronomically small, so the call consumes the same number of raw 64-bit words whether
*n* is 3 or 4. The generator state — and therefore every downstream draw in the same assembly — is
unaffected. Tier 1 verdicts never depended on which fit was chosen anyway.

**Standing rule this produced.** *"Do not assume a `choice()` tuple resize shifts the corpus; measure
it."* And the residual, worth keeping: Lemire rejection is not *impossible*, so the invariance is
empirical over one seed set, not proven. The corpus digest is what would catch it.

**Provenance.** `.superpowers/sdd/2026-08-01-pre-registration-prep/progress.md:57-64` and
`task-1-report.md:88, 136`; brief's contrary prediction at `task-1-brief.md:128`.

**Status: RESOLVED.**

---

### S-34 — Does the `.gitattributes` binary rule survive a fresh clone?

**Answer: YES, the rule protects the fixture — and the causal story everyone had was backwards.**
`tests/fixtures/nist_ctc_01_asme1_ap242-e1.stp` clones at **396,445 bytes** under
`core.autocrlf` ∈ {true, input, false}; with the `*.stp binary` line removed it clones at **391,739
bytes**, demonstrated by commenting the line out on a scratch branch and watching the test fail.

**The correction.** The original hypothesis was that `autocrlf=true` causes the corruption. Measurement
reversed it: `autocrlf=true` *hides* a stored corruption on checkout because it self-heals, while
`input` and `false` **expose** it. The intermediate commit `d312ad6` genuinely contains the
391,739-byte CRLF-stripped blob.

**Why it needed a clone.** CRLF normalisation is only observable across a fresh clone, and the PMI
reader returns *identical* counts from the mangled copy — so the positive control passed against the
exact corruption it existed to detect. Only size and hash catch it.

**Provenance.** `docs/superpowers/plans/2026-08-01-closeout.md` Task 7;
`tests/test_gitattributes_clone.py`; `.superpowers/sdd/2026-08-01-closeout/progress.md:181-189`.

**Status: RESOLVED.**

---

### S-35 — Is the reliability mate repair unique?

**Answer: NO — two reviewers produced two different correct-looking repairs, and only a stated
construction rule determines the number.** QA measured **0.9971**; the architect measured **0.9967**
with `hole_a.position_tol = hole_b.position_tol = 0.49965`. Both satisfy "margin = +3.5e-4 under
`min()`". Neither is wrong; the *intent* was under-specified.

**Resolution — decision D-D.** *Each sensitive-band mate has exactly one binding part at ±3.5e-4;
every other part in that mate is slack at ≥10× the band.* Applied to mates [8] and [9] this yields
**mean 0.9975, 95% CI [0.9954, 0.9992], `tested=12`, `excluded=0`** — determined by the rule rather
than chosen. Amendment 2026-08-01f. The rule is asserted, not trusted, by
`test_every_sensitive_mate_has_exactly_one_binding_part`.

**Provenance.** [LR §1, reliability mean]; `.superpowers/closeout/ROUND-2-architect-revised.md:60-64`;
design spec §7 correction 2026-08-01f.

**Status: RESOLVED.** The k-sweep against the repaired instrument is **not** — see S-17.

---

### S-36 — Do the ISO 273 grades move any Tier 1 verdict or the ladder?

**Answer: NO.** Replacing the flat `+0.2/-0.0` clearance-hole tolerance with the standard's per-series
grades (fine H12, medium H13, coarse H14) moves no Tier 1 verdict and does not move the difficulty
ladder. Hole MMC is `nominal + lower_dev` and every clearance hole has `lower_dev = 0.0`, so the
*upper* deviation cannot reach a Tier 1 verdict.

**What it does move, and the silent staleness it created.** Worst-case radius growth at LMC goes
0.100 → 0.215 mm and the required wall 3.550 → 3.780 mm. `_MIN_WALL_MM = 4.0` remains sufficient
(headroom 12.7% → 5.5%) — but `tests/gen/test_layout.py`'s literal floor asserted `>= 3.7`, which is
now *below* the true 3.78 requirement. Neither layout test failed on its own: the derived-floor test
recomputes and still passes, the literal test still passes. **The staleness was silent**, which is
why it was addressed explicitly rather than left.

**Provenance.** `docs/superpowers/plans/2026-08-01-iso273-traceability.md:31-45`. Ladder re-confirmed
at d1 19.5 / d2 32.9 / d3 52.9 / d4 69.1 [LR §1].

**Status: RESOLVED.**

---

### S-37 — Is H7/h6's verdict decided by sampling noise?

**Answer: YES — it was a coin toss wearing a ground-truth label, and it was dropped.** H7/h6 is
line-to-line at MMC: hole minimum and shaft maximum are both exactly the nominal, so exact worst-case
clearance is zero and the Monte Carlo verdict turns on whether any of 100,000 draws lands on the
boundary. Measured across the corpus: **85 True / 23 False** over 108 occurrences, with margins only
ever 1.0 or 0.99999 — one clearance failure in 100k.

**Resolution.** `SUPPORTED_FITS` reduced to `("H7/g6", "H7/k6", "H7/p6")`, pinned by
`test_no_supported_fit_is_line_to_line`, with `test_supported_fits_still_contain_both_verdict_classes`
guarding against leaving the set all-passing or all-failing. See S-33 for what removing it did *not*
do to the corpus.

**Provenance.** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md` Task 1;
`.superpowers/sdd/2026-08-01-procedural-generator/progress.md:328-331`.

**Status: RESOLVED.**

---

### S-38 — Is the ISO-fit boolean fixed by the shaft letter at every size?

**Answer: YES — structurally, as arithmetic, at every diameter.** `montecarlo.py:57` defines
`assembles = yield_frac >= 1.0`, i.e. zero interference anywhere in the tolerance range. For a
hole-basis fit that means `hole_min > shaft_max`; with `hole_min = nominal` (H holes have zero lower
deviation) and `shaft_max = nominal + es`, the verdict is True exactly when `es <= 0` — which *is* the
definition of a clearance-class shaft letter (a–h) versus transition/interference (j–zc).

**Confirmed empirically over nominals 3–180 mm:** `g6` True everywhere, `k6` and `p6` False everywhere.
**Varying the nominal cannot flip it.**

**Consequence, and why it is a disclosure rather than a bug.** Tier 1 carries the boolean; **Tier 2
contributes the clearance *yield***, which does vary usefully (`k6` spans 0.661 at 6 mm to 0.848 at
3 mm). The fact is pinned by `test_iso_fit_verdict_is_fixed_by_the_shaft_letter_at_every_size` so that
nobody later "fixes" the fit set and assumes the leak went away.

**Provenance.** `docs/superpowers/plans/2026-08-01-pre-registration-prep.md:31-37` (the I2 finding).

**Status: RESOLVED.**

---

### S-39 — Does a one-sided floor silently detach from the tree?

**Answer: YES, measured.** `MUTATION_MEASURED = 93.85` sat **2.04 pp below** the tree — four times its
own 0.50 tolerance — and the gate stayed green, because a floor is a lower bound and an improvement is
never flagged. A later commit raised the real score and nobody re-measured. This happened *inside the
layer built to catch the drift class.*

**Resolution.** Both pins are now two-sided via `check_two_sided()`, and the upward message tells the
operator to re-pin rather than merely reporting. The very first real encounter fired correctly — it is
S-16.

**Provenance.** `.superpowers/closeout/ROUND-0-architect-plan.md:13` (F1);
`scripts/check_suite_integrity.py:101-135`; [LR §1, mutation score].

**Status: RESOLVED.** This is the finding that makes S-16 a *control working*, not a regression.

---

### S-40 — Does a per-file Layer 2 test command measure anything?

**Answer: NO.** Scoping cosmic-ray's test command to the single matching test file gave **12 survivors
of 66 (18.2%)** on `types.py`, against **5 of 66 (7.58%)** for the full core subset — because
`checker.py` and `y14_5.py` tests exercise `types.py` heavily. A per-file command inflates survivors
and measures nothing useful.

**Consequence.** `cosmic-ray.toml`'s `test-command` is the whole core subset, with the reason recorded
in the file's own header. [LR §1] records 18.2% as *"a methodology note, never a score for the layer"*.

**Provenance.** `cosmic-ray.toml` header comment (spiked 2026-08-01); [LR §1, mutation score].

**Status: RESOLVED.** Relevant to S-16: the denominator and command must not be quietly re-scoped
during a re-measure.

---

### S-41 — Which mutation tool runs natively on Windows?

**Answer: cosmic-ray.** `mutmut 3.7.0` **refuses** to run natively on Windows and exits directing the
user to WSL. cosmic-ray installs, imports and exposes its CLI natively. Tool chosen on that basis.

**Why it belongs here.** It is the one recorded instance of a platform assumption being tested rather
than assumed, and it is the precedent for Band 2: the development platform is Windows, the deployment
platform is not, and nothing about either has been verified for the GPU toolchain.

**Provenance.** `.superpowers/sdd/2026-08-01-suite-integrity/progress.md:26`.

**Status: RESOLVED.**

---

# Superseded spikes

---

### S-42 — Is anything under `.superpowers/` untracked-and-unignored?

**Asked and answered at `2184485`:** no. `BLOCKERS.md` and `closeout/ROUND-{0,1,2}-*.md` tracked;
`sdd/**` ignored via `.superpowers/sdd/.gitignore` containing a single `*`; nothing
untracked-and-unignored, so no accidental state to clean up.

**SUPERSEDED because the state is being changed.** A session in progress is reversing the nested
ignore to track the SDD ledgers (excluding the regenerable `*.diff` files) with a `README.md` warning
readers not to quote figures from them. **Check `git ls-files .superpowers/sdd` before relying on
either state.** [LR §3]'s table records the pre-reversal measurement.

⚠ **Tooling note for whoever picks this up:** while `.superpowers/sdd/.gitignore` contains `*`, every
ripgrep-based search silently returns **zero hits** for that entire tree. Use plain `grep`, or pass an
explicit no-ignore flag. Searches of the ledgers that came back empty may have been lying.

---

### S-43 — How many Layer 2 survivors are untriaged?

**Asked repeatedly and answered five different ways:** ~12 (unsourced carry-forward), ~17 (40 − 23,
using the pre-correction equivalent count), ~27 (inferred from 95.89 against a 650 denominator), 0
(inferred from 100.00), and **21** (40 measured survivors at run 3 minus 19 corrected documented
equivalents).

**SUPERSEDED by S-16, which owns the current count.** [LR §1] adjudicates: **21 as of run 3 is the
canonical last *enumerated* figure; the count for the current tree is UNKNOWN.** Four of the five
recorded figures are arithmetic over a score, not enumerations — *"An inference from a score is not a
survivor enumeration."* Do not quote any of the five as current.

---

### S-44 — Is the Gate A reliability mean 0.9982 at `tested=11`?

**Asked, answered 0.9982 with `tested=11, excluded=1`, and carried in roughly a dozen ledgers.**

**SUPERSEDED.** It was measured against a defective mate set: `gate_a.py` documented mate[8]'s margin
as a SUM while `y14_5.py` implements ASME B-3's per-part `min()`, so the mate landed at exactly 0.0,
fell in the exclusion band, and was silently dropped. A second mate had the same defect latent,
surviving only because `min()` picked its negative branch. **Canonical: mean 0.9975, 95% CI
[0.9954, 0.9992], fraction of seeds ≥ 0.95 = 0.9700, `tested=12`, `excluded=0`** [LR §1].

⚠ **The superseded figure outnumbers the correct one in a grep.** Standing rule: the pre-registration
must quote the **spec**, never a ledger.

---

# Risk register — spikes whose bad answer has no fallback

A spike with no fallback is a project risk, not an engineering item. Three qualify, and they differ in
kind.

### ⚠ R1 — S-21: no fallback at all, post-timestamp

If Gate A cannot exit 0 as §7 is currently frozen, the only remedy is a **pre-data amendment** filing
D-A and D-B into the frozen table. That is permitted *now* and becomes impermissible the moment the
pre-registration carries a public timestamp. After that point Gate D's first criterion ("Gate A |
Pass") is unmeetable, `scripts/gate_a.py:4` says a skipped criterion is not a pass, and the paper
ships with a blocking gate open. **There is no post-timestamp remedy of any kind.** This is the single
highest-consequence item in the register and it costs twenty minutes to characterise and hours to fix.

### ⚠ R2 — S-01: the fallback expires

Two fallbacks exist — substitute baselines, or revise "≥8" downward pre-data — and **both expire at
the timestamp.** After it, Gate C is unmeetable if fewer than eight models run, and the threshold
cannot be lowered post hoc without invalidating the result. The spike itself is the mitigation: it
must be answered before the freeze, and its cheapest form is twenty minutes. Note the structural
irony recorded in `docs/STATE-OF-PLAY.md`: this is the highest-priority *unblocked* item and nothing
depends on it, which is exactly why it keeps getting deferred.

### ⚠ R3 — S-24, and S-29's R-7: secondary expiring fallbacks

Corpus size and baseline count (S-24) are pre-registration decisions; the published fastener
`lower_dev = -0.1` (S-29, R-7) is frozen benchmark data. Both have adequate fallbacks *before* the
timestamp — reduce scope, or disclose — and none after.

**Not on this list, and why.** S-20's bad answer has three fallbacks (state the limitation; AutoMate
geometry; SolidWorks reframing) — but note that **none of them produces a Gate A PASS**, so S-20 feeds
R1 rather than standing beside it. S-16's three branches each have a fallback. Every Band 2 spike has
a bare-metal or serialised fallback. Every Band 5 spike except S-24 and R-7 has a free fallback,
usually "disclose it".
