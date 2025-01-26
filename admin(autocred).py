import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import random
import string

# --------------------------
# Firebase Initialization
# --------------------------
if not firebase_admin._apps:
    firebase_cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key_id"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(firebase_cred)
db_firestore = firestore.client()

# --------------------------
# Helper Functions
# --------------------------

def generate_random_password(length=8):
    """Generate a random password (if needed for other admin functionalities)."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for i in range(length))

def add_client(email, expiry_date, permissions):
    """Create a new client document in Firestore."""
    username = email.split('@')[0]
    client_data = {
        'username': username,
        'password': '',
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'login_status': 0,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Add timestamp
        'edit_logs': []  # Initialize empty edit logs
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client '{email}' added successfully! Expiry Date: {expiry_date}")

def update_client(username, updated_email, updated_expiry, updated_permissions):
    """Update an existing client's information and log the changes."""
    client_doc = db_firestore.collection('clients').document(username).get()
    if client_doc.exists:
        original_data = client_doc.to_dict()
        changes = []

        if original_data['email'] != updated_email:
            changes.append(f"Email: {original_data['email']} -> {updated_email}")
        if original_data['expiry_date'] != updated_expiry:
            changes.append(f"Expiry Date: {original_data['expiry_date']} -> {updated_expiry}")
        if set(original_data['permissions']) != set(updated_permissions):
            changes.append(
                f"Permissions: {', '.join(original_data['permissions'])} "
                f"-> {', '.join(updated_permissions)}"
            )

        edit_log = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'changes': changes
        }

        db_firestore.collection('clients').document(username).update({
            'email': updated_email,
            'expiry_date': updated_expiry,
            'permissions': updated_permissions,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'edit_logs': firestore.ArrayUnion([edit_log])
        })
        st.success(f"Client '{username}' details updated successfully!")
    else:
        st.error("Client not found.")

def update_login_status(username, status):
    """Reset or update the login status (0 = logged out, 1 = logged in)."""
    db_firestore.collection('clients').document(username).update({'login_status': status})
    st.success(f"Login status for '{username}' has been reset.")

def remove_client(username):
    """Delete the client's document from Firestore."""
    db_firestore.collection('clients').document(username).delete()
    st.success(f"Client '{username}' has been removed successfully.")

def status_dot(color):
    """Return an HTML string for a colored status dot."""
    return f"<span style='height: 10px; width: 10px; background-color: {color}; " \
           f"border-radius: 50%; display: inline-block;'></span>"

# --------------------------
# Admin Dashboard
# --------------------------

def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Manage client access, edit permissions, and expiry dates.")

    # ---------------------------
    # 1) Add a new client section
    # ---------------------------
    st.subheader("Add New Client")
    email = st.text_input("Enter Client's Email:")
    expiry_option = st.selectbox(
        "Select Expiry Duration:", 
        ['1 Month', '3 Months', '6 Months']
    )
    dashboards = st.multiselect(
        "Dashboards to Provide Access:", 
        ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6']
    )

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

    # ---------------------------
    # 2) Display/Manage Clients
    # ---------------------------
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]

    # Handle missing timestamps
    for client in clients_data:
        if 'created_at' not in client:
            client['created_at'] = '2000-01-01 00:00:00'

    # Sort by creation date (descending) and username
    clients_data.sort(
        key=lambda x: (datetime.strptime(x['created_at'], '%Y-%m-%d %H:%M:%S'), x['username']), 
        reverse=True
    )

    st.subheader(f"Total Clients: {len(clients_data)}")

    st.subheader("Search Clients by Email")
    email_list = [client['email'] for client in clients_data]
    selected_email = st.selectbox("Select Client Email to Search:", [""] + email_list)

    # Filter clients
    filtered_clients = (
        clients_data 
        if not selected_email 
        else [c for c in clients_data if c['email'] == selected_email]
    )

    # ---------------------------
    # 3) Display each client
    # ---------------------------
    for idx, client_data in enumerate(filtered_clients, start=1):
        with st.expander(f"**{idx}. {client_data['username']}** - {client_data['email']}"):
            st.write("### Client Details")

            # >>> Display Username & Password
            st.write(f"**ID (Username):** {client_data['username']}")
            st.write(f"**Password:** {client_data.get('password', '')}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Expiry Date:** {client_data['expiry_date']}")
            with col2:
                st.write(f"**Dashboards:** {', '.join(client_data['permissions'])}")
            with col3:
                login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
                status_color = "green" if login_status == "Logged In" else "red"
                st.markdown(f"**Status:** {status_dot(status_color)} {login_status}", unsafe_allow_html=True)

            # Show "Edited" tag if applicable
            if 'edit_logs' in client_data and client_data['edit_logs']:
                last_edit = client_data['edit_logs'][-1]  # Get the latest edit
                st.write(f"**Last Edited:** {last_edit['timestamp']}")
                for log in last_edit['changes']:
                    st.write(f"- {log}")

            # Remove Client Button
            if st.button("Remove Client", key=f"remove_{client_data['username']}"):
                remove_client(client_data['username'])
                st.rerun()

            # Reset Login Status Button
            if st.button("Reset Login Status", key=f"reset_status_{client_data['username']}"):
                update_login_status(client_data['username'], 0)
                st.rerun()

            # Edit Client Details
            if f"edit_{client_data['username']}" not in st.session_state:
                st.session_state[f"edit_{client_data['username']}"] = False

            if st.button("Edit Client", key=f"edit_btn_{client_data['username']}"):
                st.session_state[f"edit_{client_data['username']}"] = not st.session_state[f"edit_{client_data['username']}"]

            if st.session_state[f"edit_{client_data['username']}"]:
                st.write("### Update Client Information")
                with st.form(key=f"edit_form_{client_data['username']}"):
                    updated_email = st.text_input("Update Email", value=client_data['email'])
                    updated_expiry_option = st.selectbox(
                        "Update Expiry Duration:", 
                        ['1 Month', '3 Months', '6 Months']
                    )
                    if updated_expiry_option == '1 Month':
                        updated_expiry = (datetime.now() + timedelta(days=30)).date()
                    elif updated_expiry_option == '3 Months':
                        updated_expiry = (datetime.now() + timedelta(days=90)).date()
                    else:
                        updated_expiry = (datetime.now() + timedelta(days=180)).date()

                    updated_permissions = st.multiselect(
                        "Update Dashboards", 
                        ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6'], 
                        default=client_data['permissions']
                    )
                    if st.form_submit_button("Save Changes"):
                        update_client(
                            client_data['username'], 
                            updated_email, 
                            updated_expiry.strftime('%Y-%m-%d'), 
                            updated_permissions
                        )
                        st.rerun()

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
