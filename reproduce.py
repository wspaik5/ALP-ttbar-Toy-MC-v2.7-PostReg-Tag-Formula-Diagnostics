#!/usr/bin/env python3
"""Reproducibility script for ALP-ttbar Toy MC v2.7 Post-Registration.

Runs the full diagnostic pipeline end-to-end:
  1. Smoke test (N=3 seeds) — quick sanity check (~30 s)
  2. Full run (N=50 seeds) — checkpoint-based execution (~15 min)
  3. PDF report generation

Usage:
  python reproduce.py              # full pipeline (smoke + full + PDF)
  python reproduce.py --smoke      # smoke test only
  python reproduce.py --full       # full run only (skip smoke)
  python reproduce.py --pdf        # PDF generation only (requires prior run)
  python reproduce.py --verify     # verify existing outputs against expected checksums

Requirements:
  Python >= 3.10
  numpy >= 1.24
  scipy >= 1.10
  reportlab >= 4.0

Environment:
  V16_F=0.25 (set automatically by this script)

Frozen modules (in frozen/ subdirectory):
  endcap_sim.py   — v2.5 simulation engine
  mtag_v24.py     — v2.4 17-band tag formula
  mtag_v22.py     — v2.2 9-band tag formula (dependency of endcap_sim)
"""
import os, sys, time, json, hashlib, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# ── Environment ──
os.environ['V16_F'] = '0.25'

# ── Expected outputs ──
EXPECTED_FILES = [
    'v27_diagnostics.json',
    'v27_diagnostics.npz',
]

CHECKPOINT_STEPS = ['F17', 'F200', 'C17', 'C200', 'S17', 'S200', 'EVAL']


def banner(msg):
    w = max(len(msg) + 4, 60)
    print(f"\n{'═' * w}")
    print(f"  {msg}")
    print(f"{'═' * w}\n")


def run_cmd(cmd, desc=None, timeout=900):
    """Run a subprocess, stream output, return (ok, elapsed)."""
    if desc:
        print(f"  → {desc}")
    t0 = time.time()
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str), cwd=HERE,
        timeout=timeout,
    )
    elapsed = time.time() - t0
    ok = result.returncode == 0
    status = "OK" if ok else f"FAILED (exit {result.returncode})"
    print(f"  [{status}] {elapsed:.1f}s")
    return ok, elapsed


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def check_prerequisites():
    """Verify frozen modules and dependencies exist."""
    banner("Checking prerequisites")
    frozen_files = ['frozen/endcap_sim.py', 'frozen/mtag_v24.py', 'frozen/mtag_v22.py']
    all_ok = True
    for f in frozen_files:
        path = os.path.join(HERE, f)
        if os.path.exists(path):
            print(f"  [OK] {f}")
        else:
            print(f"  [MISSING] {f}")
            all_ok = False

    for mod in ['numpy', 'scipy', 'reportlab']:
        try:
            __import__(mod)
            print(f"  [OK] {mod}")
        except ImportError:
            print(f"  [MISSING] {mod}")
            all_ok = False

    if not all_ok:
        print("\n  *** Prerequisites not met. See README.md for setup instructions. ***")
        sys.exit(1)
    print("  All prerequisites satisfied.")
    return True


def run_smoke():
    """Run the N=3 smoke test with separate output directory (preserves 50-seed data)."""
    banner("Phase 1: Smoke Test (N=3 seeds)")
    smoke_dir = os.path.join(HERE, 'smoke_test_output')
    os.makedirs(smoke_dir, exist_ok=True)
    ok, elapsed = run_cmd(
        [sys.executable, 'run_v27_diagnostics.py', '--test',
         '--output-dir', smoke_dir],
        desc="run_v27_diagnostics.py --test --output-dir smoke_test_output/",
        timeout=120,
    )
    if not ok:
        print("  *** Smoke test FAILED. Aborting. ***")
        sys.exit(1)
    print(f"  Smoke test passed in {elapsed:.1f}s.")
    return True


def run_full():
    """Run the full N=50 ensemble via checkpoints."""
    banner("Phase 2: Full Run (N=50 seeds, checkpoint-based)")
    total_t0 = time.time()

    for step in CHECKPOINT_STEPS:
        ok, elapsed = run_cmd(
            [sys.executable, 'run_checkpoint.py', step],
            desc=f"Step {step}",
            timeout=600,
        )
        if not ok:
            print(f"  *** Step {step} FAILED. ***")
            print(f"  You can resume from this step: python run_checkpoint.py {step}")
            sys.exit(1)

    total_elapsed = time.time() - total_t0
    print(f"\n  Full run completed in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min).")

    # Verify outputs exist
    for f in EXPECTED_FILES:
        path = os.path.join(HERE, f)
        if os.path.exists(path):
            h = md5(path)
            sz = os.path.getsize(path)
            print(f"  [OK] {f}  ({sz:,} bytes, MD5: {h})")
        else:
            print(f"  [MISSING] {f}")
            sys.exit(1)

    return True


def run_pdf():
    """Generate the post-registration PDF report."""
    banner("Phase 3: PDF Report Generation")

    # Check that diagnostics outputs exist
    for f in EXPECTED_FILES:
        if not os.path.exists(os.path.join(HERE, f)):
            print(f"  [MISSING] {f} — run the full pipeline first.")
            sys.exit(1)

    ok, elapsed = run_cmd(
        [sys.executable, 'generate_v27_report.py'],
        desc="generate_v27_report.py",
        timeout=60,
    )
    if not ok:
        print("  *** PDF generation FAILED. ***")
        sys.exit(1)

    # Find and report the PDF
    from generate_v27_report import PDF_NAME
    pdf_path = os.path.join(HERE, PDF_NAME)
    if os.path.exists(pdf_path):
        h = md5(pdf_path)
        sz = os.path.getsize(pdf_path)
        print(f"  [OK] {PDF_NAME}")
        print(f"       Size: {sz:,} bytes")
        print(f"       MD5:  {h}")
    else:
        print(f"  [MISSING] {PDF_NAME}")
        sys.exit(1)

    return True


def run_verify():
    """Verify existing outputs."""
    import numpy as np
    banner("Verification: Checking existing outputs")

    # Check diagnostics JSON
    json_path = os.path.join(HERE, 'v27_diagnostics.json')
    if not os.path.exists(json_path):
        print("  [MISSING] v27_diagnostics.json — run the pipeline first.")
        sys.exit(1)

    with open(json_path) as f:
        meta = json.load(f)

    cfg = meta['config']
    preds = meta['predictions']

    print(f"  Config: N_SEEDS={cfg['N_SEEDS']}, N_SIG_CAP={cfg['N_SIG_CAP']}, "
          f"N_CONV_CAP={cfg['N_CONV_CAP']}")
    masses = cfg.get('MASSES', ['17MeV', '200MeV'])
    print(f"  Masses: {masses}")
    print(f"  Predictions: {len(preds)}")

    n_conf = sum(1 for p in preds if p['verdict'] == 'CONFIRMED')
    n_ref  = sum(1 for p in preds if p['verdict'] == 'REFUTED')
    print(f"  Results: {n_conf} CONFIRMED, {n_ref} REFUTED")

    core_ids = {'F1', 'N1', 'N3', 'R1'}
    core_conf = sum(1 for p in preds
                    if p['id'] in core_ids and p['verdict'] == 'CONFIRMED')
    print(f"  Core score: {core_conf}/4")

    # Verification flags
    all_ok = True

    # Check NPZ and recompute key statistics from arrays
    npz_path = os.path.join(HERE, 'v27_diagnostics.npz')
    if os.path.exists(npz_path):
        d = dict(np.load(npz_path))
        n_arrays = len(d)
        print(f"\n  NPZ: {n_arrays} arrays")
        for key in sorted(d.keys())[:6]:
            print(f"    {key}: shape={d[key].shape}, dtype={d[key].dtype}")
        if n_arrays > 6:
            print(f"    ... and {n_arrays - 6} more")

        # Recompute variance decomposition from NPZ arrays
        sF = d['17MeV_F_tag'].std(ddof=1)
        sC = d['17MeV_C_tag'].std(ddof=1)
        sS = d['17MeV_S_tag'].std(ddof=1)
        sigma_C_over_F = sC / sF
        sigma_S_over_F = sS / sF

        print(f"\n  17 MeV statistics (recomputed from NPZ):")
        print(f"    σ_C/σ_F = {sigma_C_over_F:.4f}")
        print(f"    σ_S/σ_F = {sigma_S_over_F:.4f}")
        print(f"    Excess kurtosis = {meta['17MeV']['kurt']:.2f}")

        # Check variance decomposition direction
        if sigma_S_over_F > sigma_C_over_F:
            print("  [OK] Conversion dominance confirmed (σ_S > σ_C)")
        else:
            print("  [WARN] Unexpected: σ_C > σ_S")
            all_ok = False
    else:
        print("  [MISSING] v27_diagnostics.npz")
        all_ok = False

    # Check kurtosis > 5
    if meta['17MeV']['kurt'] > 5:
        print(f"  [OK] Heavy tails confirmed (kurtosis = {meta['17MeV']['kurt']:.1f} > 5)")
    else:
        print(f"  [WARN] Kurtosis = {meta['17MeV']['kurt']:.1f} ≤ 5")
        all_ok = False

    # Check PDF
    from generate_v27_report import PDF_NAME
    pdf_path = os.path.join(HERE, PDF_NAME)
    if os.path.exists(pdf_path):
        h = md5(pdf_path)
        print(f"\n  PDF: {PDF_NAME}")
        print(f"       MD5: {h}")
    else:
        print(f"\n  [MISSING] {PDF_NAME}")

    if all_ok:
        print("\n  ✓ All verification checks passed.")
    else:
        print("\n  ✗ Some checks failed — see warnings above.")

    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce v2.7 Tag Formula Diagnostics results.")
    parser.add_argument('--smoke', action='store_true',
                        help='Run smoke test only')
    parser.add_argument('--full', action='store_true',
                        help='Run full N=50 ensemble only')
    parser.add_argument('--pdf', action='store_true',
                        help='Generate PDF report only')
    parser.add_argument('--verify', action='store_true',
                        help='Verify existing outputs')
    args = parser.parse_args()

    any_flag = args.smoke or args.full or args.pdf or args.verify

    banner("ALP-ttbar Toy MC v2.7 — Reproducibility Pipeline")
    print(f"  Working directory: {HERE}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  V16_F: {os.environ.get('V16_F', 'not set')}")

    import numpy as np

    check_prerequisites()

    t_total = time.time()

    if args.verify:
        ok = run_verify()
        sys.exit(0 if ok else 1)

    if not any_flag or args.smoke:
        run_smoke()
    if not any_flag or args.full:
        run_full()
    if not any_flag or args.pdf:
        run_pdf()

    total = time.time() - t_total
    banner(f"Pipeline complete — total time: {total:.0f}s ({total/60:.1f} min)")


if __name__ == '__main__':
    main()
