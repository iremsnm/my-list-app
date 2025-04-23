import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.title("✅ チェックリスト")

uploaded_file = st.file_uploader("📄 CSVファイルをアップロード", type=["csv"])
sub_material_file = st.file_uploader("🧂 副原料リスト（オプション）", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index += 1

    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file).set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    show_extra_info = st.toggle("🔍 副原料の詳細表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty or item not in sub_df.index:
            return ""
        match = sub_df.loc[item]
        return (
            f"<br><span style='font-size: 0.8em; color: gray;'>"
            f"E: {match['E']} | 属性: {match['属性']} | SP: {match['SP']} | 効果: {match['効果']}</span>"
        )

    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"### 🧮 残り工程数: {unchecked_count}")

    # 表示範囲の調整
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    main_display_df = df.loc[start:end]

    def render_card(idx, row):
        extra = get_extra_info(row["item"])
        card_style = (
            "background-color: #f0f0f0;" if row["checked"] else "background-color: #ffffff;"
        )
        text_color = "gray" if row["checked"] else "black"
        html = f"""
            <div style='border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px; {card_style} cursor: pointer;' onclick="fetch('/?card_click={idx}', {{method: 'GET'}})">
                <span style='font-size: 1rem; color: {text_color};'><strong>{idx}. {row["item"]}</strong></span>
                {extra}
            </div>
        """
        return html

    st.markdown("---")
    # JavaScript hack to handle card clicks
    query_params = st.experimental_get_query_params()
    if "card_click" in query_params:
        clicked_idx = int(query_params["card_click"][0])
        st.session_state.checked[clicked_idx - 1] = not st.session_state.checked[clicked_idx - 1]
        st.experimental_set_query_params()  # clear query
        st.rerun()

    # 2カラムレイアウト：左にカード、右に表
    col1, col2 = st.columns([2, 3])
    with col1:
        for idx, row in main_display_df.iterrows():
            st.markdown(render_card(idx, row), unsafe_allow_html=True)

    with col2:
        table_data = []
        for idx, row in main_display_df.iterrows():
            if show_extra_info and row["item"] in sub_df.index:
                d = sub_df.loc[row["item"]]
                table_data.append({
                    "行": idx,
                    "項目": row["item"],
                    "E": d["E"],
                    "属性": d["属性"],
                    "SP": d["SP"],
                    "効果": d["効果"],
                    "状態": "✔️" if row["checked"] else "❌"
                })
        if table_data:
            table_df = pd.DataFrame(table_data)
            table_df_style = table_df.style.applymap(
                lambda val: "color: gray;" if val == "✔️" else ""
            )
            st.dataframe(table_df_style, use_container_width=True)

    # --- リセットボタン ---
    if st.button("🔄 チェックをリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- 保存処理 ---
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    json_bytes = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button("💾 一時保存", data=BytesIO(json_bytes), file_name=filename, mime="application/json")

    # --- 読み込み処理 ---
    json_file = st.file_uploader("📥 状態読込（json）", type=["json"])
    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONファイルの行数が一致しません。")

