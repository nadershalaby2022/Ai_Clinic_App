# app/views/page_visit_form.py

from pathlib import Path
import base64

import streamlit as st
import streamlit.components.v1 as components

from core.utils_data import (
    load_data,
    load_reference_lists,
    get_next_patient_id,
    get_next_visit_id,
    save_patient,
    save_visit,
    save_visit_drugs,
)
from core.prescription import (
    load_profile,
    save_profile,
    generate_prescription_pdf,
    build_prescription_html,
)


def render_visit_form_page(file_path, engine=None):
    lang = st.session_state.get("ui_lang", "en")

    def _t(en: str, ar: str) -> str:
        return en if lang == "en" else ar

    st.header(_t("🧾 New Visit Entry (Multi-Drug Prescription)", "🧾 إدخال زيارة جديدة (روشتة متعددة الأدوية)"))
    st.markdown("---")

    # ============================================
    # تحميل البيانات والـ Reference Lists
    # ============================================
    try:
        patients, visits, visit_drugs, ref, merged = load_data(file_path)
    except Exception as e:
        st.error(_t(f"Failed to load data from Excel file: {e}", f"خطأ في تحميل البيانات من ملف الإكسل: {e}"))
        return

    if patients.empty:
        st.warning(_t("No patients found in the database. Please add a patient first.", "لا يوجد مرضى في قاعدة البيانات. من فضلك أضف مريض أولًا."))

    # ============================================
    # Search Patient (Quick Lookup)
    # ============================================
    st.subheader(_t("🔍 Search Patient", "🔍 بحث عن مريض"))
    search_query = st.text_input(
        _t("Search by ID / Name / Phone", "ابحث بالرقم / الاسم / الهاتف"),
        key="patient_search_query",
    )
    filtered_patients = patients
    if search_query.strip():
        q = search_query.strip()
        mask = None
        if "Patient_ID" in patients.columns:
            m = patients["Patient_ID"].astype(str).str.contains(q, na=False)
            mask = m if mask is None else (mask | m)
        if "Patient_Name" in patients.columns:
            m = patients["Patient_Name"].astype(str).str.contains(q, case=False, na=False)
            mask = m if mask is None else (mask | m)
        if "Phone_Number" in patients.columns:
            m = patients["Phone_Number"].astype(str).str.contains(q, case=False, na=False)
            mask = m if mask is None else (mask | m)
        if mask is not None:
            filtered_patients = patients[mask]
    if not filtered_patients.empty:
        cols = [c for c in ["Patient_ID", "Patient_Name", "Phone_Number"] if c in filtered_patients.columns]
        st.dataframe(filtered_patients[cols], use_container_width=True)

    st.markdown("---")
    # ============================================
    # New Patient (Inline)
    # ============================================
    st.subheader(_t("➕ New Patient (Quick Add)", "➕ مريض جديد (إضافة سريعة)"))
    new_patient_id = get_next_patient_id(file_path)
    st.info(_t(f"New Patient ID: **{new_patient_id}**", f"رقم المريض الجديد: **{new_patient_id}**"))

    with st.form("patient_form_inline"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(_t("Patient Name", "اسم المريض"))
            gender = st.selectbox(_t("Gender", "النوع"), ["Male", "Female"])
            dob = st.date_input(_t("Date of Birth", "تاريخ الميلاد"))
        with col2:
            phone = st.text_input(_t("Phone Number", "رقم الهاتف"))
            parent_name = st.text_input(_t("Parent Name", "اسم ولي الأمر"))
            address = st.text_input(_t("Address", "العنوان"))

        allergies = st.text_input(_t("Allergies (optional)", "الحساسية (اختياري)"))
        notes = st.text_area(_t("Notes (optional)", "ملاحظات (اختياري)"))

        submitted_new = st.form_submit_button(_t("Save Patient", "حفظ المريض"))

    if submitted_new:
        if not name.strip():
            st.error(_t("Please enter patient name.", "من فضلك أدخل اسم المريض."))
        else:
            row = {
                "Patient_ID": int(new_patient_id),
                "Patient_Name": name,
                "Gender": gender,
                "DOB": dob,
                "Phone_Number": phone,
                "Parent_Name": parent_name,
                "Address": address,
                "Allergies": allergies,
                "Notes": notes,
            }
            try:
                save_patient(file_path, row)
                st.session_state["selected_patient_id"] = int(new_patient_id)
                st.success(_t(f"Patient saved: {new_patient_id}", f"تم حفظ المريض: {new_patient_id}"))
                try:
                    st.cache_data.clear()
                    st.cache_resource.clear()
                except Exception:
                    pass
                st.rerun()
            except Exception as e:
                st.error(_t(f"Failed to save patient: {e}", f"فشل حفظ المريض: {e}"))

    st.markdown("---")
    # ============================================
    # Prescription Header Settings (Saved Locally)
    # ============================================
    profile = load_profile()
    with st.expander(
        _t("Prescription Header Settings (saved on this device)", "إعدادات ترويسة الروشتة (محفوظة على هذا الجهاز)"),
        expanded=False,
    ):
        col_a, col_b = st.columns(2)
        with col_a:
            clinic_name = st.text_input(_t("Clinic Name", "اسم العيادة"), value=profile.get("clinic_name", ""))
            doctor_name = st.text_input(_t("Doctor Name", "اسم الطبيب"), value=profile.get("doctor_name", ""))
            doctor_title_1 = st.text_input(
                _t("Title Line 1", "اللقب سطر 1"), value=profile.get("doctor_title_1", "")
            )
            doctor_title_2 = st.text_input(
                _t("Title Line 2", "اللقب سطر 2"), value=profile.get("doctor_title_2", "")
            )
        with col_b:
            clinic_address = st.text_input(
                _t("Clinic Address", "عنوان العيادة"), value=profile.get("clinic_address", "")
            )
            clinic_phones = st.text_input(
                _t("Clinic Phones", "أرقام العيادة"), value=profile.get("clinic_phones", "")
            )
            footer_note = st.text_input(
                _t("Footer Note", "ملاحظة أسفل الروشتة"), value=profile.get("footer_note", "")
            )

        if st.button(_t("Save Header Settings", "حفظ إعدادات الترويسة")):
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
            st.success(_t("Header settings saved.", "تم حفظ إعدادات الترويسة."))

    if patients.empty:
        st.info(_t("Add a patient first to create a visit.", "أضف مريضًا أولاً لإنشاء زيارة."))
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
    st.info(_t(f"New visit will be recorded as: **{new_visit_id}**", f"سيتم تسجيل الزيارة برقم: **{new_visit_id}**"))

    # ============================================
    # Select Patient
    # ============================================
    base_patients = filtered_patients if (search_query.strip() and not filtered_patients.empty) else patients

    try:
        patient_ids = sorted(base_patients["Patient_ID"].dropna().astype(int).unique())
    except Exception:
        patient_ids = sorted(base_patients["Patient_ID"].dropna().unique())

    patient_name_map = {}
    try:
        for _, row in base_patients.iterrows():
            pid = row.get("Patient_ID")
            try:
                pid_int = int(pid)
            except Exception:
                continue
            patient_name_map[pid_int] = str(row.get("Patient_Name", ""))
    except Exception:
        pass

    selected_id = st.session_state.get("selected_patient_id")
    if selected_id in patient_ids:
        default_index = patient_ids.index(selected_id)
    else:
        default_index = len(patient_ids) - 1 if len(patient_ids) > 0 else 0

    st.subheader(_t("🧒 Select Patient", "🧒 اختيار المريض"))
    patient_id = st.selectbox(
        _t("Patient ID", "رقم المريض"),
        options=patient_ids,
        index=default_index,
        format_func=lambda pid: f"{pid} - {patient_name_map.get(pid, '')}".strip(' -'),
    )

    # ============================================
    # التحكم في عدد أسطر الروشتة (Session State)
    # ============================================
    if "rx_rows_count" not in st.session_state:
        st.session_state.rx_rows_count = 1

    # ============================================
    # فورم بيانات الزيارة + الروشتة
    # ============================================
    st.subheader(_t("📅 Visit Details", "📅 بيانات الزيارة"))

    col1, col2, col3 = st.columns(3)

    with col1:
        visit_date = st.date_input(_t("Visit Date", "تاريخ الزيارة"))
        source = st.selectbox(_t("Source", "مصدر الزيارة"), ["Clinic", "ER", "Phone"])

    with col2:
        visit_type = st.selectbox(
            _t("Visit Type", "نوع الزيارة"),
            visit_types if visit_types else ["New Case", "Follow-up"],
        )
        age_months = st.number_input(
            _t("Age (months)", "العمر (بالشهور)"), min_value=0, step=1, value=0
        )

    with col3:
        weight_kg = st.number_input(_t("Weight (KG)", "الوزن (كجم)"), min_value=0.0, step=0.1, value=0.0)
        height_cm = st.number_input(_t("Height (CM)", "الطول (سم)"), min_value=0.0, step=0.1, value=0.0)

    st.markdown(_t("### 🩺 Diagnosis & Complaint", "### 🩺 التشخيص والشكوى"))

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        chief = st.selectbox(
            _t("Chief Complaint", "الشكوى الرئيسية"),
            [""] + cc_list,
        )

    with col_d2:
        diagnosis = st.selectbox(
            _t("Diagnosis", "التشخيص"),
            [""] + diag_list,
        )

    with col_d3:
        outcome_class = st.selectbox(
            _t("Outcome Class", "نتيجة الزيارة"),
            [""] + outcome_classes,
        )

    col_o1, col_o2 = st.columns(2)
    with col_o1:
        outcome_notes = st.text_area(_t("Outcome Notes", "ملاحظات النتيجة"), height=80)
    with col_o2:
        recovery_days = st.number_input(
            _t("Recovery Days", "عدد أيام التحسن / المتابعة"),
            min_value=0,
            step=1,
            value=0,
        )

    st.markdown("---")
    st.subheader(_t("💊 Medications (Multi-Drug Prescription)", "💊 الأدوية (روشتة متعددة)"))

    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button(_t("➕ Add Drug Line", "➕ إضافة سطر دواء"), use_container_width=True):
            st.session_state.rx_rows_count += 1
    with col_remove:
        if st.button(_t("➖ Remove Last Line", "➖ حذف آخر سطر دواء"), use_container_width=True):
            if st.session_state.rx_rows_count > 1:
                st.session_state.rx_rows_count -= 1

    st.caption(
        _t(
            f"Current prescription lines: {st.session_state.rx_rows_count}",
            f"عدد أسطر الروشتة الحالية: {st.session_state.rx_rows_count}",
        )
    )

    rx_rows = []
    for i in range(st.session_state.rx_rows_count):
        st.markdown(f"**{_t('Medication Line', 'سطر دواء رقم')} {i+1}**")
        c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.6])

        with c1:
            drug_name = st.selectbox(
                _t(f"Drug Name – Line {i+1}", f"اسم الدواء – سطر {i+1}"),
                [""] + drug_list,
                key=f"drug_name_{i}",
            )

        with c2:
            dose_value = st.number_input(
                _t(f"Dose Value – Line {i+1}", f"قيمة الجرعة – سطر {i+1}"),
                min_value=0.0,
                step=0.1,
                value=0.0,
                key=f"dose_val_{i}",
            )
            dose_unit = st.selectbox(
                _t(f"Dose Unit – Line {i+1}", f"وحدة الجرعة – سطر {i+1}"),
                dose_units if dose_units else ["mg", "ml", "g", "teaspoon", "drop"],
                key=f"dose_unit_{i}",
            )

        with c3:
            freq_value = st.number_input(
                _t(f"Frequency Value – Line {i+1}", f"قيمة التكرار – سطر {i+1}"),
                min_value=0.0,
                step=1.0,
                value=0.0,
                key=f"freq_val_{i}",
            )
            freq_unit = st.selectbox(
                _t(f"Frequency Unit – Line {i+1}", f"وحدة التكرار – سطر {i+1}"),
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
                _t(f"Duration (days) – Line {i+1}", f"مدة العلاج (أيام) – سطر {i+1}"),
                min_value=0,
                step=1,
                value=0,
                key=f"duration_{i}",
            )
            route = st.selectbox(
                _t(f"Route – Line {i+1}", f"طريقة الاستخدام – سطر {i+1}"),
                routes if routes else ["Oral", "IM", "IV", "Neb", "Drops", "Topical"],
                key=f"route_{i}",
            )
            instructions = st.text_input(
                _t(f"Additional Instructions – Line {i+1}", f"تعليمات إضافية – سطر {i+1}"),
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

    submitted = st.button(_t("Save Visit + Prescription", "حفظ الزيارة + الروشتة"))

    # ============================================
    # بعد الضغط على زر الحفظ
    # ============================================
    if submitted:
        if not diagnosis:
            st.error(_t("Please choose a diagnosis.", "من فضلك اختر تشخيص."))
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
            st.error(_t(f"Failed to save data to Excel: {e}", f"حدث خطأ أثناء حفظ البيانات في ملف الإكسل: {e}"))
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
            _t(
                f"Visit {new_visit_id} saved for patient {patient_id} with "
                f"{len(drug_rows_to_save)} medication lines ✅",
                f"تم حفظ الزيارة رقم {new_visit_id} للمريض رقم {patient_id} "
                f"مع عدد {len(drug_rows_to_save)} سطر دواء ✅",
            )
        )

        # تنظيف الكاش علشان باقي الصفحات تشوف التحديث
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
        except Exception:
            pass


    # ============================================
    # ============================================
    # ============================================
    # Print Prescription (HTML Report)
    # ============================================
    st.markdown("---")
    st.subheader(_t("🖨️ Prescription Report", "🖨️ تقرير الروشتة"))
    payload = st.session_state.get("last_visit_payload")
    if payload:
        report_html = build_prescription_html(
            load_profile(),
            payload["visit_info"],
            payload["patient_info"],
            payload["drugs"],
            lang=lang,
        )

        with st.expander(_t("Preview Prescription", "معاينة الروشتة")):
            components.html(report_html, height=820, scrolling=True)

        open_label = _t("Open Prescription in New Tab", "فتح الروشتة في تبويب جديد")
        open_alert = _t(
            "Pop-ups blocked. Please allow pop-ups and try again.",
            "المتصفح منع فتح نافذة جديدة. فعّل Pop-ups ثم جرب مرة أخرى."
        )

        b64 = base64.b64encode(report_html.encode("utf-8")).decode("utf-8")
        open_js = f"""
<script>
function openPrescriptionTab(){{
  const b64 = "{b64}";
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const html = new TextDecoder("utf-8").decode(bytes);
  const w = window.open("about:blank", "_blank");
  if(!w){{ alert("{open_alert}"); return; }}
  w.document.open();
  w.document.write(html);
  w.document.close();
  w.focus();
}}
</script>
<button
  onclick="openPrescriptionTab()"
  style="background:#111827;color:#fff;border:none;border-radius:10px;padding:10px 14px;font-weight:900;cursor:pointer;"
>
  🖨️ {open_label}
</button>
"""
        components.html(open_js, height=70)

        if st.button(_t("Generate PDF (Optional)", "توليد PDF (اختياري)")):
            try:
                pdf_path = generate_prescription_pdf(
                    load_profile(),
                    payload["visit_info"],
                    payload["patient_info"],
                    payload["drugs"],
                )
                st.session_state["last_prescription_pdf"] = str(pdf_path)
                st.success(_t("PDF generated.", "تم توليد ملف PDF."))
            except Exception as exc:
                st.error(_t(f"Failed to generate PDF: {exc}", f"فشل توليد PDF: {exc}"))

        pdf_path_str = st.session_state.get("last_prescription_pdf")
        if pdf_path_str:
            pdf_path = Path(pdf_path_str)
            if pdf_path.exists():
                st.download_button(
                    _t("Download PDF", "تحميل PDF"),
                    data=pdf_path.read_bytes(),
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    use_container_width=True,
                )
    else:
        st.info(_t("Save a visit first to enable prescription printing.", "احفظ الزيارة أولًا لتفعيل طباعة الروشتة."))

    # Privacy / Session
    # ============================================
    st.markdown("---")
    st.subheader(_t("Privacy & Session", "الخصوصية والجلسة"))
    st.caption(
        _t(
            "For privacy, you can clear the session after finishing. This will remove "
            "temporary data from memory and return you to the login screen.",
            "لأجل الخصوصية يمكنك مسح الجلسة بعد الانتهاء. هذا سيزيل البيانات المؤقتة "
            "ويعيدك إلى شاشة تسجيل الدخول.",
        )
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button(_t("Clear Session (Privacy)", "مسح الجلسة (للخصوصية)"), use_container_width=True):
            try:
                st.session_state.clear()
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception:
                pass
            st.success(_t("Session cleared. Please sign in again.", "تم مسح الجلسة. سجل الدخول مرة أخرى."))
            st.rerun()
    with col_p2:
        if st.button(_t("Clear Cache", "مسح الكاش"), use_container_width=True):
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
            except Exception:
                pass
            st.success(_t("Cache cleared.", "تم مسح الكاش."))
