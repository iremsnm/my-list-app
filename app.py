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

    # 表示領域を2カラム（左にカードリスト、右に表）に分ける
    col1, col2 = st.columns([2, 1])

    with col1:
        for idx, row in df.iterrows():
            item = row["item"]
            checked = st.session_state.checked[idx - 1]

            card_style = """
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 10px;
                cursor: pointer;
                border: 1px solid #ccc;
                transition: 0.2s all;
            """

            if checked:
                card_style += "background-color: #eee; color: #999;"
            else:
                card_style += "background-color: white; color: black;"

            card_html = f"""
                <div onclick="fetch('/_stcore/rerun', {{method: 'POST'}})"
                    style="{card_style}" 
                    id="card-{idx}">
                    <b>{idx}. {item}</b>
                    {get_extra_info(item)}
                </div>
                <script>
                    const el = document.getElementById("card-{idx}");
                    el.addEventListener("click", () => {{
                        fetch("/", {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/json"
                            }},
                            body: JSON.stringify({{"
