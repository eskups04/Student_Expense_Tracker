import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from logic import compute_totals_by_category

# ── PALETTE ───────────────────────────────────────────────────────
COLORS = [
    "#4E79A7",  
    "#59A14F",  
    "#F28E2B",  
    "#E15759",  
    "#76B7B2",  
    "#EDC948", 
]

BACKGROUND = "#F7F7FB"   
TEXT_DARK  = "#2E2E3A"
TEXT_MID   = "#41415B"
ACCENT     = "#4E79A7"

def _apply_base_style():
    """Applies global matplotlib style settings for all charts."""
    plt.rcParams.update({
        "font.family":        "DejaVu Sans",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.spines.left":   False,
        "axes.spines.bottom": False,
        "axes.grid":          False,
        "figure.facecolor":   BACKGROUND,
        "axes.facecolor":     BACKGROUND,
        "text.color":         TEXT_DARK,
        "axes.labelcolor":    TEXT_DARK,
        "xtick.color":        TEXT_MID,
        "ytick.color":        TEXT_MID,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
    })

def generate_pie_chart(month):
    """
    Creates a polished donut chart showing expense breakdown by category.
    """
    totals = compute_totals_by_category(month)
    if not totals:
        print(f"No expenses found for {month}.")
        return

    _apply_base_style()

    categories = list(totals.keys())
    amounts    = list(totals.values())
    total      = sum(amounts)
    colors = [COLORS[i % len(COLORS)] for i in range(len(categories))]

    fig, (ax_donut, ax_legend) = plt.subplots(
        1, 2,
        figsize=(11, 6),
        gridspec_kw={"width_ratios": [1.2, 1]}
    )
    fig.patch.set_facecolor(BACKGROUND)

    # ── Donut ──
    wedges, _ = ax_donut.pie(
        amounts,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": BACKGROUND, "linewidth": 3},
        counterclock=False,
    )

    # Centre text
    ax_donut.text(0, 0.08, f"₱{total:,.0f}",
                  ha="center", va="center",
                  fontsize=22, fontweight="bold", color=TEXT_DARK)
    ax_donut.text(0, -0.18, "total spent",
                  ha="center", va="center",
                  fontsize=10, color=TEXT_MID)

    ax_donut.set_aspect("equal")

    # ── Legend panel ──
    ax_legend.axis("off")

    # Title
    ax_legend.text(0, 1.0, "Expense Breakdown",
                   fontsize=16, fontweight="bold", color=TEXT_DARK,
                   transform=ax_legend.transAxes, va="top")
    ax_legend.text(0, 0.90, month,
                   fontsize=11, color=TEXT_MID,
                   transform=ax_legend.transAxes, va="top")

    # Category rows
    row_start = 0.74
    row_gap   = 0.13

    for i, (cat, amt) in enumerate(zip(categories, amounts)):
        pct = amt / total * 100
        y   = row_start - i * row_gap

        # Colour swatch
        ax_legend.add_patch(mpatches.FancyBboxPatch(
            (0, y - 0.025), 0.045, 0.055,
            boxstyle="round,pad=0.005",
            facecolor=colors[i], edgecolor="none",
            transform=ax_legend.transAxes
        ))

        # Category name
        ax_legend.text(0.07, y + 0.01, cat,
                       fontsize=10, color=TEXT_DARK,
                       transform=ax_legend.transAxes, va="center")

        # Amount
        ax_legend.text(0.07, y - 0.045, f"₱{amt:,.2f}  ·  {pct:.1f}%",
                       fontsize=9, color=TEXT_MID,
                       transform=ax_legend.transAxes, va="center")

    plt.tight_layout(pad=2.5)
    filename = f"pie_{month}.png"
    plt.savefig(filename, dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    print(f"Pie chart saved as {filename}")
    plt.show()

def compare_months(month1, month2):
    """
    Creates a clean grouped bar chart comparing two months.
    """
    totals1 = compute_totals_by_category(month1)
    totals2 = compute_totals_by_category(month2)

    if not totals1 and not totals2:
        print("No data found for either month.")
        return

    _apply_base_style()

    all_categories = sorted(set(list(totals1.keys()) + list(totals2.keys())))
    amounts1 = [totals1.get(cat, 0) for cat in all_categories]
    amounts2 = [totals2.get(cat, 0) for cat in all_categories]

    x     = np.arange(len(all_categories))
    width = 0.38

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    COLOR_M1 = COLORS[0]
    COLOR_M2 = COLORS[3]

    bars1 = ax.bar(x - width / 2, amounts1, width,
                   color=COLOR_M1, label=month1,
                   zorder=2)
    bars2 = ax.bar(x + width / 2, amounts2, width,
                   color=COLOR_M2, label=month2,
                   zorder=2)

    # Subtle horizontal gridlines
    ax.yaxis.grid(True, color="#E0DBD5", linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)

    # Amount labels on top of bars
    def label_bars(bars, color):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + max(amounts1 + amounts2) * 0.01,
                    f"₱{h:,.0f}",
                    ha="center", va="bottom",
                    fontsize=8, color=color, fontweight="bold"
                )

    label_bars(bars1, COLOR_M1)
    label_bars(bars2, COLOR_M2)

    ax.set_xticks(x)
    ax.set_xticklabels(all_categories, fontsize=10)
    ax.tick_params(left=False, bottom=False)

    # Format y axis as ₱
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda val, _: f"₱{val:,.0f}")
    )

    # Custom legend
    legend_patches = [
        mpatches.Patch(color=COLOR_M1, label=month1),
        mpatches.Patch(color=COLOR_M2, label=month2),
    ]
    ax.legend(handles=legend_patches, frameon=False,
              fontsize=10, loc="upper right")

    # Title block
    fig.text(0.08, 0.96, "Month-to-Month Comparison",
             fontsize=16, fontweight="bold", color=TEXT_DARK, va="top")
    fig.text(0.08, 0.89, f"{month1}  vs  {month2}",
             fontsize=11, color=TEXT_MID, va="top")

    # Totals footer
    t1 = sum(amounts1)
    t2 = sum(amounts2)
    diff = t2 - t1
    diff_str = f"▲ ₱{diff:,.0f} more" if diff > 0 else f"▼ ₱{abs(diff):,.0f} less"
    fig.text(0.92, 0.04,
             f"{month1}: ₱{t1:,.0f}   {month2}: ₱{t2:,.0f}   {diff_str}",
             fontsize=9, color=TEXT_MID, ha="right")

    plt.tight_layout(rect=[0, 0.06, 1, 0.88])
    filename = f"compare_{month1}_vs_{month2}.png"
    plt.savefig(filename, dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    print(f"Comparison chart saved as {filename}")
    plt.show()