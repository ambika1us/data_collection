import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import datetime
import re
import io

# --- MongoDB Connection ---
@st.cache_resource
def init_connection():
    uri = f"mongodb+srv://{st.secrets['mongo']['username']}:{st.secrets['mongo']['password']}@{st.secrets['mongo']['host']}/?retryWrites=true&w=majority&appName=Cluster0"
    return MongoClient(uri, server_api=ServerApi('1'))

client = init_connection()
db = client["user_db"]
collection = db["user_data"]

# --- Page Setup ---
st.set_page_config(page_title="User Form & Admin Dashboard", layout="centered")
st.title("📋 User Information Form")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- Email Validation ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- User Form ---
with st.form("user_form"):
    st.subheader("Submit Your Info")
    name = st.text_input("Name")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    dob = st.date_input(
        "Date of Birth",
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.date(datetime.datetime.now().year, 12, 31)
    )
    submitted = st.form_submit_button("Submit")

    if submitted:
        if not all([name, email, mobile]) or not is_valid_email(email):
            st.error("Please enter valid details.")
        elif collection.find_one({'email': email}):
            st.warning("Email already exists in the database.")
        else:
            collection.insert_one({
                'name': name,
                'email': email,
                'mobile': mobile,
                'dob': dob.strftime("%Y-%m-%d")
            })
            st.success(f"Thank you, {name}. Your data has been saved!")

# --- Admin Dashboard ---
if st.session_state.logged_in:
    st.markdown("---")
    st.subheader("📊 Admin Dashboard")

    users = list(collection.find({}, {'_id': 0}))
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df)

        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="user_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No submissions yet.")