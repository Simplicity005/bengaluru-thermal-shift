# Bengaluru Urban Heat Island (UHI) — Thermal Shift Data Visualization

> **The "Garden City" to "Silicon Valley" Thermal Shift:** Visualizing how rapid urbanization and loss of green cover drive localized daytime and nighttime heat islands across Bengaluru (2001–2025).

## Datasets (`datasets/`)

| File | Resolution / Scope | Source | Description |
|---|---|---|---|
| `Bengaluru_UHI_Master_2001_2025.csv` | 243 BBMP wards × 25 years (2001–2025) | NASA MODIS/Terra (`MOD11A2` 1km LST + `MOD13Q1` 250m NDVI/EVI/NDBI) | Summer (Mar–May) Daytime & Nighttime LST (°C), Cooling Drop, NDVI, EVI, NDBI, and Day/Night UHI Anomalies. |
| `Bengaluru_BlockGrid_240m_2002_2025.csv` | 240m × 240m blocks (21,374 blocks) | USGS/NASA Landsat 7 & 8 Collection 2 L2 (April 2002, 2015, 2025) | Fine block-level LST, NDVI, NDBI, normalized UHI anomaly (`Delta_UHI_C`), and `Land_Transition` classification. |
| `Bengaluru_Hotspots_30m_2002_2025.csv` | Pure 30m × 30m pixels (21,861 pixels) | USGS/NASA Landsat 7 & 8 Collection 2 L2 | Unaggregated 30m pixels across 5 case-study zones: Bellandur/ORR Ecospace, Whitefield/ITPL, Manyata Tech Park, Electronic City Ph1, and Cubbon Park. |
| `landsat_30m/Bengaluru_30m_*.tif` | 30m × 30m GeoTIFFs (1.37M pixels each) | USGS/NASA Landsat 7 & 8 Collection 2 L2 | Aligned 3-band GeoTIFFs (`LST_C`, `NDVI`, `NDBI`) for 2002, 2015, 2025, plus `Change_2002_2025`. |
| `BBMP_Wards.geojson` | 243 BBMP wards | DataMeet `Municipal_Spatial_Data` | Municipal ward boundary polygons (`KGISWardNo`, `KGISWardName`). |
| `Bengaluru_Lakes.geojson` | 1,981 waterbodies (285 named lakes) | OpenStreetMap (Overpass API) | Waterbody polygons for thermal cooling overlays. |

## Reproduction Scripts (`scripts/`)
- `scripts/download_spatial_data.py` — Downloads `BBMP_Wards.geojson` and `Bengaluru_Lakes.geojson`.
- `scripts/download_modis_uhi.py` — Extracts 2001–2025 NASA MODIS/Terra Day/Night LST and NDVI/EVI/NDBI via Microsoft Planetary Computer STAC.
- `scripts/download_landsat_30m.py` — Extracts 30m Landsat C2 L2 April scenes (2002, 2015, 2025) and generates aligned GeoTIFFs, 240m block grid CSV, and 30m hotspot CSV.
