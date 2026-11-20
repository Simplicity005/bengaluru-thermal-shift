import os
import json
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import from_bounds, transform as window_transform
from pyproj import Transformer
import requests

os.makedirs("datasets/landsat_30m", exist_ok=True)

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SIGN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"

# Bengaluru bounding box (covers all 243 BBMP wards)
BBOX = [77.4599, 12.8335, 77.7844, 13.1426]  # [W, S, E, N]

# Exact low-cloud April scenes across 23 years (same week of April, single Path 144 / Row 51)
TARGET_SCENES = {
    2002: ("LE07_L2SP_144051_20020407_02_T1", "lwir"),
    2015: ("LC08_L2SP_144051_20150419_02_T1", "lwir11"),
    2025: ("LC08_L2SP_144051_20250414_02_T1", "lwir11"),
}

# 5 iconic 2km x 2km case-study zones for pure unaggregated 30m pixel CSV
HOTSPOT_ZONES = {
    "Bellandur_ORR_Ecospace": (77.6780, 12.9260),
    "Whitefield_ITPL":        (77.7370, 12.9850),
    "Manyata_Tech_Park":      (77.6210, 13.0450),
    "Electronic_City_Ph1":    (77.6650, 12.8450),
    "Cubbon_Park_Benchmark":  (77.5929, 12.9763),
}

_session = requests.Session()
_sas_cache = {}


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


def fetch_scene_item(scene_id: str):
    r = _session.get(f"https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/{scene_id}", timeout=30)
    r.raise_for_status()
    return r.json()


def read_and_reproject_band(href: str, dst_crs, dst_transform, dst_shape, resampling=Resampling.bilinear):
    signed = sign_href(href)
    with rasterio.open(signed) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xs, ys = tf.transform(
            [BBOX[0] - 0.01, BBOX[2] + 0.01, BBOX[0] - 0.01, BBOX[2] + 0.01],
            [BBOX[1] - 0.01, BBOX[1] - 0.01, BBOX[3] + 0.01, BBOX[3] + 0.01],
        )
        win = from_bounds(min(xs), min(ys), max(xs), max(ys), src.transform).round_offsets().round_lengths()
        win_tf = window_transform(win, src.transform)
        src_arr = src.read(1, window=win)

        dst_arr = np.zeros(dst_shape, dtype=src_arr.dtype)
        reproject(
            source=src_arr,
            destination=dst_arr,
            src_transform=win_tf,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=resampling,
        )
        return dst_arr


def main():
    # Define a single common EPSG:4326 ~30m grid (0.00027 deg ≈ 30m) so all 3 years align pixel-for-pixel!
    res = 0.00027
    width = int(round((BBOX[2] - BBOX[0]) / res))
    height = int(round((BBOX[3] - BBOX[1]) / res))
    dst_crs = "EPSG:4326"
    dst_transform = rasterio.transform.from_origin(BBOX[0], BBOX[3], res, res)
    dst_shape = (height, width)
    print(f"Common 30m WGS84 grid: {width} x {height} pixels ({width * height:,} total pixels)")

    results = {}
    for year, (scene_id, thermal_band) in TARGET_SCENES.items():
        print(f"\nProcessing {year} ({scene_id})...")
        item = fetch_scene_item(scene_id)
        assets = item["assets"]

        red_raw = read_and_reproject_band(assets["red"]["href"], dst_crs, dst_transform, dst_shape).astype(np.float32)
        nir_raw = read_and_reproject_band(assets["nir08"]["href"], dst_crs, dst_transform, dst_shape).astype(np.float32)
        swir_raw = read_and_reproject_band(assets["swir16"]["href"], dst_crs, dst_transform, dst_shape).astype(np.float32)
        th_raw = read_and_reproject_band(assets[thermal_band]["href"], dst_crs, dst_transform, dst_shape).astype(np.float32)
        qa = read_and_reproject_band(assets["qa_pixel"]["href"], dst_crs, dst_transform, dst_shape, resampling=Resampling.nearest)

        # Cloud (bit 3) and Cloud Shadow (bit 4) mask
        cloud_mask = ((qa & (1 << 3)) != 0) | ((qa & (1 << 4)) != 0) | (qa == 1)

        # Scale Surface Reflectance (USGS Collection 2 L2)
        red = np.where((red_raw > 0) & ~cloud_mask, red_raw * 0.0000275 - 0.2, np.nan)
        nir = np.where((nir_raw > 0) & ~cloud_mask, nir_raw * 0.0000275 - 0.2, np.nan)
        swir = np.where((swir_raw > 0) & ~cloud_mask, swir_raw * 0.0000275 - 0.2, np.nan)

        # Scale Surface Temperature to Celsius (USGS Collection 2 L2 ST)
        lst_c = np.where((th_raw > 0) & ~cloud_mask, th_raw * 0.00341802 + 149.0 - 273.15, np.nan)
        # Filter unphysical outliers
        lst_c = np.where((lst_c > 15.0) & (lst_c < 65.0), lst_c, np.nan)

        # Indices
        ndvi = np.where((nir + red) != 0, (nir - red) / (nir + red), np.nan)
        ndbi = np.where((swir + nir) != 0, (swir - nir) / (swir + nir), np.nan)
        ndvi = np.clip(ndvi, -1.0, 1.0)
        ndbi = np.clip(ndbi, -1.0, 1.0)

        results[year] = {"lst": lst_c, "ndvi": ndvi, "ndbi": ndbi}
        print(
            f"  {year} valid={np.isfinite(lst_c).mean()*100:.1f}% | "
            f"LST={np.nanmean(lst_c):.2f}°C (min={np.nanmin(lst_c):.1f}, max={np.nanmax(lst_c):.1f}) | "
            f"NDVI={np.nanmean(ndvi):.3f} | NDBI={np.nanmean(ndbi):.3f}"
        )

        # Save 3-band 30m GeoTIFF (Band 1: LST_C, Band 2: NDVI, Band 3: NDBI)
        out_tif = f"datasets/landsat_30m/Bengaluru_30m_{year}.tif"
        with rasterio.open(
            out_tif, "w", driver="GTiff", height=height, width=width, count=3,
            dtype="float32", crs=dst_crs, transform=dst_transform, compress="deflate", nodata=np.nan
        ) as dst:
            dst.write(lst_c.astype(np.float32), 1)
            dst.write(ndvi.astype(np.float32), 2)
            dst.write(ndbi.astype(np.float32), 3)
            dst.descriptions = ("LST_C", "NDVI", "NDBI")

    # Compute 2002 -> 2025 change GeoTIFF
    d_lst = results[2025]["lst"] - results[2002]["lst"]
    d_ndvi = results[2025]["ndvi"] - results[2002]["ndvi"]
    d_ndbi = results[2025]["ndbi"] - results[2002]["ndbi"]
    with rasterio.open(
        "datasets/landsat_30m/Bengaluru_30m_Change_2002_2025.tif", "w",
        driver="GTiff", height=height, width=width, count=3,
        dtype="float32", crs=dst_crs, transform=dst_transform, compress="deflate", nodata=np.nan
    ) as dst:
        dst.write(d_lst.astype(np.float32), 1)
        dst.write(d_ndvi.astype(np.float32), 2)
        dst.write(d_ndbi.astype(np.float32), 3)
        dst.descriptions = ("Delta_LST_C", "Delta_NDVI", "Delta_NDBI")
    print("\nSaved all 30m GeoTIFFs in datasets/landsat_30m/")

    # Build Tableau-ready 250m Block-Level Grid CSV (8x8 block average of 30m = ~240m blocks, ~18k rows)
    blk = 8
    bh, bw = height // blk, width // blk
    def downsample(arr):
        trimmed = arr[:bh * blk, :bw * blk]
        return np.nanmean(trimmed.reshape(bh, blk, bw, blk), axis=(1, 3))

    lst02_b = downsample(results[2002]["lst"])
    lst15_b = downsample(results[2015]["lst"])
    lst25_b = downsample(results[2025]["lst"])
    ndvi02_b = downsample(results[2002]["ndvi"])
    ndvi25_b = downsample(results[2025]["ndvi"])
    ndbi02_b = downsample(results[2002]["ndbi"])
    ndbi25_b = downsample(results[2025]["ndbi"])

    rows_grid = []
    for r in range(bh):
        lat = BBOX[3] - (r + 0.5) * blk * res
        for c in range(bw):
            if not (np.isfinite(lst02_b[r, c]) and np.isfinite(lst25_b[r, c])):
                continue
            lon = BBOX[0] + (c + 0.5) * blk * res
            dl = float(lst25_b[r, c] - lst02_b[r, c])
            dnv = float(ndvi25_b[r, c] - ndvi02_b[r, c])
            dnb = float(ndbi25_b[r, c] - ndbi02_b[r, c])
            nv02, nv25 = float(ndvi02_b[r, c]), float(ndvi25_b[r, c])
            nb25 = float(ndbi25_b[r, c])

            # Classify land transition
            if nv25 < 0.0 and nb25 < 0.0:
                trans = "Waterbody"
            elif nv02 >= 0.25 and nv25 < 0.20 and dnb > 0.03:
                trans = "Newly Built-Up (Green -> Concrete)"
            elif dnb > 0.04 and dnv < -0.05:
                trans = "Urban Densification"
            elif nv25 >= 0.30:
                trans = "Persistent Green / Park"
            elif dnv > 0.08:
                trans = "Greening / Recovery"
            else:
                trans = "Persistent Urban / Bare"

            rows_grid.append({
                "Grid_ID": f"B_{r}_{c}",
                "Lat": round(lat, 5),
                "Lon": round(lon, 5),
                "LST_2002_C": round(float(lst02_b[r, c]), 2),
                "LST_2015_C": round(float(lst15_b[r, c]), 2) if np.isfinite(lst15_b[r, c]) else np.nan,
                "LST_2025_C": round(float(lst25_b[r, c]), 2),
                "Delta_LST_C": round(dl, 2),
                "NDVI_2002": round(nv02, 3),
                "NDVI_2025": round(nv25, 3),
                "Delta_NDVI": round(dnv, 3),
                "NDBI_2002": round(float(ndbi02_b[r, c]), 3),
                "NDBI_2025": round(nb25, 3),
                "Delta_NDBI": round(dnb, 3),
                "Land_Transition": trans,
            })

    df_grid = pd.DataFrame(rows_grid)
    df_grid.to_csv("datasets/Bengaluru_BlockGrid_240m_2002_2025.csv", index=False)
    print(f"Saved datasets/Bengaluru_BlockGrid_240m_2002_2025.csv ({len(df_grid):,} blocks)")
    print("\nAvg Delta_LST_C by Land_Transition (2002 -> 2025):")
    print(df_grid.groupby("Land_Transition")[["LST_2002_C", "LST_2025_C", "Delta_LST_C", "Delta_NDVI", "Delta_NDBI"]].mean().round(2))

    # Build pure 100% unaggregated 30m pixel CSV for 5 iconic 2km x 2km case-study zones
    half_deg = 0.009  # ~1km radius -> 2km x 2km box (~66x66 = ~4,356 pixels per zone)
    rows_30m = []
    for zone_name, (clon, clat) in HOTSPOT_ZONES.items():
        c0 = max(0, int((clon - half_deg - BBOX[0]) / res))
        c1 = min(width, int((clon + half_deg - BBOX[0]) / res))
        r0 = max(0, int((BBOX[3] - (clat + half_deg)) / res))
        r1 = min(height, int((BBOX[3] - (clat - half_deg)) / res))
        for r in range(r0, r1):
            lat = BBOX[3] - (r + 0.5) * res
            for c in range(c0, c1):
                l02 = results[2002]["lst"][r, c]
                l25 = results[2025]["lst"][r, c]
                if not (np.isfinite(l02) and np.isfinite(l25)):
                    continue
                lon = BBOX[0] + (c + 0.5) * res
                l15 = results[2015]["lst"][r, c]
                rows_30m.append({
                    "Zone": zone_name,
                    "Lat": round(lat, 5),
                    "Lon": round(lon, 5),
                    "LST_2002_C": round(float(l02), 2),
                    "LST_2015_C": round(float(l15), 2) if np.isfinite(l15) else np.nan,
                    "LST_2025_C": round(float(l25), 2),
                    "Delta_LST_C": round(float(l25 - l02), 2),
                    "NDVI_2002": round(float(results[2002]["ndvi"][r, c]), 3),
                    "NDVI_2025": round(float(results[2025]["ndvi"][r, c]), 3),
                    "Delta_NDVI": round(float(results[2025]["ndvi"][r, c] - results[2002]["ndvi"][r, c]), 3),
                    "NDBI_2002": round(float(results[2002]["ndbi"][r, c]), 3),
                    "NDBI_2025": round(float(results[2025]["ndbi"][r, c]), 3),
                    "Delta_NDBI": round(float(results[2025]["ndbi"][r, c] - results[2002]["ndbi"][r, c]), 3),
                })

    df_30m = pd.DataFrame(rows_30m)
    df_30m.to_csv("datasets/Bengaluru_Hotspots_30m_2002_2025.csv", index=False)
    print(f"\nSaved datasets/Bengaluru_Hotspots_30m_2002_2025.csv ({len(df_30m):,} pure 30m pixels across 5 zones)")
    print(df_30m.groupby("Zone")[["LST_2002_C", "LST_2025_C", "Delta_LST_C", "Delta_NDVI"]].mean().round(2))


if __name__ == "__main__":
    main()
