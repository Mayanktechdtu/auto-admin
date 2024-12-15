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

    # Fetch and display clients
    clients_ref = db_firestore.collection('clients').stream()
    client_logs = []

    for client in clients_ref:
        client_data = client.to_dict()
        login_status = "Logged In" if client_data['login_status'] == 1 else "Logged Out"
        reset_action = (
            f"<button onclick=\"fetch('/{client_data['username']}')\">Reset</button>"
            if login_status == "Logged In" else "No Action"
        )
        client_logs.append({
            "Username": client_data['username'],
            "Email": client_data['email'],
            "Expiry Date": client_data['expiry_date'],
            "Dashboards": ", ".join(client_data['permissions']),
            "Status": login_status,
            "Action": reset_action
        })

    # Scrollable table display
    if client_logs:
        st.write("### Approved Clients")
        table_css = """
        <style>
        .scrollable-table {
            display: block;
            width: 100%;
            overflow-x: auto;
            white-space: nowrap;
        }
        .scrollable-table table {
            border-collapse: collapse;
            width: 100%;
        }
        .scrollable-table th, .scrollable-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .scrollable-table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        </style>
        """
        st.markdown(table_css, unsafe_allow_html=True)

        table_html = """
        <div class="scrollable-table">
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Expiry Date</th>
                        <th>Dashboards</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        """

        for client in client_logs:
            action_button = (
                f'<button onClick="alert(\'Reset {client["Username"]} status!\')">Reset</button>'
                if client["Status"] == "Logged In" else "No Action"
            )
            table_html += f"""
                <tr>
                    <td>{client['Username']}</td>
                    <td>{client['Email']}</td>
                    <td>{client['Expiry Date']}</td>
                    <td>{client['Dashboards']}</td>
                    <td>{client['Status']}</td>
                    <td>{action_button}</td>
                </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.write("No clients available.")

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
