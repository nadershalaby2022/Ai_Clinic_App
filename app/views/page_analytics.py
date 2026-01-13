# app/pages/page_analytics.py
import streamlit as st

from core.utils_analytics import (
    analysis_a1,
    analysis_a2,
    analysis_a3,
)


def render_analytics_page(engine):
    st.header("📊 تحليلات العيادة")

    data_merged = engine["data_merged"]

    tab1, tab2, tab3 = st.tabs(
        [
            "A-1 أفضل دواء لكل تشخيص",
            "A-2 نسبة الشفاء حسب الأعراض",
            "A-3 فعالية الدواء الشاملة",
        ]
    )

    with tab1:
        st.subheader("A-1 Drug effectiveness per Diagnosis")
        st.dataframe(analysis_a1(data_merged))

    with tab2:
        st.subheader("A-2 Cure rate by Diagnosis + Chief Complaint")
        st.dataframe(analysis_a2(data_merged))

    with tab3:
        st.subheader("A-3 Drug speed + reliability + effectiveness score")
        st.dataframe(analysis_a3(data_merged))
