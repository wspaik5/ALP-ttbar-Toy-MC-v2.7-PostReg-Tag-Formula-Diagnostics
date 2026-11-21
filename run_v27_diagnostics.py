#!/usr/bin/env python3
"""v2.7 Post-Registration: Tag Formula Diagnostics

Implements the three diagnostic approaches preregistered in v2.7
(DOI: 10.5281/zenodo.24388228):

  A. Frozen-Seed Variance Decomposition  (predictions F1–F4)
  B. Per-Vertex Weight Analysis           (predictions N1–N4)
  C. Robust Estimator Comparison          (predictions R1–R4)

Configuration: E3 (f = 0.25), η = 2.0, 17-band geometry (mtag_v24)
Focus masses: m_a = 17 MeV, 200 MeV
Ensemble: N_seeds = 50, seed formulas per preregistration §4.2

Usage
-----
  python run_v27_diagnostics.py            # full run
  python run_v27_diagnostics.py --test     # single-seed smoke test (3 seeds)

Outputs
-------
  v27_diagnostics.npz   — per-seed and pooled arrays for report generator
  v27_diagnostics.json  — derived statistics, correlations, prediction verdicts
  stdout                — prediction verdicts (CONFIRMED / REFUTED)
"""

import os, sys, time, argparse, json
import numpy as np
from scipy import stats as sp_stats

# ── Environment (must precede endcap_sim import, which reads V16_F) ──
os.environ.setdefault('V16_F', '0.25')

# ── Frozen modules (co-located in frozen/) ──
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, 'frozen'))

import endcap_sim          # simulation engine (frozen v2.5)
import mtag_v24            # 17-band tag formula (frozen v2.4)
import mtag_v22            # 9-band tag, imported by endcap_sim

# Sanity: TGRID must be identical in both tag modules
assert mtag_v22.TGRID == mtag_v24.TGRID, \
    f"TGRID mismatch: v22={mtag_v22.TGRID} vs v24={mtag_v24.TGRID}"

# ═══════════════════════════════════════════════════════════════════
# Constants (preregistration §3)
# ═══════════════════════════════════════════════════════════════════
N_SEEDS    = 50
MASSES     = [0.017, 0.200]                    # GeV
MLABEL     = {0.017: '17 MeV', 0.200: '200 MeV'}
N_SIG_CAP  = 50_000                            # §3 cap (overrides endcap_sim.N_SIG=60000)
N_CONV_CAP = 100_000                           # §3 cap (matches endcap_sim.N_CONV)
K_PCT      = [0.5, 1.0, 2.0, 5.0, 10.0]       # Approach C trim percentages
D_MM       = [1, 2, 5, 10, 20, 50]             # Approach B proximity thresholds [mm]
EPS_GAP    = 1e-12                              # inter-band p_conv threshold §3.2
CFG        = 'E3'
ETA        = 2.0

# Seed formulas (preregistration §4.2)
def sc(i): return 100 * i + 5                  # SEED_CONV(i)
def ss(i): return 100 * i + 11                 # SEED_SIG(i)

# ── 17-band edge positions for Approach B near-edge distance ──
_edges = set()
for _Zd, _, _HWd in mtag_v24.DISKS:
    _edges.add(_Zd - _HWd)
    _edges.add(_Zd + _HWd)
EDGES = np.array(sorted(_edges))               # unique, sorted


# ═══════════════════════════════════════════════════════════════════
# Utility functions
# ═══════════════════════════════════════════════════════════════════

def edge_dist(z):
    """Min |z − edge| over all 17-band edges.  Returns array same shape as z."""
    return np.min(np.abs(np.asarray(z)[:, None] - EDGES[None, :]), axis=1)


def make_keep(lam, base, k):
    """Trimming keep-mask (preregistration §3.3).

    Sorts base-passing λ and removes ⌊k·N/100⌋ from each tail.
    Ties at boundary: vertex with lower index is kept.

    Returns
    -------
    keep : bool array (len = len(lam)), True for vertices to keep
    n_rem : int, number removed from each tail
    lo_bnd, hi_bnd : float or None, boundary λ values for winsorising
    """
    idx   = np.where(base)[0]
    N     = len(idx)
    n_rem = int(np.floor(k * N / 100.0))
    keep  = np.ones(len(lam), bool)
    lo = hi = None
    if n_rem > 0:
        order = np.argsort(lam[idx])
        keep[idx[order[:n_rem]]]  = False          # lower tail
        keep[idx[order[-n_rem:]]] = False           # upper tail
        lo = float(lam[idx[order[n_rem]]])          # first retained (lower)
        hi = float(lam[idx[order[-n_rem - 1]]])     # last retained (upper)
    return keep, n_rem, lo, hi


def make_wins(lam, base, k):
    """Winsorised λ (preregistration §3.3).

    Clips the same tails as make_keep to their boundary values.
    Returns modified λ array (copy).
    """
    idx   = np.where(base)[0]
    N     = len(idx)
    n_rem = int(np.floor(k * N / 100.0))
    out   = lam.copy()
    if n_rem > 0:
        order = np.argsort(lam[idx])
        lo = lam[idx[order[n_rem]]]
        hi = lam[idx[order[-n_rem - 1]]]
        out[idx[order[:n_rem]]]  = lo
        out[idx[order[-n_rem:]]] = hi
    return out


def scan_trimmed(m, sig, bkg, ls, lc, ks, kc, mw=True):
    """scan_tag_endcap with boolean keep-masks (Approach C, Trimmed Tag).

    S0 and lim0 are from the pre-removal population (§3.3).
    """
    TGRID = mtag_v24.TGRID
    S0    = sig['w'][sig['base']].sum()
    lim0  = endcap_sim.upper_limit(S0, 0)
    best  = None

    cands = [(np.ones(len(sig['z']), bool), np.ones(len(bkg['z']), bool))]
    if mw:
        for lo in np.linspace(0, 1.5 * m, 31):
            for hi in (3 * m + 0.01, np.inf):
                cands.append(((sig['m'] > lo) & (sig['m'] < hi),
                              (bkg['m'] > lo) & (bkg['m'] < hi)))
    for t in TGRID:
        ts = np.ones(len(sig['z']), bool) if t is None else (ls >= t)
        tb = np.ones(len(bkg['z']), bool) if t is None else (lc >= t)
        for ms, mb in cands:
            cs = sig['base'] & ks & ts & ms
            cb = bkg['base'] & kc & tb & mb
            S  = sig['w'][cs].sum()
            B  = bkg['w'][cb].sum()
            lim = endcap_sim.upper_limit(S, B)
            if best is None or lim < best['limit']:
                best = dict(limit=lim, deg=lim / lim0, t=t,
                            eff_sig=float(cs.mean() * 100),
                            B=float(B), S=float(S))
    return best


# ═══════════════════════════════════════════════════════════════════
# Generation helper
# ═══════════════════════════════════════════════════════════════════

def _gen(mass, s_sig, s_conv):
    """Generate, subsample, compute Δχ² and λ for one seed pair.

    Uses N_SIG_CAP=50,000 (not endcap_sim.N_SIG=60,000).
    λ computed with mtag_v24 (17-band geometry).
    """
    sig  = endcap_sim.endcap_signal(mass, n=300_000, seed=s_sig,
                                     eta_ref=ETA, config=CFG)
    conv = endcap_sim.endcap_conversions(n=1_500_000, seed=s_conv,
                                          eta_ref=ETA, config=CFG)
    sig,  _ = endcap_sim.subsample(sig,  N_SIG_CAP)
    conv, _ = endcap_sim.subsample(conv, N_CONV_CAP)

    ds, _ = endcap_sim.compute_dchi2_endcap(sig)
    dc, _ = endcap_sim.compute_dchi2_endcap(conv)

    ls = mtag_v24.lam(sig['zm'], sig['sz'], ds)
    lc = mtag_v24.lam(conv['zm'], conv['sz'], dc)

    return sig, conv, ds, dc, ls, lc


# ═══════════════════════════════════════════════════════════════════
# Group F: both seeds vary — full Approach A/B/C diagnostics
# ═══════════════════════════════════════════════════════════════════

def run_F(mass):
    """Run Group F for one mass.  Returns all Approach A, B, C results."""
    tag  = np.zeros(N_SEEDS)
    hv   = np.zeros(N_SEEDS)

    # ── Approach B accumulators ──
    fn   = {D: np.zeros(N_SEEDS) for D in D_MM}     # near-band fraction per seed
    fg   = np.zeros(N_SEEDS)                          # inter-band fraction per seed
    fo   = {D: np.zeros(N_SEEDS) for D in D_MM}     # overlap fraction per seed
    pool_lam   = []          # pooled signal λ (all seeds)
    pool_near  = {D: [] for D in D_MM}
    pool_inter = []

    # ── Approach C accumulators ──
    tr = {k: np.zeros(N_SEEDS) for k in K_PCT}      # trimmed deg per seed
    wi = {k: np.zeros(N_SEEDS) for k in K_PCT}      # winsorised deg per seed

    print(f"  Group F ({MLABEL[mass]}): ", end='', flush=True)

    for i in range(N_SEEDS):
        print(str(i) if i % 10 == 0 else '.', end='', flush=True)

        sig, conv, ds, dc, ls, lc = _gen(mass, ss(i), sc(i))

        # ── Approach A: aggregate Tag and HV ──
        tag[i] = endcap_sim.scan_tag_endcap(mass, sig, conv, ls, lc)['deg']
        hv[i]  = endcap_sim.scan_v15_endcap(mass, sig, conv, ds, dc)['deg']

        # ── Approach B: per-vertex stats (signal vertices, base-passing) ──
        bi   = np.where(sig['base'])[0]
        zm_b = sig['zm'][bi]
        sz_b = sig['sz'][bi]
        lb   = ls[bi]
        Nu   = len(bi)                           # N_used for this seed

        pconv_b  = mtag_v24.p_conv(zm_b, sz_b)
        is_inter = pconv_b < EPS_GAP
        fg[i]    = is_inter.sum() / Nu

        ed = edge_dist(zm_b)
        for D in D_MM:
            is_near = ed < D
            fn[D][i] = is_near.sum() / Nu
            fo[D][i] = (is_near & is_inter).sum() / Nu

        # Accumulate for pooled statistics
        pool_lam.append(lb.copy())
        pool_inter.append(is_inter.copy())
        for D in D_MM:
            pool_near[D].append((ed < D).copy())

        # ── Approach C: trimmed and winsorised scans ──
        for k in K_PCT:
            ks_mask, _, _, _ = make_keep(ls, sig['base'], k)
            kc_mask, _, _, _ = make_keep(lc, conv['base'], k)
            tr[k][i] = scan_trimmed(mass, sig, conv, ls, lc,
                                     ks_mask, kc_mask)['deg']
            wi[k][i] = endcap_sim.scan_tag_endcap(
                mass, sig, conv,
                make_wins(ls, sig['base'], k),
                make_wins(lc, conv['base'], k))['deg']

    print(' done')

    # ── Pooled Approach B statistics ──
    all_lam   = np.concatenate(pool_lam)
    all_inter = np.concatenate(pool_inter)
    Np        = len(all_lam)

    kurt    = float(sp_stats.kurtosis(all_lam, fisher=True))
    kurt_se = np.sqrt(24.0 / Np)

    # 4-way and 2-way λ statistics at each D
    stats_4w = {}
    for D in D_MM:
        an = np.concatenate(pool_near[D])
        ai = all_inter
        groups = dict(near_only=(an & ~ai), inter_only=(~an & ai),
                      both=(an & ai), neither=(~an & ~ai))
        s = {}
        for name, mask in groups.items():
            n = int(mask.sum())
            if n < 2:
                s[name] = dict(n=n, mean=float('nan'), std=float('nan'),
                               skew=float('nan'), kurt=float('nan'))
            else:
                v = all_lam[mask]
                s[name] = dict(n=n,
                               mean=float(np.mean(v)),
                               std=float(np.std(v, ddof=1)),
                               skew=float(sp_stats.skew(v)),
                               kurt=float(sp_stats.kurtosis(v, fisher=True)))
        # Simple 2-way split for prediction N4: near vs far
        s['_near_std'] = (float(all_lam[an].std(ddof=1))
                          if an.sum() > 1 else float('nan'))
        s['_far_std']  = (float(all_lam[~an].std(ddof=1))
                          if (~an).sum() > 1 else float('nan'))
        stats_4w[D] = s

    # Seed-level correlations
    corr_fn = {}
    for D in D_MM:
        r, p = sp_stats.pearsonr(fn[D], tag)
        corr_fn[D] = (float(r), float(p))
    r_fg, p_fg = sp_stats.pearsonr(fg, tag)
    corr_fg = (float(r_fg), float(p_fg))

    return dict(tag=tag, hv=hv,
                fn=fn, fg=fg, fo=fo,
                kurt=kurt, kurt_se=kurt_se, Np=Np,
                stats_4w=stats_4w,
                corr_fn=corr_fn, corr_fg=corr_fg,
                tr=tr, wi=wi,
                pool_lam=all_lam)


# ═══════════════════════════════════════════════════════════════════
# Group C / S: one population fixed — Approach A only
# ═══════════════════════════════════════════════════════════════════

def run_CS(mass, group):
    """Run Group C or S for one mass (Tag and HV only).

    Group C: fixed conv seed=5, signal varies → isolates signal randomness.
    Group S: fixed sig seed=11, conv varies → isolates conversion randomness.
    """
    print(f"  Group {group} ({MLABEL[mass]}): ", end='', flush=True)
    tag = np.zeros(N_SEEDS)
    hv  = np.zeros(N_SEEDS)

    if group == 'C':
        # Prepare fixed conversion population (seed=5, mass-independent)
        conv = endcap_sim.endcap_conversions(n=1_500_000, seed=5,
                                              eta_ref=ETA, config=CFG)
        conv, _ = endcap_sim.subsample(conv, N_CONV_CAP)
        dc, _   = endcap_sim.compute_dchi2_endcap(conv)
        lc      = mtag_v24.lam(conv['zm'], conv['sz'], dc)

        for i in range(N_SEEDS):
            print(str(i) if i % 10 == 0 else '.', end='', flush=True)
            sig = endcap_sim.endcap_signal(mass, n=300_000, seed=ss(i),
                                            eta_ref=ETA, config=CFG)
            sig, _ = endcap_sim.subsample(sig, N_SIG_CAP)
            ds, _  = endcap_sim.compute_dchi2_endcap(sig)
            ls     = mtag_v24.lam(sig['zm'], sig['sz'], ds)
            tag[i] = endcap_sim.scan_tag_endcap(mass, sig, conv, ls, lc)['deg']
            hv[i]  = endcap_sim.scan_v15_endcap(mass, sig, conv, ds, dc)['deg']

    else:  # group == 'S'
        # Prepare fixed signal population (seed=11, mass-DEPENDENT)
        sig = endcap_sim.endcap_signal(mass, n=300_000, seed=11,
                                        eta_ref=ETA, config=CFG)
        sig, _ = endcap_sim.subsample(sig, N_SIG_CAP)
        ds, _  = endcap_sim.compute_dchi2_endcap(sig)
        ls     = mtag_v24.lam(sig['zm'], sig['sz'], ds)

        for i in range(N_SEEDS):
            print(str(i) if i % 10 == 0 else '.', end='', flush=True)
            conv = endcap_sim.endcap_conversions(n=1_500_000, seed=sc(i),
                                                  eta_ref=ETA, config=CFG)
            conv, _ = endcap_sim.subsample(conv, N_CONV_CAP)
            dc, _   = endcap_sim.compute_dchi2_endcap(conv)
            lc      = mtag_v24.lam(conv['zm'], conv['sz'], dc)
            tag[i]  = endcap_sim.scan_tag_endcap(mass, sig, conv, ls, lc)['deg']
            hv[i]   = endcap_sim.scan_v15_endcap(mass, sig, conv, ds, dc)['deg']

    print(' done')
    return dict(tag=tag, hv=hv)


# ═══════════════════════════════════════════════════════════════════
# Verification checks
# ═══════════════════════════════════════════════════════════════════

def verify_seed0(R):
    """Seed-0 consistency (§4.3): all 3 groups identical at i=0."""
    ok = True
    for m in MASSES:
        mk = MLABEL[m]
        for metric in ('tag', 'hv'):
            vF = R[m]['F'][metric][0]
            vC = R[m]['C'][metric][0]
            vS = R[m]['S'][metric][0]
            match = (vF == vC == vS)
            sym = 'OK' if match else 'FAIL'
            print(f"  [{sym}] {mk} {metric.upper()}: "
                  f"F={vF:.10g}  C={vC:.10g}  S={vS:.10g}")
            if not match:
                ok = False
    return ok


def verify_k0(R):
    """k=0 verification (§3.3): trimmed Tag with k=0 == standard Tag."""
    ok = True
    for m in MASSES:
        sig, conv, ds, dc, ls, lc = _gen(m, ss(0), sc(0))
        std_deg  = endcap_sim.scan_tag_endcap(m, sig, conv, ls, lc)['deg']
        ks0      = np.ones(len(ls), bool)
        kc0      = np.ones(len(lc), bool)
        trim_deg = scan_trimmed(m, sig, conv, ls, lc, ks0, kc0)['deg']
        match    = (std_deg == trim_deg)
        sym      = 'OK' if match else 'FAIL'
        print(f"  [{sym}] {MLABEL[m]}: std={std_deg:.10g}, "
              f"trim(k=0)={trim_deg:.10g}")
        if not match:
            ok = False
    return ok


# ═══════════════════════════════════════════════════════════════════
# Prediction evaluation (§5, §7)
# ═══════════════════════════════════════════════════════════════════

def evaluate(R):
    """Evaluate all 12 predictions.

    Returns list of (id, description, verdict, detail_string).
    """
    preds = []
    m17, m200 = 0.017, 0.200

    # ── Approach A: variance decomposition ──
    sF  = R[m17]['F']['tag'].std(ddof=1)
    sC  = R[m17]['C']['tag'].std(ddof=1)    # signal-only variation
    sS  = R[m17]['S']['tag'].std(ddof=1)    # conv-only variation
    sF_hv = R[m17]['F']['hv'].std(ddof=1)
    sC_hv = R[m17]['C']['hv'].std(ddof=1)
    sS_hv = R[m17]['S']['hv'].std(ddof=1)

    r_CF = sC / sF
    r_SF = sS / sF

    # F1: σ_C/σ_F > 0.5
    preds.append(('F1', 'Signal randomness substantial source of Tag sigma',
                  'CONFIRMED' if r_CF > 0.5 else 'REFUTED',
                  f'sigma_C/sigma_F = {r_CF:.4f} (threshold: > 0.5)'))

    # F2: σ_S/σ_F < σ_C/σ_F
    preds.append(('F2', 'Conversion randomness secondary',
                  'CONFIRMED' if r_SF < r_CF else 'REFUTED',
                  f'sigma_S/sigma_F = {r_SF:.4f} vs sigma_C/sigma_F = {r_CF:.4f}'))

    # F3: 0.7 < (σ_C² + σ_S²)/σ_F² < 1.3
    additivity = (sC**2 + sS**2) / sF**2
    preds.append(('F3', 'Variance approximately additive',
                  'CONFIRMED' if 0.7 < additivity < 1.3 else 'REFUTED',
                  f'(sigma_C^2 + sigma_S^2) / sigma_F^2 = {additivity:.4f}'))

    # F4: σ_C(HV)/σ_F(HV) < 1.5 AND σ_S(HV)/σ_F(HV) < 1.5
    rC_hv = sC_hv / sF_hv
    rS_hv = sS_hv / sF_hv
    preds.append(('F4', 'HV insensitive to seed decomposition',
                  'CONFIRMED' if rC_hv < 1.5 and rS_hv < 1.5 else 'REFUTED',
                  f'sigma_C(HV)/sigma_F(HV) = {rC_hv:.4f}, '
                  f'sigma_S(HV)/sigma_F(HV) = {rS_hv:.4f}'))

    # ── Approach B: per-vertex weight ──
    # N1: |R(f_near, Tag)| > 0.3 at D=10mm, 17 MeV
    R10, p10 = R[m17]['F']['corr_fn'][10]
    preds.append(('N1', 'Near-band fraction correlates with Tag',
                  'CONFIRMED' if abs(R10) > 0.3 else 'REFUTED',
                  f'R(f_near, Tag) = {R10:.4f}  (p = {p10:.2e}, D = 10 mm)'))

    # N2: |R| at 200 MeV < |R| at 17 MeV (D=10mm)
    R10_200, _ = R[m200]['F']['corr_fn'][10]
    preds.append(('N2', 'Correlation weaker at 200 MeV',
                  'CONFIRMED' if abs(R10_200) < abs(R10) else 'REFUTED',
                  f'|R|_200 = {abs(R10_200):.4f} vs |R|_17 = {abs(R10):.4f}'))

    # N3: Excess kurtosis > 5 (pooled, 17 MeV)
    ku = R[m17]['F']['kurt']
    preds.append(('N3', 'lambda distribution heavy-tailed',
                  'CONFIRMED' if ku > 5.0 else 'REFUTED',
                  f'Excess kurtosis = {ku:.2f}  (N = {R[m17]["F"]["Np"]})'))

    # N4: σ(λ_near)/σ(λ_far) > 1.5 at D=10mm, 17 MeV (pooled)
    sn = R[m17]['F']['stats_4w'][10]['_near_std']
    sf = R[m17]['F']['stats_4w'][10]['_far_std']
    ratio_nf = sn / sf if (sf and sf > 0) else float('inf')
    preds.append(('N4', 'Near-band lambda variance exceeds far-band',
                  'CONFIRMED' if ratio_nf > 1.5 else 'REFUTED',
                  f'sigma(lam_near)/sigma(lam_far) = {ratio_nf:.4f}  (D = 10 mm)'))

    # ── Approach C: robust estimators ──
    F17  = R[m17]['F']
    F200 = R[m200]['F']

    cv_base = F17['tag'].std(ddof=1) / F17['tag'].mean() * 100  # baseline %

    # R1: σ/mean < 3% at k=1%, 17 MeV (trimmed)
    cv_t1 = F17['tr'][1.0].std(ddof=1) / F17['tr'][1.0].mean() * 100
    preds.append(('R1', 'Trimmed Tag (1%) reduces sigma/mean',
                  'CONFIRMED' if cv_t1 < 3.0 else 'REFUTED',
                  f'sigma/mean = {cv_t1:.2f}%  (baseline = {cv_base:.2f}%)'))

    # R2: σ/mean(wins,1%) > σ/mean(trim,1%)
    cv_w1 = F17['wi'][1.0].std(ddof=1) / F17['wi'][1.0].mean() * 100
    preds.append(('R2', 'Winsorised less effective than trimmed',
                  'CONFIRMED' if cv_w1 > cv_t1 else 'REFUTED',
                  f'sigma/mean: wins = {cv_w1:.2f}% vs trim = {cv_t1:.2f}%'))

    # R3: σ/mean < 1% at k=5%, 17 MeV (trimmed)
    cv_t5 = F17['tr'][5.0].std(ddof=1) / F17['tr'][5.0].mean() * 100
    preds.append(('R3', 'Trimmed Tag (5%) near HV stability',
                  'CONFIRMED' if cv_t5 < 1.0 else 'REFUTED',
                  f'sigma/mean = {cv_t5:.2f}%'))

    # R4: |σ/mean(k=1%) − σ/mean(k=0)| < 0.1% at 200 MeV
    cv0_200 = F200['tag'].std(ddof=1) / F200['tag'].mean() * 100
    cv1_200 = F200['tr'][1.0].std(ddof=1) / F200['tr'][1.0].mean() * 100
    diff200 = abs(cv1_200 - cv0_200)
    preds.append(('R4', 'Trimming negligible at 200 MeV',
                  'CONFIRMED' if diff200 < 0.1 else 'REFUTED',
                  f'|delta(sigma/mean)| = {diff200:.4f}%'))

    return preds


# ═══════════════════════════════════════════════════════════════════
# Save results
# ═══════════════════════════════════════════════════════════════════

def save_results(R, preds, outdir):
    """Save per-seed arrays (.npz) and derived statistics (.json)."""

    # ── NPZ: per-seed arrays ──
    d = {}
    for m in MASSES:
        mk = MLABEL[m].replace(' ', '')         # e.g. '17MeV'
        for grp in ('F', 'C', 'S'):
            d[f'{mk}_{grp}_tag'] = R[m][grp]['tag']
            d[f'{mk}_{grp}_hv']  = R[m][grp]['hv']
        # Approach B per-seed fractions
        for D in D_MM:
            d[f'{mk}_fn_D{D}']   = R[m]['F']['fn'][D]
            d[f'{mk}_fo_D{D}']   = R[m]['F']['fo'][D]
        d[f'{mk}_fg'] = R[m]['F']['fg']
        # Approach C per-seed deg
        for k in K_PCT:
            ks = str(k).replace('.', 'p')
            d[f'{mk}_tr_k{ks}'] = R[m]['F']['tr'][k]
            d[f'{mk}_wi_k{ks}'] = R[m]['F']['wi'][k]
        # Pooled λ (for histograms in report)
        d[f'{mk}_pool_lam'] = R[m]['F']['pool_lam']

    npz_path = os.path.join(outdir, 'v27_diagnostics.npz')
    np.savez_compressed(npz_path, **d)
    print(f"  Arrays saved to {npz_path}")

    # ── JSON: derived statistics and verdicts ──
    meta = dict(
        config=dict(N_SEEDS=N_SEEDS, N_SIG_CAP=N_SIG_CAP,
                     N_CONV_CAP=N_CONV_CAP, CFG=CFG, ETA=ETA,
                     V16_F=os.environ.get('V16_F'),
                     K_PCT=K_PCT, D_MM=D_MM, EPS_GAP=EPS_GAP),
        predictions=[dict(id=pid, desc=desc, verdict=v, detail=det)
                     for pid, desc, v, det in preds],
    )
    for m in MASSES:
        mk = MLABEL[m].replace(' ', '')
        F  = R[m]['F']
        meta[mk] = dict(
            kurt=F['kurt'], kurt_se=F['kurt_se'], Np=F['Np'],
            corr_fn={str(D): list(F['corr_fn'][D]) for D in D_MM},
            corr_fg=list(F['corr_fg']),
            stats_4w={str(D): {
                name: vals for name, vals in F['stats_4w'][D].items()
            } for D in D_MM},
        )

    json_path = os.path.join(outdir, 'v27_diagnostics.json')
    with open(json_path, 'w') as f:
        json.dump(meta, f, indent=2, default=str)
    print(f"  Metadata saved to {json_path}")


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='v2.7 Tag Formula Diagnostics (post-registration)')
    parser.add_argument('--test', action='store_true',
                        help='Quick smoke test with 3 seeds')
    parser.add_argument('--output-dir', default=None,
                        help='Directory for output files (default: script directory)')
    args = parser.parse_args()

    global N_SEEDS
    if args.test:
        N_SEEDS = 3
        # Default smoke-test output to a separate directory to protect 50-seed data
        if args.output_dir is None:
            args.output_dir = os.path.join(_HERE, 'smoke_test_output')
        print("=== SMOKE TEST MODE (3 seeds) ===\n")

    t0 = time.time()

    print("v2.7 Tag Formula Diagnostics — Post-Registration")
    print(f"  Config : {CFG}  |  eta = {ETA}  |  f = {os.environ.get('V16_F')}")
    print(f"  Seeds  : N = {N_SEEDS}")
    print(f"  Caps   : N_sig = {N_SIG_CAP}  |  N_conv = {N_CONV_CAP}")
    print(f"  Masses : {', '.join(MLABEL[m] for m in MASSES)}")
    print(f"  TGRID  : {mtag_v24.TGRID}")
    print(f"  Bands  : {len(mtag_v24.DISKS)} (17-band geometry, mtag_v24)")
    print()

    # ── Run all groups for each mass ──
    R = {}
    for m in MASSES:
        print(f"{'='*60}")
        print(f"  Mass = {MLABEL[m]}")
        print(f"{'='*60}")
        R[m] = {}
        R[m]['F'] = run_F(m)
        R[m]['C'] = run_CS(m, 'C')
        R[m]['S'] = run_CS(m, 'S')

    # ── Verifications ──
    print(f"\n{'='*60}")
    print("  SEED-0 VERIFICATION (prereg section 4.3)")
    print(f"{'='*60}")
    s0_ok = verify_seed0(R)

    print(f"\n{'='*60}")
    print("  k=0 VERIFICATION (prereg section 3.3)")
    print(f"{'='*60}")
    k0_ok = verify_k0(R)

    # ── Evaluate predictions ──
    preds = evaluate(R)

    print(f"\n{'='*60}")
    print("  PREDICTION VERDICTS")
    print(f"{'='*60}")
    for pid, desc, verdict, detail in preds:
        marker = 'PASS' if verdict == 'CONFIRMED' else 'FAIL'
        print(f"  [{marker}] {pid}: {desc}")
        print(f"          {verdict} — {detail}")

    # ── Success criteria (§7) ──
    core_ids = {'F1', 'N1', 'N3', 'R1'}
    n_core = sum(1 for pid, _, v, _ in preds
                 if pid in core_ids and v == 'CONFIRMED')

    print(f"\n{'='*60}")
    print("  SUCCESS CRITERIA (prereg section 7)")
    print(f"{'='*60}")
    print(f"  Core predictions confirmed: {n_core}/4  ({', '.join(sorted(core_ids))})")
    if n_core == 4:
        print("  ==> STRONG diagnostic evidence")
    elif n_core == 3:
        print("  ==> MODERATE diagnostic evidence")
    else:
        print("  ==> WEAK or no diagnostic evidence")

    # ── Summary table ──
    print(f"\n{'='*60}")
    print("  KEY STATISTICS")
    print(f"{'='*60}")
    for m in MASSES:
        mk = MLABEL[m]
        print(f"\n  {mk}:")
        for grp_key, grp_name in [('F','Full'), ('C','Fixed-conv'), ('S','Fixed-sig')]:
            data = R[m][grp_key]
            t = data['tag'];  h = data['hv']
            se_t = t.std(ddof=1) / np.sqrt(N_SEEDS)
            se_h = h.std(ddof=1) / np.sqrt(N_SEEDS)
            cv_t = t.std(ddof=1) / t.mean() * 100
            cv_h = h.std(ddof=1) / h.mean() * 100
            print(f"    {grp_name:12s}  "
                  f"Tag = {t.mean():.4f} +/- {1.96*se_t:.4f}  "
                  f"(CV = {cv_t:.2f}%)  |  "
                  f"HV = {h.mean():.4f} +/- {1.96*se_h:.4f}  "
                  f"(CV = {cv_h:.2f}%)")

        # Approach C summary
        F = R[m]['F']
        print(f"\n    Approach C (trimmed sigma/mean %):")
        header = "    k%     "
        for k in K_PCT:
            header += f"  {k:5.1f}"
        print(header)
        row_t = "    Trimmed "
        row_w = "    Winsor. "
        for k in K_PCT:
            cv_tk = F['tr'][k].std(ddof=1) / F['tr'][k].mean() * 100
            cv_wk = F['wi'][k].std(ddof=1) / F['wi'][k].mean() * 100
            row_t += f"  {cv_tk:5.2f}"
            row_w += f"  {cv_wk:5.2f}"
        print(row_t)
        print(row_w)

    # ── Save ──
    print(f"\n{'='*60}")
    print("  SAVING RESULTS")
    print(f"{'='*60}")
    out = args.output_dir if args.output_dir else _HERE
    if out != _HERE:
        os.makedirs(out, exist_ok=True)
    save_results(R, preds, out)

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    if not s0_ok:
        print("\n*** WARNING: Seed-0 verification FAILED — results may not be "
              "comparable with v2.6 ***")
    if not k0_ok:
        print("\n*** WARNING: k=0 verification FAILED — scan_trimmed logic error ***")

    return R


if __name__ == '__main__':
    main()
