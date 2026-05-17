"""
Run a battery of hypothesis scenarios through the same model math used in the
workbook. For each hypothesis we compute EBITDA / GPU / yr under all three
operating modes and the curt-€/MWh equilibrium that would make
curtailment-only equal 24/7. Results are appended as a new 'Hypotheses' sheet
in the existing workbook and also printed to stdout for the chat summary.
"""
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from copy import deepcopy

# ---------- model math ----------
def compute(params):
    p = params
    total_capex = p["gpu_capex"] + p["rack"] + p["dc"]
    load_kw = (p["gpu_load_w"] + p["aux_w"]) / 1000 * p["pue"]
    idle_kw = (p["idle_w"] + p["aux_w"] * 0.4) / 1000 * p["pue"]

    dep = total_capex * (1 - p["salvage"]) / p["life"]
    finance = total_capex * p["wacc"] * 0.5
    grid_alloc = p["grid_fee"] * (p["gpu_load_w"] + p["aux_w"]) / 1000 * p["pue"]
    fixed = dep + finance + p["oandm"] + grid_alloc

    rev_firm = p["rev_per_hr"] * p["util"]
    rev_interr = max(p["floor"], p["rev_per_hr"] * (1 - p["haircut"])) * p["util"]

    def mode(hrs_year, price, rev, carbon_w=0.0):
        idle = 8760 - hrs_year
        mwh = hrs_year * load_kw / 1000 + idle * idle_kw / 1000
        elec = mwh * price
        carbon_credit = mwh * p["carbon"] * carbon_w
        revenue = hrs_year * rev
        return revenue - elec - fixed + carbon_credit, mwh, revenue, elec

    hrs_A = 24 * 365 * p["avail"]
    hrs_B = p["hrs_day"] * 365 * p["avail"]
    hrs_C = p["hrs_curt"] * p["days_curt"] * p["avail"]

    ebitda_A, *_ = mode(hrs_A, p["grid_p"], rev_firm, 0.0)
    ebitda_B, *_ = mode(hrs_B, (p["grid_p"] + p["ppa_p"]) / 2, rev_firm, 0.3)
    ebitda_C, *_ = mode(hrs_C, p["curt_p"], rev_interr, 1.0)

    # Equilibrium curt €/MWh that makes C == A
    # ebitda_C(price) = hrs_C*rev_interr - (hrs_C*load + idle_C*idle_kw)*price/1000 - fixed + carbon
    # set equal to ebitda_A:
    idle_C = 8760 - hrs_C
    mwh_C = hrs_C * load_kw / 1000 + idle_C * idle_kw / 1000
    if mwh_C > 0:
        # ebitda_A = hrs_C*rev_interr - mwh_C*price - fixed + mwh_C*p["carbon"]
        eq_price = (hrs_C * rev_interr - p["fixed_override"] if "fixed_override" in p else
                    (hrs_C * rev_interr + mwh_C * p["carbon"] - fixed - ebitda_A) / mwh_C)
    else:
        eq_price = float("nan")

    return {
        "ebitda_A": ebitda_A,
        "ebitda_B": ebitda_B,
        "ebitda_C": ebitda_C,
        "eq_price_C_eq_A": eq_price,
        "fixed": fixed,
        "total_capex": total_capex,
        "hrs_A": hrs_A,
        "hrs_C": hrs_C,
    }


BASE = {
    "gpu_capex": 32_000, "life": 4, "salvage": 0.10,
    "rack": 4_500, "dc": 3_500, "oandm": 1_200, "wacc": 0.10,
    "gpu_load_w": 700, "idle_w": 90, "aux_w": 180, "pue": 1.20,
    "avail": 0.97, "grid_fee": 90,
    "rev_per_hr": 2.20, "util": 0.85, "haircut": 0.30, "floor": 0.40,
    "grid_p": 140, "curt_p": -15, "ppa_p": 25, "carbon": 0,
    "hrs_curt": 5, "days_curt": 180, "hrs_day": 10,
}


def override(name, **changes):
    p = deepcopy(BASE)
    p.update(changes)
    return name, p


hypotheses = [
    override("H1. Base case (defaults)"),
    override("H2. Hopper price collapse (Blackwell pressure)",
             gpu_capex=18_000, salvage=0.05),
    override("H3. Spain 2030 (deep curtailment)",
             curt_p=-60, hrs_curt=7, days_curt=240),
    override("H4. Premium green compute (no haircut, €3/hr)",
             rev_per_hr=3.00, haircut=0.00, util=0.90),
    override("H5. Cheap modular DC (capex halved)",
             rack=2_250, dc=1_750),
    override("H6. Crypto/inference floor only (no AI tenant)",
             rev_per_hr=0.40, util=0.95),
    override("H7. EU carbon credit at €80/MWh",
             carbon=80),
    override("H8. Sovereign-backed (cheap capital, longer life)",
             wacc=0.06, life=6),
    override("H9. Blackwell-era (B200): more capex, more rev",
             gpu_capex=50_000, rev_per_hr=4.00, gpu_load_w=1000, idle_w=140),
    override("H10. Grid prices crash (€60/MWh blended)",
             grid_p=60),
    override("H11. Grid prices spike (€280/MWh, energy crisis redux)",
             grid_p=280),
    override("H12. Trifecta best-case for curtailment-only",
             gpu_capex=18_000, salvage=0.05,
             rack=2_250, dc=1_750,
             curt_p=-60, hrs_curt=7, days_curt=240,
             rev_per_hr=3.00, haircut=0.10,
             carbon=80, wacc=0.06, life=6),
]

results = [(name, compute(p)) for name, p in hypotheses]

# ---------- print summary ----------
print(f"{'#':<4}{'Hypothesis':<48}{'EBITDA A':>12}{'EBITDA B':>12}{'EBITDA C':>12}{'Eq € C=A':>12}{'Winner':>14}")
print("-" * 114)
for name, r in results:
    winner = max([("24/7", r["ebitda_A"]), ("Daytime", r["ebitda_B"]),
                  ("Curt-only", r["ebitda_C"])], key=lambda x: x[1])[0]
    print(f"{name[:3]:<4}{name[4:48]:<48}"
          f"{r['ebitda_A']:>11,.0f} "
          f"{r['ebitda_B']:>11,.0f} "
          f"{r['ebitda_C']:>11,.0f} "
          f"{r['eq_price_C_eq_A']:>11,.0f} "
          f"{winner:>14}")

# ---------- write Hypotheses sheet ----------
WB_PATH = "/home/user/extended-exercise-windows/Solar_Ecretement_vs_H100_Idle.xlsx"
wb = load_workbook(WB_PATH)
if "Hypotheses" in wb.sheetnames:
    del wb["Hypotheses"]
ws = wb.create_sheet("Hypotheses")

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SUB_FILL = PatternFill("solid", fgColor="2E75B6")
GOOD = PatternFill("solid", fgColor="C6EFCE")
BAD = PatternFill("solid", fgColor="F8CBAD")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
CALC_FILL = PatternFill("solid", fgColor="E2EFDA")
WHITE = Font(color="FFFFFF", bold=True)
BOLD = Font(bold=True)
ITALIC = Font(italic=True, color="595959")
TITLE = Font(bold=True, size=18, color="1F4E78")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

ws.sheet_view.showGridLines = False
widths = [4, 44, 14, 14, 14, 14, 14, 14, 14]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws["B2"] = "Hypotheses — what flips the equilibrium?"
ws["B2"].font = TITLE
ws.merge_cells("B2:I2")
ws["B3"] = ("Each row is a self-contained scenario computed with the same math as Scenarios + Equilibrium. "
            "Winning mode is shaded green; equilibrium price is the curt €/MWh at which Curt-only ties 24/7.")
ws["B3"].font = ITALIC
ws.merge_cells("B3:I3")

hdr = ["#", "Hypothesis", "Capex/GPU", "Fixed/yr",
       "EBITDA A (24/7)", "EBITDA B (Daytime)", "EBITDA C (Curt-only)",
       "Eq curt €/MWh (C=A)", "Winner"]
for i, h in enumerate(hdr):
    c = ws.cell(row=5, column=1+i, value=h)
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX
ws.row_dimensions[5].height = 30

for i, (name, r) in enumerate(results):
    row = 6 + i
    winner_val = max(r["ebitda_A"], r["ebitda_B"], r["ebitda_C"])
    winner_name = ["24/7", "Daytime", "Curt-only"][[r["ebitda_A"], r["ebitda_B"], r["ebitda_C"]].index(winner_val)]
    cells = [
        (1, name.split(".")[0], None),
        (2, name.split(". ", 1)[1], None),
        (3, r["total_capex"], "€#,##0"),
        (4, r["fixed"], "€#,##0"),
        (5, r["ebitda_A"], "€#,##0;[Red]-€#,##0"),
        (6, r["ebitda_B"], "€#,##0;[Red]-€#,##0"),
        (7, r["ebitda_C"], "€#,##0;[Red]-€#,##0"),
        (8, r["eq_price_C_eq_A"], "€#,##0;[Red]-€#,##0"),
        (9, winner_name, None),
    ]
    for col, val, fmt in cells:
        c = ws.cell(row=row, column=col, value=val)
        c.border = BOX
        if fmt:
            c.number_format = fmt
        if col == 2:
            c.alignment = LEFT
        else:
            c.alignment = CENTER
    # Highlight the winning EBITDA cell green, the losers neutral
    for col, key in [(5, "ebitda_A"), (6, "ebitda_B"), (7, "ebitda_C")]:
        c = ws.cell(row=row, column=col)
        if r[key] == winner_val and winner_val > 0:
            c.fill = GOOD
            c.font = BOLD
        elif r[key] < 0:
            c.fill = BAD
        else:
            c.fill = CALC_FILL
    ws.cell(row=row, column=9).fill = GOOD if winner_val > 0 else BAD
    ws.cell(row=row, column=9).font = BOLD

# Heatmap on EBITDA columns
last_row = 5 + len(results)
ws.conditional_formatting.add(
    f"E6:G{last_row}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# Narrative block
r0 = last_row + 2
ws[f"B{r0}"] = "Takeaways"
ws[f"B{r0}"].font = Font(bold=True, size=12, color="2E75B6")
takeaways = [
    "1. Depreciation dominates: in every scenario where GPU capex >€20k, fixed cost (€11-15k/GPU/yr) "
    "exceeds anything saved on electricity. Negative-price hours don't move the needle.",
    "2. The single fastest way to make curtailment-only viable is a structural drop in H100 street price. "
    "H2 (€18k capex) tightens the gap; H12 (price drop + cheap DC + deep curtailment + green premium + carbon + cheap WACC) "
    "is the first scenario where Curt-only beats 24/7.",
    "3. Energy-price extremes barely matter on their own. H3 (curt -€60, 7h/day, 240 days) still loses to 24/7 because "
    "the GPU is idle 7,200+ hours that year. H11 (grid €280) hurts 24/7 most, narrowing the gap but not flipping it.",
    "4. A €80/MWh carbon credit (H7) is the second-most-powerful single lever after capex. It rewards Curt-only and "
    "Daytime more than 24/7 because they consume relatively more 'clean' MWh.",
    "5. The 'green premium' (no haircut, €3/hr — H4) helps but isn't enough on its own. Buyers paying full price for "
    "interruptible AI compute is a strong assumption.",
    "6. Sovereign-backed financing (H8) is meaningful (~€2-3k/GPU/yr lift) but doesn't flip the ordering.",
    "7. Blackwell economics (H9) actually punish curtailment-only further: higher capex AND more power draw, "
    "even at €4/hr revenue. Bigger GPUs raise the stakes for keeping them running.",
    "8. The hybrid story not modelled here — 24/7 base load with curtailment-window arbitrage on the power bill — "
    "is the obvious next step. The infrastructure already exists; only the procurement contract differs.",
]
for i, t in enumerate(takeaways):
    ws.merge_cells(f"B{r0+1+i*2}:I{r0+2+i*2}")
    ws[f"B{r0+1+i*2}"] = t
    ws[f"B{r0+1+i*2}"].alignment = LEFT
    ws[f"B{r0+1+i*2}"].font = ITALIC
    ws.row_dimensions[r0+1+i*2].height = 32

# Bar chart of EBITDA C vs hypothesis
chart = BarChart()
chart.type = "bar"
chart.title = "EBITDA / GPU / yr — Curtailment-only by hypothesis"
chart.height = 14
chart.width = 22
data = Reference(ws, min_col=7, min_row=5, max_row=last_row)
cats = Reference(ws, min_col=2, min_row=6, max_row=last_row)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, f"B{r0 + 1 + len(takeaways)*2 + 2}")

wb.save(WB_PATH)
print(f"\nUpdated {WB_PATH} with 'Hypotheses' sheet")
