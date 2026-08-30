# This is the staff side of the app. Staff do two things here:
# log new found items (with a photo) in the "Log items" tab, and manage
# existing items (release, cancel a reservation, or delete) in the "Manage items" tab.
# Items move through a simple state machine: available -> reserved -> released, and a
# reserved item can also be sent back to available (cancel). The Manage tab only ever
# shows the buttons that are valid from an item's current state.

import streamlit as st
import pandas as pd
from db import get_supabase, upload_photo, delete_photo
supabase = get_supabase()
from datetime import datetime, timezone


@st.dialog("Please confirm")
def confirm_status_change(item, new_status, message, clear_reservation=False):
    # Shared by Release and Cancel — both just change an item's status.
    st.write(message)
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")

    changes = {"status": new_status}
    if new_status == "released":
        changes["released_date"] = datetime.now(timezone.utc).isoformat()
    if clear_reservation:
        # Cancelling wipes the child's name off the item before it goes back in the pool.
        changes["reservation_comments"] = None
        changes["reservation_date"] = None

    back_col, go_col = st.columns(2)
    with back_col:
        if st.button("No, go back"):
            st.rerun()
    with go_col:
        if st.button("Yes, do it"):
            # .eq("id", ...) pins the update to exactly this one row. Without a filter like
            # this, an update would hit EVERY row in the table — so it's essential, not optional.
            supabase.table("items").update(changes).eq("id", item["id"]).execute()
            st.rerun()


@st.dialog("Delete this item?")
def confirm_delete(item):
    # Its own dialog — deleting is a different, permanent operation.
    st.write(f"**Item-Id #{item['item_number']} — {item['name']}**")
    st.warning("This permanently removes the item. It can't be undone.")

    back_col, del_col = st.columns(2)
    with back_col:
        if st.button("No, keep it"):
            st.rerun()
    with del_col:
        if st.button("Yes, delete"):
            # Delete the photo from storage FIRST, then the row — so no orphaned image is
            # left behind and no child's photo lingers after its record is gone.
            if item.get("photo_url"):
                delete_photo(item["photo_url"])
            supabase.table("items").delete().eq("id", item["id"]).execute()
            st.rerun()    
            

tab_log, tab_manage = st.tabs(["Log items", "Manage items"])

with tab_log:
    # The intake form. Photo and name are required; category / description / location are
    # optional so logging stays fast (a staff member can add an item in a few seconds).
    with st.form("item_entry", clear_on_submit=True):
        st.title("Log a found item")
        st.caption("\\* Required")
        photo = st.file_uploader("Item Photo *")
        name = st.text_input("Item Name *")
        category = st.text_input("Item Category (optional)")
        description = st.text_area("Item Description (optional)")
        location = st.text_input("Location Found (optional)")
        submitted = st.form_submit_button("Save item", type="primary")
    if submitted:
        # Check the two required fields before saving anything.
        if photo is None:
            st.error("Please add a photo — it's how parents spot their child's item.")
        elif not name.strip():
            st.error("Please add an item name so parents can recognize it.")
        else:
            # Upload the photo, get its URL back, then save the item row with that URL.
            # (status defaults to 'available' and the Item-Id auto-increments in the database.)
            photo_url = upload_photo(photo)
            supabase.table("items").insert({"name": name, "category": category, "description": description, "location_found": location, "photo_url": photo_url}).execute()
            st.success("Item logged! Parents can see it now.")
            
    # Below the form, show every item that's been logged so far, newest first.
    st.subheader("Logged items")
    result = supabase.table("items").select("*").order("created_at", desc=True).execute()
    items = result.data

    # I upgraded this from a plain st.dataframe to a paginated table that also
    # shows the photo as a thumbnail, so it's easier to scan when there are lots of items.
    if not items:
        st.info("No items logged yet. Add one above and it'll appear here.")
    else:
        df = pd.DataFrame(items)                              # dataframe = what column_config needs

        rows_per_page = 10
        total_pages = (len(df) + rows_per_page - 1) // rows_per_page
        page = st.pagination(num_pages=total_pages)           # native page buttons (1-indexed)
        start = (page - 1) * rows_per_page
        page_df = df.iloc[start:start + rows_per_page]        # just this page's slice

        st.dataframe(
            page_df,
            hide_index=True,
            column_order=["photo_url", "item_number", "name",
                        "category", "location_found", "date_found", "status"],
            column_config={
                "photo_url": st.column_config.ImageColumn("Photo"),
                "item_number": st.column_config.NumberColumn("Item-Id"),
                "name": st.column_config.TextColumn("Item"),
                "category": st.column_config.TextColumn("Category"),
                "location_found": st.column_config.TextColumn("Location Found"),
                "date_found": st.column_config.TextColumn("Date Found"),
                "status": st.column_config.TextColumn("Status"),
            },
        )

with tab_manage:
    st.subheader("Find an item")
    search = st.text_input(
        "Search",
        placeholder="Item-Id, item name, or who it's for",
        label_visibility="collapsed",
    )

    result = (
        supabase.table("items")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    all_items = result.data

    # Omni-search: one box matches across several fields at once, so staff can type an
    # Item-Id, an item name, or the note about who it's for. (On the STAFF side it's fine to
    # search reservation_comments; on the parent side I deliberately leave that field out,
    # because it holds children's names.)
    if search:
        s = search.lower()
        all_items = [
            it for it in all_items
            if s in str(it.get("item_number") or "").lower()
            or s in (it.get("name") or "").lower()
            or s in (it.get("description") or "").lower()
            or s in (it.get("reservation_comments") or "").lower()
            or s in (it.get("location_found") or "").lower()
        ]
        # Sort the results so reserved items come first, then available, then released.
        # Anything with an unknown status gets 9 so it falls to the bottom.
        STATUS_ORDER = {"reserved": 0, "available": 1, "released": 2}
        def rank(it):
            return STATUS_ORDER.get(it["status"], 9)
        all_items.sort(key=rank)
        

    if not all_items:
        st.info("No items match that search yet. Try a shorter word or check the spelling.")
    else:
        for item in all_items:
            with st.container(border=True):
                photo_col, text_col = st.columns([1, 2], vertical_alignment="center")
                with photo_col:
                    if item.get("photo_url"):
                        st.image(item["photo_url"], width="stretch")
                with text_col:
                    st.markdown(f"**{item['name']}**")
                    st.caption(
                        f"Item-Id #{item['item_number']} · {item.get('category') or '—'} "
                        f"· found in {item.get('location_found') or '—'}"
                    )
                    if item.get("reservation_comments"):
                        st.caption(f"Reserved for: {item['reservation_comments']}")

                    # a coloured status pill — the colour makes state scannable at a glance
                    STATUS_COLOR = {
                        "reserved": "orange",
                        "available": "green",
                        "released": "gray",
                    }
                    st.badge(
                        item["status"].title(),
                        color=STATUS_COLOR.get(item["status"], "gray"),
                    )

                # Show only the buttons valid for this item's state.
                # A released item is finished, so it only offers Delete;
                # an invalid jump is impossible because that button simply isn't drawn.
                if item["status"] == "reserved":
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("Release", key=f"rel_{item['id']}", icon=":material/check_circle:", width="stretch"):
                            confirm_status_change(
                                item, "released", "Release this item to the family?"
                            )
                    with c2:
                        if st.button("Cancel reservation", key=f"cxl_{item['id']}", icon=":material/undo:", width="stretch"):
                            confirm_status_change(
                                item, "available",
                                "Cancel this reservation and return the item?",
                                clear_reservation=True,
                            )
                    with c3:
                        if st.button("Delete", key=f"del_{item['id']}", icon=":material/delete:", width="stretch"):
                            confirm_delete(item)

                elif item["status"] == "available":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Release", key=f"rel_{item['id']}", icon=":material/check_circle:", width="stretch"):
                            confirm_status_change(
                                item, "released", "Release this item?"
                            )
                    with c2:
                        if st.button("Delete", key=f"del_{item['id']}", icon=":material/delete:", width="stretch"):
                            confirm_delete(item)

                else:  # released — no primary action, just cleanup
                    if st.button("Delete", key=f"del_{item['id']}", icon=":material/delete:", width="stretch"):
                        confirm_delete(item)


