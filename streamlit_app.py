import streamlit as st

st.set_page_config(page_title="School Lost & Found", page_icon="🎒")

if "is_staff" not in st.session_state:
    st.session_state.is_staff = False


def staff_login():
    st.title("🔑 Staff sign-in")
    code = st.text_input("Staff passcode", type="password")
    if st.button("Sign in"):
        if code == st.secrets.get("STAFF_PASSCODE"):
            st.session_state.is_staff = True
            st.rerun()
        else:
            st.error("That passcode isn't right.")


def staff_logout():
    st.session_state.is_staff = False
    st.rerun()


parent_page = st.Page("views/parent.py", title="Find an item", icon="🔎", default=True)
staff_page = st.Page("views/staff.py", title="Staff Page", icon="📋")
login_page = st.Page(staff_login, title="Staff sign-in", icon="🔑")
logout_page = st.Page(staff_logout, title="Sign out", icon="🚪")

pages = [parent_page]
if st.session_state.is_staff:
    pages += [staff_page, logout_page]
else:
    pages.append(login_page)

st.navigation(pages).run()