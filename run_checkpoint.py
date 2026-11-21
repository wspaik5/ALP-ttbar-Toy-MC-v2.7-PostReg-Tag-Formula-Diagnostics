#!/usr/bin/env python3
"""Checkpoint runner for v2.7 diagnostics.

Runs one (mass, group) at a time and saves intermediate .npz checkpoints.
Usage:
  python run_checkpoint.py <step>
where step is: F17, F200, C17, C200, S17, S200, EVAL
"""
import os, sys, time, json, pickle
import numpy as np

os.environ.setdefault('V16_F', '0.25')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frozen'))

# Now import the main module
import run_v27_diagnostics as diag

CKPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checkpoints')
os.makedirs(CKPT_DIR, exist_ok=True)

MASS_MAP = {'17': 0.017, '200': 0.200}

def save_ckpt(name, data):
    path = os.path.join(CKPT_DIR, f'{name}.pkl')
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    print(f"  Checkpoint saved: {path}")

def load_ckpt(name):
    path = os.path.join(CKPT_DIR, f'{name}.pkl')
    with open(path, 'rb') as f:
        return pickle.load(f)

def run_step(step):
    t0 = time.time()

    if step.startswith('F'):
        mass = MASS_MAP[step[1:]]
        print(f"\n{'='*60}")
        print(f"  Step {step}: Group F, mass = {diag.MLABEL[mass]}")
        print(f"  N_SEEDS = {diag.N_SEEDS}")
        print(f"{'='*60}")
        result = diag.run_F(mass)
        save_ckpt(step, result)

    elif step.startswith('C') or step.startswith('S'):
        group = step[0]
        mass  = MASS_MAP[step[1:]]
        print(f"\n{'='*60}")
        print(f"  Step {step}: Group {group}, mass = {diag.MLABEL[mass]}")
        print(f"  N_SEEDS = {diag.N_SEEDS}")
        print(f"{'='*60}")
        result = diag.run_CS(mass, group)
        save_ckpt(step, result)

    elif step == 'EVAL':
        print(f"\n{'='*60}")
        print(f"  Step EVAL: merge checkpoints & evaluate")
        print(f"{'='*60}")

        # Reconstruct R dict
        R = {}
        for mk, m in MASS_MAP.items():
            R[m] = {
                'F': load_ckpt(f'F{mk}'),
                'C': load_ckpt(f'C{mk}'),
                'S': load_ckpt(f'S{mk}'),
            }

        # Verification
        print(f"\n  SEED-0 VERIFICATION")
        print(f"  {'─'*50}")
        s0_ok = diag.verify_seed0(R)

        print(f"\n  k=0 VERIFICATION")
        print(f"  {'─'*50}")
        k0_ok = diag.verify_k0(R)

        # Predictions
        preds = diag.evaluate(R)

        print(f"\n  PREDICTION VERDICTS")
        print(f"  {'─'*50}")
        for pid, desc, verdict, detail in preds:
            marker = 'PASS' if verdict == 'CONFIRMED' else 'FAIL'
            print(f"  [{marker}] {pid}: {desc}")
            print(f"          {verdict} — {detail}")

        core_ids = {'F1', 'N1', 'N3', 'R1'}
        n_core = sum(1 for pid, _, v, _ in preds
                     if pid in core_ids and v == 'CONFIRMED')
        print(f"\n  SUCCESS CRITERIA")
        print(f"  {'─'*50}")
        print(f"  Core confirmed: {n_core}/4  ({', '.join(sorted(core_ids))})")
        if n_core == 4:
            print("  ==> STRONG diagnostic evidence")
        elif n_core == 3:
            print("  ==> MODERATE diagnostic evidence")
        else:
            print("  ==> WEAK or no diagnostic evidence")

        # Key statistics
        print(f"\n  KEY STATISTICS")
        print(f"  {'─'*50}")
        for m in diag.MASSES:
            mk = diag.MLABEL[m]
            print(f"\n  {mk}:")
            for grp_key, grp_name in [('F','Full'), ('C','Fixed-conv'), ('S','Fixed-sig')]:
                data = R[m][grp_key]
                t = data['tag'];  h = data['hv']
                N = len(t)
                se_t = t.std(ddof=1) / np.sqrt(N)
                se_h = h.std(ddof=1) / np.sqrt(N)
                cv_t = t.std(ddof=1) / t.mean() * 100
                cv_h = h.std(ddof=1) / h.mean() * 100
                print(f"    {grp_name:12s}  "
                      f"Tag = {t.mean():.4f} +/- {1.96*se_t:.4f}  "
                      f"(CV = {cv_t:.2f}%)  |  "
                      f"HV = {h.mean():.4f} +/- {1.96*se_h:.4f}  "
                      f"(CV = {cv_h:.2f}%)")

            F = R[m]['F']
            print(f"\n    Approach C (trimmed sigma/mean %):")
            header = "    k%     "
            for k in diag.K_PCT:
                header += f"  {k:5.1f}"
            print(header)
            row_t = "    Trimmed "
            row_w = "    Winsor. "
            for k in diag.K_PCT:
                cv_tk = F['tr'][k].std(ddof=1) / F['tr'][k].mean() * 100
                cv_wk = F['wi'][k].std(ddof=1) / F['wi'][k].mean() * 100
                row_t += f"  {cv_tk:5.2f}"
                row_w += f"  {cv_wk:5.2f}"
            print(row_t)
            print(row_w)

        # Save final outputs
        diag.save_results(R, preds, os.path.dirname(os.path.abspath(__file__)))

        if not s0_ok:
            print("\n*** WARNING: Seed-0 verification FAILED ***")
        if not k0_ok:
            print("\n*** WARNING: k=0 verification FAILED ***")

    else:
        print(f"Unknown step: {step}")
        print("Valid steps: F17, F200, C17, C200, S17, S200, EVAL")
        sys.exit(1)

    elapsed = time.time() - t0
    print(f"\n  Step {step} done in {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python run_checkpoint.py <step>")
        print("Steps: F17, F200, C17, C200, S17, S200, EVAL")
        sys.exit(1)
    run_step(sys.argv[1])
