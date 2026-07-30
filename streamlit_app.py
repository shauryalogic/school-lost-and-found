# import streamlit as st

# st.set_page_config(page_title="School Lost & Found", page_icon="🎒")

# if "is_staff" not in st.session_state:
#     st.session_state.is_staff = False


# def staff_login():
#     st.title("🔑 Staff sign-in")
#     code = st.text_input("Staff passcode", type="password")
#     if st.button("Sign in"):
#         if code == st.secrets.get("STAFF_PASSCODE"):
#             st.session_state.is_staff = True
#             st.rerun()
#         else:
#             st.error("That passcode isn't right.")


# def staff_logout():
#     st.session_state.is_staff = False
#     st.rerun()


# parent_page = st.Page("views/parent.py", title="Find an item", icon="🔎", default=True)
# staff_page = st.Page("views/staff.py", title="Staff Page", icon="📋")
# login_page = st.Page(staff_login, title="Staff sign-in", icon="🔑")
# logout_page = st.Page(staff_logout, title="Sign out", icon="🚪")

# pages = [parent_page]
# if st.session_state.is_staff:
#     pages += [staff_page, logout_page]
# else:
#     pages.append(login_page)

# st.navigation(pages).run()
import streamlit as st

from db import sign_in, sign_up, sign_out

st.set_page_config(page_title="FoundYou", page_icon="🧸")


def login_page():
    st.title("🧸 FoundYou")
    st.caption("Reuniting kids with what they've lost")
    tab_login, tab_signup = st.tabs(["Log in", "Create account"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Log in"):
            try:
                sign_in(email, password)
                st.rerun()
            except Exception:
                st.error("That email or password isn't right.")

    with tab_signup:
            st.caption("For parents. You'll need the code your school sent you.")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (at least 6 characters)", type="password", key="signup_pw")
            school_code = st.text_input("School code", key="signup_code")
            if st.button("Create account"):
                # check the code FIRST — no account is created unless it matches
                if school_code.strip() != st.secrets.get("SCHOOL_CODE"):
                    st.error("That school code isn't right. Please check the code your school sent you.")
                else:
                    try:
                        sign_up(email, password)
                        sign_in(email, password)
                        st.rerun()
                    except Exception:
                        st.error("Couldn't create that account. Try a different email.")


def logout_page():
    sign_out()
    st.rerun()


# Decide what pages exist based on who is logged in.
role = st.session_state.get("role")

if role is None:
    # Not logged in — the ONLY reachable page is the login screen.
    st.navigation([st.Page(login_page, title="Log in")]).run()

elif role == "staff":
    st.navigation([
        st.Page("views/staff.py", title="Staff", icon="📋"),
        st.Page(logout_page, title="Sign out", icon="🚪"),
    ]).run()

else:  # parent
    st.navigation([
        st.Page("views/parent.py", title="Find an item", icon="🔎"),
        st.Page(logout_page, title="Sign out", icon="🚪"),
    ]).run()