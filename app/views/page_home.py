# app/views/home.py
from pathlib import Path
import streamlit as st


def render_home_page():
    # ====== شوية CSS بسيط يخلي الصفحة شيك على شاشة العيادة ======
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 40px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
            text-align: right;
        }
        .subtitle {
            font-size: 16px;
            color: #4B5563;
            margin-top: 0;
            margin-bottom: 20px;
            text-align: right;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            background: #DBEAFE;
            color: #1D4ED8;
            border-radius: 999px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .hero-badge span.icon {
            margin-left: 6px;
        }
        .info-card {
            background: #FFFFFF;
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
            margin-bottom: 14px;
        }
        .section-title {
            font-size: 19px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 10px;
            text-align: right;
        }
        .label {
            color: #6B7280;
            font-weight: 500;
        }
        .value {
            color: #111827;
            font-weight: 600;
        }
        .bio-text {
            font-size: 13px;
            color: #4B5563;
            text-align: right;
            line-height: 1.7;
        }
        .footer-text {
            font-size: 11px;
            color: #9CA3AF;
            margin-top: 24px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ====== بادچ صغيرة في الأعلى ======
    st.markdown(
        """
        <div class="hero-badge">
            <span class="icon">🤖</span>
            Smart Pediatric Clinic Assistant
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ====== عنوان رئيسي ووصف صغير ======
    st.markdown(
        '<div class="main-title">Smart Pediatric Clinic Assistant</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p class="subtitle">
        نظام ذكي يساعد دكتور الأطفال في إدارة المرضى والزيارات والروشتات
        واتخاذ قرارات علاجية مدعومة بالبيانات والذكاء الاصطناعي.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ====== صف واحد: صورة الدكتور + بياناته ======
    col_img, col_info = st.columns([1, 1.1])

    # مسار الصورة من المجلد الرئيسي: pics/photo.jpg
    APP_DIR = Path(__file__).resolve().parents[1]   # app/
    BASE_DIR = APP_DIR.parent                       # المجلد الرئيسي
    img_path = BASE_DIR / "pics" / "photo.jpg"

    with col_img:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)

        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.warning("⚠️ لم يتم العثور على الصورة: pics/photo.jpg")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">👨‍⚕️ بيانات الطبيب</div>',
            unsafe_allow_html=True,
        )

        # عدّل البيانات دي براحتك
        st.markdown(
            """
            <p><span class="label">الاسم:</span> <span class="value">د/ __________</span></p>
            <p><span class="label">التخصص:</span> <span class="value">طب الأطفال وحديثي الولادة</span></p>
            <p><span class="label">سنوات الخبرة:</span> <span class="value">X سنة خبرة إكلينيكية</span></p>
            <p class="label">نبذة مختصرة:</p>
            <p class="bio-text">
                • تشخيص وعلاج أمراض الأطفال الحادة والمزمنة.<br>
                • متابعة التطعيمات والنمو والتغذية السليمة للأطفال.<br>
                • استخدام أدوات رقمية وذكاء اصطناعي لدعم القرار الطبي وتحسين جودة الخدمة المقدمة للمرضى.<br>
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ====== فوتر بسيط في الأسفل ======
    st.markdown(
        """
        <div class="footer-text">
            هذه الشاشة مخصصة للعرض داخل عيادة الطبيب، وتُظهر بيانات الطبيب مع مساعد ذكي لإدارة العيادة.
        </div>
        """,
        unsafe_allow_html=True,
    )
