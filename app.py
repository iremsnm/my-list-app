import pandas as pd
import streamlit as st
import json
import os

# タイトル
st.title("チェックリストアプリ")

# 状態保存ファイル名
STATE_FILE = 'checklist_state.json'

# チェック状態をJSONファイルに保存する関数
def save_state(checked_list):
    with open(STATE_FILE, 'w') as f:
        json.dump(checked_list, f)

# JSONファイルからチェック状態を読み込む関数
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

# CSVファイルのアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # データフレームとして読み込み
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1  # 行番号を1から開始

    # セッションステート初期化 or 読み込み
    loaded = load_state()
    if "checked" not in st.session_state:
        if loaded and len(loaded) == len(df):
            st.session_state.checked = loaded
        else:
            st.session_state.checked = [False] * len(df)

    # チェック状態を反映
    df["checked"] = st.session_state.checked

    # 最新のチェック済みインデックスを取得
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    # 未チェックの最初のインデックスを取得
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    # 表示範囲の計算（最新チェックの前後5件）
    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df = df.loc[start:end]

    # 残り件数の表示
    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**残り: {unchecked_count} 件**")

    # 各行の表示
    for idx, row in sub_df.iterrows():
        text = f"{idx}. {row['item']}"
        if row["checked"]:
            st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
        elif idx == first_unchecked:
            if st.button(text, key=idx):
                st.session_state.checked[idx - 1] = True
                save_state(st.session_state.checked)
                st.experimental_rerun()
        else:
            st.markdown(text)

    # リセットボタン
    if st.button("リセット", help="チェックをすべて未チェックに戻します"):
        st.session_state.checked = [False] * len(df)
        save_state(st.session_state.checked)
        st.experimental_rerun()
