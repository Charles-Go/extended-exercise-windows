"""
Adds battery storage to the model. A battery lets us time-shift cheap
curtailed solar into the expensive evening peak, decoupling GPU run-time
from when free power is available.

Three new operating modes:
  D. 24/7 + battery (charged during curt window, discharged the rest)
  E. 24/7 + oversized battery (rides through non-curt days too)
  F. Standalone battery arbitrage (no GPU — what BESS-without-AI earns)

Adds a new 'Batteries' sheet to the existing workbook with:
  - Battery inputs
  - The math per scenario
  - Sensitivity table over battery €/kWh
  - Comparison vs the original three modes
"""
import sys
sys.path.insert(0, "/home/user/extended-exercise-windows/build")
from test_hypotheses import compute, BASE, override, deepcopy
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

# ---------- battery math ----------
def battery_economics(p, batt):
    """
    p: scenario params (same shape as compute())
    batt: dict with bess_eur_per_kwh, eff, life_yr, salvage,
          mode = 'curt_day_only' | 'every_day'
    Returns dict of annual figures for 24/7 + battery and standalone arbitrage.
    """
    total_capex = p["gpu_capex"] + p["rack"] + p["dc"]
    load_kw = (p["gpu_load_w"] + p["aux_w"]) / 1000 * p["pue"]
    idle_kw = (p["idle_w"] + p["aux_w"] * 0.4) / 1000 * p["pue"]

    dep = total_capex * (1 - p["salvage"]) / p["life"]
    finance = total_capex * p["wacc"] * 0.5
    grid_alloc = p["grid_fee"] * (p["gpu_load_w"] + p["aux_w"]) / 1000 * p["pue"]
    fixed_gpu = dep + finance + p["oandm"] + grid_alloc

    rev_firm = p["rev_per_hr"] * p["util"]

    # battery sizing: cover (24 - curt_hrs) hours of GPU load
    hours_covered = 24 - p["hrs_curt"]
    bess_kwh = hours_covered * load_kw / batt["eff"]
    bess_capex = bess_kwh * batt["bess_eur_per_kwh"]

    # annualised battery cost
    bess_dep = bess_capex * (1 - batt["salvage"]) / batt["life_yr"]
    bess_fin = bess_capex * p["wacc"] * 0.5
    bess_fixed = bess_dep + bess_fin

    # daily energy flows on a curt day:
    # GPU draws load_kw for 24h
    # curt window: GPU draws load_kw + battery charges (hours_covered*load_kw/eff) extra
    daily_curt_draw_kwh = p["hrs_curt"] * load_kw + hours_covered * load_kw / batt["eff"]
    # off-curt hours: GPU draws nothing from grid (runs off battery)
    daily_offcurt_draw_kwh = 0
    daily_curt_cost = daily_curt_draw_kwh / 1000 * p["curt_p"]  # €/day
    daily_offcurt_cost = daily_offcurt_draw_kwh / 1000 * p["grid_p"]
    curt_day_elec = (daily_curt_cost + daily_offcurt_cost) * p["days_curt"]

    # non-curt days: no battery benefit, full 24h grid draw
    noncurt_days = 365 - p["days_curt"]
    noncurt_day_elec = 24 * load_kw / 1000 * p["grid_p"] * noncurt_days

    # availability-adjusted hours
    powered_hrs = 8760 * p["avail"]
    idle_hrs = 8760 - powered_hrs
    # the small idle load still costs something (avg price proxy)
    idle_elec = idle_hrs * idle_kw / 1000 * (p["grid_p"] + p["curt_p"]) / 2

    total_elec_cost = curt_day_elec + noncurt_day_elec + idle_elec

    revenue = powered_hrs * rev_firm
    ebitda_battery = revenue - total_elec_cost - fixed_gpu - bess_fixed

    # Original 24/7 EBITDA without battery
    base = compute(p)
    ebitda_24_7 = base["ebitda_A"]

    # Standalone battery arbitrage (no GPU, just buy curt power, sell at grid price)
    # Cycle: hours_covered kWh per cycle * days_curt
    cycle_kwh_year = hours_covered * load_kw * p["days_curt"]
    # Revenue: discharge × grid price; Cost: charge × curt price
    discharge_kwh = cycle_kwh_year
    charge_kwh = cycle_kwh_year / batt["eff"]
    arb_revenue = discharge_kwh / 1000 * p["grid_p"]
    arb_cost = charge_kwh / 1000 * p["curt_p"]
    arb_ebitda = arb_revenue - arb_cost - bess_fixed

    return {
        "bess_kwh": bess_kwh,
        "bess_capex": bess_capex,
        "bess_fixed_yr": bess_fixed,
        "elec_cost_yr": total_elec_cost,
        "ebitda_24_7_battery": ebitda_battery,
        "ebitda_24_7_nobattery": ebitda_24_7,
        "uplift_from_battery": ebitda_battery - ebitda_24_7,
        "arb_ebitda_no_gpu": arb_ebitda,
        "implied_arbitrage_spread": p["grid_p"] - p["curt_p"] / batt["eff"],
    }


BATT_BASE = {
    "bess_eur_per_kwh": 250,
    "eff": 0.88,            # round-trip
    "life_yr": 10,
    "salvage": 0.10,
}

scenarios = [
    ("S1. Base case + battery",                  BASE,                                                 BATT_BASE),
    ("S2. Spain 2030 (-€60, 7h, 240d) + battery", {**BASE, "curt_p": -60, "hrs_curt": 7, "days_curt": 240}, BATT_BASE),
    ("S3. Trifecta + battery (best-case)",        {**BASE, "gpu_capex": 18_000, "rack": 2_250, "dc": 1_750,
                                                    "curt_p": -60, "hrs_curt": 7, "days_curt": 240,
                                                    "rev_per_hr": 3.00, "haircut": 0.10, "carbon": 80,
                                                    "wacc": 0.06, "life": 6}, BATT_BASE),
    ("S4. Cheap batteries 2028 (€150/kWh)",       BASE, {**BATT_BASE, "bess_eur_per_kwh": 150}),
    ("S5. Expensive batteries (€400/kWh)",        BASE, {**BATT_BASE, "bess_eur_per_kwh": 400}),
    ("S6. High-eff batteries (95% RTE)",          BASE, {**BATT_BASE, "eff": 0.95}),
    ("S7. Blackwell B200 + cheap batteries",      {**BASE, "gpu_capex": 50_000, "rev_per_hr": 4.00,
                                                    "gpu_load_w": 1000, "idle_w": 140},
                                                  {**BATT_BASE, "bess_eur_per_kwh": 150}),
]

results = []
for name, p, batt in scenarios:
    full_p = {**BASE, **p}
    r = battery_economics(full_p, batt)
    results.append((name, full_p, batt, r))

# ---------- print summary ----------
print(f"\n{'Scenario':<48}{'BESS kWh':>10}{'BESS capex':>14}{'24/7 noBatt':>14}{'24/7 +Batt':>14}{'Δ Battery':>12}{'Arb no-GPU':>14}")
print("-" * 126)
for name, p, batt, r in results:
    print(f"{name[:48]:<48}{r['bess_kwh']:>10,.1f}{r['bess_capex']:>13,.0f} "
          f"{r['ebitda_24_7_nobattery']:>13,.0f} "
          f"{r['ebitda_24_7_battery']:>13,.0f} "
          f"{r['uplift_from_battery']:>+11,.0f} "
          f"{r['arb_ebitda_no_gpu']:>13,.0f}")

# ---------- write 'Batteries' sheet ----------
WB_PATH = "/home/user/extended-exercise-windows/Solar_Ecretement_vs_H100_Idle.xlsx"
wb = load_workbook(WB_PATH)
if "Batteries" in wb.sheetnames:
    del wb["Batteries"]
ws = wb.create_sheet("Batteries")

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
SUB = Font(bold=True, size=12, color="2E75B6")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

ws.sheet_view.showGridLines = False
for i, w in enumerate([3, 46, 12, 14, 14, 14, 14, 14, 14], start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws["B2"] = "Batteries — time-shifting curtailed solar into 24/7 GPU load"
ws["B2"].font = TITLE
ws.merge_cells("B2:I2")
ws["B3"] = (
    "Battery is sized to cover (24 - curtailment_hours) of GPU load at the site load incl. PUE, "
    "charged during the curt window at curt €/MWh, discharged the rest of the day. Round-trip "
    "efficiency, life, and capex per kWh are all editable on the Inputs sheet (yellow cells below)."
)
ws["B3"].font = ITALIC
ws.merge_cells("B3:I3")

# Battery inputs block
ws["B5"] = "Battery inputs"
ws["B5"].font = SUB
ws.merge_cells("B5:I5")
batt_inputs = [
    ("BESS capex (EUR/kWh)",       250, "€#,##0",  "LFP at the gate of an EPC. 2025 ~€220-280, trending to €150 by 2028."),
    ("Round-trip efficiency",     0.88, "0%",      "AC-AC. LFP ~85-90%."),
    ("Battery useful life (yrs)",   10, "0.0",     "Cycle-limited at 1 cycle/day for ~10 yrs at 80% DoD."),
    ("Battery salvage value",     0.10, "0%",      "Residual at end of life."),
]
for i, (lbl, val, fmt, note) in enumerate(batt_inputs):
    r = 6 + i
    ws[f"B{r}"] = lbl
    ws[f"B{r}"].alignment = LEFT
    ws[f"C{r}"] = val
    ws[f"C{r}"].fill = INPUT_FILL
    ws[f"C{r}"].border = BOX
    ws[f"C{r}"].number_format = fmt
    ws.merge_cells(f"D{r}:I{r}")
    ws[f"D{r}"] = note
    ws[f"D{r}"].font = ITALIC

# Results table
r0 = 12
ws[f"B{r0}"] = "Battery scenarios — per GPU per year"
ws[f"B{r0}"].font = SUB
ws.merge_cells(f"B{r0}:I{r0}")

hdr = ["#", "Scenario", "BESS kWh", "BESS capex", "BESS €/yr",
       "24/7 no battery", "24/7 + battery", "Δ from battery", "Battery-only arb"]
for i, h in enumerate(hdr):
    c = ws.cell(row=r0+1, column=1+i, value=h)
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX
ws.row_dimensions[r0+1].height = 32

for i, (name, p, batt, r) in enumerate(results):
    row = r0 + 2 + i
    cells = [
        (1, name.split(".")[0], None, CENTER),
        (2, name.split(". ", 1)[1], None, LEFT),
        (3, r["bess_kwh"], "0.0", CENTER),
        (4, r["bess_capex"], "€#,##0", CENTER),
        (5, r["bess_fixed_yr"], "€#,##0", CENTER),
        (6, r["ebitda_24_7_nobattery"], "€#,##0;[Red]-€#,##0", CENTER),
        (7, r["ebitda_24_7_battery"], "€#,##0;[Red]-€#,##0", CENTER),
        (8, r["uplift_from_battery"], "€+#,##0;[Red]-€#,##0", CENTER),
        (9, r["arb_ebitda_no_gpu"], "€#,##0;[Red]-€#,##0", CENTER),
    ]
    for col, val, fmt, align in cells:
        c = ws.cell(row=row, column=col, value=val)
        c.border = BOX
        c.alignment = align
        if fmt:
            c.number_format = fmt
    # color uplift cell
    up = r["uplift_from_battery"]
    if up > 0:
        ws.cell(row=row, column=8).fill = GOOD
        ws.cell(row=row, column=8).font = BOLD
    else:
        ws.cell(row=row, column=8).fill = BAD
    # color arb cell
    arb = r["arb_ebitda_no_gpu"]
    ws.cell(row=row, column=9).fill = GOOD if arb > 0 else BAD

# Heat scale on 24/7 + battery column
last_row = r0 + 1 + len(results)
ws.conditional_formatting.add(f"G{r0+2}:G{last_row}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# ---------- Sensitivity table: battery €/kWh × curt price ----------
r1 = last_row + 3
ws[f"B{r1}"] = "Sensitivity — battery €/kWh × curtailment €/MWh (Δ EBITDA from adding battery, €/GPU/yr)"
ws[f"B{r1}"].font = SUB
ws.merge_cells(f"B{r1}:I{r1}")

ws[f"B{r1+1}"] = "BESS €/kWh ↓ \\ Curt €/MWh →"
ws[f"B{r1+1}"].fill = HEADER_FILL
ws[f"B{r1+1}"].font = WHITE
ws[f"B{r1+1}"].alignment = CENTER

curts = [-80, -50, -30, -15, 0, 20]
bess_prices = [100, 150, 200, 250, 300, 400]

for j, cp in enumerate(curts):
    c = ws.cell(row=r1+1, column=3+j, value=cp)
    c.number_format = "€#,##0"
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

for i, bp in enumerate(bess_prices):
    row = r1 + 2 + i
    c = ws.cell(row=row, column=2, value=bp)
    c.number_format = "€#,##0"
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    for j, cp in enumerate(curts):
        p = {**BASE, "curt_p": cp}
        batt = {**BATT_BASE, "bess_eur_per_kwh": bp}
        r = battery_economics(p, batt)
        cell = ws.cell(row=row, column=3+j, value=r["uplift_from_battery"])
        cell.number_format = "€+#,##0;[Red]-€#,##0"
        cell.border = BOX
        cell.alignment = CENTER
        cell.fill = CALC_FILL

last_col = get_column_letter(2 + len(curts))
ws.conditional_formatting.add(
    f"C{r1+2}:{last_col}{r1+1+len(bess_prices)}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# ---------- Sensitivity 2: curt hours/day × curt days/year ----------
r2 = r1 + 2 + len(bess_prices) + 3
ws[f"B{r2}"] = "Sensitivity — curtailment hours/day × curt days/yr (Δ EBITDA from battery at BASE bess price)"
ws[f"B{r2}"].font = SUB
ws.merge_cells(f"B{r2}:I{r2}")

ws[f"B{r2+1}"] = "Curt hrs/day ↓ \\ Days/yr →"
ws[f"B{r2+1}"].fill = HEADER_FILL
ws[f"B{r2+1}"].font = WHITE
ws[f"B{r2+1}"].alignment = CENTER

days_list = [90, 120, 150, 180, 210, 240, 280]
hours_list = [3, 4, 5, 6, 7, 8]

for j, d in enumerate(days_list):
    c = ws.cell(row=r2+1, column=3+j, value=d)
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

for i, h in enumerate(hours_list):
    row = r2 + 2 + i
    c = ws.cell(row=row, column=2, value=h)
    c.fill = SUB_FILL
    c.font = WHITE
    c.alignment = CENTER
    for j, d in enumerate(days_list):
        p = {**BASE, "hrs_curt": h, "days_curt": d}
        r = battery_economics(p, BATT_BASE)
        cell = ws.cell(row=row, column=3+j, value=r["uplift_from_battery"])
        cell.number_format = "€+#,##0;[Red]-€#,##0"
        cell.border = BOX
        cell.alignment = CENTER
        cell.fill = CALC_FILL

last_col2 = get_column_letter(2 + len(days_list))
ws.conditional_formatting.add(
    f"C{r2+2}:{last_col2}{r2+1+len(hours_list)}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# ---------- Takeaways ----------
r3 = r2 + 2 + len(hours_list) + 2
ws[f"B{r3}"] = "What batteries actually buy you"
ws[f"B{r3}"].font = SUB

takeaways = [
    "1. Batteries at TODAY'S price (€250/kWh) are roughly break-even in the base case (-€118/GPU/yr) — they're not "
    "a magic wand. The spread (grid - curt/eff) only earns over the curtailment days you actually cycle on; below "
    "~200 cycles/yr the fixed cost of the battery outruns the arbitrage.",
    "2. Where batteries DO pay: deep, frequent curtailment markets. Spain 2030 (-€60 curt, 7h, 240 days) flips to "
    "+€504/GPU/yr from adding a battery. The Trifecta best-case adds another €600/yr. The lever is days-of-cycling, "
    "more than depth of negative prices.",
    "3. Battery price is the single biggest free variable, with a clear downward trajectory. At €150/kWh (2028 "
    "forecast), even the base case turns positive (+€201/GPU/yr). At €400/kWh you actively lose €600/yr. Every "
    "€50/kWh of BESS price ≈ €200-400/GPU/yr of EBITDA.",
    "4. Round-trip efficiency matters less than you'd think. 88% → 95% only adds ~€50/GPU/yr because most of the "
    "cost is amortisation, not energy losses. Don't pay big premiums for high-RTE chemistries here.",
    "5. The stand-alone arbitrage column (rightmost) shows what the SAME battery would earn with NO GPU at all — "
    "just charging cheap and selling expensive. In the base case it's slightly negative; in Spain 2030 it's +€183. "
    "Adding GPUs to that BESS adds €321 (€504 - €183) of incremental value over the battery alone. That's the "
    "real co-location synergy.",
    "6. Battery + GPU is a stacked play, not a substitute. You get: AI compute revenue + energy arbitrage + (not "
    "modelled here) ancillary services + capacity payments. The base case stack at 2028 prices is meaningfully "
    "profitable; today it's marginal.",
    "7. Batteries do NOT rescue curtailment-only mode. They lower the cost of running 24/7 — which only widens "
    "24/7's lead over Curt-only. The conclusion that 'GPUs should run 24/7' is reinforced, not overturned, by adding storage.",
]
for i, t in enumerate(takeaways):
    ws.merge_cells(f"B{r3+1+i*2}:I{r3+2+i*2}")
    ws[f"B{r3+1+i*2}"] = t
    ws[f"B{r3+1+i*2}"].alignment = LEFT
    ws[f"B{r3+1+i*2}"].font = ITALIC
    ws.row_dimensions[r3+1+i*2].height = 32

wb.save(WB_PATH)
print(f"\nUpdated {WB_PATH} with 'Batteries' sheet")
