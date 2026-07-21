#import streamlit as st
#st.title("School Lost & Found")
#st.write("If it's lost, we'll help you find it.")
#st.write("happy happy happy happy")


import streamlit as st
from supabase import create_client
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

with st.form("item_entry"):
    st.title("Item Entry Form")
    name = st.text_input("Item Name")
    category = st.text_input("Item Category")
    description = st.text_area("Item Description")
    location = st.text_input("Location Found")
    submitted = st.form_submit_button("Save")
if submitted:
    if not name.strip():
        st.error("Please enter an item name.")
    else:
        supabase.table("items").insert({"name": name, "category": category, "description": description, "location_found": location}).execute()
        st.write("Item Entered Sucessfully")

# The list (Task B):
st.subheader("Logged items")
result = supabase.table("items").select("*").order("created_at", desc=True).execute()
st.dataframe(result.data)