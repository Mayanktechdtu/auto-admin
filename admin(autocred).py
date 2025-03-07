import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import random
import string
import pandas as pd
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# Email Notification Helper Function
# --------------------------
def send_email_notification(recipient_email, client_name):
    """Send an email notification to the new client."""
    # Email credentials and SMTP server configuration from st.secrets for security.
    smtp_server = st.secrets["smtp"]["server"]      # e.g., "smtp.gmail.com"
    smtp_port = st.secrets["smtp"]["port"]            # e.g., 587
    sender_email = "whalestreetofficial@gmail.com"
    sender_password = st.secrets["smtp"]["password"]  # App password or actual password

    subject = "Access Granted - WhaleStreet"
    body = f"Hello {client_name},\n\nYour access has been granted by WhaleStreet. You can now log in using your credentials.\n\nBest regards,\nWhaleStreet Team"

    # Create the MIME message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    
    try:
        # Connect to the SMTP server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        st.info(f"Email sent to {recipient_email}.")
    except Exception as e:
        st.error(f"Failed to send email to {recipient_email}: {e}")

# --------------------------
# Helper Functions
# --------------------------
def generate_random_password(length=8):
    """Generate a random password (if needed for other admin functionalities)."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for i in range(length))

def add_client(email, expiry_date, permissions):
    """Create a new client document in Firestore (manual add). 
       For manual adds, the purchase date defaults to the access granted date."""
    if "All Dashboard" in permissions:
        permissions = ALL_DASHBOARDS.copy()
    username = email.split('@')[0]
    access_granted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_data = {
        'username': username,
        'password': '',  # Optionally, generate and store a random password if needed
        'expiry_date': expiry_date,
        'permissions': permissions,
        'email': email,
        'login_status': 0,
        'created_at': access_granted,        # Access Granted Date
        'purchase_date': access_granted,       # For manual add, purchase date equals access granted date
        'edit_logs': []
    }
    db_firestore.collection('clients').document(username).set(client_data)
    st.success(f"Client '{email}' added successfully! Expiry Date: {expiry_date}")
    
    # Send email notification to the client
    send_email_notification(email, username)
    
    try:
        st.experimental_rerun()
    except Exception:
        pass

def bulk_add_client(email, expiry_date, permissions, access_granted, name, purchase_date):
    """Create a new client document in Firestore for bulk uploads.
       'purchase_date' comes from the CSV 'Date' column, while 'access_granted' is the current time."""
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
        'created_at': access_granted,        # Access Granted Date
        'purchase_date': purchase_date,        # Purchase Date from CSV
        'edit_logs': []
    }
    db_firestore.collection('clients').document(username).set(client_data)
    
    # Send email notification to the client after bulk upload
    send_email_notification(email, name if name else username)

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
            changes.append(f"Permissions: {', '.join(original_data['permissions'])} -> {', '.join(updated_permissions)}")
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
    try:
        st.experimental_rerun()
    except Exception:
        pass

def remove_client(username):
    """Delete the client's document from Firestore."""
    db_firestore.collection('clients').document(username).delete()
    st.success(f"Client '{username}' has been removed successfully.")
    try:
        st.experimental_rerun()
    except Exception:
        pass

def status_dot(color):
    """Return an HTML string for a colored status dot."""
    return f"<span style='height: 10px; width: 10px; background-color: {color}; border-radius: 50%; display: inline-block;'></span>"

def parse_date(date_str):
    """Parse a date string that could be in dd/mm/yy or dd/mm/yyyy formats."""
    date_str = str(date_str).strip()
    for fmt in ("%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def get_sort_date(client):
    """Return the access granted date (created_at) for sorting."""
    date_str = client.get("created_at", "2000-01-01 00:00:00")
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
                # Sort by the parsed purchase date from the CSV
                df = df.sort_values(by="ParsedDate")
                new_uploads = []
                for index, row in df.iterrows():
                    client_email = row["Email"]
                    client_name = row["Name"]
                    default_expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    access_granted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    purchase_date_full = row["ParsedDate"].strftime('%Y-%m-%d %H:%M:%S')
                    # Format dates with abbreviated month names (e.g., "04 Mar 2025")
                    purchase_date_disp = datetime.strptime(purchase_date_full, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y')
                    access_granted_disp = datetime.strptime(access_granted, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y')
                    bulk_add_client(client_email, default_expiry, ALL_DASHBOARDS, access_granted, client_name, purchase_date_full)
                    new_uploads.append({
                        "Name": client_name,
                        "Email": client_email,
                        "Purchase Date": purchase_date_disp,
                        "Access Granted Date": access_granted_disp
                    })
                st.success(f"Bulk upload complete, {len(new_uploads)} clients added.")
                st.write("### Newly Uploaded Clients")
                st.dataframe(pd.DataFrame(new_uploads))
        except Exception as e:
            st.error(f"Error processing CSV: {e}")

    st.write("---")

    # ---------------------------
    # 3) Display/Manage Clients (Sorted)
    # ---------------------------
    clients_ref = db_firestore.collection('clients').stream()
    clients_data = [client.to_dict() for client in clients_ref]
    for client in clients_data:
        if 'created_at' not in client:
            client['created_at'] = '2000-01-01 00:00:00'
        if 'purchase_date' not in client:
            client['purchase_date'] = client['created_at']
    clients_data.sort(key=lambda x: (-get_sort_date(x).timestamp(), x['email']))
    
    st.subheader(f"Total Clients: {len(clients_data)}")
    
    # Create dropdown options using client's Name and Email
    dropdown_options = [""] + [f"{client.get('name', client['username'])} ({client['email']})" for client in clients_data]
    selected_client_str = st.selectbox("Select Client:", dropdown_options)
    if selected_client_str:
        filtered_clients = [c for c in clients_data if f"{c.get('name', c['username'])} ({c['email']})" == selected_client_str]
    else:
        filtered_clients = clients_data

    # ---------------------------
    # 4) Display Each Client
    # ---------------------------
    for idx, client_data in enumerate(filtered_clients, start=1):
        try:
            purchase_date_disp = datetime.strptime(client_data.get("purchase_date", client_data["created_at"]), '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y')
        except Exception:
            purchase_date_disp = "N/A"
        try:
            access_granted_disp = datetime.strptime(client_data.get("created_at"), '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y')
        except Exception:
            access_granted_disp = "N/A"
        
        with st.expander(f"{client_data.get('name', client_data['username'])} Details"):
            # Display Name & Email in one line
            st.markdown(f"**Name & Email:** {client_data.get('name', client_data['username'])} | {client_data['email']}")
            # Display dates in one compact inline box
            dates_html = f"""
            <div style="border:1px solid #ccc; padding:4px; font-size:14px; display:inline-block;">
                Purchase Date: {purchase_date_disp} | Access Granted Date: {access_granted_disp}
            </div>
            """
            st.markdown(dates_html, unsafe_allow_html=True)
            st.write("---")
            # Display Login Credentials in a box
            st.markdown("**Login Credentials**")
            st.info(f"Username: {client_data['username']}\nPassword: {client_data.get('password', '')}")
            
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
            if st.button("Reset Login Status", key=f"reset_status_{client_data['username']}"):
                update_login_status(client_data['username'], 0)
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
                        try:
                            st.experimental_rerun()
                        except Exception:
                            pass

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
