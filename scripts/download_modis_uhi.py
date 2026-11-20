import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, transform as window_transform
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform
import requests

os.makedirs("datasets", exist_ok=True)

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SIGN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
YEARS = list(range(2001, 2026))
MAX_WORKERS = 12

# 1. Load BBMP Ward polygons
with open("datasets/BBMP_Wards.geojson", "r", encoding="utf-8") as f:
    bbmp = json.load(f)

wards = []
for feat in bbmp["features"]:
    props = feat["properties"]
    geom = shape(feat["geometry"])
    wards.append({
        "KGISWardNo": str(props.get("KGISWardNo", "")),
        "KGISWardName": props.get("KGISWardName", ""),
        "KGISWardID": props.get("KGISWardID", ""),
        "geom_wgs84": geom,
    })

# Bounding box with small padding
minx = min(w["geom_wgs84"].bounds[0] for w in wards) - 0.02
miny = min(w["geom_wgs84"].bounds[1] for w in wards) - 0.02
maxx = max(w["geom_wgs84"].bounds[2] for w in wards) + 0.02
maxy = max(w["geom_wgs84"].bounds[3] for w in wards) + 0.02
BBOX = [minx, miny, maxx, maxy]
print(f"Loaded {len(wards)} BBMP wards. BBox: {[round(x, 4) for x in BBOX]}")

# Cache SAS tokens per (scheme, netloc, container) so we only call sign once per container
_sas_cache = {}
_session = requests.Session()


def sign_href(href: str) -> str:
    parsed = urlparse(href)
    container = parsed.path.split("/")[1]
    key = (parsed.scheme, parsed.netloc, container)
    if key not in _sas_cache:
        r = _session.get(SIGN_URL, params={"href": href}, timeout=30)
        r.raise_for_status()
        signed = r.json()["href"]
        _sas_cache[key] = signed.split("?", 1)[1]
    sep = "&" if "?" in href else "?"
    return f"{href}{sep}{_sas_cache[key]}"


def search_stac_summer(collection: str, id_prefix: str):
    """Fetch all Terra (MOD*) summer (Mar-May) STAC items for 2001-2025."""
    items_by_year = {y: [] for y in YEARS}
    # Query in 5-year chunks to stay well under pagination limits
    for start_y in range(2001, 2026, 5):
        end_y = min(start_y + 4, 2025)
        payload = {
            "collections": [collection],
            "bbox": BBOX,
            "datetime": f"{start_y}-03-01T00:00:00Z/{end_y}-05-31T23:59:59Z",
            "limit": 500,
        }
        next_url = STAC_URL
        while next_url:
            if next_url == STAC_URL:
                r = _session.post(next_url, json=payload, timeout=45)
            else:
                r = _session.get(next_url, timeout=45)
            r.raise_for_status()
            data = r.json()
            for feat in data.get("features", []):
                fid = feat["id"]
                if not fid.startswith(id_prefix):
                    continue
                dt = feat["properties"].get("datetime") or feat["properties"].get("start_datetime", "")
                if not dt:
                    continue
                year = int(dt[:4])
                month = int(dt[5:7])
                if year in items_by_year and month in (3, 4, 5):
                    # Keep only tile h25v07 (covers Bengaluru completely)
                    if "h25v07" in fid:
                        items_by_year[year].append(feat)
            next_link = next((l["href"] for l in data.get("links", []) if l.get("rel") == "next"), None)
            next_url = next_link
    total = sum(len(v) for v in items_by_year.values())
    print(f"Found {total} {id_prefix} summer items across {sum(1 for v in items_by_year.values() if v)} years.")
    return items_by_year


def get_grid_and_masks(sample_href: str):
    """Open one sample COG to get CRS, window, transform, and precompute ward pixel masks."""
    signed = sign_href(sample_href)
    with rasterio.open(signed) as src:
        crs = src.crs
        tf = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        # Transform all 4 corners to handle sinusoidal curvature safely
        xs, ys = tf.transform([BBOX[0], BBOX[2], BBOX[0], BBOX[2]], [BBOX[1], BBOX[1], BBOX[3], BBOX[3]])
        win = from_bounds(min(xs), min(ys), max(xs), max(ys), src.transform).round_offsets().round_lengths()
        win_tf = window_transform(win, src.transform)
        out_shape = (int(win.height), int(win.width))

    proj_fn = lambda x, y, z=None: tf.transform(x, y)
    ward_masks = []
    for w in wards:
        geom_proj = shapely_transform(proj_fn, w["geom_wgs84"])
        # geometry_mask returns True where OUTSIDE, so invert=True gives True INSIDE
        mask = geometry_mask([geom_proj], out_shape=out_shape, transform=win_tf, invert=True, all_touched=True)
        if not mask.any():
            # Fallback to centroid pixel
            cx, cy = geom_proj.centroid.x, geom_proj.centroid.y
            row, col = ~win_tf * (cx, cy)
            r_idx = int(np.clip(round(row), 0, out_shape[0] - 1))
            c_idx = int(np.clip(round(col), 0, out_shape[1] - 1))
            mask[r_idx, c_idx] = True
        ward_masks.append(mask)

    return win, out_shape, ward_masks


def read_window(href: str, win):
    signed = sign_href(href)
    with rasterio.open(signed) as src:
        return src.read(1, window=win)


def process_mod11a2(items_by_year):
    """Extract annual summer mean Day_LST_C and Night_LST_C per ward."""
    sample_item = next(v[0] for v in items_by_year.values() if v)
    win, out_shape, ward_masks = get_grid_and_masks(sample_item["assets"]["LST_Day_1km"]["href"])
    print(f"MOD11A2 window shape: {out_shape}")

    def fetch_item(year, item):
        day_raw = read_window(item["assets"]["LST_Day_1km"]["href"], win).astype(np.float32)
        night_raw = read_window(item["assets"]["LST_Night_1km"]["href"], win).astype(np.float32)
        day_c = np.where(day_raw > 0, day_raw * 0.02 - 273.15, np.nan)
        night_c = np.where(night_raw > 0, night_raw * 0.02 - 273.15, np.nan)
        return year, day_c, night_c

    tasks = [(y, it) for y, items in items_by_year.items() for it in items]
    day_by_year = {y: [] for y in YEARS}
    night_by_year = {y: [] for y in YEARS}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(fetch_item, y, it) for y, it in tasks]
        done = 0
        for fut in as_completed(futs):
            y, d, n = fut.result()
            day_by_year[y].append(d)
            night_by_year[y].append(n)
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"  MOD11A2 progress: {done}/{len(tasks)} composites")

    results = {}
    for y in YEARS:
        if not day_by_year[y]:
            continue
        day_mean = np.nanmean(np.stack(day_by_year[y], axis=0), axis=0)
        night_mean = np.nanmean(np.stack(night_by_year[y], axis=0), axis=0)
        for i, w in enumerate(wards):
            m = ward_masks[i]
            d_vals = day_mean[m]
            n_vals = night_mean[m]
            d_val = float(np.nanmean(d_vals)) if np.isfinite(d_vals).any() else np.nan
            n_val = float(np.nanmean(n_vals)) if np.isfinite(n_vals).any() else np.nan
            results[(w["KGISWardNo"], y)] = (d_val, n_val)
    return results


def process_mod13q1(items_by_year):
    """Extract annual summer mean NDVI, EVI, and NDBI per ward at 250m."""
    sample_item = next(v[0] for v in items_by_year.values() if v)
    win, out_shape, ward_masks = get_grid_and_masks(sample_item["assets"]["250m_16_days_NDVI"]["href"])
    print(f"MOD13Q1 window shape: {out_shape}")

    def fetch_item(year, item):
        ndvi_raw = read_window(item["assets"]["250m_16_days_NDVI"]["href"], win).astype(np.float32)
        evi_raw = read_window(item["assets"]["250m_16_days_EVI"]["href"], win).astype(np.float32)
        mir_raw = read_window(item["assets"]["250m_16_days_MIR_reflectance"]["href"], win).astype(np.float32)
        nir_raw = read_window(item["assets"]["250m_16_days_NIR_reflectance"]["href"], win).astype(np.float32)

        ndvi = np.where(ndvi_raw != -3000, ndvi_raw / 10000.0, np.nan)
        evi = np.where(evi_raw != -3000, evi_raw / 10000.0, np.nan)
        valid_refl = (mir_raw > 0) & (nir_raw > 0)
        denom = np.where(valid_refl, mir_raw + nir_raw, np.nan)
        ndbi = np.where(valid_refl & (denom != 0), (mir_raw - nir_raw) / denom, np.nan)
        return year, ndvi, evi, ndbi

    tasks = [(y, it) for y, items in items_by_year.items() for it in items]
    ndvi_y = {y: [] for y in YEARS}
    evi_y = {y: [] for y in YEARS}
    ndbi_y = {y: [] for y in YEARS}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(fetch_item, y, it) for y, it in tasks]
        done = 0
        for fut in as_completed(futs):
            y, nv, ev, nb = fut.result()
            ndvi_y[y].append(nv)
            evi_y[y].append(ev)
            ndbi_y[y].append(nb)
            done += 1
            if done % 30 == 0 or done == len(tasks):
                print(f"  MOD13Q1 progress: {done}/{len(tasks)} composites")

    results = {}
    for y in YEARS:
        if not ndvi_y[y]:
            continue
        nv_mean = np.nanmean(np.stack(ndvi_y[y], axis=0), axis=0)
        ev_mean = np.nanmean(np.stack(evi_y[y], axis=0), axis=0)
        nb_mean = np.nanmean(np.stack(ndbi_y[y], axis=0), axis=0)
        for i, w in enumerate(wards):
            m = ward_masks[i]
            nv = float(np.nanmean(nv_mean[m])) if np.isfinite(nv_mean[m]).any() else np.nan
            ev = float(np.nanmean(ev_mean[m])) if np.isfinite(ev_mean[m]).any() else np.nan
            nb = float(np.nanmean(nb_mean[m])) if np.isfinite(nb_mean[m]).any() else np.nan
            results[(w["KGISWardNo"], y)] = (nv, ev, nb)
    return results


def main():
    print("\n1. Searching NASA MODIS/Terra MOD11A2 (LST Day & Night, 2001-2025)...")
    lst_items = search_stac_summer("modis-11A2-061", "MOD11A2")

    print("\n2. Searching NASA MODIS/Terra MOD13Q1 (250m NDVI, EVI, NDBI, 2001-2025)...")
    vi_items = search_stac_summer("modis-13Q1-061", "MOD13Q1")

    print("\n3. Extracting & aggregating MOD11A2 LST by BBMP ward...")
    lst_res = process_mod11a2(lst_items)

    print("\n4. Extracting & aggregating MOD13Q1 Vegetation/Built-up indices by BBMP ward...")
    vi_res = process_mod13q1(vi_items)

    rows = []
    available_years = sorted({y for (_, y) in lst_res.keys()})
    for y in available_years:
        for w in wards:
            wno = w["KGISWardNo"]
            day_c, night_c = lst_res.get((wno, y), (np.nan, np.nan))
            ndvi, evi, ndbi = vi_res.get((wno, y), (np.nan, np.nan, np.nan))
            rows.append({
                "KGISWardNo": wno,
                "KGISWardName": w["KGISWardName"],
                "KGISWardID": w["KGISWardID"],
                "Year": y,
                "Day_LST_C": round(day_c, 2) if np.isfinite(day_c) else np.nan,
                "Night_LST_C": round(night_c, 2) if np.isfinite(night_c) else np.nan,
                "Cooling_Drop_C": round(day_c - night_c, 2) if (np.isfinite(day_c) and np.isfinite(night_c)) else np.nan,
                "Mean_NDVI": round(ndvi, 4) if np.isfinite(ndvi) else np.nan,
                "Mean_EVI": round(evi, 4) if np.isfinite(evi) else np.nan,
                "Mean_NDBI": round(ndbi, 4) if np.isfinite(ndbi) else np.nan,
            })

    df = pd.DataFrame(rows)
    # Add annual city-wide UHI Anomaly columns (ward LST - annual city mean)
    df["Day_UHI_Anomaly_C"] = (df["Day_LST_C"] - df.groupby("Year")["Day_LST_C"].transform("mean")).round(2)
    df["Night_UHI_Anomaly_C"] = (df["Night_LST_C"] - df.groupby("Year")["Night_LST_C"].transform("mean")).round(2)

    out_path = "datasets/Bengaluru_UHI_Master_2001_2025.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved {out_path} with {len(df)} rows ({df['Year'].min()}-{df['Year'].max()}, {df['KGISWardNo'].nunique()} wards).")
    print("Missing values per column:\n", df.isna().sum())
    print("\nCity-wide summer trend (sample years):")
    summary = df.groupby("Year")[["Day_LST_C", "Night_LST_C", "Cooling_Drop_C", "Mean_NDVI", "Mean_NDBI"]].mean().round(2)
    print(summary.loc[summary.index.isin([2001, 2005, 2010, 2015, 2020, summary.index.max()])])


if __name__ == "__main__":
    main()
