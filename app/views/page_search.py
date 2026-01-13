# app/pages/page_search.py
import streamlit as st
import pandas as pd


def render_search_page(engine):
    st.header("🔍 بحث عن مريض")

    patients = engine["patients"]
    visits = engine["visits"]
    visit_drugs = engine["visit_drugs"]

    col1, col2 = st.columns(2)

    with col1:
        pid_search = st.number_input(
            "بحث برقم المريض (Patient ID)", step=1, min_value=0
        )
        btn_pid = st.button("بحث بالرقم")

    with col2:
        name_search = st.text_input("بحث بالاسم (أول جزء من الاسم)")
        btn_name = st.button("بحث بالاسم")

    result_patients = pd.DataFrame()

    if btn_pid and pid_search > 0:
        result_patients = patients[patients["Patient_ID"] == pid_search]

    if btn_name and name_search.strip():
        result_patients = patients[
            patients["Patient_Name"].str.contains(name_search, case=False, na=False)
        ]

    if result_patients.empty:
        st.info("لم يتم العثور على نتائج بعد.")
        return

    st.subheader("📋 نتائج البحث عن المريض")
    st.dataframe(result_patients)

    # لو عندنا مريض واحد فقط، نعرض ملفه بالتفصيل
    if len(result_patients) == 1:
        row = result_patients.iloc[0]
        sel_id = row["Patient_ID"]
        st.markdown("---")
        st.subheader(f"📌 ملف المريض رقم {sel_id}")

        st.markdown(
            f"""
**الاسم:** {row['Patient_Name']}  
**النوع:** {row['Gender']}  
**تاريخ الميلاد:** {row['DOB']}  
**الهاتف:** {row['Phone_Number']}  
**ولي الأمر:** {row['Parent_Name']}  
**العنوان:** {row['Address']}  
**الحساسية:** {row['Allergies']}  
**ملاحظات:** {row['Notes']}  
"""
        )

        st.markdown("### 🩺 زيارات المريض")
        v = visits[visits["Patient_ID"] == sel_id].sort_values("Visit_Date")
        st.dataframe(v)

        st.markdown("### 💊 كل الأدوية التي وصفت للمريض")
        merged = (
            visit_drugs.merge(visits, on="Visit_ID", how="left")
            .merge(patients, on="Patient_ID", how="left")
        )
        d = merged[merged["Patient_ID"] == sel_id].sort_values(
            ["Visit_Date", "Line_No"]
        )
        st.dataframe(d)
