import uuid

import streamlit as st
from supabase import create_client



def _new_client():
    # Build a fresh Supabase client.
    # We do NOT cache this anymore. Before auth, one shared client was fine because
    # everyone was anonymous. Now the client carries WHO is logged in, so a shared
    # client would leak one person's login to everyone. Each run gets its own.
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_supabase():
    # The client the pages use. If someone is logged in, we attach their login
    # so the database knows who is asking (that's what makes the RLS rules work).
    client = _new_client()
    if "access_token" in st.session_state:
        client.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token,
        )
    return client


def current_user():
    # The logged-in user's id, or None. Used to stamp/read reservations.
    return st.session_state.get("user_id")


def sign_up(email, password):
    # Create a new parent account. The database trigger makes them a 'parent'.
    _new_client().auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"school_id": st.secrets["SCHOOL_ID"]}},
    })


def sign_in(email, password):
    # Log in, then remember the tokens and who they are for THIS browser session.
    client = _new_client()
    result = client.auth.sign_in_with_password({"email": email, "password": password})

    st.session_state.access_token = result.session.access_token
    st.session_state.refresh_token = result.session.refresh_token
    st.session_state.user_id = result.user.id

    # Look up their role once (parent or staff) and remember it.
    profile = (
        get_supabase().table("profiles")
        .select("role").eq("id", result.user.id).single().execute()
    )
    st.session_state.role = profile.data["role"]


def sign_out():
    # Forget everything about this browser's login.
    for key in ["access_token", "refresh_token", "user_id", "role"]:
        st.session_state.pop(key, None)

def upload_photo(photo_file):
    # Build a client and log it in with the current user's wristband,
    # so BOTH the database part and the storage part carry the login.
    client = _new_client()
    client.auth.set_session(
        st.session_state.access_token,
        st.session_state.refresh_token,
    )

    image_bytes = photo_file.getvalue()
    content_type = photo_file.type or "image/jpeg"
    extension = content_type.split("/")[-1]
    file_name = f"{uuid.uuid4()}.{extension}"

    client.storage.from_("item-photos").upload(
        file_name,
        image_bytes,
        {"content-type": content_type},
    )
    return client.storage.from_("item-photos").get_public_url(file_name)

#delete photo
def delete_photo(photo_url):
    # Storage needs its OWN freshly-authenticated client — the same reason upload_photo does.
    # set_session reaches the database client but not the storage client, so without this
    # the delete goes out anonymous and is silently refused.
    client = _new_client()
    client.auth.set_session(
        st.session_state.access_token,
        st.session_state.refresh_token,
    )
    file_name = photo_url.split("/")[-1]
    client.storage.from_("item-photos").remove([file_name])