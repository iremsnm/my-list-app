import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    # --- 行ジャンプ機能 ---
    jump_to = st.number_input("行番号を指定してジャンプ（1〜{}）".format(len(df)), min_value=1, max_value=len(df), value=1)
    if "jump_index" not in st.session_state:
        st.session_state.jump_index = jump_to

    if st.button("ジャンプする"):
        st.session_state.jump_index = jump_to

    # 表示範囲の調整
    base_index = st.session_state.jump_index
    start = max(base_index - 5, 1)
    end = min(base_index + 5, len(df))
    sub_df = df.loc[start:end]

    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 工程**")

    # チェック表示
    for idx, row in sub_df.iterrows():
        text = f"{idx}. {row['item']}"
        if row["checked"]:
            st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
        elif idx == df[~df["checked"]].index.min():
            if st.button(text, key=f"check_{idx}"):
                st.session_state.checked[idx - 1] = True
                st.rerun()
        else:
            st.markdown(text)

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- 保存処理（日本時間付きファイル名） ---
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    json_bytes = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = BytesIO(json_bytes)

    st.download_button(
        label="中途データを生成・保存",
        data=buffer,
        file_name=filename,
        mime="application/json"
    )

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
