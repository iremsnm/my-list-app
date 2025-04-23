import streamlit as st
import pandas as pd
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

# ページ設定
st.set_page_config(layout="wide")

# スタイル
st.markdown("""
    <style>
        .card-container {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .card {
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 0.75rem;
            background-color: #fff;
            transition: background-color 0.3s, opacity 0.3s;
            cursor: pointer;
        }
        .card.checked {
            background-color: #f0f0f0;
            color: #999;
            text-decoration: line-through;
        }
        .card:hover {
            background-color: #f9f9f9;
        }
        .card .info-line {
            margin-top: 0.25rem;
            font-size: 0.85rem;
            color: #666;
        }
        @media screen and (max-width: 768px) {
            .card {
                padding: 1rem;
                font-size: 0.95rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("カード式チェックリスト")

# CSVファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

if uploaded_file is not None:
    # メインリスト
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1  # インデックス調整

    # 副原料リスト
    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file)
        sub_df = sub_df.set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    # チェック状態の初期化
    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    # ON/OFFトグル（副原料の表示）
    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty:
            return ""
        if item in sub_df.index:
            match = sub_df.loc[item]
            return f"<span style='color: lightgray;'>（E: {match['E']}, 属性: {match['属性']}, SP: {match['SP']}, 効果: {match['効果']}）</span>"
        return ""

    # --- チェックボタンとリストの表示 ---
    def display_card(idx, item):
        base_text = f"{idx}. {item}"
        extra_info_html = get_extra_info(item)
        full_html = base_text + " " + extra_info_html

        # チェック状態の反映
        card_class = "card"
        if st.session_state.checked[idx - 1]:
            card_class += " checked"

        # カードの作成
        if st.button(full_html, key=idx):
            st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
            st.rerun()

        # ここでカードにスタイルを適用
        st.markdown(f'<div class="{card_class}">{full_html}</div>', unsafe_allow_html=True)

    # カード形式でリストを表示
    st.markdown("<div class='card-container'>", unsafe_allow_html=True)
    for idx, row in df.iterrows():
        display_card(idx, row["item"])
    st.markdown("</div>", unsafe_allow_html=True)

    # チェック状況リセット
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

    if "json_loaded_once" in st.session_state:
        del st.session_state["json_loaded_once"]
