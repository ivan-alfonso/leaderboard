"""
Server-side translation strings for the LëtzEval BAF assistant.

Usage:
    from intents.i18n import t, get_responses
    lang = session.get('ui_language', 'en')
    msg = t('ask_model_name', lang, level='B2', cat='Grammar')

All keys support 6 languages: en, de, fr, it, lb, pt.
Missing translations fall back to English.
Model names, CEFR codes, and numeric scores are passed as format kwargs
and kept language-neutral.
"""
from typing import Any

# ---------------------------------------------------------------------------
# Translation table
# Each value can be a plain string or a string with {placeholders}.
# ---------------------------------------------------------------------------

_T: dict[str, dict[str, str]] = {
    # Greeting shown on first connection
    'greeting': {
        'en': (
            "Hello! I'm the **LëtzEval Assistant**. I can help you explore the "
            "Luxembourgish LLM benchmark.\n\n"
            "Try: *\"Give me GPT-6 Astra's B2 Grammar score\"*, "
            "*\"Top 5 models for C1 Total\"*, or *\"Compare Llama and Gemma at A2\"*."
        ),
        'de': (
            "Hallo! Ich bin der **LëtzEval-Assistent**. Ich helfe Ihnen, das "
            "luxemburgische LLM-Benchmark zu erkunden.\n\n"
            "Versuchen Sie: *„Gib mir den B2-Grammatik-Wert von GPT-6 Astra“*, "
            "*„Top 5 Modelle für C1 Total“* oder *„Vergleiche Llama und Gemma bei A2“*."
        ),
        'fr': (
            "Bonjour ! Je suis l'**Assistant LëtzEval**. Je peux vous aider à explorer "
            "le benchmark luxembourgeois des LLM.\n\n"
            "Essayez : *« Donne-moi le score de grammaire B2 de GPT-6 Astra »*, "
            "*« Top 5 modèles pour C1 Total »* ou *« Compare Llama et Gemma à A2 »*."
        ),
        'it': (
            "Ciao! Sono l'**Assistente LëtzEval**. Posso aiutarti a esplorare il "
            "benchmark lussemburghese dei LLM.\n\n"
            "Prova: *\"Dammi il punteggio di grammatica B2 di GPT-6 Astra\"*, "
            "*\"Top 5 modelli per C1 Total\"* o *\"Confronta Llama e Gemma ad A2\"*."
        ),
        'lb': (
            "Moien! Ech sinn den **LëtzEval-Assistent**. Ech kann Iech hëllefen, "
            "de lëtzebuergeschen LLM-Benchmark ze entdecken.\n\n"
            "Probéiert: *„Gëb mir de B2-Grammatik-Score vu GPT-6 Astra“*, "
            "*„Top 5 Modeller fir C1 Total“* oder *„Vergläich Llama an Gemma bei A2“*."
        ),
        'pt': (
            "Olá! Sou o **Assistente LëtzEval**. Posso ajudá-lo a explorar o "
            "benchmark luxemburguês de LLMs.\n\n"
            "Experimente: *\"Dá-me a pontuação B2 de Gramática do GPT-6 Astra\"*, "
            "*\"Top 5 modelos para C1 Total\"* ou *\"Compara Llama e Gemma em A2\"*."
        ),
    },

    # No candidates after name resolution
    'ask_model_name': {
        'en': "Please include a model name — e.g. *\"{level} {cat}\"* score for *\"Model Name\"*.",
        'de': "Bitte geben Sie einen Modellnamen an — z.B. *\"{level} {cat}\"*-Wert für *\"Modellname\"*.",
        'fr': "Veuillez indiquer un nom de modèle — ex. score *\"{level} {cat}\"* pour *\"Nom du modèle\"*.",
        'it': "Includi il nome di un modello — es. punteggio *\"{level} {cat}\"* per *\"Nome Modello\"*.",
        'lb': "Gitt w.e.g. en Modellnumm un — z.B. *\"{level} {cat}\"*-Score fir *\"Modellnumm\"*.",
        'pt': "Por favor inclua o nome de um modelo — ex. pontuação *\"{level} {cat}\"* para *\"Nome do Modelo\"*.",
    },

    # Ambiguous model name — list candidates
    'ambiguous_model': {
        'en': "I found multiple models matching your query: {names}. Which one did you mean?",
        'de': "Ich habe mehrere passende Modelle gefunden: {names}. Welches meinen Sie?",
        'fr': "J'ai trouvé plusieurs modèles correspondant à votre requête : {names}. Lequel vouliez-vous dire ?",
        'it': "Ho trovato più modelli corrispondenti: {names}. Quale intendevi?",
        'lb': "Ech hunn e puer Modeller fonnt, déi passen: {names}. Wat mengt Dir genee?",
        'pt': "Encontrei vários modelos correspondentes: {names}. Qual você quis dizer?",
    },

    # Macro avg ask when no model given
    'ask_model_macro': {
        'en': "Which model's Macro Average score would you like? Please include the model name.",
        'de': "Von welchem Modell möchten Sie den Makro-Durchschnitt? Bitte Modellnamen angeben.",
        'fr': "Quel modèle voulez-vous pour le score Macro Average ? Veuillez indiquer le nom du modèle.",
        'it': "Di quale modello vuoi il punteggio Macro Average? Includi il nome del modello.",
        'lb': "Vu wéi engem Modell wëllt Dir de Macro Average? Gitt w.e.g. de Modellnumm un.",
        'pt': "De qual modelo você quer a pontuação Macro Average? Por favor inclua o nome do modelo.",
    },

    # Score not found
    'score_not_found': {
        'en': "I could not find a recorded {level} {cat} score for *{model}*. A missing result is not a score of zero.",
        'de': "Ich konnte keinen {level} {cat}-Wert für *{model}* finden. Ein fehlender Wert ist kein Null-Ergebnis.",
        'fr': "Je n'ai pas trouvé de score {level} {cat} enregistré pour *{model}*. Un résultat manquant n'est pas zéro.",
        'it': "Non ho trovato un punteggio {level} {cat} registrato per *{model}*. Un risultato mancante non è zero.",
        'lb': "Ech konnt keen {level} {cat}-Score fir *{model}* fannen. En fehlende Wäert ass keng Null.",
        'pt': "Não encontrei uma pontuação {level} {cat} registada para *{model}*. Um resultado ausente não é zero.",
    },

    # No CEFR totals found
    'cefr_totals_not_found': {
        'en': "I couldn't find any CEFR Total scores for *{model}*.",
        'de': "Ich konnte keine CEFR-Gesamtwerte für *{model}* finden.",
        'fr': "Je n'ai pas trouvé de scores CEFR Total pour *{model}*.",
        'it': "Non ho trovato punteggi CEFR Total per *{model}*.",
        'lb': "Ech konnt keng CEFR-Total-Scores fir *{model}* fannen.",
        'pt': "Não encontrei pontuações CEFR Total para *{model}*.",
    },

    # Ask for CEFR level (compare intent)
    'ask_cefr_level': {
        'en': "Which CEFR level should I use to compare {m1} and {m2}? Please specify A1–C2 (and optionally a category).",
        'de': "Welches CEFR-Niveau soll ich zum Vergleich von {m1} und {m2} verwenden? Bitte A1–C2 angeben.",
        'fr': "Quel niveau CEFR dois-je utiliser pour comparer {m1} et {m2} ? Précisez A1–C2 (et optionnellement une catégorie).",
        'it': "Quale livello CEFR devo usare per confrontare {m1} e {m2}? Specifica A1–C2 (e opzionalmente una categoria).",
        'lb': "Wéi CEFR-Niveau soll ech benotzen fir {m1} an {m2} ze vergläichen? Gitt w.e.g. A1–C2 un.",
        'pt': "Qual nível CEFR devo usar para comparar {m1} e {m2}? Especifique A1–C2 (e opcionalmente uma categoria).",
    },

    # At least 2 models needed for compare
    'compare_need_two': {
        'en': "Please name at least two models to compare. For example: *\"Compare Llama 3.1 - 70B and Qwen 3 - 14B at B2 Grammar.\"*",
        'de': "Bitte nennen Sie mindestens zwei Modelle zum Vergleich. Beispiel: *„Vergleiche Llama 3.1 - 70B und Qwen 3 - 14B bei B2 Grammatik.“*",
        'fr': "Veuillez nommer au moins deux modèles à comparer. Exemple : *« Compare Llama 3.1 - 70B et Qwen 3 - 14B à B2 Grammaire. »*",
        'it': "Per favore nomina almeno due modelli da confrontare. Esempio: *\"Confronta Llama 3.1 - 70B e Qwen 3 - 14B a B2 Grammatica.\"*",
        'lb': "Gitt w.e.g. mindestens zwee Modeller un fir ze vergläichen. Beispill: *„Vergläich Llama 3.1 - 70B an Qwen 3 - 14B bei B2 Grammatik.“*",
        'pt': "Por favor nomeie pelo menos dois modelos para comparar. Exemplo: *\"Compare Llama 3.1 - 70B e Qwen 3 - 14B a B2 Gramática.\"*",
    },

    # Filter applied
    'filter_applied': {
        'en': "Applying filter: {parts}.",
        'de': "Filter wird angewendet: {parts}.",
        'fr': "Application du filtre : {parts}.",
        'it': "Applicazione filtro: {parts}.",
        'lb': "Filter gëtt ugewannt: {parts}.",
        'pt': "Aplicando filtro: {parts}.",
    },

    # No filter identified
    'filter_unrecognized': {
        'en': "I couldn't identify which filter to apply. Try: *\"Filter to B1 Grammar\"*, *\"Show only open-source models\"*.",
        'de': "Ich konnte den Filter nicht erkennen. Versuchen Sie: *„Filter auf B1 Grammatik“*, *„Nur Open-Source-Modelle anzeigen“*.",
        'fr': "Je n'ai pas pu identifier le filtre. Essayez : *« Filtrer à B1 Grammaire »*, *« Afficher seulement open source »*.",
        'it': "Non ho identificato il filtro. Prova: *\"Filtra a B1 Grammatica\"*, *\"Solo modelli open source\"*.",
        'lb': "Ech konnt de Filter net erkennen. Probéiert: *„Filter op B1 Grammatik“*, *„Nëmmen Open-Source-Modeller weisen“*.",
        'pt': "Não consegui identificar o filtro. Tente: *\"Filtrar para B1 Gramática\"*, *\"Mostrar apenas modelos open source\"*.",
    },

    # Reset all
    'reset_all': {
        'en': "Resetting all leaderboard filters to default.",
        'de': "Alle Leaderboard-Filter werden auf Standard zurückgesetzt.",
        'fr': "Réinitialisation de tous les filtres du classement.",
        'it': "Reimpostazione di tutti i filtri del leaderboard.",
        'lb': "All Leaderboard-Filter ginn op Standard zrëckgesat.",
        'pt': "Redefinindo todos os filtros do leaderboard.",
    },

    # Reset specific field(s)
    'reset_fields': {
        'en': "Resetting filter: {fields}.",
        'de': "Filter wird zurückgesetzt: {fields}.",
        'fr': "Réinitialisation du filtre : {fields}.",
        'it': "Reimpostazione filtro: {fields}.",
        'lb': "Filter gëtt zrëckgesat: {fields}.",
        'pt': "Redefinindo filtro: {fields}.",
    },

    # Out of scope
    'out_of_scope': {
        'en': "I can only answer questions about the LëtzEval leaderboard — model scores, rankings, comparisons, and the benchmark methodology. For anything else, please use a general-purpose assistant.",
        'de': "Ich kann nur Fragen zum LëtzEval-Leaderboard beantworten — Modellwerte, Rankings, Vergleiche und Methodik. Für alles andere nutzen Sie bitte einen allgemeinen Assistenten.",
        'fr': "Je ne réponds qu'aux questions sur le classement LëtzEval — scores, classements, comparaisons et méthodologie. Pour autre chose, utilisez un assistant généraliste.",
        'it': "Posso rispondere solo a domande sul leaderboard LëtzEval — punteggi, classifiche, confronti e metodologia. Per altro, usa un assistente generico.",
        'lb': "Ech kann nëmmen Froen üwwert de LëtzEval-Leaderboard beäntwerten — Scores, Rankings, Vergläicher an Methodologie. Für alles anescht, benotzt w.e.g. en allgemengen Assistenten.",
        'pt': "Só respondo a perguntas sobre o leaderboard LëtzEval — pontuações, rankings, comparações e metodologia. Para outra coisa, use um assistente de uso geral.",
    },

    # Generic error
    'error': {
        'en': "I encountered an unexpected error. Please try again.",
        'de': "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
        'fr': "Une erreur inattendue s'est produite. Veuillez réessayer.",
        'it': "Si è verificato un errore imprevisto. Per favore riprova.",
        'lb': "E onerwartede Feeler ass opgetrueden. Probéiert et w.e.g. nach eng Kéier.",
        'pt': "Ocorreu um erro inesperado. Por favor tente novamente.",
    },

    # No models found for ranking
    'rank_no_results': {
        'en': "No recorded results found for **{level} {cat}**{license_suffix}.",
        'de': "Keine Ergebnisse für **{level} {cat}**{license_suffix} gefunden.",
        'fr': "Aucun résultat enregistré pour **{level} {cat}**{license_suffix}.",
        'it': "Nessun risultato registrato per **{level} {cat}**{license_suffix}.",
        'lb': "Keng Resultater fir **{level} {cat}**{license_suffix} fonnt.",
        'pt': "Nenhum resultado registado para **{level} {cat}**{license_suffix}.",
    },

    # Clarification needed (LLM router flag)
    'llm_needs_clarification': {
        'en': "I'm not sure which model you mean. Please use the model name as shown in the table (e.g. *\"GPT-6 Astra\"*, *\"Qwen 2 - 0.5B\"*).",
        'de': "Ich bin nicht sicher, welches Modell Sie meinen. Verwenden Sie bitte den Modellnamen wie in der Tabelle (z.B. *„GPT-6 Astra“*, *„Qwen 2 - 0.5B“*).",
        'fr': "Je ne suis pas sûr du modèle. Utilisez le nom tel qu'il apparaît dans le tableau (ex. *« GPT-6 Astra »*, *« Qwen 2 - 0.5B »*).",
        'it': "Non sono sicuro di quale modello intendi. Usa il nome come appare nella tabella (es. *\"GPT-6 Astra\"*, *\"Qwen 2 - 0.5B\"*).",
        'lb': "Ech sinn net sécher, wéi Modell Dir mengt. Benotzt w.e.g. den Numm wéi an der Tabell (z.B. *„GPT-6 Astra“*, *„Qwen 2 - 0.5B“*).",
        'pt': "Não tenho certeza de qual modelo você se refere. Use o nome como aparece na tabela (ex. *\"GPT-6 Astra\"*, *\"Qwen 2 - 0.5B\"*).",
    },
}

_ALLOWED_LANGS = {'en', 'de', 'fr', 'it', 'lb', 'pt'}


def t(key: str, lang: str = 'en', **kwargs: Any) -> str:
    """Return the translation for `key` in `lang`, falling back to English.

    Keyword arguments are interpolated via str.format().  Any formatting
    error falls back to the unformatted English string.
    """
    lang = lang if lang in _ALLOWED_LANGS else 'en'
    bucket = _T.get(key, {})
    template = bucket.get(lang) or bucket.get('en', f'[{key}]')
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            try:
                return (bucket.get('en', f'[{key}]')).format(**kwargs)
            except Exception:
                return bucket.get('en', f'[{key}]')
    return template
