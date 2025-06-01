"""
GMAT 診斷標籤路由工具模組

此模塊將診斷標籤路由到適當的訓練命令，基於 gmat_route_tool.py 的功能
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging
import re


class DiagnosisRouterTool:
    """診斷路由工具類，根據診斷標籤路由到相應的AI工具推薦"""
    
    def __init__(self):
        """初始化診斷路由工具"""
        
        # 命令描述映射表 - 根據 prompt-to-label.md 完全更新
        self.command_descriptions: Dict[str, str] = {
            # CR 命令
            "Questions you did wrong": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。",
            "You did right but slowly": "使用者提供雖然做對但耗時過長的題目 (CR或TPA非數學相關)，我將提供 N分鐘內快速解題的捷徑。我會引導你先閱讀問題，識別解鎖問題的關鍵要素，然後判斷文本中哪些部分是相關信息，哪些不是，最後指出使用預寫策略還是排除策略來回答問題。每個步驟都包含清晰的提示，引導至下一步，並遵循線性的單向思維過程。",
            "Passage you fail to organize": "使用者提供一篇難以組織的文章，我將為其創建一個心智圖（markdown格式，輸出在代碼塊中），幫助你視覺化資訊間的關係，從而更好地理解文章結構和 logic。",
            "Examine your thoughts": "使用者提供口頭解題過程的錄音轉文字稿和題目文本，我將分析你的解題思路，找出其中的錯誤和可以改進的地方，幫助你提升解題效率和準確性。",
            "CR-BF Demo Thoughts": "使用者提供Boldface題目，我將扮演AI助教，專門解決邏輯推理問題（例如BF題型）。我會遵循五大原則，逐步分析和回答問題，採用循環迭代的方法，每次專注於一個核心差異，並在每個循環中進行單一推斷，以排除選項，直到剩下一個為止。如果需要更多信息，我會請求澄清，而不是假設或跳過步驟。",
            "Understand Logical terms": "使用者提供五個答案選項，我將解釋其中每個 logic 術語的含義，幫助你理解選項的確切意思。",
            "Rewrite passage into complex sentences": "使用者提供一篇文章，我將保留其確切的核心含義，不任意增刪觀點、含義或細節，將其改寫成用詞艱深、風格抽象的版本。改寫後的文章長度不超過原文1.5倍，每段至少包含2-3個體現這些風格的句子。我將提供改寫後的英文文章、一個簡單易懂的白話文版本，並簡要說明改寫如何運用抽象 logic詞彙、複雜句型和客觀語氣，同時確認未增刪意義且符合長度限制。",
            "Review distractor": "使用者提供一個GMAT問題以及一個正確選項和一個錯誤選項。我會用繁體中文，以像對10歲小孩說話的語氣和風格，詳細解釋為什麼正確選項符合題目要求，以及為什麼錯誤選項不符合。我會為正確和錯誤選項各提供兩個不同的類比情境（新故事），幫助你理解。然後，我會問你想要更多類比例子還是設計一個變體問題。如果選擇設計變體問題，我會根據你提供的英文問題和兩個選項，更改故事的領域和內容，但保留文章和選項的logic，並創建一個語法結構盡可能相似的英文變體問題和兩個選項。",
            "Classify This Question": "使用者提供CR或TPA非數學相關問題，我將判斷其屬於分析、建構、評論或計畫四大子類型中的哪一種，並進行兩次獨立判斷以確保一致性。若不一致則進行第三次最終判斷。最後，我會提供一個表格整理各子類型的出現次數，助你找出弱點題型。",

            "Boldface Interactive Tutor": "使用者提供CR boldface問題及其官方答案和用[]標記的粗體部分。我將扮演GMAT Boldface互動導師，透過『你問 -> 使用者回答 -> 評估使用者回答並問下一個問題』的互動形式，逐步引導你分析問題。首先，我會逐句引導你解釋文章中每個句子的作用，並在你理解有誤時提供糾正。完成所有句子的討論後，我會再次展示你對所有句子作用的回答（已修正），並標明文章中的第一和第二粗體部分。接著，我會逐個引導你分析每個答案選項（初期不透露官方答案）：詢問保留或排除該選項，若排除則詢問理由並評估其正確性。如果你排除了官方答案，我會指出你推理的錯誤並引導你，直到你選擇官方答案為止。",
            "Logical Chain Builder": "使用者提供CR論證評估型文章，並指定邏輯鏈的起點和終點。我將以繁體中文構建一個簡化的邏輯鏈，直接關聯起點和終點，並包含必要的隱藏假設。邏輯鏈將使用 -> 表示因果關係，+ 表示並列關係，() 表示隱藏假設。我會重新檢查邏輯鏈，確保沒有遺漏影響結論有效性的重要隱藏假設或前提，並以學術、精確和簡潔的方式引導你理解論證的 logic結構，如果文章不清晰，我會請求更多信息。",
            "Identify core issue": "使用者提供一篇GMAT CR文章，我會將其核心問題轉化為'是否'的形式，並創建具有相同邏輯結構但在不同情境下的類比場景。我不會立即揭示新場景的核心問題，而是提示你自行識別。在你回答後，我會揭示場景的實際核心問題，並評估你答案的準確性，提供糾正和指導以增強你的理解。",
            "Role-Immersion Trainer": "使用者提供GMAT CR文章，我將首先確定文章中信息最直接影響的角色。接著，我會詢問你希望進行「推斷」還是「解釋」。若選擇「解釋」，我將從該角色角度解釋文章中的不一致或矛盾事實，避免超出文本的假設；若選擇「推斷」，我將從該角色角度，嚴格基於文章數據或觀察結果得出結論，避免猜測。結論或解釋將以項目符號列表形式呈現，並使用第一人稱。最後，我會請你提供文章的官方答案，並詳細解釋我之前得出的哪個結論或解釋與官方答案最一致。",
            "Explain Textbook": "使用者提供教材的文字或截圖，我會用繁體中文並以中學生易懂的方式解釋概念，並提供三個例子。接著詢問你是否需要測驗。若同意，我會呈現三個新情境（部分正確應用概念，部分否），請你指出適用情境。我會自我檢查評估邏輯後，再評估你的答案並提供回饋。",
            "Train your close reading skill": "使用者提供短文（80-120字），我將扮演精讀教練，一次只呈現第一句話，請你理解。收到你的詮釋後，僅在對句子主旨或核心邏輯有根本性誤解，或中文語序怪異不自然時才介入修正，忽略用詞、術語不精確或措辭差異（若大致意思相同）。修正後（或無需修正時）呈現下一句，依此類推。所有句子單獨檢視完畢後，展示你所有的詮釋，並請你將其修改成連貫的段落。",
            "Train Reading for Specific Domain": "使用者指定一個特定領域，我將提供該領域內三個非常具體、狹窄但高度爭議性的主題，請你選擇其一。接著，我会根據你選擇的主題創建一篇200-350字的GMAT風格英文文章，呈現多種立場、論點或理論，並進行分析、批判或擴展，同時納入具體範例或實證數據支持論點。文章會使用正式學術詞彙和複雜句型。收到文章後，請你提供摘要。然後我會提供該文章的簡明繁體中文摘要（掌上型便利貼大小），並評估你的摘要準確性，提供具體回饋及1-10分評分。最後，我會根據文章出三道英文選擇題（主旨、細節、推論各一），每題五個選項，各選項至少25字長。",
            "Memorizing Vocabularies": "使用者提供需要記憶的單字，我將為每個單字創建一個包含英文單字、中文意思、詞性和至少25字長（含至少兩子句及複雜結構如插入語、倒裝或省略）的例句的試算表。接著，我會詢問你是否有仍不熟悉的單字，並用繁體中文和英文以十年級學生能理解的方式解釋，提供三個相關概念，然後詢問是否進入下一步。然後，我會用所有提供的單字寫一篇200-350字GMAT學術風格的英文文章，每句至少25字長且含複雜結構，並顯示字數。之後，我會提供該文章的簡明繁體中文摘要（掌上型便利貼大小），請你提供自己的摘要，我會評估其準確性並評分(1-10)。最後，我會根據文章出三道英文選擇題（主旨、細節、推論各一），每題五個選項，各選項至少25字長。",
            
            # DS 命令
            "Question you did wrong": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。",
            "Learn Math Concept": "使用者提供一個數學問題，我將從出題者的角度思考，指出這個問題想要測試哪些具體的數學概念，幫助你理解題目背後的考點。",
            "Identify features for applying a specific solution": "使用者提供一個特定的解題方法，我將總結哪些題目陳述的特徵出現時，可以應用此解題方法，幫助你識別模式並有效應用方法。",
            "Create Various Questions": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題 logic與原問題相似。",
            "Finding Similar Questions in Set": "使用者提供一個題庫和一個之前做錯的樣本問題，我將從題庫中找出與樣本問題使用相似數學概念的題目，幫助你針對性練習。",
            "Convert to real context": "使用者提供GMAT數學選擇題（文字或圖片形式），我會將其轉換成一個包含真實情境和故事情節的英文應用題（30-50字），且不更改任何數值。如果原題已是應用題，則僅翻譯成英文。",
            
            # GT 命令
            "Learn Math Concept": "使用者提供一個數學問題，我將從出題者的角度思考，指出這個問題想要測試哪些具體的數學概念，幫助你理解題目背後的考點。",
            "Sentence cracker": "使用者提供一個難以理解的句子，我會先將其簡化到九年級學生能懂的程度。然後詢問你的困難點是領域特定詞彙、一般詞彙、複雜句型，還是綜合性的。若為詞彙問題，請指出不清楚的單字。領域詞彙我會解釋並提供三個相關概念；一般詞彙則提供三個同義詞和反義詞，各附一個至少25字且含複雜結構的例句。若為句型問題，我會拆解句子結構，逐一說明各成分含義，再解釋如何組織這些含義以理解原句，最後保持原句結構，改寫成五個不同領域但句型相似的版本。",
            
            # MSR 命令
            "Passage you failed to organize": "使用者提供一篇難以組織的文章，我將為其創建一個心智圖（markdown格式，輸出在代碼塊中），幫助你視覺化資訊間的關係，從而更好地理解文章結構和 logic。",
            "Rewrite Passage into Complex Sentences": "使用者提供一篇文章，我將保留其確切的核心含義，不任意增刪觀點、含義或細節，將其改寫成用詞艱深、風格抽象的版本。改寫後的文章長度不超過原文1.5倍，每段至少包含2-3個體現這些風格的句子。我將提供改寫後的英文文章、一個簡單易懂的白話文版本，並簡要說明改寫如何運用抽象 logic詞彙、複雜句型和客觀語氣，同時確認未增刪意義且符合長度限制。",
            "Identify Features for applying a specific solution": "使用者提供一個特定的解題方法，我將總結哪些題目陳述的特徵出現時，可以應用此解題方法，幫助你識別模式並有效應用方法。",
            "Customize your preferred Problem-solving process and request an AI demonstration": "使用者告訴我你偏好的解題順序 (SOP)，我將依此判斷最短、最有效率的閱讀路徑，並遵循人類單向思維模式進行演示。",
            "Classify This Question": "使用者提供RC或MSR非數學相關問題，我將判斷其屬於主旨、支持性觀點、推論、評估或應用五大子類型中的哪一種，並進行兩次獨立判斷以確保一致性。若不一致則進行第三次最終判斷。最後，我會提供一個表格整理各子類型的出現次數，助你找出弱點題型。",
            "Train your Close Reading Skill": "使用者提供短文（80-120字），我將扮演精讀教練，一次只呈現第一句話，請你理解。收到你的詮釋後，僅在對句子主旨或核心邏輯有根本性誤解，或中文語序怪異不自然時才介入修正，忽略用詞、術語不精確或措辭差異（若大致意思相同）。修正後（或無需修正時）呈現下一句，依此類推。所有句子單獨檢視完畢後，展示你所有的詮釋，並請你將其修改成連貫的段落。",
            "Enhanced Reading Speed": "使用者提供句子，我將自動將其劃分成邏輯上有意義的區塊，每個區塊代表一個獨立的意義單元（如主語、時間範圍、因果關係、主要論點等），以助你更好地理解句子結構。我會保持原始句子結構，並使用粗體 || 分隔區塊。",
            "Sentence Cracker": "使用者提供一個難以理解的句子，我會先將其簡化到九年級學生能懂的程度。然後詢問你的困難點是領域特定詞彙、一般詞彙、複雜句型，還是綜合性的。若為詞彙問題，請指出不清楚的單字。領域詞彙我會解釋並提供三個相關概念；一般詞彙則提供三個同義詞和反義詞，各附一個至少25字且含複雜結構的例句。若為句型問題，我會拆解句子結構，逐一說明各成分含義，再解釋如何組織這些含義以理解原句，最後保持原句結構，改寫成五個不同領域但句型相似的版本。",
            "Memorizing Vocabulary": "使用者提供需要記憶的單字，我將為每個單字創建一個包含英文單字、中文意思、詞性和至少25字長（含至少兩子句及複雜結構如插入語、倒裝或省略）的例句的試算表。接著，我會詢問你是否有仍不熟悉的單字，並用繁體中文和英文以十年級學生能理解的方式解釋，提供三個相關概念，然後詢問是否進入下一步。然後，我會用所有提供的單字寫一篇200-350字GMAT學術風格的英文文章，每句至少25字長且含複雜結構，並顯示字數。之後，我會提供該文章的簡明繁體中文摘要（掌上型便利貼大小），請你提供自己的摘要，我會評估其準確性並評分(1-10)。最後，我會根據文章出三道英文選擇題（主旨、細節、推論各一），每題五個選項，各選項至少25字長。",
            
            # PS 命令  
            "Rewrite passage into compressed sentences": "將題目中複雜的句子進行複雜化、壓縮或拆解，以幫助理解句子結構，克服閱讀障礙。",
            "Finding similar questions in set": "使用者提供一個題庫和一個之前做錯的樣本問題，我將從題庫中找出與樣本問題使用相似數學概念的題目，幫助你針對性練習。",
            
            # RC 命令
            "Diagnostic Label List": "針對RC題目常見的錯誤類型進行分類與標註，協助釐清學生在閱讀理解過程中遇到的具體困難。",
            "Rewrite Passage into GMAT style": "使用者提供一篇學術文章，我將其改寫成250-400字的GMAT風格文章，適合受過教育的非專業讀者閱讀。我會運用詞彙、句法和結構上的簡化策略，保留原文的核心假設、發現和含義，並確保文章 logic連貫、內容豐富且引人入勝。",
            "Preparatory answer training": "使用者提供文章、問題和答案，我會先請你提供自己版本的答案或在閱讀選項前的思路。接著，我會分析你的初步答案與正確答案的一致性，並評分(1-10分)。如果分數低於8分，我會直接指出如何改進以更接近官方答案，並提供詳細具體的建議。我會用正式、學術的語氣提供回饋，並用學術例子和類比闡明複雜概念，專注提升你的GMAT分析和推理能力，而非直接給出答案。",
            "Interactive Understanding Passage": "使用者提供一篇GMAT RC文章，我將扮演 Dustin 的 GMAT RC 文章分析器，透過5-6個有組織的邏輯順序問題來引導你理解文章。從理解主旨開始，然後分析關鍵論點和證據，最後總結。每個問題都會基於前一個問題，循序漸進地提升你的理解和分析能力。我會對你的每個回答提供回饋，直接糾正錯誤，然後繼續下一個問題。在所有問題回答完畢後，我會指出每個句子的功能、句子間的關係、標示出過渡關鍵詞，並搜尋相關背景知識以助未來理解相似文章。",
            "Predictive and Active Reading": "使用者提供一篇文章，我將扮演預測文本導師。我會引用第一句話，請你猜測下一句會是什麼。收到你的回答後，我會評估並提供改進建議，然後創建三個可能的後續發展，接著引用下一句話，解釋它與哪個可能發展一致，並請你猜測再下一句。此過程將逐句重複，直到文章結束。",
            "Enhanced reading speed": "使用者提供句子，我將自動將其劃分成邏輯上有意義的區塊，每個區塊代表一個獨立的意義單元（如主語、時間範圍、因果關係、主要論點等），以助你更好地理解句子結構。我會保持原始句子結構，並使用粗體 || 分隔區塊。",
            
            # TPA 命令
            "Understand logical terms": "使用者提供五個答案選項，我將解釋其中每個 logic 術語的含義，幫助你理解選項的確切意思。",
            "Identify features for applying specific solution": "使用者提供一個特定的解題方法，我將總結哪些題目陳述的特徵出現時，可以應用此解題方法，幫助你識別模式並有效應用方法。",
            "Create Variant Question": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題 logic與原問題相似。",
            "Finding similar questions in set": "使用者提供一個題庫和一個之前做錯的樣本問題，我將從題庫中找出與樣本問題使用相似數學概念的題目，幫助你針對性練習。"
        }

        # 標籤到科目類型的映射
        self.tag_to_category_mapping = {
            # Q科目標籤映射到PS
            "Q_": "PS",
            "CONCEPT_APPLICATION": "PS",
            "CALCULATION": "PS", 
            "READING_COMPREHENSION": "PS",
            "FOUNDATIONAL_MASTERY": "PS",
            
            # V科目標籤映射
            "CR_": "CR",
            "RC_": "RC",
            
            # DI科目標籤映射
            "DI_READING_COMPREHENSION": ["MSR", "GT", "TPA"],  # 需要進一步判斷
            "DI_GRAPH_INTERPRETATION": "GT",
            "DI_CONCEPT_APPLICATION": ["DS", "GT", "MSR", "TPA"],  # 需要進一步判斷
            "DI_LOGICAL_REASONING": ["MSR", "TPA"],
            "DI_CALCULATION": ["DS", "GT", "MSR", "TPA"],
            "DI_DATA_EXTRACTION": "GT",
            "DI_INFORMATION_EXTRACTION": ["MSR", "TPA"]
        }

        # 中文標籤到英文代碼的映射表
        self.zh_to_en_mapping = self._build_zh_to_en_mapping()

        # 路由表 - 從 gmat_route_tool.py 複製過來
        self.route_table: Dict[str, Dict[str, List[str]]] = {
            # CR路由表
            "CR": {
                "CR_STEM_UNDERSTANDING_ERROR_VOCAB": [
                    "Questions you did wrong", "Understand Logical terms", "Memorizing Vocabularies"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_SYNTAX": [
                    "Questions you did wrong", "Rewrite passage into complex sentences", "Train your close reading skill"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_LOGIC": [
                    "Questions you did wrong", "Passage you fail to organize", "Logical Chain Builder", "Train your close reading skill"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_DOMAIN": [
                    "Questions you did wrong", "Train Reading for Specific Domain"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP": [
                    "Questions you did wrong", "Role-Immersion Trainer"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_VOCAB": [
                    "Questions you did wrong", "Understand Logical terms", "Memorizing Vocabularies"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX": [
                    "Questions you did wrong", "Rewrite passage into complex sentences", "Train your close reading skill"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_LOGIC": [
                    "Questions you did wrong", "Create Variant Question", "Train your close reading skill"
                ],
                "CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP": [
                    "Questions you did wrong", "Passage you fail to organize", "Examine your thoughts",
                    "Create Variant Question", "Logical Chain Builder"
                ],
                "CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING": [
                    "Questions you did wrong", "Examine your thoughts", "Understand Logical terms", "Create Variant Question"
                ],
                "CR_REASONING_ERROR_PREDICTION_DIRECTION": [
                    "Questions you did wrong", "Examine your thoughts", "Create Variant Question",
                    "Logical Chain Builder", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION": [
                    "Questions you did wrong", "Examine your thoughts", "Create Variant Question",
                    "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT": [
                    "Questions you did wrong", "Examine your thoughts", "Create Variant Question",
                    "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE": [
                    "Questions you did wrong", "CR-BF Demo Thoughts", "Classify This Question", "Create Variant Question",
                    "Boldface Interactive Tutor", "Logical Chain Builder", "Role-Immersion Trainer", "Explain Textbook"
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC": [
                    "You did right but slowly", "Logical Chain Builder", "Train your close reading skill"
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC": [
                    "You did right but slowly", "Train your close reading skill"
                ],
                "CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING": [
                    "You did right but slowly", "Understand Logical terms"
                ],
                "CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING": [
                    "You did right but slowly", "Create Variant Question", "Logical Chain Builder",
                    "Role-Immersion Trainer", "Identify core issue"
                ],
                "CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION": [
                    "You did right but slowly", "Create Variant Question", "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT": [
                    "You did right but slowly", "Create Variant Question", "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS": [
                    "You did right but slowly", "Review distractor", "Create Variant Question"
                ],
                "CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION": [
                    "Examine your thoughts", "Review distractor", "Create Variant Question"
                ]
            },
            
            # PS路由表
            "PS": {
                "Q_READING_COMPREHENSION_ERROR": [
                    "Questions you did wrong", "Rewrite passage into compressed sentences", "Convert to real context", "Sentence Cracker"
                ],
                "Q_CONCEPT_APPLICATION_ERROR": [
                    "Questions you did wrong", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Create Variant Question", "Finding similar questions in set", "Classify This Question", "Explain Textbook"
                ],
                "Q_CALCULATION_ERROR": [
                    "Questions you did wrong", "Create Variant Question", "Finding similar questions in set"
                ],
                "Q_READING_COMPREHENSION_DIFFICULTY": [
                    "Rewrite passage into compressed sentences", "Convert to real context", "Sentence Cracker"
                ],
                "Q_CONCEPT_APPLICATION_DIFFICULTY": [
                    "You did right but slowly", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Create Variant Question", "Finding similar questions in set", "Classify This Question", "Explain Textbook"
                ],
                "Q_CALCULATION_DIFFICULTY": [
                    "You did right but slowly", "Create Variant Question", "Finding similar questions in set"
                ],
                "Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE": [
                    "You did right but slowly", "Classify This Question"
                ]
            },
            
            # RC路由表
            "RC": {
                "RC_READING_COMPREHENSION_ERROR_VOCAB": [
                    "Questions you did wrong", "Diagnostic Label List", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "Questions you did wrong", "Diagnostic Label List", "Rewrite passage into complex sentences", "Train your Close Reading Skill"
                ],
                "RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE": [
                    "Questions you did wrong", "Passage you fail to organize", "Diagnostic Label List",
                    "Create Variant Question", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING": [
                    "Questions you did wrong", "Passage you fail to organize", "Diagnostic Label List",
                    "Create Variant Question", "Explain Textbook", "Train your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT": [
                    "Questions you did wrong", "Classify This Question", "Preparatory answer training",
                    "Create Variant Question", "Explain Textbook", "Train your Close Reading Skill"
                ],
                "RC_LOCATION_SKILL_ERROR_LOCATION": [
                    "Questions you did wrong", "Preparatory answer training",
                    "Classify This Question", "Explain Textbook"
                ],
                "RC_REASONING_ERROR_INFERENCE": [
                    "Questions you did wrong", "Examine your thoughts",
                    "Preparatory answer training", "Create Variant Question", "Classify This Question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_VOCAB": [
                    "Questions you did wrong", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_SYNTAX": [
                    "Questions you did wrong", "Rewrite passage into complex sentences"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_LOGIC": [
                    "Questions you did wrong", "Train your Close Reading Skill"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_DOMAIN": [
                    "Questions you did wrong"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT": [
                    "Questions you did wrong", "Create Variant Question",
                    "Classify This Question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION": [
                    "Questions you did wrong", "Create Variant Question",
                    "Classify This Question", "Review distractor", "Explain Textbook"
                ],
                "RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING": [
                    "Questions you did wrong", "Create Variant Question", "Classify This Question", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK": [
                    "You did right but slowly", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "You did right but slowly", "Rewrite passage into complex sentences", "Train your Close Reading Skill", "Enhanced Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR": [
                    "You did right but slowly", "Passage you fail to organize", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook", "Enhanced Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK": [
                    "You did right but slowly", "Rewrite Passage into GMAT style", "Train Reading for Specific Domain"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP": [
                    "You did right but slowly", "Preparatory answer training", "Classify This Question",
                    "Explain Textbook", "Train your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY": [
                    "You did right but slowly", "Preparatory answer training", "Classify This Question", "Explain Textbook"
                ],
                "RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW": [
                    "You did right but slowly", "Examine your thoughts", "Preparatory answer training", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB": [
                    "You did right but slowly", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX": [
                    "You did right but slowly", "Rewrite passage into complex sentences"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC": [
                    "You did right but slowly", "Train your Close Reading Skill"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN": [
                    "You did right but slowly", "Train Reading for Specific Domain"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT": [
                    "You did right but slowly", "Classify This Question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS": [
                    "You did right but slowly", "Classify This Question", "Review distractor", "Explain Textbook"
                ]
            },
            
            # DS路由表
            "DS": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": ["Question you did wrong"],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Question you did wrong", "Rewrite passage into complex sentences"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Question you did wrong"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": ["Question you did wrong"],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Question you did wrong", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Create Various Questions", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Question you did wrong", "Create Various Questions", "Finding Similar Questions in Set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "Rewrite passage into complex sentences"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Create Various Questions", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Create Various Questions", "Finding Similar Questions in Set"
                ]
            },
            
            # GT路由表
            "GT": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions you did wrong", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": ["Questions you did wrong"],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": ["Questions you did wrong"],
                "DI_GRAPH_INTERPRETATION_ERROR__GRAPH": [
                    "Questions you did wrong", "Learn Math Concept",
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions you did wrong", "Learn Math Concept",
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Learn Math Concept",
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions you did wrong"],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "Learn Math Concept", "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "Learn Math Concept", "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "Learn Math Concept", "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "Sentence cracker"
                ]
            },
            
            # MSR路由表
            "MSR": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions you did wrong", "Memorizing Vocabularies", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Rewrite Passage into Complex Sentences", "Train your Close Reading Skill", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions you did wrong", "Train your Close Reading Skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions you did wrong", "Train Reading for Specific Domain"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__GRAPH": [
                    "Questions you did wrong", "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Classify This Question", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions you did wrong", "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Classify This Question", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Classify This Question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Classify This Question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions you did wrong"],
                "DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION": [
                    "Passage you failed to organize", "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "Rewrite Passage into Complex Sentences", "Train your Close Reading Skill", "Enhanced Reading Speed", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "Customize your preferred Problem-solving process and request an AI demonstration",
                    "Train your Close Reading Skill", "Enhanced Reading Speed"
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "Learn Math Concept", "Identify Features for applying a specific solution",
                    "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "Customize your preferred Problem-solving process and request an AI demonstration"
                ],
                "DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE": ["Classify This Question"],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": ["Train Reading for Specific Domain"],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "Memorizing Vocabularies", "Sentence Cracker"
                ]
            },
            
            # TPA路由表
            "TPA": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions you did wrong", "Examine your thoughts", "Understand logical terms", "Memorizing Vocabulary", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Examine your thoughts", "Passage you fail to organize",
                    "Rewrite passage into complex sentences", "Train your Close Reading Skill", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions you did wrong", "Examine your thoughts", "Passage you fail to organize",
                    "Review distractor", "Classify This Question", "Train your Close Reading Skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions you did wrong", "Examine your thoughts", "Train Reading for Specific Domain"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Learn Math Concept",
                    "Identify features for applying specific solution", "Create Variant Question",
                    "Finding similar questions in set", "Classify This Question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Review distractor", "Classify This Question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Create Variant Question", "Finding similar questions in set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You did right but slowly", "Understand logical terms", "Memorizing Vocabulary", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly", "Passage you fail to organize", "Rewrite passage into complex sentences",
                    "Train your Close Reading Skill", "Enhanced Reading Speed", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly", "Passage you fail to organize", "Review distractor",
                    "Train your Close Reading Skill", "Enhanced Reading Speed"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": [
                    "You did right but slowly", "Train Reading for Specific Domain"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn Math Concept", "Identify features for applying specific solution",
                    "Create Variant Question", "Finding similar questions in set", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You did right but slowly", "Review distractor", "Explain Textbook"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Create Variant Question", "Finding similar questions in set"
                ]
            }
        }

    def _build_zh_to_en_mapping(self) -> Dict[str, str]:
        """
        構建中文標籤到英文代碼的映射表
        
        Returns:
            Dict[str, str]: 中文標籤到英文代碼的映射
        """
        # 從各科目的翻譯模組匯入翻譯字典
        mapping = {}
        
        try:
            # Q科目翻譯 - Use new i18n system
            from gmat_diagnosis_app.i18n.translations.zh_TW import TRANSLATIONS as ZH_TRANSLATIONS
            from gmat_diagnosis_app.i18n.translations.en import TRANSLATIONS as EN_TRANSLATIONS
            
            # Create mapping from Chinese descriptions to English keys for Q subject
            for en_key in ZH_TRANSLATIONS:
                if en_key in EN_TRANSLATIONS and en_key.startswith('Q_'):
                    zh_desc = ZH_TRANSLATIONS[en_key]
                    if isinstance(zh_desc, str) and isinstance(en_key, str):
                        mapping[zh_desc] = en_key
        except ImportError:
            logging.warning("無法匯入Q科目翻譯字典")

        try:
            # V科目翻譯 - 修正匯入路徑
            from gmat_diagnosis_app.diagnostics.v_modules.translations import APPENDIX_A_TRANSLATION_V
            for en_code, zh_desc in APPENDIX_A_TRANSLATION_V.items():
                if isinstance(zh_desc, str) and isinstance(en_code, str):
                    mapping[zh_desc] = en_code
        except ImportError:
            logging.warning("無法匯入V科目翻譯字典")

        # Note: DI modules have migrated to unified i18n system and no longer use APPENDIX_A_TRANSLATION_DI
        # The translation mappings are now handled through the central i18n system
        # This eliminates the need for separate DI translation dictionary imports

        return mapping

    def translate_zh_to_en(self, zh_tag: str) -> str:
        """
        將中文標籤轉換為英文代碼
        
        Args:
            zh_tag (str): 中文標籤
            
        Returns:
            str: 對應的英文代碼，如果找不到則返回原標籤
        """
        # 首先檢查特殊映射（優先級最高）
        special_mappings = {
            "Mathematical Concept/Formula Application Difficulty": "Q_CONCEPT_APPLICATION_DIFFICULTY",
            "Mathematical Calculation Difficulty": "Q_CALCULATION_DIFFICULTY",
            "CR Stem Understanding Error: Question Requirement Grasp": "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP",
            "DI Reading Comprehension Difficulty: Mental Block Unable to Read": "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED",
            "Q Concept Application Error: Mathematical Concept/Formula Application": "Q_CONCEPT_APPLICATION_ERROR",
            "Q Calculation Error: Mathematical Calculation": "Q_CALCULATION_ERROR",
            "數據無效：用時過短（受時間壓力影響）": "DATA_INVALID_SHORT_TIME_PRESSURE_AFFECTED",
            "Q 概念應用障礙：數學觀念/公式應用困難": "Q_CONCEPT_APPLICATION_DIFFICULTY",
            "Q 計算障礙：數學計算困難": "Q_CALCULATION_DIFFICULTY",
            "CR 題幹理解錯誤：提問要求把握": "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP",
            "CR 題幹理解錯誤：詞彙": "CR_STEM_UNDERSTANDING_ERROR_VOCAB",
            "CR 題幹理解錯誤：句式": "CR_STEM_UNDERSTANDING_ERROR_SYNTAX",
            "DI 閱讀理解障礙: 心態失常讀不進去": "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED",
            "DI 閱讀理解錯誤: 詞彙理解": "DI_READING_COMPREHENSION_ERROR__VOCABULARY",
            "DI 閱讀理解錯誤: 句式理解": "DI_READING_COMPREHENSION_ERROR__SYNTAX"
        }
        
        if zh_tag in special_mappings:
            return special_mappings[zh_tag]
        
        # 完全匹配
        if zh_tag in self.zh_to_en_mapping:
            return self.zh_to_en_mapping[zh_tag]
        
        # 部分匹配（處理可能的格式差異）
        for zh_desc, en_code in self.zh_to_en_mapping.items():
            # 檢查是否為部分匹配（中文標籤包含在翻譯描述中，或反之）
            # 但要避免過於寬鬆的匹配（如短的通用詞彙）
            if len(zh_desc) >= 5:  # 避免匹配過短的描述
                if zh_tag in zh_desc or zh_desc in zh_tag:
                    # 確保匹配的描述不是通用的短詞
                    if len(zh_desc) >= len(zh_tag) * 0.6:  # 描述長度至少是標籤的60%
                        return en_code
        
        # 中文字符模糊匹配（僅對包含中文字符的文本進行）
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', zh_tag))
        
        if has_chinese:
            best_match = None
            best_score = 0.0
            
            for zh_desc, en_code in self.zh_to_en_mapping.items():
                # 只對包含中文字符的描述進行模糊匹配
                if re.search(r'[\u4e00-\u9fa5]', zh_desc):
                    ratio = self._calculate_chinese_similarity(zh_tag, zh_desc)
                    if ratio >= 0.75:  # 75%匹配率閾值
                        # 計算綜合分數：相似度 + 長度獎勵（優先選擇更長、更具體的匹配）
                        length_bonus = min(len(zh_desc) / len(zh_tag), 2.0) * 0.1  # 最多0.2的長度獎勵
                        score = ratio + length_bonus
                        
                        if score > best_score:
                            best_score = score
                            best_match = en_code
            
            if best_match:
                return best_match
        
        # 如果沒有匹配到，返回原始標籤
        return zh_tag

    def _calculate_chinese_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個中文文本的字符相似度
        
        Args:
            text1 (str): 第一個文本
            text2 (str): 第二個文本
            
        Returns:
            float: 相似度比率 (0.0 到 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # 移除標點符號和空格，只保留中文字符、英文字母和數字
        import re
        clean_text1 = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text1)
        clean_text2 = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text2)
        
        if not clean_text1 or not clean_text2:
            return 0.0
        
        # 計算字符集合的交集
        chars1 = set(clean_text1)
        chars2 = set(clean_text2)
        intersection = chars1.intersection(chars2)
        
        # 計算相似度：交集 / 較小集合的大小
        min_chars = min(len(chars1), len(chars2))
        if min_chars == 0:
            return 0.0
            
        return len(intersection) / min_chars

    def _determine_di_subcategory(self, tag: str) -> str:
        """
        為 DI 科目標籤確定具體的子類別 (DS, GT, MSR, TPA)
        
        Args:
            tag (str): DI 科目的診斷標籤
            
        Returns:
            str: 子類別 (DS, GT, MSR, TPA)
        """
        # 根據標籤內容判斷子類別
        if "GRAPH_INTERPRETATION" in tag or "DATA_EXTRACTION" in tag:
            return "GT"
        elif "MULTI_SOURCE" in tag or tag.startswith("MSR_"):
            return "MSR"
        elif "LOGICAL_REASONING" in tag and "NON_MATH" in tag:
            return "TPA"
        elif "CALCULATION" in tag and "MATH" in tag:
            # 數學計算可能屬於多個類別，需要進一步判斷
            if "DATA_SUFFICIENCY" in tag or tag.startswith("DS_"):
                return "DS"
            elif "TABLE" in tag or "GRAPH" in tag:
                return "GT"
            else:
                return "DS"  # 默認數學計算歸類為 DS
        elif "CONCEPT_APPLICATION" in tag and "MATH" in tag:
            # 數學概念應用也需要進一步判斷
            if "DATA_SUFFICIENCY" in tag or tag.startswith("DS_"):
                return "DS"
            elif "TABLE" in tag or "GRAPH" in tag:
                return "GT"
            else:
                return "MSR"  # 默認數學概念應用歸類為 MSR
        elif "READING_COMPREHENSION" in tag:
            # 閱讀理解根據具體內容判斷
            if "MULTI_SOURCE" in tag:
                return "MSR"
            elif "VOCABULARY" in tag or "SYNTAX" in tag:
                return "TPA"  # 詞彙和語法問題更常見於 TPA
            else:
                return "MSR"  # 默認閱讀理解歸類為 MSR
        else:
            # 默認歸類
            return "MSR"

    def determine_category_from_tag(self, tag: str, subject: str = None) -> str:
        """
        根據標籤和科目確定路由類別
        
        Args:
            tag (str): 診斷標籤
            subject (str): 科目（Q, V, DI）
            
        Returns:
            str: 路由類別
        """
        # 如果標籤直接以類別開頭，優先使用
        for category in ["CR", "RC", "PS", "DS", "GT", "MSR", "TPA"]:
            if tag.startswith(category + "_"):
                return category
        
        # 根據科目和標籤前綴判斷
        if subject == "Q":
            return "PS"
        elif subject == "V":
            if "CR_" in tag:
                return "CR"
            elif "RC_" in tag:
                return "RC"
            else:
                # 默認根據內容判斷
                if any(keyword in tag.lower() for keyword in ["critical", "reasoning", "argument", "logic"]):
                    return "CR"
                else:
                    return "RC"
        elif subject == "DI":
            # 使用專門的 DI 子類別判斷方法
            return self._determine_di_subcategory(tag)
        
        # 如果無法確定，返回默認值
        return "PS" if subject == "Q" else "CR" if subject == "V" else "MSR"

    def route_diagnosis_tag(self, tag: str, subject: str = None) -> List[str]:
        """
        根據診斷標籤路由到適當的訓練命令
        
        Args:
            tag (str): 診斷標籤（中文或英文）
            subject (str): 科目（Q, V, DI）
            
        Returns:
            List[str]: 推薦的訓練命令列表
        """
        # 將中文標籤轉換為英文代碼
        en_tag = self.translate_zh_to_en(tag)
        
        # 行為標籤不顯示指令
        if en_tag.startswith('BEHAVIOR_') or tag.startswith('行為'):
            return []
        
        # 確定類別
        category = self.determine_category_from_tag(en_tag, subject)
        
        # 查找路由表
        if category in self.route_table:
            category_routes = self.route_table[category]
            
            # 嘗試精確匹配（使用英文代碼）
            if en_tag in category_routes:
                return category_routes[en_tag]
            
            # 模糊匹配（使用英文代碼）
            for route_key in category_routes:
                if self._fuzzy_match(en_tag, route_key):
                    return category_routes[route_key]
        
        # 如果沒有匹配到，返回空列表
        return []

    def _fuzzy_match(self, tag: str, route_key: str) -> bool:
        """
        模糊匹配邏輯
        
        Args:
            tag (str): 診斷標籤
            route_key (str): 路由表中的鍵
            
        Returns:
            bool: 是否匹配
        """
        # 去除下劃線和轉換為小寫進行比較
        tag_clean = tag.replace("_", " ").lower()
        route_key_clean = route_key.replace("_", " ").lower()
        
        # 檢查關鍵詞匹配
        tag_words = set(tag_clean.split())
        route_key_words = set(route_key_clean.split())
        
        # 如果有75%以上的關鍵詞匹配，認為是模糊匹配
        if len(tag_words) > 0 and len(route_key_words) > 0:
            intersection = tag_words.intersection(route_key_words)
            match_ratio = len(intersection) / min(len(tag_words), len(route_key_words))
            return match_ratio >= 0.75
        
        return False

    def generate_recommendations_from_dataframe(self, df: pd.DataFrame, subject: str) -> str:
        """
        從數據框生成AI工具建議
        
        Args:
            df (pd.DataFrame): 包含診斷標籤的數據框
            subject (str): 科目（Q, V, DI）
            
        Returns:
            str: 格式化的建議文本
        """
        if df.empty:
            return "(無數據可供分析)"
        
        # 收集所有診斷標籤
        all_tags = []
        for tags_list in df['diagnostic_params_list'].dropna():
            if isinstance(tags_list, list):
                all_tags.extend(tags_list)
        
        if not all_tags:
            return "(未找到診斷標籤)"
        
        # 計算標籤頻率
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 按頻率排序，只保留前三個標籤
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 生成建議
        recommendations = []
        
        # 處理頻率最高的三個標籤
        for tag, count in sorted_tags:
            commands = self.route_diagnosis_tag(tag, subject)
            
            recommendation_text = f"**{tag}** (出現{count}次):\n"
            
            if commands:
                # 顯示所有對應的指令，不進行過濾
                for command in commands:
                    description = self.command_descriptions.get(command, "描述暫未提供")
                    recommendation_text += f"- **{command}**: {description}\n"
            elif tag.startswith('BEHAVIOR_'):
                # 行為標籤的特殊處理
                recommendation_text += "- *此為行為模式標籤，無需特定工具練習，建議注意答題習慣的調整*\n"
            else:
                # 無法匹配的標籤
                recommendation_text += "- *暫無對應的工具推薦，建議諮詢教學專家*\n"
            
            recommendations.append(recommendation_text)
        
        if not recommendations:
            return f"未找到特定匹配的工具建議。建議參考GMAT官方指南中的{subject}科相關練習和策略。"
        
        return "\n".join(recommendations)

    def get_command_description(self, command_name: str) -> Optional[str]:
        """
        獲取命令描述
        
        Args:
            command_name (str): 命令名稱
            
        Returns:
            Optional[str]: 命令描述
        """
        return self.command_descriptions.get(command_name)

    def get_available_categories(self) -> List[str]:
        """
        獲取所有可用的類別
        
        Returns:
            List[str]: 類別列表
        """
        return list(self.route_table.keys()) 