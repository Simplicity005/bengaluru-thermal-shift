import json
import os
import requests

os.makedirs("datasets", exist_ok=True)

# 1. Download BBMP Ward Boundaries from DataMeet
bbmp_url = "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP.geojson"
print("Downloading BBMP Ward Boundaries...")
r = requests.get(bbmp_url, timeout=30)
r.raise_for_status()
with open("datasets/BBMP_Wards.geojson", "wb") as f:
    f.write(r.content)

bbmp = r.json()
print(f"Saved datasets/BBMP_Wards.geojson ({len(bbmp['features'])} wards)")
print("Sample ward properties:", bbmp["features"][0]["properties"])

# Compute bounding box [W, S, E, N]
lons, lats = [], []
def collect_coords(coords):
    if isinstance(coords[0], (int, float)):
        lons.append(coords[0])
        lats.append(coords[1])
    else:
        for c in coords:
            collect_coords(c)

for feat in bbmp["features"]:
    collect_coords(feat["geometry"]["coordinates"])

bbox = [min(lons), min(lats), max(lons), max(lats)]
print("BBMP bbox [W, S, E, N]:", [round(x, 4) for x in bbox])

# 2. Download Bengaluru Lakes & Water Bodies from OpenStreetMap Overpass API
print("\nDownloading Bengaluru Lakes & Water Bodies from OpenStreetMap...")
overpass_query = f"""
[out:json][timeout:60];
(
  way["natural"="water"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
  relation["natural"="water"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
);
out body geom;
"""
r_osm = requests.post(
    "https://overpass-api.de/api/interpreter",
    data={"data": overpass_query},
    headers={"User-Agent": "BengaluruUHIProject/1.0 (DataViz)", "Accept": "application/json"},
    timeout=90,
)
print("Overpass status:", r_osm.status_code)
if r_osm.status_code == 200:
    osm = r_osm.json()
    features = []
    for el in osm.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "way" and "geometry" in el:
            coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "osm_id": el["id"],
                        "name": tags.get("name", "Unnamed Waterbody"),
                        "water_type": tags.get("water", "water"),
                    },
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                })
        elif el["type"] == "relation" and "members" in el:
            outers = []
            for m in el["members"]:
                if m.get("role") == "outer" and "geometry" in m:
                    c = [[p["lon"], p["lat"]] for p in m["geometry"]]
                    if len(c) >= 4 and c[0] == c[-1]:
                        outers.append([c])
            if outers:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "osm_id": el["id"],
                        "name": tags.get("name", "Unnamed Waterbody"),
                        "water_type": tags.get("water", "water"),
                    },
                    "geometry": {"type": "MultiPolygon", "coordinates": outers},
                })
    geojson = {"type": "FeatureCollection", "features": features}
    with open("datasets/Bengaluru_Lakes.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)
    named = [f["properties"]["name"] for f in features if f["properties"]["name"] != "Unnamed Waterbody"]
    print(f"Saved datasets/Bengaluru_Lakes.geojson ({len(features)} waterbodies, {len(named)} named)")
    print("Sample named lakes:", named[:10])

# 3. Check Microsoft Planetary Computer STAC for NASA MODIS MOD11A2 & MOD13Q1
print("\nChecking Microsoft Planetary Computer STAC for NASA MODIS...")
for col in ["modis-11A2-061", "modis-13Q1-061"]:
    r_pc = requests.post(
        "https://planetarycomputer.microsoft.com/api/stac/v1/search",
        json={"collections": [col], "bbox": bbox, "datetime": "2024-03-01/2024-05-31", "limit": 3},
        timeout=30,
    )
    print(f"  {col}: status={r_pc.status_code}")
    if r_pc.status_code == 200:
        feats = r_pc.json().get("features", [])
        print(f"    items={len(feats)}, sample assets={list(feats[0]['assets'].keys()) if feats else []}")
