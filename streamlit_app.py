# This is the app's front door. It runs first, shows the login screen if nobody
# is signed in, and once someone logs in it sends them to the right page based on
# their role: staff go to the staff page, parents go to the parent page.
import streamlit as st

from db import sign_in, sign_up, sign_out

st.set_page_config(page_title="FoundYou", page_icon="🧸")

# The login screen. Two tabs: existing users log in, and new parents create an
# account (which needs the school code, checked below before any account is made).
def login_page():
    st.title("🧸 FoundYou")
    st.caption("Reuniting kids with what they've lost")
    tab_login, tab_signup = st.tabs(["Log in", "Create account"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Log in", type="primary"):
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
            if st.button("Create account", type="primary"):
                # No account is created unless it matches. This is
                # the gate that stops random people from signing up and browsing a school's
                # items. The real school code lives in secrets, never written into the code itself.
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


# Decide what pages exist based on who is logged in. "role" is set during sign_in and
# comes from the profiles table in the database — it is either 'staff' or 'parent'.
role = st.session_state.get("role")

# Show the app logo only once someone is signed in (keeps the login screen clean).
if role is not None:
    st.logo(
        "assets/foundyou_logo.png",
        icon_image="assets/foundyou_icon.png",
        size="large",
    )


# This is the heart of the access control: I hand st.navigation ONLY the pages a given
# role is allowed to see. A page that isn't in the list can't be reached at all — not
# even by typing its URL — so a parent can never open the staff page.
if role is None:
    # Not logged in — the ONLY reachable page is the login screen.
    st.navigation([st.Page(login_page, title="Log in")]).run()

elif role == "staff":
    # Staff get the staff page (log + manage items) and a sign-out.
    st.navigation([
        st.Page("views/staff.py", title="Staff", icon=":material/inventory_2:"),
        st.Page(logout_page, title="Sign out", icon=":material/logout:"),
    ]).run()


else:  # parent
    # Parents get the find-and-reserve page and a sign-out — and nothing staff-only.
    st.navigation([
        st.Page("views/parent.py", title="Find an item", icon=":material/search:"),
        st.Page(logout_page, title="Sign out", icon=":material/logout:"),
    ]).run()