#!/usr/bin/env python3
"""Generate v2.7 post-registration PDF report: Tag Formula Diagnostics Results.

Reads v27_diagnostics.json and v27_diagnostics.npz produced by run_v27_diagnostics.py
and generates the final report PDF.
"""
import os, json, math
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts ──
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Oblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-BoldOblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'))
pdfmetrics.registerFontFamily('DejaVuSans',
                              normal='DejaVuSans', bold='DejaVuSans-Bold',
                              italic='DejaVuSans-Oblique', boldItalic='DejaVuSans-BoldOblique')
pdfmetrics.registerFont(TTFont('DejaVuMono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))

HERE = os.path.dirname(os.path.abspath(__file__))

PDF_NAME = "ALP-ttbar_Toy-MC_v2.7_Post-Registration_Tag-Formula-Diagnostics-Results_2026-11-21.pdf"


def pct(x):
    """Format as percentage string."""
    return f"{x:.2f}%"


def fmt4(x):
    """Format to 4 decimal places."""
    return f"{x:.4f}"


def fmt2(x):
    """Format to 2 decimal places."""
    return f"{x:.2f}"


def build_pdf():
    # ── Load data ──
    with open(os.path.join(HERE, 'v27_diagnostics.json')) as f:
        meta = json.load(f)
    data = np.load(os.path.join(HERE, 'v27_diagnostics.npz'))

    preds = meta['predictions']
    cfg   = meta['config']

    # ── Extract key arrays ──
    F17_tag  = data['17MeV_F_tag']
    F17_hv   = data['17MeV_F_hv']
    C17_tag  = data['17MeV_C_tag']
    C17_hv   = data['17MeV_C_hv']
    S17_tag  = data['17MeV_S_tag']
    S17_hv   = data['17MeV_S_hv']

    F200_tag = data['200MeV_F_tag']
    F200_hv  = data['200MeV_F_hv']
    C200_tag = data['200MeV_C_tag']
    C200_hv  = data['200MeV_C_hv']
    S200_tag = data['200MeV_S_tag']
    S200_hv  = data['200MeV_S_hv']

    N = len(F17_tag)  # 50

    # ── Derived statistics ──
    def cv(arr): return arr.std(ddof=1) / arr.mean() * 100
    def se(arr): return arr.std(ddof=1) / math.sqrt(len(arr))
    def ci95(arr): return 1.96 * se(arr)

    sF  = F17_tag.std(ddof=1)
    sC  = C17_tag.std(ddof=1)
    sS  = S17_tag.std(ddof=1)
    sF_hv = F17_hv.std(ddof=1)
    sC_hv = C17_hv.std(ddof=1)
    sS_hv = S17_hv.std(ddof=1)

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        os.path.join(HERE, PDF_NAME),
        pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle('DocTitle', parent=styles['Title'],
        fontName='DejaVuSans-Bold', fontSize=14, leading=18,
        spaceAfter=6, alignment=TA_CENTER))
    styles.add(ParagraphStyle('Meta', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=8, leading=10,
        textColor=HexColor('#555555'), alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle('Disclaimer', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=7.5, leading=10,
        textColor=HexColor('#666666'),
        leftIndent=10*mm, rightIndent=10*mm,
        spaceBefore=4, spaceAfter=8, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle('SectionHead', parent=styles['Heading1'],
        fontName='DejaVuSans-Bold', fontSize=12, leading=15,
        spaceBefore=14, spaceAfter=6, textColor=HexColor('#1a1a1a')))
    styles.add(ParagraphStyle('SubHead', parent=styles['Heading2'],
        fontName='DejaVuSans-Bold', fontSize=10, leading=13,
        spaceBefore=10, spaceAfter=4, textColor=HexColor('#333333')))
    styles.add(ParagraphStyle('SubSubHead', parent=styles['Heading3'],
        fontName='DejaVuSans-Bold', fontSize=9, leading=12,
        spaceBefore=8, spaceAfter=3, textColor=HexColor('#444444')))
    styles.add(ParagraphStyle('Body', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=9, leading=12,
        spaceAfter=4, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle('SmallBody', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=8, leading=10,
        spaceAfter=3, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle('CodeBlock', parent=styles['Normal'],
        fontName='DejaVuMono', fontSize=7.5, leading=9.5,
        leftIndent=6*mm, spaceAfter=4, backColor=HexColor('#f5f5f5')))
    styles.add(ParagraphStyle('TableCell', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=7.5, leading=9))
    styles.add(ParagraphStyle('RefStyle', parent=styles['Normal'],
        fontName='DejaVuSans', fontSize=7.5, leading=9.5,
        spaceAfter=1, leftIndent=8*mm, firstLineIndent=-8*mm))
    styles.add(ParagraphStyle('FigCaption', parent=styles['Normal'],
        fontName='DejaVuSans-Oblique', fontSize=8, leading=10,
        textColor=HexColor('#444444'), alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=8))

    # ── Generate figures ──
    from make_figures import generate_all as gen_figs, fig_path
    gen_figs()

    story = []

    def S(text, style='Body'):
        story.append(Paragraph(text, styles[style]))
    def head(num, title):
        story.append(Paragraph(f"{num}. {title}", styles['SectionHead']))
    def subhead(title):
        story.append(Paragraph(title, styles['SubHead']))
    def subsubhead(title):
        story.append(Paragraph(title, styles['SubSubHead']))
    def sp(h=2):
        story.append(Spacer(1, h*mm))
    def code(text):
        story.append(Paragraph(text, styles['CodeBlock']))
    def fig(filename, caption, width=160*mm):
        """Insert a figure with caption."""
        img = Image(fig_path(filename), width=width,
                    height=width * 0.5)  # roughly 2:1 aspect
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Paragraph(caption, styles['FigCaption']))

    def make_table(headers, rows, col_widths=None):
        tdata = [headers] + rows
        t = Table(tdata, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('LEADING', (0,0), (-1,-1), 9),
            ('BACKGROUND', (0,0), (-1,0), HexColor('#e8e8e8')),
            ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
            ('GRID', (0,0), (-1,-1), 0.4, HexColor('#cccccc')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t)

    def verdict_color(v):
        return '#228B22' if v == 'CONFIRMED' else '#CC0000'

    def verdict_cell(pred):
        v = pred['verdict']
        col = verdict_color(v)
        return Paragraph(f'<font color="{col}"><b>{v}</b></font>', styles['TableCell'])

    # ══════════════════════════════════════════════════════════════
    # TITLE
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph(
        "ALP-ttbar Toy MC v2.7 — Post-Registration Report:<br/>"
        "Tag Formula Diagnostics in Displaced Light ALP → e<super>+</super>e<super>−</super>",
        styles['DocTitle']))
    story.append(Paragraph(
        "Won Shik Paik (Independent Researcher, Auckland, New Zealand)",
        styles['Meta']))
    story.append(Paragraph("2026-11-21", styles['Meta']))
    story.append(Paragraph(
        "DOI: 10.5281/zenodo.24408990 &nbsp;|&nbsp; "
        "Preregistration: 10.5281/zenodo.24388228 &nbsp;|&nbsp; "
        "Previous: 10.5281/zenodo.24373115 (v2.6 post-reg)",
        styles['Meta']))
    sp(4)
    story.append(Paragraph(
        "<i>Disclaimer.</i> Independent personal toy study, not affiliated with the authors of "
        "arXiv:2610.38932 or arXiv:2306.08686, nor with the CMS, ATLAS, LHCb or ALICE "
        "Collaborations or the FCC study. Detector numbers are assumed; only qualitative "
        "trends and ratios are meaningful.",
        styles['Disclaimer']))

    # ══════════════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════
    head("1", "Executive Summary")

    S("This report presents the results of the v2.7 Tag Formula Diagnostics, "
      "executed according to the preregistered plan (DOI: 10.5281/zenodo.24388228). "
      "The diagnostics investigate why the Tag discriminator's upper-limit degradation "
      "ratio exhibits a coefficient of variation (CV) of 5.80% at m<sub>a</sub> = 17 MeV "
      "across a 50-seed ensemble, compared to only 0.13% for the HV discriminator — "
      "a 45× ratio of variabilities.")

    S("<b>Note on baseline CV.</b> The preregistration cited σ/mean = 7.4% based on the "
      "v2.6 ensemble (N<sub>sig</sub> = 60,000). In this post-registration, the observed "
      "baseline CV is 5.80%. The exact cause of this difference was not investigated: "
      "the v2.6 original per-seed arrays were not retained for cross-comparison. "
      "All 50 seeds in the v2.7 ensemble produce 43,993–44,939 signal vertices after "
      "basic cuts, well below the N<sub>sig</sub> = 50,000 cap, so the cap is never "
      "activated. The diagnostic patterns and prediction thresholds remain unchanged.")

    S("Three key findings emerge:")

    S("<b>(1) Conversion background dominates Tag variance.</b> Frozen-seed variance "
      "decomposition (Approach A) reveals that 99.84% of Tag variance originates from "
      "conversion-vertex randomness, not signal-vertex randomness. Specifically, "
      f"σ<sub>S</sub>/σ<sub>F</sub> = {sS/sF:.4f} (conversion varies) versus "
      f"σ<sub>C</sub>/σ<sub>F</sub> = {sC/sF:.4f} (signal varies). This is the "
      "opposite direction from the preregistered prediction F1, which expected signal "
      "randomness to dominate.")

    S("<b>(2) Trimming is dramatically effective; Winsorising backfires.</b> "
      "Trimming the extreme 1% tails of the per-vertex λ distribution reduces the "
      f"Tag CV from {cv(F17_tag):.2f}% to {cv(data['17MeV_tr_k1p0']):.2f}% — a "
      "45-fold reduction. In contrast, Winsorising the same vertices (replacing their "
      f"λ with boundary values) increases the CV to {cv(data['17MeV_wi_k1p0']):.2f}%, "
      "worse than the untrimmed baseline. This confirms that the extreme-λ vertices "
      "not only inflate the variance but that capping them (rather than removing them) "
      "can paradoxically increase sensitivity to their position in the threshold scan.")

    S("<b>(3) The λ distribution is extremely heavy-tailed.</b> The pooled signal-vertex "
      f"λ distribution has excess kurtosis = {meta['17MeV']['kurt']:.1f} at 17 MeV "
      f"(SE = {meta['17MeV']['kurt_se']:.4f}), confirming that a small fraction of "
      "vertices carry disproportionate weight in the tag formula's threshold optimisation.")

    S(f"Of the 12 preregistered predictions, 8 are CONFIRMED and 4 are REFUTED. "
      f"Of the 4 core predictions (F1, N1, N3, R1), 2 are CONFIRMED (N3, R1) and "
      f"2 are REFUTED (F1, N1), yielding <b>weak diagnostic evidence</b> by the "
      f"preregistered success criterion. However, the REFUTED predictions are highly "
      f"informative: the direction of variance decomposition (conversion-dominated "
      f"rather than signal-dominated) is the most important qualitative finding of "
      f"this study.")

    # ══════════════════════════════════════════════════════════════
    # 2. CONFIGURATION
    # ══════════════════════════════════════════════════════════════
    head("2", "Configuration and Verification")

    subhead("2.1 Run Configuration")

    make_table(
        ['Parameter', 'Value'],
        [
            ['Configuration', 'E3 (f = 0.25)'],
            ['Pseudorapidity', 'η = 2.0'],
            ['Geometry', '17-band (mtag_v24)'],
            ['N<sub>seeds</sub>', '50'],
            ['N<sub>sig</sub> cap', '50,000'],
            ['N<sub>conv</sub> cap', '100,000'],
            ['Focus masses', '17 MeV, 200 MeV'],
            ['Seed formula (conv)', 'SEED_CONV(i) = 100i + 5'],
            ['Seed formula (sig)', 'SEED_SIG(i) = 100i + 11'],
        ],
        col_widths=[80, 200]
    )

    sp(3)

    subhead("2.2 Seed-0 Verification")

    S("The seed-0 consistency check (preregistration §4.3) verifies that seed i = 0 "
      "in all three groups (F, C, S) produces identical Tag and HV degradation ratios "
      "to floating-point precision. All four checks pass:")

    make_table(
        ['Mass', 'Metric', 'F[0]', 'C[0]', 'S[0]', 'Match'],
        [
            ['17 MeV', 'Tag', fmt4(F17_tag[0]), fmt4(C17_tag[0]), fmt4(S17_tag[0]),
             'OK' if F17_tag[0] == C17_tag[0] == S17_tag[0] else 'FAIL'],
            ['17 MeV', 'HV',  fmt4(F17_hv[0]),  fmt4(C17_hv[0]),  fmt4(S17_hv[0]),
             'OK' if F17_hv[0] == C17_hv[0] == S17_hv[0] else 'FAIL'],
            ['200 MeV', 'Tag', fmt4(F200_tag[0]), fmt4(C200_tag[0]), fmt4(S200_tag[0]),
             'OK' if F200_tag[0] == C200_tag[0] == S200_tag[0] else 'FAIL'],
            ['200 MeV', 'HV',  fmt4(F200_hv[0]),  fmt4(C200_hv[0]),  fmt4(S200_hv[0]),
             'OK' if F200_hv[0] == C200_hv[0] == S200_hv[0] else 'FAIL'],
        ],
        col_widths=[40, 30, 55, 55, 55, 30]
    )

    sp(3)

    subhead("2.3 k = 0 Verification")

    S("The trimmed Tag with k = 0 (no vertices removed) reproduces the standard "
      "scan_tag_endcap result exactly at seed 0 for both masses, confirming the "
      "scan_trimmed implementation is correct.")

    # ══════════════════════════════════════════════════════════════
    # 3. APPROACH A RESULTS
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    head("3", "Approach A: Frozen-Seed Variance Decomposition")

    subhead("3.1 Ensemble Statistics")

    rows_A = []
    for mk, m_tag, m_hv, label in [
        ('17 MeV',  [(F17_tag,'F'),(C17_tag,'C'),(S17_tag,'S')],
                     [(F17_hv,'F'), (C17_hv,'C'), (S17_hv,'S')], '17 MeV'),
        ('200 MeV', [(F200_tag,'F'),(C200_tag,'C'),(S200_tag,'S')],
                     [(F200_hv,'F'), (C200_hv,'C'), (S200_hv,'S')], '200 MeV'),
    ]:
        for (t_arr, grp), (h_arr, _) in zip(m_tag, m_hv):
            gname = {'F':'Full','C':'Fixed-conv','S':'Fixed-sig'}[grp]
            rows_A.append([
                mk if grp == 'F' else '',
                f'{gname} ({grp})',
                f'{t_arr.mean():.4f} ± {ci95(t_arr):.4f}',
                pct(cv(t_arr)),
                f'{h_arr.mean():.4f} ± {ci95(h_arr):.4f}',
                pct(cv(h_arr)),
            ])

    make_table(
        ['Mass', 'Group', 'Tag (mean ± 95%CI)', 'Tag CV', 'HV (mean ± 95%CI)', 'HV CV'],
        rows_A,
        col_widths=[35, 55, 80, 35, 80, 35]
    )

    sp(3)

    subhead("3.2 Variance Decomposition")

    S("The variance decomposition reveals a striking and unexpected pattern at "
      "m<sub>a</sub> = 17 MeV:")

    addit = (sC**2 + sS**2) / sF**2
    make_table(
        ['Quantity', 'Value', 'Interpretation'],
        [
            [Paragraph('σ<sub>C</sub>/σ<sub>F</sub>', styles['TableCell']),
             fmt4(sC/sF),
             Paragraph('Signal-only variation: 0.19% of total variance (σ<super>2</super>)',
                       styles['TableCell'])],
            [Paragraph('σ<sub>S</sub>/σ<sub>F</sub>', styles['TableCell']),
             fmt4(sS/sF),
             Paragraph('<b>Conversion-only variation: 99.84% of total variance</b>',
                       styles['TableCell'])],
            [Paragraph('(σ<sub>C</sub><super>2</super>+σ<sub>S</sub><super>2</super>)/'
                       'σ<sub>F</sub><super>2</super>', styles['TableCell']),
             fmt4(addit),
             Paragraph('Variance additivity: near-perfect at 17 MeV (necessary but not sufficient for independence)',
                       styles['TableCell'])],
        ],
        col_widths=[70, 45, 200]
    )

    sp(3)

    S("<b>Key insight.</b> The preregistered prediction F1 expected signal-vertex "
      "randomness to be a substantial source of Tag variance "
      "(σ<sub>C</sub>/σ<sub>F</sub> > 0.5). The observed ratio of 0.043 "
      "decisively refutes this. Instead, nearly all Tag variability originates from "
      "conversion-vertex randomness (Group S, where only conversions vary, "
      f"reproduces CV = {cv(S17_tag):.2f}% ≈ the full Group F CV = {cv(F17_tag):.2f}%).")

    S("This finding implies that the stochastic placement of "
      "<i>conversion background</i> vertices — not signal vertices — relative "
      "to the material bands determines how the optimised λ threshold and mass "
      "window selection performs from seed to seed. When conversions are frozen "
      "(Group C), the Tag becomes nearly deterministic "
      f"(CV = {cv(C17_tag):.2f}%), confirming that signal-vertex variability alone "
      "barely perturbs the optimised limit.")

    fig('fig1_variance_decomposition.png',
        'Figure 1: Variance decomposition at 17 MeV (left) and 200 MeV (right). '
        'At 17 MeV, conversion-background randomness (red) accounts for 99.84% of the total Tag variance, '
        'while signal randomness (blue) contributes only 0.19%. At 200 MeV, the variance ratio sum '
        'exceeds 100% (1.5975), indicating that variance additivity does not hold at this mass. '
        'However, the departure from additivity alone cannot determine whether the signal and '
        'conversion sources are statistically dependent.')

    fig('fig2_group_cv_comparison.png',
        'Figure 2: Seed-to-seed coefficient of variation (CV) for Tag (solid) and HV (hatched) across '
        'the three seed groups. Group S (fixed-sig, where only conversions vary) nearly reproduces Group F\'s '
        'Tag CV, while Group C (fixed-conv) is nearly deterministic — confirming conversion dominance.')

    sp(3)

    S("<b>HV comparison.</b> The HV discriminator's variance decomposition shows "
      f"σ<sub>C</sub>(HV)/σ<sub>F</sub>(HV) = {sC_hv/sF_hv:.4f} and "
      f"σ<sub>S</sub>(HV)/σ<sub>F</sub>(HV) = {sS_hv/sF_hv:.4f}. HV is completely "
      "insensitive to conversion-vertex randomness (σ<sub>S</sub>(HV)/σ<sub>F</sub>(HV) "
      "= 0.0000), and its already-tiny CV originates entirely from signal-vertex "
      "variations. This is consistent with prediction F4 (CONFIRMED): both component "
      "ratios remain below 1.5 (max = 1.0000).")

    subhead("3.3 200 MeV Comparison")

    sF2  = F200_tag.std(ddof=1)
    sC2  = C200_tag.std(ddof=1)
    sS2  = S200_tag.std(ddof=1)
    addit_200 = (sC2**2 + sS2**2) / sF2**2
    S(f"At 200 MeV, the total Tag CV is only {cv(F200_tag):.2f}%, and the decomposition "
      f"shows σ<sub>C</sub>/σ<sub>F</sub> = {sC2/sF2:.4f}, "
      f"σ<sub>S</sub>/σ<sub>F</sub> = {sS2/sF2:.4f}. The variance ratio sum "
      f"(σ<sub>C</sub><super>2</super>+σ<sub>S</sub><super>2</super>)/"
      f"σ<sub>F</sub><super>2</super> = {addit_200:.4f}, substantially exceeding 1.0 — "
      "in contrast to the near-perfect additivity at 17 MeV. This indicates that "
      "variance additivity does not hold at 200 MeV; however, the departure from "
      "additivity alone cannot determine whether the signal and conversion sources "
      "are statistically dependent — it may also reflect nonlinear interactions in "
      "the threshold-scan optimisation. The conversion-dominance pattern observed at "
      "17 MeV is specific to the low-mass regime where the Tag formula's leverage "
      "effect operates.")

    fig('fig3_ensemble_strip.png',
        'Figure 3: Strip plot of all 50 Tag values at 17 MeV. Each dot is one seed. '
        'Group S (red) nearly overlaps Group F (blue), while Group C (green) collapses '
        'to a narrow cluster, visually confirming that conversion randomness — not signal '
        'randomness — drives the spread. Vertical lines mark the group mean; shaded bands '
        'show ±1 standard deviation.')

    # ══════════════════════════════════════════════════════════════
    # 4. APPROACH B RESULTS
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    head("4", "Approach B: Per-Vertex Weight Analysis")

    subhead("4.1 λ Distribution: Pooled Statistics")

    kurt17  = meta['17MeV']['kurt']
    kse17   = meta['17MeV']['kurt_se']
    Np17    = meta['17MeV']['Np']
    kurt200 = meta['200MeV']['kurt']
    kse200  = meta['200MeV']['kurt_se']
    Np200   = meta['200MeV']['Np']

    make_table(
        ['Mass', 'N (pooled)', 'Excess Kurtosis',
         Paragraph('SE(kurt) = √(24/N)', styles['TableCell']),
         Paragraph('95% CI (Gaussian approx.)', styles['TableCell'])],
        [
            ['17 MeV',  f'{Np17:,}',  fmt2(kurt17),
             f'{kse17:.4f}', f'{kurt17-1.96*kse17:.2f} – {kurt17+1.96*kse17:.2f}'],
            ['200 MeV', f'{Np200:,}', fmt2(kurt200),
             f'{kse200:.4f}', f'{kurt200-1.96*kse200:.2f} – {kurt200+1.96*kse200:.2f}'],
        ],
        col_widths=[40, 55, 60, 55, 80]
    )

    S("<i>Note:</i> The standard error √(24/N) and the resulting 95% CI assume a "
      "Gaussian parent distribution, which is not the case here (the extreme kurtosis "
      "confirms heavy tails). These intervals are presented as conventional reference "
      "values only; a bootstrap or simulation-based CI would be more appropriate for "
      "heavy-tailed data. The qualitative conclusion (kurtosis ≫ 5) is unaffected.")

    sp(3)

    S(f"The pooled signal-vertex λ distribution is extremely heavy-tailed at both masses, "
      f"with excess kurtosis ≈ 45 at 17 MeV and ≈ 55 at 200 MeV. These values far "
      f"exceed the preregistered threshold of 5 (N3 CONFIRMED), confirming that a small "
      f"fraction of vertices carry λ values many standard deviations from the mean.")

    fig('fig4_lambda_distribution.png',
        'Figure 4: Pooled signal-vertex λ distribution (clipped to the 0.1–99.9 percentile range '
        'for visibility). Orange dashed lines mark the 1st and 99th percentiles. The extreme heavy '
        'tails (excess kurtosis ~45 at 17 MeV, ~55 at 200 MeV) confirm that a small fraction of '
        'vertices dominate the Tag\'s threshold optimisation.')

    subhead("4.2 Four-Way Vertex Classification")

    S("At D = 10 mm proximity threshold, signal vertices at 17 MeV are classified into "
      "four mutually exclusive groups:")

    s4w = meta['17MeV']['stats_4w']['10']
    total_n = sum(s4w[g]['n'] for g in ['near_only','inter_only','both','neither'])
    make_table(
        ['Group', 'Count', 'Fraction', Paragraph('Mean λ', styles['TableCell']),
         Paragraph('Std(λ)', styles['TableCell']),
         Paragraph('Kurtosis(λ)', styles['TableCell'])],
        [
            ['Near-edge only', f"{s4w['near_only']['n']:,}",
             pct(s4w['near_only']['n']/total_n*100),
             fmt2(s4w['near_only']['mean']), fmt2(s4w['near_only']['std']),
             fmt2(s4w['near_only']['kurt'])],
            ['Inter-band only', f"{s4w['inter_only']['n']:,}",
             pct(s4w['inter_only']['n']/total_n*100),
             fmt2(s4w['inter_only']['mean']), fmt2(s4w['inter_only']['std']),
             fmt2(s4w['inter_only']['kurt'])],
            ['Both', f"{s4w['both']['n']:,}",
             pct(s4w['both']['n']/total_n*100),
             fmt2(s4w['both']['mean']) if s4w['both']['n'] > 1 else '—',
             fmt2(s4w['both']['std']) if s4w['both']['n'] > 1 else '—',
             fmt2(s4w['both']['kurt']) if s4w['both']['n'] > 1 else '—'],
            ['Neither', f"{s4w['neither']['n']:,}",
             pct(s4w['neither']['n']/total_n*100),
             fmt2(s4w['neither']['mean']), fmt2(s4w['neither']['std']),
             fmt2(s4w['neither']['kurt'])],
        ],
        col_widths=[55, 50, 40, 45, 45, 45]
    )

    sp(3)

    S("The inter-band-only group (signal vertices in gaps where p<sub>conv</sub> < "
      f"10<super>−12</super>) dominates at {s4w['inter_only']['n']/total_n*100:.1f}% of all "
      f"signal vertices, with the highest mean λ ({fmt2(s4w['inter_only']['mean'])}) and "
      f"substantial spread (std = {fmt2(s4w['inter_only']['std'])}). Near-edge-only vertices "
      f"show lower mean λ but comparable kurtosis. The 'both' category has "
      f"{s4w['both']['n']:,} vertices at D = 10 mm. Note that this classification applies to "
      f"<i>signal</i> vertices; the Approach A finding that <i>conversion</i> randomness "
      f"dominates Tag variance is a separate result that is not explained by this "
      f"spatial classification.")

    fig('fig5_four_way_classification.png',
        'Figure 5: Four-way signal-vertex classification at D = 10 mm (17 MeV). '
        'The donut chart (left) shows the fraction of signal vertices in each spatial '
        'category. The table (right) summarises count, mean λ, and kurtosis per group. '
        'Inter-band signal vertices dominate and carry the highest mean λ.')

    subhead("4.3 Near-Band-Edge vs. Far-Band σ(λ) Ratio")

    near_std = s4w['_near_std']
    far_std  = s4w['_far_std']
    ratio_nf = near_std / far_std

    S(f"At D = 10 mm, σ(λ<sub>near</sub>) = {fmt2(near_std)} vs. "
      f"σ(λ<sub>far</sub>) = {fmt2(far_std)}, giving a ratio of {ratio_nf:.4f}. "
      f"This falls short of the preregistered threshold of 1.5 (N4 REFUTED). "
      f"The moderate ratio suggests that while near-band vertices do show slightly "
      f"higher λ dispersion, the effect is not concentrated at band edges alone. "
      f"High-λ signal vertices are distributed broadly across the inter-band gap "
      f"regions rather than narrowly clustered near edges.")

    subhead("4.4 Seed-Level Correlations")

    corr_17  = meta['17MeV']['corr_fn']
    corr_200 = meta['200MeV']['corr_fn']

    corr_rows = []
    for D in ['1','2','5','10','20','50']:
        r17, p17 = corr_17[D]
        r200, p200 = corr_200[D]
        corr_rows.append([
            f'{D} mm',
            f'{r17:.4f}', f'{p17:.2e}',
            f'{r200:.4f}', f'{p200:.2e}',
        ])
    make_table(
        ['D', 'R (17 MeV)', 'p (17 MeV)', 'R (200 MeV)', 'p (200 MeV)'],
        corr_rows,
        col_widths=[30, 50, 50, 50, 50]
    )

    sp(3)

    cfg_fg17 = meta['17MeV']['corr_fg']
    cfg_fg200 = meta['200MeV']['corr_fg']
    S(f"No significant correlation between near-band-edge fraction and Tag is observed "
      f"at any proximity threshold (all p > 0.05). At D = 10 mm, "
      f"R = {corr_17['10'][0]:.4f} (p = {corr_17['10'][1]:.2e}), well below the "
      f"threshold of |R| > 0.3 (N1 REFUTED). The inter-band fraction correlation is "
      f"also non-significant: R = {cfg_fg17[0]:.4f} (p = {cfg_fg17[1]:.2e}).")

    S("The lack of seed-level correlation, despite the confirmed heavy tails (N3), "
      "is an important finding. It indicates that Tag variability is not driven by "
      "how many signal vertices land near band edges in a given seed. The Approach A "
      "finding that conversion-vertex randomness dominates is a separate, complementary "
      "result: the specific mechanism by which conversion randomness affects the Tag "
      "threshold scan was not investigated in this study and remains an open question.")

    fig('fig6_correlation_vs_distance.png',
        'Figure 6: Pearson |R(f_near, Tag)| as a function of proximity threshold D. '
        'Both masses remain well below the preregistered threshold of 0.3 (grey dashed line) '
        'at all distance scales, confirming N1 REFUTED. No circled points (p < 0.05) appear, '
        'indicating that the near-band fraction is not a significant predictor of Tag at any D.',
        width=120*mm)

    # ══════════════════════════════════════════════════════════════
    # 5. APPROACH C RESULTS
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    head("5", "Approach C: Robust Estimator Comparison")

    subhead("5.1 Trimmed vs. Winsorised Tag")

    K_PCT = cfg['K_PCT']
    rows_C = []
    for k in K_PCT:
        ks = str(k).replace('.','p')
        tr_arr = data[f'17MeV_tr_k{ks}']
        wi_arr = data[f'17MeV_wi_k{ks}']
        rows_C.append([
            f'{k}%',
            f'{tr_arr.mean():.4f}',
            pct(cv(tr_arr)),
            f'{wi_arr.mean():.4f}',
            pct(cv(wi_arr)),
        ])
    make_table(
        ['k', 'Trim mean', 'Trim CV', 'Wins mean', 'Wins CV'],
        rows_C,
        col_widths=[30, 55, 55, 55, 55]
    )

    sp(3)

    cv_base = cv(F17_tag)
    cv_t1 = cv(data['17MeV_tr_k1p0'])
    cv_w1 = cv(data['17MeV_wi_k1p0'])

    S(f"<b>Trimming at k = 1%</b> reduces the Tag CV from {cv_base:.2f}% to "
      f"{cv_t1:.2f}% — a {cv_base/cv_t1:.0f}-fold improvement. "
      f"This confirms prediction R1 (σ/mean < 3%) and demonstrates that removing "
      f"just the most extreme 2% of λ vertices (1% per tail) is sufficient to "
      f"almost entirely eliminate the seed-to-seed variance amplification.")

    wi_arr = data['17MeV_wi_k1p0']
    seed28_wi = wi_arr[28]
    wi_excl = np.delete(wi_arr, 28)
    cv_wi_excl = wi_excl.std(ddof=1) / wi_excl.mean() * 100

    S(f"<b>Winsorising at k = 1%</b> not only fails to stabilise the Tag but "
      f"<i>increases</i> the CV to {cv_w1:.2f}%, worse than the untrimmed "
      f"baseline. Prediction R2 (Winsorised less effective than Trimmed) is CONFIRMED. "
      f"The elevated CV is concentrated in seed 28: its winsorised Tag value "
      f"({seed28_wi:.4f}) is the ensemble maximum, with the clipping upper bound "
      f"(25.00384) exceeding the scan threshold (25). Excluding seed 28 alone "
      f"reduces the winsorised CV to {cv_wi_excl:.4f}%.")

    S("The mechanism appears to be as follows: Winsorising replaces outlier λ values "
      "with the boundary value, which shifts many vertices to exactly the same λ. "
      "Because scan_tag_endcap optimises over λ thresholds, clustering many vertices "
      "at the boundary creates a sharp step in the threshold-scan curve. Small changes "
      "in the threshold can then include or exclude a large block of vertices at once, "
      "amplifying the seed-to-seed variation in the optimised limit.")

    cv_t5 = cv(data['17MeV_tr_k5p0'])
    S(f"<b>At k = 5%</b>, the trimmed Tag achieves CV = {cv_t5:.2f}%, consistent "
      f"with prediction R3 (σ/mean < 1%).")

    fig('fig7_robust_estimators.png',
        'Figure 7: CV (%) for Trimmed (green) and Winsorised (red) Tag estimators across '
        'k% values. At 17 MeV (left), trimming rapidly stabilises the Tag while Winsorising '
        'initially worsens it — the shaded region highlights this dramatic divergence. '
        'At 200 MeV (right), both estimators converge quickly to near-zero CV, confirming '
        'the mass-specific nature of the leverage effect. Grey dotted line: untrimmed baseline.')

    subhead("5.2 200 MeV Comparison")

    cv0_200 = cv(F200_tag)
    cv1_200 = cv(data['200MeV_tr_k1p0'])
    diff_200 = abs(cv1_200 - cv0_200)

    rows_C200 = []
    for k in K_PCT:
        ks = str(k).replace('.','p')
        tr_arr = data[f'200MeV_tr_k{ks}']
        wi_arr = data[f'200MeV_wi_k{ks}']
        rows_C200.append([
            f'{k}%',
            pct(cv(tr_arr)),
            pct(cv(wi_arr)),
        ])
    make_table(
        ['k', 'Trim CV (200 MeV)', 'Wins CV (200 MeV)'],
        rows_C200,
        col_widths=[30, 70, 70]
    )

    sp(3)

    S(f"At 200 MeV, the baseline CV is {cv0_200:.2f}% and trimming at k = 1% "
      f"changes it to {cv1_200:.2f}% (|Δ| = {diff_200:.4f}% < 0.1%), "
      f"confirming R4. The low-mass leverage effect is mass-specific.")

    # ══════════════════════════════════════════════════════════════
    # 6. PREDICTION VERDICTS
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    head("6", "Prediction Verdicts")

    pred_rows = []
    for p in preds:
        pred_rows.append([
            p['id'],
            Paragraph(p['desc'], styles['TableCell']),
            verdict_cell(p),
            Paragraph(p['detail'], styles['TableCell']),
        ])

    make_table(
        ['ID', 'Prediction', 'Verdict', 'Observed Value'],
        pred_rows,
        col_widths=[20, 85, 50, 160]
    )

    sp(4)

    n_conf = sum(1 for p in preds if p['verdict'] == 'CONFIRMED')
    n_ref  = sum(1 for p in preds if p['verdict'] == 'REFUTED')
    core_conf = sum(1 for p in preds
                    if p['id'] in {'F1','N1','N3','R1'} and p['verdict'] == 'CONFIRMED')

    S(f"<b>Summary:</b> {n_conf} CONFIRMED, {n_ref} REFUTED out of 12 predictions.")

    S(f"<b>Success criterion (§7 of preregistration):</b> Core predictions "
      f"confirmed: {core_conf}/4 (F1, N1, N3, R1). "
      f"This yields <b>weak diagnostic evidence</b> by the preregistered standard. "
      f"However, the REFUTED predictions are themselves informative — the variance "
      f"decomposition direction (conversion-dominated) is the most consequential finding.")

    fig('fig8_prediction_scorecard.png',
        'Figure 8: Visual scorecard of all 12 preregistered predictions. Green bars indicate '
        'CONFIRMED, red bars REFUTED. Star markers (★) denote the 4 core predictions '
        '(F1, N1, N3, R1). The 2/4 core score classifies the evidence as weak, but the '
        'refuted predictions (F1, N1) are the most scientifically informative.',
        width=160*mm)

    # ══════════════════════════════════════════════════════════════
    # 7. DISCUSSION
    # ══════════════════════════════════════════════════════════════
    head("7", "Discussion")

    subhead("7.1 Why Conversion Variance Dominates")

    S("The preregistration's leverage-effect hypothesis correctly identified "
      "extreme-λ vertices as the driver of Tag variability (confirmed by N3 and R1). "
      "However, it incorrectly attributed this to signal-vertex randomness. The data "
      "show that the dominant mechanism operates through the conversion background:")

    S("(a) <b>Background yield B matters more than signal yield S.</b> "
      "The upper-limit formula is lim = max(3, 2√B)/S. For the optimal Tag cut, B is "
      "typically small but nonzero. Because lim is proportional to √B when B > 2.25, "
      "fluctuations in B from seed to seed directly modulate the optimised limit. "
      "Conversion vertices whose λ values fall near the optimal threshold boundary are "
      "the likely source: small shifts in the conversion-background λ distribution from "
      "seed to seed shift B substantially. The specific conversion-vertex property "
      "responsible was not isolated in this study (see (c) below).")

    S("(b) <b>Signal vertices are robust because signal λ is dominated by "
      "Δχ<super>2</super>.</b> Signal vertices from genuine ALP decays typically have "
      "poor vertex-fit quality (large Δχ<super>2</super>), which pushes their λ to "
      "high positive values regardless of their z position. This makes the signal "
      "yield S relatively insensitive to the specific z locations of signal vertices, "
      "and hence to the signal seed.")

    S("(c) <b>The specific conversion-side mechanism is not fully established.</b> "
      "While Approach A conclusively demonstrates conversion dominance, the precise "
      "mechanism by which conversion randomness propagates to Tag instability was not "
      "isolated in this study. Up to 100,000 conversion vertices are retained per seed "
      "(a cap; the actual count was 58,669–59,687 after basic cuts). Among these, no "
      "vertices with p<sub>conv</sub> &lt; 10<super>−12</super> were observed, so the "
      "inter-band p<sub>conv</sub> → 0 mechanism that produces extreme λ in "
      "<i>signal</i> vertices does not apply to the conversion side. The conversion-side "
      "cause remains an open question. Further investigation — for example, decomposing "
      "the per-seed background yield B at the optimal Tag threshold — would be needed "
      "to identify the conversion-vertex property that drives the seed-to-seed variation.")

    subhead("7.2 Why Winsorising Backfires")

    S("The Winsorising result (R2 CONFIRMED with CV increasing rather than decreasing) "
      "deserves explanation. When outlier λ values are replaced by the boundary "
      "λ at the trimming cutoff, many vertices are assigned exactly that boundary value. "
      "In the threshold scan, the optimal t may fall near this boundary, so the transition "
      "from 'most boundary vertices pass' to 'most boundary vertices fail' happens over "
      "a very narrow threshold range. This creates instability: seeds that happen to place "
      "the boundary λ just above or just below the optimal t see sharply different B values, "
      "amplifying seed-to-seed variation.")

    S("Trimming avoids this by removing the vertices entirely, so they never participate "
      "in any threshold scan candidate. The t = None entry in TGRID (which applies no "
      "λ cut) also does not see the removed vertices, because trimming uses a boolean "
      "mask that excludes them from all candidates.")

    subhead("7.3 Synthesis: A Revised Picture of Tag Variability")

    S("Combining all three approaches, a coherent picture of Tag variability emerges "
      "that differs substantially from the preregistered hypothesis:")

    S("The preregistered model posited that signal-vertex randomness, amplified by "
      "a leverage effect at material-band edges, was the primary source of Tag "
      "instability. This predicted strong signal-variance contribution (F1), "
      "significant near-edge correlation (N1), and heavy-tailed λ (N3), with "
      "trimming as a corrective (R1).")

    S("The observed picture is simpler but less intuitive: conversion-background "
      "randomness alone accounts for 99.84% of Tag variance at 17 MeV. The λ "
      "distribution is indeed heavy-tailed (N3 CONFIRMED) and trimming is indeed "
      "effective (R1 CONFIRMED), but the variance originates from conversion "
      "randomness — not signal vertices near band edges as originally hypothesised. "
      "The specific conversion-vertex mechanism was not isolated in this study "
      "(see §7.1(c)).")

    S("This revised picture is consistent with the near-edge fraction showing no "
      "seed-level correlation with Tag (N1 REFUTED): since signal-vertex randomness "
      "accounts for only 0.19% of total variance, the spatial classification of signal "
      "vertices cannot predict the Tag outcome. The Winsorising result (R2) adds a "
      "further dimension: capping the extreme λ values creates artificial clusters at "
      "the boundary, introducing a new source of threshold-scan instability that is "
      "absent in the untrimmed or fully trimmed estimator.")

    # ══════════════════════════════════════════════════════════════
    # 8. CONCLUSION
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    head("8", "Conclusion")

    S("This post-registration report presents the complete results of the v2.7 "
      "Tag Formula Diagnostics, following the preregistered analysis plan "
      "(DOI: 10.5281/zenodo.24388228). The v2.7 Group F ensemble was computed fresh "
      "for this study; seed-0 verification confirms internal consistency among the "
      "v2.7 F/C/S groups (matching to floating-point precision at i = 0), but direct "
      "comparison with the original v2.6 per-seed arrays was not performed (they were "
      "not retained). The study deployed three complementary diagnostic approaches — "
      "frozen-seed variance decomposition, per-vertex weight analysis, and robust "
      "estimator comparison — across a 50-seed ensemble at two ALP masses (17 MeV "
      "and 200 MeV) in the E3 configuration (f = 0.25, η = 2.0, 17-band geometry).")

    subhead("8.1 Summary of Findings")

    S("Of the 12 preregistered predictions, 8 are CONFIRMED and 4 are REFUTED. "
      "The 4 core predictions yield a 2/4 score (N3 and R1 CONFIRMED; F1 and N1 "
      "REFUTED), classifying the diagnostic evidence as <b>weak</b> by the "
      "preregistered success criterion (§7). However, the scientific value of the "
      "study lies precisely in the REFUTED predictions, which reveal an unexpected "
      "and consequential mechanism.")

    S("Three central findings emerge:")

    S("<b>(1) Conversion-background dominance.</b> Frozen-seed variance decomposition "
      "demonstrates that 99.84% of the Tag discriminator's seed-to-seed variance at "
      f"17 MeV originates from conversion-vertex randomness (σ<sub>S</sub>/σ<sub>F</sub> "
      f"= {sS/sF:.4f}), not signal-vertex randomness (σ<sub>C</sub>/σ<sub>F</sub> = "
      f"{sC/sF:.4f}). This is the opposite direction from the preregistered expectation "
      "and constitutes the most important qualitative finding of this study. At 17 MeV, "
      "the variance additivity relation holds to 0.03% precision (sum = 1.0003), "
      "consistent with — though not proof of — statistical independence. At 200 MeV, "
      "the sum is 1.5975, indicating that variance additivity does not hold at that "
      "mass (though this alone cannot determine statistical dependence).")

    S(f"<b>(2) Trimming vs. Winsorising asymmetry.</b> Trimming the extreme 1% tails "
      f"of the per-vertex λ distribution reduces the Tag CV from {cv_base:.2f}% to "
      f"{cv_t1:.2f}% — a {cv_base/cv_t1:.0f}-fold improvement that nearly eliminates "
      f"seed-to-seed variation. In contrast, Winsorising the same fraction "
      f"<i>increases</i> the CV to {cv_w1:.2f}%, worse than the untrimmed baseline. "
      f"This counter-intuitive result arises because Winsorising concentrates vertices "
      f"at the boundary λ, creating a sharp step in the threshold-scan landscape that "
      f"amplifies sensitivity to seed-to-seed fluctuations.")

    S(f"<b>(3) Extreme kurtosis and mass dependence.</b> The pooled signal-vertex λ "
      f"distribution exhibits excess kurtosis of {kurt17:.1f} at 17 MeV, confirming "
      f"a strongly non-Gaussian, heavy-tailed character. The leverage effect is "
      f"mass-specific: at 200 MeV, the baseline CV is only {cv0_200:.2f}% and "
      f"trimming changes it by less than 0.05 percentage points, confirming that "
      f"the instability is confined to the low-mass regime. The specific mechanism "
      f"driving conversion-side variance at 17 MeV was not isolated in this study "
      f"(see §7.1(c)).")

    subhead("8.2 Methodological Observations")

    S("The preregistration framework proves its value even — perhaps especially — "
      "when predictions are refuted. The preregistered thresholds (σ<sub>C</sub>/"
      "σ<sub>F</sub> > 0.5 for F1, |R| > 0.3 for N1) were chosen to be conservative, "
      "so their failure is unambiguous. Had the analysis been conducted without "
      "preregistration, the temptation to rationalise the conversion dominance as "
      "'obvious in retrospect' would be strong — but the written record shows that "
      "the signal-dominance hypothesis was the natural expectation.")

    S(f"The baseline CV differs between v2.6 (7.4%) and this v2.7 run ({cv_base:.2f}%). "
      "The exact cause was not investigated, as the v2.6 original per-seed arrays "
      "were not retained for direct comparison. All 50 seeds produce 43,993–44,939 "
      "signal vertices, well below the 50,000 cap (which is therefore never activated). "
      "The diagnostic patterns — which source dominates, which robust estimator works "
      "— are more stable across parameterisations than the absolute CV values.")

    S("All verification checks passed: seed-0 consistency (F = C = S at i = 0 to "
      "floating-point precision) and k = 0 consistency (trimmed Tag at k = 0 "
      "reproduces the standard scan_tag_endcap result exactly). These confirm that "
      "the diagnostic infrastructure is correctly implemented and that the groups "
      "share the intended seed structure.")

    # ══════════════════════════════════════════════════════════════
    # 9. FUTURE DIRECTIONS
    # ══════════════════════════════════════════════════════════════
    head("9", "Future Directions")

    subhead("9.1 Trimmed Tag Estimator as Default")

    S("The most immediate practical implication is that a <b>trimmed Tag estimator</b> "
      "at k = 1% could appear advantageous as the default for future analyses. The "
      f"mean degradation ratio improves from {F17_tag.mean():.4f} (untrimmed) to "
      f"{data['17MeV_tr_k1p0'].mean():.4f} (trimmed k = 1%) — closer to 1.0 (ideal) "
      f"— while simultaneously achieving a {cv_base/cv_t1:.0f}-fold gain in stability. "
      "At 200 MeV, the effect is negligible (|Δ(σ/mean)| < 0.05%), so a uniform "
      "k = 1% trim would not compromise performance at higher masses. A formal "
      "preregistration of the trimmed Tag as the primary discriminator could be "
      "considered for a future version (v2.8 or beyond).")

    subhead("9.2 Signal-Side λ Regularisation")

    S("For <i>signal</i> vertices, the inter-band p<sub>conv</sub> floor produces "
      "extremely large λ values in the 17-band geometry. A regularised "
      "p<sub>conv</sub> that imposes a physical minimum (e.g., a constant floor "
      "above 10<super>−12</super>, matching the ε used in Approach B's inter-band "
      "classification) could reduce the extreme signal-vertex λ tail. However, since "
      "Approach A shows that signal-vertex randomness contributes only 0.19% of Tag "
      "variance, such a signal-side change alone may not substantially improve Tag "
      "stability. Identifying and regularising the conversion-side mechanism (§7.1(c)) "
      "would be a higher priority for future work. Either modification would change "
      "the tag formula itself and require a fresh preregistration.")

    subhead("9.3 Background-Focused Diagnostics")

    S("The finding that Tag variability is primarily a question of background "
      "modelling, not signal efficiency, opens new diagnostic directions. Future "
      "studies could investigate: (a) the per-seed breakdown of the optimised "
      "background yield B at the Tag's chosen threshold, to quantify how many "
      "conversion vertices cross the threshold boundary from seed to seed; "
      "(b) a decomposition of B into contributions from near-band and inter-band "
      "conversion vertices, to identify whether the instability is dominated by "
      "a few vertices at extreme λ or by a broad shift in the λ distribution; "
      "and (c) the effect of increasing N<sub>conv</sub> beyond 100,000, to test "
      "whether the variance diminishes as √N<sub>conv</sub> (suggesting independent "
      "vertex contributions) or more slowly (suggesting correlated effects).")

    subhead("9.4 Alternative Discriminator Architectures")

    S("The contrast between the Tag and HV discriminators is instructive. HV "
      f"achieves CV = {cv(F17_hv):.2f}% at 17 MeV — roughly {cv_base/cv(F17_hv):.0f}× "
      "more stable than the Tag — because it uses a material-veto approach that is "
      "binary (vertex passes or fails based on proximity to material) rather than "
      "continuous (the Tag's λ threshold scan over a 14-element TGRID). Future work "
      "could explore hybrid discriminators that combine the Tag's mass-dependent "
      "sensitivity with the HV's stability, for example by using the HV as a "
      "pre-filter to remove conversion-dominated vertices before applying a "
      "simplified Tag cut.")

    subhead("9.5 Extension to Other Configurations")

    S("This study used the E3 configuration (f = 0.25) and two masses (17 MeV, "
      "200 MeV). The conversion-dominance finding may depend on the material scale "
      "factor f: at higher f (denser material), more conversions occur near bands "
      "and fewer in gaps, potentially shifting the balance between σ<sub>C</sub> and "
      "σ<sub>S</sub>. A systematic scan over f ∈ {0.10, 0.25, 0.50, 1.00} and a "
      "broader mass grid (5 – 500 MeV) could map the boundary of the conversion-"
      "dominated regime and determine whether it extends to the full mass range of "
      "the ALP → e<super>+</super>e<super>−</super> search.")

    subhead("9.6 Preregistration Lessons")

    S("The v2.7 diagnostics demonstrate that preregistration is valuable even in "
      "exploratory toy MC studies. The 2/4 core score nominally indicates 'weak' "
      "diagnostic evidence, but the REFUTED predictions are arguably more valuable "
      "than the CONFIRMED ones: they reveal a mechanism (conversion-background "
      "dominance) that was not anticipated and that has clear implications for "
      "discriminator design. Future preregistrations in this series could benefit "
      "from (a) explicitly listing 'direction-agnostic' predictions that are "
      "informative regardless of which way they go, and (b) defining success "
      "criteria that account for the information content of refutations, not just "
      "confirmations.")

    # ══════════════════════════════════════════════════════════════
    # 10. DOI CHAIN
    # ══════════════════════════════════════════════════════════════
    head("10", "DOI Chain")

    doi_data = [
        ['v2.7 post-reg (this)',  '10.5281/zenodo.24408990',    'Tag Formula Diagnostics results'],
        ['v2.7 prereg',           '10.5281/zenodo.24388228',    'Tag Formula Diagnostics prereg'],
        ['v2.6 post-reg',        '10.5281/zenodo.24373115',     'Multi-Seed Ensemble results'],
        ['v2.6 prereg',          '10.5281/zenodo.24361872',     'Multi-Seed Ensemble prereg'],
        ['v2.5 results',         '10.5281/zenodo.24341050',     'Deconflation post-reg'],
        ['v2.5 prereg',          '10.5281/zenodo.24329044',     'Deconflation prereg'],
        ['v2.4 results',         '10.5281/zenodo.24302619',     '17-band geometry post-reg'],
        ['v2.4 prereg',          '10.5281/zenodo.24296796',     '17-band geometry prereg'],
        ['v2.3 results',         '10.5281/zenodo.24273586',     'Endcap tag post-reg'],
        ['v2.3 prereg',          '10.5281/zenodo.24244893',     'Endcap tag prereg'],
        ['v2.2 results',         '10.5281/zenodo.24238224',     'Barrel → endcap post-reg'],
        ['v2.2 prereg',          '10.5281/zenodo.24189990',     'Barrel → endcap prereg'],
        ['v2.1 results',         '10.5281/zenodo.24136462',     'Barrel material-veto post-reg'],
        ['v2.1 prereg',          '10.5281/zenodo.24063091',     'Barrel material-veto prereg'],
        ['v2.0',                 '10.5281/zenodo.24056097',     'Initial barrel study'],
    ]
    make_table(
        ['Version', 'DOI', 'Description'],
        doi_data,
        col_widths=[70, 110, 130]
    )

    # ══════════════════════════════════════════════════════════════
    # 11. REFERENCES
    # ══════════════════════════════════════════════════════════════
    head("11", "References")

    subhead("11.1 External References")

    ext_refs = [
        "[E1] J. Alimena, F. Blekman, C. Cazzaniga, X. Cid Vidal, J. Niedziela, "
        "L. Rygaard, R. Soto Rey, \"Hunting for Long-Lived ALPs in Top Events via "
        "Displaced Dielectron Pairs at the LHC,\" arXiv:2610.38932 [hep-ph] (2026) "
        "(motivating analysis: generator-level sensitivity study for displaced "
        "ALP → e<super>+</super>e<super>−</super> in tt̄ events at the CMS detector).",

        "[E2] L. Rygaard, J. Niedziela, R. Schäfer, S. Bruggisser, J. Alimena, S. Westhoff, "
        "F. Blekman, \"Top Secrets: Long-Lived ALPs in Top Production,\" "
        "arXiv:2306.08686 [hep-ph] (2023) (predecessor analysis: displaced di-muon "
        "ALP search strategy in tt̄ production at the LHC and HL-LHC).",

        "[E3] A. L. Read, \"Presentation of search results: the CL<sub>s</sub> technique,\" "
        "J. Phys. G <b>28</b> (2002) 2693 (upper-limit methodology background).",

        "[E4] D. Curtin et al., \"Long-Lived Particles at the Energy Frontier: The MATHUSLA "
        "Physics Case,\" Rep. Prog. Phys. <b>82</b> (2019) 116201, arXiv:1806.07396 "
        "(displaced-vertex physics context).",

        "[E5] NumPy v1.26, numpy.org (pseudo-random number generation, array operations).",

        "[E6] ReportLab v5.0.1, reportlab.com (PDF generation).",

        "[E7] SciPy v1.14, scipy.org (Pearson correlation, scipy.stats.pearsonr).",
    ]
    for r in ext_refs:
        story.append(Paragraph(r, styles['RefStyle']))

    sp(4)

    subhead("11.2 Internal References (ALP-ttbar Toy MC Series)")

    int_refs = [
        "[I1] W. S. Paik, \"ALP-ttbar Toy MC v2.7 — Preregistration: Tag Formula "
        "Diagnostics in Displaced Light ALP → e<super>+</super>e<super>−</super>,\" "
        "DOI: 10.5281/zenodo.24388228 (preregistered analysis plan for this study).",

        "[I2] W. S. Paik, \"ALP-ttbar Toy MC v2.6 — Post-Registration: Multi-Seed "
        "Ensemble Results,\" DOI: 10.5281/zenodo.24373115 (50-seed ensemble results, "
        "identified the Tag CV ≈ 7.4% instability that motivated this diagnostic study).",

        "[I3] W. S. Paik, \"ALP-ttbar Toy MC v2.6 — Preregistration: Multi-Seed Ensemble,\" "
        "DOI: 10.5281/zenodo.24361872.",

        "[I4] W. S. Paik, \"ALP-ttbar Toy MC v2.5 — Post-Registration: Deconflation,\" "
        "DOI: 10.5281/zenodo.24341050.",

        "[I5] W. S. Paik, \"ALP-ttbar Toy MC v2.5 — Preregistration: Deconflation,\" "
        "DOI: 10.5281/zenodo.24329044.",

        "[I6] W. S. Paik, \"ALP-ttbar Toy MC v2.4 — Post-Registration: 17-Band Geometry,\" "
        "DOI: 10.5281/zenodo.24302619 (introduced the 17-band geometry used here).",

        "[I7] W. S. Paik, \"ALP-ttbar Toy MC v2.4 — Preregistration: 17-Band Geometry,\" "
        "DOI: 10.5281/zenodo.24296796.",

        "[I8] W. S. Paik, \"ALP-ttbar Toy MC v2.3 — Post-Registration: Endcap Tag,\" "
        "DOI: 10.5281/zenodo.24273586.",

        "[I9] W. S. Paik, \"ALP-ttbar Toy MC v2.3 — Preregistration: Endcap Tag,\" "
        "DOI: 10.5281/zenodo.24244893.",

        "[I10] W. S. Paik, \"ALP-ttbar Toy MC v2.2 — Post-Registration: Barrel → Endcap,\" "
        "DOI: 10.5281/zenodo.24238224 (introduced the endcap configuration and mtag_v22).",

        "[I11] W. S. Paik, \"ALP-ttbar Toy MC v2.2 — Preregistration: Barrel → Endcap,\" "
        "DOI: 10.5281/zenodo.24189990.",

        "[I12] W. S. Paik, \"ALP-ttbar Toy MC v2.1 — Post-Registration: Barrel Material Veto,\" "
        "DOI: 10.5281/zenodo.24136462.",

        "[I13] W. S. Paik, \"ALP-ttbar Toy MC v2.1 — Preregistration: Barrel Material Veto,\" "
        "DOI: 10.5281/zenodo.24063091.",

        "[I14] W. S. Paik, \"ALP-ttbar Toy MC v2.0 — Initial Barrel Study,\" "
        "DOI: 10.5281/zenodo.24056097 (first record in the series).",
    ]
    for r in int_refs:
        story.append(Paragraph(r, styles['RefStyle']))

    # ── Build ──
    doc.build(story)
    print(f"PDF generated: {os.path.join(HERE, PDF_NAME)}")
    return os.path.join(HERE, PDF_NAME)


if __name__ == '__main__':
    build_pdf()
