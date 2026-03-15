from pathlib import Path

import streamlit as st

from core.branding import load_branding, save_branding


def _save_uploaded_image(uploaded_file, destination: str) -> None:
    if uploaded_file is None:
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(uploaded_file.getbuffer())


def render_sponsors_page() -> None:
    st.header("Sponsors Management")
    st.caption("Update sponsor images and links used across the app.")

    data = load_branding()

    st.subheader("Sponsors (4)")
    sponsors = data.get("sponsors", [])
    while len(sponsors) < 4:
        idx = len(sponsors) + 1
        sponsors.append(
            {"title": f"Sponsor {idx}", "image": f"assets/sponsors/sponsor_{idx}.png", "url": "https://example.com"}
        )

    updated_sponsors = []
    sponsor_uploads = []
    for idx in range(4):
        st.markdown(f"**Sponsor {idx + 1}**")
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input(f"Title {idx + 1}", value=sponsors[idx].get("title", ""), key=f"s_title_{idx}")
            url = st.text_input(f"URL {idx + 1}", value=sponsors[idx].get("url", ""), key=f"s_url_{idx}")
        with col2:
            image_path = sponsors[idx].get("image", f"assets/sponsors/sponsor_{idx+1}.png")
            st.caption(f"Path: {image_path}")
            image_file = st.file_uploader(
                f"Image {idx + 1}",
                type=["png", "jpg", "jpeg"],
                key=f"s_img_{idx}",
            )
        updated_sponsors.append({"title": title, "url": url, "image": image_path})
        sponsor_uploads.append((image_file, image_path))

    st.subheader("VIP Sponsors (3)")
    vip = data.get("vip_sponsors", [])
    while len(vip) < 3:
        idx = len(vip) + 1
        vip.append(
            {"title": f"VIP Sponsor {idx}", "image": f"assets/vip_sponsors/vip_{idx}.png", "url": "https://example.com"}
        )

    updated_vip = []
    vip_uploads = []
    for idx in range(3):
        st.markdown(f"**VIP Sponsor {idx + 1}**")
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input(f"VIP Title {idx + 1}", value=vip[idx].get("title", ""), key=f"v_title_{idx}")
            url = st.text_input(f"VIP URL {idx + 1}", value=vip[idx].get("url", ""), key=f"v_url_{idx}")
        with col2:
            image_path = vip[idx].get("image", f"assets/vip_sponsors/vip_{idx+1}.png")
            st.caption(f"Path: {image_path}")
            image_file = st.file_uploader(
                f"VIP Image {idx + 1}",
                type=["png", "jpg", "jpeg"],
                key=f"v_img_{idx}",
            )
        updated_vip.append({"title": title, "url": url, "image": image_path})
        vip_uploads.append((image_file, image_path))

    if st.button("Save Sponsors", use_container_width=True):
        for file_obj, image_path in sponsor_uploads:
            _save_uploaded_image(file_obj, image_path)
        for file_obj, image_path in vip_uploads:
            _save_uploaded_image(file_obj, image_path)

        payload = {
            "sponsors": updated_sponsors,
            "vip_sponsors": updated_vip,
        }
        save_branding(payload)
        st.success("Sponsors updated.")
