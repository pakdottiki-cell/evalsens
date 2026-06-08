from pathlib import Path
import sys

# Ensure the repo root is on sys.path so `ml.*` imports work when run as a script.
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ml.predict import predict_sentiment

samples = [
    "Magaling magturo si sir and he keeps the discussion engaging.",
    "The instructor is difficult to approach when we have concerns.",
    "Average overall experience for this semester.",
    "Mahirap intindihin ang discussion because of poor flow.",
]


if __name__ == "__main__":
    for s in samples:
        out = predict_sentiment(s)
        print("---")
        print(s)
        print(out)



