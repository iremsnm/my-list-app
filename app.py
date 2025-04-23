import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(page_title="Check List", layout="wide")
st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    sub_df = pd.read_csv(sub_material_file).set_index("副原料") if sub_material_file is not None else pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty or item not in sub_df.index:
            return ""
        match = sub_df.loc[item]
        return f"E: {match['E']} | 属性: {match['属性']} | SP: {match['SP']} | 効果: {match['効果']}"

    st.markdown("---")

    # 行をクリックしてチェック状態を切り替える
    def render_card(idx, row):
        col1, col2 = st.columns([3, 7])
        with col1:
            # 状態保存用フォームで rerun 抑制
            with st.form(f"form_{idx}"):
                if st.form_submit_button("", use_container_width=True):
                    st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
        with col2:
            extra = get_extra_info(row["item"])
            card_style = (
                "background-color: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 5px; cursor: pointer;"
            )
            text_color = "gray" if row["checked"] else "black"
            content = f"<div style='{card_style}; color:{text_color}'><b>{idx}. {row['item']}</b><br><small>{extra}</small></div>"
            st.markdown(content, unsafe_allow_html=True)

    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df_display = df.loc[start:end]

    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 工程**")

    # --- 上側表示 ---
    if start > 1:
        with st.expander("欄外5件"):
            extra_top_df = df.loc[max(1, start - 5):start - 1]
            for idx, row in extra_top_df.iterrows():
                render_card(idx, row)

    # --- メイン表示 ---
    for idx, row in sub_df_display.iterrows():
        render_card(idx, row)

    # --- 下側表示 ---
    if end < len(df):
        with st.expander("欄外5件"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                render_card(idx, row)

    # --- リセット ---
    if st.button("リセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    st.markdown("---")

    # --- 保存処理 ---
    now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    buffer = BytesIO(json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8"))
    st.download_button("一時保存", data=buffer, file_name=filename, mime="application/json")

    # --- 読み込み処理 ---
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")
    if json_file is not None:
        loaded_state = json.load(json_file)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")

    # --- 集計表示 ---
    st.markdown("---")
    st.markdown("### count")
    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary_df = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary_df["残"] = summary_df["必要数"] - summary_df["チェック済み"]
    summary_df = summary_df.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary_df, use_container_width=True)
