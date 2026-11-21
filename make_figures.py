#!/usr/bin/env python3
"""Generate publication-quality figures for v2.7 post-registration report.

Reads v27_diagnostics.npz and v27_diagnostics.json, writes PNG figures to figs/.
"""
import os, json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib import rcParams

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, 'figs')
os.makedirs(FIGDIR, exist_ok=True)

# ── Style ──
rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 200,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
})

# ── Color palette (colorblind-friendly) ──
C_BLUE   = '#2563EB'   # primary blue
C_RED    = '#DC2626'    # red
C_GREEN  = '#059669'    # teal-green
C_ORANGE = '#EA580C'    # orange
C_PURPLE = '#7C3AED'    # purple
C_AMBER  = '#D97706'    # amber
C_PINK   = '#DB2777'    # pink
C_CYAN   = '#0891B2'    # cyan
C_GRAY   = '#6B7280'    # neutral gray

CONFIRMED_COLOR = '#059669'
REFUTED_COLOR   = '#DC2626'

BG_LIGHT = '#FAFAFA'


def load_data():
    with open(os.path.join(HERE, 'v27_diagnostics.json')) as f:
        meta = json.load(f)
    data = dict(np.load(os.path.join(HERE, 'v27_diagnostics.npz')))
    return meta, data


def cv(arr):
    return arr.std(ddof=1) / arr.mean() * 100


def fig_path(name):
    return os.path.join(FIGDIR, name)


# ══════════════════════════════════════════════════════════════
# Figure 1: Variance Decomposition — Stacked bar + annotations
# ══════════════════════════════════════════════════════════════
def fig1_variance_decomposition(data):
    """Stacked horizontal bar: σ²_C vs σ²_S contribution at 17 MeV and 200 MeV."""
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.8), gridspec_kw={'width_ratios': [1, 1]})

    for ax, mass_label, mk in zip(axes, ['17 MeV', '200 MeV'], ['17MeV', '200MeV']):
        sF = data[f'{mk}_F_tag'].std(ddof=1)
        sC = data[f'{mk}_C_tag'].std(ddof=1)
        sS = data[f'{mk}_S_tag'].std(ddof=1)

        frac_C = (sC / sF) ** 2 * 100  # signal-only variance fraction
        frac_S = (sS / sF) ** 2 * 100  # conv-only variance fraction

        ax.barh(['Tag\nVariance'], [frac_S], height=0.5, color=C_RED,
                label=f'Conversion: {frac_S:.1f}%', edgecolor='white', linewidth=1.5)
        ax.barh(['Tag\nVariance'], [frac_C], left=[frac_S], height=0.5, color=C_BLUE,
                label=f'Signal: {frac_C:.1f}%', edgecolor='white', linewidth=1.5)

        # Annotations
        if frac_S > 15:
            ax.text(frac_S / 2, 0, f'{frac_S:.1f}%', ha='center', va='center',
                    color='white', fontweight='bold', fontsize=11)
        if frac_C > 5:
            ax.text(frac_S + frac_C / 2, 0, f'{frac_C:.1f}%', ha='center', va='center',
                    color='white', fontweight='bold', fontsize=11)
        elif frac_C > 0.1:
            ax.annotate(f'{frac_C:.1f}%', xy=(frac_S + frac_C, 0),
                        xytext=(frac_S + frac_C + 8, 0.15),
                        fontsize=9, fontweight='bold', color=C_BLUE,
                        arrowprops=dict(arrowstyle='->', color=C_BLUE, lw=1.2))

        # Dynamic x-limit to show 200 MeV's >100% variance ratio sum
        max_val = frac_S + frac_C
        ax.set_xlim(0, max(110, max_val * 1.15))
        ax.set_xlabel('Fraction of Total Variance (%)')
        ax.set_title(f'm$_a$ = {mass_label}', fontweight='bold')
        ax.legend(loc='upper right', framealpha=0.9, fontsize=8)
        ax.grid(axis='y', visible=False)

    fig.suptitle('Figure 1: Variance Decomposition — Signal vs. Conversion Contribution',
                 fontsize=11, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(fig_path('fig1_variance_decomposition.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 2: Group Comparison — CV bar chart
# ══════════════════════════════════════════════════════════════
def fig2_group_cv_comparison(data):
    """Grouped bar chart: Tag and HV CV for each group."""
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5), sharey=False)

    groups = ['F (Full)', 'C (Fixed-conv)', 'S (Fixed-sig)']
    colors_tag = [C_BLUE, C_GREEN, C_RED]
    colors_hv  = [C_BLUE, C_GREEN, C_RED]

    for ax, mass_label, mk in zip(axes, ['17 MeV', '200 MeV'], ['17MeV', '200MeV']):
        cv_tag = [cv(data[f'{mk}_{g}_tag']) for g in ['F', 'C', 'S']]
        cv_hv  = [cv(data[f'{mk}_{g}_hv'])  for g in ['F', 'C', 'S']]

        x = np.arange(3)
        w = 0.35
        bars_tag = ax.bar(x - w/2, cv_tag, w, color=colors_tag, alpha=0.85,
                          edgecolor='white', linewidth=1.2, label='Tag')
        bars_hv  = ax.bar(x + w/2, cv_hv,  w, color=colors_tag, alpha=0.35,
                          edgecolor='white', linewidth=1.2, label='HV')

        # Add value labels
        for bar, val in zip(bars_tag, cv_tag):
            if val > 0.3:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        f'{val:.2f}%', ha='center', va='bottom', fontsize=7.5,
                        fontweight='bold')
        for bar, val in zip(bars_hv, cv_hv):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{val:.2f}%', ha='center', va='bottom', fontsize=6.5,
                    color=C_GRAY)

        # Add hatching to HV bars to distinguish
        for bar in bars_hv:
            bar.set_hatch('///')

        ax.set_xticks(x)
        ax.set_xticklabels(groups, fontsize=8)
        ax.set_ylabel('Coefficient of Variation (%)')
        ax.set_title(f'm$_a$ = {mass_label}', fontweight='bold')
        ax.legend(fontsize=8)

    fig.suptitle('Figure 2: Seed-to-Seed Variability by Group — Tag (solid) vs. HV (hatched)',
                 fontsize=10, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(fig_path('fig2_group_cv_comparison.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 3: Ensemble Strip Plot — Tag values across seeds
# ══════════════════════════════════════════════════════════════
def fig3_ensemble_strip(data):
    """Strip plot showing all 50 Tag values for each group at 17 MeV."""
    fig, ax = plt.subplots(figsize=(7.5, 3.5))

    groups = {
        'S (Fixed-sig)': ('17MeV_S_tag', C_RED),
        'F (Full)':      ('17MeV_F_tag', C_BLUE),
        'C (Fixed-conv)':('17MeV_C_tag', C_GREEN),
    }

    for i, (label, (key, color)) in enumerate(groups.items()):
        arr = data[key]
        # Jitter y positions
        y_jitter = np.random.RandomState(42).uniform(-0.15, 0.15, len(arr))
        ax.scatter(arr, np.full_like(arr, i) + y_jitter, c=color, s=25, alpha=0.7,
                   edgecolors='white', linewidth=0.5, zorder=3)
        # Mean line
        ax.plot([arr.mean(), arr.mean()], [i - 0.3, i + 0.3], color=color,
                linewidth=2.5, zorder=4)
        # ±1σ band
        ax.axhspan(i - 0.3, i + 0.3, xmin=0, xmax=1, alpha=0, zorder=0)
        m, s = arr.mean(), arr.std(ddof=1)
        ax.fill_betweenx([i - 0.25, i + 0.25], m - s, m + s,
                         color=color, alpha=0.1, zorder=1)
        # Annotation
        ax.text(arr.max() + 0.01, i + 0.25,
                f'CV = {cv(arr):.2f}%', fontsize=8, color=color, fontweight='bold')

    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(list(groups.keys()))
    ax.set_xlabel('Tag Degradation Ratio')
    ax.set_title('Figure 3: 50-Seed Ensemble at 17 MeV — Each Dot is One Seed',
                 fontweight='bold')
    ax.grid(axis='y', visible=False)
    plt.tight_layout()
    fig.savefig(fig_path('fig3_ensemble_strip.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 4: λ Distribution Histogram (pooled) — heavy tails
# ══════════════════════════════════════════════════════════════
def fig4_lambda_distribution(data):
    """Histogram of pooled λ distribution showing heavy tails."""
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.0))

    for ax, mk, mass_label, color in [
        (axes[0], '17MeV', '17 MeV', C_BLUE),
        (axes[1], '200MeV', '200 MeV', C_RED),
    ]:
        lam = data[f'{mk}_pool_lam']
        # Clip for visualization (keep 0.1-99.9 percentile range)
        p01, p999 = np.percentile(lam, [0.1, 99.9])
        lam_clip = lam[(lam >= p01) & (lam <= p999)]

        ax.hist(lam_clip, bins=120, color=color, alpha=0.7, edgecolor='white',
                linewidth=0.3, density=True)

        # Mark percentiles
        for pct, ls in [(1, '--'), (99, '--')]:
            pval = np.percentile(lam, pct)
            if p01 <= pval <= p999:
                ax.axvline(pval, color=C_ORANGE, linestyle=ls, linewidth=1.2, alpha=0.8)
                ax.text(pval, ax.get_ylim()[1] * 0.9, f'{pct}%ile',
                        fontsize=7, color=C_ORANGE, ha='center',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor=C_ORANGE, alpha=0.8))

        from scipy.stats import kurtosis as sp_kurt
        k = sp_kurt(lam, fisher=True)
        ax.text(0.97, 0.85, f'Excess kurtosis\n= {k:.1f}',
                transform=ax.transAxes, ha='right', fontsize=8.5,
                fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                          edgecolor=color, alpha=0.9))

        ax.set_xlabel('λ (log-likelihood ratio)')
        ax.set_ylabel('Density')
        ax.set_title(f'm$_a$ = {mass_label}', fontweight='bold')

    fig.suptitle('Figure 4: Pooled Signal-Vertex λ Distribution — Extreme Heavy Tails',
                 fontsize=10, fontweight='bold', y=1.03)
    plt.tight_layout()
    fig.savefig(fig_path('fig4_lambda_distribution.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 5: 4-Way Vertex Classification — Donut chart
# ══════════════════════════════════════════════════════════════
def fig5_four_way_classification(meta):
    """Donut chart of 4-way vertex classification at D=10mm, 17 MeV."""
    s4w = meta['17MeV']['stats_4w']['10']
    categories = ['Near-edge only', 'Inter-band only', 'Both', 'Neither']
    keys = ['near_only', 'inter_only', 'both', 'neither']
    counts = [s4w[k]['n'] for k in keys]
    colors = [C_ORANGE, C_RED, C_PURPLE, C_CYAN]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5),
                                    gridspec_kw={'width_ratios': [1.2, 1]})

    # Donut
    wedges, texts, autotexts = ax1.pie(
        counts, labels=None, autopct='%1.1f%%',
        colors=colors, startangle=90,
        pctdistance=0.75, wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))
    for t in autotexts:
        t.set_fontsize(8)
        t.set_fontweight('bold')
        t.set_color('white')
    # Center text
    ax1.text(0, 0, f'D = 10 mm\n17 MeV\nN = {sum(counts):,}',
             ha='center', va='center', fontsize=8.5, fontweight='bold', color=C_GRAY)
    ax1.set_title('Vertex Classification', fontweight='bold')

    # Legend + stats table
    ax2.axis('off')
    y_start = 0.92
    headers = ['Group', 'Count', 'Mean λ', 'Kurt']
    col_x = [0.0, 0.42, 0.65, 0.85]
    for j, h in enumerate(headers):
        ax2.text(col_x[j], y_start, h, fontsize=8, fontweight='bold',
                 transform=ax2.transAxes, va='top')

    for i, (cat, key, color) in enumerate(zip(categories, keys, colors)):
        y = y_start - 0.15 * (i + 1)
        ax2.add_patch(plt.Rectangle((col_x[0] - 0.03, y - 0.04), 0.03, 0.08,
                                     transform=ax2.transAxes, color=color, clip_on=False))
        ax2.text(col_x[0] + 0.02, y, cat, fontsize=7.5, transform=ax2.transAxes, va='center')
        ax2.text(col_x[1], y, f"{s4w[key]['n']:,}", fontsize=7.5,
                 transform=ax2.transAxes, va='center')
        mean_val = s4w[key].get('mean', 0)
        kurt_val = s4w[key].get('kurt', 0)
        n = s4w[key]['n']
        if n > 1:
            ax2.text(col_x[2], y, f"{mean_val:.1f}", fontsize=7.5,
                     transform=ax2.transAxes, va='center')
            ax2.text(col_x[3], y, f"{kurt_val:.1f}", fontsize=7.5,
                     transform=ax2.transAxes, va='center')
        else:
            ax2.text(col_x[2], y, '—', fontsize=7.5, transform=ax2.transAxes, va='center')
            ax2.text(col_x[3], y, '—', fontsize=7.5, transform=ax2.transAxes, va='center')

    fig.suptitle('Figure 5: Four-Way Signal-Vertex Classification at D = 10 mm',
                 fontsize=10, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(fig_path('fig5_four_way_classification.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 6: Correlation |R| vs. Distance D
# ══════════════════════════════════════════════════════════════
def fig6_correlation_vs_distance(meta):
    """Line plot: |R(f_near, Tag)| as a function of proximity threshold D."""
    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    D_vals = [1, 2, 5, 10, 20, 50]

    for mk, label, color, marker in [
        ('17MeV', '17 MeV', C_BLUE, 'o'),
        ('200MeV', '200 MeV', C_RED, 's'),
    ]:
        R_vals = [abs(meta[mk]['corr_fn'][str(d)][0]) for d in D_vals]
        p_vals = [meta[mk]['corr_fn'][str(d)][1] for d in D_vals]
        ax.plot(D_vals, R_vals, color=color, marker=marker, markersize=7,
                linewidth=2, label=f'm$_a$ = {label}', zorder=3)

        # Mark significant (p < 0.05)
        for d, r, p in zip(D_vals, R_vals, p_vals):
            if p < 0.05:
                ax.scatter([d], [r], s=120, facecolors='none', edgecolors=color,
                           linewidths=2, zorder=4)

    # Threshold line
    ax.axhline(0.3, color=C_GRAY, linestyle='--', linewidth=1.5, alpha=0.6)
    ax.text(52, 0.31, 'Threshold (N1)', fontsize=8, color=C_GRAY, ha='right')

    ax.set_xscale('log')
    ax.set_xticks(D_vals)
    ax.set_xticklabels([str(d) for d in D_vals])
    ax.set_xlabel('Proximity Threshold D (mm)')
    ax.set_ylabel('|R(f$_{near}$, Tag)|')
    ax.set_ylim(-0.02, 0.5)
    ax.legend()
    ax.set_title('Figure 6: Near-Band Fraction Correlation vs. Distance',
                 fontweight='bold')
    plt.tight_layout()
    fig.savefig(fig_path('fig6_correlation_vs_distance.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 7: Trimmed vs. Winsorised CV — dual line plot
# ══════════════════════════════════════════════════════════════
def fig7_robust_estimators(data):
    """Line plots: CV(%) for Trimmed and Winsorised Tag at each k%."""
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5))

    K_PCT = [0.5, 1.0, 2.0, 5.0, 10.0]

    for ax, mk, mass_label in [
        (axes[0], '17MeV', '17 MeV'),
        (axes[1], '200MeV', '200 MeV'),
    ]:
        cv_tr = []
        cv_wi = []
        for k in K_PCT:
            ks = str(k).replace('.', 'p')
            cv_tr.append(cv(data[f'{mk}_tr_k{ks}']))
            cv_wi.append(cv(data[f'{mk}_wi_k{ks}']))

        # Baseline
        cv_base = cv(data[f'{mk}_F_tag'])
        ax.axhline(cv_base, color=C_GRAY, linestyle=':', linewidth=1.5, alpha=0.5,
                   label=f'Baseline (CV = {cv_base:.2f}%)')

        ax.plot(K_PCT, cv_tr, color=C_GREEN, marker='o', markersize=7, linewidth=2.5,
                label='Trimmed', zorder=3)
        ax.plot(K_PCT, cv_wi, color=C_RED, marker='s', markersize=7, linewidth=2.5,
                label='Winsorised', zorder=3)

        # Fill between to highlight difference
        ax.fill_between(K_PCT, cv_tr, cv_wi, alpha=0.08, color=C_RED,
                        where=[t < w for t, w in zip(cv_tr, cv_wi)])
        ax.fill_between(K_PCT, cv_tr, cv_wi, alpha=0.08, color=C_GREEN,
                        where=[t > w for t, w in zip(cv_tr, cv_wi)])

        # Data labels for key points
        for k_val, t_val, w_val in zip(K_PCT, cv_tr, cv_wi):
            if t_val > 0.01 and mass_label == '17 MeV':
                ax.annotate(f'{t_val:.2f}%', (k_val, t_val),
                            textcoords='offset points', xytext=(8, 5),
                            fontsize=7, color=C_GREEN, fontweight='bold')
            if w_val > 0.1 and mass_label == '17 MeV' and k_val <= 2:
                ax.annotate(f'{w_val:.2f}%', (k_val, w_val),
                            textcoords='offset points', xytext=(8, -12),
                            fontsize=7, color=C_RED, fontweight='bold')

        ax.set_xlabel('Trim/Winsorise Fraction k (%)')
        ax.set_ylabel('CV (%)')
        ax.set_title(f'm$_a$ = {mass_label}', fontweight='bold')
        ax.legend(fontsize=7.5, loc='upper right')
        ax.set_xscale('log')
        ax.set_xticks(K_PCT)
        ax.set_xticklabels([f'{k}%' for k in K_PCT])

    fig.suptitle('Figure 7: Robust Estimator Comparison — Trimming vs. Winsorising',
                 fontsize=10, fontweight='bold', y=1.03)
    plt.tight_layout()
    fig.savefig(fig_path('fig7_robust_estimators.png'))
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
# Figure 8: Prediction Scorecard — horizontal bar / heatmap
# ══════════════════════════════════════════════════════════════
def fig8_prediction_scorecard(meta):
    """Horizontal scorecard: 12 predictions with CONFIRMED/REFUTED coloring."""
    preds = meta['predictions']
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    n = len(preds)
    y_pos = np.arange(n)[::-1]  # reverse so F1 is at top

    colors = [CONFIRMED_COLOR if p['verdict'] == 'CONFIRMED' else REFUTED_COLOR
              for p in preds]

    # Create bars (unit width, colored by verdict)
    bars = ax.barh(y_pos, [1]*n, color=colors, alpha=0.15, edgecolor=colors,
                   linewidth=1.5, height=0.7)

    # Add verdict icons and text
    for i, p in enumerate(preds):
        y = y_pos[i]
        v = p['verdict']
        col = CONFIRMED_COLOR if v == 'CONFIRMED' else REFUTED_COLOR
        icon = '✓' if v == 'CONFIRMED' else '✗'

        # ID badge
        ax.text(-0.05, y, p['id'], fontsize=9, fontweight='bold', ha='right',
                va='center', color=col,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=col, edgecolor=col,
                          alpha=0.15))

        # Verdict icon
        ax.text(0.03, y, icon, fontsize=12, fontweight='bold', ha='left',
                va='center', color=col)

        # Description (truncated)
        desc = p['desc']
        if len(desc) > 60:
            desc = desc[:57] + '...'
        ax.text(0.12, y, desc, fontsize=7.5, ha='left', va='center', color='#333333')

        # Verdict label
        ax.text(0.95, y, v, fontsize=8, fontweight='bold', ha='right',
                va='center', color=col)

    ax.set_xlim(-0.1, 1.05)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(False)

    # Core indicator
    core_ids = {'F1', 'N1', 'N3', 'R1'}
    for i, p in enumerate(preds):
        if p['id'] in core_ids:
            y = y_pos[i]
            ax.plot(-0.08, y, marker='*', markersize=10, color=C_AMBER,
                    clip_on=False, zorder=5)

    # Legend
    conf_patch = mpatches.Patch(color=CONFIRMED_COLOR, alpha=0.6, label='CONFIRMED')
    ref_patch  = mpatches.Patch(color=REFUTED_COLOR,   alpha=0.6, label='REFUTED')
    star_line  = plt.Line2D([0], [0], marker='*', color=C_AMBER, linestyle='',
                            markersize=10, label='Core prediction')
    ax.legend(handles=[conf_patch, ref_patch, star_line], loc='lower right',
              fontsize=8, framealpha=0.9)

    ax.set_title('Figure 8: Prediction Scorecard — 12 Preregistered Predictions',
                 fontweight='bold', fontsize=11)
    plt.tight_layout()
    fig.savefig(fig_path('fig8_prediction_scorecard.png'))
    plt.close(fig)


def generate_all():
    """Generate all figures."""
    print("Loading data...")
    meta, data = load_data()

    print("  Fig 1: Variance Decomposition")
    fig1_variance_decomposition(data)

    print("  Fig 2: Group CV Comparison")
    fig2_group_cv_comparison(data)

    print("  Fig 3: Ensemble Strip Plot")
    fig3_ensemble_strip(data)

    print("  Fig 4: λ Distribution")
    fig4_lambda_distribution(data)

    print("  Fig 5: 4-Way Classification")
    fig5_four_way_classification(meta)

    print("  Fig 6: Correlation vs Distance")
    fig6_correlation_vs_distance(meta)

    print("  Fig 7: Robust Estimators")
    fig7_robust_estimators(data)

    print("  Fig 8: Prediction Scorecard")
    fig8_prediction_scorecard(meta)

    print(f"All figures saved to {FIGDIR}/")
    return FIGDIR


if __name__ == '__main__':
    generate_all()
