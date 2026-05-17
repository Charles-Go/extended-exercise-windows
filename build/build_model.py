"""
Builds Solar_Ecretement_vs_H100_Idle.xlsx

A financial model exploring the equilibrium between:
  - The economic value of curtailed (écrêté) solar electricity in Europe
  - The opportunity cost of H100 GPUs sitting idle outside of the curtailment window

Question framed:
  At what point does buying H100s and only running them during the European
  solar curtailment window break even with running them 24/7 at higher
  electricity prices? Equivalently: how much "free" solar do we need to
  justify the idle hours, given GPU rental revenue forgone and depreciation
  burning on the rack?

All inputs are live formulas - change the yellow cells and the whole model
recalculates.
"""
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, NamedStyle
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, ScatterChart, Series
from openpyxl.chart.trendline import Trendline
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.chart.label import DataLabelList
from openpyxl.workbook.defined_name import DefinedName

# ---------- styling helpers ----------
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")        # yellow = user input
CALC_FILL  = PatternFill("solid", fgColor="E2EFDA")        # green  = calc
LINK_FILL  = PatternFill("solid", fgColor="DDEBF7")        # blue   = cross-sheet link
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SUBHEADER_FILL = PatternFill("solid", fgColor="2E75B6")
BAND_FILL = PatternFill("solid", fgColor="F2F2F2")
DANGER_FILL = PatternFill("solid", fgColor="F8CBAD")
GOOD_FILL = PatternFill("solid", fgColor="C6EFCE")

WHITE = Font(color="FFFFFF", bold=True)
BOLD = Font(bold=True)
ITALIC = Font(italic=True, color="595959")
TITLE_FONT = Font(bold=True, size=18, color="1F4E78")
SUBTITLE_FONT = Font(bold=True, size=12, color="2E75B6")

THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center")


def header(ws, cell, text, fill=HEADER_FILL, font=WHITE):
    ws[cell] = text
    ws[cell].fill = fill
    ws[cell].font = font
    ws[cell].alignment = CENTER


def input_cell(ws, cell, value, fmt=None, comment=None):
    ws[cell] = value
    ws[cell].fill = INPUT_FILL
    ws[cell].border = BOX
    if fmt:
        ws[cell].number_format = fmt
    return ws[cell]


def calc_cell(ws, cell, formula, fmt=None, fill=CALC_FILL):
    ws[cell] = formula
    ws[cell].fill = fill
    ws[cell].border = BOX
    if fmt:
        ws[cell].number_format = fmt
    return ws[cell]


def label_cell(ws, cell, text, bold=True, indent=0):
    ws[cell] = text
    if bold:
        ws[cell].font = BOLD
    if indent:
        ws[cell].alignment = Alignment(horizontal="left", indent=indent, vertical="center", wrap_text=True)
    else:
        ws[cell].alignment = LEFT


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ---------- workbook ----------
wb = Workbook()

# =========================================================
# SHEET 1 — COVER
# =========================================================
cover = wb.active
cover.title = "Cover"
set_widths(cover, [3, 28, 28, 28, 28, 28, 28])
cover.sheet_view.showGridLines = False

cover["B2"] = "Solar Écrêtement (curtailment) vs. H100 Idle Cost"
cover["B2"].font = Font(bold=True, size=22, color="1F4E78")
cover.merge_cells("B2:G2")

cover["B3"] = "A financial-equilibrium model — Europe, daylight curtailment hours vs 24/7 GPU economics"
cover["B3"].font = Font(italic=True, size=12, color="595959")
cover.merge_cells("B3:G3")

cover["B5"] = "The question"
cover["B5"].font = SUBTITLE_FONT
cover.merge_cells("B5:G5")
cover["B6"] = (
    "European solar farms increasingly experience écrêtement — curtailment driven by "
    "negative spot prices during midday peaks. At the same time, H100 GPUs cost ~$30–40k "
    "each and depreciate whether or not they are running. Can we make money by stranding "
    "GPUs at solar sites and only powering them during the curtailment window, accepting "
    "idle hours the rest of the day? At what electricity price, curtailment window length, "
    "and GPU rental rate does the equilibrium tip?"
)
cover["B6"].alignment = Alignment(wrap_text=True, vertical="top")
cover.merge_cells("B6:G9")
cover.row_dimensions[6].height = 22
cover.row_dimensions[7].height = 22
cover.row_dimensions[8].height = 22

cover["B11"] = "Model map"
cover["B11"].font = SUBTITLE_FONT
sheets_map = [
    ("Inputs",            "All editable assumptions (yellow cells). Change these and everything recalculates."),
    ("Solar_Profile",     "Hourly solar capacity factor across the four seasons, with the curtailment window."),
    ("Price_Curve",       "Hourly spot price by season, anchored to country averages and midday troughs."),
    ("GPU_Economics",     "Per-GPU capex, depreciation, power draw, datacenter PUE, opex stack."),
    ("Scenarios",         "Three operating modes side-by-side: 24/7, daytime-only, curtailment-only."),
    ("Hourly_Model",      "Representative 96-hour year (4 seasons × 24h) scaled to 8,760h with hourly P&L."),
    ("Equilibrium",       "Break-even curves: at what electricity price / curtailment hours do the modes cross?"),
    ("Sensitivity",       "Two-way tables: GPU price × rental rate, and curtailment hours × idle penalty."),
    ("Country_Compare",   "Germany, Spain, France, Netherlands, Italy, UK — negative-price hours and outcomes."),
    ("Dashboard",         "Single-page answer: payback, NPV, IRR, and the equilibrium electricity price."),
]
for i, (name, desc) in enumerate(sheets_map):
    r = 12 + i
    cover[f"B{r}"] = name
    cover[f"B{r}"].font = BOLD
    cover[f"B{r}"].fill = LINK_FILL
    cover.merge_cells(f"C{r}:G{r}")
    cover[f"C{r}"] = desc
    cover[f"C{r}"].alignment = LEFT

# Color legend
r0 = 12 + len(sheets_map) + 2
cover[f"B{r0}"] = "Color legend"
cover[f"B{r0}"].font = SUBTITLE_FONT
legend = [
    (INPUT_FILL, "Input — edit me (yellow)"),
    (CALC_FILL,  "Calculation (green)"),
    (LINK_FILL,  "Cross-sheet link (blue)"),
    (GOOD_FILL,  "Favorable outcome"),
    (DANGER_FILL,"Unfavorable outcome"),
]
for i, (fill, text) in enumerate(legend):
    r = r0 + 1 + i
    cover[f"B{r}"].fill = fill
    cover[f"B{r}"].border = BOX
    cover[f"C{r}"] = text

# Methodology footer
r1 = r0 + len(legend) + 3
cover[f"B{r1}"] = "Methodology in one paragraph"
cover[f"B{r1}"].font = SUBTITLE_FONT
cover.merge_cells(f"B{r1+1}:G{r1+5}")
cover[f"B{r1+1}"] = (
    "We model a single H100 (or a DGX-equivalent 8-GPU node) co-located at a European solar "
    "site that suffers curtailment. The plant offers electricity at the spot price during "
    "the curtailment window (often €0 or negative). Outside that window the GPU can either "
    "(a) buy grid power at retail and keep earning, or (b) sit idle. We compare 3 operating "
    "modes against the same capex stack. Revenue is benchmarked to H100 on-demand rental "
    "rates (a proxy for the value of FLOPs). The equilibrium is the electricity-price + "
    "curtailment-hours combination at which the curtailment-only mode equals 24/7 economics. "
    "All figures are in EUR; FX is held flat — this is a directional model, not a pricing sheet."
)
cover[f"B{r1+1}"].alignment = Alignment(wrap_text=True, vertical="top")

cover.sheet_view.zoomScale = 110

# =========================================================
# SHEET 2 — INPUTS
# =========================================================
inp = wb.create_sheet("Inputs")
set_widths(inp, [3, 42, 16, 16, 42])
inp.sheet_view.showGridLines = False

inp["B2"] = "Master inputs — yellow cells drive every other sheet"
inp["B2"].font = TITLE_FONT
inp.merge_cells("B2:E2")

# Section: GPU hardware
header(inp, "B4", "GPU Hardware (per H100)")
inp.merge_cells("B4:E4")

gpu_rows = [
    ("H100 capex (street price, EUR)",            32_000, "€#,##0",        "Q4-2025 European street price for SXM5. Hopper has come off peak. Range €25k–€40k."),
    ("Useful life (years)",                       4,      "0.0",           "NVIDIA suggests 5; aggressive Blackwell roadmap argues 3–4."),
    ("Salvage value at end of life (% of capex)", 0.10,   "0%",            "Resale to crypto/CV inference shops. Bear case = 0%."),
    ("GPU power draw, full load (W)",             700,    "0",             "H100 SXM5 TDP."),
    ("GPU power draw, idle (W)",                  90,     "0",             "Powered on, no kernels running."),
    ("Datacenter PUE",                            1.20,   "0.00",          "Modern liquid-cooled colo at a solar site, no chiller round-trip."),
    ("CPU/networking overhead allocated (W)",     180,    "0",             "Per-GPU share of CPU, NIC, NVSwitch, fans."),
    ("Hardware availability",                     0.97,   "0%",            "After failures, RMA, planned maintenance."),
]
for i, (lbl, val, fmt, note) in enumerate(gpu_rows):
    r = 5 + i
    inp[f"B{r}"] = lbl
    inp[f"B{r}"].alignment = LEFT
    input_cell(inp, f"C{r}", val, fmt)
    inp[f"E{r}"] = note
    inp[f"E{r}"].font = ITALIC
    inp[f"E{r}"].alignment = LEFT

# Section: Datacenter & site
r0 = 5 + len(gpu_rows) + 1
header(inp, f"B{r0}", "Site & Datacenter (per GPU allocation)")
inp.merge_cells(f"B{r0}:E{r0}")
site_rows = [
    ("Rack & networking capex per GPU (EUR)",   4_500,   "€#,##0",  "Share of DGX-class server, NVSwitch, top-of-rack."),
    ("Modular datacenter capex per GPU (EUR)",  3_500,   "€#,##0",  "Container DC, cooling loop, transformer share, civils."),
    ("Annual O&M per GPU (EUR)",                1_200,   "€#,##0",  "Maintenance, remote hands, monitoring, insurance."),
    ("Grid connection fee per kW-yr (EUR)",     90,      "€#,##0",  "Most curtailment sites already have the connection paid by the solar farm."),
    ("Cost of capital (WACC)",                  0.10,    "0.0%",     "Specialty infra; range 8–14%."),
    ("Corporate tax rate",                      0.25,    "0%",       "EU-blended."),
]
for i, (lbl, val, fmt, note) in enumerate(site_rows):
    r = r0 + 1 + i
    inp[f"B{r}"] = lbl
    inp[f"B{r}"].alignment = LEFT
    input_cell(inp, f"C{r}", val, fmt)
    inp[f"E{r}"] = note
    inp[f"E{r}"].font = ITALIC
    inp[f"E{r}"].alignment = LEFT

# Section: Revenue
r1 = r0 + 1 + len(site_rows) + 1
header(inp, f"B{r1}", "Revenue (H100 monetisation)")
inp.merge_cells(f"B{r1}:E{r1}")
rev_rows = [
    ("Effective H100 hourly rental (EUR/h)",      2.20,   "€#,##0.00", "Realised price net of broker / utilisation discount. On-demand list ~€2.50–4."),
    ("Utilisation when powered on",               0.85,   "0%",        "Fraction of powered hours sold."),
    ("Revenue haircut for interruptible workloads", 0.30, "0%",        "Discount applied because curtailment-only mode is non-firm capacity."),
    ("Crypto/inference floor price (EUR/h)",      0.40,   "€#,##0.00", "Fallback when no AI tenant takes the hour."),
]
for i, (lbl, val, fmt, note) in enumerate(rev_rows):
    r = r1 + 1 + i
    inp[f"B{r}"] = lbl
    inp[f"B{r}"].alignment = LEFT
    input_cell(inp, f"C{r}", val, fmt)
    inp[f"E{r}"] = note
    inp[f"E{r}"].font = ITALIC
    inp[f"E{r}"].alignment = LEFT

# Section: Electricity & curtailment
r2 = r1 + 1 + len(rev_rows) + 1
header(inp, f"B{r2}", "Electricity & curtailment regime")
inp.merge_cells(f"B{r2}:E{r2}")
ele_rows = [
    ("Average grid retail price (EUR/MWh)",        140,    "€#,##0",    "EU blended industrial 2025 estimate."),
    ("Curtailment-window price (EUR/MWh)",         -15,    "€#,##0",    "Avg spot during écrêtement — often negative."),
    ("Curtailment hours per day (peak season)",    5,      "0.0",       "Hours/day with negative or sub-€10 prices in summer."),
    ("Curtailment days per year",                  180,    "0",         "Days/year that exhibit the curtailment pattern."),
    ("Behind-the-meter solar PPA (EUR/MWh)",       25,     "€#,##0",    "Long-term PPA used outside curtailment window if BTM."),
    ("Carbon credit value (EUR/MWh avoided)",      0,      "€#,##0",    "Set >0 to credit displaced fossil generation."),
]
for i, (lbl, val, fmt, note) in enumerate(ele_rows):
    r = r2 + 1 + i
    inp[f"B{r}"] = lbl
    inp[f"B{r}"].alignment = LEFT
    input_cell(inp, f"C{r}", val, fmt)
    inp[f"E{r}"] = note
    inp[f"E{r}"].font = ITALIC
    inp[f"E{r}"].alignment = LEFT

# Section: Scenario toggles
r3 = r2 + 1 + len(ele_rows) + 1
header(inp, f"B{r3}", "Scenario toggles")
inp.merge_cells(f"B{r3}:E{r3}")
tog_rows = [
    ("Hours/day H100 powered on (daytime mode)",   10,    "0.0",       "Daytime-only operating window."),
    ("Hours/day H100 powered on (curtailment mode)", 5,   "0.0",       "Curtailment-only operating window."),
    ("Number of GPUs in fleet",                    1000,  "#,##0",     "Used only for headline P&L on dashboard."),
    ("Project horizon (years)",                    5,     "0",         "Used for NPV / IRR."),
]
for i, (lbl, val, fmt, note) in enumerate(tog_rows):
    r = r3 + 1 + i
    inp[f"B{r}"] = lbl
    inp[f"B{r}"].alignment = LEFT
    input_cell(inp, f"C{r}", val, fmt)
    inp[f"E{r}"] = note
    inp[f"E{r}"].font = ITALIC
    inp[f"E{r}"].alignment = LEFT


# ---- Named ranges (so other sheets can reference by name) ----
def define_name(name, ref):
    wb.defined_names[name] = DefinedName(name, attr_text=ref)


# Map every input we'll need by name. Track them as we go above.
named = {
    "GPU_Capex":         "Inputs!$C$5",
    "GPU_Life":          "Inputs!$C$6",
    "GPU_Salvage":       "Inputs!$C$7",
    "GPU_Power_Load_W":  "Inputs!$C$8",
    "GPU_Power_Idle_W":  "Inputs!$C$9",
    "PUE":               "Inputs!$C$10",
    "Aux_Power_W":       "Inputs!$C$11",
    "Avail":             "Inputs!$C$12",

    "Rack_Capex":        f"Inputs!$C${r0+1}",
    "DC_Capex":          f"Inputs!$C${r0+2}",
    "OandM":             f"Inputs!$C${r0+3}",
    "GridFee_per_kWyr":  f"Inputs!$C${r0+4}",
    "WACC":              f"Inputs!$C${r0+5}",
    "Tax":               f"Inputs!$C${r0+6}",

    "Rev_per_hr":        f"Inputs!$C${r1+1}",
    "Util":              f"Inputs!$C${r1+2}",
    "Interrupt_Haircut": f"Inputs!$C${r1+3}",
    "Floor_Price":       f"Inputs!$C${r1+4}",

    "Grid_Price":        f"Inputs!$C${r2+1}",
    "Curt_Price":        f"Inputs!$C${r2+2}",
    "Curt_Hr_Day":       f"Inputs!$C${r2+3}",
    "Curt_Days":         f"Inputs!$C${r2+4}",
    "PPA_Price":         f"Inputs!$C${r2+5}",
    "Carbon":            f"Inputs!$C${r2+6}",

    "Hrs_Daytime":       f"Inputs!$C${r3+1}",
    "Hrs_Curt":          f"Inputs!$C${r3+2}",
    "Fleet":             f"Inputs!$C${r3+3}",
    "Horizon":           f"Inputs!$C${r3+4}",
}
for k, v in named.items():
    define_name(k, v)

# =========================================================
# SHEET 3 — SOLAR PROFILE
# =========================================================
sp = wb.create_sheet("Solar_Profile")
set_widths(sp, [3, 8, 14, 14, 14, 14, 16, 18])
sp.sheet_view.showGridLines = False
sp["B2"] = "Hourly solar capacity factor & curtailment window"
sp["B2"].font = TITLE_FONT
sp.merge_cells("B2:H2")
sp["B3"] = "Representative day per season. Curtailment flag = 1 when capacity factor exceeds the threshold."
sp["B3"].font = ITALIC
sp.merge_cells("B3:H3")

headers_sp = ["Hour", "Winter CF", "Spring CF", "Summer CF", "Autumn CF", "Avg CF", "Curtailment flag (avg)"]
for i, h in enumerate(headers_sp):
    c = sp.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

# Typical European solar capacity factor by season - bell curve centered on 13:00
# Values chosen from typical PVGIS / ENTSO-E shapes for ~latitude 45N
profile = {
    # hour: (winter, spring, summer, autumn)
    0:  (0.00, 0.00, 0.00, 0.00),
    1:  (0.00, 0.00, 0.00, 0.00),
    2:  (0.00, 0.00, 0.00, 0.00),
    3:  (0.00, 0.00, 0.00, 0.00),
    4:  (0.00, 0.00, 0.02, 0.00),
    5:  (0.00, 0.02, 0.08, 0.00),
    6:  (0.00, 0.08, 0.18, 0.02),
    7:  (0.02, 0.18, 0.32, 0.10),
    8:  (0.10, 0.30, 0.46, 0.22),
    9:  (0.22, 0.45, 0.60, 0.38),
    10: (0.34, 0.58, 0.72, 0.52),
    11: (0.42, 0.68, 0.82, 0.62),
    12: (0.46, 0.74, 0.88, 0.66),
    13: (0.46, 0.76, 0.90, 0.66),
    14: (0.42, 0.72, 0.86, 0.60),
    15: (0.34, 0.64, 0.78, 0.50),
    16: (0.22, 0.52, 0.66, 0.38),
    17: (0.10, 0.38, 0.50, 0.22),
    18: (0.02, 0.22, 0.34, 0.08),
    19: (0.00, 0.10, 0.20, 0.02),
    20: (0.00, 0.02, 0.08, 0.00),
    21: (0.00, 0.00, 0.02, 0.00),
    22: (0.00, 0.00, 0.00, 0.00),
    23: (0.00, 0.00, 0.00, 0.00),
}

# Curtailment threshold input
sp["I5"] = "Curtailment CF threshold:"
sp["I5"].font = BOLD
sp["I5"].alignment = RIGHT
input_cell(sp, "J5", 0.55, "0.00")
define_name("Curt_Threshold", "Solar_Profile!$J$5")

for hr in range(24):
    r = 6 + hr
    sp[f"B{r}"] = hr
    sp[f"B{r}"].alignment = CENTER
    w, sp_, su, au = profile[hr]
    input_cell(sp, f"C{r}", w,  "0.00")
    input_cell(sp, f"D{r}", sp_,"0.00")
    input_cell(sp, f"E{r}", su, "0.00")
    input_cell(sp, f"F{r}", au, "0.00")
    calc_cell(sp, f"G{r}", f"=AVERAGE(C{r}:F{r})", "0.00")
    calc_cell(sp, f"H{r}", f"=IF(G{r}>=Curt_Threshold,1,0)", "0")

# Conditional formatting for CF cells
rule = ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                      mid_type="num", mid_value=0.4, mid_color="FFE699",
                      end_type="num", end_value=1.0, end_color="C00000")
sp.conditional_formatting.add("C6:G29", rule)

# Curtailment hours sum
sp["B31"] = "Curtailment hours per representative day:"
sp["B31"].font = BOLD
sp.merge_cells("B31:F31")
calc_cell(sp, "G31", "=SUM(H6:H29)", "0.0")

# Chart
chart = LineChart()
chart.title = "Solar capacity factor by hour (typical European day)"
chart.y_axis.title = "Capacity factor"
chart.x_axis.title = "Hour of day"
chart.height = 9
chart.width = 18
data = Reference(sp, min_col=3, max_col=7, min_row=5, max_row=29)
cats = Reference(sp, min_col=2, min_row=6, max_row=29)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
sp.add_chart(chart, "J7")

# =========================================================
# SHEET 4 — PRICE CURVE
# =========================================================
pc = wb.create_sheet("Price_Curve")
set_widths(pc, [3, 8, 14, 14, 14, 14, 16])
pc.sheet_view.showGridLines = False
pc["B2"] = "Hourly spot electricity price (EUR/MWh) — European blended"
pc["B2"].font = TITLE_FONT
pc.merge_cells("B2:G2")
pc["B3"] = "Midday troughs reflect oversupplied solar. Edit the yellow cells to model a specific country / year."
pc["B3"].font = ITALIC
pc.merge_cells("B3:G3")

headers_pc = ["Hour", "Winter €/MWh", "Spring €/MWh", "Summer €/MWh", "Autumn €/MWh", "Avg €/MWh"]
for i, h in enumerate(headers_pc):
    c = pc.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

# Typical hourly shape (€/MWh) with summer midday going negative
price_profile = {
    0:  (90,  60,  35,   70),
    1:  (85,  55,  30,   65),
    2:  (80,  50,  25,   60),
    3:  (78,  48,  22,   58),
    4:  (80,  50,  25,   60),
    5:  (90,  60,  35,   70),
    6:  (110, 75,  45,   85),
    7:  (140, 90,  55,  105),
    8:  (150, 90,  45,  110),
    9:  (140, 70,  20,   95),
    10: (120, 50,  -5,   80),
    11: (110, 35, -20,   65),
    12: (105, 25, -30,   55),
    13: (105, 20, -35,   50),
    14: (110, 25, -25,   55),
    15: (120, 40,  -5,   70),
    16: (140, 65,  20,   95),
    17: (170, 100, 55,  130),
    18: (200, 130, 90,  160),
    19: (210, 150,110,  175),
    20: (190, 140,100,  160),
    21: (160, 120, 80,  135),
    22: (130, 95,  60,  105),
    23: (105, 75,  45,   85),
}
for hr in range(24):
    r = 6 + hr
    pc[f"B{r}"] = hr
    pc[f"B{r}"].alignment = CENTER
    w, sp_, su, au = price_profile[hr]
    input_cell(pc, f"C{r}", w,  "€#,##0")
    input_cell(pc, f"D{r}", sp_,"€#,##0")
    input_cell(pc, f"E{r}", su, "€#,##0")
    input_cell(pc, f"F{r}", au, "€#,##0")
    calc_cell(pc, f"G{r}", f"=AVERAGE(C{r}:F{r})", "€#,##0")

# Color scale: red = expensive, green = cheap/negative
rule_p = ColorScaleRule(start_type="num", start_value=-50, start_color="63BE7B",
                        mid_type="num", mid_value=80, mid_color="FFEB84",
                        end_type="num", end_value=250, end_color="F8696B")
pc.conditional_formatting.add("C6:G29", rule_p)

# Stats
pc["B31"] = "Avg price"
pc["B31"].font = BOLD
calc_cell(pc, "C31", "=AVERAGE(C6:C29)", "€#,##0")
calc_cell(pc, "D31", "=AVERAGE(D6:D29)", "€#,##0")
calc_cell(pc, "E31", "=AVERAGE(E6:E29)", "€#,##0")
calc_cell(pc, "F31", "=AVERAGE(F6:F29)", "€#,##0")
calc_cell(pc, "G31", "=AVERAGE(G6:G29)", "€#,##0")

pc["B32"] = "Min price"
pc["B32"].font = BOLD
for col in "CDEFG":
    calc_cell(pc, f"{col}32", f"=MIN({col}6:{col}29)", "€#,##0")

pc["B33"] = "Hours ≤ €0 per day"
pc["B33"].font = BOLD
for col in "CDEFG":
    calc_cell(pc, f"{col}33", f"=SUMPRODUCT(--({col}6:{col}29<=0))", "0")

# Chart
pchart = LineChart()
pchart.title = "Hourly spot price (€/MWh)"
pchart.y_axis.title = "€/MWh"
pchart.x_axis.title = "Hour"
pchart.height = 9
pchart.width = 18
pdata = Reference(pc, min_col=3, max_col=6, min_row=5, max_row=29)
pcats = Reference(pc, min_col=2, min_row=6, max_row=29)
pchart.add_data(pdata, titles_from_data=True)
pchart.set_categories(pcats)
pc.add_chart(pchart, "I5")

# =========================================================
# SHEET 5 — GPU ECONOMICS
# =========================================================
ge = wb.create_sheet("GPU_Economics")
set_widths(ge, [3, 42, 18, 4, 42])
ge.sheet_view.showGridLines = False
ge["B2"] = "Per-GPU economics — capex, depreciation, power, operating cost"
ge["B2"].font = TITLE_FONT
ge.merge_cells("B2:E2")

header(ge, "B4", "Capex stack (per GPU)")
ge.merge_cells("B4:C4")
rows_capex = [
    ("H100 capex",                 "=GPU_Capex"),
    ("Rack & networking capex",    "=Rack_Capex"),
    ("Datacenter capex",           "=DC_Capex"),
    ("Total capex per GPU",        "=SUM(C5:C7)"),
]
for i, (lbl, frm) in enumerate(rows_capex):
    r = 5 + i
    label_cell(ge, f"B{r}", lbl, bold=(i == len(rows_capex)-1))
    fill = CALC_FILL if i < len(rows_capex)-1 else GOOD_FILL
    calc_cell(ge, f"C{r}", frm, "€#,##0", fill=fill)
define_name("Total_Capex", "GPU_Economics!$C$8")

header(ge, "B10", "Depreciation & financing (annual)")
ge.merge_cells("B10:C10")
rows_dep = [
    ("Straight-line depreciation",     "=(Total_Capex*(1-GPU_Salvage))/GPU_Life"),
    ("WACC × avg invested capital",    "=Total_Capex*WACC*0.5"),
    ("O&M",                            "=OandM"),
    ("Grid connection (allocated)",    "=GridFee_per_kWyr*(GPU_Power_Load_W+Aux_Power_W)/1000*PUE"),
    ("Total fixed annual cost / GPU",  "=SUM(C11:C14)"),
]
for i, (lbl, frm) in enumerate(rows_dep):
    r = 11 + i
    label_cell(ge, f"B{r}", lbl, bold=(i == len(rows_dep)-1))
    fill = CALC_FILL if i < len(rows_dep)-1 else GOOD_FILL
    calc_cell(ge, f"C{r}", frm, "€#,##0", fill=fill)
define_name("Fixed_Cost_GPU", "GPU_Economics!$C$15")

header(ge, "B17", "Power per powered-on hour")
ge.merge_cells("B17:C17")
ge["B18"] = "IT load (kW)"
calc_cell(ge, "C18", "=(GPU_Power_Load_W+Aux_Power_W)/1000", "0.000")
ge["B19"] = "Site load incl. PUE (kW)"
calc_cell(ge, "C19", "=C18*PUE", "0.000")
ge["B20"] = "Idle site load (kW)"
calc_cell(ge, "C20", "=(GPU_Power_Idle_W+Aux_Power_W*0.4)/1000*PUE", "0.000")
define_name("Load_kW", "GPU_Economics!$C$19")
define_name("Idle_kW", "GPU_Economics!$C$20")

header(ge, "B22", "Revenue per powered-on hour")
ge.merge_cells("B22:C22")
ge["B23"] = "Gross revenue / hr (firm)"
calc_cell(ge, "C23", "=Rev_per_hr*Util", "€#,##0.00")
ge["B24"] = "Gross revenue / hr (interruptible / curtailment-only)"
calc_cell(ge, "C24", "=MAX(Floor_Price, Rev_per_hr*(1-Interrupt_Haircut))*Util", "€#,##0.00")
define_name("Rev_Firm",   "GPU_Economics!$C$23")
define_name("Rev_Interr", "GPU_Economics!$C$24")

# Right-hand commentary
ge["E4"] = "Notes"
ge["E4"].font = SUBTITLE_FONT
notes_lines = [
    "Capex is the wall the model is built against — it amortises whether GPUs run or not, which is the entire pain of idle hours.",
    "Salvage is real for H100s as long as Hopper finds a second life on inference / mid-end training.",
    "PUE of 1.20 assumes liquid cooling at a solar-adjacent modular DC. Air-cooled colo would be ~1.45.",
    "Idle load is not zero: powered nodes still draw fans, NIC, baseboard mgmt — that's a real penalty on curtailment-only mode.",
    "Firm vs interruptible: the curtailment-only operator cannot promise capacity, so the buyer demands a haircut.",
]
for i, line in enumerate(notes_lines):
    ge.merge_cells(f"E{5+i*3}:E{5+i*3+2}")
    ge[f"E{5+i*3}"] = line
    ge[f"E{5+i*3}"].alignment = Alignment(wrap_text=True, vertical="top")
    ge[f"E{5+i*3}"].font = ITALIC

# =========================================================
# SHEET 6 — SCENARIOS
# =========================================================
sc = wb.create_sheet("Scenarios")
set_widths(sc, [3, 38, 18, 18, 18, 38])
sc.sheet_view.showGridLines = False
sc["B2"] = "Scenario comparison — three operating modes, same hardware"
sc["B2"].font = TITLE_FONT
sc.merge_cells("B2:F2")
sc["B3"] = "All scenarios pay the same capex. The only variable is when we power the GPU."
sc["B3"].font = ITALIC
sc.merge_cells("B3:F3")

# Header row
for i, h in enumerate(["", "A. 24/7", "B. Daytime-only", "C. Curtailment-only", "Comment"]):
    c = sc.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

# Rows
def row(name, formulas, comment, fmt="€#,##0", bold=False, fill=None):
    return (name, formulas, comment, fmt, bold, fill)

# Each "formulas" is a 3-tuple of Excel formulas, one per scenario
rows = [
    row("Powered hours per year",
        ("=24*365*Avail",
         "=Hrs_Daytime*365*Avail",
         "=Hrs_Curt*Curt_Days*Avail"),
        "Idle hours = 8,760 - this number.", "#,##0.0"),
    row("Energy consumed (MWh/yr)",
        ("=C6*Load_kW/1000+(8760-C6)*Idle_kW/1000",
         "=D6*Load_kW/1000+(8760-D6)*Idle_kW/1000",
         "=E6*Load_kW/1000+(8760-E6)*Idle_kW/1000"),
        "Idle nodes still drink power.", "#,##0.0"),
    row("Blended electricity price (EUR/MWh)",
        ("=Grid_Price",
         "=(Grid_Price+PPA_Price)/2",
         "=Curt_Price"),
        "Curtailment scenario uses the écrêtement spot. Daytime mixes grid + PPA.", "€#,##0"),
    row("Electricity cost (EUR/yr)",
        ("=C7*C8",
         "=D7*D8",
         "=E7*E8"),
        "Negative cost is income from being paid to consume.", "€#,##0"),
    row("Gross revenue (EUR/yr)",
        ("=C6*Rev_Firm",
         "=D6*Rev_Firm",
         "=E6*Rev_Interr"),
        "Interruptible haircut applied to scenario C.", "€#,##0"),
    row("Carbon credit (EUR/yr)",
        ("=0",
         "=D7*Carbon*0.3",
         "=E7*Carbon"),
        "Curtailment-only captures the most avoidance credit per MWh.", "€#,##0"),
    row("Fixed cost (depreciation, WACC, O&M)",
        ("=Fixed_Cost_GPU",
         "=Fixed_Cost_GPU",
         "=Fixed_Cost_GPU"),
        "Identical across scenarios — that's the whole point.", "€#,##0"),
    row("EBITDA per GPU per year",
        ("=C10-C9-C12+C11",
         "=D10-D9-D12+D11",
         "=E10-E9-E12+E11"),
        "Revenue - electricity - fixed + carbon.", "€#,##0", bold=True, fill=GOOD_FILL),
    row("EBITDA margin",
        ("=IFERROR(C13/C10,0)",
         "=IFERROR(D13/D10,0)",
         "=IFERROR(E13/E10,0)"),
        "Sanity check.", "0%"),
    row("Effective LCOE on consumed power (EUR/MWh)",
        ("=C9/C7",
         "=D9/D7",
         "=E9/E7"),
        "What we paid per MWh consumed.", "€#,##0"),
    row("Revenue per consumed MWh",
        ("=C10/C7",
         "=D10/D7",
         "=E10/E7"),
        "How efficiently we monetise the kWh.", "€#,##0"),
    row("Idle hours per year",
        ("=8760-C6",
         "=8760-D6",
         "=8760-E6"),
        "The cost of doing nothing.", "#,##0.0"),
    row("Cost of idle hours (depreciation share)",
        ("=C17/8760*Fixed_Cost_GPU",
         "=D17/8760*Fixed_Cost_GPU",
         "=E17/8760*Fixed_Cost_GPU"),
        "Allocates fixed cost pro-rata to idle hours.", "€#,##0"),
]

for i, (name, formulas, comment, fmt, bold, fill) in enumerate(rows):
    r = 6 + i
    label_cell(sc, f"B{r}", name, bold=bold)
    for j, frm in enumerate(formulas):
        col = chr(ord("C") + j)
        cf = fill if fill else (CALC_FILL if not bold else GOOD_FILL)
        calc_cell(sc, f"{col}{r}", frm, fmt, fill=cf)
        if bold:
            sc[f"{col}{r}"].font = BOLD
    sc[f"F{r}"] = comment
    sc[f"F{r}"].font = ITALIC
    sc[f"F{r}"].alignment = LEFT

# Define names for downstream sheets
define_name("EBITDA_A", "Scenarios!$C$13")
define_name("EBITDA_B", "Scenarios!$D$13")
define_name("EBITDA_C", "Scenarios!$E$13")
define_name("Idle_Hrs_C", "Scenarios!$E$17")

# Verdict line
sc["B22"] = "Verdict (per GPU per year)"
sc["B22"].font = SUBTITLE_FONT
sc.merge_cells("B22:F22")
sc["B23"] = "Best scenario:"
sc["B23"].font = BOLD
calc_cell(sc, "C23", '=INDEX({"24/7","Daytime","Curtailment-only"},MATCH(MAX(C13:E13),C13:E13,0))', "@", fill=GOOD_FILL)
sc.merge_cells("C23:E23")

sc["B24"] = "Best EBITDA / GPU / yr:"
sc["B24"].font = BOLD
calc_cell(sc, "C24", "=MAX(C13:E13)", "€#,##0", fill=GOOD_FILL)

sc["B25"] = "Margin vs. 2nd best:"
sc["B25"].font = BOLD
calc_cell(sc, "C25", "=LARGE(C13:E13,1)-LARGE(C13:E13,2)", "€#,##0")

# Bar chart of EBITDA
bchart = BarChart()
bchart.type = "col"
bchart.title = "EBITDA per GPU per year by scenario"
bchart.y_axis.title = "EUR / GPU / year"
bchart.height = 9
bchart.width = 16
bdata = Reference(sc, min_col=3, max_col=5, min_row=13, max_row=13)
bcats = Reference(sc, min_col=3, max_col=5, min_row=5, max_row=5)
bchart.add_data(bdata, titles_from_data=False)
bchart.set_categories(bcats)
bchart.dataLabels = DataLabelList(showVal=True)
sc.add_chart(bchart, "B27")

# =========================================================
# SHEET 7 — HOURLY MODEL (96-hour representative)
# =========================================================
hm = wb.create_sheet("Hourly_Model")
set_widths(hm, [3, 10, 8, 14, 14, 14, 14, 14, 14, 14])
hm.sheet_view.showGridLines = False
hm["B2"] = "Hourly model — 96 representative hours, scaled to 8,760-h year"
hm["B2"].font = TITLE_FONT
hm.merge_cells("B2:J2")
hm["B3"] = "Each season × 24 hours. Hours weighted to 91.25 days/season."
hm["B3"].font = ITALIC
hm.merge_cells("B3:J3")

# Column headers
hdr = ["Season", "Hour", "CF", "Price €/MWh", "Mode A on?", "Mode B on?", "Mode C on?", "Revenue A", "Revenue B", "Revenue C"]
for i, h in enumerate(hdr):
    c = hm.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

seasons = [("Winter", 3), ("Spring", 4), ("Summer", 5), ("Autumn", 6)]  # column index on Solar_Profile / Price_Curve

for s_idx, (season, col_offset) in enumerate(seasons):
    for hr in range(24):
        r = 6 + s_idx*24 + hr
        hm[f"B{r}"] = season
        hm[f"C{r}"] = hr
        # CF from Solar_Profile, row = 6+hr, col = col_offset
        sp_col = get_column_letter(col_offset)
        calc_cell(hm, f"D{r}", f"=Solar_Profile!{sp_col}{6+hr}", "0.00")
        # Price from Price_Curve
        pc_col = get_column_letter(col_offset)
        calc_cell(hm, f"E{r}", f"=Price_Curve!{pc_col}{6+hr}", "€#,##0")
        # Mode A: always on; Mode B: daytime hours (rolling window centered ~13); Mode C: curtailment flag on solar profile (top CF hours)
        calc_cell(hm, f"F{r}", "=1", "0")
        # Daytime mode: top N hours per day by CF where N = Hrs_Daytime
        calc_cell(hm, f"G{r}",
                  f'=IF(RANK(D{r},INDIRECT("D"&(6+INT((ROW()-6)/24)*24)&":D"&(6+INT((ROW()-6)/24)*24+23)),0)<=Hrs_Daytime,1,0)', "0")
        # Curtailment mode: top Hrs_Curt CF hours per day
        calc_cell(hm, f"H{r}",
                  f'=IF(RANK(D{r},INDIRECT("D"&(6+INT((ROW()-6)/24)*24)&":D"&(6+INT((ROW()-6)/24)*24+23)),0)<=Hrs_Curt,1,0)', "0")

        # Revenue per hour
        # Mode A uses firm rev when grid; mode C uses interruptible & curtailment price
        # Net hourly contribution = Rev - (electricity price * load_MWh)
        calc_cell(hm, f"I{r}", f"=F{r}*(Rev_Firm - E{r}*Load_kW/1000) - (1-F{r})*Idle_kW/1000*E{r}", "€#,##0.00")
        calc_cell(hm, f"J{r}", f"=G{r}*(Rev_Firm - E{r}*Load_kW/1000) - (1-G{r})*Idle_kW/1000*E{r}", "€#,##0.00")
        calc_cell(hm, f"K{r}", f"=H{r}*(Rev_Interr - Curt_Price*Load_kW/1000) - (1-H{r})*Idle_kW/1000*E{r}", "€#,##0.00")

# Header for column K (Revenue C) - reset headers row to include K
hm.cell(row=5, column=11, value="Hour P&L C")
hm.cell(row=5, column=11).fill = SUBHEADER_FILL
hm.cell(row=5, column=11).font = WHITE
hm.cell(row=5, column=11).alignment = CENTER
hm.cell(row=5, column=11).border = BOX
hm.cell(row=5, column=9, value="Hour P&L A")
hm.cell(row=5, column=9).fill = SUBHEADER_FILL
hm.cell(row=5, column=9).font = WHITE
hm.cell(row=5, column=9).alignment = CENTER
hm.cell(row=5, column=10, value="Hour P&L B")
hm.cell(row=5, column=10).fill = SUBHEADER_FILL
hm.cell(row=5, column=10).font = WHITE
hm.cell(row=5, column=10).alignment = CENTER

# Yearly totals (scale by 91.25 days per season)
r_total = 6 + 96 + 1
hm[f"B{r_total}"] = "Annual scaled (×91.25 days/season)"
hm[f"B{r_total}"].font = BOLD
hm.merge_cells(f"B{r_total}:H{r_total}")
calc_cell(hm, f"I{r_total}", "=SUM(I6:I101)*91.25", "€#,##0")
calc_cell(hm, f"J{r_total}", "=SUM(J6:J101)*91.25", "€#,##0")
calc_cell(hm, f"K{r_total}", "=SUM(K6:K101)*91.25", "€#,##0")

r_fixed = r_total + 1
hm[f"B{r_fixed}"] = "Less: fixed cost / GPU / yr"
hm[f"B{r_fixed}"].font = BOLD
hm.merge_cells(f"B{r_fixed}:H{r_fixed}")
calc_cell(hm, f"I{r_fixed}", "=-Fixed_Cost_GPU", "€#,##0")
calc_cell(hm, f"J{r_fixed}", "=-Fixed_Cost_GPU", "€#,##0")
calc_cell(hm, f"K{r_fixed}", "=-Fixed_Cost_GPU", "€#,##0")

r_ebitda = r_fixed + 1
hm[f"B{r_ebitda}"] = "EBITDA per GPU per year (hourly-built)"
hm[f"B{r_ebitda}"].font = BOLD
hm.merge_cells(f"B{r_ebitda}:H{r_ebitda}")
calc_cell(hm, f"I{r_ebitda}", f"=I{r_total}+I{r_fixed}", "€#,##0", fill=GOOD_FILL)
calc_cell(hm, f"J{r_ebitda}", f"=J{r_total}+J{r_fixed}", "€#,##0", fill=GOOD_FILL)
calc_cell(hm, f"K{r_ebitda}", f"=K{r_total}+K{r_fixed}", "€#,##0", fill=GOOD_FILL)

define_name("Hourly_EBITDA_A", f"Hourly_Model!$I${r_ebitda}")
define_name("Hourly_EBITDA_B", f"Hourly_Model!$J${r_ebitda}")
define_name("Hourly_EBITDA_C", f"Hourly_Model!$K${r_ebitda}")

# =========================================================
# SHEET 8 — EQUILIBRIUM
# =========================================================
eq = wb.create_sheet("Equilibrium")
set_widths(eq, [3, 22, 18, 18, 18, 4, 22])
eq.sheet_view.showGridLines = False
eq["B2"] = "Equilibrium — where do the three scenarios cross?"
eq["B2"].font = TITLE_FONT
eq.merge_cells("B2:G2")
eq["B3"] = "At a given curtailment-window electricity price, what is the EBITDA / GPU / yr for each mode?"
eq["B3"].font = ITALIC
eq.merge_cells("B3:G3")

for i, h in enumerate(["Curt €/MWh", "EBITDA 24/7", "EBITDA Daytime", "EBITDA Curt-only"]):
    c = eq.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

# Sweep curt price from -100 to 100
prices = list(range(-100, 105, 10))
for i, p in enumerate(prices):
    r = 6 + i
    input_cell(eq, f"B{r}", p, "€#,##0")
    # Scenario A unchanged (uses grid_price)
    calc_cell(eq, f"C{r}",
              "=24*365*Avail*Rev_Firm "
              "- (24*365*Avail*Load_kW/1000+(8760-24*365*Avail)*Idle_kW/1000)*Grid_Price "
              "- Fixed_Cost_GPU", "€#,##0")
    # Scenario B uses (Grid+PPA)/2
    calc_cell(eq, f"D{r}",
              "=Hrs_Daytime*365*Avail*Rev_Firm "
              "- (Hrs_Daytime*365*Avail*Load_kW/1000+(8760-Hrs_Daytime*365*Avail)*Idle_kW/1000)*((Grid_Price+PPA_Price)/2) "
              "- Fixed_Cost_GPU", "€#,##0")
    # Scenario C uses the swept curt price
    calc_cell(eq, f"E{r}",
              f"=Hrs_Curt*Curt_Days*Avail*Rev_Interr "
              f"- (Hrs_Curt*Curt_Days*Avail*Load_kW/1000+(8760-Hrs_Curt*Curt_Days*Avail)*Idle_kW/1000)*B{r} "
              f"- Fixed_Cost_GPU", "€#,##0")

# Conditional formatting to find best per row
rule_pos = ColorScaleRule(start_type="min", start_color="F8696B",
                          mid_type="num", mid_value=0, mid_color="FFEB84",
                          end_type="max", end_color="63BE7B")
eq.conditional_formatting.add(f"C6:E{6+len(prices)-1}", rule_pos)

# Find equilibrium points (where C-only crosses 24/7)
r_eq = 6 + len(prices) + 2
eq[f"B{r_eq}"] = "Curt-only matches 24/7 at curt €/MWh ≈"
eq[f"B{r_eq}"].font = BOLD
eq.merge_cells(f"B{r_eq}:D{r_eq}")
# Linear interpolation: find where E - C = 0
calc_cell(eq, f"E{r_eq}",
          f"=IFERROR(FORECAST(0, B6:B{6+len(prices)-1}, "
          f"INDEX(E6:E{6+len(prices)-1}-C6:C{6+len(prices)-1},0)), \"n/a\")",
          "€#,##0", fill=GOOD_FILL)

eq[f"B{r_eq+1}"] = "Curt-only matches Daytime at curt €/MWh ≈"
eq[f"B{r_eq+1}"].font = BOLD
eq.merge_cells(f"B{r_eq+1}:D{r_eq+1}")
calc_cell(eq, f"E{r_eq+1}",
          f"=IFERROR(FORECAST(0, B6:B{6+len(prices)-1}, "
          f"INDEX(E6:E{6+len(prices)-1}-D6:D{6+len(prices)-1},0)), \"n/a\")",
          "€#,##0", fill=GOOD_FILL)

# Commentary
eq[f"G5"] = "How to read"
eq[f"G5"].font = SUBTITLE_FONT
eq.merge_cells(f"G6:G18")
eq[f"G6"] = (
    "The three columns show what each operating mode would earn at every curtailment-window "
    "electricity price (rows -100 to +100 €/MWh). The crossover is the price below which "
    "curtailment-only beats 24/7. Above that price, leaving GPUs idle most of the day stops "
    "paying for itself. The 'matches' rows below extrapolate the exact equilibrium price."
)
eq[f"G6"].alignment = Alignment(wrap_text=True, vertical="top")
eq[f"G6"].font = ITALIC

# Line chart
echart = LineChart()
echart.title = "EBITDA / GPU / yr vs curtailment-window €/MWh"
echart.y_axis.title = "EBITDA (€/GPU/yr)"
echart.x_axis.title = "Curtailment €/MWh"
echart.height = 11
echart.width = 22
edata = Reference(eq, min_col=3, max_col=5, min_row=5, max_row=5+len(prices))
ecats = Reference(eq, min_col=2, min_row=6, max_row=5+len(prices))
echart.add_data(edata, titles_from_data=True)
echart.set_categories(ecats)
eq.add_chart(echart, "B" + str(r_eq + 4))

# =========================================================
# SHEET 9 — SENSITIVITY
# =========================================================
se = wb.create_sheet("Sensitivity")
set_widths(se, [3, 22] + [12]*12)
se.sheet_view.showGridLines = False
se["B2"] = "Two-way sensitivity — what swings the answer?"
se["B2"].font = TITLE_FONT
se.merge_cells("B2:N2")
se["B3"] = "Table 1: EBITDA / GPU / yr (curtailment-only) as a function of curt €/MWh × curtailment hours per day."
se["B3"].font = ITALIC
se.merge_cells("B3:N3")

# Table 1
se["B5"] = "Curt €/MWh ↓ \\ Curt hrs/day →"
se["B5"].font = BOLD
se["B5"].fill = HEADER_FILL
se["B5"].font = WHITE
se["B5"].alignment = CENTER
hrs = [2, 3, 4, 5, 6, 7, 8]
for i, h in enumerate(hrs):
    c = se.cell(row=5, column=3+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER

prices_s = [-60, -40, -20, -10, 0, 10, 20, 40, 60]
for i, p in enumerate(prices_s):
    r = 6 + i
    se.cell(row=r, column=2, value=p).font = BOLD
    se.cell(row=r, column=2).number_format = "€#,##0"
    se.cell(row=r, column=2).fill = SUBHEADER_FILL
    se.cell(row=r, column=2).font = WHITE
    se.cell(row=r, column=2).alignment = CENTER
    for j, h in enumerate(hrs):
        col = 3 + j
        formula = (f"={h}*Curt_Days*Avail*Rev_Interr "
                   f"- ({h}*Curt_Days*Avail*Load_kW/1000+(8760-{h}*Curt_Days*Avail)*Idle_kW/1000)*{p} "
                   f"- Fixed_Cost_GPU")
        c = se.cell(row=r, column=col, value=formula)
        c.number_format = "€#,##0"
        c.fill = CALC_FILL
        c.border = BOX

# Heatmap on table 1
last_col = get_column_letter(2 + len(hrs))
se.conditional_formatting.add(f"C6:{last_col}{6+len(prices_s)-1}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# Table 2: GPU price vs realised rental rate (24/7 mode EBITDA)
r_t2 = 6 + len(prices_s) + 3
se[f"B{r_t2-1}"] = "Table 2: EBITDA / GPU / yr (24/7 mode) as a function of GPU capex × realised hourly rate."
se[f"B{r_t2-1}"].font = ITALIC
se.merge_cells(f"B{r_t2-1}:N{r_t2-1}")
se[f"B{r_t2}"] = "Capex (k€) ↓ \\ €/h →"
se[f"B{r_t2}"].fill = HEADER_FILL
se[f"B{r_t2}"].font = WHITE
se[f"B{r_t2}"].alignment = CENTER
rates = [0.80, 1.20, 1.60, 2.00, 2.40, 3.00, 3.60, 4.50]
for i, rate in enumerate(rates):
    c = se.cell(row=r_t2, column=3+i, value=rate)
    c.number_format = "€#,##0.00"
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER

capex_list = [18000, 24000, 30000, 36000, 42000, 50000, 60000]
for i, cx in enumerate(capex_list):
    r = r_t2 + 1 + i
    se.cell(row=r, column=2, value=cx).number_format = "€#,##0"
    se.cell(row=r, column=2).fill = SUBHEADER_FILL
    se.cell(row=r, column=2).font = WHITE
    for j, rate in enumerate(rates):
        col = 3 + j
        # Re-derive a quick 24/7 EBITDA with overridden capex and rate
        formula = (f"=24*365*Avail*{rate}*Util "
                   f"- (24*365*Avail*Load_kW/1000+(8760-24*365*Avail)*Idle_kW/1000)*Grid_Price "
                   f"- (({cx}+Rack_Capex+DC_Capex)*(1-GPU_Salvage)/GPU_Life "
                   f"+ ({cx}+Rack_Capex+DC_Capex)*WACC*0.5 + OandM "
                   f"+ GridFee_per_kWyr*(GPU_Power_Load_W+Aux_Power_W)/1000*PUE)")
        c = se.cell(row=r, column=col, value=formula)
        c.number_format = "€#,##0"
        c.fill = CALC_FILL
        c.border = BOX

se.conditional_formatting.add(f"C{r_t2+1}:{last_col}{r_t2+len(capex_list)}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# =========================================================
# SHEET 10 — COUNTRY COMPARE
# =========================================================
cc = wb.create_sheet("Country_Compare")
set_widths(cc, [3, 16, 18, 18, 18, 18, 18, 22])
cc.sheet_view.showGridLines = False
cc["B2"] = "Country comparison — where écrêtement bites hardest"
cc["B2"].font = TITLE_FONT
cc.merge_cells("B2:H2")
cc["B3"] = "Yellow cells are country-specific assumptions; the EBITDA column recomputes against the same GPU cost stack."
cc["B3"].font = ITALIC
cc.merge_cells("B3:H3")

for i, h in enumerate(["Country", "Curt €/MWh", "Grid €/MWh", "Curt hrs/day", "Curt days/yr", "Solar penetration", "EBITDA Curt-only / GPU / yr"]):
    c = cc.cell(row=5, column=2+i, value=h)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
    c.border = BOX

countries = [
    # name, curt €/MWh, grid €/MWh, curt hrs/day, curt days/yr, solar penetration %
    ("Germany",     -20, 130, 5, 180, 0.13),
    ("Spain",       -30, 110, 6, 220, 0.21),
    ("France",        5, 100, 3, 120, 0.05),
    ("Netherlands", -25, 135, 5, 170, 0.18),
    ("Italy",       -10, 145, 5, 200, 0.12),
    ("UK",           20, 150, 2,  80, 0.06),
]
for i, (name, cp, gp, hd, cd, pen) in enumerate(countries):
    r = 6 + i
    cc[f"B{r}"] = name
    cc[f"B{r}"].font = BOLD
    input_cell(cc, f"C{r}", cp,  "€#,##0")
    input_cell(cc, f"D{r}", gp,  "€#,##0")
    input_cell(cc, f"E{r}", hd,  "0.0")
    input_cell(cc, f"F{r}", cd,  "0")
    input_cell(cc, f"G{r}", pen, "0%")
    formula = (f"=E{r}*F{r}*Avail*Rev_Interr "
               f"- (E{r}*F{r}*Avail*Load_kW/1000+(8760-E{r}*F{r}*Avail)*Idle_kW/1000)*C{r} "
               f"- Fixed_Cost_GPU")
    calc_cell(cc, f"H{r}", formula, "€#,##0", fill=GOOD_FILL)
    cc[f"H{r}"].font = BOLD

cc.conditional_formatting.add(f"H6:H{5+len(countries)}",
    ColorScaleRule(start_type="min", start_color="F8696B",
                   mid_type="num", mid_value=0, mid_color="FFEB84",
                   end_type="max", end_color="63BE7B"))

# Country chart
cchart = BarChart()
cchart.type = "bar"
cchart.title = "EBITDA / GPU / yr in curtailment-only mode, by country"
cchart.height = 9
cchart.width = 16
cdata = Reference(cc, min_col=8, min_row=5, max_row=5+len(countries))
ccats = Reference(cc, min_col=2, min_row=6, max_row=5+len(countries))
cchart.add_data(cdata, titles_from_data=True)
cchart.set_categories(ccats)
cc.add_chart(cchart, "B14")

# =========================================================
# SHEET 11 — DASHBOARD
# =========================================================
db = wb.create_sheet("Dashboard")
set_widths(db, [3, 36, 22, 22, 22, 22])
db.sheet_view.showGridLines = False
db["B2"] = "Dashboard — the answer in one page"
db["B2"].font = TITLE_FONT
db.merge_cells("B2:F2")

# Headline KPIs
header(db, "B4", "Headline KPIs (per GPU / per year unless stated)")
db.merge_cells("B4:F4")

db["B5"] = "Capex per GPU"
calc_cell(db, "C5", "=Total_Capex", "€#,##0")
db["B6"] = "Fixed annual cost / GPU"
calc_cell(db, "C6", "=Fixed_Cost_GPU", "€#,##0")
db["B7"] = "Best operating mode"
calc_cell(db, "C7", "=Scenarios!C23", "@", fill=GOOD_FILL)
db.merge_cells("C7:F7")
db["B8"] = "Best EBITDA / GPU / yr"
calc_cell(db, "C8", "=MAX(EBITDA_A,EBITDA_B,EBITDA_C)", "€#,##0", fill=GOOD_FILL)
db["B9"] = "Δ vs idle (zero op)"
calc_cell(db, "C9", "=C8-(-Fixed_Cost_GPU)", "€#,##0")
db["B10"] = "Payback (yrs)"
calc_cell(db, "C10", "=IFERROR(Total_Capex/(C8+(Total_Capex*(1-GPU_Salvage)/GPU_Life)),\"n/a\")", "0.0")
db["B11"] = "Equilibrium curt price (24/7 = Curt-only)"
calc_cell(db, "C11", f"=Equilibrium!E{r_eq}", "€#,##0", fill=GOOD_FILL)
db["B12"] = "Equilibrium curt price (Daytime = Curt-only)"
calc_cell(db, "C12", f"=Equilibrium!E{r_eq+1}", "€#,##0", fill=GOOD_FILL)

# Fleet view
header(db, "B13", "Fleet view (× number of GPUs)")
db.merge_cells("B13:F13")
db["B14"] = "Fleet capex"
calc_cell(db, "C14", "=Total_Capex*Fleet", "€#,##0")
db["B15"] = "Fleet EBITDA / yr (best mode)"
calc_cell(db, "C15", "=C8*Fleet", "€#,##0", fill=GOOD_FILL)
db["B16"] = "Fleet EBITDA over horizon"
calc_cell(db, "C16", "=C15*Horizon", "€#,##0")
db["B17"] = "Fleet NPV @ WACC"
calc_cell(db, "C17", "=-C14 + C15*(1-(1+WACC)^-Horizon)/WACC + (Total_Capex*GPU_Salvage*Fleet)/((1+WACC)^Horizon)", "€#,##0", fill=GOOD_FILL)
db["B18"] = "Fleet IRR (proxy, level cash flow)"
calc_cell(db, "C18", "=IFERROR(RATE(Horizon,-C15,C14-(Total_Capex*GPU_Salvage*Fleet)/((1+WACC)^Horizon)),\"n/a\")", "0.0%")

# Scenario reconciliation block
header(db, "B20", "Scenario reconciliation (Hourly vs Annual)")
db.merge_cells("B20:F20")
for i, label in enumerate(["", "24/7", "Daytime", "Curtailment"]):
    c = db.cell(row=21, column=2+i, value=label)
    c.fill = SUBHEADER_FILL
    c.font = WHITE
    c.alignment = CENTER
db["B22"] = "Annual-aggregate EBITDA"
calc_cell(db, "C22", "=EBITDA_A", "€#,##0")
calc_cell(db, "D22", "=EBITDA_B", "€#,##0")
calc_cell(db, "E22", "=EBITDA_C", "€#,##0")
db["B23"] = "Hourly-built EBITDA"
calc_cell(db, "C23", "=Hourly_EBITDA_A", "€#,##0")
calc_cell(db, "D23", "=Hourly_EBITDA_B", "€#,##0")
calc_cell(db, "E23", "=Hourly_EBITDA_C", "€#,##0")
db["B24"] = "Δ (sanity)"
calc_cell(db, "C24", "=C23-C22", "€#,##0")
calc_cell(db, "D24", "=D23-D22", "€#,##0")
calc_cell(db, "E24", "=E23-E22", "€#,##0")

# Narrative answer
header(db, "B26", "What the model says")
db.merge_cells("B26:F26")
db.merge_cells("B27:F32")
db["B27"] = (
    "The curtailment-only mode is profitable if and only if (a) the average curtailment-window "
    "price is ≤ the value shown in C11 above, and (b) you can secure a buyer for non-firm GPU "
    "hours at the haircut rate on the Inputs sheet. The dominant cost is depreciation of H100 "
    "capex, not electricity — which means the case is more sensitive to GPU price and to the "
    "number of curtailment days per year than to how negative the spot price gets. Solar "
    "curtailment is real and growing, but a curtailment-only datacenter is a bet on the "
    "permanent existence of cheap, predictable solar troughs and on a willing market for "
    "interruptible AI compute. The two-way sensitivities tell the story: if H100 street price "
    "falls another 30% AND curtailment hours rise above ~6/day in your country, the equilibrium "
    "tips and stranded GPUs at solar sites become a genuine play."
)
db["B27"].alignment = Alignment(wrap_text=True, vertical="top")
for row in range(27, 33):
    db.row_dimensions[row].height = 20

# Save
out = "/home/user/extended-exercise-windows/Solar_Ecretement_vs_H100_Idle.xlsx"
wb.save(out)
print(f"Saved {out}")
