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

# Function to add a new client
def add_client(email, expiry_date, permissions):
    username = email.split('@')[0]
    client_data = {
        'username': username,
        'password': '',
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'login_status': 0,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client '{email}' added successfully! Expiry Date: {expiry_date}")

# Function to update client details
def update_client(username, updated_email, updated_expiry, updated_permissions):
    db_firestore.collection('clients').document(username).update({
        'email': updated_email,
        'expiry_date': updated_expiry,
        'permissions': updated_permissions
    })
    st.success(f"Client '{username}' details updated successfully!")

# Function to reset login status
def update_login_status(username, status):
    db_firestore.collection('clients').document(username).update({'login_status': status})
    st.success(f"Login status for '{username}' has been reset.")

# Function to remove a client
def remove_client(username):
    db_firestore.collection('clients').document(username).delete()
    st.success(f"Client '{username}' has been removed successfully.")

# Admin Dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Manage client access, edit permissions, and expiry dates.")

    # Add a new client section
    st.subheader("Add New Client")
    email = st.text_input("Enter Client's Email:")
    expiry_option = st.selectbox("Select Expiry Duration:", ['1 Month', '3 Months', '6 Months'])
    dashboards = st.multiselect("Dashboards to Provide Access:", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'])

    if expiry_option == '1 Month':
        expiry_date = (datetime.now() + timedelta(days=30)).date()
    elif expiry_option == '3 Months':
        expiry_date = (datetime.now() + timedelta(days=90)).date()
    else:
        expiry_date = (datetime.now() + timedelta(days=180)).date()

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date.strftime('%Y-%m-%d'), dashboards)
            st.rerun()
        else:
            st.error("Please provide all required details.")

    st.write("---")

    # Fetch all clients
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]

    # Handle missing timestamps
    for client in clients_data:
        if 'created_at' not in client:
            client['created_at'] = '2000-01-01 00:00:00'

    # Display total clients
    st.subheader(f"Total Clients: {len(clients_data)}")

    # Display client logs
    for idx, client_data in enumerate(clients_data, start=1):
        with st.expander(f"**{idx}. {client_data['username']}** - {client_data['email']}"):
            st.write("### Client Details")
            st.write(f"**Expiry Date:** {client_data['expiry_date']}")
            st.write(f"**Dashboards:** {', '.join(client_data['permissions'])}")
            login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
            st.write(f"**Status:** {login_status}")

            # Edit Client Details Form
            if st.button("Edit Client", key=f"edit_btn_{client_data['username']}"):
                st.session_state[f"edit_{client_data['username']}"] = {
                    'email': client_data['email'],
                    'expiry_date': client_data['expiry_date'],
                    'permissions': client_data['permissions']
                }
            
            if f"edit_{client_data['username']}" in st.session_state:
                st.write("### Update Client Information")
                prev_values = st.session_state[f"edit_{client_data['username']}"]
                with st.form(key=f"edit_form_{client_data['username']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Previous Values**")
                        st.write(f"Email: {prev_values['email']}")
                        st.write(f"Expiry Date: {prev_values['expiry_date']}")
                        st.write(f"Dashboards: {', '.join(prev_values['permissions'])}")

                    with col2:
                        st.write("**Updated Values**")
                        updated_email = st.text_input("Update Email", value=prev_values['email'])
                        updated_expiry = st.date_input("Update Expiry Date", value=datetime.strptime(prev_values['expiry_date'], "%Y-%m-%d").date())
                        updated_permissions = st.multiselect("Update Dashboards", 
                                                             ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'], 
                                                             default=prev_values['permissions'])

                    if st.form_submit_button("Save Changes"):
                        update_client(client_data['username'], updated_email, updated_expiry.strftime('%Y-%m-%d'), updated_permissions)
                        del st.session_state[f"edit_{client_data['username']}"]
                        st.rerun()

            # Remove Client
            if st.button("Remove Client", key=f"remove_{client_data['username']}"):
                remove_client(client_data['username'])
                st.rerun()

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
