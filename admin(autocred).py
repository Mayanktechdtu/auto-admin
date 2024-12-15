import streamlit as st
from datetime import datetime, timedelta
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

# Function to add a client with email, expiry date, and permissions
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
    st.success(f"Client with email '{email}' added successfully! Expiry date: {expiry_date}")

# Function to update login status (active/inactive)
def update_login_status(username, status):
    db_firestore.collection('clients').document(username).update({'login_status': status})
    st.success(f"Login status for {username} has been reset.")

# Function to create a colored dot for status
def status_dot(color):
    return f"<span style='height: 10px; width: 10px; background-color: {color}; border-radius: 50%; display: inline-block;'></span>"

# Admin Dashboard Interface
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Add approved emails with permissions and expiry dates for client access.")

    # Section to add a new client's email, permissions, and expiry date
    email = st.text_input("Enter client's email for account creation approval:")
    expiry_option = st.selectbox("Select expiry duration:", ['1 Month', '3 Months', '6 Months'])
    dashboards = st.multiselect("Dashboards to provide access to:", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'])

    # Calculate expiry date based on the selected option
    if expiry_option == '1 Month':
        expiry_date = (datetime.now() + timedelta(days=30)).date()
    elif expiry_option == '3 Months':
        expiry_date = (datetime.now() + timedelta(days=90)).date()
    elif expiry_option == '6 Months':
        expiry_date = (datetime.now() + timedelta(days=180)).date()

    # Display calculated expiry date
    st.write(f"Calculated Expiry Date: **{expiry_date}**")

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date.strftime('%Y-%m-%d'), dashboards)
        else:
            st.error("Please provide an email and select at least one dashboard.")

    st.write("---")

    # Search functionality
    st.subheader("Search Clients")
    search_query = st.text_input("Enter username to search:")
    
    # Fetch clients from Firestore
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]

    # Filter clients based on search query
    if search_query:
        filtered_clients = [client for client in clients_data if search_query.lower() in client['username'].lower()]
        if not filtered_clients:
            st.warning("No clients found with the given username.")
    else:
        filtered_clients = clients_data

    # Display filtered clients
    if filtered_clients:
        st.write("### Approved Clients:")

        # Create headers for the table
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 1, 1])
        with col1:
            st.markdown("**Username**")
        with col2:
            st.markdown("**Email**")
        with col3:
            st.markdown("**Expiry Date**")
        with col4:
            st.markdown("**Dashboards**")
        with col5:
            st.markdown("**Status**")
        with col6:
            st.markdown("**Action**")

        # Display each client's data in a row
        for client_data in filtered_clients:
            login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
            status_color = "green" if login_status == "Logged In" else "red"

            # Ensure text comes in a single line by avoiding line breaks
            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 1, 1])
            with col1:
                st.write(client_data['username'])
            with col2:
                st.write(client_data['email'])
            with col3:
                st.write(client_data['expiry_date'])
            with col4:
                st.write(", ".join(client_data['permissions']))
            with col5:
                st.markdown(f"{status_dot(status_color)} {login_status}", unsafe_allow_html=True)
            with col6:
                if login_status == "Logged In":
                    if st.button("Reset", key=f"reset_{client_data['username']}"):
                        update_login_status(client_data['username'], 0)
                        st.experimental_rerun()
                else:
                    st.write("-")

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
