import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.title("check list")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"] )
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

if uploaded_file is not None:
    # メインCSV読み込み
    df = pd.read_csv(uploaded_file, header=None, names=["item"] )
    df.index = df.index + 1

    # 副原料CSV読み込み
    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file).set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    # セッションステート初期化
    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)
    df["checked"] = st.session_state.checked

    # --- ジャンプ機能 ---
    st.markdown("---")
    jump_to = st.number_input("行番号を指定してジャンプ", min_value=1, max_value=len(df), step=1)
    if st.button("ジャンプ", key="jump_button"):
        for i in range(jump_to - 1):
            st.session_state.checked[i] = True
        st.rerun()
    st.markdown("---")

    # 状態反映
    df["checked"] = st.session_state.checked
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1
    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    view_range = df.loc[start:end]

    # レイアウト: 左にチェックリスト、右に詳細情報
    col1, col2 = st.columns([3, 2])

    with col1:
        # 残りカウント
        unchecked_count = df["checked"].value_counts().get(False, 0)
        st.markdown(f"**残り: {unchecked_count} 工程**")

        # 上側5件 (欄外)
        if start > 1:
            with st.expander("欄外5件 上部"):
                extra_top = df.loc[max(1, start-5):start-1]
                for idx, row in extra_top.iterrows():
                    text = f"{idx}. {row['item']}"
                    if row['checked']:
                        st.markdown(f"<span style='color: gray'>{text}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(text)

        # メイン表示レンジ
        for idx, row in view_range.iterrows():
            base_text = f"{idx}. {row['item']}"
            if row['checked']:
                st.markdown(f"<span style='color: gray'>{base_text}</span>", unsafe_allow_html=True)
            elif idx == first_unchecked:
                if st.button(base_text, key=idx):
                    st.session_state.checked[idx - 1] = True
                    st.rerun()
            else:
                st.markdown(base_text)

        # 下側5件 (欄外)
        if end < len(df):
            with st.expander("欄外5件 下部"):
                extra_bot = df.loc[end+1:min(end+5, len(df))]
                for idx, row in extra_bot.iterrows():
                    text = f"{idx}. {row['item']}"
                    if row['checked']:
                        st.markdown(f"<span style='color: gray'>{text}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(text)

        # リセットボタン
        if st.button("リセット", help="チェック状況をリセット"):
            st.session_state.checked = [False] * len(df)
            st.rerun()

    with col2:
        st.markdown("---")
        st.header("詳細情報")
        # 現在表示中のアイテムに対応する詳細を取得
        visible_items = view_range['item'].tolist()
        if not sub_df.empty:
            details = sub_df.loc[sub_df.index.intersection(visible_items)]
            if not details.empty:
                # インデックスを"項目"列に戻す
                details = details.reset_index().rename(columns={"副原料": "項目"})
                st.dataframe(details, use_container_width=True)
            else:
                st.markdown("表示範囲内に副原料リストの該当項目はありません。")
        else:
            st.markdown("副原料リストをアップロードすると詳細が表示されます。")

    # --- 保存と読み込み、集計表 ---
    st.markdown("---")
    # 保存
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    buffer = BytesIO(json.dumps(st.session_state.checked, ensure_ascii=False, indent=2).encode())
    st.download_button("一時保存", data=buffer, file_name=filename, mime="application/json")

    # 読み込み
    json_file = st.file_uploader("中途データ読込み", type=["json"], key="json")
    if json_file is not None:
        loaded = json.loads(StringIO(json_file.getvalue().decode()).read())
        if len(loaded) == len(df) and "json_loaded_once" not in st.session_state:
            st.session_state.checked = loaded
            st.session_state.json_loaded_once = True
            st.rerun()
        elif len(loaded) != len(df):
            st.warning("JSONとCSVの行数が一致しません。")

    # 集計表
    st.markdown("---")
    st.markdown("### count")
    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary["残"] = summary["必要数"] - summary["チェック済み"]
    summary = summary.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary, use_container_width=True)
