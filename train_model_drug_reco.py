import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

import joblib


# ===================== إعداد المسارات =====================

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "clinic_data2.xlsx"      # لازم يكون نفس اسم ملف الإكسل
MODEL_PATH = BASE_DIR / "model_drug_reco.pkl"    # ده اللى البرنامج بيحتاجه


def build_training_dataset():
    """
    نبنى داتا تدريب من:
    - Patient_Visits  (التشخيص + الأعراض + السن + الوزن)
    - Visit_Drugs     (الأدوية)
    كل صف = (Diagnosis, Chief_Complaint, Age_Months, Weight_KG) → Drug_Name
    """
    print(f"📂 Loading Excel file: {EXCEL_PATH}")
    xls = pd.ExcelFile(EXCEL_PATH)

    # تحميل الشيتات
    df_visits = pd.read_excel(xls, "Patient_Visits")
    df_drugs  = pd.read_excel(xls, "Visit_Drugs")

    # نختار الأعمدة اللى محتاجينها من الزيارات
    visits_cols = [
        "Visit_ID",
        "Diagnosis",
        "Chief_Complaint",
        "Age_Months",
        "Weight_KG",
    ]
    df_visits_small = df_visits[visits_cols]

    # نعمل join على Visit_ID علشان نعرف كل دواء كان تابع لأى تشخيص/أعراض
    df = df_drugs.merge(df_visits_small, on="Visit_ID", how="inner")

    # نشيل الصفوف اللى ناقصة
    df = df.dropna(
        subset=["Drug_Name", "Diagnosis", "Chief_Complaint", "Age_Months", "Weight_KG"]
    )

    print(f"✅ Training rows after merge & dropna: {len(df)}")

    return df


def train_and_save_model():
    df = build_training_dataset()

    # ========== Features & Target ==========
    target_col = "Drug_Name"

    feature_cols = ["Diagnosis", "Chief_Complaint", "Age_Months", "Weight_KG"]

    X = df[feature_cols]
    y = df[target_col]

    cat_cols = ["Diagnosis", "Chief_Complaint"]
    num_cols = ["Age_Months", "Weight_KG"]

    # ========== Preprocessing ==========
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", StandardScaler(), num_cols),
        ]
    )

    # ========== Model ==========
    clf = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced_subsample",
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", clf),
        ]
    )

    # ========== Train/Test Split ==========
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print("🚀 Training model...")
    model.fit(X_train, y_train)

    train_score = model.score(X_train, y_train)
    test_score  = model.score(X_test, y_test)

    print(f"✅ Train accuracy: {train_score:.3f}")
    print(f"✅ Test  accuracy: {test_score:.3f}")

    # ========== Save ==========
    joblib.dump(model, MODEL_PATH)
    print(f"💾 Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save_model()
