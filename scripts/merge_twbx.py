import zipfile
import xml.etree.ElementTree as ET

PART1 = "Part1_Concrete_vs_Canopy.twbx"
PART2 = "Part2_Nocturnal_UHI.twbx"
OUTPUT = "Bengaluru_Thermal_Shift_Final.twbx"
OUTPUT_TWB = "Bengaluru_Thermal_Shift_Final.twb"

# Preserve Tableau's user: XML namespace prefix
ET.register_namespace("user", "http://www.tableausoftware.com/xml/user")


def read_twbx(path):
    with zipfile.ZipFile(path, "r") as z:
        twb_name = next(n for n in z.namelist() if n.endswith(".twb"))
        twb_bytes = z.read(twb_name)
        other_files = {n: z.read(n) for n in z.namelist() if n != twb_name}
    return ET.fromstring(twb_bytes), other_files


root1, files1 = read_twbx(PART1)
root2, files2 = read_twbx(PART2)

# Remove repository-location so it behaves as a fresh merged workbook
repo_loc = root1.find("repository-location")
if repo_loc is not None:
    root1.remove(repo_loc)

# 1. Merge document-format-change-manifest (deduplicate by tag)
m1 = root1.find("document-format-change-manifest")
m2 = root2.find("document-format-change-manifest")
if m1 is not None and m2 is not None:
    existing_tags = {c.tag for c in m1}
    for c in m2:
        if c.tag not in existing_tags:
            m1.append(c)
            existing_tags.add(c.tag)

# 2. Merge datasources
ds1 = root1.find("datasources")
ds2 = root2.find("datasources")
if ds1 is not None and ds2 is not None:
    existing_ds = {d.get("name") for d in ds1}
    for d in ds2:
        if d.get("name") not in existing_ds:
            ds1.append(d)

# 3. Merge mapsources (deduplicate by name)
ms1 = root1.find("mapsources")
ms2 = root2.find("mapsources")
if ms1 is not None and ms2 is not None:
    existing_ms = {m.get("name") for m in ms1}
    for m in ms2:
        if m.get("name") not in existing_ms:
            ms1.append(m)

# 4. Merge actions (ensure unique caption)
ac1 = root1.find("actions")
ac2 = root2.find("actions")
if ac1 is not None and ac2 is not None:
    existing_captions = {a.get("caption") for a in ac1}
    for a in ac2:
        if a.get("caption") in existing_captions:
            a.set("caption", "Filter 2 (generated)")
        ac1.append(a)

# 5. Merge worksheets
ws1 = root1.find("worksheets")
ws2 = root2.find("worksheets")
if ws1 is not None and ws2 is not None:
    for w in ws2:
        ws1.append(w)

# 6. Merge dashboards
db1 = root1.find("dashboards")
db2 = root2.find("dashboards")
if db1 is not None and db2 is not None:
    for d in db2:
        db1.append(d)

# 7. Merge windows (keep only Dashboard 1 maximized)
win1 = root1.find("windows")
win2 = root2.find("windows")
if win1 is not None and win2 is not None:
    for w in win1:
        if w.get("name") == "Dashboard 1 - Concrete vs Canopy":
            w.set("maximized", "true")
        elif "maximized" in w.attrib:
            del w.attrib["maximized"]
    for w in win2:
        if "maximized" in w.attrib:
            del w.attrib["maximized"]
        win1.append(w)

# 8. Merge thumbnails
th1 = root1.find("thumbnails")
th2 = root2.find("thumbnails")
if th1 is not None and th2 is not None:
    for t in th2:
        th1.append(t)

# Serialize merged XML
xml_bytes = b"<?xml version='1.0' encoding='utf-8' ?>\n\n" + ET.tostring(root1, encoding="utf-8")

# Write merged .twbx
with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr(OUTPUT_TWB, xml_bytes)
    all_files = {**files1, **files2}
    for fname, content in all_files.items():
        zout.writestr(fname, content)

print(f"Created {OUTPUT} successfully!")
print("  Datasources:", len(root1.findall("./datasources/datasource")))
print("  Worksheets:", [w.get("name") for w in root1.findall("./worksheets/worksheet")])
print("  Dashboards:", [d.get("name") for d in root1.findall("./dashboards/dashboard")])
print("  Data extracts bundled:", list(all_files.keys()))
