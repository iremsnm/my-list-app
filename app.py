import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.title("📋 Check List")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

# CSV 読み込み
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index += 1

    # 副原料データ読み込み
    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file).set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    # --- 関数定義 ---
    def get_extra_info(item):
        if show_extra_info and not sub_df.empty and item in sub_df.index:
            row = sub_df.loc[item]
            return f"""
                <div style='color: lightgray; font-size: 0.8em; margin-top: 4px'>
                E: {row['E']} | 属性: {row['属性']} | SP: {row['SP']} | 効果: {row['効果']}
                </div>"""
        return ""

    def render_card(idx, item, checked):
        extra_info = get_extra_info(item)
        card_color = "#f0f0f0" if checked else "#ffffff"
        text_color = "gray" if checked else "black"
        shadow = "0 0 5px rgba(0,0,0,0.1)" if not checked else "none"

        card_html = f"""
        <div style='
            background-color: {card_color};
            color: {text_color};
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 8px;
            box-shadow: {shadow};
            cursor: pointer;
            border: 1px solid #ddd;
        '
        onclick="fetch('/?check={idx}', {{method: 'POST'}}).then(() => window.location.reload())"
        >
            <b>{idx}. {item}</b>
            {extra_info}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # --- リストの描画 ---
    df["checked"] = st.session_state.checked
    unchecked_count = df["checked"].value_counts().get(False, 0)
    st.markdown(f"**✅ 残り: {unchecked_count} 工程**")

    for idx, row in df.iterrows():
        render_card(idx, row["item"], row["checked"])

    # --- 状態更新用の処理（手動POST代替） ---
    query_params = st.experimental_get_query_params()
    if "check" in query_params:
        idx = int(query_params["check"][0])
        st.session_state.checked[idx - 1] = not st.session_state.checked[idx - 1]
        st.experimental_set_query_params()  # リロード後に削除

    # --- リセットボタン ---
    if st.button("🔁 リセット"):
        st.session_state.checked = [False] * len(df)
        st.experimental_rerun()

    # --- 一時保存と読み込み ---
    st.markdown("---")
    st.markdown("### 💾 一時保存／読込み")

    now = datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    buffer = BytesIO(json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8"))

    st.download_button("⬇️ ダウンロード", buffer, file_name=filename, mime="application/json")

    json_file = st.file_uploader("⬆️ JSON読込み", type=["json"], key="json")
    if json_file:
        loaded = json.load(json_file)
        if len(loaded) == len(df):
            st.session_state.checked = loaded
            st.experimental_rerun()
        else:
            st.warning("JSONとCSVの行数が一致しません。")
