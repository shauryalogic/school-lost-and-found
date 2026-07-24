#import streamlit as st
#st.title("School Lost & Found")
#st.write("If it's lost, we'll help you find it.")
#st.write("happy happy happy happy")

import streamlit as st
from db import get_supabase, upload_photo
supabase = get_supabase()



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




