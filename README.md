# Bengaluru Urban Heat Island (UHI) — Thermal Shift Data Visualization

> **The "Garden City" to "Silicon Valley" Thermal Shift:** Visualizing how rapid urbanization and loss of green cover drive localized daytime and nighttime heat islands across Bengaluru (2001–2025).

---

## 1. Datasets (`datasets/`)

| File | Resolution / Scope | Source | Description |
|---|---|---|---|
| `Bengaluru_UHI_Master_2001_2025.csv` | 243 BBMP wards × 25 years (6,075 rows, 0 nulls) | NASA MODIS/Terra (`MOD11A2` 1km LST + `MOD13Q1` 250m NDVI/EVI/NDBI) | Summer (Mar–May) Daytime & Nighttime LST (°C), Cooling Drop, NDVI, EVI, NDBI, and Day/Night UHI Anomalies. |
| `Bengaluru_BlockGrid_240m_2002_2025.csv` | 240m × 240m blocks (21,374 blocks) | USGS/NASA Landsat 7 & 8 Collection 2 L2 (Apr 2002, 2015, 2025) | Fine block-level LST, NDVI, NDBI, normalized UHI anomaly (`Delta_UHI_C`), and `Land_Transition` classification. |
| `Bengaluru_Hotspots_30m_2002_2025.csv` | Pure 30m × 30m pixels (21,861 pixels) | USGS/NASA Landsat 7 & 8 Collection 2 L2 | Unaggregated 30m pixels across 5 case-study zones: Bellandur/ORR Ecospace, Whitefield/ITPL, Manyata Tech Park, Electronic City Ph1, and Cubbon Park. |
| `landsat_30m/Bengaluru_30m_*.tif` | 30m × 30m GeoTIFFs (1.37M pixels each) | USGS/NASA Landsat 7 & 8 Collection 2 L2 | Aligned 3-band GeoTIFFs (`LST_C`, `NDVI`, `NDBI`) for 2002, 2015, 2025, plus `Change_2002_2025`. |
| `BBMP_Wards.geojson` | 243 BBMP wards (704.1 km²) | DataMeet `Municipal_Spatial_Data` | Municipal ward boundary polygons (`KGISWardNo`, `KGISWardName`). |
| `Bengaluru_Lakes.geojson` | 1,981 waterbodies (285 named lakes, 5,138 ha) | OpenStreetMap (Overpass API) | Waterbody polygons for thermal cooling overlays. |

---

## 2. Verified EDA Highlights (`scripts/perform_eda.py` & `eda_outputs/`)

Exploratory Data Analysis is complete—see `eda_outputs/eda_summary_metrics.json` and the 7 figures in `eda_outputs/figures/`:

* **Nocturnal Heat Trap (2001–2025):** Nighttime LST rose at **+0.81°C/decade** (*p* = 0.00016, *R²* = 0.47; 5-year mean jumped **23.72°C → 24.97°C**).
* **Collapsing Overnight Cooling:** The Day-to-Night cooling drop fell by **−1.86°C/decade** (*p* = 1.36×10⁻⁸, *R²* = 0.76)—a **−29.7% drop** (from **12.90°C** in 2001–05 to **9.07°C** in 2021–25).
* **Construction-to-Heat Jump (240m Blocks, 2002 → 2025):**
  * *Newly Built-Up (Green → Concrete):* **+6.36°C** relative UHI jump (`ΔNDVI = −0.23`, `ΔNDBI = +0.15`)
  * *Urban Densification (1,311 blocks):* **+5.16°C** relative UHI jump
  * *Persistent Green / Park:* **−0.59°C** (stayed cool)
  * *Waterbodies:* **~9.1°C cooler** than city average
* **Strongest Correlations:**
  * Built-up (`Mean_NDBI`) vs. Daytime LST: **r = +0.636** (and `Delta_NDBI` vs `Delta_UHI_C`: **r = +0.601**)
  * Vegetation (`Mean_NDVI` / `Mean_EVI`) vs. Nighttime UHI Anomaly: **r = −0.565 / −0.597**
* **Fastest-Warming IT-Corridor Wards (Nighttime, 25-yr shift):** Marathahalli (**+1.88°C**), Munnekollala (**+1.57°C**), Bellanduru (**+1.29°C**).

---

## 3. Tableau Quick-Start (20-Second Orientation)

If you are brand new to Tableau (download free **Tableau Public** or **Tableau Desktop Student**):
1. **Left Sidebar ("Data" pane):** Lists your CSV columns. **Blue pills** = text/categories; **Green pills** = numbers.
2. **Top Center ("Columns" & "Rows" shelves):** Drag columns here to create axes.
3. **Middle-Left ("Marks" card):** Controls **Color**, **Size**, **Label**, **Detail**, **Tooltip**, and mark type (**Automatic / Square / Bar / Line**).
4. **Bottom Bar:** Tabs for **Worksheets** (individual charts), **Dashboards** (grid icon), and **Stories** (book icon).

### Team Work Split (Work in Parallel!)
* **Person 1 (First Half):** Builds **Dashboard 1 — Concrete vs. Canopy (240m Block & 30m Building-Scale)** in `Part1_Concrete_vs_Canopy.twbx` (Sheets 1–4).
* **Person 2 (Second Half):** Builds **Dashboard 2 — The Nocturnal Heat Trap (2001–2025)** in `Part2_Nocturnal_UHI.twbx` (Sheets 5–8).
* **Merge & Story (Both):** Copy Person 2's sheets into Person 1's workbook and assemble the **5-Point Tableau Story** (Section 6 below).

---

## 4. Person 1 — First Half Steps (240m Block Map & 30m Building-Scale Hotspots)

### Connect Data (Person 1)
1. Open Tableau → **Connect → To a File → Text file** → open `datasets/Bengaluru_BlockGrid_240m_2002_2025.csv`.
2. *(Optional Lakes Layer)* On the Data Source screen, click **Add** (next to Connections) → **Spatial file** → open `datasets/Bengaluru_Lakes.geojson`. Drag `Bengaluru_Lakes.geojson` next to the CSV in the canvas → click **Create Relationship Calculation** on both sides and type `1` on left and `1` on right.
3. Click **`Sheet 1`** at the bottom-left.

---

### Sheet 1: `240m Heat Map` *(Where Concrete Replaced Green)*
1. Top menu: **Analysis → Create Calculated Field...**
   * Name: `Block Point`
   * Formula: `MAKEPOINT([Lat], [Lon])` → Click **OK**.
2. **Double-click `Block Point`** in the left sidebar (a map with 1 dot appears).
3. Drag **`Grid ID`** from the left sidebar onto **`Detail`** on the Marks card *(all 21,374 blocks appear!)*.
4. On the Marks card dropdown (currently *Automatic*), select **`Square`**. Click **`Size`** and adjust the slider so squares neatly tile Bengaluru.
5. Drag **`Delta UHI C`** onto **`Color`** → click **`Color`** → **Edit Colors...**:
   * Palette: **`Temperature Diverging`** (or **`Red-Blue Diverging`** with **Reversed** checked so Red = hotter, Blue = cooler).
   * Click **`Advanced >>`** → check **Start** = `-6`, **End** = `8`, **Center** = `0` → **OK**.
   * Click **`Color`** again → set **Opacity = 80%**, **Border = None**.
6. Top menu: **Map → Background Maps → Satellite** *(or **Dark**)*.
7. *(Optional Lakes Layer)* Drag **`Geometry`** (from `Bengaluru_Lakes.geojson`) onto the top-left **"Add a Marks Layer"** box on the map → color it bright cyan (`#00D4FF`), Opacity `70%`.
8. Drag **`Land Transition`** onto the **`Filters`** box → click **All → OK** → right-click it in Filters → **Show Filter**.
9. Drag `LST 2002 C`, `LST 2025 C`, `Delta NDVI`, `Delta NDBI`, and `Land Transition` onto **`Tooltip`** for rich hover details.
10. Double-click the bottom tab **`Sheet 1`** → rename to **`240m Heat Map`**.

---

### Sheet 2: `Heat Jump by Land Transition` *(Proof Bar Chart)*
1. Click the **`New Worksheet`** icon (bottom bar, `+` chart icon).
2. Drag **`Delta UHI C`** to **Columns** → right-click the green pill → **Measure → Average** (now says `AVG(Delta UHI C)`).
3. Drag **`Land Transition`** to **Rows**.
4. Click the **Sort Descending** button in the top toolbar (so *Newly Built-Up (Green -> Concrete)* at **+6.36°C** is at the top).
5. Drag **`Delta UHI C`** (set to **Average**) onto **`Color`** → Edit Colors → same Blue–Red diverging palette, **Center = `0`**.
6. Drag **`Delta UHI C`** (set to **Average**) onto **`Label`** → right-click the pill → **Format** → Numbers → **Custom** → `+0.0°C;-0.0°C`.
7. Rename tab to **`Heat Jump by Land Transition`**.

---

### Sheet 3: `30m Hotspot Zoom` *(Pure 30m Building-Scale Map)*
1. Click **New Worksheet**.
2. Top menu: **Data → New Data Source → Text file** → open `datasets/Bengaluru_Hotspots_30m_2002_2025.csv`. Click back to your new worksheet.
3. Top menu: **Analysis → Create Calculated Field...**
   * Name: `Pixel Point`
   * Formula: `MAKEPOINT([Lat], [Lon])` → **OK**.
4. Drag **`Zone`** onto **`Filters`** → select ONLY **`Bellandur_ORR_Ecospace`** → **OK**.
5. Right-click **`Zone`** in Filters → **Show Filter** → click the tiny dropdown arrow on the Zone filter card (right side) → select **Single Value (Dropdown)**.
6. **Double-click `Pixel Point`**.
7. Drag **`Lat`** and **`Lon`** onto **`Detail`** → right-click BOTH pills in Marks and select **Dimension** *(this plots every raw 30m × 30m pixel!)*.
8. Change Marks dropdown to **`Square`**, set Opacity to **`75%`**.
9. Drag **`Delta UHI C`** onto **`Color`** → Blue–Red diverging palette, **Start = `-6`, Center = `0`, End = `8`**.
10. Top menu: **Map → Background Maps → Satellite** *(now you can see actual buildings & tech parks beneath the 30m pixels!)*.
11. Drag `LST 2002 C`, `LST 2025 C`, `Delta NDVI`, `Delta NDBI` onto **`Tooltip`**.
12. Rename tab to **`30m Hotspot Zoom`**.

---

### Sheet 4: `Tree Loss vs Heat Scatter` *(Correlation Proof)*
1. Click **New Worksheet** (make sure **`Bengaluru_Hotspots_30m_2002_2025`** is selected at the top-left Data pane).
2. Drag **`Delta NDVI`** to **Columns** and **`Delta UHI C`** to **Rows**.
3. Top menu: **Analysis → uncheck "Aggregate Measures"** *(all 21,861 pixels spread into a scatter plot!)*.
4. Drag **`Zone`** to **Filters** → **Show Filter** (Single Value Dropdown, or All).
5. Drag **`Delta NDBI`** onto **`Color`** (Red-Blue or Orange-Blue palette; Opacity `45%`).
6. In the left sidebar, click the **`Analytics`** tab (next to Data) → drag **`Trend Line`** onto the canvas → drop on **Linear**.
7. Rename tab to **`Tree Loss vs Heat Scatter`**.

---

### Assemble Dashboard 1 (Person 1)
1. Click the **`New Dashboard`** icon (bottom bar, grid icon) → rename to **`Dashboard 1 - Concrete vs Canopy`**.
2. Left sidebar under **Size**: change to **Fixed Size → Generic Desktop (1600 × 900)** (or **Automatic**).
3. Drag **`240m Heat Map`** onto the left side (~55% width).
4. Drag **`Heat Jump by Land Transition`** to the top-right, and **`30m Hotspot Zoom`** (or **`Tree Loss vs Heat Scatter`**) to the bottom-right.
5. Click **`Heat Jump by Land Transition`** on the dashboard → click the tiny **funnel icon ("Use as Filter")** on its top-right border *(now clicking "Newly Built-Up" filters the 240m map live!)*.
6. Save as **`Part1_Concrete_vs_Canopy.twbx`** (*File → Save As → Tableau Packaged Workbook `.twbx`*).

---

## 5. Person 2 — Second Half Steps (25-Year Nighttime UHI & Ward Trends)

### Connect Data (Person 2)
1. Open Tableau → **Connect → To a File → Spatial file** → open `datasets/BBMP_Wards.geojson`.
2. On the Data Source screen, click **Add** (next to Connections) → **Text file** → open `datasets/Bengaluru_UHI_Master_2001_2025.csv`.
3. Drag `Bengaluru_UHI_Master_2001_2025.csv` onto the canvas next to `BBMP_Wards.geojson`.
4. In the **Edit Relationship** box at the bottom, match **`KGISWardNo` = `KGISWardNo`**.
   * *Tip:* If Tableau shows a red exclamation mark (type mismatch), click the data type icon (`Abc` or `#`) above `KGISWardNo` in one of the tables so **both are `String` (`Abc`)** or **both are `Number (whole)` (`#`)**.
5. Click **`Sheet 1`** at the bottom-left.

---

### Sheet 5: `25-Year Nighttime Heat Trap` *(Dual-Axis Trend)*
1. Drag **`Year`** to **Columns** → right-click the `Year` pill → select **Continuous** (turns green).
2. Drag **`Night LST C`** to **Rows** → right-click → **Measure → Average**.
3. Drag **`Cooling Drop C`** to **Rows** (to the right of `AVG(Night LST C)`) → right-click → **Measure → Average**.
4. Right-click **`AVG(Cooling Drop C)`** on Rows → click **Dual Axis**. *(Do NOT synchronize axes—keep Night LST on left axis and Cooling Drop on right axis.)*
5. On the Marks card, click the **`AVG(Night LST C)`** sub-card:
   * Change mark type to **`Line`**, Color = **Bright Red/Orange** (`#FF4B2B`), increase Size slightly.
6. Click the **`AVG(Cooling Drop C)`** sub-card:
   * Change mark type to **`Area`** (or **`Line`**), Color = **Cool Blue** (`#2B9BFF`), Opacity = `30%`.
7. Left sidebar → **`Analytics`** tab → drag **`Trend Line`** onto **Linear** (shows the statistically significant **+0.81°C/decade** nighttime rise and **−1.86°C/decade** cooling collapse!).
8. Double-click the bottom tab → rename to **`25-Year Nighttime Heat Trap`**.

---

### Sheet 6: `Animated Ward Night UHI Map` *(2001 → 2025 Time-Lapse)*
1. Click **New Worksheet**.
2. From `BBMP_Wards.geojson` in the left sidebar, **double-click `Geometry`** *(all 243 BBMP ward polygons appear!)*.
3. Drag **`KGISWardName`** onto **`Detail`** (and **`Tooltip`**) so each ward is distinct.
4. Drag **`Night UHI Anomaly C`** onto **`Color`** → right-click → **Measure → Average**.
5. Click **`Color`** → **Edit Colors...** → Palette: **`Temperature Diverging`** → **Advanced >>** → Start = `-2.5`, Center = `0`, End = `2.0` → **OK**.
6. Drag **`Year`** (from the CSV) onto the **`Pages`** shelf (right above the Filters box!).
   * *Magic:* A playback control box appears on the right with a **Play ▶ button** so you can animate 2001 → 2025 live!
7. Top menu: **Map → Background Maps → Dark**.
8. Drag `Day LST C`, `Night LST C`, `Cooling Drop C`, `Mean NDVI`, `Mean NDBI` onto **`Tooltip`**.
9. Rename tab to **`Animated Ward Night UHI Map`**.

---

### Sheet 7: `Warming Wards Ranking` *(Hottest vs. Coolest Wards)*
1. Click **New Worksheet**.
2. Drag **`KGISWardName`** to **Rows**.
3. Drag **`Night LST C`** to **Columns** → right-click → **Measure → Average**.
4. Drag **`Year`** to **Filters** → select **`2025`** (or `2021–2025`) → **OK** → right-click → **Show Filter** (so viewers can pick any year).
5. Click the **Sort Descending** button in the top toolbar.
6. To keep the chart clean (Top 15 Hottest Wards):
   * Drag **`KGISWardName`** onto **Filters** → click the **`Top`** tab → select **By field: Top `15` by `Night LST C` Average** → **OK**.
7. Drag **`Mean NDVI`** (Average) onto **`Color`** (Green–Red diverging palette: low greenery = red, high greenery = green) and **`AVG(Night LST C)`** onto **`Label`**.
8. Rename tab to **`Warming Wards Ranking`**.

---

### Sheet 8: `Executive KPI Cards` *(3 Sleek Modular Cards)*

Instead of a single cramped line of text, build **3 modern, professional KPI cards** that sit side-by-side across the top of your dashboard (like an executive Bloomberg/Stripe analytics header).

#### Card 1: `KPI 1 - Night Warming`
1. Click **New Worksheet** → rename to **`KPI 1 - Night Warming`**.
2. Top menu: **Analysis → Create Calculated Field...**
   * Name: `KPI 1 Value` → Formula: `"+1.25°C"` → click **OK**.
3. Drag **`KPI 1 Value`** onto **`Text`** on the Marks card.
4. Click **`Text`** on the Marks card → click the **`...`** (Edit Text) button:
   * Replace the text box with:
     ```text
     ▲ +1.25°C
     NIGHTTIME LST RISE
     2001–05 (23.7°C) → 2021–25 (25.0°C)
     ```
   * **Formatting:**
     * Line 1 (`▲ +1.25°C`): **22pt, Bold, Bright Red/Coral (`#FF4B2B`)**
     * Line 2 (`NIGHTTIME LST RISE`): **9pt, Bold, Dark Gray / White (`#666666`), Uppercase**
     * Line 3 (`2001–05...`): **8pt, Regular, Muted Gray (`#999999`)**
     * Alignment: **Center**
5. Change toolbar dropdown from *Standard* to **`Entire View`**.

---

#### Card 2: `KPI 2 - Cooling Collapse`
1. Click **New Worksheet** → rename to **`KPI 2 - Cooling Collapse`**.
2. Create Calculated Field `KPI 2 Value` → Formula: `"-29.7%"` → **OK**.
3. Drag **`KPI 2 Value`** onto **`Text`** on the Marks card.
4. Click **`Text`** → click **`...`** → enter:
   ```text
   ▼ −29.7%
   OVERNIGHT COOLING COLLAPSE
   Diurnal drop fell from 12.9°C → 9.1°C
   ```
   * **Formatting:**
     * Line 1 (`▼ −29.7%`): **22pt, Bold, Deep Orange (`#FF7A00`)**
     * Line 2 (`OVERNIGHT COOLING...`): **9pt, Bold, Dark Gray, Uppercase**
     * Line 3 (`Diurnal drop...`): **8pt, Regular, Muted Gray**
     * Alignment: **Center**
5. Change toolbar dropdown to **`Entire View`**.

---

#### Card 3: `KPI 3 - Construction Jump`
1. Click **New Worksheet** → rename to **`KPI 3 - Construction Jump`**.
2. Create Calculated Field `KPI 3 Value` → Formula: `"+6.36°C"` → **OK**.
3. Drag **`KPI 3 Value`** onto **`Text`** on the Marks card.
4. Click **`Text`** → click **`...`** → enter:
   ```text
   ▲ +6.36°C
   NEW CONSTRUCTION UHI JUMP
   240m Blocks: Green replaced by Concrete
   ```
   * **Formatting:**
     * Line 1 (`▲ +6.36°C`): **22pt, Bold, Crimson Red (`#E50914`)**
     * Line 2 (`NEW CONSTRUCTION...`): **9pt, Bold, Dark Gray, Uppercase**
     * Line 3 (`240m Blocks...`): **8pt, Regular, Muted Gray**
     * Alignment: **Center**
5. Change toolbar dropdown to **`Entire View`**.

---

### Assemble Dashboard 2 (Person 2)
1. Click **New Dashboard** → rename to **`Dashboard 2 - Nocturnal Heat Trap`**.
2. Set Size to **Fixed Size → Generic Desktop (1600 × 900)**.
3. **Build the KPI Top Banner (Horizontal Container):**
   * From the bottom-left **Objects** panel, drag a **`Horizontal`** container to the top ~12% of the dashboard canvas.
   * Drag **`KPI 1 - Night Warming`**, **`KPI 2 - Cooling Collapse`**, and **`KPI 3 - Construction Jump`** inside this horizontal container, side-by-side.
   * Right-click any card title/tab inside the container → select **Select Container: Horizontal** → click its blue dropdown arrow → select **`Distribute Contents Evenly`** *(all 3 cards automatically become perfectly equal in width!)*.
   * *(Optional Polish)* Right-click each KPI title on the dashboard → **Hide Title**. In the **Layout** tab on the left, set background to subtle gray `#F4F5F7` (or dark `#202124`) with `4px` padding and a clean thin border.
4. **Arrange the Remaining Charts:**
   * **Left (55% width):** Drag `Animated Ward Night UHI Map` (keep the **Year Pages Play control** visible right next to it!).
   * **Right Top (45% width):** Drag `25-Year Nighttime Heat Trap`.
   * **Right Bottom (45% width):** Drag `Warming Wards Ranking`.
5. Click **`Animated Ward Night UHI Map`** → enable **Use as Filter** (funnel icon) so clicking any ward updates the 25-year trend line for that specific ward!
6. Save as **`Part2_Nocturnal_UHI.twbx`** (*File → Save As → Tableau Packaged Workbook `.twbx`*).

---

## 6. Merging Both Halves + Building the Tableau Story (Final Step)

### How to Combine Person 1 & Person 2 into One Workbook
1. Open **both** `Part1_Concrete_vs_Canopy.twbx` and `Part2_Nocturnal_UHI.twbx` in Tableau.
2. In `Part2_Nocturnal_UHI.twbx`, right-click the **`Dashboard 2 - Nocturnal Heat Trap`** tab at the bottom → click **Copy**.
3. Switch to `Part1_Concrete_vs_Canopy.twbx` → right-click any tab at the bottom → click **Paste**.
   *(Tableau automatically copies Dashboard 2, all 4 of Person 2's sheets, AND Person 2's data connection in one click!)*
4. Save as **`Bengaluru_Thermal_Shift_Final.twbx`**.

### Building the 5-Point Tableau Story *(Click the "New Story" book icon at the bottom bar)*
Drag sheets/dashboards from the left panel onto each Story Point and type these captions at the top:

| Story Point | Drag Onto Canvas | Caption / Narrative Takeaway |
|---|---|---|
| **1. The Hook** | `25-Year Nighttime Heat Trap` | *"Bengaluru isn't just getting hotter—it stopped cooling down at night (−29.7% overnight cooling since 2001)."* |
| **2. The City-Wide Spread** | `Animated Ward Night UHI Map` | *"Over 25 years, nighttime heat intensified fastest across the eastern IT corridor (Marathahalli +1.88°C, Bellandur +1.29°C)."* |
| **3. Beyond Wards (240m)** | `Dashboard 1 - Concrete vs Canopy` | *"Zooming past ward averages to 240m blocks: plots where concrete replaced green cover jumped +6.36°C."* |
| **4. Down to the Building (30m)** | `30m Hotspot Zoom` (set to *Bellandur_ORR_Ecospace*) | *"At 30m satellite resolution, individual tech parks & concrete corridors stand out starkly against green parks & lakes."* |
| **5. The Solution** | `Tree Loss vs Heat Scatter` | *"Vegetation loss directly drives warming (r = −0.57 nighttime UHI), while lakes stay ~9°C cooler than concrete."* |

---

## 7. Reproduction Scripts (`scripts/`)
- `scripts/download_spatial_data.py` — Downloads `BBMP_Wards.geojson` and `Bengaluru_Lakes.geojson`.
- `scripts/download_modis_uhi.py` — Extracts 2001–2025 NASA MODIS/Terra Day/Night LST and NDVI/EVI/NDBI via Microsoft Planetary Computer STAC.
- `scripts/download_landsat_30m.py` — Extracts 30m Landsat C2 L2 April scenes (2002, 2015, 2025) and generates aligned GeoTIFFs, 240m block grid CSV, and 30m hotspot CSV.
- `scripts/perform_eda.py` — Runs full statistical & spatial EDA and saves summary metrics + 7 figures in `eda_outputs/`.
