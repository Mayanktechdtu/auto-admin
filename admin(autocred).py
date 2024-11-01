import streamlit as st
from datetime import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin for Firestore
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["service_account"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to add a client to Firestore
def add_client(email, expiry_date, permissions):
    username = email.split('@')[0]
    client_data = {
        "username": username,
        "expiry_date": expiry_date,
        "permissions": permissions,
        "email": email,
        "login_status": False
    }
    db.collection("clients").document(username).set(client_data)

# Function to update login status
def update_login_status(username, status):
    db.collection("clients").document(username).update({"login_status": status})

# Admin Dashboard Interface
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Add clients with permissions and expiry dates.")

    # Form for adding clients
    email = st.text_input("Enter client's email:")
    expiry_date = st.date_input("Set expiry date", value=datetime(2024, 12, 31))
    dashboards = st.multiselect("Dashboards to provide access to:", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4'])

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date.strftime('%Y-%m-%d'), dashboards)
            st.success(f"Client with email '{email}' added successfully!")
        else:
            st.error("Please provide an email and select at least one dashboard.")

    st.write("---")
    # Display clients
    clients = db.collection("clients").stream()
    st.write("### Approved Clients:")
    for client in clients:
        client_data = client.to_dict()
        login_status = "Logged In" if client_data['login_status'] else "Logged Out"
        st.write(f"**Username:** {client_data['username']} | **Email:** {client_data['email']} | **Expiry Date:** {client_data['expiry_date']} | **Permissions:** {client_data['permissions']} | **Status:** {login_status}")

        if login_status == "Logged In" and st.button(f"Reset Login Status for {client_data['username']}"):
            update_login_status(client_data['username'], False)
            st.success(f"Login status for {client_data['username']} has been reset.")

if __name__ == "__main__":
    admin_dashboard()
