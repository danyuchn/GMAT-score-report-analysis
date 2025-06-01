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
            "Questions You Did Wrong": {
                "description": "使用者提供做錯的題目，我將用高中生易懂的方式解釋解題步驟與答案，幫助你理解問題。最適合觀念真正不懂的各類題目。",
                "usage_occasion": "當你做錯題目，需要在事後檢討時確實理解正確解法、考點、選項的正確與錯誤原因時。"
            },
            "You Did Right But Slowly": {
                "description": "使用者提供雖然做對但耗時過長的題目，我將提供2-3分鐘內快速解題的捷徑。我會引導你先閱讀問題，識別解鎖問題的關鍵要素，然後判斷文本中哪些部分是相關信息，哪些不是，最後指出使用預寫策略還是排除策略來回答問題。每個步驟都包含清晰的提示，引導至下一步，並遵循線性的單向思維過程。",
                "usage_occasion": "當你題目雖然做對但解題速度過慢，希望在事後事後檢討時找到更快捷徑，且這個捷徑是實戰上具體可操作、非AI思維而是貼近人類單線思維。"
            },
            "Passages You Failed to Organize": {
                "description": "使用者提供一篇難以組織的文章，我將為其創建邏輯簡圖，幫助你視覺化資訊間的關係，從而更好地理解文章結構和邏輯。",
                "usage_occasion": "當你閱讀題目的文本，感到資訊難以組織在一起，對段落或論點之間的關係感到困惑，希望在事後檢討時徹底理清文本邏輯時。"
            },
            "Examine your Thoughts": {
                "description": "使用者提供口頭解題過程的錄音轉文字稿和題目文本，我將分析你的解題思路，找出其中的錯誤和可以改進的地方，幫助你事後檢討時可以針對思維盲點進行改進。",
                "usage_occasion": "當你學會了新的解題方法，且在解題過程中有錄音紀錄下思考過程，就可以在檢討中深入了解自己解題過程中的盲點或低效環節。"
            },
            "CR-BF: Demo Thoughts": {
                "description": "使用者提供Boldface題目，我將扮演AI助教，使用比較選項差異的特殊思路解決Boldface題型。",
                "usage_occasion": "當你Boldface題目做錯或做題速度過慢，需要學習如何用「比較差異法」解決Boldface題型時。"
            },
            "Understand Logical Terms": {
                "description": "使用者提供五個答案選項，我將解釋其中每個邏輯抽象術語的含義，幫助你理解選項的確切意思。",
                "usage_occasion": "當你對V/DI題目的選項中出現的邏輯抽象術語感到困惑而導致有理解障礙，希望在事後檢討時徹底理清其邏輯含義時。"
            },
            "Rewrite Passage into Complex Sentences": {
                "description": "使用者給我一篇文章，我會保留原意，把它改寫成用詞較難、句子較長、語氣較正式的英文版本，並另外一個簡單易懂的白話文版本。簡單說明改寫用了哪些抽象詞和複雜句型。",
                "usage_occasion": "當你的閱讀障礙是來自「句構複雜」，希望在平常練習題目或閱讀文章時一併提升對複雜長句的理解能力時。"
            },
            "Review Distractor (Trap Choices)": {
                "description": "使用者提供一個GMAT題目和最後二選一的選項組（正確/混淆選項），我會使用類比舉例協助你理解背後隱藏的陷阱邏輯，以及創造類似邏輯的題目供你練習。",
                "usage_occasion": "當你對某個題目的選項特別糾結，尤其是搞不清楚為什麼自己選的錯誤選項不對或正確選項為什麼對，或者是害怕下次考試又會出現類似陷阱時。"
            },
            "Classify This Question": { # CR/TPA/MSR/RC/PS/DS 皆可能
                "description": "使用者提供一串問題紀錄，如果是CR或TPA問題，我將判斷其題型類別。CR/TPA分為分析、建構、評論、計畫四類；RC/MSR分為主旨、支持、推論、評估、應用等類；PS/DS則依數學概念分類。我會進行兩次判斷確保準確性，並提供統計表格幫助你找出弱點題型。",
                "usage_occasion": "當你手上有了過去做題的錯題或者障礙題紀錄，想進一步了解自己在哪類特定分類題型上較弱，以便進行針對性練習時。"
            },
            "Create Variant Question": { # CR/DS/PS/RC/TPA 皆可能
                "description": "使用者提供一個原始問題，我將設計一個變體問題，讓你可以練習使用相同的解題方法。這個變體問題會有新的故事情境，但解題邏輯跟考點與原問題高度相似。",
                "usage_occasion": "當你剛檢討完一道題目，不確定自己會了沒有，想透過相似題目鞏固理解應用，以避免未來再犯同樣錯誤時。"
            },
            "Boldface Interactive Tutor": {
                "description": "使用者提供CR boldface問題及其官方答案和用[]標記的粗體部分。我將扮演GMAT Boldface互動導師，透過『你問 -> 使用者回答 -> 評估使用者回答並問下一個問題』的互動形式，逐步引導你分析問題。",
                "usage_occasion": "當你CR Boldface題目跟句子邏輯關係分析是弱項，需要一步一步進行深入的互動式學習和分析訓練時。"
            },
            "Logical Chain Builder": {
                "description": "使用者給我一段CR文章和邏輯鏈的起點終點，我幫你畫出簡化邏輯鏈，包含隱藏假設。用 -> (因果), + (並列), () (假設) 標示。",
                "usage_occasion": "當你做CR Assumption, Strengthen, Weaken, Evaluate等題型時，感覺文章論證繞來繞去，想快速看清楚從A到B是怎麼推的，中間藏了哪些沒明說的假設；或者是自己在做邏輯鏈推導時總是推導錯誤，無法預測正確答案時。"
            },
            "Identify Core Issue": {
                "description": "使用者給我一段CR的題幹文章，我把它核心問題變成「是不是這樣？」的問句，再給你一個不同故事但邏輯一樣的類比題讓你練習判斷核心。最後我會給你回饋。",
                "usage_occasion": "當你做CR題時，常常抓不準題目到底在吵什麼，預想思考的切入點是什麼，以及第一輪篩選常常把正確答案視作無關選項排除時。這個工具能幫你練習快速識別文章的真正辯論焦點。"
            },
            "Role-Immersion Trainer": {
                "description": "使用者給我一段CR題幹文章，我找出影響題目主題的最關鍵角色，然後讓你選這是「推論題」還是「解釋題」。接著我會代入該角色的立場，教使用者怎麼用「人設法」找破題切入點跟預想。",
                "usage_occasion": "當你做CR的Argument Constrcution題目時，如果使用「人設法」預想總是有困難，或者是第一輪篩選常常把正確答案視作「推不出」排除時。這個工具可以幫助你練習「人設法」的直觀思維。"
            },
            "Explain Textbook": { # CR/DS/GT/MSR/PS/RC/TPA 皆可能
                "description": "使用者給我來自教科書的內容（貼上文字或上傳圖片），我會用相對簡單的方式解釋，另外舉個例子協助你理解，還會幫你設計隨堂測驗以加深記憶。",
                "usage_occasion": "當你看GMAT教材（例如OG解釋、曼哈頓講義、GWD解析）時，遇到看不懂的專有名詞、解題策略或某個觀念，這個工具能淺顯易懂地解釋給你聽，並透過例子和測驗確保你真的懂了，而不只是死記硬背。"
            },
            "Train Your Close Reading Skill": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者給我一小段文章（CR/TPA篇幅，80-120字），我一句一句請你說出你的理解，並且透過逐句拆解和詮釋，引導你修正誤讀的地方，確保你理解每句話的核心意思，最後再把你的理解串成通順的段落。",
                "usage_occasion": "當你閱讀GMAT文章，常常覺得句子看過去了但意思沒進腦子，或者對句子的意思常常理解零碎或誤讀時。"
            },
            "Train Reading for Specific Domain": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者選一個你害怕的文章故事領域（如生物學、考古學），我給你一篇該領域的GMAT風格文章讓你讀和摘要，然後我會給你詳細的回饋與三道練習題。",
                "usage_occasion": "當你發現自己特別害怕或不擅長閱讀某一類GMAT文章，希望加強對特定領域文本的閱讀理解能力時。"
            },
            "Memorizing Vocabularies": { # CR/MSR/RC/TPA 皆可能
                "description": "使用者給我單詞字，我做成帶長難例句的單詞表，詳細解釋你不熟的詞，再用這些詞寫成GMAT風格文章讓你練習閱讀和摘要，最後出題考你。",
                "usage_occasion": "當你的閱讀障礙原因主要來自單字儲備量缺乏，需要補充單字，但是傳統的背單字方法對你來說卻枯燥乏味，或者背了就忘，不知道怎麼養成長久記憶時。"
            },
            # DS Commands
            "Learn Math Concepts": {
                "description": "你給我一道（DS/PS/TPA/GT）數學題，我告訴你這題想考你哪些數學觀念。",
                "usage_occasion": "當你做DS或PS題目時，常常不知道題目到底在考哪個數學知識點，或者雖然知道考點但理解不夠深入，導致無法正確解題時。"
            },
            "Identify Features for Applying a Specific Solution": { # DS/GT/MSR/PS/TPA 皆可能
                "description": "你給我一個解題方法，我告訴你未來看到哪些題目有特定特徵時可以使用同一個方法解題。",
                "usage_occasion": "當數學同樣的觀念反覆做錯，感覺好像在某一道題目的檢討並沒有讓能力完整傳遞到同類型的下一道題時。"
            },
            "Finding Similar Questions in Set": { # DS/PS 皆可能
                "description": "你給我一個題庫和一個你曾經做錯過的題，我幫你從題庫裡找出考類似觀念的題目，讓你針對性地練習。",
                "usage_occasion": "當你訂正完一個數學錯題，理解了考點和解法後，想馬上找些類似的題目來鞏固練習。或者是當你手上有大量題目卻怕自己寫不完、練習不集中時。"
            },
            "Convert to Real-Context": { # DS/PS 皆可能
                "description": "你給我GMAT數學題，我把它變成一個有生活情境的英文應用題，數字不變。",
                "usage_occasion": "當你的成績單中顯示顯示數學REAL題表現較弱，或者是數學相關的題目有文字理解錯誤或障礙，需要多加練習應用題時。"
            },
            # GT Commands  
            "Sentence Cracker": { # GT/MSR 皆可能
                "description": "你給我一個難句，我先簡化它，再根據你的困難點（單字、領域或句型）詳細解釋，拓展相關單詞、解析句型、提供類似句練習。",
                "usage_occasion": "當你的閱讀障礙是來自「單詞」「領域」「句型」，且在平常練習題目時遇到看不懂的句子時。"
            },
            # MSR Commands
            "Customize Your Preferred Problem-Solving Process": {
                "description": "你告訴我你習慣的MSR解題步驟以及一組指定的題目，我按你的步驟演示一遍如何使用指定步驟解題，並指出如何才能讓解題更有效率。",
                "usage_occasion": "當你在做MSR時，面對多個信息來源（文字、圖表、表格），會有手忙腳亂、整合混亂的障礙時。"
            },
            "Enhance Reading Speed": { # MSR/RC/TPA 皆可能
                "description": "你給我句子，我幫你把它切成一塊塊有意義的部分，讓你更快看懂句子結構。",
                "usage_occasion": "當你苦於閱讀速度無法提升，希望能夠讓自己不是一個一個字看，而是一組一組字看，進而培養閱讀節奏感時。"
            },
            # PS Commands
            "Rewrite passage into compressed sentences": {
                "description": "你給我PS題目裡難懂的句子，我幫你把它改寫得更簡潔或拆解分析，讓你更容易理解題意。",
                "usage_occasion": "當你做REAL類型的數學題有文字閱讀理解錯誤或障礙時。明明題目本身不難，但文字描述特別繞口、句子特別長，或者用了一些不常見的表達方式，導致你看不懂題目在問什麼時。"
            },
            # RC Commands
            "Rewrite Passage into GMAT Style": {
                "description": "你給我一篇學術文章，我把它改寫成GMAT RC那種風格的文章。",
                "usage_occasion": "當你的閱讀基礎能力有障礙，希望在閱讀訓練時所使用的文章素材具有GMAT等級的寫作水平，以及加強練習真實度時。"
            },
            "Preparatory Answer Training": {
                "description": "你給我題目和答案，先說說你看了題目後的初步想法。我會比較你的想法和正確答案，給你打分和改進建議。",
                "usage_occasion": "當你常常第一輪就排除掉RC的正確選項，或者擬答出現障礙，無法推理時。"
            },
            "Interactively Understand a Passage": {
                "description": "你給我RC文章，我會問你一系列問題，一步步帶你分析文章的主旨、論點和結構，並給你回饋和總結。",
                "usage_occasion": "當你讀完一篇GMAT RC文章後，感覺似懂非懂，對文章的整體架構、各段落功能、主要論點和支持細節的掌握不夠清晰時。"
            },
            "Train Predictive & Active Reading": {
                "description": "你給我文章，我一句一句念，每念一句就讓你猜下一句會說什麼，訓練你主動預測文章走向。",
                "usage_occasion": "當你閱讀GMAT文章時，常常是被動接收信息，讀到哪算哪，缺乏對文章後續發展的預期，導致閱讀效率不高、容易讀到後面忘了前面，對文章整體篇章架構掌握不清時。"
            }
        }
        # (route_table 和 error_codes_mapping 保持不變)
        self.route_table: Dict[str, Dict[str, List[str]]] = {
            # ... (您的 route_table 內容不變) ...
            # ------------------------  CR  ------------------------
            "CR": {
                "CR_STEM_UNDERSTANDING_ERROR_VOCAB": [
                    "Questions You Did Wrong", "Understand Logical Terms", "Memorizing Vocabularies"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_SYNTAX": [
                    "Questions You Did Wrong", "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_LOGIC": [
                    "Questions You Did Wrong", "Passages You Failed to Organize", "Logical Chain Builder", "Train Your Close Reading Skill"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_DOMAIN": [
                    "Questions You Did Wrong", "Train Reading for Specific Domain"
                ],
                "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP": [
                    "Questions You Did Wrong", "Role-Immersion Trainer"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_VOCAB": [
                    "Questions You Did Wrong", "Understand Logical Terms", "Memorizing Vocabularies"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX": [
                    "Questions You Did Wrong", "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill"
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_LOGIC": [
                    "Questions You Did Wrong", "Create Variant Question", "Train Your Close Reading Skill"
                ],
                "CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP": [
                    "Questions You Did Wrong", "Passages You Failed to Organize", "Examine your Thoughts",
                    "Create Variant Question", "Logical Chain Builder"
                ],
                "CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Understand Logical Terms", "Create Variant Question"
                ],
                "CR_REASONING_ERROR_PREDICTION_DIRECTION": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Create Variant Question",
                    "Logical Chain Builder", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Create Variant Question",
                    "Identify Core Issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Create Variant Question",
                    "Identify Core Issue", "Role-Immersion Trainer"
                ],
                "CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE": [
                    "Questions You Did Wrong", "CR-BF: Demo Thoughts", "Classify This Question", "Create Variant Question",
                    "Boldface Interactive Tutor", "Logical Chain Builder", "Role-Immersion Trainer", "Explain Textbook"
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC": [
                    "You Did Right But Slowly", "Logical Chain Builder", "Train Your Close Reading Skill"
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC": [
                    "You Did Right But Slowly", "Train Your Close Reading Skill"
                ],
                "CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING": [
                    "You Did Right But Slowly", "Understand Logical Terms"
                ],
                "CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING": [
                    "You Did Right But Slowly", "Create Variant Question", "Logical Chain Builder",
                    "Role-Immersion Trainer", "Identify Core Issue"
                ],
                "CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION": [
                    "You Did Right But Slowly", "Create Variant Question", "Identify Core Issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT": [
                    "You Did Right But Slowly", "Create Variant Question", "Identify Core Issue", "Role-Immersion Trainer"
                ],
                "CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS": [
                    "You Did Right But Slowly", "Review Distractor (Trap Choices)", "Create Variant Question"
                ],
                "CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION": [
                    "Examine your Thoughts", "Review Distractor (Trap Choices)", "Create Variant Question"
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB": [
                    "You Did Right But Slowly","Understand Logical Terms", "Memorizing Vocabularies" # Added You did right but slowly as per example, assuming vocab can also be a speed issue
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB": [
                    "You Did Right But Slowly","Understand Logical Terms", "Memorizing Vocabularies" # Added You did right but slowly
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX": [
                    "You Did Right But Slowly","Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill" # Added You did right but slowly
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX": [
                    "You Did Right But Slowly","Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill" # Added You did right but slowly
                ],
                "CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN": [
                    "You Did Right But Slowly","Train Reading for Specific Domain" # Added You did right but slowly
                ],
                "CR_CHOICE_UNDERSTANDING_ERROR_DOMAIN": [ # This is an ERROR, not DIFFICULTY, so "You did right but slowly" might not fit unless specified. Kept original.
                    "Questions You Did Wrong","Train Reading for Specific Domain"
                ],
                "CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN": [
                    "You Did Right But Slowly","Train Reading for Specific Domain" # Added You did right but slowly
                ],
            },
            "DS": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": ["Questions You Did Wrong"],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions You Did Wrong", "Rewrite Passage into Complex Sentences", "Convert to Real-Context"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions You Did Wrong", "Convert to Real-Context"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": ["Questions You Did Wrong"],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Learn Math Concepts", "Identify Features for Applying a Specific Solution",
                    "Create Variant Question", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook" # Changed Create Various Questions to Create variant question for consistency
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Create Variant Question", "Finding Similar Questions in Set" # Changed Create Various Questions to Create variant question
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You Did Right But Slowly","Rewrite Passage into Complex Sentences", "Convert to Real-Context" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You Did Right But Slowly", "Convert to Real-Context"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly", "Learn Math Concepts", "Identify Features for Applying a Specific Solution",
                    "Create Variant Question", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook" # Changed Create Various Questions to Create variant question
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly", "Create Variant Question", "Finding Similar Questions in Set" # Changed Create Various Questions to Create variant question
                ],
            },
            "GT": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions You Did Wrong", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions You Did Wrong", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": ["Questions You Did Wrong"],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": ["Questions You Did Wrong"],
                "DI_GRAPH_INTERPRETATION_ERROR__GRAPH": [
                    "Questions You Did Wrong", "Learn Math Concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify Features for Applying a Specific Solution", "Explain Textbook"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions You Did Wrong", "Learn Math Concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify Features for Applying a Specific Solution", "Explain Textbook"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Learn Math Concepts", # Changed Learn Math Concept to Learn math concepts
                    "Identify Features for Applying a Specific Solution", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions You Did Wrong"],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", "Explain Textbook" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You Did Right But Slowly","Sentence Cracker" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You Did Right But Slowly","Sentence Cracker" # Added You did right but slowly
                ],
            },
            "MSR": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions You Did Wrong", "Memorizing Vocabularies", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions You Did Wrong", "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions You Did Wrong", "Train Your Close Reading Skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions You Did Wrong", "Train Reading for Specific Domain"
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__GRAPH": [
                    "Questions You Did Wrong", "Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_GRAPH_INTERPRETATION_ERROR__TABLE": [
                    "Questions You Did Wrong", "Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions You Did Wrong", "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "DI_CALCULATION_ERROR__MATH": ["Questions You Did Wrong"],
                "DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION": [
                    "You Did Right But Slowly","Passages You Failed to Organize", "Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You Did Right But Slowly","Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill", "Enhance Reading Speed", "Sentence Cracker" # Added You did right but slowly
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You Did Right But Slowly","Customize Your Preferred Problem-Solving Process",
                    "Train Your Close Reading Skill", "Enhance Reading Speed" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly","Learn Math Concepts", "Identify Features for Applying a Specific Solution", # Corrected casing
                    "Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You Did Right But Slowly","Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly","Customize Your Preferred Problem-Solving Process" # Added You did right but slowly
                ],
                "DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE": ["Classify This Question"], # Assuming "You did right but slowly" isn't always implied by SFE
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": ["You Did Right But Slowly","Train Reading for Specific Domain"], # Added You did right but slowly
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You Did Right But Slowly","Memorizing Vocabularies", "Sentence Cracker" # Added You did right but slowly
                ],
            },
             "PS": {
                "Q_READING_COMPREHENSION_ERROR": [
                    "Questions You Did Wrong", "Rewrite passage into compressed sentences", "Convert to Real-Context", "Sentence Cracker"
                ],
                "Q_CONCEPT_APPLICATION_ERROR": [
                    "Questions You Did Wrong", "Learn Math Concepts", "Identify Features for Applying a Specific Solution",
                    "Create Variant Question", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook"
                ],
                "Q_CALCULATION_ERROR": [
                    "Questions You Did Wrong", "Create Variant Question", "Finding Similar Questions in Set"
                ],
                "Q_READING_COMPREHENSION_DIFFICULTY": [
                    "You Did Right But Slowly","Rewrite passage into compressed sentences", "Convert to Real-Context", "Sentence Cracker" # Added You did right but slowly
                ],
                "Q_CONCEPT_APPLICATION_DIFFICULTY": [
                    "You Did Right But Slowly", "Learn Math Concepts", "Identify Features for Applying a Specific Solution",
                    "Create Variant Question", "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook"
                ],
                "Q_CALCULATION_DIFFICULTY": [
                    "You Did Right But Slowly", "Create Variant Question", "Finding Similar Questions in Set"
                ],
                "Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE": [
                    "You Did Right But Slowly", "Classify This Question"
                ],
            },
            "RC": {
                "RC_READING_COMPREHENSION_ERROR_VOCAB": [
                    "Questions You Did Wrong",  "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "Questions You Did Wrong",  "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill"
                ],
                "RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE": [
                    "Questions You Did Wrong", "Passages You Failed to Organize", 
                    "Create Variant Question", "Interactively Understand a Passage",
                    "Train Predictive & Active Reading", "Explain Textbook"
                ],
                "RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING": [
                    "Questions You Did Wrong", "Passages You Failed to Organize", 
                    "Create Variant Question", "Explain Textbook", "Train Your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT": [
                    "Questions You Did Wrong", "Preparatory Answer Training",
                    "Create Variant Question", "Classify This Question", "Explain Textbook", "Train Your Close Reading Skill" # Changed Classify This Question to Classify this question
                ],
                "RC_LOCATION_SKILL_ERROR_LOCATION": [
                    "Questions You Did Wrong", "Preparatory Answer Training",
                    "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_REASONING_ERROR_INFERENCE": [
                    "Questions You Did Wrong", "Examine your Thoughts", 
                    "Preparatory Answer Training", "Create Variant Question", "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_ERROR_VOCAB": [
                    "Questions You Did Wrong", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_SYNTAX": [
                    "Questions You Did Wrong", "Rewrite Passage into Complex Sentences"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_LOGIC": [
                    "Questions You Did Wrong", "Train Your Close Reading Skill"
                ],
                "RC_CHOICE_ANALYSIS_ERROR_DOMAIN": [
                    "Questions You Did Wrong", "Train Reading for Specific Domain" # Added "Train Reading for Specific Domain" based on difficulty counterpart
                ],
                "RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT": [
                    "Questions You Did Wrong",  "Create Variant Question",
                    "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION": [
                    "Questions You Did Wrong",  "Create Variant Question",
                    "Classify This Question", "Review Distractor (Trap Choices)", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING": [
                    "Questions You Did Wrong", "Create Variant Question", "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK": [
                    "You Did Right But Slowly", "Memorizing Vocabularies"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS": [
                    "You Did Right But Slowly", "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill", "Enhance Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR": [
                    "You Did Right But Slowly", "Passages You Failed to Organize", "Interactively Understand a Passage",
                    "Train Predictive & Active Reading", "Explain Textbook", "Enhance Reading Speed"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK": [
                    "You Did Right But Slowly", "Rewrite Passage into GMAT Style", "Train Reading for Specific Domain"
                ],
                "RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED": [
                    "You Did Right But Slowly"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP": [
                    "You Did Right But Slowly", "Preparatory Answer Training", "Classify This Question", # Changed Classify This Question to Classify this question
                    "Explain Textbook", "Train Your Close Reading Skill"
                ],
                "RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED": [
                    "You Did Right But Slowly"
                ],
                "RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY": [
                    "You Did Right But Slowly", "Preparatory Answer Training", "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW": [
                    "You Did Right But Slowly", "Examine your Thoughts", "Preparatory Answer Training", "Explain Textbook"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB": [
                    "You Did Right But Slowly", "Memorizing Vocabularies"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX": [
                    "You Did Right But Slowly", "Rewrite Passage into Complex Sentences"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC": [
                    "You Did Right But Slowly", "Train Your Close Reading Skill"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN": [
                    "You Did Right But Slowly", "Train Reading for Specific Domain"
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT": [ # Provided example JSON used this error code
                    "You Did Right But Slowly", "Classify This Question", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
                "RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS": [
                    "You Did Right But Slowly", "Classify This Question", "Review Distractor (Trap Choices)", "Explain Textbook" # Changed Classify This Question to Classify this question
                ],
            },
             "TPA": {
                "DI_READING_COMPREHENSION_ERROR__VOCABULARY": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Understand Logical Terms", "Memorizing Vocabularies", "Sentence Cracker" # Changed Memorizing Vocabulary to Memorizing Vocabularies
                ],
                "DI_READING_COMPREHENSION_ERROR__SYNTAX": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Passages You Failed to Organize",
                    "Rewrite Passage into Complex Sentences", "Train Your Close Reading Skill", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_ERROR__LOGIC": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Passages You Failed to Organize",
                    "Review Distractor (Trap Choices)", "Classify This Question", "Train Your Close Reading Skill"
                ],
                "DI_READING_COMPREHENSION_ERROR__DOMAIN": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Train Reading for Specific Domain"
                ],
                "DI_CONCEPT_APPLICATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Learn Math Concepts",
                    "Identify Features for Applying a Specific Solution", "Create Variant Question",
                    "Finding Similar Questions in Set", "Classify This Question", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_ERROR__NON_MATH": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Review Distractor (Trap Choices)", "Classify This Question", "Explain Textbook"
                ],
                "DI_CALCULATION_ERROR__MATH": [
                    "Questions You Did Wrong", "Examine your Thoughts", "Create Variant Question", "Finding Similar Questions in Set"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY": [
                    "You Did Right But Slowly", "Understand Logical Terms", "Memorizing Vocabularies", "Sentence Cracker" # Changed Memorizing Vocabulary to Memorizing Vocabularies
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX": [
                    "You Did Right But Slowly", "Passages You Failed to Organize", "Rewrite Passage into Complex Sentences",
                    "Train Your Close Reading Skill", "Enhance Reading Speed", "Sentence Cracker"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__LOGIC": [
                    "You Did Right But Slowly", "Passages You Failed to Organize", "Review Distractor (Trap Choices)",
                    "Train Your Close Reading Skill", "Enhance Reading Speed"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN": [
                    "You Did Right But Slowly", "Train Reading for Specific Domain"
                ],
                "DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED": [
                    "You Did Right But Slowly"
                ],
                "DI_CONCEPT_APPLICATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly", "Learn Math Concepts", "Identify Features for Applying a Specific Solution",
                    "Create Variant Question", "Finding Similar Questions in Set", "Explain Textbook"
                ],
                "DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH": [
                    "You Did Right But Slowly", "Review Distractor (Trap Choices)", "Explain Textbook"
                ],
                "DI_CALCULATION_DIFFICULTY__MATH": [
                    "You Did Right But Slowly", "Create Variant Question", "Finding Similar Questions in Set"
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