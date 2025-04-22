import streamlit as st
import pandas as pd
import os

SAVE_FILE = "checklist_status.csv"

# 初期読み込み
if "df" not in st.session_state:
    if os.path.exists(SAVE_FILE):
        st.session_state.df = pd.read_csv(SAVE_FILE, index_col=0)
    else:
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file, header=None, names=["item"])
            df["checked"] = False
            df.index = df.index + 1  # 行番号を1から
            st.session_state.df = df

df = st.session_state.df

# チェック状態の表示・操作
for idx, row in df.iterrows():
    if row["checked"]:
        st.markdown(f"<span style='color:gray'>{idx}. {row['item']}</span>", unsafe_allow_html=True)
    else:
        if st.button(f"{idx}. {row['item']}", key=idx):
            df.at[idx, "checked"] = True
            st.experimental_rerun()

# 残数表示
unchecked = df[~df["checked"]]
st.markdown(f"**残り: {len(unchecked)} 件**")

# 保存ボタン
if st.button("状態を保存"):
    df.to_csv(SAVE_FILE)
    st.success("状態を保存しました！")

# リセットボタン
if st.button("リセット"):
    df["checked"] = False
    st.success("チェック状態をリセットしました")
    st.experimental_rerun()
