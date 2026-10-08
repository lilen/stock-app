// 自選股雲端同步（Google Apps Script）
// 部署方式：script.google.com → 新專案 → 貼上本檔 → 部署 → 新增部署作業
//   類型：網頁應用程式／執行身分：我／存取權：所有人 → 複製網址到 App 的「☁ 同步」設定
// 資料存在 Script Properties，不需要試算表。

const KEY = 'watch_data'

function doGet() {
  const raw = PropertiesService.getScriptProperties().getProperty(KEY)
  return json(raw ? JSON.parse(raw) : { updatedAt: 0, groups: null, names: {} })
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
