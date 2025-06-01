"""
樣式工具模組
提供資料顯示樣式的函數
"""

from gmat_diagnosis_app.constants.config import (
    ERROR_FONT_COLOR, 
    OVERTIME_FONT_COLOR,
    INVALID_FONT_COLOR
)
import logging
import streamlit as st
import re

def apply_styles(row):
    """Applies styling for invalid rows, incorrect answers, and overtime."""
    styles = [''] * len(row)
    
    try:
        # 調試信息
        if 'Subject' in row.index:
            subject = row['Subject']
            q_pos = row['question_position'] if 'question_position' in row.index else "未知"
            logging.debug(f"【styling調試】{subject}科題號{q_pos}開始樣式處理")
            
            # 記錄無效項狀態
            if 'is_invalid' in row.index:
                logging.debug(f"【styling調試】{subject}科題號{q_pos} is_invalid值: {row['is_invalid']}")
            if 'is_manually_invalid' in row.index:
                logging.debug(f"【styling調試】{subject}科題號{q_pos} is_manually_invalid值: {row['is_manually_invalid']}")
        
        # 1. 藍色文字 - 超時單元格 (第一優先級)
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用超時樣式")

        # 2. 紅色文字 - 錯題樣式（第二優先級）
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)
            # 保留超時單元格的藍色文字
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用錯題樣式")
            
        # 3. 整行灰色文字 - 無效行樣式（最後優先級，會覆蓋前面的樣式）
        # 首先檢查 is_invalid，再檢查 is_manually_invalid
        is_invalid_row = False
        # 1. 先檢查 is_invalid
        if 'is_invalid' in row.index and row['is_invalid']:
            is_invalid_row = True
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos} 依據is_invalid={row['is_invalid']}標記為無效行")
        # 2. 如果 is_invalid 不是 true，再檢查 is_manually_invalid
        if not is_invalid_row and 'is_manually_invalid' in row.index and row['is_manually_invalid']:
            is_invalid_row = True
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos} 依據is_manually_invalid={row['is_manually_invalid']}標記為無效行")
            
        if is_invalid_row:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # 即使是無效行，用時超時也應該顯示為藍色
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
                
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用無效項樣式")

    except (KeyError, IndexError) as e:
        # 記錄更多調試信息但不中斷流程
        logging.debug(f"樣式應用時出錯: {e} (row columns: {list(row.index)})")
        pass # 忽略列缺失導致的樣式錯誤
    return styles 


def format_diagnostic_report(report_text):
    """
    統一改善診斷報告的markdown格式，使其更易讀且風格一致
    
    Args:
        report_text (str): 原始診斷報告文字
        
    Returns:
        str: 格式化後的診斷報告
    """
    if not report_text or not isinstance(report_text, str):
        return report_text
    
    # 1. 處理羅馬數字開頭的第一級標題（如 "I. Report Overview and Immediate Feedback"）
    report_text = re.sub(r'\*\*([IVX]+\.[^*]+)\*\*', r'# \1', report_text)
    
    # 2. 處理英文大寫字母開頭的第二級標題（如 "A. Response Time and Strategy Assessment"）
    report_text = re.sub(r'\* \*\*([A-Z]\.[^*]+)\*\*', r'## \1', report_text)
    
    # 3. 統一中文標題格式（保留原有邏輯）
    report_text = re.sub(r'\*\*([一二三四五六七八九十]+、[^*]+)\*\*', r'## \1', report_text)
    
    # 4. 改善其他子標題格式（更精確地識別真正的標題）
    # 只匹配相對簡短的標題（不超過50字符，不包含冒號後的長描述）
    report_text = re.sub(r'\* \*\*([A-Z][^:(*]{1,48}[^:(*])\*\*(?:\s*$|\s*\n)', r'### \1', report_text, flags=re.MULTILINE)
    
    # 5. 修正過度縮排問題（防止被識別為代碼塊）
    # 將4個或更多空格開頭的行調整為最多3個空格，避免Markdown代碼塊識別
    # 但保留有意義的層級結構
    report_text = re.sub(r'^([ ]{4})([^\s])', r'  \2', report_text, flags=re.MULTILINE)  # 4空格->2空格
    report_text = re.sub(r'^([ ]{5,8})([^\s])', r'   \2', report_text, flags=re.MULTILINE)  # 5-8空格->3空格
    report_text = re.sub(r'^([ ]{9,})([^\s])', r'   \2', report_text, flags=re.MULTILINE)  # 9+空格->3空格
    
    # 6. 統一列表項目格式 - 修正層級處理
    # 先處理最深層級，避免重複轉換
    report_text = re.sub(r'^                \* ', '        - ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^            \* ', '      - ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^        \* ', '    - ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^    \* ', '  - ', report_text, flags=re.MULTILINE)
    
    # 7. 改善重要資訊的強調
    report_text = re.sub(r'時間壓力狀態：(.+)', r'**時間壓力狀態：** \1', report_text)
    report_text = re.sub(r'有效評分率.*?：(.+)', r'**有效評分率：** \1', report_text)
    report_text = re.sub(r'使用的超時閾值：(.+)', r'**超時閾值：** \1', report_text)
    
    # 8. 改善數據呈現
    report_text = re.sub(r'(\d+\.?\d*%)( \([^)]+\))', r'**\1**\2', report_text)
    
    # 9. 統一表格格式 - 確保表格周圍有適當空行
    report_text = re.sub(r'\n(\|[^|]+\|[^|]+\|)\n', r'\n\n\1\n', report_text)
    
    # 10. 改善特殊標記
    report_text = re.sub(r'Special Focus Error', '**Special Focus Error**', report_text)
    report_text = re.sub(r'SFE', '**SFE**', report_text)
    
    # 11. 改善分數和百分位
    report_text = re.sub(r'(\d{3,4})分', r'**\1分**', report_text)
    report_text = re.sub(r'第(\d+)百分位', r'第**\1**百分位', report_text)
    
    # 12. 改善數據高亮
    report_text = re.sub(r'(錯誤率|超時率|正確率).*?(\d+\.?\d*%)', r'\1：**\2**', report_text)
    
    # 13. 清理多餘空行
    report_text = re.sub(r'\n{3,}', '\n\n', report_text)
    
    # 14. 確保段落之間有適當間距
    report_text = re.sub(r'(\n#[^\n]+)\n([^\n])', r'\1\n\n\2', report_text)
    report_text = re.sub(r'(\n##[^\n]+)\n([^\n])', r'\1\n\n\2', report_text)
    report_text = re.sub(r'(\n###[^\n]+)\n([^\n])', r'\1\n\n\2', report_text)
    
    # 15. 改善注意事項格式
    report_text = re.sub(r'\*\*(重要註記|重要提醒|注意事項)\*\*', r'> **\1**', report_text)
    
    # 16. 改善數字統計的顯示
    report_text = re.sub(r'(\d+) 題', r'**\1** 題', report_text)
    report_text = re.sub(r'(\d+\.?\d*) 分鐘', r'**\1** 分鐘', report_text)
    
    # 17. 修正可能的格式化問題 - 強化代碼塊移除
    # 移除所有可能的代碼塊格式（包含中文、英文、數字、符號等）
    report_text = re.sub(r'```([^`]*)```', r'\1', report_text)
    report_text = re.sub(r'`([^`]+)`', r'\1', report_text)
    
    # 特別處理包含診斷參數的代碼塊
    report_text = re.sub(r'```\s*\[Problem Types[^\]]*\].*?```', lambda m: m.group(0).replace('```', ''), report_text, flags=re.DOTALL)
    
    # 移除單行代碼格式（反引號）
    report_text = re.sub(r'`([^`\n]*)`', r'\1', report_text)
    
    # 移除多行代碼塊標記
    report_text = re.sub(r'^```[a-zA-Z]*\n', '', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'\n```$', '', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^```$', '', report_text, flags=re.MULTILINE)
    
    # 18. 特別處理V科診斷報告中的方括號格式（防止被誤認為代碼塊）
    # 處理類似 [Other Issues] : [CR Choice Understanding Error: Logic] 的格式
    report_text = re.sub(r'\[([^\]]+)\]\s*:\s*\[([^\]]+)\]', r'\1: \2', report_text)
    
    # 處理多個方括號項目的組合，如 [Error: Key Info Location Understanding] , [ Error: Long Diffi]
    report_text = re.sub(r'\[([^\]]+)\]\s*,\s*\[\s*([^\]]+)\]', r'\1, \2', report_text)
    
    # 處理單獨的方括號項目
    report_text = re.sub(r'\[([^\]]+)\](?!\s*:)', r'\1', report_text)
    
    # 確保列表項目的一致性
    report_text = re.sub(r'^(\s*)-\s+\*\s+', r'\1- ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^(\s*)\*\s+\*\s+', r'\1- ', report_text, flags=re.MULTILINE)
    
    # 19. 特別處理可能被誤認為代碼的診斷參數行
    # 移除可能的內聯代碼格式化
    report_text = re.sub(r'(\s+- [^:]+：)`([^`]+)`', r'\1\2', report_text)
    
    # 20. 處理V科特有的【】格式（保留但優化顯示）
    # 確保【】包圍的內容不會被誤認為代碼或其他格式
    # 但保留【】的視覺效果，因為這是V科報告的設計格式
    report_text = re.sub(r'【([^】]+)】：【([^】]+)】', r'**\1**: \2', report_text)
    
    # 21. 確保沒有遺留的代碼塊標記
    report_text = re.sub(r'```', '', report_text)
    report_text = re.sub(r'`', '', report_text)
    
    return report_text.strip()


def apply_custom_css():
    """Apply custom CSS styling for better UI appearance"""
    st.markdown("""
    <style>
    /* 主要應用程式樣式 */
    .main {
        padding: 1rem 1.5rem;
    }
    
    /* 標題樣式改善 */
    h1 {
        color: #1f4e79;
        font-weight: 700;
        padding-bottom: 1rem;
        border-bottom: 3px solid #1f4e79;
        margin-bottom: 2rem;
    }
    
    h2 {
        color: #2c5282;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-left: 0.5rem;
        border-left: 4px solid #2c5282;
    }
    
    h3 {
        color: #2d3748;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    /* 分頁標籤樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #f7fafc;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        min-width: 8rem;
        padding: 0.5rem 1.25rem;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 0.375rem;
        color: #4a5568;
        font-weight: 500;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f4e79 !important;
        color: #ffffff !important;
        border-color: #1f4e79 !important;
    }
    
    /* 表格樣式改善 */
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    
    .stDataFrame [data-testid="stDataFrameColumn"] {
        background-color: #f8fafc;
    }
    
    /* 診斷報告區域樣式 */
    .diagnostic-report {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .diagnostic-report h4 {
        color: #1f4e79;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .diagnostic-report h5 {
        color: #2c5282;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* 診斷報告表格樣式 */
    .diagnostic-report table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    .diagnostic-report th {
        background-color: #f7fafc;
        color: #2d3748;
        font-weight: 600;
        padding: 0.75rem;
        text-align: left;
        border: 1px solid #e2e8f0;
    }
    
    .diagnostic-report td {
        padding: 0.75rem;
        border: 1px solid #e2e8f0;
        vertical-align: top;
    }
    
    .diagnostic-report tr:nth-child(even) {
        background-color: #f8fafc;
    }
    
    .diagnostic-report tr:hover {
        background-color: #edf2f7;
    }
    
    /* 訊息框樣式 */
    .stAlert {
        border-radius: 0.5rem;
        border: none;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 側邊欄樣式 */
    .css-1d391kg {
        background-color: #f7fafc;
    }
    
    /* 數據編輯器樣式 */
    .stDataEditor {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    /* 圖表樣式 */
    .js-plotly-plot {
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* 載入提示樣式 */
    .stSpinner {
        text-align: center;
        padding: 2rem;
    }
    
    /* 改善文字對比度 */
    .diagnostic-report ul, .diagnostic-report ol {
        padding-left: 1.5rem;
        margin: 0.5rem 0;
    }
    
    .diagnostic-report li {
        margin: 0.25rem 0;
        line-height: 1.6;
    }
    
    /* 強調文字樣式 */
    .diagnostic-report strong {
        color: #1f4e79;
        font-weight: 600;
    }
    
    /* 代碼區塊樣式 */
    .diagnostic-report code {
        background-color: #f1f5f9;
        color: #475569;
        padding: 0.125rem 0.25rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    
    /* 層級縮排改善 */
    .diagnostic-report ul ul {
        margin-left: 1rem;
    }
    
    .diagnostic-report ol ol {
        margin-left: 1rem;
    }
    
    /* 特殊標記樣式 */
    .diagnostic-report .emoji {
        margin-right: 0.25rem;
    }
    
    /* 改善數據表現 */
    .diagnostic-report .data-highlight {
        background-color: #e6fffa;
        color: #234e52;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
    }
    
    /* 警告和提示樣式 */
    .diagnostic-report .warning {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    
    .diagnostic-report .info {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    </style>
    """, unsafe_allow_html=True)


def create_report_container(content, title=None):
    """Create a styled container for diagnostic reports"""
    # 先格式化內容
    formatted_content = format_diagnostic_report(content)
    
    if title:
        st.markdown(f"""
        <div class="diagnostic-report">
            <h4>{title}</h4>
            {formatted_content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="diagnostic-report">
            {formatted_content}
        </div>
        """, unsafe_allow_html=True) 