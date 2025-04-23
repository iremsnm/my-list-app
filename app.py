import pandas as pd
import streamlit as st
import json
from io import StringIO, BytesIO
from datetime import datetime
import pytz

st.title("check list")

uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
sub_material_file = st.file_uploader("副原料リストをアップロードしてください", type=["csv"], key="sub_material")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, header=None, names=["item"])
    df.index = df.index + 1

    if sub_material_file is not None:
        sub_df = pd.read_csv(sub_material_file)
        sub_df = sub_df.set_index("副原料")
    else:
        sub_df = pd.DataFrame()

    if "checked" not in st.session_state or len(st.session_state.checked) != len(df):
        st.session_state.checked = [False] * len(df)

    df["checked"] = st.session_state.checked

    st.markdown("---")
    show_extra_info = st.toggle("副原料の追加情報を表示", value=True)

    def get_extra_info(item):
        if not show_extra_info or sub_df.empty:
            return ""
        if item in sub_df.index:
            match = sub_df.loc[item]
            return f"E: {match['E']}, 属性: {match['属性']}, SP: {match['SP']}, 効果: {match['効果']}"
        return ""

    jump_to = st.number_input("行番号を指定してジャンプ", min_value=1, max_value=len(df), step=1)
    if st.button("ジャンプ", key="jump_button"):
        for i in range(jump_to - 1):
            st.session_state.checked[i] = True
        st.rerun()

    st.markdown("---")

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

    st.write("### 表形式チェックリスト")

    for idx, row in sub_df_display.iterrows():
        cols = st.columns([1, 3, 4, 1])
        cols[0].write(f"{idx}.")
        cols[1].write(row["item"])

        extra_info = get_extra_info(row["item"])
        if extra_info:
            cols[2].markdown(f"<span style='color: gray;'>{extra_info}</span>", unsafe_allow_html=True)
        else:
            cols[2].write("-")

        if row["checked"]:
            cols[3].checkbox("✓", value=True, disabled=True, key=f"c_{idx}")
        elif idx == first_unchecked:
            if cols[3].button("チェック", key=f"btn_{idx}"):
                st.session_state.checked[idx - 1] = True
                st.rerun()
        else:
            cols[3].write("")

    if end < len(df):
        with st.expander("欄外5件"):
            extra_bottom_df = df.loc[end + 1:min(end + 5, len(df))]
            for idx, row in extra_bottom_df.iterrows():
                cols = st.columns([1, 3, 4, 1])
                cols[0].write(f"{idx}.")
                cols[1].write(row["item"])

                extra_info = get_extra_info(row["item"])
                if extra_info:
                    cols[2].markdown(f"<span style='color: gray;'>{extra_info}</span>", unsafe_allow_html=True)
                else:
                    cols[2].write("-")

                if row["checked"]:
                    cols[3].checkbox("✓", value=True, disabled=True, key=f"c_extra_{idx}")
                else:
                    cols[3].write("")

    if st.button("リセット", help="チェック状況をリセット"):
        st.session_state.checked = [False] * len(df)
        st.rerun()

    st.markdown("---")

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
