import pandas as pd
import streamlit as st
import json
from io import StringIO
from datetime import datetime
import pytz

st.title("check list")

# 📌 通常のブラウザで開くように案内
st.info("⚠️ JSON保存がうまくいかない場合は、Safari や Chrome など通常のブラウザで開いてください。")

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
            if st.button(text, key=idx):
                st.session_state.checked[idx - 1] = True
                st.rerun()
        else:
            st.markdown(text)

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- JSON状態のコピー用出力 ---
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y/%m/%d %H:%M:%S")
    st.markdown("### ✅ 現在のチェック状態を保存（手動コピー）")
    st.caption(f"保存日時: {now}")
    json_str = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False)
    st.text_area("以下をコピーして保存してください（メモ帳などに貼り付けて保存できます）", value=json_str, height=200)

    # --- 読み込み（下部に配置） ---
    st.markdown("---")
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")

    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")
