"""Debug script: evaluate how the current sentiment model handles negation
and phrase-level context (not just presence of positive/negative cue words).

Run:  venv_ml\\Scripts\\python ml\\debug_negation.py
"""
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ml.predict import predict_sentiment
from ml.preprocess import preprocess_text, tokenize_text

# (comment, expected_label)
TRICKY_CASES = [
    ("does not discuss topics clearly", "negative"),
    # Positive cue words reversed by negation -> should be NEGATIVE
    ("The teacher is not good at explaining.", "negative"),
    ("The professor is not clear during lectures.", "negative"),
    ("The instructions are not clear at all.", "negative"),
    ("The class is not interesting and I fall asleep.", "negative"),
    ("The teacher is not helpful when we ask questions.", "negative"),
    ("The explanation is not easy to follow.", "negative"),
    ("The professor is not engaging.", "negative"),
    ("The teacher is not prepared for class.", "negative"),
    ("Maliwanag po sana pero hindi naman. (not clear)", "negative"),
    # Negative cue words reversed by negation -> should be POSITIVE
    ("The class is not boring at all, it is very fun.", "positive"),
    ("The teacher is not rude, actually very kind.", "positive"),
    ("The lesson is not difficult, it is easy to understand.", "positive"),
    ("The professor is not unclear, the examples are great.", "positive"),
    # Double negatives / mixed
    ("The teacher is not bad, in fact she is quite good.", "positive"),
    ("It is not that the class is boring, it is just long.", "neutral"),
    # Clear negatives
    ("The teacher is rude and the class is boring.", "negative"),
    ("The professor is confusing and hard to understand.", "negative"),
    # Clear positives
    ("The professor is clear, helpful and engaging.", "positive"),
]

print(f"{'EXPECTED':<10}{'ACTUAL':<10}{'CONFIDENCE':<10} COMMENT")
print("-" * 100)
correct = 0
for comment, expected in TRICKY_CASES:
    out = predict_sentiment(comment)
    actual = out["label"]
    ok = "OK " if actual == expected else "XX "
    if actual == expected:
        correct += 1
    print(f"{expected:<10}{actual:<10}{out['confidence']:<10} {comment}")
    print(f"    tokens -> {tokenize_text(comment)}")
    print(f"    probs  -> {out['probabilities']} {ok}")

print("-" * 100)
print(f"Accuracy on tricky cases: {correct}/{len(TRICKY_CASES)}")
