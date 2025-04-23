import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

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

    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty:
            return ""
        if item in sub_df.index:
            match = sub_df.loc[item]
            return f"属性: {match['属性']}  |  E: {match['E']}<br><b>SP:</b> {match['SP']}  |  <b>効果:</b> {match['効果']}"
        return ""

    # ジャンプ機能
    jump_to = st.number_input("行番号を指定してジャンプ", min_value=1, max_value=len(df), step=1)
    if st.button("ジャンプ", key="jump_button"):
        for i in range(jump_to - 1):
            st.session_state.checked[i] = True
        st.rerun()

    df["checked"] = st.session_state.checked
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

    def render_item_card(idx, row):
        col1, col2 = st.columns([1, 3])
        with col1:
            if not row["checked"] and idx == first_unchecked:
                if st.button(f"{idx}. {row['item']}", key=f"btn_{idx}", use_container_width=True):
                    st.session_state.checked[idx - 1] = True
                    st.rerun()
            else:
                st.markdown("&nbsp;", unsafe_allow_html=True)
        with col2:
            checked_class = "color: gray;" if row["checked"] else ""
            info_html = get_extra_info(row["item"])
            st.markdown(f"""
                <div style='border: 1px solid #ddd; border-radius: 8px; padding: 8px; margin-bottom: 6px; {checked_class}'>
                    <strong>{idx}. {row['item']}</strong><br>
                    <span style='font-size: 0.85em;'>{info_html}</span>
                </div>
            """, unsafe_allow_html=True)

    for idx, row in sub_df_display.iterrows():
        render_item_card(idx, row)

    if start > 1:
        with st.expander("欄外5件（前）"):
            extra_top_df = df.loc[max(1, start - 5):start - 1]
            for idx, row in extra_top_df.iterrows():
                render_item_card(idx, row)

    if end < len(df):
        with st.expander("欄外5件（後）"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                render_item_card(idx, row)

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # 保存
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    json_bytes = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = BytesIO(json_bytes)

    st.download_button(
        label="一時保存",
        data=buffer,
        file_name=filename,
        mime="application/json"
    )

    # 読み込み
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")
    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            if "json_loaded_once" not in st.session_state:
                st.session_state.checked = loaded_state
                st.session_state.json_loaded_once = True
                st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")

    st.markdown("---")
    st.markdown("### count")
    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary_df = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary_df["残"] = summary_df["必要数"] - summary_df["チェック済み"]
    summary_df = summary_df.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary_df, use_container_width=True)

    if "json_loaded_once" in st.session_state:
        del st.session_state["json_loaded_once"]
