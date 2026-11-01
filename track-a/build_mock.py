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
<title>奥羽一生録・合戦実験 トラックA | 3D布陣図モック v0.12</title>
<script type="importmap">{"imports":{"three":"./vendor/three.module.js","three/addons/":"./vendor/"}}</script>
<style>
  :root{ --bg:#16140f; --panel:#221e16; --line:#4a4232; --ink:#ece2c8; --sub:#b8ab8a; --ally:#8fc1ff; --enemy:#ff9d8a; --accent:#d9a441; }
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Mincho ProN","Yu Mincho",serif;}
  header{padding:14px 16px 8px} h1{font-size:20px;margin:0 0 4px} .sub{color:var(--sub);font-size:12.5px;line-height:1.6}
  .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  .seg{display:flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
  .seg button{background:transparent;color:var(--sub);border:0;padding:8px 14px;font-size:14px;cursor:pointer;font-family:inherit}
  .seg button.on{background:var(--accent);color:#1a160d;font-weight:700}
  main{display:block;padding:10px 16px 20px}
  .fold{margin-top:9px;border-top:1px solid var(--line);padding-top:8px}
  .fold-head{width:100%;text-align:left;background:none;border:none;color:var(--ink);font-size:13.5px;font-weight:700;cursor:pointer;padding:2px 0;font-family:inherit}
  .fold-body{margin-top:6px}
  @media(max-width:860px){ main{grid-template-columns:1fr} }
  #stage{position:relative;background:#0d0c09;border:1px solid var(--line);border-radius:10px;min-height:420px;overflow:hidden}
  #view3d,#view2d{width:100%;height:520px;display:block}
  #view2d{display:none}
  #compass{position:absolute;top:10px;right:10px;width:52px;height:52px;border-radius:50%;background:rgba(20,18,13,.85);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;flex-direction:column;font-size:11px;color:var(--sub)}
  #needle{font-size:18px;line-height:1;color:var(--accent);display:block}
  #tacticOverlay{position:absolute;left:10px;right:10px;bottom:10px;z-index:6;background:rgba(14,12,9,.93);border:1px solid var(--gold);border-radius:12px;padding:10px 12px;box-shadow:0 6px 24px rgba(0,0,0,.5);max-height:82%;overflow-y:auto}
  #tacticOverlay .to-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
  #toTitle{font-weight:700;font-size:14.5px}
  #toMeta{font-size:12px;color:var(--sub)}
  #toTactics{display:grid;gap:6px}
  #toTactics .tactic{padding:8px 10px}
  #toTactics .tactic .t{font-size:13.5px}
  #toTactics .tactic .m{font-size:11.5px}
  #toResolve{width:100%;margin-top:8px;background:var(--gold);color:#241f10;font-weight:700;border:none;border-radius:9px;padding:10px;font-size:14.5px;cursor:pointer;position:sticky;bottom:0;box-shadow:0 -4px 14px rgba(0,0,0,.45)}
  #toToggle{background:#221e15;color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:4px 10px;font-size:12px;cursor:pointer;font-family:inherit}
  #toCompact{display:none;font-size:13px;color:var(--ink)}
  #tacticOverlay.collapsed #toTactics, #tacticOverlay.collapsed #toResolve{display:none}
  #tacticOverlay.collapsed #toCompact{display:block}
  #tacticOverlay.collapsed .to-head{margin-bottom:4px}
  #stageStatus{position:absolute;top:10px;left:10px;z-index:6;max-width:72%;background:rgba(14,12,9,.9);border:1px solid var(--line);border-radius:9px;padding:7px 11px;font-size:13px;color:var(--ink)}
  #resultOverlay{position:absolute;left:10px;right:10px;bottom:10px;z-index:6;background:rgba(14,12,9,.94);border:1px solid var(--gold);border-radius:12px;padding:12px 14px;max-height:62%;overflow:auto;box-shadow:0 6px 24px rgba(0,0,0,.5)}
  #roHead{font-weight:700;font-size:16px;margin-bottom:6px}
  #roBody{font-size:13.5px;line-height:1.75;color:var(--ink);white-space:pre-wrap}
  .ro-btns{display:flex;gap:8px;margin-top:10px}
  .ro-btns button{flex:1;border-radius:9px;padding:9px;font-size:13.5px;cursor:pointer;border:1px solid var(--line);background:#221e15;color:var(--ink)}
  .ro-btns #roAgain{background:var(--gold);color:#241f10;font-weight:700;border:none}
  .hiddenOv{display:none !important}
  #sheet{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:min(1060px,100%);z-index:40;background:rgba(14,12,9,.97);border:1px solid var(--gold);border-bottom:none;border-radius:14px 14px 0 0;padding:10px 14px calc(10px + env(safe-area-inset-bottom));box-shadow:0 -8px 30px rgba(0,0,0,.55)}
  .sheet-head{display:flex;justify-content:space-between;align-items:center;gap:8px}
  #shTitle{font-weight:700;font-size:15px}
  #shMeta{font-size:12px;color:var(--sub)}
  #shToggle{background:#221e15;color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:5px 12px;font-size:12.5px;cursor:pointer;font-family:inherit}
  #shCompact{display:none;font-size:13px;margin-top:3px;color:var(--ink)}
  #sheet.collapsed #shCompact{display:block}
  #sheet.collapsed .sheet-body{display:none}
  .sheet-body{margin-top:8px;max-height:44vh;overflow-y:auto}
  #shTactics{display:grid;gap:6px}
  #shTactics .tactic{padding:8px 10px}
  #shStatus{font-size:13.5px;padding:4px 0;line-height:1.7}
  #shRoHead{font-weight:700;font-size:16px;margin-bottom:5px}
  #shRoBody{font-size:13.5px;line-height:1.75;white-space:pre-wrap}
  .sheet-foot{margin-top:9px}
  #shDecide,#shAgain{width:100%;background:var(--gold);color:#241f10;font-weight:700;border:none;border-radius:9px;padding:12px;font-size:15px;cursor:pointer;font-family:inherit}
  body{padding-bottom:110px}
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
  #resolve{width:100%;padding:13px;background:var(--accent);color:#1a160d;border:0;border-radius:8px;font-size:15.5px;font-weight:700;cursor:pointer;font-family:inherit;position:sticky;bottom:8px;z-index:3;box-shadow:0 5px 20px rgba(0,0,0,.6)}
  #result{margin-top:12px;font-size:13.5px;line-height:1.8;background:#171410;border:1px solid var(--line);border-radius:8px;padding:10px;display:none;white-space:pre-wrap}
  input[type=range]{width:100%}
  .note{font-size:12px;color:var(--sub);line-height:1.7}
  label.lbl{font-size:12.5px;color:var(--sub);display:block;margin:8px 0 4px}
</style>
</head>
<body>
<header>
  <h1>合戦実験 トラックA — 3D地形の布陣図＋采配 v0.12</h1>
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
<div id="sheet">
    <div class="sheet-head"><span id="shTitle"></span><span style="display:flex;gap:8px;align-items:center"><span id="shMeta"></span><button id="shToggle">閉じる</button></span></div>
    <div id="shCompact"></div>
    <div class="sheet-body" id="shBody">
      <div id="shTactics"></div>
      <div id="shStatus" class="hiddenOv"></div>
      <div id="shResult" class="hiddenOv"><div id="shRoHead"></div><div id="shRoBody"></div></div>
      <div class="fold">
        <button class="fold-head" data-fold="foldPerson">武将・健康 ▽</button>
        <div class="fold-body hiddenOv" id="foldPerson">
          <div class="seg" id="personSeg"></div>
          <div class="stats" id="personStats" style="margin-top:8px"></div>
          <label class="lbl">健康（決定003の状態語）</label>
          <select id="healthSel">
            <option value="good">健やか</option><option value="bad">不調</option><option value="critical">重篤</option>
          </select>
        </div>
      </div>
      <div class="fold">
        <button class="fold-head" data-fold="foldInfo">合戦情報・凡例 ▽</button>
        <div class="fold-body hiddenOv" id="foldInfo">
          <h3 id="battleTitle" style="margin:2px 0 6px"></h3>
          <div class="stats" id="battleInfo"></div>
          <div class="note" style="margin-top:8px">マーカー凡例（形=大将と兵種、試作割当）: <b style="color:var(--ink)">八角形</b> 大将 / <b style="color:var(--ink)">▲</b> 槍（敵の向きに尖る） / <b style="color:var(--ink)">◆</b> 騎馬 / <b style="color:var(--ink)">■</b> 鉄砲 / <b style="color:var(--ink)">半月</b> 弓。色は味方=青、敵=赤。殿・側撃などの役目は部隊名で示します。</div>
          <label class="lbl">地形の縦誇張（3D）: <span id="exVal"></span></label>
          <input type="range" id="exSlider" min="1" max="10" step="0.5" value="6">
          <p class="note" style="margin-top:10px">危険度は設計メモv0.1の試作式: 合戦基礎＋役目危険＋敵優勢 − 実効武勇×0.25 − 知略×0.15 ＋健康補正＋地形修正。討死は危険度50以上でのみ起こりえます。数値はすべて調整用の試作値です。</p>
        </div>
      </div>
      <div class="fold">
        <button class="fold-head" data-fold="foldLog">経過ログ ▽</button>
        <div class="fold-body hiddenOv" id="foldLog">
          <div id="turnLog"></div>
          <div id="result"></div>
        </div>
      </div>
    </div>
    <div class="sheet-foot"><button id="shDecide">決定する（この采配で進める）</button><button id="shAgain" class="hiddenOv">もう一度（配置を戻す）</button></div>
  </div>
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
const UNIT_PATHS={
 hitotoribashi:{ "伊達本隊・政宗":[[64,36],[66,33],[70,29],[74,25]], "成実隊":[[45,50],[49,46],[54,42],[59,38]], "鬼庭隊（殿）":[[59,60],[59,58],[60,56],[60,54]], "連合本隊・佐竹":[[66,99],[66,90],[65,82],[65,75]], "蘆名隊":[[37,93],[40,85],[44,78],[47,72]], "岩城隊":[[93,95],[88,87],[83,80],[79,74]] },
 suriagehara:{ "伊達本隊・政宗":[[58,72],[58,65],[58,59],[59,54]], "成実隊（側撃）":[[28,54],[35,51],[42,47],[48,44]], "片倉隊":[[76,70],[73,64],[70,58],[68,53]], "蘆名本隊・義広":[[64,34],[64,39],[62,44],[60,48]], "金上隊":[[46,27],[47,33],[49,39],[51,44]], "佐瀬隊":[[84,30],[81,37],[77,43],[73,48]] } };
const BATTLE_TURNS={
 hitotoribashi:["連合軍が北上し、瀬戸川の線へ迫る。伊達勢は橋の北で迎える構え。","鬼庭の殿が橋の上で踏みとどまり、連合の先鋒と激しくぶつかる。本隊は退き始めた。","伊達勢は陣を収めて北へ退く。殿が最後まで橋を守り抜いた。"],
 suriagehara:["蘆名勢が原へ進み出る。伊達勢は高みからその動きを見ている。","成実隊が西から回り込んで側面へ迫る。金上隊が伊達本隊へ向けて駆け下りる。","蘆名勢は崩れ、南へ退いていく。原の主導権は伊達へ移った。"] };
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
  /* 采配リストは下部シート側（renderOverlay）が描く */
  $("#exVal").textContent = "×"+$("#exSlider").value;
  renderOverlay(); syncOverlay();
}
function renderOverlay(){ const B=BATTLES[curBattle], P=B.persons[curPerson];
  $("#sheet").classList.toggle("collapsed", overlayCollapsed);
  $("#shToggle").textContent = overlayCollapsed ? "開く" : "閉じる";
  const ct=P.tactics[curTactic], cd=dangerOf(ct);
  $("#shCompact").textContent = battlePhase==="playing" ? ($("#shStatus").textContent||"合戦中…") : battlePhase==="done" ? ($("#shRoHead").textContent||"結果") : "選択中: "+ct.text+"（危険度 "+cd+"）";
  $("#shTitle").textContent=P.name+" の采配 — "+B.title;
  $("#shMeta").textContent="兵種: "+P.troopLabel+" / 健康: "+healthMods().label;
  const tw=$("#shTactics"); tw.innerHTML="";
  P.tactics.forEach((t,i)=>{ const d=dangerOf(t), bd=band(d);
    const b=document.createElement("button"); b.className="tactic"+(i===curTactic?" on":"");
    const ta=troopAdj(t); const taTxt = ta!==0 ? ' / 騎馬補正 '+(ta>0?'+':'−')+Math.abs(ta) : '';
    b.innerHTML='<span class="t">'+t.text+'</span><span class="m">'+t.role+taTxt+' / 危険度 <span class="danger '+bd[1]+'">'+d+"・"+bd[0]+'</span></span>';
    b.onclick=()=>{ curTactic=i; renderPanel(); }; tw.appendChild(b); }); }
function setStatus(msg){ const st=$("#shStatus"); st.textContent=msg; if(overlayCollapsed) $("#shCompact").textContent=msg; }
function syncOverlay(){ const ready=battlePhase==="ready", playing=battlePhase==="playing", done=battlePhase==="done";
  $("#shTactics").classList.toggle("hiddenOv", !ready);
  $("#shStatus").classList.toggle("hiddenOv", !playing);
  $("#shResult").classList.toggle("hiddenOv", !done);
  $("#shDecide").classList.toggle("hiddenOv", !ready);
  $("#shAgain").classList.toggle("hiddenOv", !done);
  if(done){ overlayCollapsed=false; $("#sheet").classList.remove("collapsed"); $("#shToggle").textContent="閉じる"; } }
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
  const lines=out.split("\n"); $("#shRoHead").textContent=lines[0]; $("#shRoBody").textContent=lines.slice(1).join("\n");
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
  B.units.forEach((u,ui)=>{ const up=turnPos?turnPos[ui]:[u.gx,u.gy]; const x=up[0]/127*W, y=up[1]/127*H, R=13;
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
/* ---------- ターン進行（部隊の動き） ---------- */
let turnPos=null, battlePhase="ready", overlayCollapsed=false;
function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }
function logTurn(msg){ const tl=$("#turnLog"); const d=document.createElement("div"); d.style.cssText="margin:3px 0;color:var(--sub);font-size:13.5px"; d.textContent=msg; tl.appendChild(d); }
function syncPositions(){ if(curView==="2d") draw2D(); else if(threeState && threeState.unitGroups) positionUnitGroups(); }
function positionUnitGroups(){ threeState.unitGroups.forEach((rec,i)=>{ const v=threeState.toXYZ(turnPos[i][0], turnPos[i][1]); rec.ug.position.set(v[0], v[1]-4, v[2]); }); }
async function animateTurns(){ const B=BATTLES[curBattle]; turnPos=B.units.map(u=>[u.gx,u.gy]); syncPositions();
  logTurn("布陣完了。合戦が始まります。");
  const texts=BATTLE_TURNS[curBattle]||[];
  for(let t=1;t<=3;t++){ const from=turnPos.map(p=>p.slice());
    const to=B.units.map(u=>{ const pa=(UNIT_PATHS[curBattle]||{})[u.name]; return pa?pa[t]:[u.gx,u.gy]; });
    const t0=performance.now(), dur=1050;
    await new Promise(res=>{ const step=()=>{ const k=Math.min(1,(performance.now()-t0)/dur); const e=k<0.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
      turnPos=B.units.map((u,i)=>[from[i][0]+(to[i][0]-from[i][0])*e, from[i][1]+(to[i][1]-from[i][1])*e]); syncPositions();
      if(k<1) requestAnimationFrame(step); else res(); }; step(); });
    logTurn("第"+t+"ターン — "+(texts[t-1]||"")); setStatus("第"+t+"ターン — "+(texts[t-1]||"")); await sleep(300); } }
function resetBattlePositions(){ turnPos=null; battlePhase="ready"; if(curView==="2d") draw2D(); else buildTerrain(); syncOverlay(); }
async function playBattle(){ if(battlePhase==="playing") return; if(battlePhase==="done") resetBattlePositions();
  battlePhase="playing"; const rb=$("#shDecide"); rb.disabled=true;
  $("#turnLog").innerHTML=""; $("#result").style.display="none"; syncOverlay();
  if(threeState && threeState.ctl) threeState.ctl.autoRotate=false;
  setStatus("采配「"+BATTLES[curBattle].persons[curPerson].tactics[curTactic].text+"」— 合戦が始まります");
  await animateTurns();
  battlePhase="done"; rb.disabled=false; resolveBattle(); syncOverlay(); }
/* ---------- 3D (three.js, 同梱vendor) ---------- */
function flagTexture(u, THREE){ const isGen=u.troop==="general"; const c=document.createElement("canvas"); c.width=isGen?96:160; c.height=isGen?256:104; const x=c.getContext("2d");
  x.fillStyle=u.side==="ally"?"#2c5f9e":"#9e3b2c"; x.fillRect(0,0,c.width,c.height);
  x.strokeStyle=isGen?"#e6c96a":"#ece2c8"; x.lineWidth=isGen?8:5; x.strokeRect(x.lineWidth/2,x.lineWidth/2,c.width-x.lineWidth,c.height-x.lineWidth);
  x.fillStyle="#f6efdb"; x.textAlign="center"; x.textBaseline="middle"; x.font="bold "+(isGen?62:58)+"px sans-serif";
  if(isGen){ x.fillText(u.mark, c.width/2, c.height/2-26); x.font="bold 25px sans-serif"; x.fillText("大将", c.width/2, c.height/2+42); }
  else x.fillText(u.mark, c.width/2, c.height/2+2);
  return new THREE.CanvasTexture(c); }
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
    threeState={THREE,scene,cam,ren,ctl,mesh:null,markers:[],flags:[],unitGroups:[],toXYZ:null};
    buildTerrain(); animate();
  }catch(e){ $("#view3d").innerHTML='<div style="padding:20px;color:#b8ab8a;font-size:14px;line-height:1.8">3Dライブラリを読み込めませんでした（WebGLが使えない環境の可能性があります）。「2D等高線」表示はそのまま使えます。</div>'; }
}
function buildTerrain(){
  if(!threeState) return; const {THREE,scene}=threeState;
  if(threeState.mesh){ scene.remove(threeState.mesh); threeState.mesh.traverse(o=>{ if(o.geometry) o.geometry.dispose(); if(o.material) o.material.dispose(); }); }
  threeState.markers.forEach(m=>scene.remove(m)); threeState.markers=[]; threeState.flags=[]; threeState.unitGroups=[];
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
  const toXYZ=(gx,gy)=>{ const h=ev[Math.max(0,Math.min(127,Math.round(gy)))][Math.max(0,Math.min(127,Math.round(gx)))]; return [ (gx/127-0.5)*SIZE, (h-min)*yScale+4, (gy/127-0.5)*SIZE ]; };
  threeState.toXYZ=toXYZ;
  const B=BATTLES[curBattle];
  const osm3=OSMDATA[curBattle];
  const addLine=(pts,color)=>{ if(!pts||pts.length<2) return; const v=pts.map(p=>{ const gx=Math.max(0,Math.min(127,Math.round(p[0]))), gy=Math.max(0,Math.min(127,Math.round(p[1]))); const h=ev[gy][gx]; return new THREE.Vector3((p[0]/127-0.5)*SIZE,(h-min)*yScale+1.5,(p[1]/127-0.5)*SIZE); }); const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(v), new THREE.LineBasicMaterial({color})); scene.add(line); threeState.markers.push(line); };
  if(osm3){ osm3.highways.forEach(w=>addLine(w.pts,0x8a8064)); osm3.waters.forEach(w=>addLine(w.pts,0x4d7fa6)); osm3.waterways.forEach(w=>addLine(w.pts,0x7fc4ff)); }
  else { addLine(B.river,0x7fc4ff); }
  B.units.forEach(u=>{ const v=toXYZ(u.gx,u.gy);
    const ug=new THREE.Group(); ug.position.set(v[0], v[1]-4, v[2]); scene.add(ug); threeState.markers.push(ug);
    const isGen=u.troop==="general";
    const geo3 = u.troop==="general" ? new THREE.CylinderGeometry(3.9,3.9,2.4,8) : u.troop==="teppo" ? new THREE.BoxGeometry(4.8,2.8,4.8) : u.troop==="yumi" ? new THREE.TorusGeometry(2.7,0.95,8,18,Math.PI) : u.troop==="yari" ? new THREE.ConeGeometry(2.9,5.6,6) : new THREE.OctahedronGeometry(3.4);
    const s=new THREE.Mesh(geo3, new THREE.MeshBasicMaterial({color:u.side==="ally"?0x8fc1ff:0xff9d8a}));
    s.position.set(0,4,0); ug.add(s);
    const cv=document.createElement("canvas"); cv.width=256; cv.height=56; const cx=cv.getContext("2d");
    cx.fillStyle="rgba(10,9,6,0.75)"; cx.fillRect(0,0,256,56); cx.fillStyle="#ece2c8"; cx.font="24px sans-serif"; cx.textAlign="center"; cx.fillText(u.name,128,37);
    const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cv), transparent:true})); sp.scale.set(38,8.3,1); sp.position.set(0, isGen?27:19.5, 0); ug.add(sp);
    const poleH=isGen?22:15, fw=isGen?5:9, fh=isGen?15:6;
    const fg=new THREE.Group(); fg.position.set(4.6,0,0);
    const pole=new THREE.Mesh(new THREE.CylinderGeometry(0.14,0.14,poleH,6), new THREE.MeshBasicMaterial({color:0xd8cba6})); pole.position.y=poleH/2; fg.add(pole);
    const flag=new THREE.Mesh(new THREE.PlaneGeometry(fw,fh), new THREE.MeshBasicMaterial({map:flagTexture(u,THREE), side:THREE.DoubleSide})); flag.position.set(fw/2, poleH-fh/2-(isGen?0.4:0.6), 0); fg.add(flag);
    fg.userData.baseRot=(((u.gx*7+u.gy*13)%5)-2)*0.18; fg.rotation.y=fg.userData.baseRot; ug.add(fg); threeState.flags.push(fg);
    threeState.unitGroups.push({u, ug}); });
  if(turnPos) positionUnitGroups();
}
function animate(){ if(!threeState) return; requestAnimationFrame(animate); threeState.ctl.update(); threeState.ren.render(threeState.scene, threeState.cam);
  const tt2=performance.now()/1000; (threeState.flags||[]).forEach((f,i)=>{ f.rotation.y=f.userData.baseRot + Math.sin(tt2*0.9+i*1.7)*0.14; });
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
document.querySelectorAll("#battleSeg button").forEach(b=>b.onclick=()=>{ document.querySelectorAll("#battleSeg button").forEach(x=>x.classList.remove("on")); b.classList.add("on"); curBattle=b.dataset.b; curPerson="masamune"; curTactic=0; turnPos=null; battlePhase="ready"; $("#turnLog").innerHTML=""; $("#result").style.display="none"; $("#exSlider").value=BATTLES[curBattle].exDefault; renderPanel(); buildTerrain(); draw2D(); loadOSM(curBattle); });
document.querySelectorAll("#viewSeg button").forEach(b=>b.onclick=()=>{ document.querySelectorAll("#viewSeg button").forEach(x=>x.classList.remove("on")); b.classList.add("on"); curView=b.dataset.v;
  $("#view3d").style.display = curView==="3d"?"block":"none"; $("#view2d").style.display = curView==="2d"?"block":"none"; if(curView==="2d") draw2D(); });
$("#healthSel").onchange=renderPanel;
$("#exSlider").oninput=()=>{ $("#exVal").textContent="×"+$("#exSlider").value; buildTerrain(); };
$("#shDecide").onclick=playBattle;
$("#shToggle").onclick=()=>{ overlayCollapsed=!overlayCollapsed; renderOverlay(); };
document.querySelectorAll(".fold-head").forEach(b=>b.onclick=()=>{ const f=document.getElementById(b.dataset.fold); const nowHidden=f.classList.toggle("hiddenOv"); b.textContent=b.textContent.replace(/▽|△$/, nowHidden?"▽":"△"); });
$("#shAgain").onclick=()=>{ resetBattlePositions(); $("#result").style.display="none"; $("#turnLog").innerHTML=""; syncOverlay(); };
$("#exSlider").value=BATTLES[curBattle].exDefault;
renderPanel(); draw2D(); init3D(); loadOSM(curBattle);
</script>
</body>
</html>
"""
html = html.replace("__HITO__", hito).replace("__SURI__", suri).replace("__OSM_HITO__", osm_hito).replace("__OSM_SURI__", osm_suri)
(base/"index.html").write_text(html)
print("written", len(html))
