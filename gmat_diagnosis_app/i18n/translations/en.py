"""
English (en) translations for GMAT Diagnosis App

This file contains all English translations as faithful translations of the Chinese versions.
"""

TRANSLATIONS = {
    # UI Interface Translations
    'analysis_settings': "Analysis Settings",
    'language_selection': "Language / 語言",
    'select_language': "Select Language / 選擇語言:",
    'language_updated': "Language updated!",
    'sample_data': "Sample Data",
    'sample_data_import': "Sample Data Import",
    'sample_data_description': "Click the button below to import sample test data to experience the system functions",
    'load_sample_data': "Load Sample Data",
    'sample_data_loaded_success': "Sample data has been successfully loaded into the subject text boxes! Please check the 'Data Input and Analysis' page.",
    'ai_settings': "AI Feature Settings",
    'master_key_prompt': "Enter admin key to enable AI Q&A feature:",
    'master_key_help': "Enter a valid admin key and complete the analysis successfully, then an AI dialog box will appear below. Please contact the system administrator for the admin key.",
    'master_key_success': "Admin key verification successful, AI features enabled!",
    'master_key_failed': "Admin key verification failed, unable to enable AI features.",
    'irt_simulation_settings': "IRT Simulation Settings",
    'manual_adjustments': "Manual Question Adjustments",
    'manual_adjustments_description': "Manual Question Correctness Adjustments",
    'manual_adjustments_note': "(Only affects IRT simulation)",
    'incorrect_to_correct': "Wrong to Correct Question Numbers",
    'correct_to_incorrect': "Correct to Wrong Question Numbers",
    'example_format': "e.g.: 1,5,10",
    'main_title': "GMAT Score Diagnosis Platform by Dustin",
    'main_subtitle': "Intelligent Personalized Score Analysis and Learning Recommendation System",
    'data_input_tab': "Data Input and Analysis",
    'results_view_tab': "Results View",
    'quick_guide': "Quick User Guide 👉",
    'footer_feedback': "Have questions or suggestions? Please go to",
    'footer_github': "GitHub Issues",
    'footer_submit': "to submit feedback",
    
    # Q Diagnostic Parameters - English translations
    'Q_READING_COMPREHENSION_ERROR': "Q Reading Comprehension Error: Text Understanding",
    'Q_CONCEPT_APPLICATION_ERROR': "Q Concept Application Error: Mathematical Concept/Formula Application",
    'Q_CALCULATION_ERROR': "Q Calculation Error: Mathematical Calculation",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Q Foundation Mastery: Application Instability (Special Focus Error)",
    'Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "Behavioral Pattern: Early Stage Too Fast (Flag risk)",
    'Q_BEHAVIOR_CARELESSNESS_ISSUE': "Behavioral Pattern: Carelessness Issue (High fast-wrong ratio)",
    'Q_READING_COMPREHENSION_DIFFICULTY': "Q Reading Comprehension Difficulty: Text Understanding Difficulty",
    'Q_CONCEPT_APPLICATION_DIFFICULTY': "Q Concept Application Difficulty: Mathematical Concept/Formula Application Difficulty",
    'Q_CALCULATION_DIFFICULTY': "Q Calculation Difficulty: Mathematical Calculation Difficulty",
    'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED': "Q Reading Comprehension Difficulty: Mental Block Unable to Read",
    
    # Additional Q parameters found in code
    'Q_CARELESSNESS_DETAIL_OMISSION': "Q Carelessness Issue: Detail Omission",
    'Q_PROBLEM_UNDERSTANDING_ERROR': "Q Problem Understanding Error: Question Intent Understanding",
    'Q_EFFICIENCY_BOTTLENECK_READING': "Q Efficiency Bottleneck: Reading Speed",
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': "Q Efficiency Bottleneck: Concept Application",
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': "Q Efficiency Bottleneck: Calculation Speed",
    
    # Behavioral pattern variants (without Q_ prefix)
    'BEHAVIOR_CARELESSNESS_ISSUE': "Behavioral Pattern: Carelessness Issue (High fast-wrong ratio)",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "Behavioral Pattern: Early Stage Too Fast (Flag risk)",
    
    # Skill names (if needed for translation)
    'Unknown Skill': "Unknown Skill",
    
    # Common diagnostic terms
    'time_pressure_status': "Time Pressure Status",
    'overtime_threshold': "Overtime Threshold",
    'invalid_questions_excluded': "Invalid Questions Excluded",
    'diagnostic_params': "Diagnostic Parameters",
    'diagnostic_params_list': "Diagnostic Parameters List",
    'question_position': "Question Position",
    'question_fundamental_skill': "Question Fundamental Skill",
    'is_correct': "Is Correct",
    'is_invalid': "Is Invalid",
    'is_manually_invalid': "Is Manually Invalid",
    'question_time': "Question Time",
    'question_difficulty': "Question Difficulty",
    'question_type': "Question Type",
    'overtime': "Overtime",
    'is_sfe': "Is SFE",
    
    # Report sections
    'chapter1_results': "Chapter 1 Results",
    'chapter2_flags': "Chapter 2 Flags",
    'chapter2_summary': "Chapter 2 Summary",
    'chapter3_error_details': "Chapter 3 Error Details",
    'chapter4_correct_slow_details': "Chapter 4 Correct but Slow Details",
    'chapter5_patterns': "Chapter 5 Patterns",
    'chapter6_skill_override': "Chapter 6 Skill Override",
    
    # Behavioral patterns
    'behavioral_patterns': "Behavioral Patterns",
    'early_rushing': "Early Rushing",
    'carelessness_issue': "Carelessness Issue",
    'skill_override': "Skill Override",
    
    # General terms
    'recommendations': "Recommendations",
    'analysis': "Analysis",
    'diagnosis': "Diagnosis",
    'results': "Results",
    'summary': "Summary",
    'details': "Details",
    'error': "Error",
    'correct': "Correct",
    'slow': "Slow",
    'fast': "Fast",
    'invalid': "Invalid",
    'valid': "Valid",
    'threshold': "Threshold",
    'time': "Time",
    'difficulty': "Difficulty",
    'skill': "Skill",
    'position': "Position",
    'type': "Type",
    
    # Q Diagnostic Reporting - English translations for hardcoded Chinese text
    'q_report_title': "Q Section Diagnostic Report Details",
    'q_report_subtitle': "(Based on User Data and Simulated Difficulty Analysis)",
    'report_overview_feedback': "**I. Report Overview and Immediate Feedback**",
    'time_strategy_assessment': "* **A. Response Time and Strategy Assessment**",
    'time_pressure_status_label': "Time Pressure Status:",
    'overtime_threshold_used': "Overtime Threshold Used:",
    'minutes': "minutes",
    'important_notes': "* **B. Important Notes**",
    'manual_invalid_data_count': "Manually Marked Invalid Data Count:",
    'valid_score_rate': "Valid Score Rate (Based on Manual Invalid Exclusion):",
    'yes': "Yes",
    'no': "No",
    
    'core_performance_analysis': "**II. Core Performance Analysis**",
    'content_domain_overview': "* **A. Content Domain Performance Overview**",
    'by_question_type': "* **By Question Type (Real vs Pure):**",
    'real_performance_poor': "Real questions performance poor: Error rate significantly higher than Pure questions",
    'pure_performance_poor': "Pure questions performance poor: Error rate significantly higher than Real questions",
    'real_slower': "Real questions slower: Overtime rate significantly higher than Pure questions",
    'pure_slower': "Pure questions slower: Overtime rate significantly higher than Pure questions",
    'no_significant_difference': "No significant difference between Real and Pure question types performance",
    'error_difficulty_distribution': "* **Error Difficulty Distribution:**",
    'questions_count': "questions",
    
    'core_issues_diagnosis': "**III. Core Issues Diagnosis**",
    'high_frequency_potential_issues': "* **B. High-Frequency Potential Issues**",
    'sfe_attention_note': "Particularly noteworthy is that errors occurred on basic or intermediate difficulty questions within already mastered skill areas",
    'sfe_skills_involved': ", involving skills:",
    'sfe_stability_problem': ", indicating potential stability issues in the application of these knowledge points.",
    'careless_tendency': "Tendency to answer quickly but incorrectly, possibly involving",
    'concept_understanding_issue': "Spent considerable time but still unable to solve some problems, or understanding deviations exist, possibly involving",
    'calculation_error_cause': "Calculation errors are also a cause of point loss",
    'reading_comprehension_barrier': "Text information understanding in Real questions may have barriers",
    'efficiency_time_consumption': "Some questions were answered correctly but took too long in areas such as {} ({}), reflecting that application efficiency needs improvement.",
    'no_core_issues_identified': "No major core problem patterns identified.",
    'reading_real_questions': "Real question reading",
    'concept_thinking': "Concept thinking",
    'calculation_process': "Calculation process",
    'or': " or ",
    
    'special_behavioral_patterns': "* **C. Special Behavioral Pattern Observations**",
    'early_rushing_warning': "Some questions at the beginning of the test were answered at a faster pace. It is recommended to maintain a steady response rhythm to avoid potential \"flag for review\" risks.",
    'carelessness_analysis': "Analysis shows that \"fast and wrong\" situations account for a high proportion ({}), suggesting the need to focus on response carefulness to reduce careless errors.",
    'no_special_patterns': "No obvious special response patterns found.",
    
    'practice_consolidation': "**III. Practice Recommendations and Foundation Consolidation**",
    'priority_consolidation_skills': "* **A. Priority Consolidation Skills**",
    'core_skills_consolidation': "For [**{}**] these core skills, due to overall performance showing significant room for improvement, it is recommended to prioritize systematic foundation consolidation rather than just targeting individual incorrect questions.",
    'no_skill_override_triggered': "No skill override rules requiring priority foundation consolidation were triggered.",
    
    'overall_practice_direction': "* **B. Overall Practice Direction**",
    'sfe_priority_note': "(Note: Recommendations involving \"**Foundation Mastery Instability**\" are listed with priority)",
    'no_specific_practice_recommendations': "No specific practice recommendations generated.",
    
    'follow_up_action_guidance': "**IV. Follow-up Action and Deep Reflection Guidance**",
    'guided_reflection_prompts': "* **B. Guided Reflection Prompts (Targeting Specific Skills and Performance)**",
    'reflection_instruction': "Look for pre-exam practice records of [**{}**] [**{}**], find [**{}**] questions, review and reflect on whether you have:",
    'problems_category': "and other issues.",
    'default_reflection_prompt': "Look for incorrect questions in pre-exam practice records, analyze and reflect on systematic problems and improvement directions according to dimensions such as [Basic Skills] [Question Type] [Time Performance] [Diagnostic Labels].",
    
    'practice_record_review': "* **A. Practice Record Review (Secondary Evidence Reference)**",
    'review_purpose': "* **Purpose:** When you cannot accurately recall specific error causes, involved knowledge points, or need more objective data to confirm problem patterns.",
    'review_method': "* **Method:** It is recommended to review recent practice records according to the above guided reflection and organize related incorrect or overtime questions.",
    'key_focus': "* **Key Focus:** Whether questions repeatedly involve core issues pointed out in Part III of the report:",
    'key_focus_general': "* **Key Focus:** According to core performance analysis, pay attention to common error types.",
    'sample_insufficient_note': "* **Note:** If the sample is insufficient, please pay attention to collecting in upcoming practice for more accurate problem identification.",
    'no_secondary_evidence_needed': "(This analysis found no issues requiring secondary evidence for in-depth exploration, or insufficient data)",
    
    'advanced_assistance': "**V. Seeking Advanced Assistance (Qualitative Analysis)**",
    'qualitative_analysis_suggestion': "* **Recommendation:** If you are still confused about some issues pointed out in the report, you can try **providing 2-3 detailed solution processes and thinking examples of related incorrect questions** for consultants to conduct more in-depth case analysis.",
    
    # Utility functions translations
    'unknown_difficulty': "Unknown Difficulty",
    'low_difficulty': "Low Difficulty / 505+",
    'mid_difficulty_555': "Mid Difficulty / 555+",
    'mid_difficulty_605': "Mid Difficulty / 605+",
    'mid_difficulty_655': "Mid Difficulty / 655+",
    'high_difficulty_705': "High Difficulty / 705+",
    'high_difficulty_805': "High Difficulty / 805+",
    'unknown_difficulty_short': "Unknown Difficulty",
    
    # Main diagnosis module translations
    'report_generation_disabled': "Report generation is disabled or encountered issues.",
    
    # AI prompts module translations
    'no_data_for_analysis': "(No data available for analysis)",
    'no_diagnostic_tags_found': "(No diagnostic tags found)",
    
    # Recommendations module translations
    'macro_comprehensive_foundation': "**Priority Comprehensive Foundation Consolidation** (Overall error rate or overtime rate > 50%): Start from {} difficulty, recommended time limit {} minutes.",
    'start_from_basic_difficulty': "Recommended to start from basic difficulty (specific difficulty unknown)",
    'question_related_trigger': "Question {} related",
    'correct_but_slow_marker': " (correct but slow)",
    'practice_details': "Practice {}, time limit {} minutes.",
    'practice_details_speed': "Practice {}, time limit {} minutes (improve speed).",
    'foundation_instability_marker': "*Foundation Mastery Instability* {}",
    'practice_volume_warning': " **Note: Initial time limit far exceeds target, need to increase practice volume to ensure gradual time limiting is effective**",
    'real_questions_ratio_note': " **Real questions ratio recommended to account for 2/3 of total practice volume.**",
    'increase_practice_volume_note': " **Recommended to increase practice volume for this concept.**",
    'overall_practice_notes': "Overall Practice Notes: {}",
    'skill_label': "Skill: {}",
    'skill_perfect_exemption': "* Skill {} performance is perfect, exempted from practice recommendations.",
    'no_specific_skill_recommendation': "* (No specific recommendations for skill {}, please refer to overall summary.)",
    'no_quantitative_recommendations': "Based on this analysis, no specific quantitative practice recommendations were generated. Please refer to the overall diagnostic summary.",
    
    # Time performance categories
    'fast_wrong': "Fast & Wrong",
    'slow_wrong': "Slow & Wrong",
    'normal_time_wrong': "Normal Time & Wrong",
    
    # Problem categories for reflection
    'carelessness_problems': "Carelessness Issues",
    'reading_comprehension_problems': "Reading Comprehension Issues",
    'calculation_problems': "Calculation Issues",
    'concept_application_problems': "Concept Application Issues",
    'efficiency_problems': "Efficiency Issues",
    'problem_types': "Problem Types",
    
    # AI tool recommendations
    'q_ai_tool_recommendations': "Q Section AI Tool Recommendations",
    'q_no_data_for_ai': "(No Q section data available to generate AI recommendations.)",
    'q_missing_diagnostic_params': "(Q section data missing 'diagnostic_params_list' column, unable to generate AI recommendations.)",
    'q_no_specific_ai_recommendations': "(Based on your Q section edits, no specific tool or AI prompt recommendations were triggered.)",
    'q_ai_missing_config': "(AI recommendation configuration missing, unable to generate Q section recommendations.)",
    'ai_diagnosis_involves': "**If diagnosis involves [**{}**]:**",
    'general_gmat_q_tool_suggestion': "No specific matching tool recommendations found. It is recommended to refer to GMAT official guide Q section related practice and strategies."
} 