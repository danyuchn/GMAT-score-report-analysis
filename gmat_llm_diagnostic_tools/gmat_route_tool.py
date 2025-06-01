"""
title: GMAT Issue Router
author: GMAT GPT Team
author_url: https://github.com/your-repo
description: Routes GMAT issues to appropriate training commands based on category and error code, with integrated command descriptions and usage occasions
version: 2.1.0
license: MIT
requirements: typing
"""

from typing import Dict, List, Optional, TypedDict

# 為 command_details 定義一個 TypedDict，更清晰
class CommandDetail(TypedDict):
    description: str
    usage_occasion: str

class FormattedCommand(TypedDict):
    command: str
    description: str
    usage_occasion: str

class Tools:
    def __init__(self):
        """Initialize the GMAT Issue Router tool with integrated command descriptions and usage occasions."""
        
        # 修改 command_descriptions 結構，每個指令包含 description 和 usage_occasion
        self.command_details: Dict[str, CommandDetail] = {
            "Questions you did wrong": {
                "description": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。最適合觀念真正不懂的題目",
                "usage_occasion": "當你做錯題目，需要理解正確解法與考點時。"
            },
            "You did right but slowly": {
                "description": "使用者提供雖然做對但耗時過長的題目 (CR或TPA非數學相關)，我將提供 N分鐘內快速解題的捷徑。我會引導你先閱讀問題，識別解鎖問題的關鍵要素，然後判斷文本中哪些部分是相關信息，哪些不是，最後指出使用預寫策略還是排除策略來回答問題。每個步驟都包含清晰的提示，引導至下一步，並遵循線性的單向思維過程。",
                "usage_occasion": "當你題目雖然做對，但解題速度過慢，希望找到更快捷徑時。"
            },
            "Passages you fail to organize": {
                "description": "使用者提供一篇難以組織的文章，我將為其創建一個心智圖（markdown格式，輸出在代碼塊中），幫助你視覺化資訊間的關係，從而更好地理解文章結構和 logic。",
                "usage_occasion": "當你閱讀文章後，對整體結構、段落關係或論點脈絡感到困惑時。"
            },
            "Examine your thoughts": {
                "description": "使用者提供口頭解題過程的錄音轉文字稿和題目文本，我將分析你的解題思路，找出其中的錯誤和可以改進的地方，幫助你提升解題效率和準確性。",
                "usage_occasion": "當你想深入了解自己解題過程中的盲點或低效環節時。"
            },
            "CR-BF Demo Thoughts": {
                "description": "使用者提供Boldface題目，我將扮演AI助教，專門解決邏輯推理問題（例如BF題型）。我會遵循五大原則，逐步分析和回答問題，採用循環迭代的方法，每次專注於一個核心差異，並在每個循環中進行單一推斷，以排除選項，直到剩下一個為止。如果需要更多信息，我會請求澄清，而不是假設或跳過步驟。",
                "usage_occasion": "當你需要學習如何有條理地分析CR Boldface題目的論證結構時。"
            },
            "Understand Logical terms": {
                "description": "使用者提供五個答案選項，我將解釋其中每個 logic 術語的含義，幫助你理解選項的確切意思。",
                "usage_occasion": "當你對CR或TPA題目選項中出現的邏輯術語（如前提、結論、假設、削弱等）感到困惑時。"
            },
            "Rewrite passage into complex sentences": {
                "description": "使用者提供一篇文章，我將保留其確切的核心含義，不任意增刪觀點、含義或細節，將其改寫成用詞艱深、風格抽象的版本。改寫後的文章長度不超過原文1.5倍，每段至少包含2-3個體現這些風格的句子。我將提供改寫後的英文文章、一個簡單易懂的白話文版本，並簡要說明改寫如何運用抽象 logic詞彙、複雜句型和客觀語氣，同時確認未增刪意義且符合長度限制。",
                "usage_occasion": "當你想提升對複雜長句的理解能力，或想了解學術文章的常見表達方式時。"
            },
            "Review distractor": {
                "description": "使用者提供一個GMAT問題以及一個正確選項和一個錯誤選項。我會用繁體中文，以像對10歲小孩說話的語氣和風格，詳細解釋為什麼正確選項符合題目要求，以及為什麼錯誤選項不符合。我會為正確和錯誤選項各提供兩個不同的類比情境（新故事），幫助你理解。然後，我會問你想要更多類比例子還是設計一個變體問題。如果選擇設計變體問題，我會根據你提供的英文問題和兩個選項，更改故事的領域和內容，但保留文章和選項的logic，並創建一個語法結構盡可能相似的英文變體問題和兩個選項。",
                "usage_occasion": "當你對某個題目的選項特別糾結，尤其是搞不清楚為什麼自己選的錯誤選項不對，或者正確選項為什麼對時。"
            },
            "Classify this question": { # CR/TPA/MSR/RC/PS/DS 皆可能
                "description": "使用者提供CR或TPA非數學相關問題，我將判斷其屬於分析、建構、評論或計畫四大子類型中的哪一種，並進行兩次獨立判斷以確保一致性。若不一致則進行第三次最終判斷。最後，我會提供一個表格整理各子類型的出現次數，助你找出弱點題型。 (對於RC/MSR，則判斷主旨、支持、推論、評估、應用等類型；對於PS/DS，則判斷涉及的數學概念領域)",
                "usage_occasion": "當你想了解自己在哪類特定問題上較弱，以便進行針對性練習時。"
            },
            "Create variant question": { # CR/DS/PS/RC/TPA 皆可能
                "description": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題 logic與原問題相似。",
                "usage_occasion": "當你理解了一個題目的解法後，想透過相似題目鞏固理解並練習應用時。"
            },
            "Boldface Interactive Tutor": {
                "description": "使用者提供CR boldface問題及其官方答案和用[]標記的粗體部分。我將扮演GMAT Boldface互動導師，透過『你問 -> 使用者回答 -> 評估使用者回答並問下一個問題』的互動形式，逐步引導你分析問題。首先，我會逐句引導你解釋文章中每個句子的作用，並在你理解有誤時提供糾正。完成所有句子的討論後，我會再次展示你對所有句子作用的回答（已修正），並標明文章中的第一和第二粗體部分。接著，我會逐個引導你分析每個答案選項（初期不透露官方答案）：詢問保留或排除該選項，若排除則詢問理由並評估其正確性。如果你排除了官方答案，我會指出你推理的錯誤並引導你，直到你選擇官方答案為止。",
                "usage_occasion": "當你需要針對CR Boldface題目進行深入的互動式學習和分析訓練時。"
            },
            "Logical Chain Builder": {
                "description": "使用者提供CR論證評估型文章，並指定邏輯鏈的起點和終點。我將以繁體中文構建一個簡化的邏輯鏈，直接關聯起點和終點，並包含必要的隱藏假設。邏輯鏈將使用 -> 表示因果關係，+ 表示並列關係，() 表示隱藏假設。我會重新檢查邏輯鏈，確保沒有遺漏影響結論有效性的重要隱藏假設或前提，並以學術、精確和簡潔的方式引導你理解論證的 logic結構，如果文章不清晰，我會請求更多信息。",
                "usage_occasion": "當你需要理清CR題目中的論證脈絡，找出前提、結論及隱含假設時。"
            },
            "Identify core issue": {
                "description": "使用者提供一篇GMAT CR文章，我會將其核心問題轉化為'是否'的形式，並創建具有相同邏輯結構但在不同情境下的類比場景。我不會立即揭示新場景的核心問題，而是提示你自行識別。在你回答後，我會揭示場景的實際核心問題，並評估你答案的準確性，提供糾正和指導以增強你的理解。",
                "usage_occasion": "當你難以準確判斷CR題目論證的核心爭議點或問題焦點時。"
            },
            "Role-Immersion Trainer": {
                "description": "使用者提供GMAT CR文章，我將首先確定文章中信息最直接影響的角色。接著，我會詢問你希望進行「推斷」還是「解釋」。若選擇「解釋」，我將從該角色角度解釋文章中的不一致或矛盾事實，避免超出文本的假設；若選擇「推斷」，我將從該角色角度，嚴格基於文章數據或觀察結果得出結論，避免猜測。結論或解釋將以項目符號列表形式呈現，並使用第一人稱。最後，我會請你提供文章的官方答案，並詳細解釋我之前得出的哪個結論或解釋與官方答案最一致。",
                "usage_occasion": "當你想練習從特定視角理解CR文章信息並進行推斷或解釋時。"
            },
            "Explain Textbook": { # CR/DS/GT/MSR/PS/RC/TPA 皆可能
                "description": "使用者提供教材的文字或截圖，我會用繁體中文並以中學生易懂的方式解釋概念，並提供三個例子。接著詢問你是否需要測驗。若同意，我會呈現三個新情境（部分正確應用概念，部分否），請你指出適用情境。我會自我檢查評估邏輯後，再評估你的答案並提供回饋。",
                "usage_occasion": "當你對GMAT教材中的特定概念或知識點感到不理解時。"
            },
            "Train your close reading skill": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者提供短文（80-120字），我將扮演精讀教練，一次只呈現第一句話，請你理解。收到你的詮釋後，僅在對句子主旨或核心邏輯有根本性誤解，或中文語序怪異不自然時才介入修正，忽略用詞、術語不精確或措辭差異（若大致意思相同）。修正後（或無需修正時）呈現下一句，依此類推。所有句子單獨檢視完畢後，展示你所有的詮釋，並請你將其修改成連貫的段落。",
                "usage_occasion": "當你想提升對句子層面細節和邏輯的精準理解能力時。"
            },
            "Train Reading for Specific Domain": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者指定一個特定領域，我將提供該領域內三個非常具體、狹窄但高度爭議性的主題，請你選擇其一。接著，我会根據你選擇的主題創建一篇200-350字的GMAT風格英文文章，呈現多種立場、論點或理論，並進行分析、批判或擴展，同時納入具體範例或實證數據支持論點。文章會使用正式學術詞彙和複雜句型。收到文章後，請你提供摘要。然後我會提供該文章的簡明繁體中文摘要（掌上型便利貼大小），並評估你的摘要準確性，提供具體回饋及1-10分評分。最後，我會根據文章出三道英文選擇題（主旨、細節、推論各一），每題五個選項，各選項至少25字長。",
                "usage_occasion": "當你發現在特定學科領域（如科技、社科、人文）的文章閱讀上有困難時。"
            },
            "Memorizing Vocabularies": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者提供需要記憶的單字，我將為每個單字創建一個包含英文單字、中文意思、詞性和至少25字長（含至少兩子句及複雜結構如插入語、倒裝或省略）的例句的試算表。接著，我會詢問你是否有仍不熟悉的單字，並用繁體中文和英文以十年級學生能理解的方式解釋，提供三個相關概念，然後詢問是否進入下一步。然後，我會用所有提供的單字寫一篇200-350字GMAT學術風格的英文文章，每句至少25字長且含複雜結構，並顯示字數。之後，我會提供該文章的簡明繁體中文摘要（掌上型便利貼大小），請你提供自己的摘要，我會評估其準確性並評分(1-10)。最後，我會根據文章出三道英文選擇題（主旨、細節、推論各一），每題五個選項，各選項至少25字長。",
                "usage_occasion": "當你需要系統性地學習和記憶GMAT核心詞彙時。"
            },
            # DS Commands
            "Learn math concepts": {
                "description": "使用者提供一個數學問題，我將從出題者的角度思考，指出這個問題想要測試哪些具體的數學概念，幫助你理解題目背後的考點。",
                "usage_occasion": "當你對DS或PS題目涉及的數學概念不熟悉或理解不透徹時。"
            },
            "Identify features for applying a specific solution": { # DS/GT/MSR/PS/TPA 皆可能
                "description": "使用者提供一個特定的解題方法，我將總結哪些題目陳述的特徵出現時，可以應用此解題方法，幫助你識別模式並有效應用方法。",
                "usage_occasion": "當你學會了一種解題方法，但不知道在何種題型或條件下應用它時。"
            },
            "Finding Similar Questions in Set": { # DS/PS 皆可能
                "description": "使用者提供一個題庫和一個之前做錯的樣本問題，我將從題庫中找出與樣本問題使用相似數學概念的題目，幫助你針對性練習。",
                "usage_occasion": "當你想針對特定數學概念或錯題類型進行集中練習時。"
            },
            "Convert to real context": { # DS/PS 皆可能
                "description": "使用者提供GMAT數學選擇題（文字或圖片形式），我會將其轉換成一個包含真實情境和故事情節的英文應用題（30-50字），且不更改任何數值。如果原題已是應用題，則僅翻譯成英文。",
                "usage_occasion": "當你覺得抽象的數學題目難以理解，希望透過實際情境幫助思考時。"
            },
            # GT Commands  
            "Sentence cracker": { # GT/MSR 皆可能
                "description": "使用者提供一個難以理解的句子，我會先將其簡化到九年級學生能懂的程度。然後詢問你的困難點是領域特定詞彙、一般詞彙、複雜句型，還是綜合性的。若為詞彙問題，請指出不清楚的單字。領域詞彙我會解釋並提供三個相關概念；一般詞彙則提供三個同義詞和反義詞，各附一個至少25字且含複雜結構的例句。若為句型問題，我會拆解句子結構，逐一說明各成分含義，再解釋如何組織這些含義以理解原句，最後保持原句 estructura，改寫成五個不同領域但句型相似的版本。",
                "usage_occasion": "當你在閱讀圖表題或多源推理的文字說明時，遇到難以理解的長句或複雜表達時。"
            },
            # MSR Commands
            "Customize your preferred Problem-solving process and request an AI demonstration": {
                "description": "使用者告訴我你偏好的解題順序 (SOP)，我將依此判斷最短、最有效率的閱讀路徑，並遵循人類單向思維模式進行演示。",
                "usage_occasion": "當你想優化多源推理題目的解題流程，或驗證自己SOP的有效性時。"
            },
            "Enhanced Reading Speed": { # MSR/RC/TPA 皆可能
                "description": "使用者提供句子，我將自動將其劃分成邏輯上有意義的區塊，每個區塊代表一個獨立的意義單元（如主語、時間範圍、因果關係、主要論點等），以助你更好地理解句子結構。我會保持原始句子結構，並使用粗體 || 分隔區塊。",
                "usage_occasion": "當你需要提高閱讀速度，並快速抓住句子核心意義單元時。"
            },
            # PS Commands
            "Rewrite passage into compressed sentences": {
                "description": "將題目中複雜的句子進行複雜化、壓縮或拆解，以幫助理解句子結構，克服閱讀障礙。",
                "usage_occasion": "當PS題目的文字描述過於冗長或複雜，影響你理解題意時。"
            },
            # RC Commands
            "Diagnostic Label List": {
                "description": "針對RC題目常見的錯誤類型進行分類與標註，協助釐清學生在閱讀理解過程中遇到的具體困難。",
                "usage_occasion": "當你想系統性地分析自己在RC題目上的錯誤模式和原因時。"
            },
            "Rewrite Passage into GMAT style": {
                "description": "使用者提供一篇學術文章，我將其改寫成250-400字的GMAT風格文章，適合受過教育的非專業讀者閱讀。我會運用詞彙、句法和結構上的簡化策略，保留原文的核心假設、發現和含義，並確保文章 logic連貫、內容豐富且引人入勝。",
                "usage_occasion": "當你想了解GMAT RC文章的典型風格和寫作特點，或想將其他學術內容轉換為GMAT閱讀材料時。"
            },
            "Preparatory answer training": {
                "description": "使用者提供文章、問題和答案，我會先請你提供自己版本的答案或在閱讀選項前的思路。接著，我會分析你的初步答案與正確答案的一致性，並評分(1-10分)。如果分數低於8分，我會直接指出如何改進以更接近官方答案，並提供詳細具體的建議。我會用正式、學術的語氣提供回饋，並用學術例子和類比闡明複雜概念，專注提升你的GMAT分析和推理能力，而非直接給出答案。",
                "usage_occasion": "當你想訓練自己在看選項前主動思考答案的能力，並獲得針對性的思路修正建議時。"
            },
            "Interactive Understanding Passage": {
                "description": "使用者提供一篇GMAT RC文章，我將扮演 Dustin 的 GMAT RC 文章分析器，透過5-6個有組織的邏輯順序問題來引導你理解文章。從理解主旨開始，然後分析關鍵論點和證據，最後總結。每個問題都會基於前一個問題，循序漸進地提升你的理解和分析能力。我會對你的每個回答提供回饋，直接糾正錯誤，然後繼續下一個問題。在所有問題回答完畢後，我會指出每個句子的功能、句子間的關係、標示出過渡關鍵詞，並搜尋相關背景知識以助未來理解相似文章。",
                "usage_occasion": "當你需要逐層深入地理解RC文章的結構、論點和細節時。"
            },
            "Predictive and Active Reading": {
                "description": "使用者提供一篇文章，我將扮演預測文本導師。我會引用第一句話，請你猜測下一句會是什麼。收到你的回答後，我會評估並提供改進建議，然後創建三個可能的後續發展，接著引用下一句話，解釋它與哪個可能發展一致，並請你猜測再下一句。此過程將逐句重複，直到文章結束。",
                "usage_occasion": "當你想訓練主動閱讀和預測文章發展的能力，以提高閱讀專注度和理解深度時。"
            }
            # TPA Commands - 部分已在CR/MSR/DS中定義，此處可按需補充TPA特有的
            # "Understand logical terms" - 已有
            # "Passage you fail to organize" - 已有
            # "Identify features for applying specific solution" - 已有
            # "Create Variant Question" - 已有
            # "Memorizing Vocabulary" - 已有 (注意 TPA 可能會有特定術語，但通用指令已覆蓋)
            # "Enhanced reading speed" - 已有
        }
        # (route_table 和 error_codes_mapping 保持不變)
        self.route_table: Dict[str, Dict[str, List[str]]] = {
            # ... (您的 route_table 內容不變) ...
            # ------------------------  CR  ------------------------
            "CR": {
                "CR_STEM_UNDERSTANDING_ERROR_VOCAB": [
                    "Questions you did wrong", "Understand Logical terms", "Memorizing Vocabularies"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_SYNTAX": [
                    "Questions you did wrong", "Rewrite passage into complex sentences", "Train your close reading skill"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_LOGIC": [
                    "Questions you did wrong", "Passages you fail to organize", "Logical Chain Builder", "Train your close reading skill"
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
                    "Questions you did wrong", "Create variant question", "Train your close reading skill"
                ],
                "CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP": [
                    "Questions you did wrong", "Passages you fail to organize", "Examine your thoughts",
                    "Create variant question", "Logical Chain Builder"
                ],
                "CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING": [
                    "Questions you did wrong", "Examine your thoughts", "Understand Logical terms", "Create variant question"
                ],
                "CR_REASONING_ERROR_PREDICTION_DIRECTION": [
                    "Questions you did wrong", "Examine your thoughts", "Create variant question",
                    "Logical Chain Builder", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION": [
                    "Questions you did wrong", "Examine your thoughts", "Create variant question",
                    "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT": [
                    "Questions you did wrong", "Examine your thoughts", "Create variant question",
                    "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE": [
                    "Questions you did wrong", "CR-BF Demo Thoughts", "Classify this question", "Create variant question",
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
                    "You did right but slowly", "Create variant question", "Logical Chain Builder",
                    "Role-Immersion Trainer", "Identify core issue"
                ],
                "CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION": [
                    "You did right but slowly", "Create variant question", "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT": [
                    "You did right but slowly", "Create variant question", "Identify core issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS": [
                    "You did right but slowly", "Review distractor", "Create variant question"
                ],
                "CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION": [
                    "Examine your thoughts", "Review distractor", "Create variant question"
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB": [
                    "You did right but slowly","Understand Logical terms", "Memorizing Vocabularies" # Added You did right but slowly as per example, assuming vocab can also be a speed issue
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB": [
                    "You did right but slowly","Understand Logical terms", "Memorizing Vocabularies" # Added You did right but slowly
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX": [
                    "You did right but slowly","Rewrite passage into complex sentences", "Train your close reading skill" # Added You did right but slowly
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX": [
                    "You did right but slowly","Rewrite passage into complex sentences", "Train your close reading skill" # Added You did right but slowly
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN": [
                    "You did right but slowly","Train Reading for Specific Domain" # Added You did right but slowly
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_DOMAIN": [ # This is an ERROR, not DIFFICULTY, so "You did right but slowly" might not fit unless specified. Kept original.
                    "Questions you did wrong","Train Reading for Specific Domain"
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN": [
                    "You did right but slowly","Train Reading for Specific Domain" # Added You did right but slowly
                ],
            },
            "DS": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": ["Question you did wrong"],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Question you did wrong", "Rewrite passage into complex sentences", "Convert to real context"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Question you did wrong", "Convert to real context"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": ["Question you did wrong"],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Question you did wrong", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook" # Changed Create Various Questions to Create variant question for consistency
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Question you did wrong", "Create variant question", "Finding Similar Questions in Set" # Changed Create Various Questions to Create variant question
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly","Rewrite passage into complex sentences", "Convert to real context" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly", "Convert to real context"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook" # Changed Create Various Questions to Create variant question
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Create variant question", "Finding Similar Questions in Set" # Changed Create Various Questions to Create variant question
                ],
            },
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
                    "Questions you did wrong", "Learn math concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions you did wrong", "Learn math concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Learn math concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify features for applying a specific solution", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions you did wrong"],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "You did right but slowly","Learn math concepts", "Identify features for applying a specific solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "You did right but slowly","Learn math concepts", "Identify features for applying a specific solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly","Learn math concepts", "Identify features for applying a specific solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You did right but slowly","Sentence cracker" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly","Sentence cracker" # Added You did right but slowly
                ],
            },
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
                    "Questions you did wrong", "Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions you did wrong", "Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions you did wrong"],
                "DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION": [
                    "You did right but slowly","Passage you fail to organize", "Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly","Rewrite Passage into Complex Sentences", "Train your Close Reading Skill", "Enhanced Reading Speed", "Sentence Cracker" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly","Customize your preferred Problem-solving process and request an AI demonstration",
                    "Train your Close Reading Skill", "Enhanced Reading Speed" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "You did right but slowly","Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "You did right but slowly","Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly","Learn math concepts", "Identify Features for applying a specific solution", # Corrected casing
                    "Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You did right but slowly","Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly","Customize your preferred Problem-solving process and request an AI demonstration" # Added You did right but slowly
                ],
                "DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE": ["Classify this question"], # Assuming "You did right but slowly" isn't always implied by SFE
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": ["You did right but slowly","Train Reading for Specific Domain"], # Added You did right but slowly
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You did right but slowly","Memorizing Vocabularies", "Sentence Cracker" # Added You did right but slowly
                ],
            },
             "PS": {
                "Q_READING_COMPREHENSION_ERROR": [
                    "Questions you did wrong", "Rewrite passage into compressed sentences", "Convert to real context", "Sentence Cracker"
                ],
                "Q_CONCEPT_APPLICATION_ERROR": [
                    "Questions you did wrong", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding similar questions in set", "Classify this question", "Explain Textbook"
                ],
                "Q_CALCULATION_ERROR": [
                    "Questions you did wrong", "Create variant question", "Finding similar questions in set"
                ],
                "Q_READING_COMPREHENSION_DIFFICULTY": [
                    "You did right but slowly","Rewrite passage into compressed sentences", "Convert to real context", "Sentence Cracker" # Added You did right but slowly
                ],
                "Q_CONCEPT_APPLICATION_DIFFICULTY": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding similar questions in set", "Classify this question", "Explain Textbook"
                ],
                "Q_CALCULATION_DIFFICULTY": [
                    "You did right but slowly", "Create variant question", "Finding similar questions in set"
                ],
                "Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE": [
                    "You did right but slowly", "Classify this question"
                ],
            },
            "RC": {
                "RC_READING_COMPREHENSION_ERROR_VOCAB": [
                    "Questions you did wrong", "Diagnostic Label List", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "Questions you did wrong", "Diagnostic Label List", "Rewrite passage into complex sentences", "Train your Close Reading Skill"
                ],
                "RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE": [
                    "Questions you did wrong", "Passages you fail to organize", "Diagnostic Label List",
                    "Create variant question", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING": [
                    "Questions you did wrong", "Passages you fail to organize", "Diagnostic Label List",
                    "Create variant question", "Explain Textbook", "Train your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT": [
                    "Questions you did wrong", "Diagnostic Label List", "Preparatory answer training",
                    "Create variant question", "Classify this question", "Explain Textbook", "Train your Close Reading Skill" # Changed Classify This Question to Classify this question
                ],
                "RC_LOCATION_SKILL_ERROR_LOCATION": [
                    "Questions you did wrong", "Diagnostic Label List", "Preparatory answer training",
                    "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_REASONING_ERROR_INFERENCE": [
                    "Questions you did wrong", "Examine your thoughts", "Diagnostic Label List",
                    "Preparatory answer training", "Create variant question", "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_ERROR_VOCAB": [
                    "Questions you did wrong", "Diagnostic Label List", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_SYNTAX": [
                    "Questions you did wrong", "Diagnostic Label List", "Rewrite passage into complex sentences"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_LOGIC": [
                    "Questions you did wrong", "Diagnostic Label List", "Train your Close Reading Skill"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_DOMAIN": [
                    "Questions you did wrong", "Diagnostic Label List", "Train Reading for Specific Domain" # Added "Train Reading for Specific Domain" based on difficulty counterpart
                ],
                "RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT": [
                    "Questions you did wrong", "Diagnostic Label List", "Create variant question",
                    "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION": [
                    "Questions you did wrong", "Diagnostic Label List", "Create variant question",
                    "Classify this question", "Review distractor", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING": [
                    "Questions you did wrong", "Create variant question", "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK": [
                    "You did right but slowly", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "You did right but slowly", "Rewrite passage into complex sentences", "Train your Close Reading Skill", "Enhanced Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR": [
                    "You did right but slowly", "Passages you fail to organize", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook", "Enhanced Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK": [
                    "You did right but slowly", "Rewrite Passage into GMAT style", "Train Reading for Specific Domain"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP": [
                    "You did right but slowly", "Preparatory answer training", "Classify this question", # Changed Classify This Question to Classify this question
                    "Explain Textbook", "Train your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY": [
                    "You did right but slowly", "Preparatory answer training", "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
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
                "RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT": [ # Provided example JSON used this error code
                    "You did right but slowly", "Classify this question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS": [
                    "You did right but slowly", "Classify this question", "Review distractor", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
            },
             "TPA": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions you did wrong", "Examine your thoughts", "Understand logical terms", "Memorizing Vocabularies", "Sentence Cracker" # Changed Memorizing Vocabulary to Memorizing Vocabularies
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Examine your thoughts", "Passages you fail to organize",
                    "Rewrite passage into complex sentences", "Train your Close Reading Skill", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions you did wrong", "Examine your thoughts", "Passages you fail to organize",
                    "Review distractor", "Classify this question", "Train your Close Reading Skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions you did wrong", "Examine your thoughts", "Train Reading for Specific Domain"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Learn math concepts",
                    "Identify features for applying a specific solution", "Create variant question",
                    "Finding similar questions in set", "Classify this question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Review distractor", "Classify this question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Create variant question", "Finding similar questions in set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You did right but slowly", "Understand logical terms", "Memorizing Vocabularies", "Sentence Cracker" # Changed Memorizing Vocabulary to Memorizing Vocabularies
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly", "Passages you fail to organize", "Rewrite passage into complex sentences",
                    "Train your Close Reading Skill", "Enhanced Reading Speed", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly", "Passages you fail to organize", "Review distractor",
                    "Train your Close Reading Skill", "Enhanced Reading Speed"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": [
                    "You did right but slowly", "Train Reading for Specific Domain"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding similar questions in set", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You did right but slowly", "Review distractor", "Explain Textbook"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Create variant question", "Finding similar questions in set"
                ],
            },
        }
        self.error_codes_mapping_dict = {
            # ... (您的 error_codes_mapping_dict 內容不變) ...
             "CR": {
                # ERROR types
                "題幹詞彙理解錯誤": "CR_STEM_UNDERSTANDING_ERROR_VOCAB",
                "題幹語法理解錯誤": "CR_STEM_UNDERSTANDING_ERROR_SYNTAX",
                "題幹邏輯理解錯誤": "CR_STEM_UNDERSTANDING_ERROR_LOGIC",
                "題幹領域知識錯誤": "CR_STEM_UNDERSTANDING_ERROR_DOMAIN",
                "題幹問題要求理解錯誤": "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP",
                "選項詞彙理解錯誤": "CR_CHOICE_UNDERSTANDING_ERROR_VOCAB",
                "選項語法理解錯誤": "CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX",
                "選項邏輯理解錯誤": "CR_CHOICE_UNDERSTANDING_ERROR_LOGIC",
                "選項領域知識錯誤": "CR_CHOICE_UNDERSTANDING_ERROR_DOMAIN",
                "邏輯鏈分析前提結論關係錯誤": "CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP",
                "抽象邏輯術語理解錯誤": "CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING",
                "預測方向錯誤": "CR_REASONING_ERROR_PREDICTION_DIRECTION",
                "核心問題識別錯誤": "CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION",
                "選項相關性判斷錯誤": "CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT",
                "強干擾選項混淆錯誤": "CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION",
                "特定題型弱點": "CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE",
                # DIFFICULTY types
                "題幹詞彙理解困難": "CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB",
                "題幹語法理解困難": "CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX",
                "題幹邏輯理解困難": "CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC",
                "題幹領域知識困難": "CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN",
                "選項詞彙理解困難": "CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB",
                "選項語法理解困難": "CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX",
                "選項邏輯理解困難": "CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC",
                "選項領域知識困難": "CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN",
                "抽象邏輯術語理解困難": "CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING",
                "預測方向缺失困難": "CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING",
                "核心問題識別困難": "CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION",
                "選項相關性判斷困難": "CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT",
                "強干擾選項分析困難": "CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS"
            },
            "DS": {
                "閱讀理解詞彙錯誤": "DI_READING_COMPREHENSION_ERROR__VOCABULARY",
                "閱讀理解語法錯誤": "DI_READING_COMPREHENSION_ERROR__SYNTAX",
                "閱讀理解邏輯錯誤": "DI_READING_COMPREHENSION_ERROR__LOGIC",
                "閱讀理解領域錯誤": "DI_READING_COMPREHENSION_ERROR__DOMAIN",
                "數學概念應用錯誤": "DI_CONCEPT_APPLICATION_ERROR__MATH",
                "數學計算錯誤": "DI_CALCULATION_ERROR__MATH",
                "閱讀理解語法困難": "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX",
                "閱讀理解邏輯困難": "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC",
                "數學概念應用困難": "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH",
                "數學計算困難": "DI_CALCULATION_DIFFICULTY__MATH"
            },
            "GT": {
                "閱讀理解詞彙錯誤": "DI_READING_COMPREHENSION_ERROR__VOCABULARY",
                "閱讀理解語法錯誤": "DI_READING_COMPREHENSION_ERROR__SYNTAX",
                "閱讀理解邏輯錯誤": "DI_READING_COMPREHENSION_ERROR__LOGIC",
                "閱讀理解領域錯誤": "DI_READING_COMPREHENSION_ERROR__DOMAIN",
                "圖表解讀錯誤": "DI_GRAPH_INTERPRETATION_ERROR__GRAPH",
                "表格解讀錯誤": "DI_GRAPH_INTERPRETATION_ERROR__TABLE",
                "數學概念應用錯誤": "DI_CONCEPT_APPLICATION_ERROR__MATH",
                "數學計算錯誤": "DI_CALCULATION_ERROR__MATH",
                "閱讀理解詞彙困難": "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY",
                "閱讀理解語法困難": "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX",
                "圖表解讀困難": "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH",
                "表格解讀困難": "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE",
                "數學概念應用困難": "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH"
            },
            "MSR": {
                "閱讀理解詞彙錯誤": "DI_READING_COMPREHENSION_ERROR__VOCABULARY",
                "閱讀理解語法錯誤": "DI_READING_COMPREHENSION_ERROR__SYNTAX",
                "閱讀理解邏輯錯誤": "DI_READING_COMPREHENSION_ERROR__LOGIC",
                "閱讀理解領域錯誤": "DI_READING_COMPREHENSION_ERROR__DOMAIN",
                "圖表解讀錯誤": "DI_GRAPH_INTERPRETATION_ERROR__GRAPH",
                "表格解讀錯誤": "DI_GRAPH_INTERPRETATION_ERROR__TABLE",
                "數學概念應用錯誤": "DI_CONCEPT_APPLICATION_ERROR__MATH",
                "非數學邏輯推理錯誤": "DI_LOGICAL_REASONING_ERROR__NON_MATH",
                "數學計算錯誤": "DI_CALCULATION_ERROR__MATH",
                "閱讀理解詞彙困難": "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY",
                "閱讀理解語法困難": "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX",
                "閱讀理解邏輯困難": "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC",
                "閱讀理解領域困難": "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN",
                "多源整合困難": "DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION",
                "圖表解讀困難": "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH",
                "表格解讀困難": "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE",
                "數學概念應用困難": "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH",
                "非數學邏輯推理困難": "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH",
                "數學計算困難": "DI_CALCULATION_DIFFICULTY__MATH",
                "基礎掌握不穩定": "DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE"
            },
            "PS": {
                "閱讀理解錯誤": "Q_READING_COMPREHENSION_ERROR",
                "概念應用錯誤": "Q_CONCEPT_APPLICATION_ERROR",
                "計算錯誤": "Q_CALCULATION_ERROR",
                "閱讀理解困難": "Q_READING_COMPREHENSION_DIFFICULTY",
                "概念應用困難": "Q_CONCEPT_APPLICATION_DIFFICULTY",
                "計算困難": "Q_CALCULATION_DIFFICULTY",
                "基礎掌握不穩定": "Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE"
            },
            "RC": {
                # ERROR types
                "閱讀理解詞彙錯誤": "RC_READING_COMPREHENSION_ERROR_VOCAB",
                "長難句分析錯誤": "RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS",
                "文章結構理解錯誤": "RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE",
                "關鍵信息定位理解錯誤": "RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING",
                "問題焦點理解錯誤": "RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT",
                "定位技巧錯誤": "RC_LOCATION_SKILL_ERROR_LOCATION",
                "推理錯誤": "RC_REASONING_ERROR_INFERENCE",
                "選項分析詞彙錯誤": "RC_CHOICE_ANALYSIS_ERROR_VOCAB",
                "選項分析語法錯誤": "RC_CHOICE_ANALYSIS_ERROR_SYNTAX",
                "選項分析邏輯錯誤": "RC_CHOICE_ANALYSIS_ERROR_LOGIC",
                "選項分析領域錯誤": "RC_CHOICE_ANALYSIS_ERROR_DOMAIN",
                "選項相關性判斷錯誤": "RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT",
                "強干擾選項混淆錯誤": "RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION",
                "特定題型處理方法錯誤": "RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING",
                # DIFFICULTY types
                "詞彙瓶頸困難": "RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK",
                "長難句分析困難": "RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS",
                "文章結構把握不清困難": "RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR",
                "特定領域背景知識缺乏困難": "RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK",
                "思維阻塞困難": "RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED",
                "問題焦點把握困難": "RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP",
                "問題理解思維阻塞困難": "RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED",
                "定位技巧效率低困難": "RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY",
                "推理速度慢困難": "RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW",
                "選項分析詞彙困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB",
                "選項分析語法困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX",
                "選項分析邏輯困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC",
                "選項分析領域困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN",
                "選項相關性判斷困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT", # Example JSON used this
                "強干擾選項分析困難": "RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS"
            },
            "TPA": {
                "閱讀理解詞彙錯誤": "DI_READING_COMPREHENSION_ERROR__VOCABULARY",
                "閱讀理解語法錯誤": "DI_READING_COMPREHENSION_ERROR__SYNTAX",
                "閱讀理解邏輯錯誤": "DI_READING_COMPREHENSION_ERROR__LOGIC",
                "閱讀理解領域錯誤": "DI_READING_COMPREHENSION_ERROR__DOMAIN",
                "數學概念應用錯誤": "DI_CONCEPT_APPLICATION_ERROR__MATH",
                "非數學邏輯推理錯誤": "DI_LOGICAL_REASONING_ERROR__NON_MATH",
                "數學計算錯誤": "DI_CALCULATION_ERROR__MATH",
                "閱讀理解詞彙困難": "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY",
                "閱讀理解語法困難": "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX",
                "閱讀理解邏輯困難": "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC",
                "閱讀理解領域困難": "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN",
                "閱讀理解思維阻塞困難": "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED",
                "數學概念應用困難": "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH",
                "非數學邏輯推理困難": "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH",
                "數學計算困難": "DI_CALCULATION_DIFFICULTY__MATH"
            }
        }


    def route_gmat_issue(self, category: str, error_code: str) -> Dict[str, List[str]]:
        """
        Routes GMAT issues to appropriate training commands based on category and error code.
        (此方法文檔不變)
        """
        if category not in self.route_table:
            return {
                "commands": [],
                "error": f"Invalid category '{category}'. Valid categories are: {', '.join(self.route_table.keys())}"
            }
        
        commands = self.route_table.get(category, {}).get(error_code, [])
        
        if not commands:
            available_codes = list(self.route_table[category].keys())
            return {
                "commands": [],
                "error": f"Error code '{error_code}' not found in category '{category}'. Available codes: {available_codes[:5]}..."
            }
        
        return {"commands": commands}

    def get_command_details(self, command_name: str) -> Optional[CommandDetail]: # 修改方法名和返回類型
        """
        Get the details (description and usage occasion) for a specific command.
        
        :param command_name: Name of the command
        :return: Dictionary with description and usage_occasion of the command or None if not found
        """
        return self.command_details.get(command_name)

    def get_commands_with_descriptions(self, category: str, error_code: str) -> Dict: # 返回類型可以更精確
        """
        Get commands with their descriptions and usage occasions for a specific error code.
        
        :param category: GMAT category (CR / DS / GT / MSR / PS / RC / TPA)
        :param error_code: GMAT error code identifying the specific issue
        :return: Dictionary containing commands, their descriptions, and usage occasions
        """
        result = self.route_gmat_issue(category, error_code)
        
        if "error" in result:
            return result
        
        commands_with_details: List[FormattedCommand] = []
        for command_name in result["commands"]:
            details = self.get_command_details(command_name)
            if details:
                commands_with_details.append({
                    "command": command_name,
                    "description": details["description"],
                    "usage_occasion": details["usage_occasion"]
                })
            else: # Fallback if a command is in route_table but not in command_details (should not happen ideally)
                commands_with_details.append({
                    "command": command_name,
                    "description": "描述暫未提供",
                    "usage_occasion": "使用時機暫未提供"
                })
        
        return {
            "commands": result["commands"], # 原始指令列表仍然保留
            "commands_with_descriptions": commands_with_details # 修改此處的key名以反映內容變化，或保持原樣但告知LLM新結構
                                                              # 為了最小化prompt修改，我將保持 "commands_with_descriptions"
                                                              # 但其內部結構已改變
        }

    def get_available_categories(self) -> List[str]:
        return list(self.route_table.keys())

    def get_error_codes_for_category(self, category: str) -> List[str]:
        if category not in self.route_table:
            return []
        return list(self.route_table[category].keys())

    def get_all_commands(self) -> List[str]:
        return list(self.command_details.keys()) # 從 command_details 獲取

    def get_error_codes_mapping(self, category: str = None) -> Dict:
        if category:
            return self.error_codes_mapping_dict.get(category, {})
        return self.error_codes_mapping_dict