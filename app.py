import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(layout="wide")  # ワイド表示でスマホ対応
st.title("📋 チェックリスト")

uploaded_file = st.file_uploader("📄 メインCSVファイルをアップロード", type=["csv"])
sub_material_file = st.file_uploader("🧪 副原料リストをアップロード", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index += 1

    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file)
        sub_df = sub_df.set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    show_extra_info = st.toggle("👁️ 副原料の追加情報を表示", value=True)

    def get_extra_info_row(item):
        if not show_extra_info or sub_df.empty or item not in sub_df.index:
            return None
        return sub_df.loc[item]

    def render_info_table(idx, item, checked):
        info = get_extra_info_row(item)
        if info is None:
            return

        style = "color: gray;" if checked else ""
        table = f"""
        <table style='width: 100%; font-size: 14px; border: 1px solid #ccc; border-radius: 8px; margin-top: 0.25rem;'>
          <tr style='{style}'>
            <td style='padding: 4px; width: 20%;'><b>E</b></td><td style='padding: 4px;'>{info['E']}</td>
          </tr>
          <tr style='{style}'>
            <td style='padding: 4px;'><b>属性</b></td><td style='padding: 4px;'>{info['属性']}</td>
          </tr>
          <tr style='{style}'>
            <td style='padding: 4px;'><b>SP</b></td><td style='padding: 4px;'>{info['SP']}</td>
          </tr>
          <tr style='{style}'>
            <td style='padding: 4px;'><b>効果</b></td><td style='padding: 4px;'>{info['効果']}</td>
          </tr>
        </table>
        """
        st.markdown(table, unsafe_allow_html=True)

    # --- ジャンプ機能 ---
    jump_to = st.number_input("🔎 行番号ジャンプ", min_value=1, max_value=len(df), step=1)
    if st.button("ジャンプ", key="jump_button"):
        for i in range(jump_to - 1):
            st.session_state.checked[i] = True
        st.rerun()

    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    sub_df_display = df.loc[start:end]

    st.markdown(f"🧮 **残り: {df['checked'].value_counts().get(False, 0)} 工程**")

    # --- 上側の欄外表示 ---
    if start > 1:
        with st.expander("⬆️ 上側5件"):
            extra_top_df = df.loc[max(1, start - 5):start - 1]
            for idx, row in extra_top_df.iterrows():
                col1, col2 = st.columns([1.5, 3])
                with col1:
                    if row["checked"]:
                        st.markdown(f"<span style='color: gray;'>{idx}. {row['item']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"{idx}. {row['item']}")
                with col2:
                    render_info_table(idx, row["item"], row["checked"])

    # --- メインリスト表示 ---
    for idx, row in sub_df_display.iterrows():
        col1, col2 = st.columns([1.5, 3])
        with col1:
            if row["checked"]:
                st.markdown(f"<span style='color: gray;'>{idx}. {row['item']}</span>", unsafe_allow_html=True)
            elif idx == first_unchecked:
                if st.button(f"{idx}. {row['item']}", key=idx):
                    st.session_state.checked[idx - 1] = True
                    st.rerun()
            else:
                st.markdown(f"{idx}. {row['item']}")
        with col2:
            render_info_table(idx, row["item"], row["checked"])

    # --- 下側の欄外表示 ---
    if end < len(df):
        with st.expander("⬇️ 下側5件"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                col1, col2 = st.columns([1.5, 3])
                with col1:
                    if row["checked"]:
                        st.markdown(f"<span style='color: gray;'>{idx}. {row['item']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"{idx}. {row['item']}")
                with col2:
                    render_info_table(idx, row["item"], row["checked"])

    if st.button("🔄 チェックをリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    # --- 保存 ---
    japan_tz = pytz.timezone('Asia/Tokyo')
    now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
    filename = f"check_state_{now}.json"
    buffer = BytesIO(json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8"))

    st.download_button("💾 一時保存", data=buffer, file_name=filename, mime="application/json")

    # --- 読み込み ---
    json_file = st.file_uploader("📥 中途データ読込み", type=["json"], key="json")
    if json_file is not None:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded_state = json.loads(json_str)
        if len(loaded_state) == len(df):
            if "json_loaded_once" not in st.session_state:
                st.session_state.checked = loaded_state
                st.session_state.json_loaded_once = True
                st.rerun()
        else:
            st.warning("⚠️ JSONとCSVの行数が一致しません。")

    # --- 集計表 ---
    st.markdown("---")
    st.markdown("### 📊 カウント")

    total_counts = df["item"].value_counts().rename("必要数")
    checked_counts = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary_df = pd.concat([total_counts, checked_counts], axis=1).fillna(0).astype(int)
    summary_df["残"] = summary_df["必要数"] - summary_df["チェック済み"]
    summary_df = summary_df.reset_index().rename(columns={"index": "項目"})
    st.dataframe(summary_df, use_container_width=True)

    if "json_loaded_once" in st.session_state:
        del st.session_state["json_loaded_once"]
