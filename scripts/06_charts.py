"""Walkthrough images (docs/images/*.png).

Static charts for the walkthrough and README. One colour per job: blue for the series that
matters, orange as the second series, grey for context. Solid hairline grids, no dual axes.
The numbers behind every chart are in docs/results/*.md (the table view).

Run: uv run python scripts/06_charts.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from common import IMAGES_DIR, connect

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE, CONTEXT = "#e1e0d9", "#c3c2b7", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASE, "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.titlesize": 12,
    "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlecolor": INK,
})
thousands = FuncFormatter(lambda v, _: f"{v:,.0f}")
pct = FuncFormatter(lambda v, _: f"{v:.0f}%")


def style(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left" if grid_axis == "x" else "bottom"].set_color(BASE)
    ax.spines["bottom" if grid_axis == "x" else "left"].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, name, subtitle=None):
    fig.tight_layout()
    if subtitle:  # below everything, so it never collides with axis labels
        fig.text(0.01, -0.02, subtitle, color=INK2, fontsize=8.5, ha="left", va="top")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGES_DIR / name, dpi=160, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("saved", name)


def fraud_by_type(con):
    df = con.execute("""SELECT type, sum(is_fraud) AS fraud FROM transactions
                        GROUP BY type ORDER BY fraud, type DESC""").df()
    fig, ax = plt.subplots(figsize=(7, 3))
    colors = [BLUE if v > 0 else CONTEXT for v in df.fraud]
    ax.barh(df.type, df.fraud, height=0.5, color=colors)
    for y, v in enumerate(df.fraud):
        ax.text(v + 60, y, f"{v:,.0f}", va="center", color=INK, fontsize=9)
    ax.set_title("Fraud cases by transaction type")
    ax.xaxis.set_major_formatter(thousands)
    style(ax, "x")
    save(fig, "01_fraud_by_type.png", "All 8,213 fraud cases are transfers or cash-outs: money leaving the account.")


def by_hour(con):
    df = con.execute("""SELECT hour, count(*) AS n, sum(is_fraud) AS fraud, 100 * avg(is_fraud) AS rate
                        FROM transactions GROUP BY hour ORDER BY hour""").df()
    night = df.hour <= 6
    fig, axes = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True, gridspec_kw={"hspace": 0.45})
    panels = [("All transactions per hour of day", df.n / 1000, "thousands", thousands),
              ("Fraud cases per hour of day", df.fraud, "cases", thousands),
              ("Share of transactions that are fraud", df.rate, "% of transactions", pct)]
    for ax, (title, values, ylabel, fmt) in zip(axes, panels):
        ax.bar(df.hour, values, width=0.6, color=[BLUE if n else CONTEXT for n in night])
        ax.set_title(title)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.yaxis.set_major_formatter(fmt)
        style(ax)
    peak = df.loc[df.rate.idxmax()]
    axes[2].text(peak.hour + 0.5, peak.rate, f"{peak.rate:.0f}% at {int(peak.hour):02d}:00",
                 va="center", fontsize=9, color=INK)
    axes[2].set_xticks(range(0, 24, 2))
    axes[2].set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
    save(fig, "02_by_hour.png",
         "Blue = 00:00-06:59. Customers sleep, fraudsters do not: fraud stays level while normal activity collapses.")


def rules(con):
    df = con.execute("""SELECT * FROM read_csv('powerbi/data/rule_performance.csv')""").df()
    df = df.iloc[::-1].reset_index(drop=True)
    labels = [f"{r.rule_id} {r.rule}" for r in df.itertuples()]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = range(len(df))
    ax.barh([i + 0.18 for i in y], df.precision_pct, height=0.32, color=BLUE, label="Precision: alerts that were real fraud")
    ax.barh([i - 0.18 for i in y], df.recall_pct, height=0.32, color=ORANGE, label="Recall: share of all fraud caught")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=INK2)
    ax.set_xlim(0, 110)
    ax.xaxis.set_major_formatter(pct)
    ax.set_title("Each rule on its own")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    style(ax, "x")
    save(fig, "03_rules.png", "R1 is perfect only because of how the data was simulated; the other rules show the usual trade-off.")


def thresholds(con):
    df = con.execute("SELECT * FROM read_csv('powerbi/data/threshold_analysis.csv')").df()
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, scenario in zip(axes, ["All rules", "Without R1 (stress test)"]):
        d = df[df.scenario == scenario]
        for col, color, label in [("precision_pct", BLUE, "Precision"), ("recall_pct", ORANGE, "Recall")]:
            ax.plot(d.threshold, d[col], color=color, linewidth=2, marker="o", markersize=5,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
        ax.axvline(30, color=BASE, linewidth=1)
        ax.text(30.8, 8, "chosen: 30", fontsize=8.5, color=INK2)
        ax.set_title(scenario)
        ax.set_xlabel("alert when risk score is at least")
        ax.set_xticks(d.threshold)
        ax.yaxis.set_major_formatter(pct)
        ax.set_ylim(0, 105)
        style(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8.5, loc="upper right", ncol=2, bbox_to_anchor=(0.99, 1.04))
    save(fig, "04_thresholds.png",
         "A higher threshold means fewer, surer alerts but more fraud slips through. 30 keeps both in balance.")


def priorities(con):
    df = con.execute("""SELECT priority, sum(is_fraud) AS fraud, sum(1 - is_fraud) AS false_alarms
                        FROM scored WHERE is_alert GROUP BY priority
                        ORDER BY CASE priority WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END""").df()
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.barh(df.priority, df.fraud, height=0.5, color=BLUE, label="Confirmed fraud")
    ax.barh(df.priority, df.false_alarms, left=df.fraud + 40, height=0.5, color=ORANGE, label="False alarm")
    for y, r in enumerate(df.itertuples()):
        ax.text(r.fraud + r.false_alarms + 120, y, f"{r.fraud:,.0f} fraud / {r.false_alarms:,.0f} false",
                va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, 6300)
    ax.xaxis.set_major_formatter(thousands)
    ax.set_title("Alerts by priority and outcome")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    style(ax, "x")
    save(fig, "05_priorities.png", "High and Medium alerts are almost all real fraud; the Low band is mostly noise in this data.")


def headline(con):
    rows = [("Simulator's own flag", 16), ("Our rules without R1", None), ("Our rules (all)", None)]
    caught_all, caught_wo = con.execute("""SELECT sum((risk_score >= 30 AND is_fraud = 1)::INT),
                                                  sum((risk_score_without_r1 >= 30 AND is_fraud = 1)::INT)
                                           FROM scored WHERE is_money_out""").fetchone()
    values = [16, caught_wo, caught_all]
    fig, ax = plt.subplots(figsize=(7, 2.4))
    ax.barh([r[0] for r in rows], values, height=0.5, color=[CONTEXT, BLUE, BLUE])
    for y, v in enumerate(values):
        ax.text(v + 80, y, f"{v:,.0f} of 8,213 ({100 * v / 8213:.1f}%)", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 10500)
    ax.xaxis.set_major_formatter(thousands)
    ax.set_title("Fraud cases caught")
    style(ax, "x")
    save(fig, "00_headline.png", "The existing flag misses almost everything; simple, explainable rules do far better.")


def main() -> None:
    con = connect(read_only=True)
    for chart in (headline, fraud_by_type, by_hour, rules, thresholds, priorities):
        chart(con)
    con.close()


if __name__ == "__main__":
    import os

    os.chdir(IMAGES_DIR.parents[1])  # so the powerbi/data paths above resolve
    main()
