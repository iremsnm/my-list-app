import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.title("📋 チェックリスト（副原料付き）")

uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロード", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index += 1

    sub_df = pd.read_csv(sub_material_file).set_index("副原料") if sub_material_file else pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info_html(item):
        if not show_extra_info or sub_df.empty or item not in sub_df.index:
            return ""
        match = sub_df.loc[item]
        return (
            f"<div style='color: #888; font-size: 0.85em; margin-top: 4px;'>"
            f"<b>E:</b> {match['E']} &nbsp;|&nbsp; "
            f"<b>属性:</b> {match['属性']} &nbsp;|&nbsp; "
            f"<b>SP:</b> {match['SP']} &nbsp;|&nbsp; "
            f"<b>効果:</b> {match['効果']}</div>"
        )

    # 表示範囲の決定
    checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
    latest_checked = checked_indices[-1] if checked_indices else 1

    try:
        first_unchecked = df.index[df["checked"] == False][0]
    except IndexError:
        first_unchecked = None

    start = max(latest_checked - 5, 1)
    end = min((first_unchecked or latest_checked) + 5, len(df))
    display_df = df.loc[start:end]

    st.markdown(f"🟡 残り **{df['checked'].value_counts().get(False, 0)}** 件")

    # 表示用関数
    def render_item_card(idx, row):
        bg = "#f9f9f9"
        border = "solid 1px #ccc"
        color = "gray" if row["checked"] else "black"
        html = f"""
        <div style='background:{bg};border-radius:8px;border:{border};padding:12px;margin-bottom:10px;'>
            <div style='color:{color};font-weight:bold;'>{idx}. {row['item']}</div>
            {get_extra_info_html(row['item'])}
        </div>
        """
        return html

    # メイン表示
    for idx, row in display_df.iterrows():
        if idx == first_unchecked:
            if st.button(f"{idx}. {row['item']}", key=f"btn_{idx}", use_container_width=True):
                st.session_state.checked[idx - 1] = True
                st.rerun()
        else:
            st.markdown(render_item_card(idx, row), unsafe_allow_html=True)

    # 上下欄外表示
    def render_outside_df(df_part):
        for idx, row in df_part.iterrows():
            st.markdown(render_item_card(idx, row), unsafe_allow_html=True)

    if start > 1:
        with st.expander("⬆️ 前の5件"):
            render_outside_df(df.loc[max(1, start - 5):start - 1])

    if end < len(df):
        with st.expander("⬇️ 次の5件"):
            render_outside_df(df.loc[end + 1:min(end + 5, len(df))])

    if st.button("🔄 リセット", help="チェックをリセットします"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    st.markdown("---")

    # 保存・読込機能
    now = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y%m%d_%H-%M-%S")
    json_bytes = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button("💾 一時保存", data=BytesIO(json_bytes), file_name=f"check_state_{now}.json")

    json_file = st.file_uploader("🔁 JSON読込", type=["json"], key="json")
    if json_file:
        json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
        loaded = json.loads(json_str)
        if len(loaded) == len(df):
            st.session_state.checked = loaded
            st.rerun()
        else:
            st.warning("行数が一致しません")

    # 集計表示
    st.markdown("---")
    st.markdown("📊 **集計表**")
    total = df["item"].value_counts().rename("必要数")
    checked = df[df["checked"]]["item"].value_counts().rename("チェック済み")
    summary = pd.concat([total, checked], axis=1).fillna(0).astype(int)
    summary["残"] = summary["必要数"] - summary["チェック済み"]
    st.dataframe(summary.reset_index().rename(columns={"index": "項目"}), use_container_width=True)
