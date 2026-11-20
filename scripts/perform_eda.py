import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import geopandas as gpd
import tifffile

# Set styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11

OUTPUT_DIR = "eda_outputs"
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

print("=" * 80)
print("BENGALURU URBAN HEAT ISLAND (UHI) - EXPLORATORY DATA ANALYSIS (EDA)")
print("=" * 80)

# ==============================================================================
# 1. BBMP WARDS MASTER DATASET (2001-2025)
# ==============================================================================
print("\n>>> 1. ANALYZING Bengaluru_UHI_Master_2001_2025.csv...")
master_path = "datasets/Bengaluru_UHI_Master_2001_2025.csv"
df_master = pd.read_csv(master_path)

# Basic Schema & Integrity
n_rows, n_cols = df_master.shape
n_wards = df_master["KGISWardNo"].nunique()
years = sorted(df_master["Year"].unique())
min_year, max_year = min(years), max(years)
n_years = len(years)
missing_counts = df_master.isnull().sum().to_dict()
duplicates = int(df_master.duplicated(subset=["KGISWardNo", "Year"]).sum())

print(f"Dimensions: {n_rows} rows × {n_cols} columns")
print(f"Unique Wards: {n_wards} | Year span: {min_year} - {max_year} ({n_years} years)")
print(f"Duplicates (Ward x Year): {duplicates}")
print(f"Missing values: {missing_counts}")

# Numeric summary stats
num_cols_master = [
    "Day_LST_C", "Night_LST_C", "Cooling_Drop_C", 
    "Mean_NDVI", "Mean_EVI", "Mean_NDBI", 
    "Day_UHI_Anomaly_C", "Night_UHI_Anomaly_C"
]
master_desc = df_master[num_cols_master].describe().T
master_desc["skew"] = df_master[num_cols_master].skew()
master_desc["kurtosis"] = df_master[num_cols_master].kurtosis()
print("\nMaster Dataset Numerical Summary:")
print(master_desc[["mean", "std", "min", "50%", "max", "skew", "kurtosis"]].round(3))

# Temporal Trend Analysis (City-wide Annual Means)
annual_means = df_master.groupby("Year")[num_cols_master].mean()

# Compute Linear Trends (OLS regression slope per year & per decade)
trend_stats = {}
for col in num_cols_master:
    slope, intercept, r_val, p_val, std_err = stats.linregress(annual_means.index, annual_means[col])
    trend_stats[col] = {
        "slope_per_year": float(slope),
        "slope_per_decade": float(slope * 10),
        "r_squared": float(r_val**2),
        "p_value": float(p_val),
        "std_err": float(std_err)
    }

print("\nLong-term Trends (2001-2025):")
for col, ts in trend_stats.items():
    print(f"  {col:20s}: {ts['slope_per_decade']:+.3f} per decade | R²={ts['r_squared']:.3f} | p={ts['p_value']:.4e}")

# Decadal comparison
dec_early = df_master[df_master["Year"].isin(range(2001, 2006))]
dec_mid = df_master[df_master["Year"].isin(range(2011, 2016))]
dec_late = df_master[df_master["Year"].isin(range(2021, 2026))]

decadal_summary = pd.DataFrame({
    "2001_2005_Mean": dec_early[num_cols_master].mean(),
    "2011_2015_Mean": dec_mid[num_cols_master].mean(),
    "2021_2025_Mean": dec_late[num_cols_master].mean(),
    "Change_25yr": dec_late[num_cols_master].mean() - dec_early[num_cols_master].mean(),
    "Pct_Change": ((dec_late[num_cols_master].mean() - dec_early[num_cols_master].mean()) / dec_early[num_cols_master].mean().abs()) * 100
}).round(3)
print("\nDecadal Shift (2001-2005 vs 2021-2025):")
print(decadal_summary)

# Ward-Level Warming & Vegetation Dynamics
ward_early = dec_early.groupby(["KGISWardNo", "KGISWardName"])[["Day_LST_C", "Night_LST_C", "Cooling_Drop_C", "Mean_NDVI", "Mean_NDBI"]].mean()
ward_late = dec_late.groupby(["KGISWardNo", "KGISWardName"])[["Day_LST_C", "Night_LST_C", "Cooling_Drop_C", "Mean_NDVI", "Mean_NDBI"]].mean()
ward_shift = (ward_late - ward_early).rename(columns=lambda c: f"Delta_{c}")
ward_overall = df_master.groupby(["KGISWardNo", "KGISWardName"])[num_cols_master].mean()
ward_full = ward_overall.join(ward_shift).reset_index()

# Top / Bottom Wards
top_day_lst = ward_full.nlargest(10, "Day_LST_C")[["KGISWardNo", "KGISWardName", "Day_LST_C", "Night_LST_C", "Mean_NDVI", "Mean_NDBI"]]
cool_day_lst = ward_full.nsmallest(10, "Day_LST_C")[["KGISWardNo", "KGISWardName", "Day_LST_C", "Night_LST_C", "Mean_NDVI", "Mean_NDBI"]]
top_warming = ward_full.nlargest(10, "Delta_Day_LST_C")[["KGISWardNo", "KGISWardName", "Delta_Day_LST_C", "Delta_Night_LST_C", "Delta_Mean_NDVI", "Delta_Mean_NDBI"]]
top_veg_loss = ward_full.nsmallest(10, "Delta_Mean_NDVI")[["KGISWardNo", "KGISWardName", "Delta_Mean_NDVI", "Delta_Day_LST_C", "Delta_Mean_NDBI"]]
top_built_gain = ward_full.nlargest(10, "Delta_Mean_NDBI")[["KGISWardNo", "KGISWardName", "Delta_Mean_NDBI", "Delta_Mean_NDVI", "Delta_Day_LST_C"]]
min_cooling_drop = ward_full.nsmallest(10, "Cooling_Drop_C")[["KGISWardNo", "KGISWardName", "Cooling_Drop_C", "Day_LST_C", "Night_LST_C", "Mean_NDBI"]]

print("\nTop 5 Hottest Wards (25-yr Summer Mean Day LST):")
print(top_day_lst.head(5).to_string(index=False))
print("\nTop 5 Coolest Wards (25-yr Summer Mean Day LST):")
print(cool_day_lst.head(5).to_string(index=False))
print("\nTop 5 Fastest Warming Wards (Daytime ΔLST 2001-05 to 2021-25):")
print(top_warming.head(5).to_string(index=False))
print("\nTop 5 Wards with Greatest Vegetation Loss (ΔNDVI):")
print(top_veg_loss.head(5).to_string(index=False))

# Correlation Analysis
corr_pearson = df_master[num_cols_master].corr(method="pearson").round(3)
corr_spearman = df_master[num_cols_master].corr(method="spearman").round(3)
print("\nPearson Correlation Matrix:")
print(corr_pearson)

# ==============================================================================
# 2. 240M BLOCK GRID DATASET (2002-2025)
# ==============================================================================
print("\n>>> 2. ANALYZING Bengaluru_BlockGrid_240m_2002_2025.csv...")
grid_path = "datasets/Bengaluru_BlockGrid_240m_2002_2025.csv"
df_grid = pd.read_csv(grid_path)

grid_rows, grid_cols = df_grid.shape
grid_nulls = df_grid.isnull().sum().to_dict()
print(f"Dimensions: {grid_rows} blocks × {grid_cols} columns")
print(f"Missing values: {grid_nulls}")

grid_num_cols = ["LST_2002_C", "LST_2015_C", "LST_2025_C", "Delta_LST_C", "NDVI_2002", "NDVI_2025", "Delta_NDVI", "NDBI_2002", "NDBI_2025", "Delta_NDBI"]
grid_desc = df_grid[grid_num_cols].describe().T
print("\nBlock Grid Numerical Summary:")
print(grid_desc[["mean", "std", "min", "50%", "max"]].round(3))

# Land Transition Breakdown
trans_counts = df_grid["Land_Transition"].value_counts()
trans_pcts = (df_grid["Land_Transition"].value_counts(normalize=True) * 100).round(2)
trans_summary = pd.DataFrame({"Count": trans_counts, "Percentage": trans_pcts})
print("\nLand Transition Breakdown:")
print(trans_summary)

# Transition Stats
trans_stats = df_grid.groupby("Land_Transition")[["Delta_LST_C", "Delta_NDVI", "Delta_NDBI", "LST_2002_C", "LST_2025_C"]].agg(["mean", "std", "median"]).round(2)
print("\nMean Shifts by Land Transition:")
print(trans_stats)

# ANOVA Test: Is Delta_LST_C statistically significantly different across Land Transition types?
groups_lst = [group["Delta_LST_C"].dropna().values for _, group in df_grid.groupby("Land_Transition")]
f_val, p_val_anova = stats.f_oneway(*groups_lst)
kw_stat, p_val_kw = stats.kruskal(*groups_lst)
print(f"\nANOVA test for Delta_LST_C across Land Transitions: F={f_val:.2f}, p-value={p_val_anova:.4e}")
print(f"Kruskal-Wallis test: H={kw_stat:.2f}, p-value={p_val_kw:.4e}")

# Correlation at 240m resolution
grid_corr = df_grid[["Delta_LST_C", "Delta_NDVI", "Delta_NDBI", "NDVI_2002", "NDVI_2025", "NDBI_2002", "NDBI_2025"]].corr().round(3)
print("\n240m Grid Correlation Matrix (Deltas):")
print(grid_corr)

# ==============================================================================
# 3. 30M HOTSPOTS DATASET (5 CASE-STUDY ZONES)
# ==============================================================================
print("\n>>> 3. ANALYZING Bengaluru_Hotspots_30m_2002_2025.csv...")
hotspots_path = "datasets/Bengaluru_Hotspots_30m_2002_2025.csv"
df_hotspots = pd.read_csv(hotspots_path)

hot_rows, hot_cols = df_hotspots.shape
print(f"Dimensions: {hot_rows} pixels × {hot_cols} columns")
print("Pixel count per Zone:")
print(df_hotspots["Zone"].value_counts())

hotspot_stats = df_hotspots.groupby("Zone")[["LST_2002_C", "LST_2015_C", "LST_2025_C", "Delta_LST_C", "NDVI_2002", "NDVI_2025", "Delta_NDVI", "NDBI_2002", "NDBI_2025", "Delta_NDBI"]].mean().round(2)
print("\nZonal Means (30m pixels):")
print(hotspot_stats)

# Compute Differential Warming against Cubbon Park Benchmark
cubbon_delta_lst = hotspot_stats.loc["Cubbon_Park_Benchmark", "Delta_LST_C"]
cubbon_2025_lst = hotspot_stats.loc["Cubbon_Park_Benchmark", "LST_2025_C"]
thermal_penalty = pd.DataFrame({
    "Mean_LST_2025_C": hotspot_stats["LST_2025_C"],
    "Delta_LST_C": hotspot_stats["Delta_LST_C"],
    "Thermal_Penalty_vs_Cubbon_2025": hotspot_stats["LST_2025_C"] - cubbon_2025_lst,
    "Excess_Warming_vs_Cubbon": hotspot_stats["Delta_LST_C"] - cubbon_delta_lst,
    "Delta_NDVI": hotspot_stats["Delta_NDVI"],
    "Delta_NDBI": hotspot_stats["Delta_NDBI"]
}).round(2)
print("\nThermal Penalty Relative to Cubbon Park Benchmark:")
print(thermal_penalty)

# ==============================================================================
# 4. SPATIAL DATASETS: BBMP_Wards.geojson & Bengaluru_Lakes.geojson
# ==============================================================================
print("\n>>> 4. ANALYZING Spatial GeoJSON Datasets...")
gdf_wards = gpd.read_file("datasets/BBMP_Wards.geojson")
gdf_lakes = gpd.read_file("datasets/Bengaluru_Lakes.geojson")

print(f"BBMP Wards GeoDataFrame: {len(gdf_wards)} wards | CRS: {gdf_wards.crs}")
print(f"Valid Geometries: {gdf_wards.is_valid.sum()} / {len(gdf_wards)}")
bounds = gdf_wards.total_bounds
print(f"Ward Extents [W, S, E, N]: {[round(x, 4) for x in bounds]}")

# Reproject to UTM 43N (EPSG:32643) for accurate area calculation in sq km
gdf_wards_proj = gdf_wards.to_crs(epsg=32643)
gdf_wards["area_sqkm"] = gdf_wards_proj.geometry.area / 1e6
total_bbmp_area = gdf_wards["area_sqkm"].sum()
print(f"Total BBMP Area: {total_bbmp_area:.2f} sq km")
print(f"Ward Area Stats (sq km): Min={gdf_wards['area_sqkm'].min():.2f}, Max={gdf_wards['area_sqkm'].max():.2f}, Mean={gdf_wards['area_sqkm'].mean():.2f}")

print(f"\nBengaluru Lakes GeoDataFrame: {len(gdf_lakes)} waterbodies | CRS: {gdf_lakes.crs}")
print(f"Valid Geometries: {gdf_lakes.is_valid.sum()} / {len(gdf_lakes)}")
gdf_lakes_proj = gdf_lakes.to_crs(epsg=32643)
gdf_lakes["area_ha"] = gdf_lakes_proj.geometry.area / 10000.0  # hectares
named_lakes = gdf_lakes[gdf_lakes["name"] != "Unnamed Waterbody"]
print(f"Named Lakes: {len(named_lakes)} | Unnamed Waterbodies: {len(gdf_lakes) - len(named_lakes)}")
print(f"Total Lake Area: {gdf_lakes['area_ha'].sum():.2f} ha ({gdf_lakes['area_ha'].sum() / 100:.2f} sq km)")
print("Top 5 Largest Named Lakes by Area:")
top_lakes = named_lakes.sort_values(by="area_ha", ascending=False)[["name", "area_ha"]].head(5)
print(top_lakes.to_string(index=False))

# ==============================================================================
# 5. GEOTIFF RASTERS (datasets/landsat_30m/)
# ==============================================================================
print("\n>>> 5. ANALYZING GeoTIFF Landsat Rasters...")
tif_files = [
    ("Bengaluru_30m_2002.tif", ["LST_C", "NDVI", "NDBI"]),
    ("Bengaluru_30m_2015.tif", ["LST_C", "NDVI", "NDBI"]),
    ("Bengaluru_30m_2025.tif", ["LST_C", "NDVI", "NDBI"]),
    ("Bengaluru_30m_Change_2002_2025.tif", ["Delta_LST_C", "Delta_NDVI", "Delta_NDBI"])
]
tif_stats = {}
for tf_name, band_names in tif_files:
    tf_path = os.path.join("datasets/landsat_30m", tf_name)
    arr = tifffile.imread(tf_path)  # shape: (1145, 1202, 3)
    h, w, c = arr.shape
    b1 = arr[:, :, 0]
    b2 = arr[:, :, 1]
    b3 = arr[:, :, 2]
    valid_mask = np.isfinite(b1)
    tif_stats[tf_name] = {
        "width": w,
        "height": h,
        "bands": c,
        "valid_pct": float(valid_mask.mean() * 100),
        "b1_name": band_names[0],
        "b1_mean": float(np.nanmean(b1)),
        "b1_std": float(np.nanstd(b1)),
        "b1_min": float(np.nanmin(b1)),
        "b1_max": float(np.nanmax(b1)),
        "b2_name": band_names[1],
        "b2_mean": float(np.nanmean(b2)),
        "b3_name": band_names[2],
        "b3_mean": float(np.nanmean(b3)),
    }
print("GeoTIFF Metadata & Stats:")
for k, v in tif_stats.items():
    print(f"  {k}: {v['width']}x{v['height']}, {v['valid_pct']:.1f}% valid | {v['b1_name']} Mean={v['b1_mean']:.2f} (±{v['b1_std']:.2f}) | {v['b2_name']} Mean={v['b2_mean']:.3f} | {v['b3_name']} Mean={v['b3_mean']:.3f}")

# ==============================================================================
# 6. GENERATING EDA VISUALIZATION FIGURES
# ==============================================================================
print("\n>>> 6. GENERATING EDA VISUALIZATION FIGURES...")

# Figure 1: 25-Year Summer Temporal Trajectories (MODIS Master)
fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)

# 1a. LST Day & Night
axes[0].plot(annual_means.index, annual_means["Day_LST_C"], marker="o", color="#d95f02", linewidth=2.2, label="Daytime LST (MOD11A2)")
axes[0].plot(annual_means.index, annual_means["Night_LST_C"], marker="s", color="#7570b3", linewidth=2.2, label="Nighttime LST (MOD11A2)")
# Trendlines
z_day = np.polyfit(annual_means.index, annual_means["Day_LST_C"], 1)
p_day = np.poly1d(z_day)
axes[0].plot(annual_means.index, p_day(annual_means.index), "--", color="#d95f02", alpha=0.7, label=f"Day Trend: {trend_stats['Day_LST_C']['slope_per_decade']:+.2f}°C/dec")
z_night = np.polyfit(annual_means.index, annual_means["Night_LST_C"], 1)
p_night = np.poly1d(z_night)
axes[0].plot(annual_means.index, p_night(annual_means.index), "--", color="#7570b3", alpha=0.7, label=f"Night Trend: {trend_stats['Night_LST_C']['slope_per_decade']:+.2f}°C/dec")
axes[0].set_ylabel("Summer Mean LST (°C)")
axes[0].set_title("Bengaluru City-Wide Summer (Mar-May) Thermal Trajectory (2001-2025)", fontweight="bold")
axes[0].legend(loc="upper left", frameon=True)
axes[0].grid(True, linestyle="--", alpha=0.5)

# 1b. Diurnal Cooling Drop
axes[1].plot(annual_means.index, annual_means["Cooling_Drop_C"], marker="^", color="#1b9e77", linewidth=2.2, label="Diurnal Cooling Drop (Day - Night)")
z_drop = np.polyfit(annual_means.index, annual_means["Cooling_Drop_C"], 1)
p_drop = np.poly1d(z_drop)
axes[1].plot(annual_means.index, p_drop(annual_means.index), "--", color="#1b9e77", alpha=0.7, label=f"Cooling Trend: {trend_stats['Cooling_Drop_C']['slope_per_decade']:+.2f}°C/dec")
axes[1].set_ylabel("Diurnal Drop (°C)")
axes[1].set_title("Diurnal Heat Dissipation / Nocturnal Cooling Capacity", fontweight="bold")
axes[1].legend(loc="upper right", frameon=True)
axes[1].grid(True, linestyle="--", alpha=0.5)

# 1c. Indices (NDVI vs NDBI)
axes[2].plot(annual_means.index, annual_means["Mean_NDVI"], marker="o", color="#2ca02c", linewidth=2.2, label="Mean NDVI (Vegetation Index)")
axes[2].plot(annual_means.index, annual_means["Mean_NDBI"], marker="s", color="#e7298a", linewidth=2.2, label="Mean NDBI (Built-up Index)")
axes[2].set_ylabel("Index Value (-1 to +1)")
axes[2].set_xlabel("Year")
axes[2].set_title("Vegetation Decline vs Built-Up Expansion Across Bengaluru Wards", fontweight="bold")
axes[2].set_xticks(range(2001, 2026, 2))
axes[2].legend(loc="center left", frameon=True)
axes[2].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
fig1_path = os.path.join(FIGURES_DIR, "fig1_temporal_trends_2001_2025.png")
plt.savefig(fig1_path, dpi=200)
plt.close()
print(f"Saved: {fig1_path}")

# Figure 2: Correlation Heatmap
fig, ax = plt.subplots(figsize=(9, 7))
mask = np.triu(np.ones_like(corr_pearson, dtype=bool))
cmap = sns.diverging_palette(230, 20, as_cmap=True)
sns.heatmap(corr_pearson, mask=mask, cmap=cmap, vmin=-1.0, vmax=1.0, center=0,
            annot=True, fmt=".2f", square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax)
ax.set_title("Pearson Correlation Matrix — Bengaluru Ward UHI Metrics (2001-2025)", fontweight="bold", pad=12)
plt.tight_layout()
fig2_path = os.path.join(FIGURES_DIR, "fig2_correlation_matrix.png")
plt.savefig(fig2_path, dpi=200)
plt.close()
print(f"Saved: {fig2_path}")

# Figure 3: Scatter & Regression: NDVI and NDBI vs Day LST
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sample_df = df_master.dropna(subset=["Day_LST_C", "Mean_NDVI", "Mean_NDBI"]).sample(n=min(2000, len(df_master)), random_state=42)

# NDVI vs Day LST
sns.regplot(data=sample_df, x="Mean_NDVI", y="Day_LST_C", ax=axes[0],
            scatter_kws={"alpha": 0.25, "color": "#2ca02c", "s": 20},
            line_kws={"color": "#006400", "linewidth": 2.5})
slope_ndvi, _, r_ndvi, p_ndvi, _ = stats.linregress(df_master.dropna(subset=["Day_LST_C", "Mean_NDVI"])["Mean_NDVI"], df_master.dropna(subset=["Day_LST_C", "Mean_NDVI"])["Day_LST_C"])
axes[0].set_title(f"Vegetation Cooling: NDVI vs Daytime LST\nSlope = {slope_ndvi:.2f}°C per unit NDVI (r = {r_ndvi:.2f})", fontweight="bold")
axes[0].set_xlabel("Mean Ward NDVI (250m)")
axes[0].set_ylabel("Summer Mean Daytime LST (°C)")
axes[0].grid(True, linestyle="--", alpha=0.5)

# NDBI vs Day LST
sns.regplot(data=sample_df, x="Mean_NDBI", y="Day_LST_C", ax=axes[1],
            scatter_kws={"alpha": 0.25, "color": "#e7298a", "s": 20},
            line_kws={"color": "#990000", "linewidth": 2.5})
slope_ndbi, _, r_ndbi, p_ndbi, _ = stats.linregress(df_master.dropna(subset=["Day_LST_C", "Mean_NDBI"])["Mean_NDBI"], df_master.dropna(subset=["Day_LST_C", "Mean_NDBI"])["Day_LST_C"])
axes[1].set_title(f"Built-Up Heating: NDBI vs Daytime LST\nSlope = +{slope_ndbi:.2f}°C per unit NDBI (r = {r_ndbi:.2f})", fontweight="bold")
axes[1].set_xlabel("Mean Ward NDBI (Built-Up Index)")
axes[1].set_ylabel("Summer Mean Daytime LST (°C)")
axes[1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
fig3_path = os.path.join(FIGURES_DIR, "fig3_vegetation_builtup_vs_lst.png")
plt.savefig(fig3_path, dpi=200)
plt.close()
print(f"Saved: {fig3_path}")

# Figure 4: 240m Land Transition Boxplots (Delta LST, Delta NDVI, Delta NDBI)
fig, axes = plt.subplots(1, 3, figsize=(16, 6))

order = [
    "Newly Built-Up (Green -> Concrete)",
    "Urban Densification",
    "Persistent Urban / Bare",
    "Persistent Green / Park",
    "Greening / Recovery",
    "Waterbody"
]
palette = ["#e41a1c", "#ff7f00", "#984ea3", "#4daf4a", "#377eb8", "#a65628"]

# Delta LST
sns.boxplot(data=df_grid, y="Land_Transition", x="Delta_LST_C", order=order, palette=palette, ax=axes[0], showmeans=True, meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black"})
axes[0].set_title("Thermal Shift (ΔLST 2002-2025)", fontweight="bold")
axes[0].set_xlabel("Δ LST (°C)")
axes[0].set_ylabel("Land Transition Category")
axes[0].grid(True, linestyle="--", alpha=0.5)

# Delta NDVI
sns.boxplot(data=df_grid, y="Land_Transition", x="Delta_NDVI", order=order, palette=palette, ax=axes[1], showmeans=True, meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black"})
axes[1].set_title("Vegetation Shift (ΔNDVI)", fontweight="bold")
axes[1].set_xlabel("Δ NDVI")
axes[1].set_ylabel("")
axes[1].set_yticklabels([])
axes[1].grid(True, linestyle="--", alpha=0.5)

# Delta NDBI
sns.boxplot(data=df_grid, y="Land_Transition", x="Delta_NDBI", order=order, palette=palette, ax=axes[2], showmeans=True, meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black"})
axes[2].set_title("Built-Up Shift (ΔNDBI)", fontweight="bold")
axes[2].set_xlabel("Δ NDBI")
axes[2].set_ylabel("")
axes[2].set_yticklabels([])
axes[2].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
fig4_path = os.path.join(FIGURES_DIR, "fig4_land_transition_distributions_240m.png")
plt.savefig(fig4_path, dpi=200)
plt.close()
print(f"Saved: {fig4_path}")

# Figure 5: 30m Hotspots: Tech Hubs vs Cubbon Park Benchmark
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

zone_display_names = {
    "Bellandur_ORR_Ecospace": "Bellandur / ORR",
    "Whitefield_ITPL": "Whitefield / ITPL",
    "Manyata_Tech_Park": "Manyata Tech Park",
    "Electronic_City_Ph1": "Electronic City Ph1",
    "Cubbon_Park_Benchmark": "Cubbon Park (Benchmark)"
}
df_hotspots["Zone_Clean"] = df_hotspots["Zone"].map(zone_display_names)
zone_order = ["Cubbon Park (Benchmark)", "Electronic City Ph1", "Manyata Tech Park", "Whitefield / ITPL", "Bellandur / ORR"]
colors_zone = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#9467bd"]

# 5a. LST Trajectory across 2002, 2015, 2025
hotspot_means = df_hotspots.groupby("Zone_Clean")[["LST_2002_C", "LST_2015_C", "LST_2025_C"]].mean().loc[zone_order]
years_x = [2002, 2015, 2025]
for idx, (zname, row) in enumerate(hotspot_means.iterrows()):
    axes[0].plot(years_x, [row["LST_2002_C"], row["LST_2015_C"], row["LST_2025_C"]],
                 marker="o", linewidth=2.5, label=zname, color=colors_zone[idx])
axes[0].set_title("High-Resolution 30m LST Trajectory (2002 vs 2015 vs 2025)", fontweight="bold")
axes[0].set_xlabel("Year")
axes[0].set_ylabel("April Surface Temperature (°C)")
axes[0].set_xticks([2002, 2015, 2025])
axes[0].legend(loc="upper left", frameon=True)
axes[0].grid(True, linestyle="--", alpha=0.5)

# 5b. Delta LST Distribution (2002 -> 2025)
sns.violinplot(data=df_hotspots, x="Zone_Clean", y="Delta_LST_C", order=zone_order, palette=colors_zone, ax=axes[1], inner="quartile")
axes[1].set_title("Distribution of Net 23-Year Warming (ΔLST 2002-2025)", fontweight="bold")
axes[1].set_xlabel("Case-Study Zone")
axes[1].set_ylabel("Δ LST (°C)")
axes[1].axhline(0, color="gray", linestyle="--", alpha=0.6)
axes[1].tick_params(axis="x", rotation=25)
axes[1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
fig5_path = os.path.join(FIGURES_DIR, "fig5_hotspots_30m_comparison.png")
plt.savefig(fig5_path, dpi=200)
plt.close()
print(f"Saved: {fig5_path}")

# Figure 6: Ward Rankings: Top 10 Hottest Wards vs Top 10 Coolest Wards & Top Warming Wards
fig, axes = plt.subplots(1, 2, figsize=(15, 7))

# 6a. 25-yr Mean Day LST Extremes
top_bottom_lst = pd.concat([cool_day_lst.sort_values("Day_LST_C"), top_day_lst.sort_values("Day_LST_C")])
colors_bar = ["#2b83ba"] * 10 + ["#d7191c"] * 10
axes[0].barh(top_bottom_lst["KGISWardName"], top_bottom_lst["Day_LST_C"], color=colors_bar, edgecolor="none", alpha=0.85)
axes[0].axvline(df_master["Day_LST_C"].mean(), color="black", linestyle="--", label=f"City Mean ({df_master['Day_LST_C'].mean():.1f}°C)")
axes[0].set_title("Ward Extremes: 10 Coolest vs 10 Hottest Wards (2001-2025)", fontweight="bold")
axes[0].set_xlabel("25-Year Summer Mean Daytime LST (°C)")
axes[0].legend(loc="lower right")
axes[0].grid(True, linestyle="--", alpha=0.5)

# 6b. Top 10 Warming Wards (Decadal Change)
top_warming_sorted = top_warming.sort_values("Delta_Day_LST_C")
axes[1].barh(top_warming_sorted["KGISWardName"], top_warming_sorted["Delta_Day_LST_C"], color="#e6550d", edgecolor="none", alpha=0.85)
axes[1].set_title("Top 10 Fastest Warming Wards (2001-05 to 2021-25 ΔLST)", fontweight="bold")
axes[1].set_xlabel("Net Warming (°C)")
axes[1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
fig6_path = os.path.join(FIGURES_DIR, "fig6_ward_rankings_extremes.png")
plt.savefig(fig6_path, dpi=200)
plt.close()
print(f"Saved: {fig6_path}")

# Figure 7: Spatial Scatter Map of 240m Blocks (Delta LST and Land Transitions)
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# 7a. Delta LST spatial distribution
sc1 = axes[0].scatter(df_grid["Lon"], df_grid["Lat"], c=df_grid["Delta_LST_C"], cmap="coolwarm", s=3, alpha=0.8, vmin=-2, vmax=8)
cbar1 = plt.colorbar(sc1, ax=axes[0], fraction=0.046, pad=0.04)
cbar1.set_label("Δ LST 2002-2025 (°C)")
axes[0].set_title("Spatial Pattern of Thermal Shift (240m Resolution)", fontweight="bold")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].set_aspect("equal")

# 7b. Land Transition spatial distribution
cat_colors = {
    "Newly Built-Up (Green -> Concrete)": "#e41a1c",
    "Urban Densification": "#ff7f00",
    "Persistent Urban / Bare": "#984ea3",
    "Persistent Green / Park": "#4daf4a",
    "Greening / Recovery": "#377eb8",
    "Waterbody": "#3182bd"
}
for cat, color in cat_colors.items():
    sub = df_grid[df_grid["Land_Transition"] == cat]
    axes[1].scatter(sub["Lon"], sub["Lat"], c=color, s=2.5, alpha=0.7, label=cat)
axes[1].set_title("Spatial Pattern of Urban & Environmental Transitions", fontweight="bold")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")
axes[1].set_aspect("equal")
axes[1].legend(markerscale=5, loc="lower left", frameon=True, fontsize=9)

plt.tight_layout()
fig7_path = os.path.join(FIGURES_DIR, "fig7_spatial_patterns_240m.png")
plt.savefig(fig7_path, dpi=200)
plt.close()
print(f"Saved: {fig7_path}")

# Save all summary tables to JSON for precise reporting
eda_export = {
    "dataset_overview": {
        "master_rows": n_rows,
        "master_cols": n_cols,
        "wards_count": n_wards,
        "year_range": [int(min_year), int(max_year)],
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "hotspots_rows": hot_rows,
        "bbmp_wards_count": len(gdf_wards),
        "total_bbmp_area_sqkm": float(total_bbmp_area),
        "lakes_count": len(gdf_lakes),
        "named_lakes_count": len(named_lakes),
        "total_lake_area_ha": float(gdf_lakes["area_ha"].sum())
    },
    "master_numerical_summary": master_desc.to_dict(),
    "temporal_trends": trend_stats,
    "decadal_shift": decadal_summary.to_dict(),
    "top_hottest_wards": top_day_lst.to_dict(orient="records"),
    "top_coolest_wards": cool_day_lst.to_dict(orient="records"),
    "top_warming_wards": top_warming.to_dict(orient="records"),
    "top_veg_loss_wards": top_veg_loss.to_dict(orient="records"),
    "top_built_gain_wards": top_built_gain.to_dict(orient="records"),
    "min_cooling_drop_wards": min_cooling_drop.to_dict(orient="records"),
    "pearson_correlations": corr_pearson.to_dict(),
    "spearman_correlations": corr_spearman.to_dict(),
    "grid_land_transitions": trans_summary.to_dict(),
    "grid_transition_stats": {str(k): {str(col): float(val) for col, val in v.items()} for k, v in trans_stats.to_dict().items()},
    "hotspots_zonal_means": hotspot_stats.to_dict(),
    "thermal_penalties": thermal_penalty.to_dict(),
    "geotiff_stats": tif_stats
}

with open(os.path.join(OUTPUT_DIR, "eda_summary_metrics.json"), "w") as f:
    json.dump(eda_export, f, indent=2)

print("\n" + "=" * 80)
print(f"EDA COMPLETED SUCCESSFULLY! All figures saved in {FIGURES_DIR}")
print(f"Metrics exported to {os.path.join(OUTPUT_DIR, 'eda_summary_metrics.json')}")
print("=" * 80)
