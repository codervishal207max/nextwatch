"""Train the NextWatch recommender: Logistic Regression first, Random Forest if LR isn't good enough.

Run:  cd ml && python train.py            (simulated data)
      cd ml && python train.py --source db  (real data from the platform)
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import FEATURES, build_features
from simulate_data import simulate

ARTIFACTS = Path(__file__).parent / "artifacts"
LR_GOOD_ENOUGH_AUC = 0.80   # if LR reaches this on validation, we keep it
MIN_GAIN_FOR_RF = 0.01      # RF must beat LR by this much AUC to replace it


def time_split(df, train=0.6, val=0.2):
    df = df.sort_values("ts").reset_index(drop=True)
    a, b = int(len(df) * train), int(len(df) * (train + val))
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def precision_at_k(df, score_col, k=3):
    """Per user: of the k films the model ranks highest, how many did the user actually like?"""
    out = []
    for _, g in df.groupby("user_id"):
        if len(g) >= k:
            out.append(g.nlargest(k, score_col)["label"].mean())
    return float(np.mean(out)) if out else float("nan")


def evaluate(name, y, proba, df, score_col):
    return {
        "model": name,
        "accuracy": round(accuracy_score(y, proba >= 0.5), 3),
        "roc_auc": round(roc_auc_score(y, proba), 3),
        "pr_auc": round(average_precision_score(y, proba), 3),
        "precision@3": round(precision_at_k(df.assign(_s=proba), "_s"), 3),
    }


def load(source):
    if source == "db":  # real data collected by the platform
        import os
        from sqlalchemy import create_engine
        from db_loader import load_interactions
        url = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).parent.parent / 'backend' / 'nextwatch.db'}")
        return load_interactions(create_engine(url))
    return simulate()  # simulated data, for building/testing the pipeline only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "db"], default="sim")
    args = ap.parse_args()
    ARTIFACTS.mkdir(exist_ok=True)
    interactions, movies = load(args.source)
    if interactions.empty:
        raise SystemExit("No watch sessions in the database yet.")
    data = build_features(interactions, movies)
    data = data.dropna(subset=["label"]).astype({"label": int})
    train, val, test = time_split(data)
    X = {k: d[FEATURES] for k, d in {"train": train, "val": val, "test": test}.items()}
    print(f"rows: train={len(train)} val={len(val)} test={len(test)} | positive rate={data.label.mean():.2f}")

    # --- baseline: rank by platform popularity only ---
    base = test["popularity"].to_numpy() / 100
    baseline = evaluate("popularity baseline", test.label, base, test, "_s")

    # --- 1) Logistic Regression ---
    lr = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))
    lr.fit(X["train"], train.label)
    lr_val_auc = roc_auc_score(val.label, lr.predict_proba(X["val"])[:, 1])
    print(f"Logistic Regression validation AUC = {lr_val_auc:.3f} (target {LR_GOOD_ENOUGH_AUC})")

    chosen_name, chosen, rf = "logistic_regression", lr, None
    if lr_val_auc < LR_GOOD_ENOUGH_AUC:
        # --- 2) Random Forest, only because LR fell short ---
        rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced_subsample",
                                    n_jobs=-1, random_state=42)
        rf.fit(X["train"], train.label)
        rf_val_auc = roc_auc_score(val.label, rf.predict_proba(X["val"])[:, 1])
        print(f"Random Forest validation AUC       = {rf_val_auc:.3f}")
        if rf_val_auc >= lr_val_auc + MIN_GAIN_FOR_RF:
            chosen_name, chosen = "random_forest", rf
    print(f"-> chosen: {chosen_name}\n")

    # --- final report on the untouched test period ---
    results = [baseline, evaluate("logistic_regression", test.label, lr.predict_proba(X["test"])[:, 1], test, "_s")]
    if rf is not None:  # shown even when not chosen, so the comparison is visible
        results.append(evaluate("random_forest", test.label, rf.predict_proba(X["test"])[:, 1], test, "_s"))
    print(pd.DataFrame(results).to_string(index=False))

    # --- what did the model learn? ---
    if chosen_name == "logistic_regression":
        imp = pd.Series(chosen[-1].coef_[0], index=FEATURES).sort_values(key=abs, ascending=False)
        print("\nTop LR coefficients (standardised):")
    else:
        imp = pd.Series(chosen.feature_importances_, index=FEATURES).sort_values(ascending=False)
        print("\nTop RF feature importances:")
    print(imp.head(8).round(3).to_string())

    joblib.dump({"model": chosen, "features": FEATURES, "name": chosen_name, "data_source": args.source}, ARTIFACTS / "model.joblib")
    (ARTIFACTS / "metrics.json").write_text(json.dumps(results, indent=2))
    print(f"\nsaved -> {ARTIFACTS / 'model.joblib'}")


if __name__ == "__main__":
    main()
