# core/utils_data.py

import pandas as pd
from pathlib import Path


# ================== قراءة البيانات من Excel ==================
def load_data(file_path: str):
    """
    يرجّع:
    patients, visits, visit_drugs, ref, merged
    """
    patients = pd.read_excel(file_path, sheet_name="Patients")
    visits = pd.read_excel(file_path, sheet_name="Visits")
    visit_drugs = pd.read_excel(file_path, sheet_name="Visit_Drugs")
    ref = pd.read_excel(file_path, sheet_name="Reference_Data")

    merged = visits.merge(visit_drugs, on="Visit_ID", how="left")
    return patients, visits, visit_drugs, ref, merged


# ================== قراءة ليستات الـ Reference_Data ==================
def load_reference_lists(file_path: str):
    """
    يقرأ شيت Reference_Data ويستخرج:
    diag_list, cc_list, drug_list, dose_units, freq_units,
    visit_types, outcome_classes, routes
    """
    ref = pd.read_excel(file_path, sheet_name="Reference_Data")

    def col_list(col_name):
        if col_name not in ref.columns:
            return []
        return (
            ref[col_name]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

    diag_list = col_list("Diagnosis_List")
    cc_list = col_list("Chief_Complaints")
    drug_list = col_list("Drug_List")
    dose_units = col_list("Dose_Units")
    freq_units = col_list("Freq_Units")
    visit_types = col_list("Visit_Types")
    outcome_classes = col_list("Outcome_Classes")
    routes = col_list("Routes")

    return (
        diag_list,
        cc_list,
        drug_list,
        dose_units,
        freq_units,
        visit_types,
        outcome_classes,
        routes,
    )


# ================== أدوات مساعدة عامة ==================
def _load_all_sheets(file_path: str):
    xls = pd.ExcelFile(file_path)
    return {name: xls.parse(name) for name in xls.sheet_names}


def _write_all_sheets(file_path: str, sheets: dict):
    # نكتب كل الشيتات مرة واحدة (overwrite)
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)


# ================== Auto-ID للمرضى والزيارات ==================
def get_next_patient_id(file_path: str, start_from: int = 1001) -> int:
    sheets = _load_all_sheets(file_path)
    patients = sheets.get("Patients", pd.DataFrame())

    if "Patient_ID" not in patients.columns or patients.empty:
        return start_from

    max_id = pd.to_numeric(patients["Patient_ID"], errors="coerce").max()
    return start_from if pd.isna(max_id) else int(max_id) + 1


def get_next_visit_id(file_path: str, start_from: int = 2001) -> int:
    sheets = _load_all_sheets(file_path)
    visits = sheets.get("Visits", pd.DataFrame())

    if "Visit_ID" not in visits.columns or visits.empty:
        return start_from

    max_id = pd.to_numeric(visits["Visit_ID"], errors="coerce").max()
    return start_from if pd.isna(max_id) else int(max_id) + 1


# ================== حفظ مريض جديد ==================
def save_patient(file_path: str, new_row: dict):
    sheets = _load_all_sheets(file_path)
    patients = sheets.get("Patients", pd.DataFrame())

    patients = pd.concat([patients, pd.DataFrame([new_row])], ignore_index=True)
    sheets["Patients"] = patients

    _write_all_sheets(file_path, sheets)


# ================== حفظ زيارة جديدة ==================
def save_visit(file_path: str, new_row: dict):
    sheets = _load_all_sheets(file_path)
    visits = sheets.get("Visits", pd.DataFrame())

    visits = pd.concat([visits, pd.DataFrame([new_row])], ignore_index=True)
    sheets["Visits"] = visits

    _write_all_sheets(file_path, sheets)


# ================== حفظ روشتة (أدوية الزيارة) ==================
def save_visit_drugs(file_path: str, new_rows):
    sheets = _load_all_sheets(file_path)
    drugs = sheets.get("Visit_Drugs", pd.DataFrame())

    if isinstance(new_rows, dict):
        new_df = pd.DataFrame([new_rows])
    else:
        new_df = pd.DataFrame(new_rows)

    drugs = pd.concat([drugs, new_df], ignore_index=True)
    sheets["Visit_Drugs"] = drugs

    _write_all_sheets(file_path, sheets)


# ================== تنظيف الداتا المدموجة للـ ML ==================
def df_base_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    تنظيف بسيط للـ merged dataframe قبل التدريب / التنبؤ
    """
    df = df.copy()

    if "Diagnosis" in df.columns:
        df["Diagnosis"] = df["Diagnosis"].fillna("Unknown")

    if "Drug_Name" in df.columns:
        df["Drug_Name"] = df["Drug_Name"].fillna("Unknown")

    return df.reset_index(drop=True)
