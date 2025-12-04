# 農業氣象一週預報視覺化

此專案使用中央氣象署農業氣象 API（`F-A0010-001.json`）資料，建立 SQLite 資料庫，並透過 Streamlit 提供互動式視覺化介面。

## 環境需求

- Python 3.9+
- 已安裝 `pip`

## 安裝步驟

在本專案目錄（與 `app.py`、`F-A0010-001.json` 同一層）執行：

```bash
pip install -r requirements.txt
```

## 執行應用程式

在專案目錄執行：

```bash
streamlit run app.py
```

終端機會顯示本機網址（通常為 `http://localhost:8501`），以瀏覽器開啟即可使用。

## 功能說明

- 讀取 `F-A0010-001.json`，自動建立/更新 `weather.db`（SQLite）。
- 儲存各地區一週逐日的：
  - 天氣描述
  - 最高氣溫
  - 最低氣溫
- Streamlit 介面：
  - 側邊欄選擇地區，或瀏覽全部地區資料。
  - 按鈕「重新從 JSON 匯入資料」可重建資料表並重新匯入。
  - 主畫面顯示：
    - 預報資料表格。
    - 最高/最低溫折線圖（依日期、地區）。
    - 各地區平均最高/最低溫長條圖。
    - 日溫差（最高溫 - 最低溫）折線圖。
    - 最高溫、最低溫面積圖。

## 檔案結構

- `F-A0010-001.json`：中央氣象署農業氣象一週預報 JSON 範例。
- `app.py`：建立 SQLite 資料庫並提供 Streamlit 視覺化介面。
- `weather.db`：程式執行後自動建立的 SQLite 資料庫。
- `requirements.txt`：Python 套件需求列表。
- `README.md`：專案說明文件。
