"""
EDITABLE -- This is the only file the AutoResearch agent may modify.

Define build_model(), returning an sklearn-compatible estimator or Pipeline.
"""
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


def build_model():
    """Pairwise interaction features with tuned logistic regularization."""
    return Pipeline(
        [
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("logistic", LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
        ]
    )
