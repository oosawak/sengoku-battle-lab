import json, pathlib
base = pathlib.Path("workspace/sengoku-battle-lab/track-a")
hito = (base/"data/hitotoribashi.json").read_text()
suri = (base/"data/suriagehara.json").read_text()
MAJOR = {"motorway","motorway_link","trunk","primary","secondary","tertiary"}
def filtered_osm(bid):
    d = json.loads((base/f"data/osm-{bid}.json").read_text())
    hw = [h for h in d["highways"] if h["kind"] in MAJOR or h["name"]]
    seen = set(); out_hw = []
    for h in hw:
        key = (h["name"], tuple(map(tuple, h["pts"])))
        if key in seen: continue
        seen.add(key); out_hw.append({"name": h["name"], "pts": h["pts"]})
    return {"waterways": [{"name": w["name"], "pts": w["pts"]} for w in d["waterways"]],
            "highways": out_hw,
            "waters": [{"name": w["name"], "pts": w["pts"]} for w in d["waters"]]}
osm_hito = json.dumps(filtered_osm("hitotoribashi"), ensure_ascii=False)
osm_suri = json.dumps(filtered_osm("suriagehara"), ensure_ascii=False)
print("osm embed sizes:", len(osm_hito), len(osm_suri))

html = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>奥羽一生録・合戦実験 トラックA | 3D布陣図モック v0.3</title>
<script type="importmap">{"imports":{"three":"./vendor/three.module.js","three/addons/":"./vendor/"}}</script>
<style>
  :root{ --bg:#16140f; --panel:#221e16; --line:#4a4232; --ink:#ece2c8; --sub:#b8ab8a; --ally:#8fc1ff; --enemy:#ff9d8a; --accent:#d9a441; }
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Mincho ProN","Yu Mincho",serif;}
  header{padding:14px 16px 8px} h1{font-size:20px;margin:0 0 4px} .sub{color:var(--sub);font-size:12.5px;line-height:1.6}
  .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  .seg{display:flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
  .seg button{background:transparent;color:var(--sub);border:0;padding:8px 14px;font-size:14px;cursor:pointer;font-family:inherit}
  .seg button.on{background:var(--accent);color:#1a160d;font-weight:700}
  main{display:grid;grid-template-columns:1fr 340px;gap:12px;padding:10px 16px 20px}
  @media(max-width:860px){ main{grid-template-columns:1fr} }
  #stage{position:relative;background:#0d0c09;border:1px solid var(--line);border-radius:10px;min-height:420px;overflow:hidden}
  #view3d,#view2d{width:100%;height:520px;display:block}
  #view2d{display:none}
  #compass{position:absolute;top:10px;right:10px;width:52px;height:52px;border-radius:50%;background:rgba(20,18,13,.85);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;flex-direction:column;font-size:11px;color:var(--sub)}
  #needle{font-size:18px;line-height:1;color:var(--accent);display:block}
  #hint{position:absolute;right:10px;bottom:10px;background:rgba(20,18,13,.8);border:1px solid var(--line);border-radius:8px;padding:5px 9px;font-size:11.5px;color:var(--sub)}
  .badge{position:absolute;left:10px;bottom:10px;background:rgba(20,18,13,.85);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:12px;color:var(--sub)}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
  .panel h2{font-size:15px;margin:0 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}
  .panel h3{font-size:13px;margin:14px 0 6px;color:var(--accent)}
  select{width:100%;padding:8px;background:#171410;color:var(--ink);border:1px solid var(--line);border-radius:8px;font-family:inherit}
  .tactic{display:block;width:100%;text-align:left;background:#1b1811;border:1px solid var(--line);border-radius:8px;padding:10px;margin:0 0 8px;color:var(--ink);cursor:pointer;font-family:inherit}
  .tactic.on{border-color:var(--accent);background:#2a2113}
  .tactic .t{font-size:14px;display:block}
  .tactic .m{font-size:12px;color:var(--sub);display:block;margin-top:4px;line-height:1.5}
  .danger{font-weight:700} .d-low{color:#9fd48f}.d-mid{color:#e8cf7a}.d-high{color:#f0a35e}.d-ext{color:#ff7d6b}
  .stats{font-size:13px;line-height:1.9;color:var(--sub)} .stats b{color:var(--ink)}
  #resolve{width:100%;padding:12px;background:var(--accent);color:#1a160d;border:0;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit}
  #result{margin-top:12px;font-size:13.5px;line-height:1.8;background:#171410;border:1px solid var(--line);border-radius:8px;padding:10px;display:none;white-space:pre-wrap}
  input[type=range]{width:100%}
  .note{font-size:12px;color:var(--sub);line-height:1.7}
  label.lbl{font-size:12.5px;color:var(--sub);display:block;margin:8px 0 4px}
</style>
</head>
<body>
<header>
  <h1>合戦実験 トラックA — 3D地形の布陣図＋采配 v0.3</h1>
  <div class="sub">『奥羽一生録』本体とは独立した実験モックです。地形は国土地理院DEM10Bの実データ（中心約3.9km四方を128×128に縮小）。部隊配置は模式図で、史実の布陣再現ではありません。川・道はOpenStreetMapの実線です（2026-11-01に取得した分を同梱。川は全件、道は主要道と名前のある道のみ）。</div>
  <div class="row" style="margin-top:10px">
    <div class="seg" id="battleSeg">
      <button data-b="hitotoribashi" class="on">人取橋 1585</button>
      <button data-b="suriagehara">摺上原 1589</button>
    </div>
    <div class="seg" id="viewSeg">
      <button data-v="3d" class="on">3D線画</button>
      <button data-v="2d">2D等高線</button>
    </div>
  </div>
</header>
<main>
  <section id="stage">
    <div id="view3d"></div>
    <canvas id="view2d" width="900" height="620"></canvas>
    <div id="compass"><span id="needle">↑</span><span>北</span></div>
    <div id="hint">ドラッグ: 回転 / ピンチ・ホイール: 拡大（自動回転は触ると止まります）</div>
    <div class="badge" id="stageBadge"></div>
  </section>
  <aside class="panel">
    <h2 id="battleTitle"></h2>
    <div class="stats" id="battleInfo"></div>
    <div class="note" style="margin-top:8px">マーカー凡例（形=大将と兵種、試作割当）: <b style="color:var(--ink)">八角形</b> 大将 / <b style="color:var(--ink)">▲</b> 槍（敵の向きに尖る） / <b style="color:var(--ink)">◆</b> 騎馬 / <b style="color:var(--ink)">■</b> 鉄砲 / <b style="color:var(--ink)">半月</b> 弓。色は味方=青、敵=赤。殿・側撃などの役目は部隊名で示します。</div>
    <h3>視点（人物）</h3>
    <div class="seg" id="personSeg"></div>
    <div class="stats" id="personStats" style="margin-top:8px"></div>
    <label class="lbl">健康（決定003の状態語）</label>
    <select id="healthSel">
      <option value="good">健やか</option><option value="bad">不調</option><option value="critical">重篤</option>
    </select>
    <h3>采配を選ぶ</h3>
    <div id="tactics"></div>
    <label class="lbl">地形の縦誇張（3D）: <span id="exVal"></span></label>
    <input type="range" id="exSlider" min="1" max="10" step="0.5" value="6">
    <button id="resolve">この采配で合戦を解決する</button>
    <div id="result"></div>
    <p class="note" style="margin-top:12px">危険度は設計メモv0.1の試作式: 合戦基礎＋役目危険＋敵優勢 − 実効武勇×0.25 − 知略×0.15 ＋健康補正＋地形修正。討死は危険度50以上でのみ起こりえます。数値はすべて調整用の試作値です。</p>
  </aside>
</main>
<script>
const DEM = { hitotoribashi: __HITO__, suriagehara: __SURI__ };
const OSM_BAKED = { hitotoribashi: __OSM_HITO__, suriagehara: __OSM_SURI__ };
const BATTLES = {
  hitotoribashi: {
    title: "人取橋の戦い", date: "1585年11月17日", place: "本宮市・人取橋古戦場（37.49831, 140.38847）",
    info: "伊達 約7,000 vs 佐竹・蘆名連合 約30,000（伝承値）。問いは「勝つ」ではなく「軍を残して退けるか」。標高 202〜360m。",
    base: 35, enemyAdv: 20, exDefault: 6, contourStep: 20,
    river: [[0,66],[20,62],[42,65],[63,60],[84,63],[127,58]],
    lat:37.49831, lon:140.38847, riverLabel: "瀬戸川・人取橋（模式線）", northLabel: "北: 二本松方面", southLabel: "南: 本宮・連合軍の来た道",
    units: [
      {name:"伊達本隊・政宗", mark:"政", troop:"general", side:"ally", gx:64, gy:36},
      {name:"成実隊", mark:"実", troop:"kiba", side:"ally", gx:45, gy:50},
      {name:"鬼庭隊（殿）", mark:"鬼", troop:"yari", side:"ally", gx:59, gy:60},
      {name:"連合本隊・佐竹", mark:"佐", troop:"general", side:"enemy", gx:66, gy:99},
      {name:"蘆名隊", mark:"蘆", troop:"yari", side:"enemy", gx:37, gy:93},
      {name:"岩城隊", mark:"岩", troop:"yumi", side:"enemy", gx:93, gy:95},
    ],
    persons: {
      masamune: { name:"伊達政宗", troopKey:"general", troopLabel:"本隊（大将）", age:18, buyu:72, chiryaku:86, tactics:[
        {text:"成実に後を任せ、本隊を退く", role:"退却指揮", roleD:5, merit:3, src:"既存イベント", ok:"成実の奮戦で退き口が開いた。負けはしたが、軍と自分の命は残った。"},
        {text:"自ら先頭に残って押し返す", role:"先陣", roleD:25, merit:6, src:"既存イベント", ok:"味方は奮い立った。囲まれる危険と隣り合わせで退けた。"},
        {text:"橋のたもとを守り、退き口を確保する", role:"橋頭の防衛", roleD:20, merit:5, src:"試作追加", ok:"橋の出入り口を押さえ、本隊の退却を最後まで支えた。"},
      ]},
      shigezane: { name:"伊達成実", troopKey:"kiba", troopLabel:"騎馬", age:17, buyu:78, chiryaku:82, tactics:[
        {text:"殿を務め、政宗を先に退かせる", role:"殿（しんがり）", roleD:30, merit:8, src:"既存イベント", ok:"激しい攻撃を受けながらも退き口を守り抜いた。政宗から感状を与えられた。"},
        {text:"政宗と一緒に、一気に突き抜ける", role:"強行突破", roleD:22, merit:3, src:"既存イベント", ok:"勢いで一角は崩したが、本隊との間が開き、危うい退却になった。"},
        {text:"鬼庭隊と並んで二段の殿を組む", role:"殿・第二段", roleD:26, merit:6, src:"試作追加", ok:"二段構えの殿で追撃を食い止めた。史実ではこの役目で鬼庭良直が討死している。"},
      ]},
    }
  },
  suriagehara: {
    title: "摺上原の戦い", date: "1589年6月5日", place: "磐梯町・猪苗代町、磐梯山南麓（37.56214, 140.06633）",
    info: "伊達 vs 蘆名義広。標高550〜600mの火山扇状地（コトバンク）。標高 516〜877mと起伏が大きく、3Dが映える舞台。前日の偵察が鍵。",
    base: 35, enemyAdv: 10, exDefault: 3.5, contourStep: 25,
    river: [[0,96],[30,88],[58,90],[90,82],[127,86]],
    lat:37.56214, lon:140.06633, riverLabel: "日橋川方面（模式線）", northLabel: "北: 磐梯山", southLabel: "南: 猪苗代湖",
    units: [
      {name:"伊達本隊・政宗", mark:"政", troop:"general", side:"ally", gx:58, gy:72},
      {name:"成実隊（側撃）", mark:"実", troop:"kiba", side:"ally", gx:28, gy:54},
      {name:"片倉隊", mark:"片", troop:"teppo", side:"ally", gx:76, gy:70},
      {name:"蘆名本隊・義広", mark:"義", troop:"general", side:"enemy", gx:64, gy:34},
      {name:"金上隊", mark:"金", troop:"yari", side:"enemy", gx:46, gy:27},
      {name:"佐瀬隊", mark:"瀬", troop:"kiba", side:"enemy", gx:84, gy:30},
    ],
    persons: {
      masamune: { name:"伊達政宗", troopKey:"general", troopLabel:"本隊（大将）", age:22, buyu:72, chiryaku:86, tactics:[
        {text:"成実の側撃に賭け、一気に攻める", role:"側撃への全軍呼応", roleD:18, terra:-5, merit:8, src:"既存イベント", ok:"横からの一撃が蘆名の陣を崩した。会津への道が開けた。"},
        {text:"堅く構えて、相手が崩れるのを待つ", role:"本陣・堅守", roleD:5, merit:2, src:"既存イベント", ok:"大きな勝ちはなかったが、味方の損耗も少なかった。会津攻めは長引いた。"},
        {text:"正面から一気に押し切る", role:"正面決戦", roleD:22, merit:6, src:"試作追加", ok:"正面の押し合いは互角に近く、決め手は他隊の働きに委ねられた。"},
      ]},
      shigezane: { name:"伊達成実", troopKey:"kiba", troopLabel:"騎馬", age:21, buyu:78, chiryaku:82, tactics:[
        {text:"地形を使って回り込み、横から突く", role:"側撃", roleD:20, terra:-10, merit:8, src:"既存イベント", ok:"側面への一撃が蘆名軍を崩した。この合戦の勝敗を分けた働きになった。（前日に片倉景綱と偵察済み: 地形修正 −10）"},
        {text:"本隊と並んで正面から当たる", role:"正面", roleD:15, merit:3, src:"既存イベント", ok:"堅実な戦いになったが、決め手には欠けた。勝ちは他隊の働きに譲った。"},
        {text:"囮となって敵先鋒を引き込む", role:"囮・誘引", roleD:26, merit:6, src:"試作追加", ok:"敵先鋒を原の奥へ引き込み、本隊の挟撃が決まった。"},
      ]},
    }
  }
};
let curBattle="hitotoribashi", curPerson="masamune", curTactic=0, curView="3d";
const $=s=>document.querySelector(s);
function healthMods(){ const h=$("#healthSel").value; return h==="good"?{buyu:0,danger:0,label:"健やか"}:h==="bad"?{buyu:-8,danger:4,label:"不調"}:{buyu:-20,danger:10,label:"重篤"}; }
function troopAdj(t){ const P=BATTLES[curBattle].persons[curPerson]; if(P.troopKey!=="kiba") return 0;
  if(/側撃|突破|囮|強行/.test(t.role)) return -4; if(/堅守|本陣|橋頭/.test(t.role)) return 2; return 0; }
function dangerOf(t){ const B=BATTLES[curBattle], P=B.persons[curPerson], hm=healthMods();
  const eff=P.buyu+hm.buyu; return Math.max(2, Math.round(B.base + t.roleD + B.enemyAdv - eff*0.25 - P.chiryaku*0.15 + hm.danger + (t.terra||0) + troopAdj(t))); }
function band(d){ return d<30?["低","d-low"]:d<55?["中","d-mid"]:d<75?["高","d-high"]:["極高","d-ext"]; }
function renderPanel(){
  const B=BATTLES[curBattle];
  $("#battleTitle").textContent = B.title+"（"+B.date+"）";
  $("#battleInfo").innerHTML = B.place+"<br>"+B.info;
  updateBadge();
  const ps=$("#personSeg"); ps.innerHTML="";
  Object.entries(B.persons).forEach(([k,p])=>{ const b=document.createElement("button"); b.textContent=p.name; if(k===curPerson)b.className="on"; b.onclick=()=>{curPerson=k;curTactic=0;renderPanel();}; ps.appendChild(b); });
  const P=B.persons[curPerson];
  $("#personStats").innerHTML = "年齢 <b>"+P.age+"歳</b> / 武勇 <b>"+P.buyu+"</b> / 知略（采配） <b>"+P.chiryaku+"</b> / 兵種 <b>"+P.troopLabel+"</b>";
  const tw=$("#tactics"); tw.innerHTML="";
  P.tactics.forEach((t,i)=>{ const d=dangerOf(t), bd=band(d);
    const b=document.createElement("button"); b.className="tactic"+(i===curTactic?" on":"");
    const ta=troopAdj(t); const taTxt = ta!==0 ? ' / 兵種（騎馬）補正 '+(ta>0?'+':'−')+Math.abs(ta) : '';
    b.innerHTML = '<span class="t">'+t.text+'</span><span class="m">役目: '+t.role+'（'+t.src+'） / 手柄の期待: 評判+'+t.merit+taTxt+' / 危険度 <span class="danger '+bd[1]+'">'+d+"・"+bd[0]+'</span></span>';
    b.onclick=()=>{curTactic=i;renderPanel();}; tw.appendChild(b); });
  $("#exVal").textContent = "×"+$("#exSlider").value;
}
function resolveBattle(){
  const B=BATTLES[curBattle], P=B.persons[curPerson], t=P.tactics[curTactic], d=dangerOf(t);
  const deathP = d>=50 ? Math.min(35,(d-38)*0.35) : 0;
  const injuryP = 10 + d*0.35, captureP = d>45?8:3;
  const r = Math.random()*100; let out="";
  if(r < deathP){ out = "【討死】\n危険度 "+d+" の采配で、討死判定（"+deathP.toFixed(1)+"%）に入りました。\nこの人物の一生はここで終わります。列伝には合戦の経緯が残ります。"; }
  else if(r < deathP+injuryP){ out = "【負傷・生還】\n"+t.ok+"\nただし深い傷を負った。効果: 評判 +"+Math.max(1,t.merit-2)+" / 健康 −30（決定003の健康管理へ接続） / flag: battle-injured"; }
  else if(r < deathP+injuryP+captureP){ const branches=["身代金・人質交換で帰還（貫を支払い、数か月が経過）","捕えた側への仕官に応じる（一生の分岐: 所属が変わる）","幽閉で年月が過ぎる（敵将との関係イベントへ）"]; const br=branches[Math.floor(Math.random()*branches.length)];
    out = "【捕虜】\n敗北の中で捕らえられた。行き先は「"+br+"」。\n処刑はごく稀な分岐として別に置き、ここでは発生しませんでした（方針メモ004）。"; }
  else { out = "【生還・手柄】\n"+t.ok+"\n効果: 評判 +"+t.merit+" / flag: "+curBattle+"-"+curPerson+"-"+curTactic; }
  const el=$("#result"); el.style.display="block";
  el.textContent = out+"\n—\n判定内訳（試作値）: 危険度 "+d+" / 討死 "+deathP.toFixed(1)+"% / 負傷 "+injuryP.toFixed(1)+"% / 捕虜 "+captureP+"% / 乱数 "+r.toFixed(1);
}
/* ---------- 2D ---------- */
function draw2D(){
  const cv=$("#view2d"), ctx=cv.getContext("2d"), W=cv.width, H=cv.height, data=DEM[curBattle], N=data.meta.grid, ev=data.elev;
  ctx.fillStyle="#12100b"; ctx.fillRect(0,0,W,H);
  const px=W/N, py=H/N, min=data.meta.min, max=data.meta.max;
  for(let j=0;j<N;j++) for(let i=0;i<N;i++){ const t=(ev[j][i]-min)/(max-min); const r=Math.floor(28+t*90), g=Math.floor(34+t*70), b=Math.floor(20+t*34); ctx.fillStyle=`rgb(${r},${g},${b})`; ctx.fillRect(i*px,j*py,px+1,py+1); }
  ctx.strokeStyle="rgba(236,226,200,0.35)"; ctx.lineWidth=0.6;
  const step=BATTLES[curBattle].contourStep;
  for(let lv=Math.ceil(min/step)*step; lv<max; lv+=step){
    ctx.beginPath();
    for(let j=0;j<N-1;j++) for(let i=0;i<N-1;i++){
      const a=ev[j][i],b=ev[j][i+1],c=ev[j+1][i+1],d2=ev[j+1][i];
      const pts=[];
      const cross=(x1,y1,v1,x2,y2,v2)=>{ if((v1<lv&&v2>=lv)||(v2<lv&&v1>=lv)){ const t=(lv-v1)/(v2-v1); pts.push([ (x1+(x2-x1)*t)*px, (y1+(y2-y1)*t)*py ]); } };
      cross(i,j,a,i+1,j,b); cross(i+1,j,b,i+1,j+1,c); cross(i+1,j+1,c,i,j+1,d2); cross(i,j+1,d2,i,j,a);
      if(pts.length>=2){ ctx.moveTo(pts[0][0],pts[0][1]); ctx.lineTo(pts[1][0],pts[1][1]); if(pts.length>2){ ctx.moveTo(pts[2][0],pts[2][1]); ctx.lineTo(pts[3][0],pts[3][1]); } }
    }
    ctx.stroke();
  }
  const B=BATTLES[curBattle];
  const osm=OSMDATA[curBattle];
  const drawPts=(pts,close)=>{ ctx.beginPath(); pts.forEach((p,i)=>{ const x=p[0]/127*W, y=p[1]/127*H; i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); if(close)ctx.closePath(); ctx.stroke(); };
  if(osm){
    ctx.strokeStyle="rgba(225,215,185,0.38)"; ctx.lineWidth=1; osm.highways.forEach(w=>drawPts(w.pts,false));
    ctx.strokeStyle="rgba(127,196,255,0.55)"; ctx.lineWidth=1.5; osm.waters.forEach(w=>drawPts(w.pts,true));
    ctx.strokeStyle="#7fc4ff"; ctx.lineWidth=2.5; osm.waterways.forEach(w=>drawPts(w.pts,false));
    const rn=osm.waterways.find(w=>w.name);
    ctx.fillStyle="#cfe8ff"; ctx.font="12px sans-serif"; ctx.fillText(rn?("川: "+rn.name+"（OSM実線）"):"川・道: OSM実線", 14, H-34);
  } else {
    ctx.strokeStyle="#7fc4ff"; ctx.lineWidth=3; drawPts(B.river,false);
    ctx.fillStyle="#cfe8ff"; ctx.font="12px sans-serif"; ctx.fillText(B.riverLabel, 14, H-34);
  }
  ctx.fillStyle="#b8ab8a"; ctx.fillText(B.northLabel, 14, 20); ctx.fillText(B.southLabel, 14, H-14);
  B.units.forEach(u=>{ const x=u.gx/127*W, y=u.gy/127*H, R=13;
    // 兵種・役割で形を変える: 本隊=二重菱 / 主力=三角（敵方向） / 側撃=旗 / 殿=盾
    const fillC=u.side==="ally"?"#274b78":"#7e2f22";
    ctx.fillStyle=fillC; ctx.lineWidth=1.6; ctx.strokeStyle="#d9c68f";
    let kx=x, ky=y+0.5;
    const oct=(cx,cy,r)=>{ ctx.beginPath(); for(let k=0;k<8;k++){ const a=Math.PI/8 + k*Math.PI/4; const px=cx+r*Math.cos(a), py=cy+r*Math.sin(a); k?ctx.lineTo(px,py):ctx.moveTo(px,py); } ctx.closePath(); };
    if(u.troop==="general"){ oct(x,y,R+2.5); ctx.fill(); ctx.lineWidth=2.2; ctx.strokeStyle="#e6c96a"; ctx.stroke(); oct(x,y,R-1.5); ctx.lineWidth=1; ctx.strokeStyle="#f2e9d4"; ctx.stroke(); }
    else if(u.troop==="yari"){ const dir=u.side==="ally"?1:-1; ctx.beginPath(); ctx.moveTo(x, y+dir*(R+1)); ctx.lineTo(x-R, y-dir*R*0.75); ctx.lineTo(x+R, y-dir*R*0.75); ctx.closePath(); ctx.fill(); ctx.stroke(); ky=y-dir*2; }
    else if(u.troop==="teppo"){ ctx.beginPath(); ctx.rect(x-R+2, y-R+2, (R-2)*2, (R-2)*2); ctx.fill(); ctx.stroke(); }
    else if(u.troop==="yumi"){ const dir=u.side==="ally"?1:-1; ctx.beginPath(); if(dir>0){ ctx.arc(x,y-2,R,0,Math.PI,false); } else { ctx.arc(x,y+2,R,Math.PI,0,false); } ctx.closePath(); ctx.fill(); ctx.stroke(); ky=y+dir*(R*0.32); }
    else { ctx.beginPath(); ctx.moveTo(x,y-R); ctx.lineTo(x+R,y); ctx.lineTo(x,y+R); ctx.lineTo(x-R,y); ctx.closePath(); ctx.fill(); ctx.stroke(); }
    ctx.fillStyle="#f2e9d4"; ctx.font="bold 12.5px sans-serif"; ctx.textAlign="center"; ctx.textBaseline="middle"; ctx.fillText(u.mark||"", kx, ky);
    // 名前は小さな陣幕風ラベルに
    ctx.font="11.5px sans-serif"; const tw=ctx.measureText(u.name).width, pw=tw+12, ph=17, px0=Math.max(2,Math.min(W-pw-2, x-pw/2)), py0=y-R-ph-3;
    ctx.fillStyle="rgba(12,10,7,0.82)"; ctx.fillRect(px0,py0,pw,ph); ctx.strokeStyle="rgba(217,198,143,0.6)"; ctx.lineWidth=1; ctx.strokeRect(px0,py0,pw,ph);
    ctx.fillStyle="#ece2c8"; ctx.fillText(u.name, px0+pw/2, py0+ph/2+0.5);
    ctx.textAlign="left"; ctx.textBaseline="alphabetic"; });
}
/* ---------- 3D (three.js, 同梱vendor) ---------- */
let threeState=null;
async function init3D(){
  try{
    const THREE = await import("three");
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const host=$("#view3d"); const W=host.clientWidth||900, H=520;
    const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0d0c09);
    const cam=new THREE.PerspectiveCamera(50, W/H, 0.1, 2000); cam.position.set(-30,92,188);
    const ren=new THREE.WebGLRenderer({antialias:true}); ren.setSize(W,H); host.appendChild(ren.domElement);
    const ctl=new OrbitControls(cam, ren.domElement); ctl.enableDamping=true; ctl.target.set(0,2,-8); ctl.maxPolarAngle=Math.PI*0.49; ctl.autoRotate=true; ctl.autoRotateSpeed=0.55; ctl.addEventListener('start',()=>{ ctl.autoRotate=false; });
    scene.fog=new THREE.Fog(0x0d0c09, 300, 560);
    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const sun=new THREE.DirectionalLight(0xfff2d8, 1.6); sun.position.set(-80,140,50); scene.add(sun);
    threeState={THREE,scene,cam,ren,ctl,mesh:null,markers:[]};
    buildTerrain(); animate();
  }catch(e){ $("#view3d").innerHTML='<div style="padding:20px;color:#b8ab8a;font-size:14px;line-height:1.8">3Dライブラリを読み込めませんでした（WebGLが使えない環境の可能性があります）。「2D等高線」表示はそのまま使えます。</div>'; }
}
function buildTerrain(){
  if(!threeState) return; const {THREE,scene}=threeState;
  if(threeState.mesh){ scene.remove(threeState.mesh); threeState.mesh.traverse(o=>{ if(o.geometry) o.geometry.dispose(); if(o.material) o.material.dispose(); }); }
  threeState.markers.forEach(m=>scene.remove(m)); threeState.markers=[];
  const data=DEM[curBattle], N=data.meta.grid, ev=data.elev, min=data.meta.min, max=data.meta.max;
  const ex=parseFloat($("#exSlider").value), SIZE=200, yScale=(SIZE/3900)*ex;
  const geo=new THREE.PlaneGeometry(SIZE,SIZE,N-1,N-1); geo.rotateX(-Math.PI/2);
  const pos=geo.attributes.position, colors=[];
  const cLow=new THREE.Color(0x51663a), cHigh=new THREE.Color(0xe8ddba);
  for(let k=0;k<pos.count;k++){ const i=k%N, j=Math.floor(k/N); const h=ev[j][i]; pos.setY(k,(h-min)*yScale);
    const c=cLow.clone().lerp(cHigh,(h-min)/(max-min)); colors.push(c.r,c.g,c.b); }
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors,3)); geo.computeVertexNormals();
  const group=new THREE.Group();
  const surf=new THREE.Mesh(geo, new THREE.MeshStandardMaterial({vertexColors:true, roughness:1, metalness:0, flatShading:true}));
  surf.position.y=-0.45; group.add(surf);
  const wire=new THREE.Mesh(geo, new THREE.MeshBasicMaterial({wireframe:true, vertexColors:true, transparent:true, opacity:0.55}));
  group.add(wire);
  scene.add(group); threeState.mesh=group;
  const toXYZ=(gx,gy)=>{ const h=ev[Math.round(gy)][Math.round(gx)]; return [ (gx/127-0.5)*SIZE, (h-min)*yScale+4, (gy/127-0.5)*SIZE ]; };
  const B=BATTLES[curBattle];
  const osm3=OSMDATA[curBattle];
  const addLine=(pts,color)=>{ if(!pts||pts.length<2) return; const v=pts.map(p=>{ const gx=Math.max(0,Math.min(127,Math.round(p[0]))), gy=Math.max(0,Math.min(127,Math.round(p[1]))); const h=ev[gy][gx]; return new THREE.Vector3((p[0]/127-0.5)*SIZE,(h-min)*yScale+1.5,(p[1]/127-0.5)*SIZE); }); const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(v), new THREE.LineBasicMaterial({color})); scene.add(line); threeState.markers.push(line); };
  if(osm3){ osm3.highways.forEach(w=>addLine(w.pts,0x8a8064)); osm3.waters.forEach(w=>addLine(w.pts,0x4d7fa6)); osm3.waterways.forEach(w=>addLine(w.pts,0x7fc4ff)); }
  else { addLine(B.river,0x7fc4ff); }
  B.units.forEach(u=>{ const v=toXYZ(u.gx,u.gy);
    const geo3 = u.troop==="general" ? new THREE.CylinderGeometry(3.9,3.9,2.4,8) : u.troop==="teppo" ? new THREE.BoxGeometry(4.8,2.8,4.8) : u.troop==="yumi" ? new THREE.TorusGeometry(2.7,0.95,8,18,Math.PI) : u.troop==="yari" ? new THREE.ConeGeometry(2.9,5.6,6) : new THREE.OctahedronGeometry(3.4);
    const s=new THREE.Mesh(geo3, new THREE.MeshBasicMaterial({color:u.side==="ally"?0x8fc1ff:0xff9d8a}));
    if(u.troop==="yumi") s.rotation.z=0;
    s.position.set(v[0],v[1],v[2]); scene.add(s); threeState.markers.push(s);
    const cv=document.createElement("canvas"); cv.width=256; cv.height=56; const cx=cv.getContext("2d");
    cx.fillStyle="rgba(10,9,6,0.75)"; cx.fillRect(0,0,256,56); cx.fillStyle="#ece2c8"; cx.font="24px sans-serif"; cx.textAlign="center"; cx.fillText(u.name,128,37);
    const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cv), transparent:true})); sp.scale.set(38,8.3,1); sp.position.set(v[0],v[1]+8,v[2]); scene.add(sp); threeState.markers.push(sp); });
}
function animate(){ if(!threeState) return; requestAnimationFrame(animate); threeState.ctl.update(); threeState.ren.render(threeState.scene, threeState.cam);
  const nd=document.getElementById("needle"); if(nd){ const c=threeState.cam.position; nd.style.transform='rotate('+(Math.atan2(c.x,c.z))+'rad)'; } }
/* ---------- OSM runtime fetch (pattern adapted from the user's OSMCityScout, MIT) ---------- */
let OSMDATA=OSM_BAKED, OSMSTATUS={hitotoribashi:'baked', suriagehara:'baked'};
function globalPx(lat,lon){ const n=16384; const gx=(lon+180)/360*n*256; const r=lat*Math.PI/180; const gy=(1-Math.log(Math.tan(r)+1/Math.cos(r))/Math.PI)/2*n*256; return [gx,gy]; }
function cropOrigin(lat,lon){ const g=globalPx(lat,lon); const cx=Math.floor(g[0]), cy=Math.floor(g[1]); const tx=Math.floor(cx/256), ty=Math.floor(cy/256); const px=cx-(tx-1)*256, py=cy-(ty-1)*256; const left=Math.max(0,Math.min(768-512,px-256)), top=Math.max(0,Math.min(768-512,py-256)); return [(tx-1)*256+left,(ty-1)*256+top]; }
function toGrid(lat,lon,origin){ const g=globalPx(lat,lon); return [(g[0]-origin[0])/512*127,(g[1]-origin[1])/512*127]; }
function simplifyPts(pts){ if(pts.length<=2) return pts; const out=[pts[0]]; for(let i=1;i<pts.length-1;i++){ const a=out[out.length-1]; if(Math.hypot(pts[i][0]-a[0],pts[i][1]-a[1])>=1.6) out.push(pts[i]); } out.push(pts[pts.length-1]); return out; }
const OVERPASS_SERVERS=[{name:'private.coffee',url:'https://overpass.private.coffee/api/interpreter'},{name:'VK Maps',url:'https://maps.mail.ru/osm/tools/overpass/api/interpreter'},{name:'overpass-api.de',url:'https://overpass-api.de/api/interpreter'}];
async function fetchOverpass(query){ let lastErr=null;
  for(const sv of OVERPASS_SERVERS){ const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(),20000);
    try{ const resp=await fetch(sv.url,{method:'POST',body:'data='+encodeURIComponent(query),signal:ctrl.signal,mode:'cors',credentials:'omit'});
      if(!resp.ok) throw new Error('HTTP '+resp.status); const j=await resp.json(); if(!Array.isArray(j&&j.elements)) throw new Error('bad response'); return {elements:j.elements, server:sv.name};
    }catch(e){ lastErr=e; } finally{ clearTimeout(to); } }
  throw lastErr||new Error('overpass failed'); }
function updateBadge(){ const m=DEM[curBattle].meta; let osmMsg='川・道: 模式線'; const st=OSMSTATUS[curBattle], d=OSMDATA[curBattle];
  if(st==='loading') osmMsg='川・道: OSMから読み込み中…'; else if(d) osmMsg='川 '+(d.waterways.length)+'本・道 '+(d.highways.length)+'本: OSM実線'+(st&&st.startsWith('ok:')?'（'+st.slice(3)+'）':st==='cache'?'（保存分）':st==='baked'?'（取得済み）':''); else if(st==='fail') osmMsg='川・道: OSM取得に失敗したため模式線';
  $("#stageBadge").textContent='地形: 地理院DEM10B実データ / 標高 '+m.min+'〜'+m.max+'m / '+osmMsg; }
async function loadOSM(bid){ if(OSMDATA[bid]){ updateBadge(); return; } const B=BATTLES[bid]; OSMSTATUS[bid]='loading'; if(bid===curBattle) updateBadge();
  const cacheKey='battlelab-osm:'+bid;
  try{ const sx=localStorage.getItem(cacheKey); if(sx){ const x=JSON.parse(sx); if(Date.now()-x.time<24*3600*1000){ OSMDATA[bid]=x.data; OSMSTATUS[bid]='cache'; if(bid===curBattle){ updateBadge(); draw2D(); buildTerrain(); } return; } } }catch(e){}
  const q='[out:json][timeout:25];(way["waterway"](around:2400,'+B.lat+','+B.lon+');way["highway"](around:2400,'+B.lat+','+B.lon+');way["natural"="water"](around:2400,'+B.lat+','+B.lon+'););out geom;';
  try{ const res=await fetchOverpass(q); const origin=cropOrigin(B.lat,B.lon); const out={waterways:[],highways:[],waters:[],server:res.server};
    for(const e of res.elements){ if(!e.geometry||e.geometry.length<2) continue; const pts=simplifyPts(e.geometry.map(g=>toGrid(g.lat,g.lon,origin))); if(!pts.some(p=>p[0]>-5&&p[0]<132&&p[1]>-5&&p[1]<132)) continue; const item={name:(e.tags&&e.tags.name)||'',pts}; if(e.tags&&e.tags.waterway) out.waterways.push(item); else if(e.tags&&e.tags.highway) out.highways.push(item); else if(e.tags&&e.tags.natural==='water') out.waters.push(item); }
    OSMDATA[bid]=out; OSMSTATUS[bid]='ok:'+res.server; try{ localStorage.setItem(cacheKey,JSON.stringify({time:Date.now(),data:out})); }catch(e){}
  }catch(e){ OSMSTATUS[bid]='fail'; }
  if(bid===curBattle){ updateBadge(); draw2D(); buildTerrain(); } }
/* ---------- wiring ---------- */
document.querySelectorAll("#battleSeg button").forEach(b=>b.onclick=()=>{ document.querySelectorAll("#battleSeg button").forEach(x=>x.classList.remove("on")); b.classList.add("on"); curBattle=b.dataset.b; curPerson="masamune"; curTactic=0; $("#exSlider").value=BATTLES[curBattle].exDefault; renderPanel(); buildTerrain(); draw2D(); loadOSM(curBattle); });
document.querySelectorAll("#viewSeg button").forEach(b=>b.onclick=()=>{ document.querySelectorAll("#viewSeg button").forEach(x=>x.classList.remove("on")); b.classList.add("on"); curView=b.dataset.v;
  $("#view3d").style.display = curView==="3d"?"block":"none"; $("#view2d").style.display = curView==="2d"?"block":"none"; if(curView==="2d") draw2D(); });
$("#healthSel").onchange=renderPanel;
$("#exSlider").oninput=()=>{ $("#exVal").textContent="×"+$("#exSlider").value; buildTerrain(); };
$("#resolve").onclick=resolveBattle;
$("#exSlider").value=BATTLES[curBattle].exDefault;
renderPanel(); draw2D(); init3D(); loadOSM(curBattle);
</script>
</body>
</html>
"""
html = html.replace("__HITO__", hito).replace("__SURI__", suri).replace("__OSM_HITO__", osm_hito).replace("__OSM_SURI__", osm_suri)
(base/"index.html").write_text(html)
print("written", len(html))
