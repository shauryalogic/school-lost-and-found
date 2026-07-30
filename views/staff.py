#import streamlit as st
#st.title("School Lost & Found")
#st.write("If it's lost, we'll help you find it.")
#st.write("happy happy happy happy")

import streamlit as st
from db import get_supabase, upload_photo
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
        changes["reservation_comments"] = None
        changes["reservation_date"] = None

    back_col, go_col = st.columns(2)
    with back_col:
        if st.button("No, go back"):
            st.rerun()
    with go_col:
        if st.button("Yes, do it"):
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
            supabase.table("items").delete().eq("id", item["id"]).execute()
            st.rerun()

tab_log, tab_manage = st.tabs(["Log items", "Manage items"])

with tab_log:
    with st.form("item_entry", clear_on_submit=True):
        st.title("Staff - Item Entry Form")
        photo = st.file_uploader("Item Photo")
        name = st.text_input("Item Name")
        category = st.text_input("Item Category")
        description = st.text_area("Item Description")
        location = st.text_input("Location Found")
        submitted = st.form_submit_button("Save")
    if submitted:
        if not name.strip():
            st.error("Please enter an item name.")
        elif photo is None:
            st.error("A photo is required to log an item")
        else:
            photo_url = upload_photo(photo)
            supabase.table("items").insert({"name": name, "category": category, "description": description, "location_found": location, "photo_url": photo_url}).execute()
            st.write("Item Entered Sucessfully") 
            

    # The list :
    import pandas as pd
    st.subheader("Logged items")
    result = supabase.table("items").select("*").order("created_at", desc=True).execute()
    items = result.data
    #st.dataframe(result.data) below code upgared from standard datafarem to pagination and thumbnail
    if not items:
        st.info("No items logged yet.")
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

    # Omni-search: one box matches across several fields.
    if search:
        s = search.lower()
        all_items = [
            it for it in all_items
            if s in str(it.get("item_number") or "").lower()
            or s in (it.get("name") or "").lower()
            or s in (it.get("description") or "").lower()
            or s in (it.get("reservation_comments") or "").lower()
        ]
        #below lines sort the all_items in status of orders. It assigns value 9 if no status is found
        STATUS_ORDER = {"reserved": 0, "available": 1, "released": 2}
        def rank(it):
            return STATUS_ORDER.get(it["status"], 9)
        all_items.sort(key=rank)
        

    if not all_items:
        st.info("No items match that search.")
    else:
        for item in all_items:
            with st.container(border=True):
                photo_col, text_col = st.columns([1, 2])
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
                        st.caption(f"For: {item['reservation_comments']}")

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
                if item["status"] == "reserved":
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("Release", key=f"rel_{item['id']}"):
                            confirm_status_change(
                                item, "released", "Release this item to the family?"
                            )
                    with c2:
                        if st.button("Cancel reservation", key=f"cxl_{item['id']}"):
                            confirm_status_change(
                                item, "available",
                                "Cancel this reservation and return the item?",
                                clear_reservation=True,
                            )
                    with c3:
                        if st.button("Delete", key=f"del_{item['id']}"):
                            confirm_delete(item)

                elif item["status"] == "available":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Release", key=f"rel_{item['id']}"):
                            confirm_status_change(
                                item, "released", "Release this item?"
                            )
                    with c2:
                        if st.button("Delete", key=f"del_{item['id']}"):
                            confirm_delete(item)

                else:  # released — no primary action, just cleanup
                    if st.button("Delete", key=f"del_{item['id']}"):
                        confirm_delete(item)


