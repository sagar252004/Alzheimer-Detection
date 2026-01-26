# main.py (ML ONLY)

import os
import pandas as pd
import joblib

from utils.feature_extraction import extract_features, FEATURE_ORDER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- LAZY-LOADED MODELS ----------
_classifier_model = None
_mmse_model = None


def get_models():
    global _classifier_model, _mmse_model

    if _classifier_model is None:
        _classifier_model = joblib.load(
            os.path.join(BASE_DIR, "models", "svm_classifier.pkl")
        )

    if _mmse_model is None:
        _mmse_model = joblib.load(
            os.path.join(BASE_DIR, "models", "svm_regressor.pkl")
        )

    return _classifier_model, _mmse_model


def predict(audio_path: str):
    """
    Input: audio file path
    Output: dict with classification + mmse score
    """

    # Feature extraction
    features = extract_features(audio_path)
    features_df = pd.DataFrame([features], columns=FEATURE_ORDER)
    features_df = features_df.replace([float("inf"), float("-inf")], 0).fillna(0)

    # Load models only when needed
    classifier_model, mmse_model = get_models()

    classification_pred = classifier_model.predict(features_df)[0]
    mmse_pred = mmse_model.predict(features_df)[0]

    return {
        "classification": "AD" if classification_pred == 1 else "HC",
        "mmse_score": int(round(mmse_pred))
    }
