import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.header("極簡 ListColumn 編輯測試")

initial_data = {
    'id': [1, 2, 3, 4],
    'tags_list': [
        ['初始標籤A', '初始標籤B'],
        ['只有一個'],
        [],
        ['可編輯標籤1', '可編輯標籤2']
    ]
}
df = pd.DataFrame(initial_data)

st.subheader("請嘗試編輯下方的 '標籤列表 (可編輯)' 欄位")
st.markdown("""
操作說明：
1. 點擊 '標籤列表 (可編輯)' 欄中的任一儲存格 (例如有 `['初始標籤A', '初始標籤B']` 的那格)。
2. 應該會彈出一個列表編輯視窗。
3. **在彈出視窗中**：
    * **刪除標籤**：嘗試用滑鼠點擊某個標籤的文字 (例如 "初始標籤A")，然後用鍵盤的 `Backspace` 或 `Delete` 鍵將其文字完全清除。
    * **修改標籤**：修改某個標籤的文字。
    * **新增標籤**：通常會有一個 "Add item" 或 "+" 的地方讓您輸入新標籤。
""")

edited_df = st.data_editor(
    df,
    column_config={
        "tags_list": st.column_config.ListColumn(
            "標籤列表 (可編輯)",
            help="點擊儲存格以編輯列表。嘗試新增、修改或刪除。",
            width="large"
        ),
        "id": st.column_config.NumberColumn("ID", disabled=True)
    },
    num_rows="fixed",
    key="minimal_editor_test"
)

st.subheader("編輯後的數據：")
st.dataframe(edited_df) 