# OSM (Overpass) -> river/road lines in DEM grid coordinates for battle lab.
# Fallback pattern adapted from the user's own OSMCityScout (MIT, (c) oosawak):
# try multiple public Overpass endpoints in order, sequentially.
import math, urllib.request, urllib.parse, json, os, time

SERVERS = [
  "https://overpass.private.coffee/api/interpreter",
  "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
  "https://overpass-api.de/api/interpreter",
]
Z = 14
OUT = os.path.join(os.path.dirname(__file__), "..", "data")
BATTLES = {
  "hitotoribashi": (37.49831, 140.38847),
  "suriagehara": (37.56214, 140.06633),
}
RADIUS = 2400

def global_px(lat, lon):
    n = 2**Z
    gx = (lon + 180) / 360 * n * 256
    lat_rad = math.radians(lat)
    gy = (1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n * 256
    return gx, gy

def crop_origin(lat, lon):
    gx, gy = global_px(lat, lon)
    cx, cy = int(gx), int(gy)
    tx, ty = cx // 256, cy // 256
    px, py = cx - (tx - 1) * 256, cy - (ty - 1) * 256
    left = max(0, min(768 - 512, px - 256)); top = max(0, min(768 - 512, py - 256))
    return (tx - 1) * 256 + left, (ty - 1) * 256 + top

def to_grid(lat, lon, origin):
    gx, gy = global_px(lat, lon)
    return [round((gx - origin[0]) / 512 * 127, 1), round((gy - origin[1]) / 512 * 127, 1)]

def fetch(query):
    data = urllib.parse.urlencode({"data": query}).encode()
    errs = []
    for url in SERVERS:
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "sengoku-battle-lab/0.1 (OSM fetch for prototype)"})
            with urllib.request.urlopen(req, timeout=45) as r:
                j = json.load(r)
                print("  OK via", url, "elements", len(j.get("elements", [])))
                return j.get("elements", [])
        except Exception as e:
            print("  fail", url, e); errs.append(str(e)); time.sleep(2)
    raise RuntimeError("all overpass servers failed: " + " / ".join(errs))

def simplify(pts, min_dist=1.6):
    if len(pts) <= 2: return pts
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.dist(p, out[-1]) >= min_dist: out.append(p)
    out.append(pts[-1])
    return out

def clip_ok(pts):
    return any(-5 <= x <= 132 and -5 <= y <= 132 for x, y in pts)

for bid, (lat, lon) in BATTLES.items():
    print(bid)
    q = f"""[out:json][timeout:40];(way["waterway"](around:{RADIUS},{lat},{lon});way["highway"](around:{RADIUS},{lat},{lon});way["natural"="water"](around:{RADIUS},{lat},{lon}););out geom;"""
    els = fetch(q)
    origin = crop_origin(lat, lon)
    waterways, highways, waters = [], [], []
    for e in els:
        geom = e.get("geometry") or []
        if len(geom) < 2: continue
        pts = simplify([to_grid(g["lat"], g["lon"], origin) for g in geom])
        if not clip_ok(pts): continue
        tags = e.get("tags", {})
        item = {"name": tags.get("name", ""), "pts": pts}
        if "waterway" in tags: item["kind"] = tags["waterway"]; waterways.append(item)
        elif "highway" in tags: item["kind"] = tags["highway"]; highways.append(item)
        elif tags.get("natural") == "water": waters.append(item)
    result = {"waterways": waterways, "highways": highways, "waters": waters,
              "source": "OpenStreetMap (ODbL), Overpass API, fetched 2026-11-01, radius 2400m"}
    with open(os.path.join(OUT, f"osm-{bid}.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"  waterways {len(waterways)} highways {len(highways)} waters {len(waters)}")
    print("  river names:", sorted({w['name'] for w in waterways if w['name']}))
