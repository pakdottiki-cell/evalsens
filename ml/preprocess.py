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
    "omw-1.4": "corpora/omw-1.4"
}

for resource, path in RESOURCE_MAP.items():
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()
english_stopwords = set(stopwords.words("english"))


def preprocess_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"http[s]?://\\S+|www\\.\\S+", " ", text)
    text = re.sub(r"\\S+@\\S+", " ", text)
    text = re.sub(r"[^a-zA-Z\\s]", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))

    tokens = word_tokenize(text)

    cleaned_tokens = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if token in english_stopwords:
            continue
        if len(token) < 2:
            continue
        if not token.isalpha():
            continue
        cleaned_tokens.append(lemmatizer.lemmatize(token))

    return " ".join(cleaned_tokens)

for resource, path in RESOURCE_MAP.items():
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()
english_stopwords = set(stopwords.words("english"))


def preprocess_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"http[s]?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))

    tokens = word_tokenize(text)

    cleaned_tokens = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if token in english_stopwords:
            continue
        if len(token) < 2:
            continue
        if not token.isalpha():
            continue
        cleaned_tokens.append(lemmatizer.lemmatize(token))

    return " ".join(cleaned_tokens)