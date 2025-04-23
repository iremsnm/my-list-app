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
    df.index += 1

    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file).set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty or item not in sub_df.index:
            return ""
        match = sub_df.loc[item]
        return f"""
            <div style='font-size: 12px; color: gray; margin-top: 5px;'>
                E: {match['E']} / 属性: {match['属性']}<br>
                SP: {match['SP']}<br>
                効果: {match['効果']}
            </div>
        """

    st.markdown("---")
    unchecked_count = st.session_state.checked.count(False)
    st.markdown(f"**残り: {unchecked_count} 工程**")

    col1, col2 = st.columns([2, 1])

    with col1:
        for idx, row in df.iterrows():
            item = row["item"]
            checked = st.session_state.checked[idx - 1]

            card_color = "#eee" if checked else "white"
            text_color = "#999" if checked else "black"

            card_html = f"""
                <div style='
                    background-color: {card_color};
                    color: {text_color};
                    padding: 12px;
                    margin-bottom: 10px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                '>
                    <b>{idx}. {item}</b>
                    {get_extra_info(item)}
                </div>
            """

            if st.button(f"　", key=f"card_{idx}"):  # invisible label
                st.session_state.checked[idx - 1] = not checked
                st.rerun()

            st.markdown(card_html, unsafe_allow_html=True)

    with col2:
        table_data = []
        for idx, row in df.iterrows():
            item = row["item"]
            if item in sub_df.index:
                info = sub_df.loc[item]
                table_data.append({
                    "No.": idx,
                    "副原料": item,
                    "E": info["E"],
                    "属性": info["属性"],
                    "SP": info["SP"],
                    "効果": info["効果"],
                    "状態": "済" if st.session_state.checked[idx - 1] else ""
                })

        if table_data:
            info_df = pd.DataFrame(table_data)
            st.dataframe(info_df, use_container_width=True)

    st.markdown("---")

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()
