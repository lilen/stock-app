// 自選股雲端同步 + 行情代理（Google Apps Script）
// 部署方式：script.google.com → 新專案 → 貼上本檔 → 部署 → 新增部署作業
//   類型：網頁應用程式／執行身分：我／存取權：所有人 → 複製網址到 App 的「☁ 同步」設定
// 更新程式後：部署 → 管理部署作業 → ✎ 編輯 → 版本選「新版本」→ 部署（網址不變）
// 資料存在 Script Properties，不需要試算表。

const KEY = 'watch_data'

// 行情代理只允許這些來源（證交所、櫃買中心沒有開 CORS，瀏覽器無法直接讀）
const PROXY_HOSTS = ['mis.twse.com.tw', 'openapi.twse.com.tw', 'www.tpex.org.tw']

function doGet(e) {
  const url = e && e.parameter && e.parameter.url
  if (url) return proxy(url)
  const raw = PropertiesService.getScriptProperties().getProperty(KEY)
  return json(raw ? JSON.parse(raw) : { updatedAt: 0, groups: null, names: {} })
}

function proxy(url) {
  const m = url.match(/^https:\/\/([^\/?#]+)\//)
  if (!m || PROXY_HOSTS.indexOf(m[1]) < 0) return json({ error: 'host not allowed' })
  const res = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true,
    headers: { Referer: 'https://mis.twse.com.tw/stock/index.jsp' },
  })
  if (res.getResponseCode() !== 200) return json({ error: 'upstream ' + res.getResponseCode() })
  return ContentService.createTextOutput(res.getContentText('UTF-8'))
    .setMimeType(ContentService.MimeType.JSON)
}

function doPost(e) {
  const lock = LockService.getScriptLock()
  lock.waitLock(10000)
  try {
    const body  = JSON.parse(e.postData.contents)
    const props = PropertiesService.getScriptProperties()
    const cur   = JSON.parse(props.getProperty(KEY) || '{"updatedAt":0}')
    // 只接受較新的資料，避免舊手機覆蓋新資料
    if (!Array.isArray(body.groups) || (body.updatedAt || 0) < (cur.updatedAt || 0)) {
      return json({ ok: false, ...cur })
    }
    const data = { updatedAt: body.updatedAt, groups: body.groups, names: body.names || {} }
    props.setProperty(KEY, JSON.stringify(data))
    return json({ ok: true, ...data })
  } finally {
    lock.releaseLock()
  }
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON)
}
