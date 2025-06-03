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
from gmat_diagnosis_app.i18n import translate as t

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
    按照 q_section_diagnostic_report_formatted.md 的格式要求
    
    Args:
        report_text (str): 原始診斷報告文字
        
    Returns:
        str: 格式化後的診斷報告
    """
    if not report_text or not isinstance(report_text, str):
        return report_text
    
    # 1. 處理主要章節標題（如 "### I. 報告概覽與即時反饋"）
    report_text = re.sub(r'^### ([IVX]+\. [^#\n]+)', r'### \1', report_text, flags=re.MULTILINE)
    
    # 2. 處理次標題（如 "**A. 答題時間與策略評估**"）
    report_text = re.sub(r'^\*\*([A-Z]\. [^*\n]+)\*\*', r'**\1**', report_text, flags=re.MULTILINE)
    
    # 3. 處理中文標題格式
    chinese_numbers_pattern = f'([{t("chinese_numbers")}]+、[^*\\n]+)'
    report_text = re.sub(f'^\\*\\*{chinese_numbers_pattern}\\*\\*', r'**\1**', report_text, flags=re.MULTILINE)
    
    # 4. 統一bullet point格式 - 只保留必要的列表項目
    # 將多層縮排的 * 轉換為適當的 - 格式
    report_text = re.sub(r'^                \* ', '        - ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^            \* ', '      - ', report_text, flags=re.MULTILINE) 
    report_text = re.sub(r'^        \* ', '    - ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^    \* ', '  - ', report_text, flags=re.MULTILINE)
    
    # 5. 修正過度縮排問題（防止被識別為代碼塊）但保留層級結構
    # 特別處理列表結構，包括Key Focus、反思提示等需要縮排層級的內容
    lines = report_text.split('\n')
    processed_lines = []
    in_list_section = False
    list_section_patterns = [
        r'^\s*.*Key Focus:|^\s*.*重點關注',  # Q報告Key Focus
        r'^\s*.*引導性反思提示',  # DI報告反思提示
        r'^\s*.*引導反思提示',   # V報告反思提示
        r'^\s*.*\*\*.*\*\*：.*題目.*反思',  # 具體反思標題
        r'^\s*.*【.*】：',  # 分類標題（如【概念應用錯誤】：）
    ]
    
    for i, line in enumerate(lines):
        # 檢查是否進入需要處理縮排的列表區域
        if not in_list_section:
            for pattern in list_section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    in_list_section = True
                    break
        
        # 檢查是否離開列表區域
        if in_list_section and line.strip():
            # 如果遇到新的主要標題則離開
            if ((line.startswith('**') and line.endswith('**') and '：' not in line) or 
                line.startswith('###') or line.startswith('##')):
                in_list_section = False
            # 如果遇到段落文字（非列表項目且非空白）也離開
            elif (not line.startswith('-') and not line.startswith(' ') and 
                  not line.startswith('**') and not line.startswith('【') and
                  not any(keyword in line for keyword in ['題目', '問題', '注意', '如果', '建議', '方向', '反思'])):
                in_list_section = False
        
        # 處理縮排
        if in_list_section:
            # 為不同類型的列表項目添加適當縮排
            if line.startswith('- '):
                # 第一層列表項目添加2個空格縮排
                processed_lines.append('  ' + line)
            elif line.startswith('            * 【'):
                # DI報告中的分類項目（原本12個空格），調整為8個空格
                processed_lines.append('        ' + line.lstrip())
            elif line.startswith('        * '):
                # DI報告中的第二層項目（原本8個空格），調整為4個空格
                processed_lines.append('    ' + line.lstrip())
            elif line.startswith('    * '):
                # 保持4個空格的項目不變
                processed_lines.append(line)
            elif re.match(r'^\s*\*\s', line):
                # 其他星號開頭的項目，添加基本縮排
                processed_lines.append('  ' + line.lstrip())
            elif line.startswith('**注意**') or line.startswith('**建議**'):
                # 注意事項和建議保持原樣
                processed_lines.append(line)
            else:
                # 避免過度縮排成為代碼塊，但保留層級
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 8:
                    processed_lines.append('    ' + line.lstrip())
                else:
                    processed_lines.append(line)
        else:
            # 非列表區域，按原邏輯處理過度縮排
            if re.match(r'^[ ]{4,}[^\s]', line):
                processed_lines.append('  ' + line.lstrip())
            else:
                processed_lines.append(line)
    
    report_text = '\n'.join(processed_lines)
    
    # 6. 改善重要資訊的強調格式
    time_pressure_status = t('time_pressure_status')
    effective_accuracy_rate = t('effective_accuracy_rate')
    timeout_threshold_prefix = t('timeout_threshold_prefix')
    timeout_threshold = t('timeout_threshold')
    
    report_text = re.sub(f'{time_pressure_status}：(.+)', f'**{time_pressure_status}：** \\1', report_text)
    report_text = re.sub(f'{effective_accuracy_rate}.*?：(.+)', f'**{effective_accuracy_rate}：** \\1', report_text)
    report_text = re.sub(f'{timeout_threshold_prefix}：(.+)', f'**{timeout_threshold}：** \\1', report_text)
    
    # 7. 改善技能名稱的格式化
    skill_prefix = t('skill_prefix')
    report_text = re.sub(f'^(\\*\\*{skill_prefix}：)([^*]+)(\\*\\*)', r'\1\2\3', report_text, flags=re.MULTILINE)
    
    # 8. 改善數據呈現
    report_text = re.sub(r'(\d+\.?\d*%)( \([^)]+\))', r'**\1**\2', report_text)
    
    # 9. 確保表格周圍有適當空行
    report_text = re.sub(r'\n(\|[^|]+\|[^|]+\|)\n', r'\n\n\1\n', report_text)
    
    # 10. 改善特殊標記
    report_text = re.sub(r'Special Focus Error', '**Special Focus Error**', report_text)
    report_text = re.sub(r'SFE', '**SFE**', report_text)
    
    # 11. 改善分數和百分位
    score_suffix = t('score_suffix')
    percentile_prefix = t('percentile_prefix')
    percentile_suffix = t('percentile_suffix')
    
    report_text = re.sub(f'(\\d{{3,4}}){score_suffix}', f'**\\1{score_suffix}**', report_text)
    
    # Handle different language formats for percentile
    if percentile_prefix:  # For Chinese: 第X百分位
        report_text = re.sub(f'{percentile_prefix}(\\d+){percentile_suffix}', f'{percentile_prefix}**\\1**{percentile_suffix}', report_text)
    else:  # For English: Xth percentile
        report_text = re.sub(f'(\\d+)(?:st|nd|rd|th) {percentile_suffix}', f'**\\1**th {percentile_suffix}', report_text)
    
    # 12. 改善數據高亮
    error_timeout_accuracy_pattern = t('error_rate_timeout_rate_accuracy_rate')
    report_text = re.sub(f'({error_timeout_accuracy_pattern}).*?(\\d+\\.?\\d*%)', r'\1：**\2**', report_text)
    
    # 13. 移除所有代碼塊格式（包含中文、英文、數字、符號等）
    report_text = re.sub(r'```([^`]*)```', r'\1', report_text, flags=re.DOTALL)
    report_text = re.sub(r'`([^`]+)`', r'\1', report_text)
    
    # 14. 處理診斷參數格式 - 移除方括號但保留強調
    report_text = re.sub(r'\[([^\]]+)\]\s*:\s*\[([^\]]+)\]', r'**\1**: \2', report_text)
    report_text = re.sub(r'\[([^\]]+)\]\s*,\s*\[\s*([^\]]+)\]', r'\1, \2', report_text)
    report_text = re.sub(r'\[([^\]]+)\](?!\s*:)', r'\1', report_text)
    
    # 15. 確保段落之間有適當間距
    report_text = re.sub(r'(\n#{1,3}[^\n]+)\n([^\n])', r'\1\n\n\2', report_text)
    
    # 16. 改善注意事項格式
    important_keywords = t('important_note_reminder_attention')
    report_text = re.sub(f'\\*\\*({important_keywords})\\*\\*', r'> **\1**', report_text)
    
    # 17. 改善數字統計的顯示
    question_suffix = t('question_suffix')
    minute_suffix = t('minute_suffix')
    
    report_text = re.sub(f'(\\d+) {question_suffix}', f'**\\1** {question_suffix}', report_text)
    report_text = re.sub(f'(\\d+\\.?\\d*) {minute_suffix}', f'**\\1** {minute_suffix}', report_text)
    
    # 18. 清理多餘空行但保持適當間距
    report_text = re.sub(r'\n{3,}', '\n\n', report_text)
    
    # 19. 確保列表項目的一致性
    report_text = re.sub(r'^(\s*)-\s+\*\s+', r'\1- ', report_text, flags=re.MULTILINE)
    report_text = re.sub(r'^(\s*)\*\s+\*\s+', r'\1- ', report_text, flags=re.MULTILINE)
    
    # 20. 移除任何殘留的代碼塊標記
    report_text = re.sub(r'```', '', report_text)
    report_text = re.sub(r'`', '', report_text)
    
    # 21. 處理「（註：...）」格式的特殊說明
    note_prefix = t('note_prefix')
    report_text = re.sub(f'（{note_prefix}：([^）]+)）', f'*（{note_prefix}：\\1）*', report_text)
    
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
        background-color: transparent;
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