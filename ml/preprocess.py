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


def preprocess_text(text):
    if not text:
        return ""

    text = text.lower()

    # Remove URLs/emails
    text = re.sub(r"http[s]?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)

    # Convert common negation contractions into space-preserving tokens.
    # Keep them as alphabetic tokens so we don't lose the negation signal.
    # Examples: can't -> ca n't, not -> not
    text = text.replace("can't", "ca n't")
    text = text.replace("cannot", "can not")
    text = text.replace("won't", "wo n't")
    text = text.replace("isn't", "is not")
    text = text.replace("aren't", "are not")
    text = text.replace("wasn't", "was not")
    text = text.replace("weren't", "were not")
    text = text.replace("doesn't", "does not")
    text = text.replace("don't", "do not")
    text = text.replace("didn't", "did not")
    text = text.replace("wouldn't", "would not")
    text = text.replace("shouldn't", "should not")
    text = text.replace("can't", "ca n't")

    # Remove punctuation but keep whitespace.
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Tokenize
    tokens = word_tokenize(text)

    cleaned_tokens = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        # Allow negation-like tokens through stopword filtering
        if token in english_stopwords:
            continue
        if len(token) < 2:
            # Keep single-letter negation parts like 'n' if they appear as tokens
            # (e.g., from "can't" -> "ca" "n" after punctuation stripping)
            if token not in {"n"}:
                continue
        if not token.isalpha():
            continue
        cleaned_tokens.append(lemmatizer.lemmatize(token))

    return " ".join(cleaned_tokens)

