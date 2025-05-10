## Excel數據貼上處理流程

當使用者在頁面上貼上從Excel複製的表格數據後，系統會進行以下處理：

### 1. 初始數據接收與轉換

1. **數據接收**：
   - 系統通過`streamlit`的`text_area`元件接收使用者貼上的Excel數據
   - 該數據被存儲在一個名為`pasted_data`的變數中
   - 這個步驟發生在`process_subject_tab`函數中（`gmat_diagnosis_app/utils/data_processing.py`）

2. **數據轉換為可處理格式**：
   - 系統使用`io.StringIO`將貼上的文本轉換為類似文件的流對象
   - 這使得pandas可以像處理文件一樣處理這些數據
   ```python
   source = io.StringIO(pasted_data)
   data_source_type = 'Pasted Data'
   ```

3. **數據讀取與解析**：
   - 使用`pandas.read_csv`函數讀取數據，嘗試自動偵測分隔符號
   ```python
   temp_df = pd.read_csv(source, sep=None, engine='python', skip_blank_lines=True)
   ```
   - 系統會自動跳過空白行，並嘗試智能判斷分隔符號（如制表符或逗號）

### 2. 數據清理與預處理

1. **初始清理**：
   - 丟棄以`_b`結尾的列
   - 移除全空的行和列
   - 重設索引
   ```python
   cols_to_drop = [col for col in temp_df.columns if str(col).endswith('_b')]
   temp_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
   temp_df.dropna(how='all', axis=0, inplace=True)
   temp_df.dropna(how='all', axis=1, inplace=True)
   ```

2. **添加無效標記列**：
   - 系統添加`is_manually_invalid`列，默認值為`False`
   - 這個列允許使用者標記不應納入分析的題目

3. **無效題目建議**：
   - 系統會根據時間壓力估計自動建議可能的無效題目
   - 依據不同科目使用不同的閾值：Q科目為3.0，DI科目為2.0，V科目為3.0
   ```python
   # 依據科目設定不同閾值
   diff_threshold = 3.0  # 默認閾值
   if subject == 'Q': diff_threshold = 3.0
   elif subject == 'DI': diff_threshold = 2.0
   elif subject == 'V': diff_threshold = 3.0
   pressure_guess = (times.max() - times.min()) > diff_threshold
   ```

4. **列名標準化**：
   - 系統會嘗試將Excel數據中的列名轉換為內部標準列名
   - 將`Response Time (Minutes)`轉換為`question_time`
   - 將`Question`或`\ufeffQuestion`轉換為`question_position`
   - 將`Performance`轉換為`is_correct`，並根據值是否為`'Correct'`轉換為布爾值

### 3. 數據交互與編輯

1. **顯示編輯器**：
   - 系統顯示可編輯的數據表格，讓使用者可以：
      - 手動標記無效題目
      - 檢查數據正確性
      - 在需要時修改內容
   ```python
   edited_df = tab_container.data_editor(
       temp_df,
       key=f"editor_{subject_key}",
       num_rows="dynamic",
       use_container_width=True,
       column_order=column_order,
       column_config={
           "is_manually_invalid": st.column_config.CheckboxColumn(
               "是否草率做題？ (手動標記)",
               help="勾選此框表示您手動判斷此題為無效（例如因倉促/慌亂）。此標記將優先於系統自動建議。",
               default=False,
           )
       }
   )
   ```

### 4. 數據驗證與標準化

1. **編輯後驗證**：
   - 系統會對編輯後的數據進行驗證，確保符合診斷邏輯所需格式
   - 檢查必要欄位是否存在，數據類型是否正確
   ```python
   validation_errors, warnings = validate_dataframe(df_to_validate, subject)
   ```

2. **最終標準化**：
   - 應用列名映射，確保所有列名符合內部標準
   - 根據科目進行特殊標準化（例如Q科目的`question_type`列轉換為大寫）
   - 確保`is_correct`列為布爾值
   - 確保`question_position`為數值型，並在缺失時自動生成
   - 設置最終的`is_invalid`標記，完全基於使用者的`is_manually_invalid`手動標記
   - 添加`Subject`列標識數據所屬科目

3. **結果確認**：
   - 顯示數據處理成功消息
   - 將處理好的數據返回給應用程序主流程

### 5. 分析前最終準備

1. **數據合併**：
   - 將不同科目的數據合併為一個統一的DataFrame（`df_combined_input`）
   - 確保所有必要的科目（Q、V、DI）都有有效數據

2. **IRT模擬與診斷前準備**：
   - 將數據傳遞給診斷模塊進行進一步處理
   - 運行IRT模擬，估計使用者的能力值和題目難度
   - 基於時間表現、正確性等多維度進行深度診斷

### 總結

使用者貼上Excel數據的處理流程是一個多步驟的過程，包括：
1. 接收原始文本
2. 轉換為結構化DataFrame
3. 清理與預處理
4. 標準化列名與數據格式 
5. 提供交互式編輯與無效題目標記
6. 驗證數據完整性與格式
7. 準備最終的標準化數據供診斷分析

---



Search files...

Search files...

Read file: gmat_diagnosis_app/diagnostics/di_modules/main.py

Read file: gmat_diagnosis_app/diagnostics/v_modules/main.py
基於對GMAT診斷應用程序代碼的深入分析，我將詳細解釋各科目(Q、V、DI)數據在分析過程中的詳細流程。

# GMAT診斷應用中的各科目分析流程

## Q科目（Quantitative）分析流程

### 1. 預處理與初始化
- **時間壓力判定**：先從輸入數據的屬性中獲取時間壓力狀態(`time_pressure_q`)
- **無效數據處理**：
  - 優先使用用戶手動標記的`is_manually_invalid`作為無效題目的依據
  - 若不存在，則使用系統自動判定的`is_invalid`
  - 將無效標記轉換為布爾值以確保一致性
- **有效數據篩選**：僅使用有效題目(`~df_q['is_invalid']`)創建一個有效數據集`df_valid_for_analysis`

### 2. 基礎統計指標計算
- **計算題型平均時間**：對有效數據按題型分組，計算各題型平均耗時
- **計算技能最大正確難度**：對於每個基礎技能(如代數、算術等)，找出用戶正確解答的最高難度題目

### 3. 根本原因診斷（核心問題分析）
- **診斷參數應用**：調用`diagnose_q_root_causes`，針對每道題目分析可能的問題模式
  - 輸入：原始數據、各題型平均時間、各技能最高正確難度
  - 輸出：添加了`diagnostic_params`診斷參數的DataFrame
- **診斷參數翻譯**：將英文診斷代碼翻譯為中文標籤(如`Q_CALCULATION_ERROR`翻譯為`計算錯誤`)
- **特殊錯誤標記(SFE)**：識別特殊聚焦錯誤(Special Focus Error)
  - SFE指用戶在已掌握技能範圍內犯的錯誤，即難度低於或等於用戶已成功解決的同類題目，表明知識點掌握不穩定

### 4. 內部分析（章節2-6）
- **Real vs Pure分析**：比較公式化純數學題(Pure)與應用場景題(Real)的表現差異
- **錯誤難度分佈**：分析錯誤題目在不同難度級別的分佈情況
- **行為模式分析**：
  - 早期倉促行為：測試開始階段回答速度異常快
  - 粗心問題：快速作答但出錯的比例高
- **技能覆蓋分析**：檢查是否有特定技能需要系統性鞏固而非僅關注個別錯題

### 5. 建議生成
- **基於問題模式**：根據診斷出的問題生成針對性練習建議
- **優先級排序**：將涉及SFE（知識掌握不穩定）的建議優先展示
- **建議內容**：包括基礎鞏固、針對性練習方向、時間管理策略等

### 6. 報告生成
- **報告章節**：由七個主要章節組成
  - 開篇總結、表現概覽、核心問題診斷、模式觀察、鞏固提示、練習計劃、行動指南
- **總結報告**：集成所有診斷結果，生成完整摘要報告
- **結果輸出**：返回診斷結果字典、最終報告文本、帶有診斷標籤的數據框

## V科目（Verbal）分析流程

### 1. 數據準備與處理
- **優先使用手動標記**：
  ```python
  if 'is_manually_invalid' in df_v_processed.columns:
      df_v_processed['is_invalid'] = False  # 完全重設
      df_v_processed.loc[df_v_processed['is_manually_invalid'] == True, 'is_invalid'] = True
  ```
- **數據類型轉換**：將時間、難度等轉換為數值型，將正確性轉換為布爾型
- **初始化診斷列**：為每行添加空的診斷參數列表`diagnostic_params`

### 2. 閱讀理解障礙查詢（RC特有）
- **分析RC閱讀時間**：檢查閱讀理解(RC)題組的閱讀時間是否超過閾值
  - 3題RC組：閾值4分鐘
  - 4題RC組：閾值5分鐘
- **標記閱讀障礙**：對超過閾值的RC題組進行標記，用於後續診斷

### 3. 異常快速作答標記
- **各題型快速作答閾值**：基於各題型平均時間的特定比例（如40%）
- **可疑快速標記**：對於比閾值還快的答題進行標記，用於模式分析

### 4. 診斷規則應用
- **計算技能最高正確難度**：類似Q科目，但針對V的技能分類(如閱讀理解、批判性思維等)
- **應用診斷規則**：調用`apply_ch3_diagnostic_rules`
  - 分析時間表現：快、慢或正常
  - 分析錯誤原因：閱讀理解錯誤、邏輯推理錯誤等
  - 特殊錯誤(SFE)標記：找出已掌握技能的稱定性問題
  - 輸出：各題目的時間表現分類和診斷參數

### 5. 結果和模式分析
- **各維度表現分析**：
  - 題型分析：CR(批判性思維)和RC(閱讀理解)的比較
  - 技能分析：不同閱讀技能的表現差異
- **行為模式觀察**：
  - 識別"慢而對"模式：需要時間但能正確解答的題目
  - 分析"快而錯"模式：可能的猜題或粗心現象

### 6. 建議和報告生成
- **生成練習建議**：基於診斷結果和模式分析
- **報告生成**：使用`generate_v_summary_report`生成結構化報告
- **清理和最終處理**：
  - 確保英文診斷代碼已轉為中文標籤
  - 確保`is_invalid`為布爾型
  - 確保`Subject`列值為'V'

## DI科目（Data Insights）分析流程

### 1. 基礎準備和數據檢查
- **確認數據有效性**：檢查是否有DI數據
- **數據類型轉換**：
  ```python
  df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
  if 'question_position' not in df_di.columns: df_di['question_position'] = range(len(df_di))
  ```
- **初始化診斷列**：與其他科目類似，初始化`diagnostic_params`列表

### 2. 時間策略與無效數據標記
- **時間壓力確認**：採用輸入的時間壓力狀態`di_time_pressure_status`
- **無效數據識別**：
  - 檢查後三分之一的題目是否有異常快速作答
  - 對於各題型(DS, TPA, GT等)使用不同的異常快速閾值
  - 對MSR(多源推理)題型採用特殊的題組時間分析
  - 標準：絕對倉促(小於0.5分鐘)、相對倉促(小於首三分之一平均的40%)

### 3. MSR特殊處理
- **MSR題組識別**：多源推理題目通常是題組形式，需要特殊處理
- **閱讀時間估計**：根據題組中第一道題的時間與後續題目平均時間的差異估計閱讀時間
  ```python
  reading_time = time_q1 - (time_q2 + time_q3) / 2
  ```
- **題組效率評估**：分析整個MSR題組的總時間與表現

### 4. 維度分析（基於有效數據）
- **比較三個核心維度**：
  - 領域分析：比較Math-Related vs Non-Math-Related表現
  - 題型分析：分析DS、TPA、MSR、GT四種題型表現
  - 難度分析：按難度等級分析表現
- **維度標籤生成**：識別特別弱的領域和題型組合

### 5. 根本原因診斷
- **計算基準指標**：使用有效數據計算各題型平均時間和各組合最大正確難度
- **應用診斷規則**：將規則應用於所有數據(包括無效數據)
  - 診斷錯誤原因：計算錯誤、多源整合錯誤等
  - 時間表現分類：快錯、慢錯、正常時間錯
  - 特殊錯誤(SFE)標記：與Q、V類似，但針對DI的技能分類

### 6. 基礎覆蓋和練習建議
- **題型領域豁免**：
  ```python
  exempted_type_domain_combinations = set(df_diagnosed.groupby(['question_type', 'content_domain'], observed=False, dropna=False).groups.keys())
  ```
- **優先順序設定**：根據表現差距設定各題型和領域的練習優先級
- **推薦建議生成**：生成結構化的練習建議，包括豁免、SFE聚合建議和一般建議

### 7. 報告和數據返回
- **生成報告**：使用`_generate_di_summary_report`生成結構化報告
- **整理最終數據**：
  - 確保`is_invalid`為布爾型
  - 確保診斷參數已正確翻譯為中文
  - 確保`Subject`列值為'DI'

## 數據流程通用要素

所有三個科目的診斷流程中都共享以下要素：

1. **手動無效標記優先**：用戶手動標記的無效題目(`is_manually_invalid`)始終優先於系統自動判斷
2. **有效/無效數據分離**：
   - 對部分分析僅使用有效數據（如均值計算、錯誤模式識別）
   - 對診斷標籤應用於全部數據，但無效數據會添加特殊標記
3. **診斷參數翻譯**：所有科目都將英文診斷代碼翻譯為中文標籤
4. **SFE重點標記**：特別關注已掌握技能範圍內的錯誤，作為知識不穩定的關鍵指標
5. **綜合報告生成**：基於各個章節的分析結果，生成一份結構化的診斷報告

---



Search files...

Search files...

Read file: gmat_diagnosis_app/ui/chat_interface.py

Read file: gmat_diagnosis_app/utils/excel_utils.py

Read file: gmat_diagnosis_app/app.py
報告生成之後，數據流向主要分為以下幾個方向：

### 1. 報告內容的顯示和交互
- **結果顯示頁面**：
  * 報告生成後，結果通過`display_results()`函數在Streamlit界面的"結果查看"標籤頁中呈現
  * 系統會顯示各科目(Q、V、DI)的診斷報告
  * 報告以結構化的文本形式展示，包含章節標題、項目符號和重點標記等
  * 每個報告包括總覽、核心表現分析、核心問題診斷、練習建議等部分

### 2. 數據到AI交互系統
- **聊天界面功能**：
  * 生成的報告和處理過的診斷數據會被傳送到AI聊天系統
  * 透過`display_chat_interface()`函數提供基於報告內容的AI問答功能
  * 聊天系統使用OpenAI API，將用戶的提問與報告內容和診斷數據結合作為上下文
  * 用戶可以針對報告內容和數據提問，AI會根據這些上下文提供回答

### 3. 數據到Excel導出
- **Excel文件生成**：
  * 用戶可以將處理後的診斷數據以Excel格式下載
  * 系統使用`to_excel()`函數將處理過的DataFrame轉為Excel格式
  * Excel檔案中包含各種條件格式設置，例如：
    - 正確答案以淺綠色標記
    - 錯誤答案以淺紅色標記
    - 超時題目以藍色加粗標記
    - 無效題目以灰色標記
  * 數據會根據題號排序，確保閱讀順序一致

### 4. 數據編輯與更新
- **交互式編輯**：
  * 用戶可以在UI界面編輯診斷數據，例如將題目標記為無效
  * 編輯後的數據會重新處理，更新診斷標籤
  * 用戶可以點擊"套用變更並更新質化分析輸出"按鈕保存編輯內容

### 5. 數據持久化
- **會話狀態保存**：
  * 所有報告和數據都保存在Streamlit的`session_state`中
  * 這允許用戶在不同標籤頁之間切換而不丟失數據
  * 數據在網頁會話期間保持，但不會永久保存

### 6. 聯動更新
- **編輯後的更新流程**：
  * 當用戶編輯診斷數據後，AI交互系統會自動更新上下文
  * Excel導出功能會使用最新的編輯數據
  * 報告顯示也會根據編輯後的數據更新

整體來看，報告生成後的數據流是一個環形系統，用戶可以查看報告、與AI互動討論報告內容、編輯診斷數據並重新生成報告，同時可以隨時將數據導出為Excel檔案以便進一步分析。

