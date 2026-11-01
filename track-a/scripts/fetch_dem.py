# GSI DEM PNG tiles -> downsampled elevation grid JSON for battle lab
# Source: https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png (DEM10B)
# Decode: x=R*65536+G*256+B; x==2^23 invalid; x>2^23 -> x-2^24; h=x*0.01 m
import math, urllib.request, io, json, os
from PIL import Image

Z=14
OUT=os.path.join(os.path.dirname(__file__),"..","data")
BATTLES={
  "hitotoribashi": {"name":"人取橋", "lat":37.49831, "lon":140.38847},
  "suriagehara": {"name":"摺上原", "lat":37.56214, "lon":140.06633},
}
def tile_and_pixel(lat,lon,z):
    n=2**z
    gx=(lon+180)/360*n*256
    lat_rad=math.radians(lat)
    gy=(1-math.log(math.tan(lat_rad)+1/math.cos(lat_rad))/math.pi)/2*n*256
    return gx,gy

def fetch_tile(z,x,y):
    url=f"https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png"
    with urllib.request.urlopen(url, timeout=20) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")

for bid,b in BATTLES.items():
    gx,gy=tile_and_pixel(b["lat"],b["lon"],Z)
    cx,cy=int(gx),int(gy)
    tx,ty=cx//256,cy//256
    # stitch 3x3 tiles
    big=Image.new("RGB",(768,768))
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            im=fetch_tile(Z,tx+dx,ty+dy)
            big.paste(im,((dx+1)*256,(dy+1)*256))
    # center pixel in stitched image
    px,py=cx-(tx-1)*256, cy-(ty-1)*256
    # crop 512x512 around center
    left=max(0,min(768-512,px-256)); top=max(0,min(768-512,py-256))
    crop=big.crop((left,top,left+512,top+512))
    pxdata=crop.load()
    # downsample 512 -> 128 (4px block mean of valid)
    N=128; grid=[]
    hs_all=[]
    for j in range(N):
        row=[]
        for i in range(N):
            vals=[]
            for yy in range(j*4,(j+1)*4):
                for xx in range(i*4,(i+1)*4):
                    R,G,B=pxdata[xx,yy]
                    xv=R*65536+G*256+B
                    if xv==8388608: continue
                    if xv>8388608: xv-=16777216
                    vals.append(xv*0.01)
            h=sum(vals)/len(vals) if vals else 0
            row.append(round(h,1)); hs_all.append(h)
        grid.append(row)
    # center position in grid coords
    center_grid=[round((px-left)/512*(N-1),1), round((py-top)/512*(N-1),1)]
    meta={"id":bid,"name":b["name"],"lat":b["lat"],"lon":b["lon"],"zoom":Z,
          "grid":N,"min":round(min(hs_all),1),"max":round(max(hs_all),1),
          "center":center_grid,"source":"GSI DEM10B dem_png tiles, fetched 2026-11-01, 512px crop downsampled to 128x128"}
    with open(os.path.join(OUT,f"{bid}.json"),"w") as f:
        json.dump({"meta":meta,"elev":grid},f)
    print(bid, meta["min"], meta["max"], "center", center_grid)
