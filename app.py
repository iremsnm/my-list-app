import pandas as pd
import streamlit as st
import json
from io import StringIO
from datetime import datetime
import pytz
import base64

st.set_page_config(layout="wide")
st.title("check list")

uploaded_file = st.file_uploader("チャートリストをアップロード", type=["csv"])
sub_material_file = st.file_uploader("情報用リストをアップロード", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index += 1
    sub_df = pd.read_csv(sub_material_file).set_index("副原料") if sub_material_file else pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)
    df["checked"] = st.session_state.checked

    tabs = st.tabs(["✅ チェックリスト", "📊 集計"])

    # -------------------------------
    # ✅ チェックリストタブ
    # -------------------------------
    with tabs[0]:
        checked_indices = [i for i, val in enumerate(df["checked"], 1) if val]
        latest_checked = checked_indices[-1] if checked_indices else 1
        try:
            first_unchecked = df.index[df["checked"] == False][0]
        except IndexError:
            first_unchecked = None

        start = max(latest_checked - 4, 1)
        end = min((first_unchecked or latest_checked) + 3, len(df))
        display_df = df.loc[start:end]

        with st.container():
            jump_to = st.number_input("行番号を指定してジャンプ", min_value=1, max_value=len(df), step=1)
            if st.button("ジャンプ", key="jump_button"):
                for i in range(jump_to - 1):
                    st.session_state.checked[i] = True
                st.rerun()
        st.markdown("---")

        show_extra_info = st.toggle("追加情報を表示", value=False)

        st.markdown(f"残り **{df['checked'].value_counts().get(False, 0)}** step")

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

        def render_item_card(idx, row):
            bg = "#f9f9f9"
            border = "solid 1px #ccc"
            color = "gray" if row["checked"] else "black"
            if row["checked"] and idx != latest_checked:
                previous_checked = checked_indices[:-1][-3:]
                if idx in previous_checked:
                    bg = "#d3ffd3"
            if idx == latest_checked:
                bg = "#d3f7ff"

            html = f"""
            <div style='background:{bg};border-radius:8px;border:{border};padding:12px;margin-bottom:10px;'>
                <div style='color:{color};font-weight:bold;'>{idx}. {row['item']}</div>
                {get_extra_info_html(row['item'])}
            </div>
            """
            return html

        if start > 1:
            with st.expander("前の5件"):
                for idx, row in df.loc[max(1, start - 5):start - 1].iterrows():
                    st.markdown(render_item_card(idx, row), unsafe_allow_html=True)

        for idx, row in display_df.iterrows():
            if idx == first_unchecked:
                if st.button(f"{idx}. {row['item']}", key=f"btn_{idx}", use_container_width=True):
                    st.session_state.checked[idx - 1] = True
                    st.rerun()
            else:
                st.markdown(render_item_card(idx, row), unsafe_allow_html=True)

        if end < len(df):
            with st.expander("次の5件"):
                for idx, row in df.loc[end + 1:min(end + 5, len(df))].iterrows():
                    st.markdown(render_item_card(idx, row), unsafe_allow_html=True)
        st.markdown("---")

        # 保存処理
        japan_tz = pytz.timezone("Asia/Tokyo")
        now = datetime.now(japan_tz).strftime("%Y%m%d_%H-%M-%S")
        filename = f"check_state_{now}.json"
        json_data = json.dumps(st.session_state.checked, indent=2, ensure_ascii=False)
        json_bytes = json_data.encode("utf-8")
        b64 = base64.b64encode(json_bytes).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="{filename}">一時保存</a>'
        st.markdown(href, unsafe_allow_html=True)

        json_file = st.file_uploader("中途データ読込", type=["json"], key="json")
        if json_file:
            json_str = StringIO(json_file.getvalue().decode("utf-8")).read()
            loaded = json.loads(json_str)
            if len(loaded) == len(df):
                st.session_state.checked = loaded
                st.rerun()
            else:
                st.warning("行数が一致しません")

        if st.button("リセット", help="チェックをリセット"):
            st.session_state.checked = [False] * len(df)
            st.rerun()

    # -------------------------------
    # 📊 集計タブ
    # -------------------------------
    with tabs[1]:
        st.markdown("集計")
        total = df["item"].value_counts().rename("必要数")
        checked = df[df["checked"]]["item"].value_counts().rename("チェック済み")
        summary = pd.concat([total, checked], axis=1).fillna(0).astype(int)
        summary["残"] = summary["必要数"] - summary["チェック済み"]

        st.dataframe(
            summary.reset_index().rename(columns={"index": "項目"}),
            use_container_width=True,
            hide_index=True
        )
