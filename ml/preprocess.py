import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

RESOURCE_MAP = {
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "stopwords": "corpora/stopwords",
    "wordnet": "corpora/wordnet",
    "omw-1.4": "corpora/omw-1.4",
}

for resource, path in RESOURCE_MAP.items():
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()

# Keep common negation tokens instead of removing them as stopwords.
# This helps cases like: "can't explain..." / "not clear".
_base_stopwords = set(stopwords.words("english"))
NEGATION_TOKENS = {
    "no",
    "nor",
    "not",
    "don",
    "don't",
    "didn",
    "didn't",
    "doesn",
    "doesn't",
    "can't",
    "cannot",
    "won",
    "won't",
    "wouldn",
    "wouldn't",
    "shouldn",
    "shouldn't",
    "aren",
    "aren't",
    "isn",
    "isn't",
    "weren",
    "weren't",
    "wasn't",
    "weren",
    "haven",
    "haven't",
    "hasn",
    "hasn't",
    "hadn",
    "hadn't",
    "ma",
}

english_stopwords = _base_stopwords - NEGATION_TOKENS

NEGATION_WORDS = {"not", "no", "never", "cannot"}
CONTRACTION_EXPANSIONS = {
    "can't": "can not",
    "cannot": "can not",
    "won't": "will not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "doesn't": "does not",
    "don't": "do not",
    "didn't": "did not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
}


def _normalize_text(text: str) -> str:
    text = (text or "").lower()

    # Remove URLs/emails
    text = re.sub(r"http[s]?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)

    # Expand contractions so negation is explicit.
    for contracted, expanded in CONTRACTION_EXPANSIONS.items():
        text = text.replace(contracted, expanded)

    # Remove punctuation but keep whitespace.
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


def tokenize_text(text):
    """Tokenize and clean text while preserving negation context."""
    normalized = _normalize_text(text)
    if not normalized.strip():
        return []

    raw_tokens = word_tokenize(normalized)

    cleaned_tokens = []
    i = 0
    while i < len(raw_tokens):
        token = raw_tokens[i].strip()
        if not token:
            i += 1
            continue

        # Keep alphabetic tokens only
        if not token.isalpha():
            i += 1
            continue

        # Negation binding: not + adjective/verb -> not_word
        if token in NEGATION_WORDS and i + 1 < len(raw_tokens):
            next_tok = raw_tokens[i + 1].strip().lower()
            if next_tok.isalpha() and next_tok not in english_stopwords:
                lemma_next = lemmatizer.lemmatize(next_tok)
                cleaned_tokens.append(f"not_{lemma_next}")
                i += 2
                continue
            cleaned_tokens.append("not")
            i += 1
            continue

        if token in english_stopwords:
            i += 1
            continue

        if len(token) < 2:
            i += 1
            continue

        cleaned_tokens.append(lemmatizer.lemmatize(token))
        i += 1

    return cleaned_tokens


def preprocess_text(text):
    tokens = tokenize_text(text)
    return " ".join(tokens)

