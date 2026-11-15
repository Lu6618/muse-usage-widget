// ============================================================
// AI 用量挂件（Scriptable）multi — Medium 横长，多服务一行
// 按帖子做法：ListWidget 画出来，不是 WebView 套网页。
// 每服务一行：服务名、周剩余%、残量条、重置时间 + 剩几天
// 右上角是数据时间。剩余<=10% 红、<=25% 黄。
// 5 小时枠有的服务会小字併记，没有的不编。
// 数据源：只读 GitHub raw JSON（本机定时跑 subscription-status 生成）
// https://raw.githubusercontent.com/xiadasy/muse-usage-widget/main/data/ai_usage.json
// JSON 里只有套餐/百分比/重置时间，没有账号、没有密钥。
// 取不到就显示手机里上次缓存的数据，并标“缓存”。
// 挂件自己不登录任何账号，脚本里也不贴 token。
//
// 安装：Scriptable 里新建脚本粘贴全文，命名“AI 用量”，
// 长按桌面 -> + -> Scriptable -> 选这个脚本，选 Medium。
// ============================================================

const DATA_URL = "https://raw.githubusercontent.com/xiadasy/muse-usage-widget/main/data/ai_usage.json";

const TIMEOUT_SECONDS = 15;
const CACHE_FILE = "ai-usage-cache.json";

// ---------- 配色（暖米白卡，沿用 v3） ----------
const C = {
  bg: new Color("#fbf6ec"),
  title: new Color("#241a12"),
  label: new Color("#8a7a66"),
  value: new Color("#241a12"),
  track: new Color("#e9dfc9"),
  footer: new Color("#a08b74"),
  grey: new Color("#9a8d7a"),
  red: new Color("#dc2626"),
  yellow: new Color("#d97706"),
  green: new Color("#16a34a"),
};

function num(v, d = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

function remainColor(remaining) {
  if (remaining <= 10) return C.red;
  if (remaining <= 25) return C.yellow;
  return C.green;
}

function fmtResetDate(s) {
  const m = String(s || "").match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  if (!m) return String(s || "—");
  return Number(m[2]) + "月" + Number(m[3]) + "日 " + m[4] + ":" + m[5];
}

function fmtUpdated(s) {
  const m = String(s || "").match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  if (!m) return "";
  return Number(m[2]) + "/" + Number(m[3]) + " " + m[4] + ":" + m[5];
}

// ---------- 缓存 ----------
function readCache() {
  try {
    const fm = FileManager.local();
    const path = fm.joinPath(fm.libraryDirectory(), CACHE_FILE);
    if (!fm.fileExists(path)) return null;
    return JSON.parse(fm.readString(path));
  } catch (e) {
    return null;
  }
}

function writeCache(j) {
  try {
    const fm = FileManager.local();
    const path = fm.joinPath(fm.libraryDirectory(), CACHE_FILE);
    fm.writeString(path, JSON.stringify(j));
  } catch (e) {}
}

async function fetchData() {
  const req = new Request(DATA_URL + "?t=" + Date.now());
  req.method = "GET";
  req.timeoutInterval = TIMEOUT_SECONDS;
  req.headers = { Accept: "application/json", "Cache-Control": "no-store" };
  const j = await req.loadJSON();
  writeCache(j);
  return { data: j, cached: false };
}

// ---------- 行：每服务一行（名 + 条 + 剩余% + 重置/原因） ----------
// Medium 只有 170pt 高，4 个服务做两行会溢出，严格按帖子“一行一个服务”画。
function addServiceRow(widget, s) {
  const row = widget.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();
  row.spacing = 6;

  const name = row.addText(String(s.name || "—"));
  name.font = Font.semiboldSystemFont(12);
  name.textColor = C.value;

  // 残量条（定宽 84pt，填充按剩余%算）
  const barBg = row.addStack();
  barBg.size = new Size(84, 6);
  barBg.cornerRadius = 3;
  barBg.backgroundColor = C.track;
  barBg.layoutHorizontally();
  if (s.status === "ok") {
    const rem = num(s.percent_remaining, 0);
    const fill = barBg.addStack();
    fill.size = new Size(Math.max(84 * rem / 100, rem > 0 ? 4 : 0), 6);
    fill.cornerRadius = 3;
    fill.backgroundColor = remainColor(rem);
  }

  if (s.status === "ok") {
    const rem = num(s.percent_remaining, 0);
    const pct = row.addText("剩" + rem + "%");
    pct.font = Font.boldSystemFont(12);
    pct.textColor = remainColor(rem);
    let sub = fmtResetShort(s.resets_at);
    if (s.days_left != null) sub += "·剩" + s.days_left + "天";
    if (s.window_5h != null) sub += "·5h剩" + s.window_5h + "%";
    const subT = row.addText(sub);
    subT.font = Font.systemFont(10);
    subT.textColor = C.label;
    subT.lineLimit = 1;
  } else {
    const pct = row.addText("查不到");
    pct.font = Font.semiboldSystemFont(12);
    pct.textColor = C.grey;
    const subT = row.addText(String(s.short || s.reason || "未接通"));
    subT.font = Font.systemFont(10);
    subT.textColor = C.label;
    subT.lineLimit = 1;
  }
}

function fmtResetShort(s) {
  const m = String(s || "").match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  if (!m) return String(s || "—");
  return Number(m[2]) + "-" + Number(m[3]) + " " + m[4] + ":" + m[5];
}

// ---------- 主流程 ----------
let data = null;
let cached = false;
try {
  const r = await fetchData();
  data = r.data;
  cached = r.cached;
} catch (e) {
  data = readCache();
  cached = true;
}

const widget = new ListWidget();
widget.backgroundColor = C.bg;
widget.setPadding(12, 14, 10, 14);

if (!data || !data.services) {
  const t = widget.addText("暂无数据");
  t.font = Font.boldSystemFont(16);
  t.textColor = C.value;
  widget.addSpacer();
  const f = widget.addText("请联网后点挂件重试");
  f.font = Font.systemFont(11);
  f.textColor = C.label;
} else {
  // 顶栏：标题 + 右上数据时间
  const head = widget.addStack();
  head.layoutHorizontally();
  head.centerAlignContent();
  const title = head.addText("AI 用量");
  title.font = Font.boldSystemFont(16);
  title.textColor = C.title;
  head.addSpacer();
  const upd = head.addText(fmtUpdated(data.updated_at) + (cached ? " · 缓存" : ""));
  upd.font = Font.systemFont(11);
  upd.textColor = cached ? C.red : C.label;

  widget.addSpacer(6);

  const services = data.services || [];
  // Medium：全部 4 行；小尺寸只放第一条有数的
  const list = config.widgetFamily === "small" ? services.slice(0, 1) : services;
  for (let i = 0; i < list.length; i++) {
    addServiceRow(widget, list[i]);
    if (i < list.length - 1) widget.addSpacer(6);
  }

  widget.addSpacer(6);
  // 底栏
  const foot = widget.addStack();
  foot.layoutHorizontally();
  const f1 = foot.addText("iOS 定时刷新 · 非实时");
  f1.font = Font.systemFont(10);
  f1.textColor = C.footer;
  foot.addSpacer();
  const muse = services.find((x) => x.id === "muse");
  if (muse && muse.status === "ok" && muse.extra && muse.extra.left_label) {
    const f2 = foot.addText("额外 " + muse.extra.left_label.replace(" tokens left", "B"));
    f2.font = Font.systemFont(10);
    f2.textColor = C.footer;
  }
}

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  widget.presentMedium();
}
Script.complete();
