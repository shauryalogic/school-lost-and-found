# This is the parent side of the app: parents browse the available items,
# reserve one, and see their own reservations. Everything a parent can do
# lives on this page.
from datetime import datetime, timezone
import streamlit as st
from db import get_supabase, current_user


st.title("🔎 Find your child's item")

# Pop-up that lets a parent claim an item. The note field is required so staff
# know who to hand it to at pickup. Reserving flips the item to "reserved" and
# stamps who reserved it and when.
@st.dialog("Reserve this item")
def reserve_dialog(item):
    if item.get("photo_url"):
        st.image(item["photo_url"], width=200)
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")
    note = st.text_area("Who is this for?", placeholder="Maya, Room 12, Parent=Stacy")

    if st.button("Confirm reservation", type="primary"):
        if not note.strip():
            st.error("Please tell us who this is for.")
        else:
            # reserved_by = current_user() records that THIS parent made the reservation.
            # That one field powers the private "My reservations" list below and lets the
            # database guarantee one parent can't see or cancel another parent's reservation.
            # .eq("id", ...) makes the change apply to exactly this one item, no others.
            supabase.table("items").update(
                {
                    "status": "reserved",
                    "reservation_comments": note.strip(),
                    "reservation_date": datetime.now(timezone.utc).isoformat(),
                    "reserved_by": current_user(),
                }
            ).eq("id", item["id"]).execute()
            st.rerun()

# Pop-up to undo a reservation. It clears the reservation fields and sets the
# item back to "available" so another family can find it.
@st.dialog("Cancel this reservation?")
def unreserve_dialog(item):
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")
    st.warning("This puts the item back for other families to find.")

    keep_col, cancel_col = st.columns(2)
    with keep_col:
        if st.button("Keep it"):
            st.rerun()
    with cancel_col:
        if st.button("Yes, cancel"):
            # Setting reserved_by and the reservation fields back to None releases the item
            # AND scrubs the child's name from it, so nothing personal stays once it's
            # back in the public pool.
            supabase.table("items").update(
                {
                    "status": "available",
                    "reservation_comments": None,
                    "reservation_date": None,
                    "reserved_by": None
                }
            ).eq("id", item["id"]).execute()
            st.rerun()



def item_card(item, button_label, button_key, extra_line=None, button_type="secondary", button_icon=None):
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
        return st.button(button_label, key=button_key, type=button_type, icon=button_icon)

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
    # Only available items are ever fetched here, so a parent never even sees items that
    # someone else has already reserved.
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
        st.info("No items match that search yet — staff add new ones all the time, so check back soon.")
    else:
        # Show 5 items per page. The +per_page-1 is a rounding trick so a
        # leftover partial page still counts as one whole page.
        per_page = 5
        total_pages = (len(items) + per_page - 1) // per_page
        page = st.pagination(num_pages=total_pages) if total_pages > 1 else 1
        start = (page - 1) * per_page

        for item in items[start : start + per_page]:
            if item_card(item, "Reserve this item", f"reserve_{item['id']}", button_type="primary", button_icon=":material/bookmark_add:"):
                reserve_dialog(item)

with tab_mine:
    if not mine:
        st.info("No reservations yet. When you reserve an item, it'll show up here so you can pick it up.")
    else:
        st.success("Show the Item-Id on each item at the front desk to pick it up.")
        for item in mine:
            note_line = f"Reserved for: {item.get('reservation_comments') or '—'}"
            if item_card(item, "Cancel reservation", f"unreserve_{item['id']}", extra_line=note_line):
                unreserve_dialog(item)