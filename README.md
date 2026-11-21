# ALP-ttbar Toy MC v2.7 — Post-Registration: Tag Formula Diagnostics

**Author:** Won Shik Paik (Independent Researcher, Auckland, New Zealand)  
**Date:** 2026-11-21  
**DOI:** [10.5281/zenodo.24408990](https://doi.org/10.5281/zenodo.24408990)  
**Preregistration DOI:** [10.5281/zenodo.24388228](https://doi.org/10.5281/zenodo.24388228)  
**Previous (v2.6 post-reg):** [10.5281/zenodo.24373115](https://doi.org/10.5281/zenodo.24373115)

---

## Overview

This repository implements the **v2.7 Tag Formula Diagnostics**, a preregistered study investigating why the Tag discriminator's upper-limit degradation ratio exhibits 45× higher seed-to-seed variability than the HV discriminator in a toy Monte Carlo simulation of displaced ALP → e⁺e⁻ searches in tt̄ events.

Three diagnostic approaches are deployed across a 50-seed ensemble at two ALP masses (17 MeV, 200 MeV):

| Approach | Method | Key Question |
|----------|--------|-------------|
| **A** | Frozen-Seed Variance Decomposition | Is signal or conversion randomness dominant? |
| **B** | Per-Vertex Weight Analysis | Do near-band-edge vertices drive instability? |
| **C** | Robust Estimator Comparison | Can trimming/Winsorising stabilise the Tag? |

### Key Findings

1. **99.84% of Tag variance comes from conversion-background randomness** (σ_S/σ_F = 0.9992), not signal randomness (σ_C/σ_F = 0.0432) — the opposite of the preregistered prediction.
2. **Trimming k=1% reduces CV from 5.80% → 0.13%** (45-fold improvement), while **Winsorising worsens it to 7.35%** — a counter-intuitive asymmetry caused by threshold-scan instability.
3. **Excess kurtosis = 44.97** at 17 MeV confirms extremely heavy-tailed λ distribution.
4. **8/12 predictions CONFIRMED, 4/12 REFUTED** — core score 2/4 (weak evidence by preregistered criteria, but the refutations are scientifically informative).

---

## Repository Structure

```
v27_postreg/
├── README.md                          ← This file
├── reproduce.py                       ← One-command reproducibility script
├── run_v27_diagnostics.py             ← Main diagnostics (3 approaches, N=50)
├── run_checkpoint.py                  ← Checkpoint runner (timeout-safe)
├── generate_v27_report.py             ← PDF report generator (ReportLab)
├── frozen/                            ← Frozen simulation modules (DO NOT MODIFY)
│   ├── endcap_sim.py                  ← v2.5 simulation engine
│   ├── mtag_v24.py                    ← v2.4 17-band tag formula
│   └── mtag_v22.py                    ← v2.2 9-band tag formula
├── checkpoints/                       ← Intermediate .pkl files (auto-generated)
│   ├── F17.pkl, F200.pkl              ← Group F results
│   ├── C17.pkl, C200.pkl              ← Group C results
│   └── S17.pkl, S200.pkl              ← Group S results
├── v27_diagnostics.json               ← Full results (predictions + statistics)
├── v27_diagnostics.npz                ← Per-seed arrays (all groups/masses)
└── ALP-ttbar_Toy-MC_v2.7_Post-
    Registration_Tag-Formula-
    Diagnostics-Results_2026-11-21.pdf  ← Final report PDF
```

---

## Quick Start

### Prerequisites

- Python ≥ 3.10
- numpy ≥ 1.24
- scipy ≥ 1.10
- reportlab ≥ 4.0
- matplotlib ≥ 3.7
- DejaVu Sans fonts (usually bundled with matplotlib; also available via `fonts-dejavu-core` on Debian/Ubuntu)

```bash
pip install numpy scipy reportlab matplotlib
```

### Full Reproducibility (recommended)

```bash
python reproduce.py
```

This runs the complete pipeline:
1. **Smoke test** (N=3 seeds, ~30 seconds) — verifies the code runs correctly
2. **Full run** (N=50 seeds, ~15 minutes) — generates `v27_diagnostics.json` and `.npz`
3. **PDF generation** — produces the final report PDF

### Individual Steps

```bash
# Smoke test only
python reproduce.py --smoke

# Full run only (skips smoke test)
python reproduce.py --full

# PDF report only (requires prior full run)
python reproduce.py --pdf

# Verify existing outputs
python reproduce.py --verify
```

### Manual Step-by-Step (if timeouts occur)

```bash
# Run each checkpoint step individually
python run_checkpoint.py F17
python run_checkpoint.py F200
python run_checkpoint.py C17
python run_checkpoint.py C200
python run_checkpoint.py S17
python run_checkpoint.py S200
python run_checkpoint.py EVAL   # merges checkpoints, evaluates predictions

# Generate PDF
python generate_v27_report.py
```

---

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `N_SEEDS` | 50 | Number of ensemble seeds |
| `N_SIG_CAP` | 50,000 | Maximum signal vertices (after base cuts) |
| `N_CONV_CAP` | 100,000 | Maximum conversion vertices (after base cuts) |
| `V16_F` | 0.25 | Material scale factor (E3 config) |
| `η` | 2.0 | Pseudorapidity |
| Geometry | 17-band | 9 sensor disks + 8 service bands |
| `SEED_CONV(i)` | `100i + 5` | Conversion seed formula |
| `SEED_SIG(i)` | `100i + 11` | Signal seed formula |

### Seed Groups

- **Group F (Full):** Both signal and conversion seeds vary — `SEED_SIG(i)`, `SEED_CONV(i)`
- **Group C (Fixed-conv):** Conversion seed fixed at `SEED_CONV(0) = 5` — only signal varies
- **Group S (Fixed-sig):** Signal seed fixed at `SEED_SIG(0) = 11` — only conversion varies

---

## Outputs

### `v27_diagnostics.json`

Complete results including:
- All 12 prediction verdicts with observed values
- Per-mass statistics (kurtosis, correlations, 4-way classification)
- Configuration metadata

### `v27_diagnostics.npz`

Per-seed arrays for all groups and masses:
- `{mass}_{group}_tag` — Tag degradation ratios (shape: [50])
- `{mass}_{group}_hv` — HV degradation ratios (shape: [50])
- `{mass}_tr_k{k}` — Trimmed Tag at each k% (shape: [50])
- `{mass}_wi_k{k}` — Winsorised Tag at each k% (shape: [50])
- `{mass}_fn_D{d}` — Near-edge fractions at each D (shape: [50])
- `{mass}_fg_D{d}` — Inter-band fractions at each D (shape: [50])

### PDF Report

The final PDF report contains:
1. Executive Summary
2. Configuration and Verification
3. Approach A: Frozen-Seed Variance Decomposition
4. Approach B: Per-Vertex Weight Analysis
5. Approach C: Robust Estimator Comparison
6. Prediction Verdicts (12 predictions)
7. Discussion
8. Conclusion
9. Future Directions
10. DOI Chain
11. References (External + Internal)

---

## Verification Checks

Two built-in verification checks confirm implementation correctness:

1. **Seed-0 consistency:** At seed index i = 0, all three groups (F, C, S) use the same seeds, so their Tag and HV values must match to floating-point precision.

2. **k = 0 consistency:** The trimmed Tag at k = 0% (no vertices removed) must reproduce the standard `scan_tag_endcap` result exactly at seed 0.

Both checks are run automatically during the EVAL step and must pass for results to be valid.

---

## Prediction Summary

| ID | Prediction | Verdict | Key Value |
|----|-----------|---------|-----------|
| F1 | σ_C/σ_F > 0.5 (signal contributes substantially) | **REFUTED** | 0.0432 |
| F2 | σ_C/σ_F > σ_S/σ_F (signal > conversion) | **REFUTED** | Reversed |
| F3 | Variance additivity ≈ 1.0 | **CONFIRMED** | 1.0003 |
| F4 | HV ratios both < 1.5 | **CONFIRMED** | Max 1.0000 |
| N1 | \|R(f_near, Tag)\| > 0.3 (near-edge correlation) | **REFUTED** | 0.0934 |
| N2 | \|R\|_200 < \|R\|_17 (mass dependence) | **CONFIRMED** | 0.0828 < 0.0934 |
| N3 | Excess kurtosis > 5 (heavy tails) | **CONFIRMED** | 44.97 |
| N4 | σ(λ_near)/σ(λ_far) > 1.5 (edge dispersion) | **REFUTED** | 1.1889 |
| R1 | Trimmed k=1% CV < 3% | **CONFIRMED** | 0.13% |
| R2 | Winsorised less effective than trimmed | **CONFIRMED** | 7.35% vs 0.13% |
| R3 | Trimmed k=5% CV < 1% | **CONFIRMED** | 0.00% |
| R4 | \|Δ(σ/mean)\|_200 < 0.1% at k=1% | **CONFIRMED** | 0.0468% |

**Core score:** 2/4 (N3, R1 confirmed; F1, N1 refuted) → **Weak diagnostic evidence**

---

## DOI Chain

| Version | DOI | Description |
|---------|-----|-------------|
| v2.7 post-reg | [10.5281/zenodo.24408990](https://doi.org/10.5281/zenodo.24408990) | Tag Formula Diagnostics results (this study) |
| v2.7 prereg | [10.5281/zenodo.24388228](https://doi.org/10.5281/zenodo.24388228) | Tag Formula Diagnostics preregistration |
| v2.6 post-reg | [10.5281/zenodo.24373115](https://doi.org/10.5281/zenodo.24373115) | Multi-Seed Ensemble results |
| v2.6 prereg | [10.5281/zenodo.24361872](https://doi.org/10.5281/zenodo.24361872) | Multi-Seed Ensemble preregistration |
| v2.5 post-reg | [10.5281/zenodo.24341050](https://doi.org/10.5281/zenodo.24341050) | Deconflation results |
| v2.5 prereg | [10.5281/zenodo.24329044](https://doi.org/10.5281/zenodo.24329044) | Deconflation preregistration |
| v2.4 post-reg | [10.5281/zenodo.24302619](https://doi.org/10.5281/zenodo.24302619) | 17-band geometry results |
| v2.4 prereg | [10.5281/zenodo.24296796](https://doi.org/10.5281/zenodo.24296796) | 17-band geometry preregistration |
| v2.3 post-reg | [10.5281/zenodo.24273586](https://doi.org/10.5281/zenodo.24273586) | Endcap tag results |
| v2.3 prereg | [10.5281/zenodo.24244893](https://doi.org/10.5281/zenodo.24244893) | Endcap tag preregistration |
| v2.2 post-reg | [10.5281/zenodo.24238224](https://doi.org/10.5281/zenodo.24238224) | Barrel → endcap results |
| v2.2 prereg | [10.5281/zenodo.24189990](https://doi.org/10.5281/zenodo.24189990) | Barrel → endcap preregistration |
| v2.1 post-reg | [10.5281/zenodo.24136462](https://doi.org/10.5281/zenodo.24136462) | Barrel material-veto results |
| v2.1 prereg | [10.5281/zenodo.24063091](https://doi.org/10.5281/zenodo.24063091) | Barrel material-veto preregistration |
| v2.0 | [10.5281/zenodo.24056097](https://doi.org/10.5281/zenodo.24056097) | Initial barrel study |

---

## Disclaimer

This is an independent personal toy study, not affiliated with the authors of arXiv:2610.38932 or arXiv:2306.08686, nor with the CMS, ATLAS, LHCb or ALICE Collaborations or the FCC study. Detector numbers are assumed; only qualitative trends and ratios are meaningful.

---

## License

This work is provided under the terms of the Creative Commons Attribution 4.0 International License (CC BY 4.0).
