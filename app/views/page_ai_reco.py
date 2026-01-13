# app/views/page_ai_reco.py
import datetime

import pandas as pd
import streamlit as st

from config import FILE_PATH
from core.utils_data import (
    load_data,
    load_reference_lists,
    get_next_visit_id,
    save_visit,
    save_visit_drugs,
)


def render_ai_reco_page(engine):
    """
    صفحة توصية علاج بناءً على آخر زيارة + تاريخ العيادة (Rule-based / Data-driven)
    """
    st.header("🤖 توصية علاج بالذكاء الاصطناعي (Data-driven)")

    # نقرأ أحدث نسخة من البيانات من الإكسل
    patients, visits, visit_drugs, ref, merged = load_data(FILE_PATH)

    if patients.empty:
        st.warning("لا توجد بيانات مرضى في الملف حتى الآن.")
        return

    # ========== اختيار المريض (Patient ID) – آخر مريض افتراضيًا ==========
    patient_ids = sorted(patients["Patient_ID"].unique())
    default_index = len(patient_ids) - 1 if len(patient_ids) > 0 else 0

    patient_id = st.selectbox(
        "Patient ID (رقم المريض)",
        options=patient_ids,
        index=default_index,
    )

    # نجيب بيانات المريض
    p_row = patients.loc[patients["Patient_ID"] == patient_id].iloc[0]
    st.markdown(
        f"""
        **المريض:** {p_row['Patient_Name']}  
        **النوع:** {p_row['Gender']} – **تاريخ الميلاد:** {p_row['DOB'].date() if isinstance(p_row['DOB'], pd.Timestamp) else p_row['DOB']}  
        **العنوان:** {p_row.get('Address', '')} – **هاتف:** {p_row.get('Phone_Number', '')}
        """
    )

    # زيارات هذا المريض
    visits_p = visits.loc[visits["Patient_ID"] == patient_id].copy()

    if visits_p.empty:
        st.info("لا توجد زيارات مسجّلة لهذا المريض بعد. لا يمكن توليد توصية علاج.")
        return

    # نجيب آخر زيارة بناءً على التاريخ (أو على ID لو التاريخ مش واضح)
    if "Visit_Date" in visits_p.columns:
        # نحول لتواريخ لو لسه سترينج
        visits_p["Visit_Date_parsed"] = pd.to_datetime(
            visits_p["Visit_Date"], errors="coerce"
        )
        last_visit = visits_p.sort_values("Visit_Date_parsed").iloc[-1]
    else:
        last_visit = visits_p.sort_values("Visit_ID").iloc[-1]

    st.subheader("🧾 آخر زيارة للمريض")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Visit ID:** {int(last_visit['Visit_ID'])}")
        st.write(
            f"**التاريخ:** {last_visit['Visit_Date'].date() if isinstance(last_visit['Visit_Date'], pd.Timestamp) else last_visit['Visit_Date']}"
        )
        st.write(f"**نوع الزيارة:** {last_visit.get('Visit_Type', '')}")
    with col2:
        st.write(f"**Age (شهراً):** {last_visit.get('Age_Months', '')}")
        st.write(f"**Weight (KG):** {last_visit.get('Weight_KG', '')}")
        st.write(f"**Height (CM):** {last_visit.get('Height_CM', '')}")
    with col3:
        st.write(f"**الشكوى:** {last_visit.get('Chief_Complaint', '')}")
        st.write(f"**التشخيص:** {last_visit.get('Diagnosis', '')}")
        st.write(f"**النتيجة:** {last_visit.get('Outcome_Class', '')}")

    diagnosis = str(last_visit.get("Diagnosis", "")).strip()
    chief = str(last_visit.get("Chief_Complaint", "")).strip()

    # ========== توليد توصية علاج من بيانات العيادة ==========

    st.subheader("💊 التوصية المقترحة بناءً على حالات مشابهة")

    if not diagnosis:
        st.warning("التشخيص غير موجود في آخر زيارة، لا يمكن توليد توصية علاج.")
        return

    # نستخدم الـ merged (Visits + Visit_Drugs) لاستخراج الأدوية الأكثر تكراراً لنفس التشخيص
    df = merged.copy()
    df["Diagnosis"] = df["Diagnosis"].astype(str).str.strip()

    similar = df.loc[df["Diagnosis"] == diagnosis].copy()

    if similar.empty:
        st.info("لا توجد زيارات أخرى بنفس هذا التشخيص في البيانات، لا يمكن بناء توصية من السجل التاريخي.")
        return

    # نحسب أكثر الأدوية استخداماً مع هذا التشخيص
    grp = (
        similar.groupby("Drug_Name")
        .agg(
            n=("Drug_Name", "size"),
            avg_dose=("Dose_Value", "mean"),
            most_dose_unit=("Dose_Unit", lambda x: x.value_counts().index[0]),
            most_freq_unit=("Freq_Unit", lambda x: x.value_counts().index[0]),
            avg_freq=("Freq_Value", "mean"),
            avg_duration=("Duration_Days", "mean"),
            most_route=("Route", lambda x: x.value_counts().index[0]),
        )
        .reset_index()
    )

    grp = grp.sort_values("n", ascending=False)

    top_k = st.slider("عدد الأدوية المقترحة", min_value=1, max_value=5, value=3, step=1)
    top_drugs = grp.head(top_k).copy()

    if top_drugs.empty:
        st.info("لا توجد أدوية كافية مرتبطة بهذا التشخيص في البيانات.")
        return

    # نرتب الأعمدة لعرض أوضح
    top_drugs_display = top_drugs[
        [
            "Drug_Name",
            "n",
            "avg_dose",
            "most_dose_unit",
            "avg_freq",
            "most_freq_unit",
            "avg_duration",
            "most_route",
        ]
    ].rename(
        columns={
            "Drug_Name": "الدواء",
            "n": "عدد المرات في البيانات",
            "avg_dose": "متوسط الجرعة",
            "most_dose_unit": "وحدة الجرعة",
            "avg_freq": "متوسط التكرار",
            "most_freq_unit": "وحدة التكرار",
            "avg_duration": "متوسط المدة (يوم)",
            "most_route": "طريقة الإعطاء",
        }
    )

    # تقريب الأرقام
    num_cols = ["متوسط الجرعة", "متوسط التكرار", "متوسط المدة (يوم)"]
    for c in num_cols:
        top_drugs_display[c] = top_drugs_display[c].round(2)

    st.dataframe(top_drugs_display, use_container_width=True)

    st.caption(
        "💡 هذه التوصية مبنية على الأدوية الأكثر استخداماً في العيادة لنفس التشخيص، "
        "وليست بديلاً عن قرار الطبيب."
    )

    # ========== خيار: إضافة هذه الروشتة فعلياً للملف ==========
    st.subheader("📝 حفظ هذه التوصية كزيارة جديدة (اختياري)")

    today = datetime.date.today()
    col_a, col_b = st.columns(2)
    with col_a:
        new_visit_date = st.date_input("تاريخ الزيارة الجديدة", value=today)
        new_visit_type = st.selectbox(
            "نوع الزيارة", ["Follow-up", "New Case", "Clinic", "ER", "Phone"], index=0
        )
    with col_b:
        note_suffix = st.text_input(
            "ملاحظات للـ Outcome (اختياري)",
            value="AI-recommended regimen",
        )

    if st.button("💾 حفظ كزيارة جديدة + روشتة مقترحة"):
        new_visit_id = get_next_visit_id(FILE_PATH)

        # نحضر صف الزيارة الجديدة بالاعتماد على آخر زيارة
        visit_row = {
            "Visit_ID": int(new_visit_id),
            "Patient_ID": int(patient_id),
            "Visit_Date": pd.to_datetime(new_visit_date),
            "Visit_Type": new_visit_type,
            "Source": last_visit.get("Source", "Clinic"),
            "Age_Months": last_visit.get("Age_Months", None),
            "Weight_KG": last_visit.get("Weight_KG", None),
            "Height_CM": last_visit.get("Height_CM", None),
            "Chief_Complaint": chief,
            "Diagnosis": diagnosis,
            "Outcome_Class": "Cured",
            "Outcome_Notes": note_suffix,
            "Recovery_Days": last_visit.get("Recovery_Days", None),
        }

        # نحفظ الزيارة
        save_visit(FILE_PATH, visit_row)

        # الروشتة المقترحة
        drug_rows = []
        line_no = 1
        for _, r in top_drugs.iterrows():
            drug_rows.append(
                {
                    "Visit_ID": int(new_visit_id),
                    "Line_No": line_no,
                    "Drug_Name": r["Drug_Name"],
                    "Drug_Code": "",
                    "Dose_Value": float(r["avg_dose"]) if pd.notna(r["avg_dose"]) else None,
                    "Dose_Unit": r["most_dose_unit"],
                    "Freq_Value": float(r["avg_freq"]) if pd.notna(r["avg_freq"]) else None,
                    "Freq_Unit": r["most_freq_unit"],
                    "Duration_Days": float(r["avg_duration"])
                    if pd.notna(r["avg_duration"])
                    else None,
                    "Route": r["most_route"],
                    "Instructions": note_suffix,
                }
            )
            line_no += 1

        save_visit_drugs(FILE_PATH, drug_rows)

        st.success(
            f"تم حفظ زيارة جديدة برقم {new_visit_id} للمريض {patient_id} مع الروشتة المقترحة ✅"
        )
