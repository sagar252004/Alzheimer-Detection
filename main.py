# main.py (ML ONLY)

import os
import uuid
import pandas as pd
import joblib
import shutil

from utils.feature_extraction import extract_features, FEATURE_ORDER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

classifier_model = joblib.load(
    os.path.join(BASE_DIR, "models", "svm_classifier.pkl")
)

mmse_model = joblib.load(
    os.path.join(BASE_DIR, "models", "svm_regressor.pkl")
)

TEMP_DIR = os.path.join(BASE_DIR, "temp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)


def predict(audio_path: str):
    """
    Input: audio file path
    Output: dict with classification + mmse score
    """

    features = extract_features(audio_path)
    features_df = pd.DataFrame([features], columns=FEATURE_ORDER)
    features_df = features_df.fillna(0)


    print(features_df.isna().sum())
    print(features_df.head())

    classification_pred = classifier_model.predict(features_df)[0]
    mmse_pred = mmse_model.predict(features_df)[0]

    

    return {
        "classification": "AD" if classification_pred == 1 else "HC",
        "mmse_score": int(round(mmse_pred))
    }
