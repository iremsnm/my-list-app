import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

# 副原料リストを事前読み込み
sub_df = pd.read_csv("/mnt/data/副原料リスト.csv")
sub_df = sub_df.set_index("副原料")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    st.markdown("---")

    # --- ジャンプ機能 ---
    jump_to = st.number_input("行番号を指定してジャンプ", min_value=1, max_value=len(df), step=1)
    if st.button("ジャンプ", key="jump_button"):
        for i in range(jump_to - 1):
            st.session_state.checked[i] = True
        st.rerun()

    st.markdown("---")

    # チェック状態を反映
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

    # --- 上側の追加表示 ---
    if start > 1:
        with st.expander("欄外5件"):
            extra_top_df = df.loc[max(1, start - 5):start - 1]
            for idx, row in extra_top_df.iterrows():
                text = f"{idx}. {row['item']}"
                if row["checked"]:
                    st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(text)

    # メイン表示
    for idx, row in sub_df_display.iterrows():
        base_text = f"{idx}. {row['item']}"
        extra_info = ""
        if row['item'] in sub_df.index:
            match = sub_df.loc[row['item']]
            extra_info = f"\n - E: {match['E']}\n - 属性: {match['属性']}\n - SP: {match['SP']}\n - 効果: {match['効果']}"

        full_text = base_text + extra_info

        if row["checked"]:
            st.markdown(f"<span style='color: gray; white-space: pre-wrap;'>{full_text}</span>", unsafe_allow_html=True)
        elif idx == first_unchecked:
            if st.button(base_text, key=idx):
                st.session_state.checked[idx - 1] = True
                st.rerun()
        else:
            st.markdown(full_text)

    # --- 下側の追加表示 ---
    if end < len(df):
        with st.expander("欄外5件"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                text = f"{idx}. {row['item']}"
                if row["checked"]:
                    st.markdown(f"<span style='color: gray;'>{text}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(text)

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    st.markdown("---")

    # --- 保存処理 ---
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

    # --- 読み込み ---
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")

    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            # フラグで無限ループ回避
            if "json_loaded_once" not in st.session_state:
                st.session_state.checked = loaded_state
                st.session_state.json_loaded_once = True
                st.rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")

    # --- 集計表の表示 ---
    st.markdown("---")
    st.markdown("### count")

    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary_df = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary_df["残"] = summary_df["必要数"] - summary_df["チェック済み"]
    summary_df = summary_df.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary_df, use_container_width=True)

    # 一度読み込んだらフラグを消す（次の読み込みに備える）
    if "json_loaded_once" in st.session_state:
        del st.session_state["json_loaded_once"]
