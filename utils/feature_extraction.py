import whisper
import os
import numpy as np
import pandas as pd
import librosa
import parselmouth
import whisper
import spacy
from tqdm import tqdm
# from google.colab import drive

# whisper_model = whisper.load_model("tiny")
# nlp = spacy.load("en_core_web_sm")
# drive.mount("/content/drive")
# audio_path = "/content/drive/MyDrive/ADReSSo/ADReSS M/train/adrso317.mp3"

_whisper_model = None
_nlp = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model

# def get_nlp():
#     global _nlp
#     if _nlp is None:
#         _nlp = spacy.load("en_core_web_sm")
#     return _nlp

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback: blank English pipeline (Python 3.13 safe)
            _nlp = spacy.blank("en")
    return _nlp

def safe_stats(x):
    x = np.array(x).flatten()
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return {"mean": 0, "std": 0, "min": 0, "max": 0}
    return {
        "mean": float(np.mean(x)),
        "std":  float(np.std(x)),
        "min":  float(np.min(x)),
        "max":  float(np.max(x))
    }

FEATURE_ORDER = [
    "pitch_mean","pitch_std","pitch_min","pitch_max",
    "jitter","shimmer","hnr","rms_energy","zcr_mean",

    "spectral_centroid_mean","spectral_centroid_std",
    "spectral_bandwidth_mean","spectral_bandwidth_std",
    "spectral_rolloff_mean","spectral_rolloff_std",
    "spectral_contrast_mean","spectral_flatness_mean",

    "mfcc1_mean","mfcc2_mean","mfcc3_mean","mfcc4_mean","mfcc5_mean","mfcc6_mean",
    "mfcc7_mean","mfcc8_mean","mfcc9_mean","mfcc10_mean","mfcc11_mean","mfcc12_mean","mfcc13_mean",

    "mfcc1_std","mfcc2_std","mfcc3_std","mfcc4_std","mfcc5_std","mfcc6_std",
    "mfcc7_std","mfcc8_std","mfcc9_std","mfcc10_std","mfcc11_std","mfcc12_std","mfcc13_std",

    "speech_duration","pause_ratio","pause_count",
    "pause_mean_duration","pause_max_duration","speech_rate_wps",

    "word_count","sentence_count","avg_sentence_len",
    "noun_ratio","verb_ratio","pron_ratio"
]


def extract_features(audio_path):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    y = y.astype(np.float32)
    features = {}


    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i in range(13):
        features[f"mfcc{i+1}_mean"] = mfcc[i].mean()
        features[f"mfcc{i+1}_std"]  = mfcc[i].std()


    spectral_feats = {
        "centroid": librosa.feature.spectral_centroid(y=y, sr=sr),
        "bandwidth": librosa.feature.spectral_bandwidth(y=y, sr=sr),
        "rolloff": librosa.feature.spectral_rolloff(y=y, sr=sr),
        "contrast": librosa.feature.spectral_contrast(y=y, sr=sr),
        "flatness": librosa.feature.spectral_flatness(y=y)
    }

    for name, val in spectral_feats.items():
        stats = safe_stats(val)
        features[f"spectral_{name}_mean"] = stats["mean"]
        features[f"spectral_{name}_std"]  = stats["std"]


    features["zcr_mean"] = librosa.feature.zero_crossing_rate(y).mean()
    features["rms_energy"] = librosa.feature.rms(y=y).mean()


    snd = parselmouth.Sound(audio_path)
    pitch = snd.to_pitch()
    pitch_vals = pitch.selected_array['frequency']
    pitch_vals = pitch_vals[pitch_vals > 0]

    pitch_stats = safe_stats(pitch_vals)
    features["pitch_mean"] = pitch_stats["mean"]
    features["pitch_std"]  = pitch_stats["std"]
    features["pitch_min"]  = pitch_stats["min"]
    features["pitch_max"]  = pitch_stats["max"]

    point = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", 75, 500)
    features["jitter"] = parselmouth.praat.call(point, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    features["shimmer"] = parselmouth.praat.call([snd, point], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    try:
        harmonicity = parselmouth.praat.call(snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        features["hnr"] = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)
    except:
        features["hnr"] = np.nan


    non_silent = librosa.effects.split(y, top_db=30)
    speech_dur = sum((e - s) / sr for s, e in non_silent)
    total_dur = len(y) / sr

    pauses = total_dur - speech_dur
    features["speech_duration"] = speech_dur
    features["pause_ratio"] = pauses / total_dur if total_dur else 0
    features["pause_count"] = len(non_silent) - 1 if len(non_silent) > 1 else 0

    pause_durations = []
    for i in range(1, len(non_silent)):
        pause = (non_silent[i][0] - non_silent[i-1][1]) / sr
        if pause > 0:
            pause_durations.append(pause)

    pause_stats = safe_stats(pause_durations)
    features["pause_mean_duration"] = pause_stats["mean"]
    features["pause_max_duration"]  = pause_stats["max"]


    whisper_model = get_whisper()
    nlp = get_nlp()

    text = whisper_model.transcribe(y, task="translate")["text"]
    doc = nlp(text)

    words = [t for t in doc if t.is_alpha]
    sents = list(doc.sents)

    features["word_count"] = len(words)
    features["sentence_count"] = len(sents)
    features["avg_sentence_len"] = (
        np.mean([len([t for t in s if t.is_alpha]) for s in sents]) if sents else 0
    )

    pos_tags = [t.pos_ for t in words]
    features["noun_ratio"] = pos_tags.count("NOUN") / len(pos_tags) if pos_tags else 0
    features["verb_ratio"] = pos_tags.count("VERB") / len(pos_tags) if pos_tags else 0
    features["pron_ratio"] = pos_tags.count("PRON") / len(pos_tags) if pos_tags else 0

    features["lexical_diversity"] = len(set(words)) / len(words) if words else 0

    fillers = {"um", "uh", "er", "ah"}
    features["filler_ratio"] = (
        sum(1 for w in words if w.text.lower() in fillers) / len(words)
        if words else 0
    )

    features["speech_rate_wps"] = len(words) / speech_dur if speech_dur > 0 else 0

    return {k: features.get(k, 0) for k in FEATURE_ORDER}

# features = extract_features("./ex1.wav")