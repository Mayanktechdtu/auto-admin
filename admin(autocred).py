import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK using Streamlit secrets
if not firebase_admin._apps:
    firebase_cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(firebase_cred)
db_firestore = firestore.client()

# Function to add a client with email, expiry date, and permissions only
def add_client(email, expiry_date, permissions):
    username = email.split('@')[0]
    client_data = {
        'username': username,
        'password': '',  # Blank password initially
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'login_status': 0  # Default to logged out
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client with email '{email}' added successfully!")

# Function to update login status (active/inactive)
def update_login_status(username, status):
    db_firestore.collection('clients').document(username).update({'login_status': status})

# Admin Dashboard Interface
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Add approved emails with permissions and expiry dates for client access.")

    # Section to add a new client's email, permissions, and expiry date
    email = st.text_input("Enter client's email for account creation approval:")
    expiry_date = st.date_input("Set expiry date for the client", value=datetime(2024, 12, 31))
    dashboards = st.multiselect("Dashboards to provide access to:", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'])

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date.strftime('%Y-%m-%d'), dashboards)
        else:
            st.error("Please provide an email and select at least one dashboard.")

    st.write("---")

    # Display all clients with their email, permissions, and expiry dates
    clients_ref = db_firestore.collection('clients').stream()
    st.write("### Approved Clients:")
    for client in clients_ref:
        client_data = client.to_dict()
        login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
        st.write(f"**Username:** {client_data['username']} | **Email:** {client_data['email']} | **Expiry Date:** {client_data['expiry_date']} | **Dashboards Access:** {', '.join(client_data['permissions'])} | **Status:** {login_status}")
        
        # Add a button to reset the login status for each client
        if login_status == "Logged In":
            if st.button(f"Reset Login Status for {client_data['username']}"):
                update_login_status(client_data['username'], 0)
                st.success(f"Login status for {client_data['username']} has been reset.")
                st.experimental_rerun()  # Refresh to show updated status

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
