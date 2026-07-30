from datetime import datetime, timezone
import streamlit as st
from db import get_supabase, current_user


st.title("🔎 Find your child's item")

@st.dialog("Reserve this item")
def reserve_dialog(item):
    if item.get("photo_url"):
        st.image(item["photo_url"], width=200)
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")
    note = st.text_area("Who is this for?", placeholder="Maya, Room 12, Parent=Stacy")

    if st.button("Confirm reservation"):
        if not note.strip():
            st.error("Please tell us who this is for.")
        else:
            supabase.table("items").update(
                {
                    "status": "reserved",
                    "reservation_comments": note.strip(),
                    "reservation_date": datetime.now(timezone.utc).isoformat(),
                    "reserved_by": current_user(),
                }
            ).eq("id", item["id"]).execute()
            st.rerun()


@st.dialog("Cancel this reservation?")
def unreserve_dialog(item):
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")
    st.warning("This puts the item back for other families to find.")

    keep_col, cancel_col = st.columns(2)
    with keep_col:
        if st.button("Keep it"):
            st.rerun()
    with cancel_col:
        if st.button("Yes, un-reserve"):
            supabase.table("items").update(
                {
                    "status": "available",
                    "reservation_comments": None,
                    "reservation_date": None,
                    "reserved_by": None
                }
            ).eq("id", item["id"]).execute()
            st.rerun()


def item_card(item, button_label, button_key, extra_line=None):
    # One card design, used by both tabs. It draws the item and returns
    # True if its button was clicked — that's all. 
    with st.container(border=True):
        photo_col, text_col = st.columns([1, 2], vertical_alignment="center")
        with photo_col:
            if item.get("photo_url"):
                st.image(item["photo_url"], width="stretch")
        with text_col:
            st.markdown(f"**{item['name']}**")
            st.caption(f"Item-Id #{item['item_number']} · {item.get('category') or '—'}")
            st.caption(
                f"{item.get('location_found') or '—'} · found {item.get('date_found') or '—'}"
            )
            if extra_line:
                st.caption(extra_line)
        return st.button(button_label, key=button_key)

supabase = get_supabase()

# My reservations = items the database says I reserved.
mine = (
    supabase.table("items")
    .select("*")
    .eq("reserved_by", current_user())
    .eq("status", "reserved")
    .execute()
).data

tab_all, tab_mine = st.tabs(["All items", f"My reservations ({len(mine)})"])

with tab_all:
    query = st.text_input(
        "Search",
        placeholder="Search by name, description, or category",
        label_visibility="collapsed",
    )
    result = (
        supabase.table("items")
        .select("*")
        .eq("status", "available")
        .order("created_at", desc=True)
        .execute()
    )
    items = result.data

    # Parent search — only the public fields. NOT reservation_comments,
    # because that holds children's names and must never be searchable here.
    if query:
        q = query.lower()
        items = [
            it for it in items
            if q in str(it.get("item_number") or "").lower()
            or q in (it.get("name") or "").lower()
            or q in (it.get("description") or "").lower()
            or q in (it.get("category") or "").lower()
        ]

    if not items:
        st.info("No matching items are available right now.")
    else:
        per_page = 5
        total_pages = (len(items) + per_page - 1) // per_page
        page = st.pagination(num_pages=total_pages) if total_pages > 1 else 1
        start = (page - 1) * per_page

        for item in items[start : start + per_page]:
            if item_card(item, "Reserve this item", f"reserve_{item['id']}"):
                reserve_dialog(item)

with tab_mine:
    if not mine:
        st.info("You haven't reserved anything yet.")
    else:
        st.success("Show the Item-Id at the front desk to collect.")
        for item in mine:
            note_line = f"For: {item.get('reservation_comments') or '—'}"
            if item_card(item, "Un-reserve", f"unreserve_{item['id']}", extra_line=note_line):
                unreserve_dialog(item)