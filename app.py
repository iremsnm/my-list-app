import pandas as pd
import streamlit as st
import json
from io import StringIO
from datetime import datetime
import pytz
import base64


st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df = df.loc[start:end]

    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 工程**")

    for idx, row in sub_df.iterrows():
        text = f"{idx}. {row['item']}"
        if row["checked"]:
            st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
        elif idx == first_unchecked:
            
            if st.button(text, key=idx, help="クリックしてチェック", use_container_width=True):
                st.session_state.checked[idx - 1] = True
                st.rerun()

        else:
            st.markdown(text)

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- 保存リンク生成 ---
    st.markdown("---")
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    json_data = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False)

    # base64 エンコードしてダウンロードリンク生成
    b64 = base64.b64encode(json_data.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">保存</a>'
    st.markdown(href, unsafe_allow_html=True)

    # --- 読み込み（下部） ---
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")

    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")
