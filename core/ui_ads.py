from pathlib import Path

import streamlit as st

from core.branding import load_branding


def render_vip_sponsors() -> None:
    branding = load_branding()
    sponsors = branding.get("vip_sponsors", [])
    st.subheader("VIP Sponsors")
    cols = st.columns(3)
    for idx, ad in enumerate(sponsors[:3]):
        with cols[idx % 3]:
            image_path = Path(ad.get("image", ""))
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)
            else:
                st.info(ad.get("title", f"VIP Sponsor {idx+1}"))
            title = ad.get("title", "VIP Sponsor")
            url = ad.get("url", "")
            if url:
                st.markdown(f"[{title}]({url})")
            else:
                st.markdown(title)


def render_sponsor_sidebar() -> None:
    branding = load_branding()
    sponsors = branding.get("sponsors", [])
    st.sidebar.markdown("---")
    st.sidebar.subheader("Sponsors")
    for ad in sponsors:
        image_path = Path(ad.get("image", ""))
        if image_path.exists():
            st.sidebar.image(str(image_path), caption=ad.get("title", "Sponsor"), use_container_width=True)
        title = ad.get("title", "Sponsor")
        url = ad.get("url", "")
        if url:
            st.sidebar.markdown(f"[{title}]({url})")
        else:
            st.sidebar.markdown(title)


def render_sponsor_footer() -> None:
    branding = load_branding()
    sponsors = branding.get("sponsors", [])
    st.markdown("---")
    st.subheader("Sponsors")
    cols = st.columns(4)
    for idx, ad in enumerate(sponsors[:4]):
        with cols[idx % 4]:
            image_path = Path(ad.get("image", ""))
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)
            title = ad.get("title", "Sponsor")
            url = ad.get("url", "")
            if url:
                st.markdown(f"[{title}]({url})")
            else:
                st.markdown(title)
