import re
import string
import zipfile
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Keep the project's downloaded data discoverable without relying on a
# machine-wide NLTK installation or a shell-specific NLTK_DATA setting.
PROJECT_NLTK_DATA = Path(__file__).resolve().parents[1] / "nltk_data"
PROJECT_NLTK_DATA.mkdir(parents=True, exist_ok=True)
nltk.data.path.insert(0, str(PROJECT_NLTK_DATA))

RESOURCE_MAP = {
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "stopwords": "corpora/stopwords",
}

def _remove_corrupt_archive(resource: str, path: str) -> None:
    """Remove only the archive for a resource that NLTK cannot open."""
    category = path.split("/", 1)[0]
    for data_dir in nltk.data.path:
        archive = Path(data_dir) / category / f"{resource}.zip"
        try:
            if archive.is_file():
                archive.unlink()
        except OSError:
            # The download below will provide the actionable error if the cache
            # cannot be repaired (for example, due to file permissions).
            pass


def _ensure_nltk_resource(resource: str, path: str) -> None:
    """Ensure an NLTK package is present, repairing an invalid ZIP cache."""
    try:
        nltk.data.find(path)
        return
    except (LookupError, zipfile.BadZipFile):
        _remove_corrupt_archive(resource, path)

    nltk.data.clear_cache()
    try:
        # `force=True` is important here: NLTK can report a package as already
        # installed even when its cache is incomplete or corrupt.
        nltk.download(resource, quiet=True, force=True, raise_on_error=True)
    except (OSError, ValueError) as error:
        raise RuntimeError(
            f"Required NLTK resource '{resource}' is unavailable. "
            "Connect to the internet and run the NLTK setup command in the README."
        ) from error

    # Validate the newly downloaded package now, so startup fails with the
    # correct resource name rather than later during sentiment prediction.
    nltk.data.find(path)


for resource, path in RESOURCE_MAP.items():
    _ensure_nltk_resource(resource, path)

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
                lemma_next = _lemmatize(next_tok)
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

        cleaned_tokens.append(_lemmatize(token))
        i += 1

    return cleaned_tokens


def _lemmatize(token: str) -> str:
    """Lemmatize when WordNet is installed; otherwise retain the token."""
    try:
        return lemmatizer.lemmatize(token)
    except LookupError:
        # WordNet is an optional NLTK data package and may be unreachable in
        # offline environments. Tokenization and sentiment prediction can
        # still proceed without lemmatization.
        return token


def preprocess_text(text):
    tokens = tokenize_text(text)
    return " ".join(tokens)

