"""
Curated static text responses for text-based intents.
Content is grounded in verified project documentation and methodology.
"""

LEADERBOARD_OVERVIEW = (
    "This leaderboard presents the performance of large language models (LLMs) on the LëtzEval "
    "benchmark — a Luxembourgish language assessment covering six CEFR proficiency levels "
    "(A1 to C2) and four task categories: Grammar, Vocabulary, Reading Comprehension, and "
    "Listening Comprehension. The evaluation was conducted by the Institute for National Languages "
    "(INL).\n\n"
    "I can help you:\n"
    "• **Look up** a specific model's score at a given CEFR level and category\n"
    "• **Rank** models by any metric\n"
    "• **Compare** two or more models side by side\n"
    "• **Explain** the benchmark methodology or what a metric means\n"
    "• **Apply or reset** filters on the leaderboard view"
)

METHODOLOGY_OVERVIEW = (
    "The LëtzEval benchmark evaluates LLMs on multiple-choice questions covering Luxembourgish "
    "language at six CEFR proficiency levels (A1–C2). Each level is assessed across four "
    "categories: Grammar, Vocabulary, Reading Comprehension (RC), and Listening Comprehension (LC).\n\n"
    "**Scoring:**\n"
    "• Each sub-score is the percentage of correct answers in that level × category combination.\n"
    "• The **Total** for a level is the unweighted mean of its four category scores.\n"
    "• The **Macro Average** is the unweighted mean of the six level Totals (A1 through C2).\n\n"
    "All models were tested on the same questions with identical prompt formats. Scores reflect "
    "task accuracy on this specific benchmark — not general Luxembourgish language proficiency.\n\n"
    "A missing score indicates no recorded result, not a score of zero."
)

CEFR_EXPLANATION = (
    "CEFR (Common European Framework of Reference for Languages) defines six proficiency levels:\n\n"
    "• **A1** – Beginner: understands and uses simple everyday expressions\n"
    "• **A2** – Elementary: handles simple tasks in familiar contexts\n"
    "• **B1** – Intermediate: manages most everyday situations\n"
    "• **B2** – Upper Intermediate: understands complex texts and interacts spontaneously\n"
    "• **C1** – Advanced: uses the language flexibly for academic and professional purposes\n"
    "• **C2** – Proficient: understands and expresses anything with precision\n\n"
    "A model's score at a given level shows what percentage of questions designed for that "
    "proficiency level it answered correctly on the LëtzEval benchmark."
)

METRIC_EXPLANATIONS: dict[str, str] = {
    'Grammar': (
        "The **Grammar** metric measures the percentage of multiple-choice grammar questions answered "
        "correctly at a specific CEFR level. These questions test morphosyntactic knowledge such as "
        "verb conjugation, agreement, and sentence structure in Luxembourgish."
    ),
    'Vocab': (
        "The **Vocabulary** (Vocab) metric measures the percentage of multiple-choice vocabulary "
        "questions answered correctly at a specific CEFR level. These questions test lexical "
        "knowledge, word meanings, and appropriate word usage in Luxembourgish."
    ),
    'RC': (
        "**Reading Comprehension** (RC) measures the percentage of questions answered correctly on "
        "written passages at a specific CEFR level. Models must interpret Luxembourgish text and "
        "select the correct answer from multiple choices."
    ),
    'LC': (
        "**Listening Comprehension** (LC) measures the percentage of questions answered correctly "
        "based on audio transcripts at a specific CEFR level. It assesses understanding of spoken "
        "Luxembourgish scenarios."
    ),
    'Total': (
        "The **Total** score for a CEFR level is the unweighted mean of the four task-category "
        "scores (Grammar, Vocabulary, RC, LC) at that level. It summarises a model's overall "
        "performance at that proficiency level."
    ),
    'Macro': (
        "The **Macro Average** is the arithmetic mean of the six CEFR-level Total scores "
        "(A1 through C2), each weighted equally. It provides a single summary score across the "
        "full CEFR range. This is the default metric shown in the Simple chart view."
    ),
}

SCORE_INTERPRETATION = (
    "Scores are percentages of correct answers (0–100%). A score of 70 means the model answered "
    "70% of questions correctly on that specific subset.\n\n"
    "**Key notes:**\n"
    "• Scores compare task accuracy on this benchmark, not general language ability.\n"
    "• A missing score ≠ zero — it means no result was recorded for that model.\n"
    "• Chance level (random guessing, 4 choices) is approximately 25%; the baseline "
    "reference line in the chart shows ~34.6% (Macro Average baseline)."
)

OUT_OF_SCOPE = (
    "I'm focused on the LëtzEval Luxembourgish LLM evaluation results. I can help you look up "
    "scores, compare models, explain the benchmark, or apply leaderboard filters. I'm not able "
    "to help with requests outside that scope."
)

GREETING = (
    "Hello! I'm the **LëtzEval Assistant**. I can answer questions about the Luxembourgish "
    "LLM leaderboard — model scores, rankings, comparisons, and benchmark methodology.\n\n"
    "Try asking:\n"
    "• *\"Give me the results for GPT-4o at B2 Grammar\"*\n"
    "• *\"Show the top 5 models for C1 Total\"*\n"
    "• *\"Compare GPT-4o and Llama 3.1 at B2 Grammar\"*\n"
    "• *\"Explain the methodology\"*"
)
