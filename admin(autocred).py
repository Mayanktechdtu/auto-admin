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

    # Display all clients in a table format
    clients_ref = db_firestore.collection('clients').stream()
    st.write("### Approved Clients:")
    
    # Header row
    st.markdown("""
    <style>
        .table-header, .table-row {
            display: grid;
            grid-template-columns: 15% 25% 20% 30% 10%;
            text-align: left;
            padding: 5px 0;
            border-bottom: 1px solid #ccc;
        }
        .table-header {
            font-weight: bold;
        }
        .table-row button {
            margin: 0;
            padding: 5px 10px;
            font-size: 12px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Table Header
    st.markdown(
        '<div class="table-header">'
        '<div>Username</div>'
        '<div>Email</div>'
        '<div>Expiry Date</div>'
        '<div>Dashboards</div>'
        '<div>Status/Action</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Table Rows
    for client in clients_ref:
        client_data = client.to_dict()
        username = client_data['username']
        email = client_data['email']
        expiry_date = client_data['expiry_date']
        dashboards = ', '.join(client_data['permissions'])
        status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
        
        action_html = (
            f'<button onclick="document.location.reload()">Reset</button>'
            if status == "Logged In" else status
        )
        
        # Row content
        row_html = (
            f'<div class="table-row">'
            f'<div>{username}</div>'
            f'<div>{email}</div>'
            f'<div>{expiry_date}</div>'
            f'<div>{dashboards}</div>'
            f'<div>{button_html}</div>'
            '</div>'
     ]
