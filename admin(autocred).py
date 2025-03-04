import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import random
import string
import pandas as pd
import io

# --------------------------
# Firebase Initialization
# --------------------------
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

# Global list for full dashboards
ALL_DASHBOARDS = ['dashboard1', 'dashboard2', 'dashboard3', 'dashboard4', 'dashboard5', 'dashboard6']

# --------------------------
# Helper Functions
# --------------------------
def generate_random_password(length=8):
    """Generate a random password (if needed for other admin functionalities)."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for i in range(length))

def add_client(email, expiry_date, permissions):
    """Create a new client document in Firestore (manual add)."""
    if "All Dashboard" in permissions:
        permissions = ALL_DASHBOARDS.copy()
        
    username = email.split('@')[0]
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # For manual add, set sheet_date equal to created_at
    client_data = {
        'username': username,
        'password': '',
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'login_status': 0,
        'created_at': created_at,
        'sheet_date': created_at,
        'edit_logs': []
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client '{email}' added successfully! Expiry Date: {expiry_date}")

def bulk_add_client(email, expiry_date, permissions, created_at, name, sheet_date):
    """Create a new client document in Firestore for bulk uploads."""
    if "All Dashboard" in permissions:
        permissions = ALL_DASHBOARDS.copy()
        
    username = email.split('@')[0]
    client_data = {
        'username': username,
        'password': '',
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'name': name,
        'login_status': 0,
        'created_at': created_at,
        'sheet_date': sheet_date,
        'edit_logs': []
    }
    db_firestore.collection('clients').document(username).set(client_data)

def update_client(username, updated_email, updated_expiry, updated_permissions):
    """Update an existing client's information and log the changes."""
    if "All Dashboard" in updated_permissions:
        updated_permissions = ALL_DASHBOARDS.copy()
        
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

def parse_date(date_str):
    """Parse a date string that could be in dd/mm/yy or dd/mm/yyyy format."""
    date_str = str(date_str).strip()
    for fmt in ("%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def get_sort_date(client):
    """Return the date for sorting. Prefer 'sheet_date' if available; else 'created_at'."""
    date_str = client.get("sheet_date", client.get("created_at", "2000-01-01 00:00:00"))
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return datetime(2000, 1, 1)

# --------------------------
# Admin Dashboard
# --------------------------
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Manage client access, edit permissions, and expiry dates.")

    # ---------------------------
    # 1) Add a New Client Section (Manual Add)
    # ---------------------------
    st.subheader("Add New Client")
    email = st.text_input("Enter Client's Email:")
    # Optionally, capture name manually if needed.
    expiry_option = st.selectbox("Select Expiry Duration:", ['1 Month', '3 Months', '6 Months'])
    dashboards_options = ["All Dashboard"] + ALL_DASHBOARDS
    dashboards = st.multiselect("Dashboards to Provide Access:", dashboards_options)
    if "All Dashboard" in dashboards:
        dashboards = ALL_DASHBOARDS.copy()

    if expiry_option == '1 Month':
        expiry_date = (datetime.now() + timedelta(days=30)).date()
    elif expiry_option == '3 Months':
        expiry_date = (datetime.now() + timedelta(days=90)).date()
    else:
        expiry_date = (datetime.now() + timedelta(days=180)).date()

    if st.button("Add Client"):
        if email and dashboards:
            add_client(email, expiry_date.strftime('%Y-%m-%d'), dashboards)
            st.experimental_rerun()
        else:
            st.error("Please provide all required details.")

    # ---------------------------
    # 2) Bulk Upload Clients via CSV
    # ---------------------------
    st.write("---")
    st.subheader("Bulk Upload Clients via CSV")
    st.write(
        "Upload a CSV file with your subscription data. "
        "The CSV must include the following columns: **Date**, **Email**, **Status**, and **Name**. "
        "Rows with a **Status** of 'Success' will be added with a default 1-month expiry and full dashboard access."
    )
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {"Date", "Email", "Status", "Name"}
            if not required_cols.issubset(df.columns):
                st.error("CSV file must contain the columns: Date, Email, Status, and Name.")
            else:
                df = df.dropna(subset=["Email"])
                df = df[df["Status"].astype(str).str.strip() == "Success"]
                df["ParsedDate"] = df["Date"].apply(parse_date)
                df = df[df["ParsedDate"].notnull()]
                # Sort by the parsed date from the CSV
                df = df.sort_values(by="ParsedDate")
                
                new_uploads = []
                for index, row in df.iterrows():
                    client_email = row["Email"]
                    client_name = row["Name"]
                    # Default expiry is 1 month from now
                    default_expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Use the parsed date from the CSV as the sheet date (formatted)
                    sheet_date_full = row["ParsedDate"].strftime('%Y-%m-%d %H:%M:%S')
                    # Format the date to show only the date part
                    sheet_date = sheet_date_full.split(" ")[0]
                    bulk_add_client(client_email, default_expiry, ALL_DASHBOARDS, created_at, client_name, sheet_date_full)
                    
                    new_uploads.append({
                        "Name": client_name,
                        "Email": client_email,
                        "Date Uploaded": sheet_date
                    })
                
                st.success(f"Bulk upload complete, {len(new_uploads)} clients added.")
                st.write("### Newly Uploaded Clients")
                st.dataframe(pd.DataFrame(new_uploads))
                # Optionally, call st.experimental_rerun() here to refresh the full clients list.
        except Exception as e:
            st.error(f"Error processing CSV: {e}")

    st.write("---")

    # ---------------------------
    # 3) Display/Manage Clients (Sorted)
    # ---------------------------
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]
    
    # Ensure each client has a 'sheet_date' (fallback to created_at)
    for client in clients_data:
        if 'sheet_date' not in client:
            client['sheet_date'] = client.get('created_at', '2000-01-01 00:00:00')
    
    # Sort clients by descending sheet_date and then by email alphabetically
    clients_data.sort(
        key=lambda x: (-get_sort_date(x).timestamp(), x['email'])
    )
    
    st.subheader(f"Total Clients: {len(clients_data)}")
    st.subheader("Search Clients by Email")
    email_list = [client['email'] for client in clients_data]
    selected_email = st.selectbox("Select Client Email to Search:", [""] + email_list)

    filtered_clients = clients_data if not selected_email else [c for c in clients_data if c['email'] == selected_email]

    # ---------------------------
    # 4) Display Each Client
    # ---------------------------
    for idx, client_data in enumerate(filtered_clients, start=1):
        # Get the date uploaded (date only)
        try:
            date_uploaded = datetime.strptime(client_data.get("sheet_date", client_data["created_at"]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        except Exception:
            date_uploaded = "N/A"
        with st.expander(f"Client {idx} Details"):
            # Header line: Name | Email | Date Uploaded
            st.markdown(f"**{client_data.get('name', client_data['username'])}** | {client_data['email']} | Date Uploaded: {date_uploaded}")
            st.write("---")
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

            if 'edit_logs' in client_data and client_data['edit_logs']:
                last_edit = client_data['edit_logs'][-1]
                st.write(f"**Last Edited:** {last_edit['timestamp']}")
                for log in last_edit['changes']:
                    st.write(f"- {log}")

            if st.button("Remove Client", key=f"remove_{client_data['username']}"):
                remove_client(client_data['username'])
                st.experimental_rerun()

            if st.button("Reset Login Status", key=f"reset_status_{client_data['username']}"):
                update_login_status(client_data['username'], 0)
                st.experimental_rerun()

            if f"edit_{client_data['username']}" not in st.session_state:
                st.session_state[f"edit_{client_data['username']}"] = False

            if st.button("Edit Client", key=f"edit_btn_{client_data['username']}"):
                st.session_state[f"edit_{client_data['username']}"] = not st.session_state[f"edit_{client_data['username']}"]

            if st.session_state[f"edit_{client_data['username']}"]:
                st.write("### Update Client Information")
                with st.form(key=f"edit_form_{client_data['username']}"):
                    updated_email = st.text_input("Update Email", value=client_data['email'])
                    updated_expiry_option = st.selectbox("Update Expiry Duration:", ['1 Month', '3 Months', '6 Months'])
                    if updated_expiry_option == '1 Month':
                        updated_expiry = (datetime.now() + timedelta(days=30)).date()
                    elif updated_expiry_option == '3 Months':
                        updated_expiry = (datetime.now() + timedelta(days=90)).date()
                    else:
                        updated_expiry = (datetime.now() + timedelta(days=180)).date()

                    updated_dashboards_options = ["All Dashboard"] + ALL_DASHBOARDS
                    updated_permissions = st.multiselect("Update Dashboards", updated_dashboards_options, default=client_data['permissions'])
                    if st.form_submit_button("Save Changes"):
                        update_client(
                            client_data['username'], 
                            updated_email, 
                            updated_expiry.strftime('%Y-%m-%d'), 
                            updated_permissions
                        )
                        st.experimental_rerun()

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
