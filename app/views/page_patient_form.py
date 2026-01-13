# app/views/page_patient_form.py

import streamlit as st

from core.utils_data import (
    get_next_patient_id,
    save_patient,
)


def render_patient_form_page(file_path, engine=None):
    st.header("👶 إدخال بيانات مريض جديد")
    st.markdown("---")

    # نحسب Patient_ID الجديد أوتوماتيك من ملف الإكسل
    new_id = get_next_patient_id(file_path)
    st.info(f"سيتم تسجيل المريض برقم: **{new_id}**")

    with st.form("patient_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("اسم المريض (Patient Name)")
            gender = st.selectbox("النوع (Gender)", ["Male", "Female"])
            dob = st.date_input("تاريخ الميلاد (Date of Birth)")

        with col2:
            phone = st.text_input("رقم الهاتف (Phone Number)")
            parent_name = st.text_input("اسم ولي الأمر (Parent Name)")
            address = st.text_input("العنوان (Address)")

        allergies = st.text_input("الحساسية (Allergies) – اختياري")
        notes = st.text_area("ملاحظات إضافية (Notes) – اختياري")

        submitted = st.form_submit_button("💾 حفظ المريض")

    if submitted:
        if not name.strip():
            st.error("من فضلك أدخل اسم المريض.")
            return

        row = {
            "Patient_ID": int(new_id),
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
        except Exception as e:
            st.error(f"حدث خطأ أثناء حفظ المريض في ملف الإكسل: {e}")
            return

        st.success(f"تم حفظ المريض برقم {new_id} بنجاح ✅")

        # تنظيف الكاش علشان بقية الصفحات تشوف التعديل
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
        except Exception:
            pass

        # إعادة تحميل الصفحة
        st.rerun()
