# core/utils_ml.py
# مسؤول عن بناء موديل ML + التوصية بالأدوية + بناء الـ Engine

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import joblib

from .utils_data import load_data, df_base_clean
from .utils_analytics import (
    analysis_a1,
    dose_ranges,
    recurrence_summary,
    recurrence_table,
)


# =========================================================
# 1) بناء الـ Pipeline
# =========================================================
def build_pipe():
    cat_cols = ["Diagnosis", "Chief_Complaint", "Gender"]
    num_cols = ["Age_Months", "Weight_KG"]

    preprocess = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )
    clf = LogisticRegression(max_iter=1000)
    pipe = Pipeline([("prep", preprocess), ("clf", clf)])
    return pipe


# =========================================================
# 2) Auto Smart Split (مع التعامل مع Rare Classes)
# =========================================================
def auto_train_test_split(X, y, sample_weight, test_size=0.2, random_state=42):
    counts = y.value_counts()
    rare = counts[counts < 2].index.tolist()
    print("Rare classes (<2):", rare)

    if rare:
        mask = ~y.isin(rare)
        X2, y2, w2 = X[mask], y[mask], sample_weight[mask]

        n_classes = y2.nunique()
        n_total = len(y2)
        min_test = n_classes / max(n_total, 1)

        if test_size < min_test:
            test_size = round(min_test + 0.01, 2)
            print(f"✅ Auto-increase test_size to {test_size} for stratify.")

        return train_test_split(
            X2, y2, w2,
            test_size=test_size,
            random_state=random_state,
            stratify=y2,
        )
    else:
        return train_test_split(
            X, y, sample_weight,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )


# =========================================================
# 3) تدريب الموديل
# =========================================================
def train_model(data_merged):
    """
    Train ML Recommender v1.
    """
    df_ml = data_merged.dropna(
        subset=[
            "Diagnosis",
            "Drug_Name",
            "Age_Months",
            "Weight_KG",
            "Chief_Complaint",
            "Gender",
            "Outcome_Class",
        ]
    )

    X = df_ml[["Diagnosis", "Chief_Complaint", "Age_Months", "Weight_KG", "Gender"]]
    y = df_ml["Drug_Name"]
    sample_weight = df_ml["Outcome_Class"].apply(
        lambda x: 2 if x == "Cured" else 1
    ).values

    pipe = build_pipe()

    X_train, X_test, y_train, y_test, w_train, w_test = auto_train_test_split(
        X, y, sample_weight
    )
    pipe.fit(X_train, y_train, clf__sample_weight=w_train)
    return pipe


# =========================================================
# 4) حفظ/تحميل الموديل
# =========================================================
def save_model(pipe, model_path):
    joblib.dump(pipe, model_path)


def load_model(model_path):
    return joblib.load(model_path)


# =========================================================
# 5) جداول نجاح/فشل الأدوية لطفل معيّن
# =========================================================
def drugs_worked_table(patient_id, data_merged):
    temp = data_merged[
        (data_merged["Patient_ID"] == patient_id)
        & (data_merged["Outcome_Class"] == "Cured")
    ]
    if temp.empty:
        return pd.DataFrame(
            columns=["Drug_Name", "success_count", "avg_recovery"]
        )

    out = (
        temp.groupby("Drug_Name")
        .agg(
            success_count=("Outcome_Class", "count"),
            avg_recovery=("Recovery_Days", "mean"),
        )
        .reset_index()
        .sort_values(["success_count", "avg_recovery"], ascending=[False, True])
    )
    out["avg_recovery"] = out["avg_recovery"].round(2)
    return out


def drugs_failed_table(patient_id, data_merged):
    temp = data_merged[
        (data_merged["Patient_ID"] == patient_id)
        & (
            data_merged["Outcome_Class"].isin(
                ["No Change", "Worsened", "Side Effects"]
            )
        )
    ]
    if temp.empty:
        return pd.DataFrame(columns=["Drug_Name", "fail_count"])

    out = (
        temp.groupby("Drug_Name")
        .agg(fail_count=("Outcome_Class", "count"))
        .reset_index()
        .sort_values("fail_count", ascending=False)
    )
    return out


# =========================================================
# 6) التوصية المحسّنة A-3
# =========================================================
def recommend_drugs_a3(
    patient_id,
    diagnosis,
    age_months,
    weight_kg,
    chief_complaint,
    gender,
    allergies_text=None,
    k=3,
    fail_threshold=2,
    pipe=None,
    drug_diag_stats=None,
    dose_stats_df=None,
    data_merged=None,
):
    """
    Enhanced recommendation:
    - ML probs + baseline per diagnosis
    - Patient history boost/penalty
    - Recurrence-aware weighting
    - Safety rules (allergy, failed>=threshold)
    - Exclusion log
    """

    if any(x is None for x in [pipe, drug_diag_stats, data_merged]):
        raise ValueError("pipe, drug_diag_stats, and data_merged must be provided.")

    row = pd.DataFrame(
        [
            {
                "Diagnosis": diagnosis,
                "Chief_Complaint": chief_complaint or "Unknown",
                "Age_Months": age_months,
                "Weight_KG": weight_kg,
                "Gender": gender or "Unknown",
            }
        ]
    )

    probs = pipe.predict_proba(row)[0]
    drugs = pipe.named_steps["clf"].classes_
    ml_rank = pd.DataFrame({"Drug_Name": drugs, "ml_prob": probs})

    base = drug_diag_stats[drug_diag_stats["Diagnosis"] == diagnosis][
        ["Drug_Name", "cure_rate", "avg_recovery", "total_cases"]
    ].copy()

    if base.empty:
        base = pd.DataFrame(
            {
                "Drug_Name": drugs,
                "cure_rate": 0,
                "avg_recovery": 999,
                "total_cases": 0,
            }
        )

    candidates = ml_rank.merge(base, on="Drug_Name", how="left").fillna(
        {"cure_rate": 0, "avg_recovery": 999, "total_cases": 0}
    )

    candidates["final_score"] = (
        0.6 * candidates["ml_prob"]
        + 0.3 * candidates["cure_rate"]
        + 0.1 * (1 / (candidates["avg_recovery"] + 1))
    )

    candidates["excluded"] = False
    candidates["exclusion_reason"] = ""

    # ---------------- Patient history ----------------
    failed = drugs_failed_table(patient_id, data_merged)
    worked = drugs_worked_table(patient_id, data_merged)
    fail_map = dict(zip(failed["Drug_Name"], failed["fail_count"])) if not failed.empty else {}
    success_map = dict(zip(worked["Drug_Name"], worked["success_count"])) if not worked.empty else {}

    candidates["fail_count_patient"] = (
        candidates["Drug_Name"].map(fail_map).fillna(0).astype(int)
    )
    candidates["success_count_patient"] = (
        candidates["Drug_Name"].map(success_map).fillna(0).astype(int)
    )

    candidates["final_score"] += 0.05 * candidates["success_count_patient"]
    candidates["final_score"] -= 0.05 * candidates["fail_count_patient"]

    # ---------------- Recurrence-aware ----------------
    rec_sum = recurrence_summary(patient_id, data_merged)
    rec_map = (
        dict(zip(rec_sum["Diagnosis"], rec_sum["recurrence_count"]))
        if not rec_sum.empty
        else {}
    )
    recurrence_n = rec_map.get(diagnosis, 0)
    candidates["recurrence_factor"] = recurrence_n

    if recurrence_n > 0:
        candidates["final_score"] += (
            0.03 * recurrence_n * candidates["success_count_patient"]
        )
        candidates["final_score"] -= (
            0.02 * recurrence_n * candidates["fail_count_patient"]
        )

    # ---------------- Safety: Allergies ----------------
    if allergies_text:
        al = allergies_text.lower()
        mask_allergy = (
            candidates["Drug_Name"].str.lower().str.contains(al, na=False)
        )
        candidates.loc[mask_allergy, "excluded"] = True
        candidates.loc[mask_allergy, "exclusion_reason"] += "Allergy; "

    # ---------------- Safety: failed >= threshold ----------------
    mask_fail = candidates["fail_count_patient"] >= fail_threshold
    candidates.loc[mask_fail, "excluded"] = True
    candidates.loc[mask_fail, "exclusion_reason"] += (
        f"Failed >= {fail_threshold} times; "
    )

    # Dose flag (معلومات فقط)
    candidates["dose_flag"] = "NoHistDose"
    if dose_stats_df is not None and not dose_stats_df.empty:
        def dose_flag(drug):
            rowd = dose_stats_df[dose_stats_df["Drug_Name"] == drug]
            return "HistDoseAvailable" if not rowd.empty else "NoHistDose"

        candidates["dose_flag"] = candidates["Drug_Name"].apply(dose_flag)

    excluded_tbl = candidates[candidates["excluded"]].copy().sort_values(
        "final_score", ascending=False
    )
    final_tbl = (
        candidates[~candidates["excluded"]]
        .copy()
        .sort_values("final_score", ascending=False)
        .head(k)
    )

    return {
        "candidates": candidates.sort_values("final_score", ascending=False),
        "excluded": excluded_tbl,
        "final": final_tbl,
        "worked_table": worked,
        "failed_table": failed,
        "recurrence_summary": rec_sum,
        "recurrence_timeline": recurrence_table(patient_id, data_merged),
    }


def recommend_drugs_final(
    engine,
    patient_id,
    diagnosis,
    age_months,
    weight_kg,
    chief_complaint,
    gender,
    allergies_text=None,
    k=3,
):
    """Wrapper سهل للاستخدام من الواجهة."""
    return recommend_drugs_a3(
        patient_id=patient_id,
        diagnosis=diagnosis,
        age_months=age_months,
        weight_kg=weight_kg,
        chief_complaint=chief_complaint,
        gender=gender,
        allergies_text=allergies_text,
        k=k,
        pipe=engine["pipe"],
        drug_diag_stats=engine["drug_diag_stats"],
        dose_stats_df=engine["dose_stats"],
        data_merged=engine["data_merged"],
    )


# =========================================================
# 7) Engine Builder (يستخدم في الواجهة)
# =========================================================
def build_engine(file_path, model_path=None, retrain_if_missing=True):
    """
    تحميل الداتا + تحليلات أساسية + الموديل في dict واحد.
    """
    patients, visits, visit_drugs, ref, data_merged = load_data(file_path)

    df_base = df_base_clean(data_merged)
    drug_diag_stats = analysis_a1(data_merged)
    dose_stats_df = dose_ranges(data_merged)

    pipe = None
    if model_path:
        try:
            pipe = load_model(model_path)
        except Exception:
            pipe = None

    if pipe is None and retrain_if_missing:
        pipe = train_model(data_merged)
        if model_path:
            save_model(pipe, model_path)

    return {
        "patients": patients,
        "visits": visits,
        "visit_drugs": visit_drugs,
        "ref": ref,
        "data_merged": data_merged,
        "df_base": df_base,
        "drug_diag_stats": drug_diag_stats,
        "dose_stats": dose_stats_df,
        "pipe": pipe,
    }
