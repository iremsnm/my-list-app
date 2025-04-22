import pandas as pd
import streamlit as st
import json
from io import StringIO

st.title("check list")

# --- CSVファイルアップロード ---
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

# --- 初期化・状態読み込み ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    # チェック状態の初期化
    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    # --- チェック済み・未チェックの処理 ---
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df = df.loc[start:end]

    # --- 残数表示 ---
    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 件**")

    # --- チェック表示 ---
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

    # --- リセット ---
    if st.button("リセット", help="チェックをすべて未チェックに戻します"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- JSON保存ボタン ---
    st.download_button(
        label="チェック状態を保存（JSON）",
        data=json.dumps(st.session_state.checked, indent=2),
        file_name="check_state.json",
        mime="application/json"
    )

    # --- JSON読み込み（リセットボタンの下に移動）---
    st.markdown("---")
    st.subheader("中途データ読み込み")
    json_file = st.file_uploader("中途データ読み込み（任意）", type=["json"], key="json")

    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            st.session_state.checked = loaded_state
            st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しないため、チェック状態を無視しました。")
