from datetime import datetime, timezone

import streamlit as st

from db import get_supabase

supabase = get_supabase()

if "my_reservations" not in st.session_state:
    st.session_state.my_reservations = []

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
                }
            ).eq("id", item["id"]).execute()
            st.session_state.my_reservations.append(item["id"])
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
                }
            ).eq("id", item["id"]).execute()
            st.session_state.my_reservations.remove(item["id"])
            st.rerun()


def item_card(item, button_label, button_key, on_click, extra_line=None):
    with st.container(border=True):
        photo_col, text_col = st.columns([1, 2])
        with photo_col:
            if item.get("photo_url"):
                st.image(item["photo_url"], width=110)
        with text_col:
            st.markdown(f"**{item['name']}**")
            st.caption(f"Item-Id #{item['item_number']} · {item.get('category') or '—'}")
            st.caption(
                f"{item.get('location_found') or '—'} · found {item.get('date_found') or '—'}"
            )
            if extra_line:
                st.caption(extra_line)
        if st.button(button_label, key=button_key):
            on_click(item)


count = len(st.session_state.my_reservations)
tab_all, tab_mine = st.tabs(["All items", f"My reservations ({count})"])

with tab_all:
    result = (
        supabase.table("items")
        .select("*")
        .eq("status", "available")
        .order("created_at", desc=True)
        .execute()
    )
    items = result.data

    if not items:
        st.info("No items are available right now.")
    else:
        per_page = 5
        total_pages = (len(items) + per_page - 1) // per_page
        page = st.pagination(num_pages=total_pages) if total_pages > 1 else 1
        start = (page - 1) * per_page

        for item in items[start : start + per_page]:
            item_card(
                item,
                "Reserve this item",
                f"reserve_{item['id']}",
                reserve_dialog,
            )

with tab_mine:
    ids = st.session_state.my_reservations
    if not ids:
        st.info("You haven't reserved anything yet.")
    else:
        result = (
            supabase.table("items")
            .select("*")
            .in_("id", ids)
            .eq("status", "reserved")
            .execute()
        )
        mine = result.data

        if not mine:
            st.info("Your reservations have been collected or released.")
        else:
            st.success("Show the Item-Id at the front desk to collect.")
            for item in mine:
                item_card(
                    item,
                    "Un-reserve",
                    f"unreserve_{item['id']}",
                    unreserve_dialog,
                    extra_line=f"For: {item.get('reservation_comments') or '—'}",
                )