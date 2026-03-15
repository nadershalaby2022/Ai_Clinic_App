import pandas as pd
import streamlit as st

from core.utils_auth import list_guest_logins


def render_admin_accounts_page() -> None:
    st.header("Admin Account Management")
    st.caption("Guest logins captured from the demo access flow.")

    rows = list_guest_logins()
    if not rows:
        st.info("No guest logins recorded yet.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Guest Logins (CSV)",
        data=csv_data,
        file_name="guest_logins.csv",
        mime="text/csv",
        use_container_width=True,
    )
