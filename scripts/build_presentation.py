"""Builds the full project presentation: Bengaluru_Thermal_Shift_Presentation.pptx"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = os.path.join(ROOT, "ss")
FIG = os.path.join(ROOT, "eda_outputs", "figures")
OUT = os.path.join(ROOT, "Bengaluru_Thermal_Shift_Presentation.pptx")

# ---------- Theme ----------
BG = RGBColor(0x0F, 0x14, 0x1C)
PANEL = RGBColor(0x1A, 0x21, 0x2D)
PANEL2 = RGBColor(0x23, 0x2C, 0x3B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xC9, 0xD1, 0xDC)
MUTED = RGBColor(0x8A, 0x96, 0xA8)
RED = RGBColor(0xE6, 0x39, 0x46)
ORANGE = RGBColor(0xF4, 0xA2, 0x61)
BLUE = RGBColor(0x4E, 0xA8, 0xDE)
GREEN = RGBColor(0x52, 0xB7, 0x88)
CYAN = RGBColor(0x00, 0xD4, 0xFF)
FONT = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = 13.333, 7.5
slide_no = [0]


# ---------- Helpers ----------
def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.08
    return s


def add_runs(paragraph, text, size, color, bold=False):
    """Supports **bold** inline markup."""
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = paragraph.add_run()
        r.text = part
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.color.rgb = WHITE if (i % 2 == 1) else color
        r.font.bold = bold or (i % 2 == 1)


def text(slide, x, y, w, h, content, size=16, color=LIGHT, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.1):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = anchor
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        if isinstance(line, tuple):
            t, s, c, b = (list(line) + [None, None, None])[:4]
            add_runs(p, t, s or size, c or color, b if b is not None else bold)
        else:
            add_runs(p, line, size, color, bold)
    return tb


def bullets(slide, x, y, w, h, items, size=15, color=LIGHT, gap=6, marker_color=ORANGE):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        level = 0
        if isinstance(item, tuple):
            item, level = item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.08
        r = p.add_run()
        r.text = ("      – " if level else "▸  ")
        r.font.name = FONT
        r.font.size = Pt(size - (2 if level else 0))
        r.font.color.rgb = MUTED if level else marker_color
        r.font.bold = True
        add_runs(p, item, size - (2 if level else 0), color)
    return tb


def image_fit(slide, path, x, y, w, h, border=True):
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
    if border:
        rect(slide, dx - 0.04, dy - 0.04, dw + 0.08, dh + 0.08, PANEL2)
    slide.shapes.add_picture(path, Inches(dx), Inches(dy), Inches(dw), Inches(dh))
    return dx, dy, dw, dh


def new_slide(title=None, kicker=None):
    s = prs.slides.add_slide(BLANK)
    slide_no[0] += 1
    rect(s, 0, 0, SW, SH, BG)
    if title:
        rect(s, 0.5, 0.42, 0.09, 0.62, RED)
        if kicker:
            text(s, 0.72, 0.28, 11, 0.35, kicker.upper(), size=11, color=ORANGE, bold=True)
            text(s, 0.72, 0.55, 12, 0.7, title, size=28, color=WHITE, bold=True)
        else:
            text(s, 0.72, 0.4, 12, 0.7, title, size=28, color=WHITE, bold=True)
    # footer
    rect(s, 0, SH - 0.38, SW, 0.38, PANEL)
    text(s, 0.5, SH - 0.35, 9, 0.3, "Bengaluru Thermal Shift  •  Urban Heat Island Visualization (2001–2025)",
         size=10, color=MUTED)
    text(s, SW - 1.5, SH - 0.35, 1.0, 0.3, str(slide_no[0]), size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def section(number, title, subtitle):
    s = prs.slides.add_slide(BLANK)
    slide_no[0] += 1
    rect(s, 0, 0, SW, SH, BG)
    rect(s, 0, 0, 0.35, SH, RED)
    text(s, 1.2, 2.2, 3, 1.2, f"{number:02d}", size=80, color=RED, bold=True)
    text(s, 1.2, 3.55, 11, 0.9, title, size=40, color=WHITE, bold=True)
    text(s, 1.2, 4.45, 11, 0.8, subtitle, size=18, color=MUTED)
    return s


def card(slide, x, y, w, h, big, label, sub=None, color=RED, big_size=34):
    rect(slide, x, y, w, h, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y + 0.15, 0.07, h - 0.3, color)
    text(slide, x + 0.25, y + 0.12, w - 0.35, 0.75, big, size=big_size, color=color, bold=True)
    text(slide, x + 0.25, y + 0.12 + big_size / 72 + 0.18, w - 0.35, 0.4, label.upper(), size=11, color=WHITE, bold=True)
    if sub:
        text(slide, x + 0.25, y + 0.12 + big_size / 72 + 0.5, w - 0.35, h - 1.1, sub, size=11, color=MUTED)


def table(slide, x, y, w, rows, col_widths, row_h=0.42, header_fill=PANEL2, size=12, first_col_color=None):
    nrows, ncols = len(rows), len(rows[0])
    shp = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
    tbl = shp.table
    for j, cw in enumerate(col_widths):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if i == 0 else (PANEL if i % 2 else BG)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            color = WHITE if i == 0 else LIGHT
            if isinstance(val, tuple):
                val, color = val
            elif i > 0 and j == 0 and first_col_color:
                color = first_col_color
            add_runs(p, str(val), size, color, bold=(i == 0))
    return tbl


def insight_panel(slide, x, y, w, h, heading, items, size=14):
    rect(slide, x, y, w, h, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    text(slide, x + 0.25, y + 0.18, w - 0.5, 0.4, heading.upper(), size=12, color=ORANGE, bold=True)
    bullets(slide, x + 0.2, y + 0.6, w - 0.4, h - 0.8, items, size=size)


def figure_slide(kicker, title, img, heading, items, img_w=8.4, size=14):
    s = new_slide(title, kicker)
    top, bottom = 1.45, SH - 0.6
    image_fit(s, img, 0.5, top, img_w, bottom - top)
    insight_panel(s, 0.5 + img_w + 0.3, top, SW - (0.5 + img_w + 0.3) - 0.5, bottom - top, heading, items, size)
    return s


# =====================================================================
# 1. TITLE
# =====================================================================
s = prs.slides.add_slide(BLANK)
slide_no[0] += 1
rect(s, 0, 0, SW, SH, BG)
# Crop the 30m hotspot map (no Tableau chrome) to the right-panel aspect ratio
src = Image.open(os.path.join(SS, "w3d1.png")).convert("RGB")
map_top, map_bot = 44, 820
mh = map_bot - map_top
mw = int(mh * (SW - 6.6) / SH)
cx = 690
hero = src.crop((cx - mw // 2, map_top, cx + mw // 2, map_bot))
hero_path = os.path.join(ROOT, "eda_outputs", "_title_hero.png")
hero.save(hero_path)
s.shapes.add_picture(hero_path, Inches(6.6), Inches(0), Inches(SW - 6.6), Inches(SH))
rect(s, 6.6, 0, 0.12, SH, RED)
text(s, 0.7, 1.15, 6, 0.4, "DATA VISUALIZATION PROJECT  •  5TH SEMESTER", size=12, color=ORANGE, bold=True)
text(s, 0.7, 1.65, 5.9, 2.2, ["The \u201cGarden City\u201d to", "\u201cSilicon Valley\u201d", "Thermal Shift"],
     size=40, color=WHITE, bold=True, spacing=0.95)
text(s, 0.7, 3.95, 5.7, 1.0, "Visualizing Bengaluru\u2019s Urban Heat Island from city scale down to individual buildings (2001\u20132025)",
     size=17, color=LIGHT)
rect(s, 0.7, 5.15, 1.2, 0.05, RED)
text(s, 0.7, 5.35, 5.8, 0.4, "Presented by: Arjun Sanesh & <Teammate Name>", size=14, color=WHITE, bold=True)
text(s, 0.7, 5.75, 5.8, 0.7, ["NASA MODIS  •  USGS Landsat 30m  •  BBMP Wards  •  OpenStreetMap",
                               "Python EDA  •  Tableau Dashboards & Story"], size=12, color=MUTED)

# =====================================================================
# 2. PROBLEM STATEMENT
# =====================================================================
s = new_slide("Problem Statement", "Why this project")
text(s, 0.72, 1.45, 7.4, 2.4, [
    "Bengaluru\u2019s rapid transformation into a global tech hub has replaced lakes, tree canopy and open land "
    "with concrete, glass and asphalt, creating a pronounced **Urban Heat Island (UHI)**.",
    "",
    "City-wide weather reports hide these hyper-local extremes. We need a visualization that exposes **where** "
    "urban sprawl replaced green cover, **how much hotter** those exact places became, and why the city is "
    "**losing its ability to cool down at night**.",
], size=16, color=LIGHT, spacing=1.15)
card(s, 8.5, 1.45, 2.05, 1.6, "+1055%", "Built-up area", "5 decades of sprawl", RED, 26)
card(s, 10.75, 1.45, 2.05, 1.6, "\u221288%", "Vegetation", "cover lost", GREEN, 26)
card(s, 8.5, 3.25, 2.05, 1.6, "\u221279%", "Water bodies", "lost / shrunk", BLUE, 26)
card(s, 10.75, 3.25, 2.05, 1.6, "+7.9\u00b0C", "Surface temp", "1992\u20132017 surge", ORANGE, 26)
text(s, 8.5, 4.95, 4.3, 0.4, "Context figures from published IISc land-use research", size=10, color=MUTED)
rect(s, 0.72, 4.35, 7.4, 2.25, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, 0.95, 4.5, 7.0, 0.4, "TARGET AUDIENCE", size=12, color=ORANGE, bold=True)
bullets(s, 0.9, 4.9, 7.1, 1.7, [
    "**Urban planners (BBMP / BDA):** identify heat-vulnerable zones for green-cover policy",
    "**Environmental researchers:** quantify the land-cover \u2192 temperature relationship",
    "**Residents:** understand why their neighbourhood feels hotter, especially at night",
], size=14)

# =====================================================================
# 3. OBJECTIVES & RESEARCH QUESTIONS
# =====================================================================
s = new_slide("Objectives & Research Questions", "What we set out to answer")
qs = [
    ("Q1", "Is Bengaluru failing to cool down at night?", "25-year MODIS Day vs Night LST trend & diurnal cooling drop", RED),
    ("Q2", "Where did concrete replace green cover?", "240m block-level land-transition classification (2002 \u2192 2025)", ORANGE),
    ("Q3", "How much hotter do newly built-up areas get?", "Normalized UHI anomaly jump per transition class", BLUE),
    ("Q4", "Can we see heat at the building scale?", "Unaggregated 30m Landsat pixels over 5 iconic zones", GREEN),
    ("Q5", "Do trees & lakes measurably cool the city?", "Correlation of NDVI / NDBI / waterbodies with LST", CYAN),
]
for i, (q, title, how, c) in enumerate(qs):
    y = 1.5 + i * 1.0
    rect(s, 0.72, y, 11.9, 0.85, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, 0.72, y, 1.0, 0.85, c, MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, 0.72, y, 1.0, 0.85, q, size=22, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.95, y + 0.06, 6.0, 0.75, title, size=17, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 7.9, y + 0.06, 4.6, 0.75, how, size=13, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# 4. DATA SOURCES
# =====================================================================
s = new_slide("Datasets", "Six open datasets, three spatial scales")
rows = [
    ["Dataset", "Source", "Resolution / Scale", "Rows", "Key Fields"],
    ["Bengaluru_UHI_Master_2001_2025.csv", "NASA MODIS/Terra MOD11A2 + MOD13Q1", "1 km LST, 250 m NDVI \u2192 243 wards \u00d7 25 yrs", "6,075", "Day/Night LST, Cooling Drop, NDVI, EVI, NDBI, UHI anomaly"],
    ["Bengaluru_BlockGrid_240m_2002_2025.csv", "USGS Landsat 7/8 Collection 2 L2", "30 m \u2192 240 m blocks (Apr 2002/15/25)", "21,374", "LST, NDVI, NDBI, \u0394UHI, Land_Transition"],
    ["Bengaluru_Hotspots_30m_2002_2025.csv", "USGS Landsat 7/8 Collection 2 L2", "Pure 30 m pixels, 5 zones (2\u00d72 km)", "21,861", "Zone, LST, NDVI, NDBI, \u0394UHI"],
    ["landsat_30m/*.tif", "USGS Landsat 7/8 Collection 2 L2", "30 m GeoTIFF (1.37 M px each)", "4 rasters", "LST_C, NDVI, NDBI (+ change raster)"],
    ["BBMP_Wards.geojson", "DataMeet Municipal_Spatial_Data", "243 ward polygons (704 km\u00b2)", "243", "KGISWardNo, KGISWardName"],
    ["Bengaluru_Lakes.geojson", "OpenStreetMap (Overpass API)", "1,981 waterbodies (5,138 ha)", "1,981", "name, water_type, geometry"],
]
table(s, 0.6, 1.5, 12.13, rows, [3.35, 2.6, 2.75, 0.85, 2.58], row_h=0.62, size=11, first_col_color=CYAN)
text(s, 0.6, 6.05, 12, 0.5, "All satellite data accessed programmatically via the Microsoft Planetary Computer STAC API "
     "(no manual downloads) \u2014 scripts in /scripts make the pipeline fully reproducible.", size=12, color=MUTED)

# =====================================================================
# 5. METHODOLOGY PIPELINE
# =====================================================================
s = new_slide("Methodology Pipeline", "From raw satellite pixels to interactive story")
steps = [
    ("1  ACQUIRE", RED, ["MODIS MOD11A2 / MOD13Q1 (2001\u201325, Mar\u2013May)", "Landsat 7/8 C2-L2 (Apr 2002, 2015, 2025, <4% cloud)", "BBMP wards + OSM lakes"]),
    ("2  PROCESS", ORANGE, ["Cloud & shadow masking (QA bits)", "Scale DN \u2192 \u00b0C and reflectance", "Reproject all years to one aligned 30m grid"]),
    ("3  DERIVE", BLUE, ["NDVI (vegetation), NDBI (built-up)", "Normalized UHI anomaly", "Land-transition classes"]),
    ("4  AGGREGATE", GREEN, ["Ward zonal means (243)", "240m blocks (21,374)", "Raw 30m pixels (21,861)"]),
    ("5  ANALYZE & VISUALIZE", CYAN, ["Python EDA: trends, correlations, distributions", "Tableau: 2 dashboards", "Tableau Story (5 points)"]),
]
bw, gap = 2.3, 0.15
for i, (head, c, items) in enumerate(steps):
    x = 0.6 + i * (bw + gap)
    rect(s, x, 1.6, bw, 0.6, c, MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, x, 1.6, bw, 0.6, head, size=13, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, x, 2.3, bw, 2.55, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    bullets(s, x + 0.08, 2.42, bw - 0.16, 2.4, items, size=12, gap=8, marker_color=c)
    if i < len(steps) - 1:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw - 0.02), Inches(1.75), Inches(0.19), Inches(0.3))
        a.fill.solid(); a.fill.fore_color.rgb = MUTED; a.line.fill.background()
rect(s, 0.6, 5.05, 12.13, 1.6, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, 0.85, 5.15, 11.7, 0.4, "KEY FORMULAS", size=12, color=ORANGE, bold=True)
text(s, 0.85, 5.5, 5.9, 1.1, [
    "**MODIS LST (\u00b0C)** = DN \u00d7 0.02 \u2212 273.15",
    "**Landsat LST (\u00b0C)** = DN \u00d7 0.00341802 + 149 \u2212 273.15",
    "**Cooling Drop** = Day LST \u2212 Night LST",
], size=13, color=LIGHT)
text(s, 6.9, 5.5, 5.7, 1.1, [
    "**NDVI** = (NIR \u2212 Red) / (NIR + Red)",
    "**NDBI** = (SWIR \u2212 NIR) / (SWIR + NIR)",
    "**UHI anomaly** = pixel LST \u2212 city-mean LST (same date)",
], size=13, color=LIGHT)

# =====================================================================
# 6. NORMALIZATION & CLASSIFICATION
# =====================================================================
s = new_slide("Going Beyond Ward Averages", "Data preparation decisions")
rect(s, 0.6, 1.5, 5.9, 5.1, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
text(s, 0.85, 1.65, 5.5, 0.4, "WHY NORMALIZE? (UHI ANOMALY)", size=12, color=ORANGE, bold=True)
bullets(s, 0.8, 2.05, 5.55, 4.5, [
    "Each Landsat scene is a **single April day** \u2014 regional weather differs between 2002, 2015 and 2025 "
    "(city mean 42.7\u00b0C vs 38.4\u00b0C vs 39.3\u00b0C).",
    "Raw \u0394LST would mix **weather noise** with **urbanization signal**.",
    "We measure each block **relative to the city average of that same day**, so \u0394UHI isolates how much "
    "hotter a place became **compared to the rest of Bengaluru**.",
    "Ward aggregation (1 km MODIS) hides building-scale change \u2192 we added **240m blocks** and **raw 30m pixels**.",
], size=14)
text(s, 6.8, 1.5, 6, 0.4, "LAND-TRANSITION CLASSIFICATION RULES (240m BLOCKS)", size=12, color=ORANGE, bold=True)
rows = [
    ["Class", "Rule (2002 \u2192 2025)", "Blocks"],
    [("Newly Built-Up (Green \u2192 Concrete)", RED), "NDVI\u2082\u2080\u2080\u2082 \u2265 0.25, NDVI\u2082\u2080\u2082\u2085 < 0.20, \u0394NDBI > 0.03", "59"],
    [("Urban Densification", ORANGE), "\u0394NDBI > 0.04 and \u0394NDVI < \u22120.05", "1,311"],
    [("Persistent Green / Park", GREEN), "NDVI\u2082\u2080\u2082\u2085 \u2265 0.30", "13,736"],
    [("Greening / Recovery", BLUE), "\u0394NDVI > 0.08", "720"],
    [("Persistent Urban / Bare", MUTED), "All remaining blocks", "5,546"],
    [("Waterbody", CYAN), "NDVI < 0 and NDBI < 0", "2"],
]
table(s, 6.8, 1.95, 5.93, rows, [2.45, 2.68, 0.8], row_h=0.58, size=11)
text(s, 6.8, 6.1, 5.9, 0.5, "Rules applied in order (first match wins) in scripts/download_landsat_30m.py", size=11, color=MUTED)

# =====================================================================
# SECTION: EDA
# =====================================================================
section(1, "Exploratory Data Analysis", "Python (pandas, scipy, matplotlib, seaborn)  \u2022  scripts/perform_eda.py  \u2022  7 figures")

# EDA overview KPIs
s = new_slide("EDA at a Glance", "Data quality & headline statistics")
card(s, 0.6, 1.5, 2.9, 1.75, "0", "Missing values", "6,075 ward-years \u2022 all 12 columns complete", GREEN)
card(s, 3.7, 1.5, 2.9, 1.75, "49,310", "Spatial records", "6,075 ward-yrs + 21,374 blocks + 21,861 pixels", BLUE)
card(s, 6.8, 1.5, 2.9, 1.75, "25 yrs", "Time span", "2001\u20132025 summer (Mar\u2013May) composites", ORANGE)
card(s, 9.9, 1.5, 2.83, 1.75, "704 km\u00b2", "Study area", "243 BBMP wards \u2022 1,981 waterbodies", CYAN)
rows = [
    ["Metric (ward-year)", "Mean", "Std", "Min", "Max"],
    ["Day LST (\u00b0C)", "35.61", "1.52", "30.41", "40.24"],
    ["Night LST (\u00b0C)", "24.42", "1.26", "19.51", "28.13"],
    ["Cooling Drop (\u00b0C)", "11.19", "1.86", "5.49", "17.55"],
    ["Mean NDVI", "0.304", "0.056", "0.163", "0.545"],
    ["Mean NDBI", "\u22120.124", "0.057", "\u22120.408", "0.045"],
]
table(s, 0.6, 3.5, 6.6, rows, [2.6, 1.0, 1.0, 1.0, 1.0], row_h=0.5, size=12, first_col_color=WHITE)
insight_panel(s, 7.5, 3.5, 5.23, 3.0, "Decadal shift (5-yr means)", [
    "Night LST: **23.72 \u2192 24.97\u00b0C** (+1.25\u00b0C)",
    "Cooling drop: **12.90 \u2192 9.07\u00b0C** (\u221229.7%)",
    "Day LST: 36.62 \u2192 34.04\u00b0C (\u22122.58\u00b0C)",
    "Nights warm while days cool \u2192 heat is being **trapped**, not just added",
], size=14)

figure_slide("EDA 1  \u2022  Temporal trends", "The Nocturnal Heat Trap (2001\u20132025)",
             os.path.join(FIG, "fig1_temporal_trends_2001_2025.png"), "Key insights", [
                 "Night LST rises **+0.81\u00b0C / decade** (p = 0.00016, R\u00b2 = 0.47)",
                 "Day\u2013night cooling drop collapses **\u22121.86\u00b0C / decade** (p = 1.4\u00d710\u207b\u2078, R\u00b2 = 0.76) \u2014 the strongest trend in the data",
                 "2025 recorded the **lowest cooling drop (6.6\u00b0C)** in 25 years",
                 "Daytime LST trends down (\u22121.05\u00b0C/dec), so the real story is **lost night-time cooling**",
                 "City-wide NDVI/NDBI look flat \u2014 averages hide local change, motivating finer scales",
             ], img_w=6.3, size=14)

figure_slide("EDA 2  \u2022  Correlation analysis", "What Drives Surface Heat?",
             os.path.join(FIG, "fig2_correlation_matrix.png"), "Key insights", [
                 "Built-up index \u2194 Day LST: **r = +0.64**",
                 "Built-up \u2194 Day UHI anomaly: **r = +0.60**",
                 "Vegetation (EVI) \u2194 Night LST: **r = \u22120.58**",
                 "NDVI \u2194 Night UHI anomaly: **r = \u22120.56**",
                 "NDVI \u2194 NDBI: r = \u22120.84 \u2014 green and concrete are direct trade-offs",
                 "Concrete heats the day; **loss of greenery traps heat at night**",
             ], img_w=6.6, size=14)

figure_slide("EDA 3  \u2022  Regression", "Vegetation Cools, Concrete Heats",
             os.path.join(FIG, "fig3_vegetation_builtup_vs_lst.png"), "Key insights", [
                 "Each +0.1 NDVI \u2192 **\u22121.05\u00b0C** daytime surface temp (slope \u221210.5\u00b0C/unit)",
                 "Each +0.1 NDBI \u2192 **+1.7\u00b0C** daytime surface temp (slope +17.15\u00b0C/unit)",
                 "Built-up density is a **stronger predictor** of heat than vegetation alone",
                 "6,075 ward-year observations",
             ], img_w=8.6, size=14)

figure_slide("EDA 4  \u2022  240m land transitions", "Distribution of Change by Land Transition",
             os.path.join(FIG, "fig4_land_transition_distributions_240m.png"), "Key insights", [
                 "Only **Newly Built-Up** and **Urban Densification** blocks show positive median \u0394LST",
                 "Their \u0394NDVI is strongly negative and \u0394NDBI strongly positive \u2014 the signature of construction",
                 "Persistent green & greening blocks cool, even though the 2025 scene was cooler overall",
                 "Waterbodies stay the coolest surfaces in the city",
             ], img_w=8.6, size=14)

figure_slide("EDA 5  \u2022  30m case-study zones", "Building-Scale Hotspot Comparison",
             os.path.join(FIG, "fig5_hotspots_30m_comparison.png"), "Key insights", [
                 "Raw April LST differs by scene weather, so zones are compared on the **normalized UHI**",
                 "**Bellandur / ORR** shows the largest relative jump: **+3.2\u00b0C \u0394UHI** with NDVI \u22120.11 and NDBI +0.05",
                 "Its violin has the **widest upper tail**: some pixels warmed by up to ~9\u00b0C even in raw LST",
                 "Electronic City & Whitefield cooled relative to the city as campuses matured and got more greenery",
             ], img_w=8.6, size=14)

figure_slide("EDA 6  \u2022  Ward rankings", "Hottest, Coolest & Fastest-Changing Wards",
             os.path.join(FIG, "fig6_ward_rankings_extremes.png"), "Key insights", [
                 "Hottest wards (day): **Rajeshwari Nagar, Hegganahalli, Peenya**, in the industrial west",
                 "Coolest wards: **Bellanduru, Agaram, Hagadur**, all lake- or green-dominated",
                 "Biggest night-time warming: **Marathahalli +1.88\u00b0C**, Munnekollala +1.57\u00b0C, Bellanduru +1.29\u00b0C",
                 "Same wards lead built-up gain (\u0394NDBI \u2248 +0.10): the **eastern IT corridor**",
             ], img_w=8.6, size=13)

figure_slide("EDA 7  \u2022  Spatial patterns", "Where the City Changed (240m)",
             os.path.join(FIG, "fig7_spatial_patterns_240m.png"), "Key insights", [
                 "Hot \u0394LST streaks trace the **Outer Ring Road arc** (Bellandur \u2192 Marathahalli \u2192 Whitefield)",
                 "Additional hotspots: **Yelahanka/NW belt**, the western industrial edge and Hebbal\u2013Manyata",
                 "Orange Urban-Densification clusters on the right map **line up with the heat streaks**",
                 "Strong evidence that heat is **spatially tied to construction**",
             ], img_w=8.6, size=14)

# EDA correlations at block level
s = new_slide("EDA Summary: The Construction \u2192 Heat Link", "240m block-level results (2002 \u2192 2025)")
rows = [
    ["Land Transition", "Blocks", "UHI 2002", "UHI 2025", "\u0394UHI", "\u0394NDVI", "\u0394NDBI"],
    [("Newly Built-Up (Green \u2192 Concrete)", RED), "59", "\u22124.30", "+2.06", ("+6.36\u00b0C", RED), "\u22120.23", "+0.15"],
    [("Urban Densification", ORANGE), "1,311", "\u22124.96", "+0.20", ("+5.16\u00b0C", ORANGE), "\u22120.17", "+0.15"],
    [("Persistent Urban / Bare", MUTED), "5,546", "+0.63", "+0.89", "+0.26\u00b0C", "+0.01", "\u22120.05"],
    [("Greening / Recovery", BLUE), "720", "+1.27", "+0.91", ("\u22120.36\u00b0C", BLUE), "+0.11", "\u22120.08"],
    [("Persistent Green / Park", GREEN), "13,736", "+0.15", "\u22120.44", ("\u22120.59\u00b0C", GREEN), "+0.10", "\u22120.09"],
    [("Waterbody", CYAN), "2", "\u22129.41", "\u22129.13", "+0.28\u00b0C", "\u2014", "\u2014"],
]
table(s, 0.6, 1.5, 12.13, rows, [3.9, 1.15, 1.35, 1.35, 1.6, 1.39, 1.39], row_h=0.55, size=13)
card(s, 0.6, 5.5, 3.9, 1.15, "r = +0.60", "\u0394NDBI vs \u0394UHI", None, RED, 24)
card(s, 4.72, 5.5, 3.9, 1.15, "r = \u22120.42", "\u0394NDVI vs \u0394UHI", None, GREEN, 24)
card(s, 8.83, 5.5, 3.9, 1.15, "~9\u00b0C cooler", "Lakes vs city average", None, CYAN, 24)

# =====================================================================
# SECTION: DASHBOARD 1
# =====================================================================
section(2, "Dashboard 1: Concrete vs Canopy", "240m block-level heat jump  \u2022  30m building-scale hotspots  \u2022  Landsat 2002 \u2192 2025")

s = new_slide("Dashboard 1: Concrete vs Canopy", "Tableau dashboard overview")
image_fit(s, os.path.join(SS, "w5d1.png"), 0.5, 1.45, 8.9, SH - 2.05)
insight_panel(s, 9.65, 1.45, 3.18, SH - 2.05, "How it works", [
    "**Left:** 240m heat map of all 21,374 blocks + lakes",
    "**Top-right:** heat jump by land transition (doubles as a **filter action**)",
    "**Bottom-right:** 30m building-scale zoom with a **Zone** selector",
    "Clicking a bar instantly highlights those blocks on the map",
], size=13)

figure_slide("Dashboard 1  \u2022  Sheet 1", "240m Heat Map: Where Concrete Replaced Green",
             os.path.join(SS, "w1d1.png"), "Design choices", [
                 "**Square marks** tile 21,374 blocks seamlessly via MAKEPOINT(Lat, Lon)",
                 "**Diverging palette** (\u22126 \u2192 +8\u00b0C) centred on 0: red = hotter than city, green = cooler",
                 "**Cyan OSM lakes** layered on top to show natural cooling zones",
                 "**Satellite basemap** so viewers recognise real places",
                 "**Land Transition filter** isolates construction hotspots",
             ], img_w=8.6, size=13)

figure_slide("Dashboard 1  \u2022  Sheet 2", "Heat Jump by Land Transition",
             os.path.join(SS, "w2d1.png"), "Takeaway", [
                 "Green \u2192 Concrete: **+6.4\u00b0C**",
                 "Urban Densification: **+5.2\u00b0C**",
                 "Persistent Green / Park: **\u22120.6\u00b0C**",
                 "Sorted bar chart + diverging colour = the **single most persuasive chart** in the project",
                 "Used as a dashboard filter for drill-down",
             ], img_w=8.6, size=14)

figure_slide("Dashboard 1  \u2022  Sheet 3", "30m Hotspot Zoom: Bellandur / ORR Ecospace",
             os.path.join(SS, "w3d1.png"), "What we see", [
                 "Every square is a **raw 30m \u00d7 30m Landsat pixel**, with no aggregation",
                 "Large tech-park rooftops and dense housing **glow red**",
                 "Bellandur Lake (bottom) and tree pockets stay **deep blue**",
                 "Zone dropdown flies between 5 zones: Bellandur, Whitefield, Manyata, Electronic City and Cubbon Park",
             ], img_w=8.6, size=13)

figure_slide("Dashboard 1  \u2022  Sheet 4", "Tree Loss vs Heat Scatter (30m Pixels)",
             os.path.join(SS, "w4d1.png"), "Takeaway", [
                 "21,861 pixels, x = \u0394NDVI, y = \u0394UHI, colour = \u0394NDBI",
                 "Clear **negative linear trend**: tree loss \u2192 warming",
                 "Orange (concrete gain) clusters **top-left**, blue (concrete loss) **bottom-right**",
                 "Direct pixel-level evidence for the **green-cover cooling effect**",
             ], img_w=8.6, size=14)

# =====================================================================
# SECTION: DASHBOARD 2
# =====================================================================
section(3, "Dashboard 2: The Nocturnal Heat Trap", "NASA MODIS 2001\u20132025  \u2022  243 BBMP wards  \u2022  Animated time-lapse")

s = new_slide("Dashboard 2: The Nocturnal Heat Trap", "Tableau dashboard overview")
image_fit(s, os.path.join(SS, "w8d2.png"), 0.5, 1.45, 8.9, SH - 2.05)
insight_panel(s, 9.65, 1.45, 3.18, SH - 2.05, "How it works", [
    "**KPI banner** with the 3 headline numbers",
    "**Left:** animated ward map with a Year **Pages \u25b6 Play** control",
    "**Top-right:** 25-year dual-axis trend",
    "**Bottom-right:** hottest-ward ranking coloured by NDVI",
    "Clicking a ward filters the trend to that ward",
], size=13)

figure_slide("Dashboard 2  \u2022  Sheet 5", "25-Year Nighttime Heat Trap (Dual Axis)",
             os.path.join(SS, "w1d2.png"), "Takeaway", [
                 "**Red:** average night LST, trending up",
                 "**Blue:** day\u2013night cooling drop, trending steeply down",
                 "Linear trend lines make the **diverging trajectories** obvious",
                 "2025 hits a **25-year low cooling drop of 6.6\u00b0C**",
                 "Separate axes keep both metrics readable on one chart",
             ], img_w=8.6, size=14)

figure_slide("Dashboard 2  \u2022  Sheet 6", "Animated Ward Night UHI Map",
             os.path.join(SS, "w2d2.png"), "Takeaway", [
                 "243 BBMP ward polygons coloured by **night UHI anomaly**",
                 "**Year on the Pages shelf** animates 2001 \u2192 2025",
                 "Dense **old core (west-central)** retains the most heat at night",
                 "Lake-rich eastern fringe stays coolest, but is **warming fastest**",
                 "Dark basemap makes the thermal palette pop",
             ], img_w=8.6, size=13)

figure_slide("Dashboard 2  \u2022  Sheet 7", "Warming Wards Ranking (2021\u20132025)",
             os.path.join(SS, "w3d2.png"), "Takeaway", [
                 "Top 15 wards by average night LST, e.g. **Hampi Nagar 26.23\u00b0C**",
                 "Colour = mean NDVI: **red = least green**",
                 "Most of the hottest wards are also the **least vegetated**",
                 "Year-range slider lets viewers compare any period",
             ], img_w=8.6, size=14)

s = new_slide("Dashboard 2: KPI Headline Cards", "Executive summary metrics")
card(s, 0.6, 1.7, 3.9, 2.3, "\u25b2 +1.25\u00b0C", "Nighttime LST rise", "2001\u201305 (23.7\u00b0C) \u2192 2021\u201325 (25.0\u00b0C)", RED, 40)
card(s, 4.72, 1.7, 3.9, 2.3, "\u25bc \u221229.7%", "Overnight cooling collapse", "Diurnal drop fell from 12.9\u00b0C \u2192 9.1\u00b0C", ORANGE, 40)
card(s, 8.83, 1.7, 3.9, 2.3, "\u25b2 +6.36\u00b0C", "New construction UHI jump", "240m blocks: green replaced by concrete", RED, 40)
text(s, 0.6, 4.4, 12.1, 2.0, [
    "Built as three calculated-field text sheets (KPI 1, KPI 2, KPI 3) and placed as a banner on top of Dashboard 2.",
    "",
    "Each number is backed by the EDA: Night LST trend p = 0.00016  \u2022  Cooling-drop trend p = 1.4\u00d710\u207b\u2078  \u2022  21,374 classified blocks.",
], size=15, color=LIGHT)

# =====================================================================
# SECTION: STORY
# =====================================================================
section(4, "The Tableau Story", "Five story points that walk from city scale down to individual buildings")

s = new_slide("Story Flow: Macro \u2192 Micro", "Tableau Story points")
story = [
    ("1", "The Hook", "25-Year Nighttime Heat Trap", "Bengaluru stopped cooling down at night (\u221229.7% since 2001)", RED),
    ("2", "City-Wide Spread", "Animated Ward Night UHI Map", "Night heat surged fastest in the IT corridor (Marathahalli +1.88\u00b0C)", ORANGE),
    ("3", "Beyond Wards (240m)", "Dashboard 1: Concrete vs Canopy", "Blocks where concrete replaced trees jumped +6.36\u00b0C", BLUE),
    ("4", "Down to Buildings (30m)", "30m Hotspot Zoom (Bellandur)", "Tech-park rooftops glow red beside cool lakes", GREEN),
    ("5", "The Solution", "Dashboard 2 / Scatter", "Trees cool nights (r = \u22120.57); lakes ~9\u00b0C cooler", CYAN),
]
for i, (n, head, sheet, cap, c) in enumerate(story):
    x = 0.6 + i * 2.47
    rect(s, x, 1.6, 2.3, 4.7, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    circ = rect(s, x + 0.75, 1.85, 0.8, 0.8, c, MSO_SHAPE.OVAL)
    text(s, x + 0.75, 1.85, 0.8, 0.8, n, size=26, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.12, 2.85, 2.06, 0.7, head, size=16, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    rect(s, x + 0.85, 3.6, 0.6, 0.04, c)
    text(s, x + 0.12, 3.75, 2.06, 0.8, sheet, size=12, color=c, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 0.12, 4.55, 2.06, 1.7, f"\u201c{cap}\u201d", size=12, color=LIGHT, align=PP_ALIGN.CENTER)
text(s, 0.6, 6.45, 12.1, 0.4, "Each story point stays fully interactive: tooltips, filters and the year animation all work during the presentation.",
     size=12, color=MUTED, align=PP_ALIGN.CENTER)

# =====================================================================
# KEY FINDINGS
# =====================================================================
s = new_slide("Key Findings", "Answering our research questions")
finds = [
    ("Q1", "Yes. Bengaluru is losing its night-time cooling: the cooling drop is falling 1.86\u00b0C per decade and night LST is rising 0.81\u00b0C per decade.", RED),
    ("Q2", "Construction is concentrated along the ORR / eastern IT corridor, the Yelahanka belt and the western industrial edge (1,370 blocks).", ORANGE),
    ("Q3", "Blocks that went from green to concrete became 6.36\u00b0C hotter relative to the city; densified blocks became 5.16\u00b0C hotter.", BLUE),
    ("Q4", "At 30 m, individual tech-park rooftops and dense housing appear as distinct red hotspots beside blue lakes.", GREEN),
    ("Q5", "Yes. Vegetation correlates with cooler nights (r = \u22120.56 to \u22120.58) and lakes stay ~9\u00b0C cooler than the city average.", CYAN),
]
for i, (q, t, c) in enumerate(finds):
    y = 1.5 + i * 1.0
    rect(s, 0.6, y, 12.13, 0.85, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, 0.6, y, 0.9, 0.85, c, MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, 0.6, y, 0.9, 0.85, q, size=20, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.7, y, 10.9, 0.85, t, size=15, color=LIGHT, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# RECOMMENDATIONS
# =====================================================================
s = new_slide("Recommendations", "Turning the visuals into action")
recs = [
    ("Protect remaining lakes & rajakaluves", "Waterbodies are the city\u2019s strongest cooling assets (~9\u00b0C cooler); enforce buffer zones.", CYAN),
    ("Mandate green cover in new IT parks", "Green-to-concrete blocks jump 6.4\u00b0C, so require canopy and green-roof quotas in building approvals.", GREEN),
    ("Target the eastern IT corridor", "Marathahalli, Bellandur and Munnekollala are warming fastest at night; prioritise them for urban forestry.", ORANGE),
    ("Cool roofs & reflective surfaces", "Large flat rooftops are the hottest 30m pixels; reflective coatings cut absorbed heat.", RED),
    ("Monitor with open satellite data", "This pipeline is free and reproducible; BBMP could refresh it every summer.", BLUE),
]
for i, (h, d, c) in enumerate(recs):
    col, row = i % 2, i // 2
    x = 0.6 + col * 6.15
    y = 1.5 + row * 1.7
    w = 5.98 if i < 4 else 12.13
    rect(s, x, y, w, 1.5, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, x, y + 0.2, 0.08, 1.1, c)
    text(s, x + 0.3, y + 0.15, w - 0.5, 0.45, h, size=16, color=WHITE, bold=True)
    text(s, x + 0.3, y + 0.6, w - 0.5, 0.85, d, size=13, color=LIGHT)

# =====================================================================
# LIMITATIONS
# =====================================================================
s = new_slide("Limitations & Future Work", "Being honest about the data")
insight_panel(s, 0.6, 1.5, 6.0, 5.1, "Limitations", [
    "**Land Surface Temperature \u2260 air temperature**: satellites measure surface (roof/road) heat",
    "Landsat comparison uses **single April scenes**; we normalize to the city mean, but one-day weather still adds noise",
    "MODIS is **1 km**, so ward values for small wards come from only a few pixels",
    "Daytime LST trends slightly down (possible irrigation, aerosol or sensor effects), which needs further study",
    "Zone-level 30m results are mixed (e.g. the Cubbon Park box includes surrounding CBD densification)",
], size=13)
insight_panel(s, 6.85, 1.5, 5.88, 5.1, "Future work", [
    "Use **multi-scene seasonal composites** for Landsat instead of single dates",
    "Add **ECOSTRESS** (70m, multiple times of day) for true night-time detail",
    "Overlay **building footprints** (Google Open Buildings / OSM) and **population** (WorldPop) for heat exposure",
    "Add ground-truth **air temperature** from KSNDMC weather stations",
    "Publish to **Tableau Public** as a live civic tool",
], size=13)

# =====================================================================
# TOOLS & REPRODUCIBILITY
# =====================================================================
s = new_slide("Tools & Reproducibility", "Tech stack")
tools = [
    ("Data acquisition", "Microsoft Planetary Computer STAC  \u2022  OSM Overpass API  \u2022  DataMeet GitHub", RED),
    ("Geospatial processing", "Python  \u2022  rasterio  \u2022  pyproj  \u2022  shapely  \u2022  numpy", ORANGE),
    ("Analysis & EDA", "pandas  \u2022  scipy (linregress, Pearson/Spearman)  \u2022  matplotlib  \u2022  seaborn", BLUE),
    ("Visualization", "Tableau Public: 11 worksheets, 2 dashboards, 1 story", GREEN),
    ("Version control", "Git + GitHub: github.com/Simplicity005/bengaluru-thermal-shift", CYAN),
]
for i, (h, d, c) in enumerate(tools):
    y = 1.5 + i * 0.9
    rect(s, 0.6, y, 12.13, 0.75, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, 0.6, y, 3.3, 0.75, c, MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, 0.6, y, 3.3, 0.75, h, size=15, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 4.1, y, 8.5, 0.75, d, size=14, color=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.6, 6.15, 12.1, 0.5, "Scripts: download_spatial_data.py  \u2022  download_modis_uhi.py  \u2022  download_landsat_30m.py  \u2022  perform_eda.py  \u2022  merge_twbx.py",
     size=12, color=MUTED)

# =====================================================================
# CONCLUSION / THANK YOU
# =====================================================================
s = prs.slides.add_slide(BLANK)
slide_no[0] += 1
rect(s, 0, 0, SW, SH, BG)
rect(s, 0, 0, 0.35, SH, RED)
text(s, 1.2, 1.3, 11, 0.5, "CONCLUSION", size=14, color=ORANGE, bold=True)
text(s, 1.2, 1.8, 11.2, 2.2, [
    "Bengaluru isn\u2019t just getting hotter.",
    "It is losing the ability to cool down.",
], size=38, color=WHITE, bold=True, spacing=1.0)
text(s, 1.2, 3.55, 11, 1.2, "Every patch of green replaced by concrete adds ~6\u00b0C of relative surface heat. "
     "Protecting trees and lakes is the city\u2019s cheapest air-conditioner.", size=18, color=LIGHT)
rect(s, 1.2, 4.95, 1.2, 0.05, RED)
text(s, 1.2, 5.2, 11, 0.8, "Thank You  \u2022  Questions?", size=30, color=WHITE, bold=True)
text(s, 1.2, 6.0, 11, 0.5, "github.com/Simplicity005/bengaluru-thermal-shift", size=14, color=CYAN)

prs.save(OUT)
print(f"Saved {OUT} with {len(prs.slides)} slides")
