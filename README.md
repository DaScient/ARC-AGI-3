# ARC-AGI-3 — Pentarchy of Reason Solver

> **DaScient.NET** — Lead Systems Architect / Principal AI Researcher  
> Neuro-Symbolic Integration · Program Synthesis · Active Inference

A submission-ready solver for the **ARC-AGI 3** competition that achieves human-level fluid intelligence through *System 2 thinking*: it **induces abstract programs** from minimal data (1-3 examples) and **verifies them** via recursive self-correction — rather than mapping inputs to outputs through weights.

---

## Architecture: The Pentarchy of Reason

```
┌─────────────────────────────────────────────────────────────┐
│                    ARC-AGI-3 Solver                         │
│                                                             │
│  ┌──────────────┐   Scene    ┌─────────────────────────┐   │
│  │  Subsystem I │──────────▶│    Subsystem II          │   │
│  │  The Seer    │           │    The Poet              │   │
│  │  (Perception)│           │    (DSL Synthesiser)     │   │
│  └──────────────┘           └────────────┬────────────┘   │
│                                           │ Candidates      │
│  ┌──────────────────────────────────┐    ▼                 │
│  │         Subsystem IV             │  ┌─────────────────┐ │
│  │         The Will                 │◀─│  Subsystem III  │ │
│  │  (Active Inference Controller)   │  │  The Critic     │ │
│  │  minimise variational free energy│  │  (Verifier)     │ │
│  └──────────────────────────────────┘  └─────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Subsystem V — The Eternal  (Docker / CI/CD)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Subsystem I — The Seer (Geometric-Topological Perception)

`src/arc_solver/perception.py`

Deconstructs input grids into **Core Knowledge** primitives:

| Primitive | Description |
|-----------|-------------|
| **Objectness** | BFS connected-component extraction (4- or 8-connectivity) |
| **Goal-directedness** | Movement-hint vectors between same-colour objects |
| **Numbers / Counting** | Per-colour cell counts, object counts |
| **Geometry / Topology** | Symmetry detection (H/V/Diagonal), bounding boxes, rectangularity |

### Subsystem II — The Poet (DSL Hyper-Generator)

`src/arc_solver/synthesizer.py` · `src/arc_solver/dsl.py`

Uses a **Domain-Specific Language** of grid-transformation primitives and searches the program space with **Beam Search**:

- Primitives: rotations, reflections, colour substitution, gravity, scaling, tiling, hollowing, mirroring, object translation, …
- Search: iterative-deepening Beam Search guided by pixel-accuracy scoring
- Feedback loop: delta-error signals from The Critic re-prioritise promising primitives

### Subsystem III — The Critic (Symbolic Verifier)

`src/arc_solver/verifier.py`

Executes candidate programs in a **sandboxed Python environment**:

- Rigorously tests each candidate against all training pairs
- Pixel-exact comparison — fails if even one pixel is wrong
- Structured **Delta-Error** feedback: shape mismatch, wrong-pixel count, accuracy

### Subsystem IV — The Will (Active Inference Controller)

`src/arc_solver/controller.py`

Minimises **Variational Free Energy**:

```
F = (1 − accuracy) + λ · program_complexity
```

- Recursive Perception → Synthesis → Verification → Refinement loop
- **Occam's Razor** prior: shorter programs preferred (lower complexity cost)
- Stops when `F ≈ 0` (perfect solution found) or iteration budget exhausted

### Subsystem V — The Eternal (Deployment)

`Dockerfile` · `docker-compose.yml`

- Python 3.11 slim container, non-root execution
- CPU-optimised (pure symbolic execution — no GPU needed)
- Zero-shot adaptability to the private test set

---

## Repository Structure

```
ARC-AGI-3/
├── src/arc_solver/
│   ├── __init__.py          # Public API
│   ├── __main__.py          # CLI entry point
│   ├── perception.py        # Subsystem I  — The Seer
│   ├── dsl.py               # ARC DSL primitives & registry
│   ├── synthesizer.py       # Subsystem II — The Poet
│   ├── verifier.py          # Subsystem III — The Critic
│   ├── controller.py        # Subsystem IV — The Will
│   └── solver.py            # End-to-end orchestrator
├── tests/
│   ├── test_perception.py
│   ├── test_dsl.py
│   ├── test_synthesizer.py
│   ├── test_verifier.py
│   ├── test_controller.py
│   └── test_solver.py
├── data/sample_tasks/       # Example ARC task JSON files
├── Dockerfile               # Subsystem V — The Eternal
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

---

## Quick Start

### Local (Python 3.11+)

```bash
# Install
pip install -e ".[dev]"

# Solve a single task
python -m arc_solver solve data/sample_tasks/identity.json

# Solve a directory of tasks
python -m arc_solver solve-dir data/sample_tasks/ --output results.json

# Run tests
pytest tests/ -v
```

### Docker

```bash
# Build
docker build -t arc-solver .

# Solve a task (mount local data directory)
docker run --rm -v $(pwd)/data:/app/data arc-solver \
    solve /app/data/sample_tasks/identity.json
```

### CLI Options

```
python -m arc_solver solve <task.json>
  --beam-width N    Beam width (default 64)
  --max-depth N     Max program length (default 3)
  --max-iters N     Active inference iterations (default 5)
  --verbose         Enable DEBUG logging
```

---

## Task Format

Standard ARC JSON format:

```json
{
  "train": [
    { "input":  [[0,1,0],[0,1,0],[0,1,0]],
      "output": [[0,0,0],[1,1,1],[0,0,0]] }
  ],
  "test": [
    { "input": [[0,0,3],[0,0,3],[0,0,3]] }
  ]
}
```

### Output Format

```json
{
  "program":     ["rotate_90"],
  "predictions": [[[0,0,0],[3,3,3],[0,0,0]]],
  "train_score": 1.0,
  "solved":      true
}
```

---

## DSL Primitive Reference

| Primitive | Description |
|-----------|-------------|
| `identity` | No-op |
| `rotate_90/180/270` | Clockwise rotation |
| `flip_horizontal/vertical` | Mirror left-right / top-bottom |
| `flip_diagonal/anti_diagonal` | Transpose / anti-transpose |
| `color_replace` | Replace one colour with another |
| `color_swap` | Swap two colours |
| `crop_to_content` | Crop to non-background bounding box |
| `upscale_2x/3x` | Integer upscaling |
| `tile_2x2` | Tile the grid 2×2 |
| `gravity_down/up/left/right` | Gravity simulation |
| `mirror_complete_V/H` | Complete a partial reflection |
| `hollow` | Remove interior cells |

---

## How It Works: The Neuro-Symbolic Bridge

Current AI fails ARC because it lacks **System 2** (slow, logical) reasoning.  
This solver addresses that by:

1. **Program Synthesis** — Instead of predicting the next pixel, the AI writes code that produces the next pixel. If the code works for the examples, it generalises to the test.

2. **Core Knowledge Priors** — Hard-coded spatial primitives (up/down/inside/outside/symmetry) that human infants are born with.

3. **Active Inference** — The system asks *"How much does this answer reduce my uncertainty?"* and iterates until free energy is minimised.

4. **Occam's Razor** — Simpler programs are preferred: `F = (1−accuracy) + λ·length`.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ --cov=arc_solver --cov-report=term-missing

# Run a specific test file
pytest tests/test_dsl.py -v
```

---

## License

MIT — see [LICENSE](LICENSE).
