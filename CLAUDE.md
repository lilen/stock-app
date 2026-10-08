# CLAUDE.md

This file guides Claude Code when it works in this repository.

## 專案概要

台股自選股網頁 App（單一 `index.html`，Vue 3 CDN），部署在 GitHub Pages：
https://lilen.github.io/stock-app/ （push 到 `master` 約 1～2 分鐘後生效）

| 檔案 | 用途 |
|------|------|
| `index.html` | 整個 App（HTML + CSS + Vue setup） |
| `stocks.json` | 靜態股票清單（代號／名稱／市場），供搜尋加入自選 |
| `sync.gs` | Google Apps Script：多裝置同步自選股 + 行情代理 |
| `server.py` | 本機開發用伺服器（含各 API 的 proxy），`uv run --no-project python server.py 8765` |

本機（localhost）時 App 走 `server.py` 的 `/proxy/*`；線上時走下面的來源。

## 雲端同步（sync.gs）

- 使用者自己部署在 script.google.com（網頁應用程式／執行身分：我／存取權：所有人）。
- **雲端網址只存在各手機的 localStorage，絕對不要寫進 repo**（repo 是公開的，網址等同自選股的寫入鑰匙）。在手機 App 按 ☁ 可以看到網址。
- 資料存在 Script Properties：`{ updatedAt, groups, names }`，以 `updatedAt` 較新者為準。「目前所在群組」每台裝置各自獨立，不同步。
- ☁ 面板有「⬆ 以這支手機為準上傳」「⬇ 用雲端覆蓋這支手機」兩個手動按鈕，另有分享連結 `…/stock-app/#sync=<網址>`，可讓新裝置自動完成設定。
- **改了 `sync.gs` 之後，使用者必須到「部署 → 管理部署作業 → ✎ → 版本：新版本」重新部署**，這樣網址不變。不要叫使用者「新增部署作業」，那會產生新網址。

## 行情資料來源（2026-10-09 實測）

證交所、櫃買中心、MIS、Yahoo 都**沒有開 CORS**，瀏覽器不能直接讀，所以要經使用者的 Apps Script 代理（`sync.gs` 的 `?url=`，只允許白名單網域）。

| 用途 | 來源 | 狀態 |
|------|------|------|
| 即時報價（主） | Yahoo 奇摩 `tw.stock.yahoo.com/_td-stock/api/resource/StockServices.stockList` 經 Apps Script | ✅ 5/5 成功，`exchangeDataDelayedBy: 0`，耗時 2～11 秒（App 逾時設 20 秒）。後綴一律用 `.TW`，上櫃股 Yahoo 會自動改成 `.TWO` |
| 即時報價（備援） | MIS `mis.twse.com.tw` 經 Apps Script | ❌ MIS 拒絕 Google 伺服器（0/10，錯誤「無法開啟網址」） |
| 上市收盤 | `www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data`（CSV，有 CORS） | ✅ 收盤後當天就更新 |
| 加權指數收盤 | `www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?response=json&type=IND`（有 CORS） | ✅ |
| 上櫃收盤 | `www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes` 經 Apps Script | ✅ |
| 舊備援 | `openapi.twse.com.tw` | ⚠️ 資料晚一天，欄位已改成中文 |
| 已失效 | corsproxy.io（403，要付費 key）、allorigins.win（逾時） | ❌ |

`refresh()` 的順序：Yahoo → MIS → `fetchFallback()`（收盤資料）。狀態列顯示資料的**實際日期**，避免把前一日資料標成今天。法人／信用分頁也經由 `fetchJsonList()` 走代理。

## 目前進度與待辦

- ✅ 多支手機共用自選股（已在兩支手機驗證，清單一致）
- ✅ 收盤價正確（已對照 10/08 收盤）
- ⏳ **待驗證：盤中即時報價**。使用者會在開盤後（9:00–13:30）回報：加權指數列右側應為綠色「● 時間」並持續更新；若顯示橘色「收盤資料」或價格停住，就要排查 Yahoo 經 Apps Script 的那一段（可以請使用者提供雲端網址來實測，不要寫進 repo）。
- Apps Script 配額：UrlFetch 每日 20,000 次。盤中每台手機約每 10～20 秒 1 次，兩台手機在額度內。

## 使用慣例

- 用繁體中文回覆。Python 一律用 `uv run` / `uvx`，不要用 pip。
- commit 訊息用英文；只 commit 本 repo 的檔案。
