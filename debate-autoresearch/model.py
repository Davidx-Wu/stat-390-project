"""
EDITABLE -- This is the only file the AutoResearch agent may modify.

Define build_model(), returning an sklearn-compatible estimator or Pipeline.
"""
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model():
    """Current best baseline: v3 safe structured numeric logistic regression."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("logistic", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
