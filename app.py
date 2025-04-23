import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(page_title="Check List", layout="wide")
st.title("Check List")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

# CSS for card styling
st.markdown("""
    <style>
    .card {
        border: 1px solid #ccc;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 12px;
        transition: background-color 0.3s ease;
    }
    .card:hover {
        background-color: #f0f0f0;
        cursor: pointer;
    }
    .checked {
        background-color: #f8f8f8 !important;
        color: gray !important;
    }
    .extra-info {
        color: #999;
        font-size: 0.9em;
        margin-top: 6px;
    }
    .info-label {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file)
        sub_df = sub_df.set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    # --- トグルで副原料の情報を表示/非表示 ---
    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty:
            return ""
        if item in sub_df.index:
            match = sub_df.loc[item]
            return f"""
                <div class='extra-info'>
                    <span class='info-label'>E:</span> {match['E']}　
                    <span class='info-label'>属性:</span> {match['属性']}　
                    <span class='info-label'>SP:</span> {match['SP']}　
                    <span class='info-label'>効果:</span> {match['効果']}
                </div>
            """
        return ""

    st.markdown("---")
    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 工程**")

    # 表示用範囲の調整
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df_display = df.loc[start:end]

    # --- メイン表示 ---
    for idx, row in sub_df_display.iterrows():
        is_checked = row["checked"]
        card_class = "card checked" if is_checked else "card"
        info_html = get_extra_info(row["item"])

        if st.button(f"{idx}. {row['item']}", key=f"card_{idx}"):
            st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
            st.rerun()

        st.markdown(f"""
            <div class="{card_class}">
                <strong>{idx}. {row["item"]}</strong>
                {info_html}
            </div>
        """, unsafe_allow_html=True)

    # --- 欄外5件表示 ---
    if start > 1:
        with st.expander("欄外5件（前）"):
            extra_top_df = df.loc[max(1, start - 5):start - 1]
            for idx, row in extra_top_df.iterrows():
                card_class = "card checked" if row["checked"] else "card"
                info_html = get_extra_info(row["item"])
                if st.button(f"{idx}. {row['item']}", key=f"card_top_{idx}"):
                    st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
                    st.rerun()
                st.markdown(f"""
                    <div class="{card_class}">
                        <strong>{idx}. {row["item"]}</strong>
                        {info_html}
                    </div>
                """, unsafe_allow_html=True)

    if end < len(df):
        with st.expander("欄外5件（後）"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                card_class = "card checked" if row["checked"] else "card"
                info_html = get_extra_info(row["item"])
                if st.button(f"{idx}. {row['item']}", key=f"card_bottom_{idx}"):
                    st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
                    st.rerun()
                st.markdown(f"""
                    <div class="{card_class}">
                        <strong>{idx}. {row["item"]}</strong>
                        {info_html}
                    </div>
                """, unsafe_allow_html=True)

    # --- リセット ---
    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    st.markdown("---")

    # --- 保存 ---
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    json_bytes = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = BytesIO(json_bytes)
    st.download_button("一時保存", buffer, file_name=filename, mime="application/json")

    # --- 読み込み ---
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")
    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")

    # --- 集計表示 ---
    st.markdown("---")
    st.markdown("### 集計")
    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary_df = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary_df["残"] = summary_df["必要数"] - summary_df["チェック済み"]
    summary_df = summary_df.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary_df, use_container_width=True)
