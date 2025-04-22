import pandas as pd
import streamlit as st
import json
import os

# 保存ファイル名
STATE_FILE = "checklist_state.json"

# 状態保存用関数
def save_state(df):
    state = df[["item", "checked"]].to_dict(orient="records")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# 状態読み込み用関数
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        return pd.DataFrame(state)
    return None

# タイトル
st.title("チェックリストアプリ")

# CSVアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    saved_df = load_state()

    if saved_df is not None and len(saved_df) == len(df):
        df["checked"] = saved_df["checked"]
        st.session_state.checked = list(saved_df["checked"])
    else:
        if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
            st.session_state.checked = [False] * len(df)
        df["checked"] = st.session_state.checked

    # 最新のチェック済みインデックス
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    # 未チェックの最初
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    # 表示範囲（前後10件）
    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df = df.loc[start:end]

    # 残り件数
    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 件**")

    # 表示
    for idx, row in sub_df.iterrows():
        text = f"{idx}. {row['item']}"
        if row["checked"]:
            st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
        elif idx == first_unchecked:
            if st.button(text, key=idx):
                st.session_state.checked[idx - 1] = True
                df["checked"] = st.session_state.checked
                save_state(df)
                st.rerun()
        else:
            st.markdown(text)

    # 小さめのリセットボタン
    if st.button("🔄 リセット", help="チェックをすべて未チェックに戻します"):
        st.session_state.checked = [False] * len(df)
        df["checked"] = st.session_state.checked
        save_state(df)
        st.rerun()
