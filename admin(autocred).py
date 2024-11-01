import streamlit as st
from datetime import datetime
import sqlite3

# Connect to the SQLite database (creates the file if it doesn’t exist)
conn = sqlite3.connect('clients_new.db')
cursor = conn.cursor()

# Create the clients table if it doesn’t exist, with a login_status column defaulting to 0
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        username TEXT PRIMARY KEY,
        password TEXT,
        expiry_date TEXT,
        permissions TEXT,
        email TEXT UNIQUE,
        login_status INTEGER DEFAULT 0
    )
''')
conn.commit()

# Add the login_status column if it doesn’t exist and ensure default is 0
try:
    cursor.execute('ALTER TABLE clients ADD COLUMN login_status INTEGER DEFAULT 0')
    conn.commit()
except sqlite3.OperationalError:
    # Ignore the error if the column already exists
    pass

# Function to add a client with email, expiry date, and permissions only
def add_client(email, expiry_date, permissions):
    # Generate username from email prefix
    username = email.split('@')[0]
    # Insert the client data with an empty password and inactive login status
    cursor.execute('''
        INSERT OR IGNORE INTO clients (username, password, expiry_date, permissions, email, login_status)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (username, '', expiry_date, ','.join(permissions), email))
    conn.commit()

# Function to update login status (active/inactive)
def update_login_status(username, status):
    cursor.execute('UPDATE clients SET login_status = ? WHERE username = ?', (status, username))
    conn.commit()

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
            st.success(f"Client with email '{email}' added successfully!")
        else:
            st.error("Please provide an email and select at least one dashboard.")

    st.write("---")

    # Display all clients with their email, permissions, and expiry dates
    cursor.execute('SELECT username, email, expiry_date, permissions, login_status FROM clients')
    clients = cursor.fetchall()
    st.write("### Approved Clients:")
    if clients:
        for client in clients:
            login_status = "Logged In" if client[4] == 1 else "Logged Out"
            st.write(f"**Username:** {client[0]} | **Email:** {client[1]} | **Expiry Date:** {client[2]} | **Dashboards Access:** {client[3]} | **Status:** {login_status}")
            
            # Add a button to reset the login status for each client
            if login_status == "Logged In":
                if st.button(f"Reset Login Status for {client[0]}"):
                    update_login_status(client[0], 0)
                    st.success(f"Login status for {client[0]} has been reset.")
    else:
        st.write("No clients added yet.")

# Run the admin dashboard
if __name__ == "__main__":
    admin_dashboard()
