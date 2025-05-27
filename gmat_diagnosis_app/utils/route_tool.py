"""
GMAT 診斷標籤路由工具模組

此模塊將診斷標籤路由到適當的訓練命令，基於 gmat_route_tool.py 的功能
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging


class DiagnosisRouterTool:
    def __init__(self):
        """初始化診斷路由工具"""
        
        # 命令描述映射表
        self.command_descriptions: Dict[str, str] = {
            "Questions you did wrong": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。",
            "You did right but slowly": "使用者提供雖然做對但耗時過長的題目 (CR或TPA非數學相關)，我將提供 N分鐘內快速解題的捷徑。我會引導你先閱讀問題，識別解鎖問題的關鍵要素，然後判斷文本中哪些部分是相關信息，哪些不是，最後指出使用預寫策略還是排除策略來回答問題。每個步驟都包含清晰的提示，引導至下一步，並遵循線性的單向思維過程。",
            "Passages you fail to organize": "使用者提供一篇難以組織的文章，我將為其創建一個心智圖（markdown格式，輸出在代碼塊中），幫助你視覺化資訊間的關係，從而更好地理解文章結構和 logic。",
            "Examine your thoughts": "使用者提供口頭解題過程的錄音轉文字稿和題目文本，我將分析你的解題思路，找出其中的錯誤和可以改進的地方，幫助你提升解題效率和準確性。",
            "CR-BF Demo Thoughts": "使用者提供Boldface題目，我將扮演AI助教，專門解決邏輯推理問題（例如BF題型）。我會遵循五大原則，逐步分析和回答問題，採用循環迭代的方法，每次專注於一個核心差異，並在每個循環中進行單一推斷，以排除選項，直到剩下一個為止。",
            "Understand Logical terms": "使用者提供五個答案選項，我將解釋其中每個 logic 術語的含義，幫助你理解選項的確切意思。",
            "Rewrite passage into complex sentences": "使用者提供一篇文章，我將保留其確切的核心含義，不任意增刪觀點、含義或細節，將其改寫成用詞艱深、風格抽象的版本。",
            "Review distractor": "使用者提供一個GMAT問題以及一個正確選項和一個錯誤選項。我會用繁體中文，以像對10歲小孩說話的語氣和風格，詳細解釋為什麼正確選項符合題目要求，以及為什麼錯誤選項不符合。",
            "Classify this question": "使用者提供CR或TPA非數學相關問題，我將判斷其屬於分析、建構、評論或計畫四大子類型中的哪一種，並進行兩次獨立判斷以確保一致性。",
            "Create variant question": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題 logic與原問題相似。",
            "Boldface Interactive Tutor": "使用者提供CR boldface問題及其官方答案和用[]標記的粗體部分。我將扮演GMAT Boldface互動導師，透過『你問 -> 使用者回答 -> 評估使用者回答並問下一個問題』的互動形式，逐步引導你分析問題。",
            "Logical Chain Builder": "使用者提供CR論證評估型文章，並指定邏輯鏈的起點和終點。我將以繁體中文構建一個簡化的邏輯鏈，直接關聯起點和終點，並包含必要的隱藏假設。",
            "Identify core issue": "使用者提供一篇GMAT CR文章，我會將其核心問題轉化為'是否'的形式，並創建具有相同邏輯結構但在不同情境下的類比場景。",
            "Role-Immersion Trainer": "使用者提供GMAT CR文章，我將首先確定文章中信息最直接影響的角色。接著，我會詢問你希望進行「推斷」還是「解釋」。",
            "Explain Textbook": "使用者提供教材的文字或截圖，我會用繁體中文並以中學生易懂的方式解釋概念，並提供三個例子。",
            "Train your close reading skill": "使用者提供短文（80-120字），我將扮演精讀教練，一次只呈現第一句話，請你理解。",
            "Train Reading for Specific Domain": "使用者指定一個特定領域，我將提供該領域內三個非常具體、狹窄但高度爭議性的主題，請你選擇其一。",
            "Memorizing Vocabularies": "使用者提供需要記憶的單字，我將為每個單字創建一個包含英文單字、中文意思、詞性和至少25字長（含至少兩子句及複雜結構如插入語、倒裝或省略）的例句的試算表。",
            # DS/PS Commands
            "Question you did wrong": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。",
            "Learn math concepts": "使用者提供一個數學問題，我將從出題者的角度思考，指出這個問題想要測試哪些具體的數學概念，幫助你理解題目背後的考點。",
            "Identify features for applying a specific solution": "使用者提供一個特定的解題方法，我將總結哪些題目陳述的特徵出現時，可以應用此解題方法，幫助你識別模式並有效應用方法。",
            "Create Various Questions": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題 logic與原問題相似。",
            "Finding Similar Questions in Set": "使用者提供一個題庫和一個之前做錯的樣本問題，我將從題庫中找出與樣本問題使用相似數學概念的題目，幫助你針對性練習。",
            "Convert to real context": "使用者提供GMAT數學選擇題（文字或圖片形式），我會將其轉換成一個包含真實情境和故事情節的英文應用題（30-50字），且不更改任何數值。",
            # RC Commands
            "Diagnostic Label List": "針對RC題目常見的錯誤類型進行分類與標註，協助釐清學生在閱讀理解過程中遇到的具體困難。",
            "Rewrite Passage into GMAT style": "使用者提供一篇學術文章，我將其改寫成250-400字的GMAT風格文章，適合受過教育的非專業讀者閱讀。",
            "Preparatory answer training": "使用者提供文章、問題和答案，我會先請你提供自己版本的答案或在閱讀選項前的思路。",
            "Interactive Understanding Passage": "使用者提供一篇GMAT RC文章，我將扮演 Dustin 的 GMAT RC 文章分析器，透過5-6個有組織的邏輯順序問題來引導你理解文章。",
            "Predictive and Active Reading": "使用者提供一篇文章，我將扮演預測文本導師。我會引用第一句話，請你猜測下一句會是什麼。",
            "Enhanced reading speed": "使用者提供句子，我將自動將其劃分成邏輯上有意義的區塊，每個區塊代表一個獨立的意義單元（如主語、時間範圍、因果關係、主要論點等），以助你更好地理解句子結構。",
            # GT/MSR/TPA共用的命令
            "Sentence cracker": "使用者提供一個難以理解的句子，我會先將其簡化到九年級學生能懂的程度。然後詢問你的困難點是領域特定詞彙、一般詞彙、複雜句型，還是綜合性的。",
            "Learn Math Concept": "使用者提供一個數學問題，我將從出題者的角度思考，指出這個問題想要測試哪些具體的數學概念，幫助你理解題目背後的考點。"
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
                ]
            },
            
            # PS路由表
            "PS": {
                "Q_READING_COMPREHENSION_ERROR": [
                    "Questions you did wrong", "Convert to real context", "Sentence cracker"
                ],
                "Q_CONCEPT_APPLICATION_ERROR": [
                    "Questions you did wrong", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook"
                ],
                "Q_CALCULATION_ERROR": [
                    "Questions you did wrong", "Create variant question", "Finding Similar Questions in Set"
                ],
                "Q_READING_COMPREHENSION_DIFFICULTY": [
                    "Convert to real context", "Sentence cracker"
                ],
                "Q_CONCEPT_APPLICATION_DIFFICULTY": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook"
                ],
                "Q_CALCULATION_DIFFICULTY": [
                    "You did right but slowly", "Create variant question", "Finding Similar Questions in Set"
                ],
                "Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE": [
                    "You did right but slowly", "Classify this question"
                ]
            },
            
            # RC路由表
            "RC": {
                "RC_READING_COMPREHENSION_ERROR_VOCAB": [
                    "Questions you did wrong", "Diagnostic Label List", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "Questions you did wrong", "Diagnostic Label List", "Rewrite passage into complex sentences", "Train your close reading skill"
                ],
                "RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE": [
                    "Questions you did wrong", "Passages you fail to organize", "Diagnostic Label List",
                    "Create variant question", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING": [
                    "Questions you did wrong", "Passages you fail to organize", "Diagnostic Label List",
                    "Create variant question", "Explain Textbook", "Train your close reading skill"
                ],
                "RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT": [
                    "Questions you did wrong", "Diagnostic Label List", "Preparatory answer training",
                    "Create variant question", "Classify this question", "Explain Textbook", "Train your close reading skill"
                ],
                "RC_LOCATION_SKILL_ERROR_LOCATION": [
                    "Questions you did wrong", "Diagnostic Label List", "Preparatory answer training",
                    "Classify this question", "Explain Textbook"
                ],
                "RC_REASONING_ERROR_INFERENCE": [
                    "Questions you did wrong", "Examine your thoughts", "Diagnostic Label List",
                    "Preparatory answer training", "Create variant question", "Classify this question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_VOCAB": [
                    "Questions you did wrong", "Diagnostic Label List", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_SYNTAX": [
                    "Questions you did wrong", "Diagnostic Label List", "Rewrite passage into complex sentences"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_LOGIC": [
                    "Questions you did wrong", "Diagnostic Label List", "Train your close reading skill"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_DOMAIN": [
                    "Questions you did wrong", "Diagnostic Label List"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT": [
                    "Questions you did wrong", "Diagnostic Label List", "Create variant question",
                    "Classify this question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION": [
                    "Questions you did wrong", "Diagnostic Label List", "Create variant question",
                    "Classify this question", "Review distractor", "Explain Textbook"
                ],
                "RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING": [
                    "Questions you did wrong", "Create variant question", "Classify this question", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK": [
                    "You did right but slowly", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "You did right but slowly", "Rewrite passage into complex sentences", "Train your close reading skill", "Enhanced reading speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR": [
                    "You did right but slowly", "Passages you fail to organize", "Interactive Understanding Passage",
                    "Predictive and Active Reading", "Explain Textbook", "Enhanced reading speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK": [
                    "You did right but slowly", "Rewrite Passage into GMAT style", "Train Reading for Specific Domain"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP": [
                    "You did right but slowly", "Preparatory answer training", "Classify this question",
                    "Explain Textbook", "Train your close reading skill"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY": [
                    "You did right but slowly", "Preparatory answer training", "Classify this question", "Explain Textbook"
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
                    "You did right but slowly", "Train your close reading skill"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN": [
                    "You did right but slowly", "Train Reading for Specific Domain"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT": [
                    "You did right but slowly", "Classify this question", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS": [
                    "You did right but slowly", "Classify this question", "Review distractor", "Explain Textbook"
                ]
            },
            
            # DS路由表
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
                    "Create Various Questions", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Question you did wrong", "Create Various Questions", "Finding Similar Questions in Set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "Rewrite passage into complex sentences", "Convert to real context"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly", "Convert to real context"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create Various Questions", "Finding Similar Questions in Set", "Classify this question", "Explain Textbook"
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
                    "Questions you did wrong", "Memorizing Vocabularies", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Rewrite passage into complex sentences", "Train your close reading skill", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions you did wrong", "Train your close reading skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions you did wrong", "Train Reading for Specific Domain"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__GRAPH": [
                    "Questions you did wrong", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Classify this question", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions you did wrong", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Classify this question", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Learn Math Concept", "Identify features for applying a specific solution",
                    "Classify this question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Classify this question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions you did wrong"],
                "DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION": [
                    "Passages you fail to organize"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "Rewrite passage into complex sentences", "Train your close reading skill", "Enhanced reading speed", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "Train your close reading skill", "Enhanced reading speed"
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "Learn Math Concept", "Identify features for applying a specific solution"
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "Learn Math Concept", "Identify features for applying a specific solution"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "Learn Math Concept", "Identify features for applying a specific solution"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [],
                "DI_CALCULATION_DIFFICULTY__MATH": [],
                "DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE": ["Classify this question"],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": ["Train Reading for Specific Domain"],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "Memorizing Vocabularies", "Sentence cracker"
                ]
            },
            
            # TPA路由表
            "TPA": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions you did wrong", "Examine your thoughts", "Understand Logical terms", "Memorizing Vocabularies", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions you did wrong", "Examine your thoughts", "Passages you fail to organize",
                    "Rewrite passage into complex sentences", "Train your close reading skill", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions you did wrong", "Examine your thoughts", "Passages you fail to organize",
                    "Review distractor", "Classify this question", "Train your close reading skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions you did wrong", "Examine your thoughts", "Train Reading for Specific Domain"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Learn math concepts",
                    "Identify features for applying a specific solution", "Create variant question",
                    "Finding Similar Questions in Set", "Classify this question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Review distractor", "Classify this question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Questions you did wrong", "Examine your thoughts", "Create variant question", "Finding Similar Questions in Set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You did right but slowly", "Understand Logical terms", "Memorizing Vocabularies", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You did right but slowly", "Passages you fail to organize", "Rewrite passage into complex sentences",
                    "Train your close reading skill", "Enhanced reading speed", "Sentence cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You did right but slowly", "Passages you fail to organize", "Review distractor",
                    "Train your close reading skill", "Enhanced reading speed"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": [
                    "You did right but slowly", "Train Reading for Specific Domain"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED": [
                    "You did right but slowly"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Learn math concepts", "Identify features for applying a specific solution",
                    "Create variant question", "Finding Similar Questions in Set", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You did right but slowly", "Review distractor", "Explain Textbook"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You did right but slowly", "Create variant question", "Finding Similar Questions in Set"
                ]
            }
        }

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
            tag (str): 診斷標籤
            subject (str): 科目（Q, V, DI）
            
        Returns:
            List[str]: 推薦的訓練命令列表
        """
        # 確定類別
        category = self.determine_category_from_tag(tag, subject)
        
        # 查找路由表
        if category in self.route_table:
            category_routes = self.route_table[category]
            
            # 嘗試精確匹配
            if tag in category_routes:
                return category_routes[tag]
            
            # 模糊匹配 (保留原有的模糊匹配功能)
            for route_key in category_routes:
                if self._fuzzy_match(tag, route_key):
                    return category_routes[route_key]
        
        # 如果沒有匹配到，返回通用建議
        return self._get_fallback_commands(category)

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

    def _get_fallback_commands(self, category: str) -> List[str]:
        """
        獲取備選命令
        
        Args:
            category (str): 類別
            
        Returns:
            List[str]: 備選命令列表
        """
        fallback_map = {
            "CR": ["Questions you did wrong", "Examine your thoughts"],
            "RC": ["Questions you did wrong", "Diagnostic Label List"],
            "PS": ["Questions you did wrong", "Learn math concepts"],
            "DS": ["Question you did wrong", "Learn math concepts"],
            "GT": ["Questions you did wrong", "Learn Math Concept"],
            "MSR": ["Questions you did wrong", "Train your close reading skill"],
            "TPA": ["Questions you did wrong", "Examine your thoughts"]
        }
        return fallback_map.get(category, ["Questions you did wrong"])

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
        
        # 生成建議
        recommendations = []
        already_recommended = set()
        
        # 按頻率排序處理標籤
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
            commands = self.route_diagnosis_tag(tag, subject)
            
            if commands:
                recommendation_text = f"**{tag}** (出現{count}次):\n"
                tools_added = False
                
                for command in commands:
                    if command not in already_recommended:
                        description = self.command_descriptions.get(command, "描述暫未提供")
                        recommendation_text += f"- **{command}**: {description}\n"
                        already_recommended.add(command)
                        tools_added = True
                
                if tools_added:
                    recommendations.append(recommendation_text)
        
        if not recommendations:
            return f"未找到特定匹配的工具建議。建議參考GMAT官方指南中的{subject}科相關練習和策略。"
        
        return "\n".join(recommendations[:10])  # 最多顯示10條建議

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