import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account)  # Use your provided service account JSON here
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Add Client function using Firebase Firestore
def add_client(email, expiry_date, permissions):
    username = email.split('@')[0]
    client_data = {
        'username': username,
        'password': "",  # Store generated password here
        'expiry_date': expiry_date.strftime('%Y-%m-%d'),
        'permissions': permissions,
        'email': email,
        'login_status': 0
    }
    db.collection('clients').document(username).set(client_data)

# Admin Dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Add approved emails with permissions and expiry dates for client access.")
    
    # Input for client details
    email = st.text_input("Enter client's email for account creation approval:")
    expiry_date = st.date_input("Set expiry date for the client", value=datetime(2024, 12, 31))
    dashboards = st.multiselect("Dashboards to provide access to:", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'])

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date, dashboards)
            st.success(f"Client with email '{email}' added successfully!")
        else:
            st.error("Please provide an email and select at least one dashboard.")
    
    # Display all clients from Firestore
    st.write("---")
    clients = db.collection('clients').stream()
    st.write("### Approved Clients:")
    for client in clients:
        client_data = client.to_dict()
        login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
        st.write(f"**Username:** {client_data['username']} | **Email:** {client_data['email']} | **Expiry Date:** {client_data['expiry_date']} | **Dashboards Access:** {', '.join(client_data['permissions'])} | **Status:** {login_status}")
        
        # Reset login status for each client
        if login_status == "Logged In":
            if st.button(f"Reset Login Status for {client_data['username']}"):
                db.collection('clients').document(client_data['username']).update({"login_status": 0})
                st.success(f"Login status for {client_data['username']} has been reset.")

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
