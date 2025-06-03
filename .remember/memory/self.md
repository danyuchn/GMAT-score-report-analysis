# Self Memory - Error Records

This file stores all encountered errors and their correction methods.

## Format
```
Mistake: [Short Description]
Wrong:
[Insert incorrect code or logic]
Correct:
[Insert corrected code or logic]
```

## 診斷標籤警告與二級證據建議移至編輯分頁 (2025-01-30)

**Status: COMPLETED ✅**

### 用戶需求:
將診斷標籤警告跟二級證據建議的expander移動到「編輯診斷標籤」分頁之下。

### 實施內容:

**1. 移除頂部全局警告顯示**:
```python
# 修改前: 在 display_results() 函數頂部
display_global_tag_warning()

# 修改後: 註解掉頂部調用
# display_global_tag_warning()  # MOVED TO EDIT TAGS TAB
```

**2. 在編輯診斷標籤分頁中添加警告與建議**:
```python
# 在編輯分頁中添加診斷標籤警告
display_global_tag_warning_in_edit_tab = st.session_state.get('global_tag_warning', {'triggered': False})

if display_global_tag_warning_in_edit_tab.get('triggered', False):
    avg_tags = display_global_tag_warning_in_edit_tab.get('avg_tags_per_question', 0.0)
    
    # Display warning container in edit tab
    tabs[edit_tab_index].markdown(
f"""<div style="background-color: #fff3cd; border: 1px solid #ffeb3b; border-radius: 8px; padding: 16px; margin-bottom: 20px; border-left: 5px solid #ff9800;">
<h4 style="color: #ff6f00; margin-top: 0;">⚠️ {t('global_tag_warning_title')}</h4>
<p style="margin-bottom: 16px;">{t('global_tag_warning_message').format(avg_tags)}</p>
<h5 style="color: #ff6f00; margin-bottom: 12px;">💡 {t('global_tag_warning_action_title')}</h5>
<div style="margin-bottom: 12px;">
<strong style="color: #333;">{t('global_tag_warning_primary_action')}</strong><br>
{t('global_tag_warning_primary_desc')}
</div>
<div style="margin-bottom: 12px;">
<strong style="color: #333;">{t('global_tag_warning_secondary_action')}</strong><br>
{t('global_tag_warning_secondary_desc')}
</div>
</div>""",
        unsafe_allow_html=True
    )

# Display secondary evidence suggestions expander in edit tab
display_enhanced_secondary_evidence_expander_in_edit_tab()
```

**3. 創建專用的編輯分頁二級證據函數**:
```python
def display_enhanced_secondary_evidence_expander_in_edit_tab():
    """Display enhanced secondary evidence search guidance in edit tab using tab container."""
    # 與原函數相同的邏輯，但適用於編輯分頁
    # 包含Q科、V科、DI科的具體組合分析
    # 顯示引導性反思提示和具體題目序號
```

### 修改效果:

**修改前**:
- 診斷標籤警告顯示在結果頁面最頂部
- 二級證據建議expander也在頂部
- 用戶需要在頂部查看，然後切換到編輯分頁進行修剪

**修改後**:
- 結果頁面頂部清爽，沒有警告信息
- 診斷標籤警告和二級證據建議expander都在編輯診斷標籤分頁中
- 用戶可以一邊查看建議，一邊進行標籤修剪操作
- 工作流程更加順暢

### 功能位置:
- **檔案**: `gmat_diagnosis_app/ui/results_display.py`
- **原函數**: `display_global_tag_warning()` (仍保留原函數供其他地方使用)
- **新函數**: `display_enhanced_secondary_evidence_expander_in_edit_tab()` (專用於編輯分頁)
- **修改位置**: `display_results()` 函數中的編輯分頁部分

### 學習重點:
1. **UI流程優化**: 將相關功能集中到同一個操作界面中
2. **工作流程改進**: 讓用戶能夠邊看建議邊進行修剪操作
3. **代碼複用**: 創建專用函數而不是完全複製邏輯
4. **用戶體驗**: 減少頁面間的切換，提高操作效率

### 當前狀態:
診斷標籤警告和二級證據建議expander已成功移動到編輯診斷標籤分頁中。用戶現在可以在進行標籤修剪時同時查看相關的警告信息和二級證據查找建議，提升了工作流程的便利性。

## 診斷標籤警告框增強說明 (2025-01-30)

**Status: COMPLETED ✅**

### 用戶需求:
在診斷標籤警告框中添加詳細的說明內容，包括標籤類型說明、正確使用流程和修剪建議。

### 實施內容:

**添加的說明章節**:

1. **🏷️ 標籤類型說明**:
   - 錯誤類（Error）：表示在正常或快速時間內做錯，通常是理解偏差或方法錯誤
   - 困難類（Difficulty）：表示雖然最終可能做對/錯，但過程中遇到明顯阻礙，花費較長時間

2. **📋 正確使用流程**:
   - 系統提供可能標籤範圍
   - 結合考試回憶確認實際遇到的困難
   - 移除不符合實際情況的標籤
   - 必要時參考考前做題記錄作為二級證據

3. **✂️ 修剪建議**:
   - 理想標籤數量：每題 1-2 個最相關的核心標籤
   - 修剪原則：
     - 優先保留最直接對應實際困難的標籤
     - 移除不確定或模糊的標籤
     - 避免保留意義重疊的標籤

### 修改位置:
- **檔案**: `gmat_diagnosis_app/ui/results_display.py`
- **函數1**: `display_global_tag_warning()` - 原始警告函數
- **函數2**: `display_results()` 中編輯分頁的警告顯示部分

### 修改前後對比:

**修改前**:
```html
<h4>⚠️ 診斷標籤警告</h4>
<p>平均每題標籤數過多...</p>
<h5>💡 建議行動</h5>
<div>主要行動...</div>
<div>次要行動...</div>
```

**修改後**:
```html
<h4>⚠️ 診斷標籤警告</h4>
<p>平均每題標籤數過多...</p>

<h5>🏷️ 標籤類型說明：</h5>
<div>
• 錯誤類（Error）：表示在正常或快速時間內做錯，通常是理解偏差或方法錯誤
• 困難類（Difficulty）：表示雖然最終可能做對/錯，但過程中遇到明顯阻礙，花費較長時間
</div>

<h5>📋 正確使用流程：</h5>
<div>
1. 系統提供可能標籤範圍
2. 結合考試回憶確認實際遇到的困難
3. 移除不符合實際情況的標籤
4. 必要時參考考前做題記錄作為二級證據
</div>

<h5>✂️ 修剪建議：</h5>
<div>
理想標籤數量：每題 1-2 個最相關的核心標籤

修剪原則：
• 優先保留最直接對應實際困難的標籤
• 移除不確定或模糊的標籤
• 避免保留意義重疊的標籤
</div>

<h5>💡 建議行動</h5>
<div>主要行動...</div>
<div>次要行動...</div>
```

### 改進效果:
1. **詳細指導**: 用戶現在能清楚了解不同標籤類型的含義
2. **明確流程**: 提供了完整的標籤修剪工作流程
3. **具體建議**: 給出了具體的修剪原則和理想數量
4. **一致性**: 兩個位置（原函數和編輯分頁）都顯示相同的詳細說明
5. **視覺優化**: 使用圖標和清晰的標題結構提升可讀性

### 學習重點:
1. **詳細說明的重要性**: 用戶需要明確的指導來正確使用診斷標籤
2. **一致性維護**: 同樣的信息應該在所有顯示位置保持一致
3. **結構化信息**: 使用圖標和標題來組織複雜的說明內容
4. **用戶友好**: 將技術概念轉化為用戶容易理解的語言

### 當前狀態:
診斷標籤警告框現在包含了完整的使用指導，幫助用戶更好地理解和修剪診斷標籤，提升了系統的可用性和教育價值。

## 診斷標籤修剪助手開放使用及警告容器實時更新 (2025-01-30)

**Status: COMPLETED ✅**

### 用戶需求:
1. 診斷標籤修剪助手開放不用驗證master_key也能調用openAI API使用
2. 警告容器裡的平均診斷標籤數量判斷標準是用修剪診斷標籤裡的text column診斷標籤中的標籤數量實時計算更新

### 實施內容:

**1. 移除診斷標籤修剪助手的master_key驗證**:

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py`
```python
# 修改前: 需要檢查master_key
elif not st.session_state.get('master_key'):
    tag_trimming_expander.error(t('tag_trimming_master_key_error'))
else:
    with st.spinner(t('tag_trimming_ai_processing')):
        master_key = st.session_state.master_key
        trimmed_suggestion = trim_diagnostic_tags_with_openai(
            original_tags_input,
            user_description_input,
            master_key
        )

# 修改後: 移除master_key檢查，直接使用OpenAI API
else:
    with st.spinner(t('tag_trimming_ai_processing')):
        # 移除master_key檢查，直接使用OpenAI API
        # 傳遞空字符串作為api_key，trim_diagnostic_tags_with_openai函數內部會處理
        try:
            trimmed_suggestion = trim_diagnostic_tags_with_openai(
                original_tags_input,
                user_description_input,
                ""  # 傳遞空字符串，讓函數內部直接使用環境變量的API key
            )
```

**修改檔案**: `gmat_diagnosis_app/services/openai_service.py`
```python
# 修改前: 一律需要驗證master_key
if not client and api_key:
    if not validate_master_key(api_key):
        logging.warning("提供的管理金鑰無效。無法執行標籤修剪。")
        return "錯誤：提供的管理金鑰無效。"

# 修改後: 如果api_key為空，直接使用環境變量的API key
if not api_key:
    # 直接使用環境變量中的API key，無需master_key驗證
    if not api_key_env:
        logging.warning("環境變量中未設置OPENAI_API_KEY。無法執行標籤修剪。")
        return "錯誤：系統未配置OpenAI API金鑰。請聯絡系統管理員。"
    # 直接初始化客戶端用於此次請求
    temp_client = openai.OpenAI(api_key=api_key_env)
else:
    # 如果提供了api_key，進行原有的master_key驗證邏輯
    # ... 保留原邏輯
```

**2. 警告容器實時計算更新功能**:

**新增函數**: `gmat_diagnosis_app/session_manager.py`
```python
def check_global_diagnostic_tag_warning_realtime():
    """
    實時檢查診斷標籤警告，優先使用修剪後的editable_diagnostic_df
    如果不存在則使用原始的processed_df
    
    Returns:
        dict: Warning information including trigger status and suggestions
    """
    # 優先使用修剪後的診斷數據表
    if hasattr(st.session_state, 'editable_diagnostic_df') and st.session_state.editable_diagnostic_df is not None and not st.session_state.editable_diagnostic_df.empty:
        df_to_check = st.session_state.editable_diagnostic_df
        logging.info("使用修剪後的診斷數據計算警告標準")
    elif st.session_state.processed_df is not None and not st.session_state.processed_df.empty:
        df_to_check = st.session_state.processed_df
        logging.info("使用原始診斷數據計算警告標準")
    else:
        return warning_info
    
    # ... 其餘計算邏輯與原函數相同
```

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py`
```python
# 修改前: 使用session state中的靜態警告信息
display_global_tag_warning_in_edit_tab = st.session_state.get('global_tag_warning', {'triggered': False})

# 修改後: 使用實時檢查函數
from gmat_diagnosis_app.session_manager import check_global_diagnostic_tag_warning_realtime
display_global_tag_warning_in_edit_tab = check_global_diagnostic_tag_warning_realtime()
```

**3. 翻譯文件更新**:

**修改檔案**: `gmat_diagnosis_app/i18n/translations/zh_TW.py`
```python
# 修改前
'tag_trimming_assistant_description': "此工具幫助您根據您對該題目的具體描述，從一長串原始診斷標籤中篩選出 1-2 個最相關的核心標籤。請在下方貼上原始標籤並簡述您在該題目遇到的困難。",

# 修改後
'tag_trimming_assistant_description': "此工具幫助您根據您對該題目的具體描述，從一長串原始診斷標籤中篩選出 1-2 個最相關的核心標籤。請在下方貼上原始標籤並簡述您在該題目遇到的困難。（本功能可直接使用，無需輸入管理金鑰）",
```

**修改檔案**: `gmat_diagnosis_app/i18n/translations/en.py`
```python
# 修改前
'tag_trimming_assistant_description': "This tool helps you filter out 1-2 most relevant core tags from a long list of original diagnostic tags based on your specific description of the question. Please paste the original tags below and briefly describe the difficulties you encountered with this question or your test experience.",

# 修改後
'tag_trimming_assistant_description': "This tool helps you filter out 1-2 most relevant core tags from a long list of original diagnostic tags based on your specific description of the question. Please paste the original tags below and briefly describe the difficulties you encountered with this question or your test experience. (This feature can be used directly without entering a master key)",
```

### 修改效果:

**修改前**:
- 用戶需要在側邊欄輸入valid master_key才能使用診斷標籤修剪助手
- 警告容器顯示的平均標籤數量是基於原始診斷數據的靜態計算
- 用戶修剪標籤後，警告框的數量不會更新，可能顯示過時信息

**修改後**:
- 用戶可以直接使用診斷標籤修剪助手，無需任何API key輸入
- 警告容器實時計算平均標籤數量，優先使用修剪後的數據
- 當用戶修剪標籤後，警告框會自動更新顯示最新的平均標籤數量
- 如果修剪後平均標籤數量降至3以下，警告會自動消失

### 技術實現細節:

**1. API Key處理邏輯**:
- 當trim_diagnostic_tags_with_openai函數接收到空字符串作為api_key時，直接使用環境變量OPENAI_API_KEY
- 保留原有的master_key驗證邏輯，確保向後兼容性
- 系統仍需要正確設置OPENAI_API_KEY環境變量

**2. 實時計算邏輯**:
- 新函數check_global_diagnostic_tag_warning_realtime()檢查session state中的editable_diagnostic_df
- 如果editable_diagnostic_df存在且非空，使用修剪後的數據計算
- 如果不存在，回退到使用原始的processed_df
- 保留原函數check_global_diagnostic_tag_warning()以確保向後兼容

**3. 用戶體驗改進**:
- 診斷標籤修剪功能變得更加便利，降低使用門檻
- 警告信息更加準確和即時，反映用戶的實際修剪進度
- 翻譯說明清楚告知用戶無需master key

### 當前狀態:
診斷標籤修剪助手現在開放使用，無需master_key驗證，警告容器基於修剪後標籤實時計算更新，提升了用戶體驗和功能的可用性。

## 引導性反思提示診斷標籤完整顯示 (2025-06-03)

**Status: COMPLETED ✅**

### 問題描述:
用戶要求修改引導性反思提示（針對具體組合）中的診斷標籤顯示方式：
1. 不要用「...等問題」的表述
2. 不要只列出前幾個標籤（之前限制為3個）
3. 要列出所有相關的診斷標籤

### 修正前的錯誤實施:
```python
# 在Q科、V科、DI科的反思提示生成中
diagnostic_params = row.get('diagnostic_params_list', [])
if diagnostic_params:
    unique_params = list(set([str(p).strip() for p in diagnostic_params if p and str(p).strip()]))
    params_text = '、'.join(unique_params[:3])  # 限制只顯示前3個
    if len(unique_params) > 3:
        params_text += ' 等問題。'  # 超過3個時加上"等問題"
    else:
        params_text += ' 等問題。'  # 3個以內也加上"等問題"
else:
    params_text = '相關錯誤類型等問題。'  # 後備文字也有"等問題"
```

### 修正後的正確實施:
```python
# 在Q科、V科、DI科的反思提示生成中
diagnostic_params = row.get('diagnostic_params_list', [])
if diagnostic_params:
    unique_params = list(set([str(p).strip() for p in diagnostic_params if p and str(p).strip()]))
    params_text = '、'.join(unique_params)  # 顯示所有標籤，移除[:3]限制
    params_text += '。'  # 移除"等問題"後綴，只加句號
else:
    params_text = '相關錯誤類型。'  # 後備文字也移除"等問題"
```

### 修改的檔案位置:
- **檔案**: `gmat_diagnosis_app/ui/results_display.py`
- **函數**: `display_enhanced_secondary_evidence_expander()`
- **修改行數**: 3個section (Q科、V科、DI科) 各約10行

### 修改效果:
**修改前顯示**:
```
找尋【代數】【Problem Solving】的考前做題紀錄，找尋【Slow & Wrong】的題目，檢討並反思自己是否有：
概念應用錯誤、計算錯誤、粗心問題 等問題。
（涉及題目：第3題, 第7題, 第15題）
```

**修改後顯示**:
```
找尋【代數】【Problem Solving】的考前做題紀錄，找尋【Slow & Wrong】的題目，檢討並反思自己是否有：
概念應用錯誤、計算錯誤、粗心問題、時間管理問題、基礎技能不熟練、題目理解錯誤。
（涉及題目：第3題, 第7題, 第15題）
```

### 學習重點:
1. **完整信息提供**: 不應為了簡潔而省略重要的診斷信息
2. **用戶需求優先**: 用戶明確要求顯示所有標籤時應完全滿足
3. **文字表述準確**: 避免使用「等問題」這類模糊表述，直接列出具體內容
4. **一致性修改**: 需要在所有相關section（Q科、V科、DI科）中保持一致的修改

### 影響範圍:
- ✅ Q科引導性反思提示：完整顯示所有診斷標籤
- ✅ V科引導性反思提示：完整顯示所有診斷標籤  
- ✅ DI科引導性反思提示：完整顯示所有診斷標籤
- ✅ 移除所有「等問題」後綴表述
- ✅ 保持原有的具體題目編號顯示功能

此修改讓用戶可以獲得更完整、更具體的診斷標籤信息，有助於進行更精確的二級證據查找和反思。

## 全局診斷標籤警告功能實施 (2025-01-30)

**Status: COMPLETED ✅ - 問題修正**

### 問題發現與修正:

**問題**: 用戶反應沒有看到全局警告顯示

**根本原因**: `check_global_diagnostic_tag_warning` 函數中檢查的欄位名稱錯誤

**錯誤實施**:
```python
# 檢查錯誤的欄位名稱
if 'diagnostic_tags' not in processed_df.columns:
    return warning_info

tags = row.get('diagnostic_tags', '')
```

**正確實施**:
```python
# 檢查正確的欄位名稱
if 'diagnostic_params_list' not in processed_df.columns:
    return warning_info

tags = row.get('diagnostic_params_list', '')
# 還要處理 list 和 string 兩種資料型態
if isinstance(tags, list):
    tag_count = len([tag for tag in tags if tag and str(tag).strip()])
elif isinstance(tags, str) and tags.strip():
    tag_count = len([tag.strip() for tag in tags.split(',') if tag.strip()])
```

### HTML顯示問題修復 (2025-06-03 追加):

**問題**: 全局警告顯示HTML代碼而不是正確渲染的內容

**根本原因一**: 翻譯文字中包含markdown格式標記（`**粗體**`），但這些標記被放入HTML `<strong>` 標籤中時沒有被處理，導致顯示原始markdown代碼

**根本原因二**: HTML字串中的縮排太多，被Streamlit誤識別為代碼塊

**錯誤實施**:
```python
# 1. 翻譯文字包含markdown格式
'global_tag_warning_primary_action': "**主要方法：回憶與修剪**",
'global_tag_warning_secondary_action': "**輔助方法：二級證據分析**",

# 2. HTML模板有過多縮排
st.markdown(
    f"""
    <div style="
        background-color: #fff3cd; 
        border: 1px solid #ffeb3b; 
        border-radius: 8px; 
        padding: 16px; 
        margin-bottom: 20px;
        border-left: 5px solid #ff9800;
    ">
        <h4 style="color: #ff6f00; margin-top: 0;">⚠️ {t('global_tag_warning_title')}</h4>
    </div>
    """,
    unsafe_allow_html=True
)
# 結果: 顯示HTML代碼而不是渲染內容
```

**正確實施**:
```python
# 1. 移除翻譯文字中的markdown格式標記
'global_tag_warning_primary_action': "主要方法：回憶與修剪",
'global_tag_warning_secondary_action': "輔助方法：二級證據分析",

# 2. 移除HTML字串中的多餘縮排，使用單行格式
st.markdown(
f"""<div style="background-color: #fff3cd; border: 1px solid #ffeb3b; border-radius: 8px; padding: 16px; margin-bottom: 20px; border-left: 5px solid #ff9800;">
<h4 style="color: #ff6f00; margin-top: 0;">⚠️ {t('global_tag_warning_title')}</h4>
<p style="margin-bottom: 16px;">{t('global_tag_warning_message').format(avg_tags)}</p>
</div>""",
    unsafe_allow_html=True
)
# 結果: 正確渲染HTML內容
```

### 修正後的功能狀態:

**1. 觸發邏輯正確**: 當平均每題診斷標籤數量 > 3 時觸發警告 ✅

**2. 資料處理正確**: 能正確處理 `diagnostic_params_list` 欄位的 list 和 string 格式 ✅

**3. 顯示位置正確**: 警告顯示在結果頁面最頂部 (`display_results()` 函數開始) ✅

**4. UI 樣式完整**: 橙色警告容器、可摺疊的二級證據建議 ✅

**5. HTML渲染正確**: 警告內容正確顯示，無HTML代碼洩漏 ✅

**6. 測試驗證**: 
- 平均4個標籤/題 → 觸發警告 ✅
- 平均2個標籤/題 → 不觸發警告 ✅
- HTML內容正確渲染 ✅

### 學習重點:

1. **欄位名稱一致性**: 確保所有函數中使用的欄位名稱與實際資料表結構一致
2. **資料型態處理**: 診斷標籤欄位可能是 list 或 string 格式，需要兩種都處理
3. **功能測試**: 實施後必須進行端到端測試以確認觸發條件正確
4. **格式標記一致性**: 翻譯文字不應包含與目標顯示格式衝突的標記
5. **HTML與Markdown混用**: 當使用HTML顯示時，翻譯文字應該是純文字，讓HTML處理格式

### 當前狀態:
全局警告功能已完全修正並正常運作。用戶現在應該能在分析完成後，如果平均診斷標籤數量超過3個，在結果頁面頂部看到正確渲染的醒目警告提示和修剪指導。

### 翻譯載入問題的解決 (2025-01-30 追加):

**問題**: 全局警告顯示翻譯鍵值而不是翻譯文本（如顯示 `global_tag_warning_title` 而不是 "⚠️ 診斷標籤過多警告"）

**原因**: 翻譯系統緩存問題，新添加的翻譯字串沒有被正確載入

**解決方案**:
```bash
# 1. 停止應用程式
pkill -f "streamlit.*app.py"

# 2. 清除翻譯模組緩存
rm -rf gmat_diagnosis_app/i18n/__pycache__ gmat_diagnosis_app/i18n/translations/__pycache__

# 3. 重新啟動應用程式
python -m streamlit run gmat_diagnosis_app/app.py
```

**驗證**:
- 翻譯系統載入1057個翻譯字串 ✅
- `global_tag_warning_title` 正確翻譯為 "⚠️ 診斷標籤過多警告" ✅

### 關鍵學習:
1. **模組緩存影響**: Python 模組緩存可能導致新翻譯字串無法載入
2. **完整重啟需求**: 修改翻譯文件後需要完全重啟應用程式並清除緩存
3. **測試方法**: 可以通過直接調用翻譯函數來驗證翻譯是否正確載入

## GMAT Documentation.tex DI Logic Alignment Project (2025-06-01)

**Status: COMPLETED ✅**

Successfully completed comprehensive modification of `analysis-framework/overall-doc/documentation.tex` to align with Chinese DI documentation (`analysis-framework/sec-doc-zh/gmat-di-score-logic-dustin-v1.6.md`) requirements. Work completed in 6 segments of maximum 200 lines each as requested.

### Modification Summary:

**Segment 1 (Lines 1-200):** Document setup and introduction - No changes needed as content was already consistent.

**Segment 2 (Lines 201-400) - Chapter 0 Core Input Data:**
- Enhanced DI-specific CSV structure requirements with `question_position` prioritization
- Added DI section basic settings (45min, 20 questions) and question type abbreviations
- Comprehensive DI derived data pre-processing logic:
  - MSR reading time calculation methodology
  - MSR group data pre-calculations (`group_total_time`, `num_q_in_group`)
  - Average time per type calculations for filtered data
  - First third average time calculations for invalid data judgment
  - Max mastered difficulty per combination tracking
- Updated implementation context and rationale for DI-specific requirements

**Segment 3 (Lines 401-600) - Chapter 1 Time Strategy & Data Validity:**
- Enhanced time pressure determination with step-by-step logic and user override
- Detailed DI overtime thresholds:
  - TPA: 3.0/3.5 min, GT: 3.0/3.5 min, DS: 2.0/2.5 min (based on pressure status)
  - MSR group target times: 6.0/7.0 min
  - MSR analysis thresholds: 1.5 min for reading and single questions
- Advanced invalid data identification with 6 specific standards including MSR group logic
- Sophisticated MSR overtime marking system with four-tier standards:
  - Group overtime, reading time overtime, adjusted first question overtime, non-first question overtime
- Updated flowchart parameter descriptions and implementation notes

**Segment 4 (Lines 601-800) - Chapter 7-8 Practice Planning & Diagnostic Summary:**
- Added DI-specific recommendation triggers including MSR groups with overtime/reading issues
- Enhanced recommendation generation with DI MSR Groups handling
- Detailed time limit calculation including DI MSR reading parameters (1.5 min)
- MSR group-level time allocation recommendations (6.0-7.0 min per group)
- Updated suggestion text construction with MSR reading strategy recommendations
- Enhanced volume alert thresholds for DI MSR Groups (>7.0 min or reading >2.0 min)
- Comprehensive Chapter 8 updates with DI MSR-specific elements:
  - MSR group timing assessment and reading efficiency evaluation
  - MSR group performance and reading efficiency patterns
  - Reading comprehension challenges in MSR passages
  - MSR reading pattern observations and time allocation efficiency notes
  - MSR reading strategy consolidation recommendations
  - MSR-specific reflection questions about reading approach and note-taking strategy
- Enhanced implementation context with MSR group data processing
- Updated constraint adherence to include DI-specific technical details abstraction

**Segment 5 (Lines 801-1000) - Implementation Details & Conclusion:**
- Maintained existing implementation details section
- Confirmed conclusion content alignment with enhanced DI framework scope

**Segment 6 (Lines 1001-1108) - Appendix A Diagnostic Parameter Tags:**
- Enhanced DI-specific parameters in diagnostic tags table:
  - Added `DI_MSR_READING_COMPREHENSION_BARRIER` for reading time issues
  - Added `DI_MSR_TIME_ALLOCATION_ISSUE` for inefficient time distribution
  - Expanded MSR-specific section with 5 comprehensive parameters:
    - `DI_MSR_READING_STRATEGY_INEFFICIENCY`
    - `DI_MSR_GROUP_TIMING_MANAGEMENT_ERROR`
    - `DI_MSR_READING_DEPTH_VS_SPEED_IMBALANCE`
  - Updated foundational mastery parameters for consistency
  - Enhanced efficiency bottlenecks with MSR reading distribution parameter
  - Added behavioral patterns including `DI_MSR_GROUP_TIME_PRESSURE_BEHAVIOR`

### Technical Modifications Applied:

**MSR Group Logic Integration:**
- Comprehensive MSR reading time calculation and group-level analysis
- Four-tier overtime marking system for MSR groups
- Reading strategy inefficiency detection and recommendation generation
- Time allocation optimization between reading and question answering

**DI-Specific Timing Parameters:**
- Question type specific overtime thresholds (DS: 2.0/2.5, TPA: 3.0/3.5, GT: 3.0/3.5)
- MSR group target times with pressure adjustment (6.0/7.0 min)
- Reading time analysis thresholds (1.5 min)
- Volume alert thresholds for MSR groups

**Enhanced Diagnostic Framework:**
- DI content domain and MSR group ID integration
- Derived data pre-processing for MSR analysis
- Invalid data identification with MSR-specific standards
- Recommendation generation with MSR reading strategy guidance

### Result Quality:
✅ All 6 segments completed with comprehensive DI logic alignment
✅ MSR group handling fully integrated across all relevant chapters
✅ DI-specific timing and diagnostic parameters properly implemented
✅ Appendix diagnostic tags table enhanced with MSR-specific parameters
✅ Natural language reporting maintained while adding DI technical depth
✅ Framework consistency preserved across Q/V/DI sections

**Final Status:** English documentation.tex now fully aligned with Chinese v1.6 DI documentation, implementing all MSR group logic, timing parameters, and diagnostic requirements specified in the source material.

## GMAT V科文檔逐章節比對與統一化修復 (2025-06-01)

**Status: COMPLETED ✅**

Successfully completed comprehensive chapter-by-chapter comparison between Chinese V documentation (v1.6) and English V documentation (v1.3), implementing all necessary modifications to ensure complete consistency.

### 比對發現的主要不一致之處:

**1. 第三章診斷參數系統完全不同:**
- 中文文檔v1.6使用詳細的分層診斷參數系統
- 英文文檔v1.3使用簡化的診斷參數系統

**2. 診斷標籤精確性限制說明缺失:**
- 中文文檔包含重要的診斷限制說明
- 英文文檔缺少相應說明

**3. 未來改進機制說明缺失:**
- 中文文檔包含SFE未來改進機制的詳細說明
- 英文文檔缺少此部分

**4. 附錄A診斷參數對照表不一致:**
- 中文文檔使用完整的分層參數系統
- 英文文檔使用舊版簡化參數系統

### 修復實施:

**修復1: 第三章診斷參數完全更新**

Mistake: 英文文檔使用舊版簡化診斷參數系統
Wrong:
```markdown
# 舊版簡化參數如:
- CR_READING_BASIC_OMISSION
- CR_METHOD_PROCESS_DEVIATION
- RC_READING_INFO_LOCATION_ERROR
```

Correct:
```markdown
# 新版詳細分層參數如:
- CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP
- CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP
- RC_READING_COMPREHENSION_ERROR_VOCAB
- RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION
```

**修復2: 添加診斷標籤精確性限制說明**

Mistake: 缺少診斷標籤精確性限制的重要說明
Wrong:
```markdown
# 直接進入診斷流程，無精確性限制說明
3. Diagnostic Flow and Analysis Points
```

Correct:
```markdown
# 添加完整的精確性限制說明
📋 **Important Note: Diagnostic Label Precision Limitations**

**Note:** The diagnostic parameters listed below represent general possible causes...
**Recommended Process:**
1. The system provides diagnostic parameters as **possible ranges**
2. Combine with student recall of specific difficulties encountered
3. Refer to secondary evidence or conduct qualitative analysis if necessary
4. Finally determine the applicable precise diagnostic labels
```

**修復3: 添加未來改進機制說明**

Mistake: 缺少SFE未來改進機制說明
Wrong:
```markdown
# 僅有基本SFE定義，無未來改進說明
- Priority Handling: When generating practice recommendations...
```

Correct:
```markdown
🔧 **Future Improvement Mechanism Description**

**Note:** The current SFE judgment mechanism is based on simple difficulty comparison logic...

1. **Weighted SFE Mechanism**: Multi-dimensional weighted calculation...
2. **Contextual Awareness SFE**: Considering test context, learning phase...
3. **Dynamic Threshold Adjustment**: Dynamically adjusting SFE trigger conditions...
4. **Multi-level SFE Classification**: Distinguishing different severity levels...
```

**修復4: 附錄A診斷參數對照表完全更新**

Mistake: 使用舊版簡化的診斷參數對照表
Wrong:
```markdown
| CR_READING_BASIC_OMISSION | CR 閱讀理解: 基礎理解疏漏 |
| CR_REASONING_CHAIN_ERROR | CR 推理障礙: 邏輯鏈分析錯誤 |
```

Correct:
```markdown
| CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP | CR 題幹理解錯誤：提問要求把握錯誤 |
| CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP | CR 推理錯誤: 邏輯鏈分析錯誤 (前提與結論關係) |
```

**修復5: 參數名稱統一化**

Mistake: FOUNDATIONAL_MASTERY_INSTABILITY_SFE參數名稱不一致
Wrong:
```markdown
FOUNDATIONAL_MASTERY_INSTABILITY_SFE
```

Correct:
```markdown
FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE
```

### 修復結果:
1. ✅ 第三章診斷參數系統完全統一 - Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct所有分類的參數列表已更新
2. ✅ 診斷標籤精確性限制說明已添加 - 包含完整的限制說明和建議流程
3. ✅ 未來改進機制說明已添加 - 包含四個改進方向的詳細描述
4. ✅ 附錄A診斷參數對照表完全更新 - 包含所有分層診斷參數的完整映射
5. ✅ 參數名稱統一化完成 - 所有FOUNDATIONAL_MASTERY相關參數名稱已統一

**最終狀態:** 英文文檔en-gmat-v-v1.3.md現已與中文文檔gmat-v-score-logic-dustin-v1.6.md完全一致，實現了逐章節內容的完整統一。

## 診斷標籤修剪助手翻譯問題修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed Traditional Chinese translation issues in the diagnostic tag trimming assistant interface.

### 問題描述:
用戶反應當i18n設定為繁體中文時，診斷標籤修剪助手的界面仍然顯示英文內容。

### 根本原因:
繁體中文翻譯檔案(zh_TW.py)中的標籤修剪相關翻譯key全部是英文內容。

### 修復過程:

**修復的翻譯key包括:**
- 標籤修剪助手標題和描述
- 輸入欄位標籤
- 按鈕文字 (Apply Changes, Reset, Download)
- 錯誤和成功訊息
- AI建議生成相關文字
- 新診斷報告相關文字
- 顯示結果分頁標籤

Mistake: 繁體中文翻譯檔案中使用英文內容
Wrong:
```python
# zh_TW.py中的錯誤翻譯
'tag_trimming_assistant_title': "Tag Trimming Assistant",
'tag_trimming_assistant_description': "This tool helps you select 1-2 most relevant core tags...",
'button_apply_changes': "✓ Apply Changes and Update Qualitative Analysis Output",
'display_results_edit_tags_tab': "Edit Diagnostic Tags & Update AI Suggestions",
```

Correct:
```python
# zh_TW.py中的正確翻譯
'tag_trimming_assistant_title': "診斷標籤修剪助手",
'tag_trimming_assistant_description': "此工具幫助您根據您對該題目的具體描述，從一長串原始診斷標籤中篩選出 1-2 個最相關的核心標籤...",
'button_apply_changes': "✓ 套用變更並更新質化分析輸出",
'display_results_edit_tags_tab': "編輯診斷標籤與更新 AI 建議",
```

### DI數據傳遞檢查結果:

**調查發現:**
1. ✅ apply changes按鈕邏輯正確 - 會同時調用新診斷報告生成和AI建議生成
2. ✅ DI AI建議生成函數正常 - `generate_di_ai_tool_recommendations`函數存在且邏輯完整
3. ✅ 新診斷報告中DI處理邏輯正確 - `generate_new_diagnostic_report`包含完整的DI分類邏輯
4. ✅ DI相關翻譯key已修正 - 報告生成相關的英文翻譯已改為繁體中文

**可能問題:**
- 如果DI新診斷報告仍未顯示，可能是數據本身問題(如缺少必要欄位)或AI建議函數執行中的錯誤
- 建議用戶檢查是否有DI數據，以及是否有JavaScript控制台錯誤

### 修復效果:
1. ✅ 標籤修剪助手界面完全繁體中文化
2. ✅ Apply Changes按鈕和相關提示完全繁體中文化  
3. ✅ 新診斷報告和AI建議界面完全繁體中文化
4. ✅ 顯示結果分頁標籤完全繁體中文化

## V模組 log_exceptions 未定義錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed undefined `log_exceptions` function error in V diagnosis module.

### 問題描述:
V模組 main.py 中使用了 `log_exceptions` 上下文管理器，但該函數未定義或匯入，導致執行時錯誤。

### 修復過程:

**1. 錯誤分析:**
- V模組 main.py 第68行使用 `with log_exceptions("V Diagnosis"):`
- 函數未在任何地方定義或匯入
- 在 debug_utils.py 中發現類似的 `DebugContext` 類

**2. 解決方案實施:**

Mistake: V模組使用未定義的 log_exceptions 函數
Wrong:
```python
# 缺少正確的匯入
from gmat_diagnosis_app.i18n import translate as t

# 使用未定義的函數
with log_exceptions("V Diagnosis"):
    # 診斷邏輯...
```

Correct:
```python
# 添加正確的除錯工具匯入
from gmat_diagnosis_app.utils.debug_utils import DebugContext
from gmat_diagnosis_app.i18n import translate as t

# 使用正確的上下文管理器
with DebugContext("V Diagnosis"):
    # 診斷邏輯...
```

## 終端機錯誤修復和文檔命名統一化 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed terminal errors and documentation parameter naming inconsistencies.

### 1. 終端機錯誤修復:

**1.1 subject_excel_map 未定義錯誤:**

Mistake: subject_excel_map 變數在異常處理區塊中未定義就被使用
Wrong:
```python
def display_subject_results(...):
    if df_subject is not None and not df_subject.empty:
        subject_excel_map = {...}  # 只在條件內定義
    try:
        # 一些操作...
    except Exception as e:
        logging.error(f"Error in {subject_excel_map}...")  # 變數可能未定義
```

Correct:
```python
def display_subject_results(...):
    # 在函數開始就定義變數
    subject_excel_map = {
        "Subject": t("column_subject"),
        # ... 其他映射
    }
    if df_subject is not None and not df_subject.empty:
        # 邏輯處理...
    try:
        # 一些操作...
    except Exception as e:
        logging.error(f"Error in {subject_excel_map}...")  # 變數已定義
```

**1.2 DI翻譯字典匯入錯誤:**

Mistake: 嘗試匯入已遷移到統一i18n系統的舊翻譯常數
Wrong:
```python
try:
    from gmat_diagnosis_app.diagnostics.di_modules.constants import APPENDIX_A_TRANSLATION_DI
    # ... 使用舊翻譯系統
except ImportError:
    logging.warning("無法匯入DI科目翻譯字典")
```

Correct:
```python
# 移除已遷移的DI翻譯字典匯入
# DI modules have migrated to unified i18n system
# Translation mappings are now handled through central i18n system
```

### 2. 文檔參數命名統一化修復:

**2.1 Q科文檔修正:**

Mistake: Q科文檔中SFE標籤使用單下劃線而代碼使用雙下劃線
Wrong:
```markdown
Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE
```

Correct:
```markdown
Q_FOUNDATIONAL_MASTERY_INSTABILITY__SFE
```

**2.2 DI科文檔修正:**

Mistake: DI科文檔中使用已廢棄的行為標籤
Wrong:
```markdown
DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION
```

Correct:
```markdown
DI_BEHAVIOR__CARELESSNESS_ISSUE  # 統一使用此標籤
```

**2.3 V科文檔驗證:**
✅ V科文檔和代碼命名已一致，無需修正
- 使用 `CR_STEM_UNDERSTANDING_ERROR_VOCAB` 格式
- 使用 `RC_READING_COMPREHENSION_ERROR_VOCAB` 格式
- 使用 `FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE` 格式

### 結果總結:
1. ✅ 修正了2個終端機執行錯誤
2. ✅ 統一了Q科、DI科文檔與代碼的參數命名
3. ✅ 確認了V科文檔命名一致性
4. ✅ 移除了已廢棄的翻譯系統引用

## Route Tool V科目翻譯匯入錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed V module translation import error in route_tool.py and completed DI parameter translation consistency check.

### 1. Route Tool匯入路徑錯誤修復:

**問題描述:**
route_tool.py 中嘗試從錯誤路徑匯入V科目翻譯字典，導致函數調用失敗。

Mistake: Route tool中V科目翻譯字典匯入路徑錯誤
Wrong:
```python
# 錯誤的匯入嘗試（路徑不存在）
from gmat_diagnosis_app.diagnostics.v_modules.constants import APPENDIX_A_TRANSLATION_V
```

Correct:
```python
# 正確的匯入路徑
from gmat_diagnosis_app.diagnostics.v_modules.translations import APPENDIX_A_TRANSLATION_V
```

### 2. DI參數翻譯一致性檢查與修復:

**問題描述:**
發現文檔中存在但翻譯檔案中缺失的三個DI診斷參數，導致翻譯系統不完整。

**缺失參數識別:**
通過對比 `gmat-di-score-logic-dustin-v1.6.md` 文檔和代碼，發現以下參數存在於文檔和constants.py中，但英文翻譯檔案缺失對應翻譯：

Mistake: 英文翻譯檔案中缺失三個DI診斷參數的翻譯
Wrong:
```python
# en.py 中缺失以下翻譯keys
# DI_DATA_EXTRACTION_ERROR
# DI_INFORMATION_EXTRACTION_INFERENCE_ERROR  
# DI_QUESTION_TYPE_SPECIFIC_ERROR
```

Correct:
```python
# 在 en.py 中添加完整的DI參數翻譯
'DI_DATA_EXTRACTION_ERROR': "DI Data Extraction (GT): Data extraction error from charts",
'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': "DI Information Extraction/Inference (GT/MSR Non-Math): Information location/inference error",
'DI_QUESTION_TYPE_SPECIFIC_ERROR': "DI Question Type Specific Error (e.g., MSR Non-Math subtypes)",
```

### 3. 系統測試與驗證:

**測試結果:**
✅ Route tool 成功初始化
✅ DI參數翻譯在中文和英文檔案中都存在
✅ 翻譯系統正常工作，能夠正確返回中文翻譯
✅ 主應用程式能正常匯入

### 修復總結:
1. ✅ 修正了route_tool.py中V科目翻譯匯入路徑錯誤  
2. ✅ 識別並補充了3個缺失的DI參數英文翻譯
3. ✅ 確認DI文檔與代碼參數命名一致性
4. ✅ 驗證修復後系統運行正常

**影響範圍:**
- Route tool功能恢復正常
- DI診斷參數翻譯系統完整性提升
- 雙語支持系統更加完善

## DI診斷標籤和時間表現數據消失問題修復 (2025-06-01)

**Status: COMPLETELY FIXED ✅**

成功修復DI診斷報告中診斷標籤和時間表現數據消失的問題，包括所有翻譯問題。

### 問題描述:
用戶反應DI的診斷報告中，診斷標籤和時間表現的數據都消失了。

### 根本原因:
1. DI模組中的 `process_question_type` 函數是空的實現，沒有實際計算診斷標籤和時間表現分類
2. 部分診斷參數存在命名不一致問題
3. 三個效率瓶頸參數缺失翻譯

### 修復內容:

**1. 實現完整的 `process_question_type` 函數**:
✅ 添加時間表現分類計算邏輯 (Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct等)
✅ 實現SFE (Systematic Foundational Error) 檢測
✅ 添加基於時間和難度的診斷參數分配

**2. 新增的輔助函數**:
✅ `calculate_time_performance_category`: 計算時間表現分類
✅ `get_max_correct_difficulty`: 獲取SFE檢測所需的最大正確難度
✅ `get_time_specific_parameters`: 基於時間表現添加診斷參數
✅ `get_difficulty_specific_parameters`: 基於難度添加診斷參數
✅ `calculate_override_conditions`: 計算macro建議觸發條件

**3. 實現的核心邏輯**:
✅ 時間相對快慢判斷 (基於RELATIVELY_FAST_MULTIPLIER)
✅ 六種時間表現分類: Fast/Normal/Slow + Correct/Wrong
✅ SFE檢測: 錯題難度低於該題型最高答對難度
✅ 診斷參數分配: 基於題型、內容領域、時間表現組合

**4. 修復的問題**:
✅ 命名不一致問題: `DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK` → `DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`
✅ 添加缺失的翻譯參數:
   - `DI_EFFICIENCY_BOTTLENECK_LOGIC`
   - `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE`
   - `DI_EFFICIENCY_BOTTLENECK_INTEGRATION`

### 修復效果:
1. ✅ DI診斷報告現在會正確顯示時間表現分類
2. ✅ 診斷標籤會根據表現模式正確生成
3. ✅ SFE檢測正常工作
4. ✅ Macro和Case建議會基於實際診斷結果觸發
5. ✅ 與V、Q模組的實現模式保持一致
6. ✅ 所有診斷參數都有正確的中英文翻譯
7. ✅ 參數命名與翻譯系統完全一致

### 技術細節:
- 使用RELATIVELY_FAST_MULTIPLIER (0.8) 判斷相對快速
- 實現六種時間表現分類的完整邏輯
- 添加題型特定的診斷參數映射
- 支援數學相關/非數學相關內容領域的不同參數
- 實現完整的override條件計算 (錯誤率≥40% 或 超時率≥30%)
- 修復所有翻譯系統相關問題

Mistake: DI模組process_question_type函數為空實現 + 參數命名不一致 + 缺失翻譯
Wrong:
```python
def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """Process diagnostic logic for a specific question type."""
    # Implementation details...
    # (This is a simplified version - the actual implementation would be more complex)
    
    override_info = {
        'override_triggered': False,
        'Y_agg': None,
        'Z_agg': None,
        'triggering_error_rate': 0.0,
        'triggering_overtime_rate': 0.0
    }
    
    return q_type_df, override_info

# 錯誤的參數命名
'DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK'

# 缺失的翻譯參數
# DI_EFFICIENCY_BOTTLENECK_* 參數無翻譯
```

Correct:
```python
def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """
    Process diagnostic logic for a specific question type.
    Implementation of DI Chapter 3 diagnostic rules.
    """
    # 完整實現包括:
    # 1. 計算時間表現分類 (Fast/Slow/Normal + Correct/Wrong)  
    # 2. SFE檢測 (錯題難度 < 最高答對難度)
    # 3. 分配相應的診斷參數 (基於時間、難度、題型)
    # 4. 計算override觸發條件 (錯誤率≥40% 或 超時率≥30%)
    
    processed_df = q_type_df.copy()
    
    # 為每個題目計算時間表現分類和診斷參數
    for idx, row in processed_df.iterrows():
        time_category = calculate_time_performance_category(
            q_time, is_correct, is_overtime, avg_time
        )
        processed_df.loc[idx, 'time_performance_category'] = time_category
        
        # 對有效題目進行診斷參數分配
        if not is_invalid:
            # SFE檢測、時間參數、難度參數等
            # ...完整實現邏輯
    
    return processed_df, override_info

# 正確的參數命名
'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK' 

# 完整的翻譯參數
'DI_EFFICIENCY_BOTTLENECK_LOGIC': "DI 效率瓶頸: 邏輯推理速度",
'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': "DI 效率瓶頸: 圖表解讀速度", 
'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': "DI 效率瓶頸: 多源整合速度",
```

### 後續修正 (第二次錯誤):
錯誤仍然出現在 `process_question_type` 函數第187行，當設置 `diagnostic_params` 列表值時。

**進一步修正**: 將所有單行索引設置從 `.loc[idx, col]` 改為 `.at[idx, col]`
- `.at` 方法更適合設置單一位置的值，特別是對於列表等複雜對象
- 避免了 pandas 在 `.loc` 方法中的索引對齊檢查導致的錯誤
- 提升了設置操作的效率和穩定性

**影響範圍**:
- `processed_df.at[idx, 'diagnostic_params'] = current_params`
- `processed_df.at[idx, 'time_performance_category'] = time_category`  
- `processed_df.at[idx, 'is_sfe'] = True`

## DI 模組 Pandas 索引設置錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed pandas DataFrame index assignment error in DI diagnosis module.

### 問題描述:
DI模組在診斷過程中出現 `ValueError: Must have equal len keys and value when setting with an iterable` 錯誤，發生在 analysis.py 第185行的 DataFrame 索引設置操作。

### 根本原因:
在 `diagnose_root_causes` 函數中，第78行嘗試將整個 processed_df 賦值給 df_diagnosed 的子集：
```python
df_diagnosed.loc[q_type_mask, :] = processed_df
```
這會導致索引對齊問題，特別是當兩個 DataFrame 的索引不完全匹配時。

### 修復過程:

Mistake: DataFrame 整行賦值導致索引對齊錯誤
Wrong:
```python
# 嘗試整行賦值，可能導致索引不匹配
df_diagnosed.loc[q_type_mask, :] = processed_df
```

Correct:
```python
# 只更新需要的特定列，使用 .values 避免索引對齊問題
df_diagnosed.loc[q_type_mask, 'diagnostic_params'] = processed_df['diagnostic_params'].values
df_diagnosed.loc[q_type_mask, 'is_sfe'] = processed_df['is_sfe'].values
df_diagnosed.loc[q_type_mask, 'time_performance_category'] = processed_df['time_performance_category'].values
```

### 技術細節:
1. **錯誤原因**: pandas 在進行 DataFrame 賦值時會嘗試按索引對齊數據，當索引不匹配時會產生長度不等的錯誤
2. **解決方案**: 使用 `.values` 屬性來獲取底層的 numpy 數組，避免索引對齊，只更新特定的必要列
3. **安全性**: 這種方法確保只更新診斷邏輯中實際修改的列，避免意外覆蓋其他數據

### 修復效果:
1. ✅ 消除了 DataFrame 索引賦值錯誤
2. ✅ 保持了診斷邏輯的完整性
3. ✅ 避免了索引對齊問題
4. ✅ 確保了只更新必要的欄位

## DI科診斷標籤映射邏輯與標準文件一致性修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully aligned DI module diagnostic tag mapping logic with `diagnostic_tags_summary.md` standard.

### 問題描述:
用戶要求確保DI科的診斷標籤映射邏輯與 `diagnostic_tags_summary.md` 文檔中的標準完全一致，特別是基於 `(時間表現類別, 題型, 內容領域)` 的精確標籤分配。

### 修復過程:

**1. 建立完整的DI_PARAM_ASSIGNMENT_RULES字典:**
- 實現基於 `(time_category, question_type, content_domain)` 的精確標籤映射
- 覆蓋所有時間表現類別: Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct
- 支援所有DI題型: Data Sufficiency, Two-part analysis, Graph and Table, Multi-source reasoning
- 區分內容領域: Math Related, Non-Math Related

**2. 修正行為標籤檢測邏輯:**

Mistake: 行為標籤檢測邏輯不符合標準文件規定
Wrong:
```python
# 粗心檢測使用錯誤的計算基準
fast_wrong_rate = fast_wrong_count / total_valid  # 使用全部有效題目作分母

# 早期衝刺檢測邏輯過於簡化
if q_time < avg_time * 0.5:  # 使用平均時間50%作標準
```

Correct:
```python
# 粗心檢測使用正確的計算基準 - 符合標準文件
total_fast_questions = fast_wrong_mask.sum() + fast_correct_mask.sum()
fast_wrong_rate = fast_wrong_count / total_fast_questions  # 使用快速作答題目作分母

# 早期衝刺檢測基於前1/3題目且用時<1分鐘
first_third_count = max(1, total_questions // 3)
if q_time < 1.0:  # 用時 < 1分鐘
```

**3. 確保標籤名稱完全符合標準:**
- SFE標籤: `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`
- 行為標籤: `DI_BEHAVIOR_CARELESSNESS_ISSUE`, `DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`
- 具體題目粗心標籤: `DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION`

**4. 實現MSR題型特殊處理:**
- MSR題型在 Normal Time & Wrong 和 Slow & Wrong 類別中添加 `DI_MULTI_SOURCE_INTEGRATION_ERROR`
- MSR題型在困難類標籤中添加 `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`

### 關鍵改進:

**精確的時間表現分類映射:**
```python
DI_PARAM_ASSIGNMENT_RULES = {
    ('Fast & Wrong', 'Data Sufficiency', 'Math Related'): [
        'DI_READING_COMPREHENSION_ERROR__VOCABULARY',
        'DI_CONCEPT_APPLICATION_ERROR__MATH',
        # ... 完整標籤列表
    ],
    # ... 覆蓋所有 (時間類別, 題型, 領域) 組合
}
```

**改進的行為模式檢測:**
- 粗心問題觸發閾值: 快錯率 > 25% (基於快速作答題目)
- 早期衝刺檢測: 前1/3題目中存在用時<1分鐘的題目
- 具體題目標籤: Fast & Wrong 題目自動添加細節忽略標籤

**標準化的標籤分配邏輯:**
- 基於標準化的題型和領域名稱映射
- 精確的時間表現類別計算
- 符合MD文檔的完整標籤集合

### 修復效果:
1. ✅ DI科診斷標籤映射邏輯完全符合 `diagnostic_tags_summary.md` 標準
2. ✅ 所有標籤名稱與文檔完全一致
3. ✅ 行為標籤檢測邏輯精確實現標準要求
4. ✅ MSR題型特殊標籤正確處理
5. ✅ SFE檢測邏輯與V科、Q科保持一致

**Result**: DI科診斷模組現在完全符合診斷標籤摘要文件的標準，提供精確且一致的診斷標籤分配。

## DI 英文文檔診斷標籤對齊修復 (2025-06-01)

**Status: FIXED ✅**

Successfully aligned English DI documentation diagnostic parameters with Chinese version.

### 問題描述:
用戶要求將英文版本DI文檔 (en-gmat-di-v1.3.md) 的附錄診斷標籤與中文版本 (gmat-di-score-logic-dustin-v1.6.md) 對齊。

### 根本原因:
英文版本使用簡化的診斷標籤系統，而中文版本使用詳細的細分標籤系統。

### 修復過程:

**主要差異發現:**
1. **閱讀理解標籤:** 英文版本使用 `DI_READING_COMPREHENSION_ERROR`，中文版本細分為詞彙、語法、邏輯、領域四個子類別
2. **圖表解讀標籤:** 英文版本使用 `DI_GRAPH_TABLE_INTERPRETATION_ERROR`，中文版本分為圖形和表格兩個子類別
3. **參數命名:** 中文版本使用雙下劃線格式 (如 `__VOCABULARY`, `__MATH`)
4. **行為標籤:** 英文版本缺少詳細的行為類別標籤

Mistake: 英文DI文檔使用簡化的診斷標籤系統
Wrong:
```markdown
| `DI_READING_COMPREHENSION_ERROR`           | DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math) |
| `DI_GRAPH_TABLE_INTERPRETATION_ERROR`      | DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙            |
| `DI_CONCEPT_APPLICATION_ERROR`             | DI 概念應用 (Math): 數學觀念/公式應用錯誤/障礙      |
```

Correct:
```markdown
| `DI_READING_COMPREHENSION_ERROR__VOCABULARY` | DI 閱讀理解錯誤: 詞彙理解                          |
| `DI_READING_COMPREHENSION_ERROR__SYNTAX`     | DI 閱讀理解錯誤: 句式理解                          |
| `DI_READING_COMPREHENSION_ERROR__LOGIC`      | DI 閱讀理解錯誤: 邏輯理解                          |
| `DI_READING_COMPREHENSION_ERROR__DOMAIN`     | DI 閱讀理解錯誤: 領域理解                          |
| `DI_GRAPH_INTERPRETATION_ERROR__GRAPH`       | DI 圖表解讀錯誤: 圖形信息解讀                      |
| `DI_GRAPH_INTERPRETATION_ERROR__TABLE`       | DI 圖表解讀錯誤: 表格信息解讀                      |
| `DI_CONCEPT_APPLICATION_ERROR__MATH`         | DI 概念應用 (數學) 錯誤: 數學觀念/公式應用         |
```

### 修復內容:

**1. 完整替換附錄A診斷標籤系統:**
- 添加按時間表現分類的詳細診斷標籤列表 (Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct)
- 包含所有閱讀理解細分類別: VOCABULARY, SYNTAX, LOGIC, DOMAIN
- 包含圖表解讀細分類別: GRAPH, TABLE
- 包含數學和非數學領域的詳細區分
- 添加MSR特定參數和行為模式參數

**2. 統一參數命名格式:**
- 使用雙下劃線格式: `DI_CATEGORY__SUBCATEGORY`
- 數學相關標籤使用 `__MATH` 後綴
- 非數學相關標籤使用 `__NON_MATH` 後綴
- 行為標籤使用 `DI_BEHAVIOR__` 前綴

**3. 添加完整的標籤分類結構:**
- Reading & Understanding (閱讀與理解)
- Concept & Application (概念與應用)
- Logical Reasoning (邏輯推理)
- Data Handling & Calculation (數據處理與計算)
- MSR Specific (MSR特定)
- Question Type Specific (題型特定)
- Foundational & Efficiency (基礎與效率)
- Behavior (行為)

### 修復效果:
1. ✅ 英文版本診斷標籤完全與中文版本一致
2. ✅ 標籤命名格式統一為詳細的細分系統
3. ✅ 按時間表現分類的診斷參數體系完整
4. ✅ 包含所有MSR特定和行為模式標籤
5. ✅ 保持了中英文對照表的完整性

**結果:** 英文DI文檔附錄現在與中文版本完全一致，使用相同的詳細診斷標籤系統，確保兩個版本的診斷參數體系統一。

## V科文檔 v1.6 版本一致性驗證完成 (2025-06-01)

**Status: VERIFIED CONSISTENT ✅**

Successfully verified V科中英文文檔（v1.6版本）已完全一致，無需修復。

### 驗證範圍：

**全文檔逐章節比對:**
1. ✅ 第零章：核心輸入數據和配置
2. ✅ 第一章：整體時間策略與數據有效性評估
3. ✅ 第二章：多維度表現分析
4. ✅ 第三章：根本原因診斷與分析
5. ✅ 第四章：核心技能/題型/領域參考
6. ✅ 第五章：特殊模式觀察與粗心評估
7. ✅ 第六章：基礎能力覆蓋規則
8. ✅ 第七章：練習規劃與建議
9. ✅ 第八章：診斷總結與後續行動
10. ✅ 附錄A：診斷標籤參數與中文對照表

### 一致性確認：

**1. 參數系統完全一致：**
- 英文版本使用詳細的分層診斷參數系統
- 所有診斷參數完全對應中文版本
- 參數命名格式統一（如：`CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP`）
- SFE參數正確命名：`FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE`

**2. 診斷流程邏輯完全一致：**
- Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct 診斷參數列表完全相同
- 時間表現分類標準一致
- SFE檢測邏輯完全相同
- 行為模式檢測邏輯一致

**3. 附錄A對照表完全一致：**
- 包含所有分層診斷參數的完整映射
- 英文參數與中文描述完全對應
- 參數分類結構完全相同

**4. 章節結構與內容完全一致：**
- 所有章節目標、重點、邏輯完全相同
- 診斷標籤精確性限制說明完全相同
- 未來改進機制說明完全相同
- 技能豁免規則和覆蓋規則完全相同

### 驗證結果：
✅ V科中英文文檔v1.6版本已實現完全一致性
✅ 無需任何修復或調整
✅ 兩個版本可安全並行使用
✅ 診斷參數系統完全統一

**結論：** V科文檔中英文版本v1.6已達到完全一致狀態，診斷框架和技術規格完全對齊。之前的修復工作已成功完成，當前版本無需進一步調整。

## DI診斷模塊覆蓋規則閾值修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully fixed DI module override rule thresholds to match documentation standards.

### 問題描述:
DI模塊中的覆蓋規則閾值設定與標準文檔不一致，實現中使用了錯誤率40%和超時率30%的閾值，而文檔要求使用50%和50%。

### 根本原因:
在`gmat_diagnosis_app/diagnostics/di_modules/analysis.py`文件中，兩個函數使用了錯誤的閾值：
1. `calculate_override_conditions` 函數
2. `check_foundation_override` 函數

### 修復過程:

Mistake: DI模塊覆蓋規則閾值與文檔不一致
Wrong:
```python
# 在 calculate_override_conditions 函數中
error_threshold = 0.4  # 40%
overtime_threshold = 0.3  # 30%

# 在 check_foundation_override 函數中  
override_threshold_error = 0.4  # 40%
override_threshold_overtime = 0.3  # 30%
```

Correct:
```python
# 在 calculate_override_conditions 函數中
error_threshold = 0.5  # 50% - 修正為與文檔一致
overtime_threshold = 0.5  # 50% - 修正為與文檔一致

# 在 check_foundation_override 函數中
override_threshold_error = 0.5  # 50% - 修正為與文檔一致  
override_threshold_overtime = 0.5  # 50% - 修正為與文檔一致
```

### 修復效果:
1. ✅ DI模塊覆蓋規則閾值完全符合文檔標準
2. ✅ 錯誤率和超時率閾值統一為50%/50%
3. ✅ 與Q/V模塊保持一致的覆蓋規則標準
4. ✅ 診斷參數觸發條件更加嚴格和準確

### 技術背景:
根據GMAT診斷文檔第五章標準，當某題型或技能的錯誤率或超時率超過50%時才觸發覆蓋規則，生成特殊的練習建議。此修復確保了DI模塊與文檔規範的完全一致性。

## DI豁免規則文檔符合性優化和MSR錯誤處理改進 (2025-01-30)

**Status: COMPLETED ✅**

Successfully optimized DI exemption rules to fully comply with documentation standards and improved MSR time handling error recovery mechanisms.

### 1. 豁免規則文檔符合性優化

**問題描述:**
DI豁免規則實現基本正確，但需要更明確地遵循文檔第五章標準，特別是有效題目篩選和條件檢查。

**修復過程:**

Mistake: 豁免規則邏輯可以更明確地遵循文檔標準
Wrong:
```python
# 簡化的豁免條件檢查
if not group_df.empty and not ((group_df['is_correct'] == False) | (group_df['overtime'] == True)).any():
    exempted_type_domain_combinations.add((q_type, domain))
```

Correct:
```python
# 按照文檔第五章標準：首先篩選有效題目
valid_questions = group_df[group_df.get('is_invalid', False) == False]
if valid_questions.empty:
    continue  # 如果沒有有效題目，跳過此組合

# 條件一：所有有效題目必須全部正確 
condition1_all_correct = valid_questions['is_correct'].all()

# 條件二：所有有效題目必須全部無超時
condition2_no_overtime = ~valid_questions['overtime'].any()

# 同時滿足兩個條件才豁免
if condition1_all_correct and condition2_no_overtime:
    exempted_type_domain_combinations.add((q_type, domain))
```

### 2. MSR時間處理錯誤處理機制改進

**問題描述:**
MSR時間處理在多個層級存在錯誤處理，但建議生成階段的錯誤處理可以更加詳細和健壯。

**發現的三層錯誤處理架構:**
1. **數據預處理階段**: 處理MSR組識別、閱讀時間計算的數據缺失問題
2. **超時計算階段**: 處理群組超時和個別超時計算中的數據缺失
3. **建議生成階段**: 處理時間限制建議計算中的數據問題

**修復過程:**

Mistake: MSR建議生成階段的錯誤處理不夠詳細
Wrong:
```python
triggering_group_ids = group_df['msr_group_id'].unique()
group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
if group_times.notna().any():
    max_group_time_minutes = group_times.max()
    # 簡化的錯誤處理...
```

Correct:
```python
triggering_group_ids = group_df['msr_group_id'].unique()
# 過濾掉NaN的group_id
triggering_group_ids = [gid for gid in triggering_group_ids if pd.notna(gid)]

if triggering_group_ids:
    group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
    valid_group_times = group_times.dropna()
    
    if len(valid_group_times) > 0:
        max_group_time_minutes = valid_group_times.max()
        if pd.notna(max_group_time_minutes) and max_group_time_minutes > 0:
            # 正常計算邏輯...
        else: 
            logging.warning(f"[DI Case Reco MSR] Invalid max_group_time_minutes...")
            max_z_minutes = 6.0
    else: 
        logging.warning(f"[DI Case Reco MSR] No valid group times found...")
        max_z_minutes = 6.0
```

### 修復效果:
1. ✅ DI豁免規則完全符合文檔第五章標準
2. ✅ 明確區分有效題目篩選和條件檢查
3. ✅ MSR時間處理錯誤處理更加健壯
4. ✅ 增加詳細的警告日誌協助調試
5. ✅ 多層級的錯誤回退機制確保系統穩定性

**技術改進:**
- 豁免規則按照文檔標準先篩選有效題目，再檢查兩個條件
- MSR錯誤處理增加NaN過濾、數據有效性檢查、詳細警告
- 保持6.0分鐘的默認回退值，確保MSR建議生成不會失敗

## 三科診斷報告語言切換即時更新修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully implemented real-time language switching for diagnostic reports in all three subjects (Q, V, DI).

### 問題描述:
用戶反映三個科目的文字診斷報告在i18n語言切換後沒有即時更新，需要重新生成報告才會顯示新語言。

### 根本原因:
診斷報告的內容在分析完成時生成為完整的文字字符串，並存儲在`st.session_state.report_dict`中。這些內容是固定字符串而非動態翻譯鍵，因此語言切換時不會自動更新。

### 修復過程:

**1. 創建報告重新生成機制**

在`gmat_diagnosis_app/utils/report_regeneration.py`中實現了完整的報告重新生成邏輯：

Mistake: 診斷報告使用固定文字存儲，語言切換時不會更新
Wrong:
```python
# 語言切換時只更新i18n系統，報告內容不變
if selected_language != current_lang:
    st.session_state.current_language = selected_language
    set_language(selected_language)
    st.rerun()
```

Correct:
```python
# 語言切換時重新生成診斷報告
if selected_language != current_lang:
    st.session_state.current_language = selected_language
    set_language(selected_language)
    
    # Re-generate diagnostic reports if analysis is complete
    if st.session_state.get("diagnosis_complete", False) and st.session_state.get("processed_df") is not None:
        from gmat_diagnosis_app.utils.report_regeneration import regenerate_reports_for_language_switch
        regenerate_reports_for_language_switch()
    
    st.rerun()
```

**2. 實現完整的重新生成函數**

```python
def regenerate_reports_for_language_switch():
    """
    Regenerate diagnostic reports when language is switched.
    Re-runs the diagnosis logic on existing processed data to get reports in the new language.
    """
    # 重新獲取處理過的數據
    df_final = st.session_state.get("processed_df")
    
    # 恢復時間壓力設定
    time_pressure_map = {}
    for subject in SUBJECTS:
        time_pressure_key = f"{subject.lower()}_time_pressure"
        # ... 恢復邏輯 ...
    
    # 重新生成每個科目的報告
    temp_report_dict = {}
    for subject in SUBJECTS:
        if subject == 'Q':
            subj_results, subj_report, df_subj_diagnosed = diagnose_q(df_subj)
        elif subject == 'DI':
            subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_subj, time_pressure)
        elif subject == 'V':
            subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
        
        temp_report_dict[subject] = final_report_for_subject
    
    # 更新session state
    st.session_state.report_dict = temp_report_dict
    
    # 重新生成AI綜合報告（如有）
    if st.session_state.get('master_key'):
        consolidated_report = generate_ai_consolidated_report(temp_report_dict, st.session_state.master_key)
        st.session_state.consolidated_report = consolidated_report
```

### 修復效果:
1. ✅ 三個科目診斷報告支持即時語言切換
2. ✅ 語言切換時自動重新生成報告內容
3. ✅ 保持原有診斷邏輯和數據完整性
4. ✅ AI綜合報告也會重新生成（如適用）
5. ✅ 用戶體驗改善：無需重新分析即可看到新語言報告

### 技術實現:
- 在語言切換邏輯中檢測是否已有診斷結果
- 如有結果則調用報告重新生成函數
- 重新生成過程復用原有診斷邏輯，確保一致性
- 保持時間壓力設定和其他分析參數
- 支持OpenAI報告總結功能的重新生成

**用戶影響:** 現在用戶可以在查看結果時隨時切換語言，診斷報告會立即以新語言顯示，大幅提升了多語言使用體驗。

## MSR Group ID 生成邏輯完整修復 (2025-06-02)

**Status: COMPLETELY FIXED ✅**

Successfully fixed MSR group ID generation logic in DI preprocessor, implementing both MSR Set ID and contiguity-based grouping according to documentation standards.

### 問題描述:
用戶詢問代碼中是否有MSR group ID計算和標記的規則，發現MSR group ID沒有正確生成，導致recommendations模組無法獲得valid group IDs。

### 根本原因:
DI預處理器中MSR group ID生成邏輯存在以下問題：
1. `_identify_msr_groups`函數在處理MSR Set ID時，對所有行包括非MSR行都生成了group ID
2. `df_processed.update(df_di_subset)`操作失敗，因為主DataFrame沒有MSR相關欄位
3. 後續的欄位初始化邏輯會覆蓋已計算的MSR數據

### 修復過程:

**修復1: 改進MSR group識別邏輯**

Mistake: MSR group ID對所有行都設置值，包括非MSR題目
Wrong:
```python
if 'MSR Set ID' in df_di_subset.columns and df_di_subset['MSR Set ID'].notna().any():
    df_di_subset['msr_group_id'] = 'MSR-' + df_di_subset['MSR Set ID'].astype(str)
```

Correct:
```python
if 'MSR Set ID' in df_di_subset.columns and df_di_subset['MSR Set ID'].notna().any():
    # 修復: 先初始化所有行為NaN，然後只為有MSR Set ID的行設置值
    df_di_subset['msr_group_id'] = pd.Series(index=df_di_subset.index, dtype='object')
    msr_set_mask = df_di_subset['MSR Set ID'].notna()
    df_di_subset.loc[msr_set_mask, 'msr_group_id'] = 'MSR-' + df_di_subset.loc[msr_set_mask, 'MSR Set ID'].astype(str)
    df_di_subset.loc[~msr_set_mask, 'msr_group_id'] = pd.NA
```

**修復2: 解決DataFrame update操作失敗**

Mistake: 嘗試update不存在的欄位導致失敗
Wrong:
```python
df_di_subset = _identify_msr_groups(df_di_subset)
# ... MSR計算邏輯 ...
df_processed.update(df_di_subset)  # 失敗：msr_group_id等欄位不存在
```

Correct:
```python
df_di_subset = _identify_msr_groups(df_di_subset)
# ... MSR計算邏輯 ...

# 修復: 先確保主DataFrame中有所有MSR欄位，然後才進行update
msr_all_cols = ['msr_group_id', 'msr_group_total_time', 'msr_group_num_questions', 'msr_reading_time', 'is_first_msr_q']
for col in msr_all_cols:
    if col not in df_processed.columns:
        if col == 'msr_group_id':
            df_processed[col] = pd.NA
        elif col == 'is_first_msr_q':
            df_processed[col] = False
        else:
            df_processed[col] = 0.0

df_processed.update(df_di_subset)
```

**修復3: 改進MSR數據更新方式**

Mistake: 使用df.update()可能覆蓋已計算的數據
Wrong:
```python
# Update the DI subset with new columns
df_di_subset.update(df_msr_part)
```

Correct:
```python
# 修復: 使用更精確的方式更新MSR相關列，避免覆蓋其他數據
msr_cols_to_update = ['msr_group_total_time', 'msr_group_num_questions', 'msr_reading_time', 'is_first_msr_q']
for col in msr_cols_to_update:
    if col in df_msr_part.columns:
        df_di_subset.loc[msr_rows_mask, col] = df_msr_part[col].values
```

### 實現的功能:

**1. MSR Set ID方式 (優先使用):**
- 當數據包含`MSR Set ID`欄位時，使用該ID作為group標識
- 生成格式：`MSR-1`, `MSR-2`等
- 只對有MSR Set ID值的MSR題目設置group ID

**2. Contiguity方式 (fallback):**
- 當沒有MSR Set ID時，基於相鄰MSR題目自動分組
- 生成格式：`MSRG-1`, `MSRG-2`等
- 根據題目位置和題型自動識別連續的MSR題組

**3. 完整的MSR計算:**
- `msr_group_total_time`: 題組總時間
- `msr_group_num_questions`: 題組題目數量
- `msr_reading_time`: 閱讀時間 (僅對多題組的第一題)
- `is_first_msr_q`: 是否為題組第一題標記

### 修復效果:
1. ✅ MSR group ID正確生成 - 支持MSR Set ID和contiguity兩種方式
2. ✅ MSR相關時間計算正常工作 - 群組總時間、題目數量等
3. ✅ 閱讀時間計算符合文檔標準 - 第一題時間減去其他題平均時間
4. ✅ 消除recommendations模組中的group ID缺失警告
5. ✅ 支援文檔v1.6第六章的完整MSR處理邏輯
6. ✅ 提供robust的錯誤處理和fallback機制

**測試結果:**
- 有MSR Set ID的數據: 正確生成`MSR-1.0`, `MSR-2.0`等group ID
- 無MSR Set ID的數據: 正確生成`MSRG-1`, `MSRG-2`等group ID  
- MSR群組時間計算: 正確計算group total time和number of questions
- 與recommendations模組整合: 完全消除group ID缺失警告

**結論:** DI預處理器現在完全符合文檔標準，正確實現MSR group ID生成、時間計算和相關標記邏輯，為後續診斷和建議生成提供完整的MSR群組數據支持。

## 國際化缺失修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed two internationalization issues identified by the user:

### 問題 1: DI_MSR_READING_COMPREHENSION_BARRIER 標籤未國際化

**根本原因:**
DI_MSR_READING_COMPREHENSION_BARRIER 診斷標籤在翻譯檔案中缺少對應的翻譯鍵值，導致在繁體中文界面中顯示英文原文。

Mistake: DI MSR 閱讀障礙標籤缺少國際化翻譯
Wrong:
```python
# zh_TW.py 和 en.py 中都缺少 DI_MSR_READING_COMPREHENSION_BARRIER 的翻譯
# 導致系統無法找到翻譯，顯示原始英文鍵值
```

Correct:
```python
# zh_TW.py 中添加:
'DI_MSR_READING_COMPREHENSION_BARRIER': "DI MSR 閱讀障礙：題組整體閱讀時間過長",

# en.py 中添加:
'DI_MSR_READING_COMPREHENSION_BARRIER': "DI MSR Reading Barrier: Excessive Overall Reading Time for the Group",
```

### 問題 2: Q診斷報告中出現英文鍵值而非翻譯

**根本原因:**
在 `gmat_diagnosis_app/diagnostics/q_modules/reporting.py` 第134行，核心問題列表使用了硬編碼的英文字符串而非翻譯函數調用。

Mistake: Q診斷報告使用硬編碼英文字符串而非翻譯鍵值
Wrong:
```python
# reporting.py 第134行
core_issues = ["Q Carelessness Issue: Detail Omission", "Q Concept Application Error: Mathematical Concept/Formula Application", "Q Calculation Error: Mathematical Calculation", "Q Reading Comprehension Error: Text Understanding"]
if sfe_skills_involved:
    core_issues.append("Q Foundation Mastery: Application Instability (Special Focus Error)")
```

Correct:
```python
# reporting.py 修正後
core_issues = [t("Q_CARELESSNESS_DETAIL_OMISSION"), t("Q_CONCEPT_APPLICATION_ERROR"), t("Q_CALCULATION_ERROR"), t("Q_READING_COMPREHENSION_ERROR")]
if sfe_skills_involved:
    core_issues.append(t("Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE"))
```

### 修復結果:
1. ✅ DI_MSR_READING_COMPREHENSION_BARRIER 標籤現已完全國際化，支持繁體中文和英文雙語顯示
2. ✅ Q診斷報告中的核心問題列表現已使用翻譯函數，在中文界面中正確顯示中文翻譯
3. ✅ 所有相關翻譯鍵值在 zh_TW.py 和 en.py 中都已正確配置
4. ✅ 測試確認翻譯功能正常工作，能正確返回對應語言的翻譯文字

**影響範圍:**
- DI 診斷模組：MSR 閱讀障礙標籤國際化
- Q 診斷模組：報告生成中的核心問題列表國際化
- 用戶界面：繁體中文界面將不再出現英文鍵值，提升用戶體驗

## 下載功能優化與檔案組合修復 (2025-06-02)

**Status: COMPLETED ✅**

Successfully implemented user's request to remove individual subject download buttons and enhance the edit diagnostic tags download functionality.

### 問題描述:
用戶要求：
1. 把三個科目的「下載..科詳細數據」按鈕拿掉
2. 在編輯診斷標籤區域，將「下載編輯後試算表」改為「下載編輯後試算表與文字報告」
3. 讓三科的文字報告變成md檔，讓用戶跟原來編輯後的xlsx檔一起下載

### 修復過程:

**修復1: 移除個別科目的下載詳細數據按鈕**

Mistake: 三個科目頁面都有各自的下載詳細數據按鈕
Wrong:
```python
# 在 display_subject_results 函數中的下載按鈕
tab_container.download_button(
    t("download_subject_detailed_data").format(subject),
    data=excel_bytes,
    file_name=f"{today_str}_GMAT_{subject}_detailed_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

Correct:
```python
# 將整個下載按鈕區段註釋掉
# 4. Download Button (removed per user request)
# Commenting out the download detailed data button for individual subjects
"""
try:
    # ... 原本的下載邏輯 ...
except Exception as e:
    # ... 錯誤處理 ...
"""
```

**修復2: 創建組合下載功能**

新增了 `create_combined_download_zip` 函數在 `excel_utils.py` 中：

```python
def create_combined_download_zip(df, column_map, report_dict):
    """
    創建包含Excel和Markdown報告的zip檔案
    
    Args:
        df: 包含數據的DataFrame
        column_map: 欄位名稱映射字典
        report_dict: 包含各科目文字報告的字典
        
    Returns:
        bytes: ZIP文件的字節流
    """
    import zipfile
    import io
    from datetime import datetime
    
    # Create zip buffer
    zip_buffer = io.BytesIO()
    
    # Generate timestamp for filenames
    today_str = datetime.now().strftime('%Y%m%d')
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add Excel file
        excel_bytes = to_excel(df, column_map)
        zip_file.writestr(f"{today_str}_GMAT_edited_diagnostic_data.xlsx", excel_bytes)
        
        # Add markdown reports for each subject
        for subject in ['Q', 'V', 'DI']:
            if subject in report_dict and report_dict[subject]:
                # Clean the markdown content (remove HTML tags if any)
                clean_report = report_dict[subject]
                
                # Add subject report as markdown file
                zip_file.writestr(
                    f"{today_str}_GMAT_{subject}_diagnostic_report.md", 
                    clean_report.encode('utf-8')
                )
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
```

**修復3: 更新編輯診斷標籤的下載按鈕**

Mistake: 編輯診斷標籤區域只下載xlsx檔案
Wrong:
```python
# 原本只下載Excel檔案
st.download_button(
    label=t('edit_tags_download_button_label'),
    data=excel_bytes,
    file_name=f"{today_str}_GMAT_edited_diagnostic_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="actual_download_excel_button_col3_rerun",
    use_container_width=True
)
```

Correct:
```python
# 使用組合下載功能
# Get current report dict from session state
report_dict = st.session_state.get('report_dict', {})

# Create zip with both Excel and MD files
zip_bytes = create_combined_download_zip(
    df_to_export_final, 
    excel_column_map_for_export_final, 
    report_dict
)

# Trigger download
st.download_button(
    label=t('edit_tags_download_button_combined_label'),
    data=zip_bytes,
    file_name=f"{today_str}_GMAT_edited_data_and_reports.zip",
    mime="application/zip",
    key="actual_download_combined_button_col3_rerun",
    use_container_width=True
)
```

**修復4: 更新翻譯系統**

添加新的翻譯鍵值：
- 中文: `'edit_tags_download_button_combined': "下載編輯後試算表與文字報告"`
- 英文: `'edit_tags_download_button_combined': "Download Modified Spreadsheet & Text Reports"`

### 修復效果:
1. ✅ 移除了三個科目頁面的個別下載按鈕，簡化了界面
2. ✅ 編輯診斷標籤區域的下載按鈕現在下載zip檔案
3. ✅ zip檔案包含：
   - 編輯後的Excel試算表 (YYYYMMDD_GMAT_edited_diagnostic_data.xlsx)
   - 三個科目的Markdown文字報告 (YYYYMMDD_GMAT_Q/V/DI_diagnostic_report.md)
4. ✅ 按鈕文字更新為「下載編輯後試算表與文字報告」
5. ✅ 支援繁體中文和英文雙語界面
6. ✅ 保持原有的變更檢查邏輯 (未儲存變更時會提示警告)

**技術實現:**
- 使用Python的zipfile模組創建壓縮檔案
- 從session_state.report_dict獲取各科目的文字報告
- 將文字報告以UTF-8編碼儲存為.md檔案
- 保持原有的Excel檔案生成邏輯
- 更新了相關的翻譯鍵值以支援雙語

**用戶影響:**
現在用戶可以一次下載包含編輯後試算表和完整文字報告的組合檔案，更方便進行離線查看和與教師討論。

## 三科診斷報告合併為單一文字檔案修復 (2025-06-02)

**Status: COMPLETED ✅**

Successfully implemented user's request to combine all three subject reports into a single text file instead of separate markdown files.

### 問題描述:
用戶要求將三個科目的報告放在同一個txt檔裡讓用戶下載，而不是分別的md檔案。

### 修復過程:

**修復: 合併三科報告為單一txt檔案**

Mistake: 三個科目的報告分別存儲為獨立的md檔案
Wrong:
```python
# 原本的分別下載邏輯
for subject in ['Q', 'V', 'DI']:
    if subject in report_dict and report_dict[subject]:
        # Add subject report as markdown file
        zip_file.writestr(
            f"{today_str}_GMAT_{subject}_diagnostic_report.md", 
            clean_report.encode('utf-8')
        )
```

Correct:
```python
# 合併三科報告為單一txt檔案
combined_report_lines = []
combined_report_lines.append("GMAT 診斷報告綜合分析")
combined_report_lines.append("=" * 50)
combined_report_lines.append(f"生成日期: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")

subjects_order = ['Q', 'V', 'DI']
subject_names = {
    'Q': 'Quantitative (數學科)',
    'V': 'Verbal (語文科)', 
    'DI': 'Data Insights (數據洞察科)'
}

for i, subject in enumerate(subjects_order):
    if subject in report_dict and report_dict[subject]:
        combined_report_lines.append(f"{i+1}. {subject_names[subject]}")
        combined_report_lines.append("-" * 30)
        
        # 清理報告內容，移除HTML標籤，轉換markdown為純文字
        clean_report = re.sub(r'<[^>]+>', '', report_dict[subject])
        clean_report = re.sub(r'^#+\s*', '', clean_report, flags=re.MULTILINE)
        clean_report = re.sub(r'\n\s*\n', '\n\n', clean_report)
        
        combined_report_lines.append(clean_report.strip())
    else:
        combined_report_lines.append(f"{i+1}. {subject_names[subject]}")
        combined_report_lines.append("-" * 30)
        combined_report_lines.append(f"此科目暫無診斷報告數據")

combined_report_text = '\n'.join(combined_report_lines)
zip_file.writestr(
    f"{today_str}_GMAT_三科綜合診斷報告.txt", 
    combined_report_text.encode('utf-8')
)
```

### 實現的功能:
1. ✅ 將Q、V、DI三科的診斷報告合併為單一txt檔案
2. ✅ 添加完整的報告標題、日期、科目分隔
3. ✅ 自動移除HTML標籤和markdown格式，轉換為純文字
4. ✅ 為缺失報告的科目添加占位符說明
5. ✅ 保持原有的Excel檔案下載功能
6. ✅ 更新翻譯鍵值以反映新的文字報告格式

### 修復效果:
1. ✅ 下載的zip檔案現在包含：
   - Excel試算表檔案：`YYYYMMDD_GMAT_edited_diagnostic_data.xlsx`
   - 綜合文字報告：`YYYYMMDD_GMAT_三科綜合診斷報告.txt`
2. ✅ 文字報告格式化美觀，包含完整的標題和分隔
3. ✅ 支援繁體中文和英文界面
4. ✅ 提供離線閱讀和分享的便利性

**用戶影響:** 現在用戶可以獲得一個更方便的綜合文字報告，包含所有三科的診斷結果，適合打印、分享或與教師討論使用。

## 二級證據提示邏輯動態化改進 (2025-06-03)

**Status: COMPLETED ✅ - 動態二級證據建議實施**

### 問題背景:

**問題**: 用戶要求參考三個科目診斷報告中的二級證據提示邏輯，將expander「各科二級證據查找重點」中的硬編碼建議改為根據題型/領域/時間表現觸發映射的診斷標籤邏輯。

**改進目標**: 
1. 不要硬編碼的通用建議文字
2. 根據實際診斷參數動態生成具體的查找重點
3. 提供更精確、更有針對性的二級證據分析指導

### 實施內容:

**1. 創建動態二級證據工具函數**:
```python
# 新建檔案: gmat_diagnosis_app/utils/secondary_evidence_utils.py
- get_diagnostic_param_mapping(): 診斷參數到重點領域的映射
- generate_dynamic_secondary_evidence_suggestions(): 基於實際診斷參數生成建議
- get_question_type_specific_guidance(): 題型特定指導
- get_time_performance_specific_guidance(): 時間表現特定指導
```

**2. 修改全局警告系統**:
```python
# 修改檔案: gmat_diagnosis_app/session_manager.py
- check_global_diagnostic_tag_warning() 函數
- 從硬編碼翻譯字串改為動態建議生成
- 整合 generate_dynamic_secondary_evidence_suggestions()
```

**3. 增強結果顯示功能**:
```python
# 修改檔案: gmat_diagnosis_app/ui/results_display.py
- 新增 display_enhanced_secondary_evidence_expander() 函數
- 修改 display_global_tag_warning() 使用增強的expander
- 提供三層指導結構：
  * 基於診斷結果的具體建議
  * 按題型查找的詳細指導
  * 按時間表現查找的指導
  * 具體問題組合分析（最優先建議）
```

### 功能特點:

**1. 診斷參數映射覆蓋範圍**:
- Q科: 12個診斷參數（粗心、概念應用、計算錯誤、文字理解、基礎掌握等）
- V科: 6個診斷參數（CR邏輯鏈、RC詞彙/句式/推理、基礎掌握等）
- DI科: 10個診斷參數（文字理解、圖表解讀、數學概念、邏輯推理、MSR效率、基礎掌握等）

**2. 動態建議生成邏輯**:
- 從 processed_df 提取實際診斷參數
- 按科目分組並去重診斷參數
- 根據參數映射生成重點領域和查找策略
- 添加科目特定的一般性指導
- 包含樣本數量提醒

**3. 增強的expander功能**:
- **基於診斷結果的具體建議**: 根據實際觸發的診斷參數生成
- **詳細查找指導**: 按科目展開的三層結構
  * 按題型查找: 結合內容領域的題型特定指導
  * 按時間表現查找: 針對問題時間表現類別的指導
  * 具體組合分析: 顯示實際出現問題的具體組合（題型+領域+時間表現）

**4. 智能顯示邏輯**:
- 即使沒有觸發全局警告，也會顯示增強的expander
- 過濾掉正確的時間表現類別（Fast & Correct, Normal Time & Correct）
- 優先顯示具體問題組合，並標註題目數量

### 技術優勢:

**1. 非硬編碼設計**:
- 所有建議都基於實際數據動態生成
- 診斷參數映射可輕鬆擴展和修改
- 支援未來新增診斷參數

**2. 三科一致性**:
- 遵循Q、V、DI三科診斷報告中的二級證據邏輯
- 整合題型、內容領域、時間表現三個維度
- 符合診斷框架文檔的分析方法

**3. 用戶體驗**:
- 漸進式展開的信息層次
- 優先顯示最具體、最有針對性的建議
- 包含實際問題組合和題目數量統計

### 修正前後對比:

**修正前**:
```python
# 硬編碼的科目建議
if subject == 'Q':
    warning_info['secondary_evidence_suggestions'][subject] = t('global_tag_secondary_evidence_q')
elif subject == 'V':
    warning_info['secondary_evidence_suggestions'][subject] = t('global_tag_secondary_evidence_v')
elif subject == 'DI':
    warning_info['secondary_evidence_suggestions'][subject] = t('global_tag_secondary_evidence_di')
```

**修正後**:
```python
# 動態生成基於實際診斷參數的建議
dynamic_suggestions = generate_dynamic_secondary_evidence_suggestions(valid_df)
warning_info['secondary_evidence_suggestions'] = dynamic_suggestions

# 同時提供增強的expander，包含：
# - 基於診斷結果的具體建議
# - 按題型查找的詳細指導  
# - 按時間表現查找的指導
# - 具體問題組合分析
```

### 當前狀態:
動態二級證據提示邏輯已完全實施並整合到現有系統中。用戶現在可以看到：
1. 基於實際診斷參數的具體二級證據查找建議
2. 按題型、時間表現、具體組合的分層指導
3. 實際問題組合的優先建議與統計信息

該功能完全取代了硬編碼的通用建議，提供了更精確、更有針對性的二級證據分析指導。

## DataFrame 布爾值檢查錯誤修正 (2025-06-03)

**Status: COMPLETED ✅ - DataFrame 布爾值錯誤已修正**

### 錯誤詳情:

**問題**: 在 `display_enhanced_secondary_evidence_expander` 函數中出現 `ValueError: The truth value of a DataFrame is ambiguous` 錯誤

**錯誤原因**: 
```python
if not st.session_state.get('processed_df') and not st.session_state.get('original_processed_df'):
```
當 `st.session_state.get()` 返回 DataFrame 時，`not DataFrame` 會導致布爾值模糊錯誤。

**解決方案**:
```python
# Wrong approach
if not st.session_state.get('processed_df') and not st.session_state.get('original_processed_df'):

# Correct approach  
processed_df = st.session_state.get('processed_df')
original_processed_df = st.session_state.get('original_processed_df')

if (processed_df is None or processed_df.empty) and (original_processed_df is None or original_processed_df.empty):
```

**教訓**: 在檢查 pandas DataFrame 的存在性時，應該：
1. 先將 DataFrame 賦值給變數
2. 明確檢查 `is None` 和 `.empty` 
3. 避免直接對 DataFrame 使用布爾運算符

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py` 的 `display_enhanced_secondary_evidence_expander` 函數

## Streamlit 嵌套 Expander 錯誤修正 (2025-06-03)

**Status: COMPLETED ✅ - 嵌套 expander 錯誤已修正**

### 錯誤詳情:

**問題**: `StreamlitAPIException: Expanders may not be nested inside other expanders.`

**錯誤原因**: 在 `display_enhanced_secondary_evidence_expander` 函數中，已經在一個主要的 expander 內部（"🔍 各科二級證據查找重點"），然後又嘗試創建子 expanders。

**解決方案**: 
1. 保留主要的 expander 
2. 將原本的嵌套 expanders 改為使用 `st.columns()` 進行水平佈局
3. 使用 markdown 標題和項目符號來組織內容層次

**修改前**:
```python
with st.expander("🔍 各科二級證據查找重點", expanded=False):
    # 主要內容
    with st.expander(f"{subject}科按題型查找", expanded=False):  # ❌ 嵌套 expander
        # 子內容
```

**修改後**:
```python
with st.expander("🔍 各科二級證據查找重點", expanded=False):
    # 主要內容
    col1, col2, col3 = st.columns(3)  # ✅ 使用 columns 代替嵌套 expander
    with col1:
        st.markdown(f"**{subject}科按題型查找:**")
        # 子內容
```

**教訓**: 
1. Streamlit 不允許 expander 嵌套
2. 使用 `st.columns()` 或 `st.container()` 來組織複雜的佈局結構
3. 用 markdown 標題和格式化來替代嵌套 expanders 的層次感

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py` 的 `display_enhanced_secondary_evidence_expander` 函數

## 二級證據查找重點功能簡化 (2025-06-03)

**Status: COMPLETED ✅ - 功能已簡化為只包含具體組合**

### 修改需求:

**用戶要求**: 詳細查找指導中只需要有具體組合，邏輯是參考各科文字報告中的引導反思提示。

### 實施內容:

**簡化前**: 包含三個部分
1. 按題型查找
2. 按時間表現查找  
3. 具體組合分析

**簡化後**: 只保留具體組合分析，並參考各科診斷報告的引導反思邏輯

**新的實施邏輯**:
```python
# Q科: 按【基礎技能】【題型】【時間表現】組合
reflection_prompt = f"找尋【{skill}】【{qtype}】的考前做題紀錄，找尋【{time_perf}】的題目，檢討並反思自己是否有："

# V科: 按【基礎技能】【時間表現】組合  
reflection_prompt = f"找尋【{skill}】的考前做題紀錄，找尋【{time_perf}】的題目，檢討並反思自己是否有："

# DI科: 按【內容領域】【題型】【時間表現】組合
reflection_prompt = f"找尋【{domain}】【{qtype}】的考前做題紀錄，找尋【{time_perf}】的題目，檢討並反思自己是否有："
```

**參考來源**: 
- Q科診斷報告中的 "引導性反思提示 (針對特定技能與表現)"
- V科診斷報告中的 "引導性反思提示" 
- DI科診斷報告中的 "引導性反思提示 (針對特定題型與表現)"

**顯示格式**:
- 每個組合顯示具體的反思提示
- 包含該組合涉及的診斷參數
- 顯示涉及的題目數量

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py` 的 `display_enhanced_secondary_evidence_expander` 函數

## 二級證據查找重點顯示具體題目序號 (2025-06-03)

**Status: COMPLETED ✅ - 改為顯示具體題目序號**

### 修改需求:

**用戶要求**: 現在顯示的是「涉及N題」（N是題目數量），但是想要具體到涉及第幾題（題目序號），這樣才能讓考生精確知道自己要去修剪哪題的診斷標籤。

### 實施內容:

**修改前**:
```python
'question_position': 'count'  # 計算題目數量
# 顯示：*（涉及 3 題）*
```

**修改後**:
```python
'question_position': lambda x: sorted(list(x))  # 收集具體題目序號
question_list = ', '.join([f"第{q}題" for q in question_numbers])
# 顯示：*（涉及題目：第5題, 第12題, 第18題）*
```

### 功能改進:

1. **精確定位**: 考生能明確知道要檢視哪些具體題目
2. **便於修剪**: 可以精確到具體題目進行診斷標籤修剪
3. **排序顯示**: 題目序號按升序排列，便於查找
4. **清晰格式**: 使用「第X題」的格式，符合中文表達習慣

### 顯示格式範例:

```
1. 找尋【代數】【PURE】的考前做題紀錄，找尋【Fast & Wrong】的題目，檢討並反思自己是否有：
   概念應用錯誤、計算錯誤、粗心問題等問題。
   *（涉及題目：第3題, 第7題, 第15題）*

2. 找尋【幾何】【REAL】的考前做題紀錄，找尋【Slow & Wrong】的題目，檢討並反思自己是否有：
   文字理解問題、概念應用錯誤等問題。
   *（涉及題目：第11題, 第22題）*
```

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py` 的 `display_enhanced_secondary_evidence_expander` 函數

## 移除通用動態建議文字 (2025-06-03)

**Status: COMPLETED ✅ - 已移除通用建議文字**

### 修改需求:

**用戶要求**: 刪除「基於您的診斷結果的具體建議」這一段文字，包括Q科、V科、DI科的通用建議。

### 移除的內容:

**刪除的文字段落**:
```
基於您的診斷結果的具體建議
Q科二級證據重點（基於您的診斷結果）：
- 特別注意：對比REAL和PURE題型的表現差異
- 注意：樣本數量少於10題時，統計參考價值有限

V科二級證據重點（基於您的診斷結果）：
- 特別注意：區分CR和RC題型的不同問題模式
- 注意：樣本數量少於10題時，統計參考價值有限

DI科二級證據重點（基於您的診斷結果）：
- 特別注意：分析不同題型（DS、TPA、GT、MSR）的錯誤集中點
- MSR題組：重點關注閱讀效率與時間分配問題
- 注意：樣本數量少於10題時，統計參考價值有限
```

### 修改內容:

1. **移除顯示邏輯**: 刪除了顯示 `dynamic_suggestions` 的部分
2. **移除生成邏輯**: 刪除了 `generate_dynamic_secondary_evidence_suggestions()` 的調用
3. **簡化結構**: 現在只顯示「引導性反思提示（針對具體組合）」

### 簡化後的結構:

現在 `🔍 各科二級證據查找重點` expander 只包含：
- 引導性反思提示（針對具體組合）
- 具體的題目序號和診斷參數

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py` 的 `display_enhanced_secondary_evidence_expander` 函數

## 日夜主題切換系統實施 (2025-06-03)

**Status: COMPLETED ✅**

### 問題描述:
用戶要求修改 `modern_gui_styles.py` 的顏色搭配，實現：
1. **白天模式**：白底黑字
2. **晚上模式**：黑底白字
3. 提供主題切換功能

### 實施的主題系統:

#### 白天模式（Light Theme）：
```css
:root {
    --bg-primary: #ffffff;          /* 白色背景 */
    --bg-secondary: #f8f9fa;        /* 次要背景 */
    --bg-tertiary: #e9ecef;         /* 第三層背景 */
    --text-primary: #000000;        /* 黑色主文字 */
    --text-secondary: #212529;      /* 次要文字 */
    --text-muted: #6c757d;          /* 灰色文字 */
    --accent-color: #007bff;        /* 藍色強調色 */
    --card-bg: rgba(255, 255, 255, 0.95);  /* 白色卡片 */
}
```

#### 晚上模式（Dark Theme）：
```css
:root {
    --bg-primary: #000000;          /* 黑色背景 */
    --bg-secondary: #1a1a1a;        /* 次要背景 */
    --bg-tertiary: #2a2a2a;         /* 第三層背景 */
    --text-primary: #ffffff;        /* 白色主文字 */
    --text-secondary: #e0e0e0;      /* 次要文字 */
    --text-muted: #b0b0b0;          /* 灰色文字 */
    --accent-color: #4a90e2;        /* 藍色強調色 */
    --card-bg: rgba(26, 26, 26, 0.95);    /* 深色卡片 */
}
```

### 實施的核心功能:

#### 1. 主題CSS生成函數：
```python
def get_theme_css(is_dark_mode: bool = False):
    """Generate CSS for light or dark theme"""
    if is_dark_mode:
        # Night Mode: Black background, white text
        theme_vars = """..."""
    else:
        # Day Mode: White background, black text  
        theme_vars = """..."""
    return f"""<style>...{theme_vars}...</style>"""
```

#### 2. 主題切換按鈕：
```python
def create_theme_toggle():
    """Create a theme toggle button"""
    # Initialize theme state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    
    # Theme toggle button
    theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
    theme_label = "夜間模式" if not st.session_state.dark_mode else "日間模式"
    
    if st.button(f"{theme_icon} {theme_label}", key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
```

#### 3. 主題初始化函數：
```python
def initialize_theme():
    """Initialize theme system and apply CSS"""
    # Create theme toggle and get current mode
    is_dark = create_theme_toggle()
    
    # Apply appropriate CSS
    apply_modern_css(is_dark)
    
    return is_dark
```

### 修改的關鍵特色:

1. **CSS變數系統**: 使用CSS自訂屬性實現主題切換
2. **即時切換**: 透過 `st.rerun()` 實現即時主題切換
3. **狀態持久化**: 使用 `st.session_state` 保存主題選擇
4. **完整覆蓋**: 所有UI元件都支援主題切換
5. **平滑過渡**: 所有元件都有 `transition` 效果

### 使用方法:

#### 在應用程式中初始化主題：
```python
from gmat_llm_diagnostic_tools.modern_gui_styles import initialize_theme

# 在應用開始時調用
is_dark_mode = initialize_theme()

# 或手動控制
from gmat_llm_diagnostic_tools.modern_gui_styles import create_theme_toggle, apply_modern_css

is_dark = create_theme_toggle()
apply_modern_css(is_dark)
```

### 影響範圍:
- ✅ **完全重寫** `modern_gui_styles.py`：從固定藍灰色系統改為日夜切換
- ✅ **白天模式**：純白背景 + 黑色文字
- ✅ **晚上模式**：純黑背景 + 白色文字  
- ✅ **主題切換**：右上角按鈕，即時切換
- ✅ **狀態保存**：在session中保持主題選擇
- ✅ **過渡效果**：平滑的主題切換動畫

### 移除的舊設計:
- ❌ 複雜的漸變背景
- ❌ 固定的藍灰色調
- ❌ Glassmorphism效果（部分保留但簡化）
- ❌ 過於複雜的色彩系統

### 學習重點:
1. **簡潔性優於複雜性**: 用戶更喜歡簡單的黑白對比
2. **功能性設計**: 主題切換是實用功能，不只是視覺效果
3. **可訪問性**: 高對比度的黑白設計更易讀
4. **用戶控制**: 讓用戶選擇自己喜歡的主題

### 當前狀態:
現代GUI樣式系統已完全重構為支援日夜主題切換，提供清晰的白天（白底黑字）和晚上（黑底白字）模式，用戶可以透過右上角的切換按鈕即時切換主題。

## 二級證據查找重點文字簡化 (2025-01-30)

**Status: COMPLETED ✅**

### 用戶需求:
簡化二級證據查找重點expander的文字，從詳細列出診斷標籤改為強調修剪動作，使內容更簡潔實用。

### 修改範例:

**修改前版本**:
```
1. 找尋【Counting/Sets/Series/Prob/Stats】【PURE】的考前做題紀錄，找尋【Fast & Wrong】的題目，檢討並反思自己是否有：

Q 計算錯誤：數學計算、Q 概念應用錯誤：數學觀念/公式應用、Q 基礎掌握：應用不穩定（Special Focus Error）（純註記，無需修剪）。

（涉及題目：第13題）
```

**修改後版本**:
```
1. 找尋【Counting/Sets/Series/Prob/Stats】【PURE】的考前做題紀錄，找尋【Fast & Wrong】的題目，檢討並修剪第13題的診斷標籤，把符合的保留，不符合的去掉，留下最相關的1-2個問題。
```

### 實施內容:

**修改的核心邏輯**:

1. **Q科修改**:
```python
# 修改前: 列出具體診斷標籤
reflection_prompt = f"找尋【{skill}】【{qtype}】的考前做題紀錄，找尋【{time_perf}】的題目，檢討並反思自己是否有："
diagnostic_params = row.get('diagnostic_params_list', [])
if diagnostic_params:
    unique_params = list(set([str(p).strip() for p in diagnostic_params if p and str(p).strip()]))
    params_text = '、'.join(unique_params) + '。'
else:
    params_text = '相關錯誤類型。'

# 修改後: 強調修剪動作
reflection_prompt = f"找尋【{skill}】【{qtype}】的考前做題紀錄，找尋【{time_perf}】的題目，檢討並修剪"
if len(question_numbers) == 1:
    question_list = f"第{question_numbers[0]}題"
    trimming_guidance = f"{question_list}的診斷標籤，把符合的保留，不符合的去掉，留下最相關的1-2個問題。"
else:
    question_list = '、'.join([f"第{q}題" for q in question_numbers])
    trimming_guidance = f"{question_list}的診斷標籤，把符合的保留，不符合的去掉，留下最相關的1-2個問題。"
```

2. **V科修改**: 相同邏輯應用到V科
3. **DI科修改**: 相同邏輯應用到DI科

### 修改位置:
- **檔案**: `gmat_diagnosis_app/ui/results_display.py`
- **函數**: `display_enhanced_secondary_evidence_expander_in_edit_tab()`
- **影響範圍**: Q科、V科、DI科的引導性反思提示生成邏輯

### 顯示格式調整:
```python
# 調整顯示邏輯，不再單獨顯示題目列表
for i, combo in enumerate(combinations, 1):
    st.markdown(f"**{i}. {combo['prompt']}**")
    st.markdown(f"   {combo['details']}")
    if combo['questions']:  # Only show if questions exist (for backward compatibility)
        st.markdown(f"   *（涉及題目：{combo['questions']}）*")
    st.markdown("")
```

### 改進效果:

**1. 文字簡化**:
- 移除了冗長的診斷標籤列表
- 直接切入修剪動作的核心

**2. 行動導向**:
- 從「反思是否有某些問題」改為「修剪標籤」
- 提供明確的操作指導

**3. 一致性**:
- 統一的修剪指導語句
- 適用於所有科目和題目數量

**4. 實用性**:
- 直接告訴用戶要做什麼
- 強調「留下最相關的1-2個問題」的目標

### 學習重點:
1. **用戶反饋重要性**: 冗長的文字會降低實用性
2. **行動導向設計**: 直接告訴用戶要採取什麼行動比列出所有選項更有效
3. **簡潔原則**: 在保持功能完整的前提下，越簡潔越好
4. **目標明確**: 明確告知用戶修剪的目標（1-2個最相關問題）

### 當前狀態:
二級證據查找重點expander現在提供簡潔而實用的修剪指導，幫助用戶更有效地完成診斷標籤修剪任務。

## 警告容器黑暗模式顯示修復 (2025-01-30)

**Status: COMPLETED ✅**

### 問題描述:
警告容器在黑暗模式下字根本讀不到，因為使用了固定的淺色背景和深色文字，在黑暗模式下造成可讀性問題。

### 問題原因:
```css
/* 問題的固定樣式 */
background-color: #fff3cd;  /* 固定的淺黃色背景 */
color: #333;                /* 固定的深色文字 */
border: 1px solid #ffeb3b;  /* 固定的黃色邊框 */
```

在黑暗模式下，淺色背景會變得突兀，深色文字在暗色主題下可讀性差。

### 解決方案:
實施CSS變數系統，支援主題自適應：

**1. 使用CSS自定義屬性（變數）**:
```css
/* 主要容器樣式 */
background-color: var(--background-color, #fff3cd);
border: 1px solid var(--border-color, #ffc107);
border-left: 5px solid var(--accent-color, #ff9800);
color: var(--text-color, #333);

/* 標題和強調色 */
color: var(--warning-header-color, #ff6f00);
```

**2. 定義明暗主題色彩變數**:
```css
:root {
    /* 亮色主題（預設） */
    --background-color: #fff3cd;     /* 淺黃色背景 */
    --border-color: #ffc107;         /* 黃色邊框 */
    --accent-color: #ff9800;         /* 橙色強調 */
    --text-color: #333;              /* 深色文字 */
    --warning-header-color: #ff6f00; /* 橙紅色標題 */
}

/* 黑暗主題檢測 */
@media (prefers-color-scheme: dark) {
    :root {
        --background-color: #2d1810;    /* 深棕色背景 */
        --border-color: #8B4513;        /* 暗棕色邊框 */
        --accent-color: #D2691E;        /* 暗橙色強調 */
        --text-color: #e0e0e0;          /* 淺色文字 */
        --warning-header-color: #FFB347; /* 亮橙色標題 */
    }
}

/* Streamlit特定黑暗主題檢測 */
[data-theme="dark"] :root,
.stApp[data-theme="dark"] :root {
    --background-color: #2d1810;
    --border-color: #8B4513;
    --accent-color: #D2691E;
    --text-color: #e0e0e0;
    --warning-header-color: #FFB347;
}
```

### 修改位置:
- **檔案**: `gmat_diagnosis_app/ui/results_display.py`
- **函數1**: `display_global_tag_warning()` - 原始警告函數
- **函數2**: `display_results()` 中編輯分頁的警告顯示部分

### 修改前後對比:

**修改前（固定樣式）**:
```html
<div style="background-color: #fff3cd; border: 1px solid #ffeb3b; color: #333;">
<h4 style="color: #ff6f00;">警告標題</h4>
<strong style="color: #333;">強調文字</strong>
```

**修改後（自適應樣式）**:
```html
<div style="background-color: var(--background-color, #fff3cd); border: 1px solid var(--border-color, #ffc107); color: var(--text-color, #333);">
<h4 style="color: var(--warning-header-color, #ff6f00);">警告標題</h4>
<strong style="color: var(--text-color, #333);">強調文字</strong>
```

### 色彩設計考量:

**亮色主題**:
- 背景：淺黃色 (#fff3cd) - 溫和的警告色
- 文字：深灰色 (#333) - 良好對比度
- 標題：橙紅色 (#ff6f00) - 顯眼的警告色

**黑暗主題**:
- 背景：深棕色 (#2d1810) - 溫暖但不刺眼
- 文字：淺灰色 (#e0e0e0) - 在暗背景上清晰可讀
- 標題：亮橙色 (#FFB347) - 保持警告視覺效果

### 技術特點:
1. **向後相容**: 使用 `var(--variable, fallback)` 語法提供後備值
2. **多層檢測**: 支援系統主題檢測和Streamlit特定主題檢測
3. **一致性**: 兩個顯示位置使用相同的樣式系統
4. **可維護性**: 色彩集中管理，便於未來調整

### 改進效果:
1. **黑暗模式可讀性**: 文字在黑暗背景下清晰可見
2. **主題一致性**: 警告容器會自動適應當前主題
3. **視覺和諧**: 色彩選擇與黑暗模式整體風格協調
4. **無縫切換**: 主題切換時警告容器自動調整

### 學習重點:
1. **CSS變數的威力**: 實現主題自適應的有效方法
2. **多重主題檢測**: 覆蓋不同的主題檢測機制
3. **可讀性優先**: 確保在所有主題下都有良好的對比度
4. **使用者體驗**: 技術實現服務於實際使用需求

### 當前狀態:
警告容器現在能夠根據使用者的主題偏好自動調整顏色，在黑暗模式下提供良好的可讀性，同時保持警告的視覺效果。

## Mistake: 警告容器在黑暗模式下可讀性差
Wrong:
```css
/* 固定的亮色主題樣式 */
background-color: #fff3cd;
color: #333;
border: 1px solid #ffeb3b;
```

Correct:
```css
/* 使用CSS變數實現主題自適應 */
background-color: var(--background-color, #fff3cd);
color: var(--text-color, #333);
border: 1px solid var(--border-color, #ffc107);

/* 添加黑暗主題支援 */
@media (prefers-color-scheme: dark) {
    :root {
        --background-color: #2d1810;
        --text-color: #e0e0e0;
        --border-color: #8B4513;
    }
}
```

### 當前狀態:
詳細的標籤說明已成功從警告容器移動到編輯說明後，提供更好的用戶體驗和更清晰的信息組織結構。

## 移除警告容器中的建議行動部分 (2025-01-30)

**Status: COMPLETED ✅**

### 用戶需求:
移除警告容器中的「建議行動」部分，讓警告容器只保留基本的警告信息。

### 實施內容:

**1. 簡化警告容器內容**:

**修改檔案**: `gmat_diagnosis_app/ui/results_display.py`

```python
# 修改前: 警告容器包含建議行動
<h4>⚠️ 診斷標籤警告</h4>
<p>平均每題標籤數過多...</p>
<h5>💡 建議行動</h5>
<div><strong>主要方法：回憶與修剪</strong><br>...</div>
<div><strong>輔助方法：二級證據分析</strong><br>...</div>

# 修改後: 警告容器只保留基本警告
<h4>⚠️ 診斷標籤警告</h4>
<p>平均每題標籤數過多...</p>
```

**2. 保持編輯分頁警告容器的簡潔性**:
- 編輯分頁中的警告容器已經是簡潔版本
- 只包含警告標題和基本信息
- 不包含建議行動內容

### 改進效果:
- **信息層次清晰**: 警告容器專注於警告信息，建議行動在編輯說明中提供
- **避免重複**: 防止同一頁面出現重複的建議內容
- **用戶體驗提升**: 警告更簡潔明瞭，詳細指導在適當位置提供
- **頁面整潔**: 減少冗餘信息，提高可讀性