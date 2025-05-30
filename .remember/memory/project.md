# Project Memory - User Preferences and Rules

This file stores user preferences and custom rules for the GMAT Score Report Analysis project.

## Language Preferences
- Primary language: 繁體中文 (Traditional Chinese)
- Secondary language: English
- Comments in code: English
- Documentation: 繁體中文

## Code Style Preferences
- Python: PEP 8 style
- Function names: snake_case
- Class names: PascalCase
- Constants: UPPER_SNAKE_CASE
- Import style: individual imports preferred
- Comments: English with descriptive naming

## Translation System
- Use i18n system for all user-facing text
- Support Traditional Chinese and English
- Keep original logic intact when implementing translations
- Preserve data flow and function signatures
- Language switching implemented in sidebar with real-time updates
- UI elements are fully translatable via the i18n system

## GMAT Diagnosis Specific Rules
- Never modify diagnostic logic or numerical values
- Preserve all function call signatures
- Keep data validation intact
- Maintain error handling patterns

## I18n Implementation Details
- Language selector placed in sidebar expander at the top
- Session state tracks current language and language changes
- Translation system supports both Traditional Chinese and English
- Real-time language switching with st.rerun() for immediate updates
- All UI text keys stored in translation dictionaries in /i18n/translations/
- Translation function imported as 'translate' throughout the application

## Recent Implementations
- ✅ I18n bilingual system setup completed
- ✅ Language switching button implemented in sidebar
- ✅ Translation system integrated into main UI elements
- ✅ Session state management for language preferences added
- ✅ Real-time language switching functionality working
- ✅ Q Diagnosis module i18n implementation completed
  - All hardcoded Chinese text in user-facing functions replaced with translation calls
  - Translation keys added for reporting, recommendations, AI prompts, and utility functions
  - Full bilingual support for Q section diagnostic reports and recommendations
  - grade_difficulty_q() function converted to use translation system
  - AI prompt fallback messages now support bilingual switching
- ✅ V Diagnosis module i18n implementation completed (2025-01-28)
  - All hardcoded Chinese text converted to translation keys
  - V diagnostic parameters added to translation dictionaries (CR/RC specific)
  - All V modules updated: reporting.py, recommendations.py, main.py, ai_prompts.py
  - V skills translation support (Plan/Construct, Identify Stated Idea, etc.)
  - V report structure fully bilingual compatible
  - Consistent import pattern: from gmat_diagnosis_app.i18n import translate as t

## Q Diagnosis I18n Conversion Status
- ✅ reporting.py: All report sections and user messages converted
- ✅ utils.py: Difficulty labeling functions converted
- ✅ main.py: Error messages converted
- ✅ recommendations.py: Practice suggestions and skill labels converted
- ✅ ai_prompts.py: AI tool recommendations and fallback messages converted
- Translation coverage: Complete for all user-facing text in Q diagnosis module

## V Diagnosis I18n Conversion Status (2025-01-28)
- ✅ reporting.py: All report sections, time assessment, analysis text converted
- ✅ recommendations.py: Practice suggestions, skill exemptions, consolidation advice converted
- ✅ main.py: Error messages and diagnostic parameter translations converted
- ✅ ai_prompts.py: AI analysis messages, tag formatting, recommendations converted
- ✅ Translation keys added: ~100+ V-specific keys including CR/RC parameters
- ✅ V skills mapping: Plan/Construct → "計劃/構建", Identify Stated Idea → "識別明確觀點"
- Translation coverage: Complete for all user-facing text in V diagnosis module

--- 