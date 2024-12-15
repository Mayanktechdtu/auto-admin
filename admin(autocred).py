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
        'login_status': 0,  # Default to logged out
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Add timestamp
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client with email '{email}' added successfully! Expiry date: {expiry_date}")

# Function to update client details
def update_client(username, updated_email, updated_expiry, updated_permissions):
    db_firestore.collection('clients').document(username).update({
        'email': updated_email,
        'expiry_date': updated_expiry,
        'permissions': updated_permissions
    })
    st.success(f"Client '{username}' details updated successfully!")

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

    # Fetch clients from Firestore
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]

    # Handle missing `created_at` by assigning a default value
    for client in clients_data:
        if 'created_at' not in client:
            client['created_at'] = '2000-01-01 00:00:00'  # Assign a very old default date

    # Sort clients by created_at (latest first) and username (alphabetical order for ties)
    clients_data.sort(key=lambda x: (datetime.strptime(x['created_at'], '%Y-%m-%d %H:%M:%S'), x['username']), reverse=True)

    # Display total number of clients
    total_clients = len(clients_data)
    st.write(f"### Total Clients: {total_clients}")

    # Extract email list for autosuggestion
    email_list = [client['email'] for client in clients_data]

    # Search functionality with autosuggestion
    st.subheader("Search Clients by Email")
    selected_email = st.selectbox("Start typing to search by email:", [""] + email_list)

    # Filter clients based on selected email
    if selected_email:
        filtered_clients = [client for client in clients_data if client['email'] == selected_email]
    else:
        filtered_clients = clients_data

    # Display filtered clients
    if filtered_clients:
        st.write("### Approved Clients:")

        # Create headers for the table
        col0, col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1, 2, 2, 2, 1, 1, 1])
        with col0:
            st.markdown("**S.No**")
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
        with col7:
            st.markdown("**Edit**")

        # Display each client's data in a row
        for idx, client_data in enumerate(filtered_clients, start=1):
            login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
            status_color = "green" if login_status == "Logged In" else "red"

            # Ensure text comes in a single line by avoiding line breaks
            col0, col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1, 2, 2, 2, 1, 1, 1])
            with col0:
                st.write(idx)
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
            with col7:
                if st.button("Edit", key=f"edit_{client_data['username']}"):
                    with st.form(key=f"edit_form_{client_data['username']}"):
                        updated_email = st.text_input("Update Email", value=client_data['email'])
                        updated_expiry = st.date_input("Update Expiry Date", value=datetime.strptime(client_data['expiry_date'], "%Y-%m-%d").date())
                        updated_permissions = st.multiselect("Update Dashboards", ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'], default=client_data['permissions'])
                        if st.form_submit_button("Save Changes"):
                            update_client(client_data['username'], updated_email, updated_expiry.strftime('%Y-%m-%d'), updated_permissions)
                            st.experimental_rerun()
    else:
        st.warning("No clients found.")

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
