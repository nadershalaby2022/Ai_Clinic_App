# core/utils_analytics.py
# مسؤول عن التحليلات A-1..A-9 + الجرعات + تكرار المرض

import pandas as pd
import numpy as np

from .utils_data import df_base_clean


# =========================================================
# A-1: فعالية الدواء لكل تشخيص
# =========================================================
def analysis_a1(data_merged):
    df = df_base_clean(data_merged)
    out = (
        df.groupby(["Diagnosis", "Drug_Name"])
        .agg(
            total_cases=("Patient_ID", "count"),
            cured_cases=("Outcome_Class", lambda x: (x == "Cured").sum()),
            cure_rate=("Outcome_Class", lambda x: (x == "Cured").mean()),
            avg_recovery=("Recovery_Days", "mean"),
        )
        .reset_index()
    )
    out["cure_rate"] = out["cure_rate"].fillna(0)
    out["avg_recovery"] = out["avg_recovery"].fillna(999)
    return out.sort_values(
        ["Diagnosis", "cure_rate", "avg_recovery"],
        ascending=[True, False, True],
    )


# =========================================================
# A-2: نسبة الشفاء حسب التشخيص + الشكوى الرئيسية
# =========================================================
def analysis_a2(data_merged):
    df = df_base_clean(data_merged)
    out = (
        df.groupby(["Diagnosis", "Chief_Complaint"])
        .agg(
            total_cases=("Patient_ID", "count"),
            cured_cases=("Outcome_Class", lambda x: (x == "Cured").sum()),
            cure_rate=("Outcome_Class", lambda x: (x == "Cured").mean()),
            avg_recovery=("Recovery_Days", "mean"),
        )
        .reset_index()
    )
    out["cure_rate"] = (out["cure_rate"] * 100).round(1)
    out["avg_recovery"] = out["avg_recovery"].round(2)
    return out.sort_values(["Diagnosis", "cure_rate"], ascending=[True, False])


# =========================================================
# A-3: Score لسرعة وموثوقية الدواء
# =========================================================
def analysis_a3(data_merged):
    df = df_base_clean(data_merged)
    out = (
        df.groupby("Drug_Name")
        .agg(
            total_cases=("Patient_ID", "count"),
            cured_cases=("Outcome_Class", lambda x: (x == "Cured").sum()),
            cure_rate=("Outcome_Class", lambda x: (x == "Cured").mean()),
            avg_recovery=("Recovery_Days", "mean"),
        )
        .reset_index()
    )
    out["avg_recovery"] = out["avg_recovery"].fillna(999)
    out["cure_rate"] = out["cure_rate"].fillna(0)

    out["speed_score"] = 1 / (out["avg_recovery"] + 1)
    out["reliability_score"] = np.log1p(out["total_cases"])

    if out["reliability_score"].max() == 0:
        rel_norm = 0
    else:
        rel_norm = out["reliability_score"] / out["reliability_score"].max()

    out["effectiveness_score"] = (
        0.6 * out["cure_rate"] +
        0.2 * out["speed_score"] +
        0.2 * rel_norm
    )
    return out.sort_values("effectiveness_score", ascending=False)


# =========================================================
# A-6: مدى الجرعات لكل دواء
# =========================================================
def dose_ranges(data_merged):
    df = df_base_clean(data_merged).dropna(
        subset=["Dose_Value", "Dose_Unit", "Weight_KG"]
    )
    if df.empty:
        return pd.DataFrame()

    df["Dose_per_KG"] = df["Dose_Value"] / df["Weight_KG"]

    out = (
        df.groupby(["Drug_Name", "Dose_Unit"])
        .agg(
            min_dose=("Dose_Value", "min"),
            max_dose=("Dose_Value", "max"),
            avg_dose=("Dose_Value", "mean"),
            avg_dose_per_kg=("Dose_per_KG", "mean"),
            cases=("Patient_ID", "count"),
        )
        .reset_index()
    )
    out["avg_dose"] = out["avg_dose"].round(2)
    out["avg_dose_per_kg"] = out["avg_dose_per_kg"].round(2)
    return out


# =========================================================
# A-7: جرعات شاذة (Outliers)
# =========================================================
def dose_outliers(data_merged, z=3):
    temp = data_merged.dropna(subset=["Drug_Name", "Dose_per_KG"]).copy()
    if temp.empty:
        return pd.DataFrame()

    out_list = []
    for drug, g in temp.groupby("Drug_Name"):
        if len(g) < 3:
            continue
        m = g["Dose_per_KG"].mean()
        s = g["Dose_per_KG"].std()
        if s == 0 or np.isnan(s):
            continue
        gg = g[(g["Dose_per_KG"] - m).abs() > (z * s)]
        if not gg.empty:
            out_list.append(gg)

    if out_list:
        return pd.concat(out_list).sort_values("Dose_per_KG", ascending=False)
    return pd.DataFrame()


# =========================================================
# A-8: جودة البيانات
# =========================================================
def data_quality_report(data_merged):
    report = {
        "rows": len(data_merged),
        "unique_patients": data_merged["Patient_ID"].nunique(),
        "missing_rate": data_merged.isna().mean().sort_values(ascending=False),
    }
    return report


# =========================================================
# A-4/A-5: تكرار المرض Recurrence
# =========================================================
def recurrence_table(patient_id, data_merged):
    temp = data_merged[
        (data_merged["Patient_ID"] == patient_id)
        & (data_merged["Visit_Type"] == "New Case")
    ].copy()

    if temp.empty:
        return pd.DataFrame(
            columns=["Diagnosis", "Visit_Date", "days_since_last", "episode_no"]
        )

    temp = temp.sort_values(["Diagnosis", "Visit_Date"])
    temp["Prev_Date"] = temp.groupby("Diagnosis")["Visit_Date"].shift(1)
    temp["days_since_last"] = (temp["Visit_Date"] - temp["Prev_Date"]).dt.days
    temp["episode_no"] = temp.groupby("Diagnosis").cumcount() + 1
    return temp[["Diagnosis", "Visit_Date", "days_since_last", "episode_no"]]


def recurrence_summary(patient_id, data_merged):
    t = recurrence_table(patient_id, data_merged)
    if t.empty:
        return pd.DataFrame(
            columns=[
                "Diagnosis", "recurrence_count",
                "avg_days_between", "min_days_between"
            ]
        )

    s = (
        t.dropna(subset=["days_since_last"])
        .groupby("Diagnosis")
        .agg(
            recurrence_count=("days_since_last", "count"),
            avg_days_between=("days_since_last", "mean"),
            min_days_between=("days_since_last", "min"),
        )
        .reset_index()
        .sort_values(
            ["recurrence_count", "avg_days_between"],
            ascending=[False, True],
        )
    )
    s["avg_days_between"] = s["avg_days_between"].round(1)
    return s
