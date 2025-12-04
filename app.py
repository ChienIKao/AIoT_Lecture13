import json
import sqlite3
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "F-A0010-001.json"
DB_PATH = BASE_DIR / "weather.db"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            date TEXT NOT NULL,
            weather TEXT,
            weather_id TEXT,
            t_max REAL,
            t_min REAL
        );
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_forecast_region_date ON forecast(region, date);")
    conn.commit()


def reset_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS forecast;")
    conn.commit()
    init_db(conn)


def import_from_json(conn: sqlite3.Connection, data: dict) -> None:
    root = data.get("cwaopendata", {})
    resources = root.get("resources", {})
    resource = resources.get("resource", {})
    data_node = resource.get("data", {})
    agr_weather = data_node.get("agrWeatherForecasts", {})
    weather_forecasts = agr_weather.get("weatherForecasts", {})

    locations = weather_forecasts.get("location", [])

    rows = []
    for loc in locations:
        region = loc.get("locationName")
        we = loc.get("weatherElements", {})

        wx_daily = {d["dataDate"]: d for d in we.get("Wx", {}).get("daily", [])}
        max_daily = {d["dataDate"]: d for d in we.get("MaxT", {}).get("daily", [])}
        min_daily = {d["dataDate"]: d for d in we.get("MinT", {}).get("daily", [])}

        all_dates = sorted(set(wx_daily.keys()) | set(max_daily.keys()) | set(min_daily.keys()))

        for date in all_dates:
            wx = wx_daily.get(date, {})
            tmax = max_daily.get(date, {}).get("temperature")
            tmin = min_daily.get(date, {}).get("temperature")
            rows.append(
                (
                    region,
                    date,
                    wx.get("weather"),
                    wx.get("weatherid"),
                    float(tmax) if tmax is not None else None,
                    float(tmin) if tmin is not None else None,
                )
            )

    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO forecast (region, date, weather, weather_id, t_max, t_min) VALUES (?, ?, ?, ?, ?, ?);",
        rows,
    )
    conn.commit()


def ensure_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # If table is empty, auto-import from JSON
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM forecast;")
    count = cur.fetchone()[0]
    if count == 0 and JSON_PATH.exists():
        data = load_json(JSON_PATH)
        import_from_json(conn, data)

    return conn


def query_forecast(conn: sqlite3.Connection, region: str | None = None):
    cur = conn.cursor()
    if region:
        cur.execute(
            "SELECT region, date, weather, weather_id, t_max, t_min FROM forecast WHERE region = ? ORDER BY date;",
            (region,),
        )
    else:
        cur.execute(
            "SELECT region, date, weather, weather_id, t_max, t_min FROM forecast ORDER BY region, date;"
        )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def get_regions(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT region FROM forecast ORDER BY region;")
    return [r[0] for r in cur.fetchall()]


def main():
    st.set_page_config(page_title="農業氣象一週預報", layout="wide")

    st.title("農業氣象一週預報查詢")
    st.caption("資料來源：中央氣象署 F-A0010-001 JSON")

    conn = ensure_db()

    with st.sidebar:
        st.header("設定")
        if st.button("重新從 JSON 匯入資料"):
            reset_db(conn)
            data = load_json(JSON_PATH)
            import_from_json(conn, data)
            st.success("已重新匯入 JSON 資料")

        regions = ["全部"] + get_regions(conn)
        selected_region = st.selectbox("選擇地區", regions)

    region_filter = None if selected_region == "全部" else selected_region
    data = query_forecast(conn, region_filter)

    if not data:
        st.warning("目前資料庫沒有任何資料。請確認 JSON 檔案是否存在，或在側邊欄重新匯入。")
        return

    import pandas as pd

    df = pd.DataFrame(data)

    st.subheader("預報列表")
    st.dataframe(df, use_container_width=True)

    st.subheader("溫度走勢")
    col1, col2 = st.columns(2)

    with col1:
        st.line_chart(df, x="date", y="t_max", color="region")
    with col2:
        st.line_chart(df, x="date", y="t_min", color="region")

    st.subheader("各地區平均溫度比較")
    agg = (
        df.groupby("region", as_index=False)[["t_max", "t_min"]]
        .mean(numeric_only=True)
        .sort_values("t_max", ascending=False)
    )
    st.bar_chart(agg, x="region", y=["t_max", "t_min"])

    st.subheader("日溫差變化")
    df_diff = df.copy()
    df_diff["diurnal_range"] = df_diff["t_max"] - df_diff["t_min"]
    st.line_chart(df_diff, x="date", y="diurnal_range", color="region")

    st.subheader("最高/最低溫分布")
    col3, col4 = st.columns(2)
    with col3:
        st.area_chart(df, x="date", y="t_max", color="region")
    with col4:
        st.area_chart(df, x="date", y="t_min", color="region")


if __name__ == "__main__":
    main()
