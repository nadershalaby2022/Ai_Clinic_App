# app/views/page_visit_form.py

from pathlib import Path

import streamlit as st

from core.utils_data import (
    load_data,
    load_reference_lists,
    get_next_visit_id,
    save_visit,
    save_visit_drugs,
)
from core.prescription import load_profile, save_profile, generate_prescription_pdf


def render_visit_form_page(file_path, engine=None):
    st.header("🧾 إدخال زيارة جديدة (روشتة متعددة الأدوية)")
    st.markdown("---")

    # ============================================
    # Prescription Header Settings (Saved Locally)
    # ============================================
    profile = load_profile()
    with st.expander("Prescription Header Settings (saved on this device)", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            clinic_name = st.text_input("Clinic Name", value=profile.get("clinic_name", ""))
            doctor_name = st.text_input("Doctor Name", value=profile.get("doctor_name", ""))
            doctor_title_1 = st.text_input(
                "Title Line 1", value=profile.get("doctor_title_1", "")
            )
            doctor_title_2 = st.text_input(
                "Title Line 2", value=profile.get("doctor_title_2", "")
            )
        with col_b:
            clinic_address = st.text_input(
                "Clinic Address", value=profile.get("clinic_address", "")
            )
            clinic_phones = st.text_input(
                "Clinic Phones", value=profile.get("clinic_phones", "")
            )
            footer_note = st.text_input(
                "Footer Note", value=profile.get("footer_note", "")
            )

        if st.button("Save Header Settings"):
            updated = {
                "clinic_name": clinic_name,
                "doctor_name": doctor_name,
                "doctor_title_1": doctor_title_1,
                "doctor_title_2": doctor_title_2,
                "clinic_address": clinic_address,
                "clinic_phones": clinic_phones,
                "footer_note": footer_note,
            }
            save_profile(updated)
            profile = updated
            st.success("Header settings saved.")

    # ============================================
    # تحميل البيانات والـ Reference Lists
    # ============================================
    try:
        patients, visits, visit_drugs, ref, merged = load_data(file_path)
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات من ملف الإكسل: {e}")
        return

    if patients.empty:
        st.warning("لا يوجد مرضى في قاعدة البيانات. من فضلك أضف مريض أولًا.")
        return

    (
        diag_list,
        cc_list,
        drug_list,
        dose_units,
        freq_units,
        visit_types,
        outcome_classes,
        routes,
    ) = load_reference_lists(file_path)

    # ============================================
    # Auto-ID: زيارة جديدة
    # ============================================
    new_visit_id = get_next_visit_id(file_path)
    st.info(f"سيتم تسجيل الزيارة برقم: **{new_visit_id}**")

    # ============================================
    # اختيار Patient_ID (آخر مريض بشكل افتراضي)
    # ============================================
    try:
        patient_ids = sorted(patients["Patient_ID"].dropna().astype(int).unique())
    except Exception:
        patient_ids = sorted(patients["Patient_ID"].dropna().unique())

    default_index = len(patient_ids) - 1 if len(patient_ids) > 0 else 0

    st.subheader("🧒 اختيار المريض")
    patient_id = st.selectbox(
        "Patient ID (رقم المريض)",
        options=patient_ids,
        index=default_index,
    )

    # ============================================
    # التحكم في عدد أسطر الروشتة (Session State)
    # ============================================
    if "rx_rows_count" not in st.session_state:
        st.session_state.rx_rows_count = 1

    st.markdown("### 💊 إعداد الروشتة (عدد أسطر الأدوية)")
    col_add, col_del = st.columns(2)
    with col_add:
        if st.button("➕ إضافة سطر دواء"):
            st.session_state.rx_rows_count += 1
    with col_del:
        if st.button("➖ حذف آخر سطر دواء"):
            if st.session_state.rx_rows_count > 1:
                st.session_state.rx_rows_count -= 1

    st.caption(f"عدد أسطر الروشتة الحالية: {st.session_state.rx_rows_count}")

    st.markdown("---")

    # ============================================
    # فورم بيانات الزيارة + الروشتة
    # ============================================
    with st.form("visit_form"):
        st.subheader("📅 بيانات الزيارة")

        col1, col2, col3 = st.columns(3)

        with col1:
            visit_date = st.date_input("تاريخ الزيارة (Visit Date)")
            source = st.selectbox("Source (مصدر الزيارة)", ["Clinic", "ER", "Phone"])

        with col2:
            visit_type = st.selectbox(
                "نوع الزيارة (Visit Type)",
                visit_types if visit_types else ["New Case", "Follow-up"],
            )
            age_months = st.number_input(
                "Age (بالشهور)", min_value=0, step=1, value=0
            )

        with col3:
            weight_kg = st.number_input("Weight (KG)", min_value=0.0, step=0.1, value=0.0)
            height_cm = st.number_input("Height (CM)", min_value=0.0, step=0.1, value=0.0)

        st.markdown("### 🩺 التشخيص والشكوى")

        col_d1, col_d2, col_d3 = st.columns(3)

        with col_d1:
            chief = st.selectbox(
                "الشكوى الرئيسية (Chief Complaint)",
                [""] + cc_list,
            )

        with col_d2:
            diagnosis = st.selectbox(
                "التشخيص (Diagnosis)",
                [""] + diag_list,
            )

        with col_d3:
            outcome_class = st.selectbox(
                "نتيجة الزيارة (Outcome Class)",
                [""] + outcome_classes,
            )

        col_o1, col_o2 = st.columns(2)
        with col_o1:
            outcome_notes = st.text_area("ملاحظات النتيجة (Outcome Notes)", height=80)
        with col_o2:
            recovery_days = st.number_input(
                "عدد أيام التحسن / المتابعة (Recovery Days)",
                min_value=0,
                step=1,
                value=0,
            )

        st.markdown("---")
        st.subheader("💊 الأدوية (روشتة متعددة)")

        rx_rows = []
        for i in range(st.session_state.rx_rows_count):
            st.markdown(f"**سطر دواء رقم {i+1}**")
            c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.6])

            with c1:
                drug_name = st.selectbox(
                    f"اسم الدواء (Drug Name) – سطر {i+1}",
                    [""] + drug_list,
                    key=f"drug_name_{i}",
                )

            with c2:
                dose_value = st.number_input(
                    f"Dose Value – سطر {i+1}",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    key=f"dose_val_{i}",
                )
                dose_unit = st.selectbox(
                    f"Dose Unit – سطر {i+1}",
                    dose_units if dose_units else ["mg", "ml", "g", "teaspoon", "drop"],
                    key=f"dose_unit_{i}",
                )

            with c3:
                freq_value = st.number_input(
                    f"Freq Value – سطر {i+1}",
                    min_value=0.0,
                    step=1.0,
                    value=0.0,
                    key=f"freq_val_{i}",
                )
                freq_unit = st.selectbox(
                    f"Freq Unit – سطر {i+1}",
                    freq_units if freq_units else [
                        "once daily",
                        "twice daily",
                        "3 times daily",
                        "every 6 hours",
                        "every 8 hours",
                    ],
                    key=f"freq_unit_{i}",
                )

            with c4:
                duration_days = st.number_input(
                    f"مدة العلاج (أيام) – سطر {i+1}",
                    min_value=0,
                    step=1,
                    value=0,
                    key=f"duration_{i}",
                )
                route = st.selectbox(
                    f"Route – سطر {i+1}",
                    routes if routes else ["Oral", "IM", "IV", "Neb", "Drops", "Topical"],
                    key=f"route_{i}",
                )
                instructions = st.text_input(
                    f"تعليمات إضافية – سطر {i+1}",
                    key=f"instructions_{i}",
                )

            st.markdown("---")

            rx_rows.append(
                dict(
                    Drug_Name=drug_name,
                    Dose_Value=dose_value,
                    Dose_Unit=dose_unit,
                    Freq_Value=freq_value,
                    Freq_Unit=freq_unit,
                    Duration_Days=duration_days,
                    Route=route,
                    Instructions=instructions,
                )
            )

        submitted = st.form_submit_button("💾 حفظ الزيارة + الروشتة")

    # ============================================
    # بعد الضغط على زر الحفظ
    # ============================================
    if submitted:
        if not diagnosis:
            st.error("من فضلك اختر تشخيص (Diagnosis).")
            return

        # تجهيز صف الزيارة للحفظ في شيت Visits
        visit_row = {
            "Visit_ID": int(new_visit_id),
            "Patient_ID": int(patient_id),
            "Visit_Date": visit_date,
            "Visit_Type": visit_type,
            "Source": source,
            "Age_Months": age_months,
            "Weight_KG": weight_kg,
            "Height_CM": height_cm,
            "Chief_Complaint": chief,
            "Diagnosis": diagnosis,
            "Outcome_Class": outcome_class,
            "Outcome_Notes": outcome_notes,
            "Recovery_Days": recovery_days,
        }

        # تجهيز روشتة الأدوية للحفظ في شيت Visit_Drugs
        drug_rows_to_save = []
        line_no = 1

        for row in rx_rows:
            if not row["Drug_Name"]:
                continue  # نتجاهل الأسطر الفارغة

            r = {
                "Visit_ID": int(new_visit_id),
                "Line_No": line_no,
                "Drug_Name": row["Drug_Name"],
                "Drug_Code": "",
                "Dose_Value": row["Dose_Value"],
                "Dose_Unit": row["Dose_Unit"],
                "Freq_Value": row["Freq_Value"],
                "Freq_Unit": row["Freq_Unit"],
                "Duration_Days": row["Duration_Days"],
                "Route": row["Route"],
                "Instructions": row["Instructions"],
            }
            drug_rows_to_save.append(r)
            line_no += 1

        try:
            save_visit(file_path, visit_row)
            if drug_rows_to_save:
                save_visit_drugs(file_path, drug_rows_to_save)
        except Exception as e:
            st.error(f"حدث خطأ أثناء حفظ البيانات في ملف الإكسل: {e}")
            return

        patient_name = ""
        try:
            if "Patient_Name" in patients.columns:
                pid_str = str(patient_id)
                matched = patients[patients["Patient_ID"].astype(str) == pid_str]
                if not matched.empty:
                    patient_name = str(matched.iloc[0]["Patient_Name"])
        except Exception:
            patient_name = ""

        st.session_state["last_visit_payload"] = {
            "visit_info": {
                "visit_id": new_visit_id,
                "visit_date": str(visit_date),
                "diagnosis": diagnosis,
            },
            "patient_info": {
                "patient_id": patient_id,
                "patient_name": patient_name,
            },
            "drugs": drug_rows_to_save,
        }
        st.session_state["last_prescription_pdf"] = None

        st.success(
            f"تم حفظ الزيارة رقم {new_visit_id} للمريض رقم {patient_id} "
            f"مع عدد {len(drug_rows_to_save)} سطر دواء ✅"
        )

        # تنظيف الكاش علشان باقي الصفحات تشوف التحديث
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
        except Exception:
            pass


    # ============================================
    # Print Prescription (PDF)
    # ============================================
    st.markdown("---")
    st.subheader("Print Prescription")
    payload = st.session_state.get("last_visit_payload")
    if payload:
        if st.button("Generate Prescription PDF"):
            try:
                current_profile = load_profile()
                pdf_path = generate_prescription_pdf(
                    current_profile,
                    payload["visit_info"],
                    payload["patient_info"],
                    payload["drugs"],
                )
                st.session_state["last_prescription_pdf"] = str(pdf_path)
                st.success("Prescription PDF generated.")
            except Exception as exc:
                st.error(f"Failed to generate prescription PDF: {exc}")

        pdf_path_str = st.session_state.get("last_prescription_pdf")
        if pdf_path_str:
            pdf_path = Path(pdf_path_str)
            if pdf_path.exists():
                st.download_button(
                    "Download Prescription PDF",
                    data=pdf_path.read_bytes(),
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    use_container_width=True,
                )
    else:
        st.info("Save a visit first to enable prescription printing.")

    # ============================================
    # Privacy / Session
    # ============================================
    st.markdown("---")
    st.subheader("Privacy & Session")
    st.caption(
        "For privacy, you can clear the session after finishing. This will remove "
        "temporary data from memory and return you to the login screen."
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Clear Session (Privacy)", use_container_width=True):
            try:
                st.session_state.clear()
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception:
                pass
            st.success("Session cleared. Please sign in again.")
            st.rerun()
    with col_p2:
        if st.button("Clear Cache", use_container_width=True):
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception:
                pass
            st.success("Cache cleared.")
