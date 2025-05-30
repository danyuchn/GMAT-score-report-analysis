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

## DI Diagnosis i18n Implementation Status (2025-01-28)

**Status: COMPLETED ✅**

Successfully migrated DI diagnostic modules from custom translation system to unified i18n system:

### Implementation Summary:
1. **Translation Keys Added**: ~100+ DI translation keys added to both zh_TW.py and en.py
2. **Files Updated**: All DI module files converted to use `from gmat_diagnosis_app.i18n import translate as t`
3. **Constant Migration**: Replaced INVALID_DATA_TAG_DI with i18n key 'di_invalid_data_tag'
4. **Functionality Verified**: All files compile successfully and i18n translations work correctly

### Files Modified:
- `main.py`: Updated imports and error messages
- `report_generation.py`: Converted all hardcoded Chinese text to translation keys
- `ai_prompts.py`: Updated AI tool recommendations and error messages
- `utils.py`: Updated difficulty grading function
- `chapter_logic.py`: Replaced _translate_di calls with t() function calls
- `constants.py`: Removed hardcoded constants, now uses i18n keys
- `zh_TW.py` & `en.py`: Added comprehensive DI translations

### Technical Approach:
- Followed exact same pattern as V/Q modules
- Maintained all existing functionality while enabling bilingual support
- Real-time language switching capability via session state
- Consistent translation key naming convention

**Result**: DI diagnostic report now fully supports bilingual output with unified i18n system, matching V/Q module implementation patterns.

--- 