import streamlit as st
import pandas as pd
from streamlit_oauth import OAuth2Component
import gspread
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="Personal Expense Tracker", layout="centered")
st.title("💰 Personal Expense Tracker")

# ---- OAuth setup ----
AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
SCOPE = "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file"

CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)

# ---- Login screen ----
if 'token' not in st.session_state:
    st.subheader("Connect your Google account to get started")
    result = oauth2.authorize_button(
        name="Connect Google Sheets",
        icon="https://www.google.com/favicon.ico",
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        key="google",
        extras_params={"access_type": "offline", "prompt": "consent"},
    )
    if result and 'token' in result:
        st.session_state.token = result['token']
        st.rerun()
    st.stop()

# ---- Build gspread client from the user's token ----
token = st.session_state.token
creds = Credentials(token=token['access_token'])
gc = gspread.authorize(creds)

# ---- Open or create the user's own sheet ----
if 'sheet' not in st.session_state:
    try:
        sheet = gc.open("My Expense Tracker").sheet1
    except gspread.SpreadsheetNotFound:
        sh = gc.create("My Expense Tracker")
        sheet = sh.sheet1
        sheet.update([['Date', 'Category', 'Description', 'Amount']])
    st.session_state.sheet = sheet

sheet = st.session_state.sheet

# ---- Load data from their sheet ----
if 'df' not in st.session_state:
    existing_data = sheet.get_all_records()
    if existing_data:
        st.session_state.df = pd.DataFrame(existing_data)
    else:
        st.session_state.df = pd.DataFrame(columns=['Date', 'Category', 'Description', 'Amount'])

def sync_data():
    sheet.clear()
    sheet.update([st.session_state.df.columns.values.tolist()] + st.session_state.df.values.tolist())

# ---- Sidebar ----
st.sidebar.success("Connected to Google Sheets")
if st.sidebar.button("Disconnect"):
    for key in ['token', 'sheet', 'df']:
        st.session_state.pop(key, None)
    st.rerun()

menu = st.sidebar.radio(
    "Action",
    ['Add Expense', 'View Expense', 'View Summary', 'Edit Expense', 'Delete Expense', 'Save Data']
)

# ---- Add Expense ----
if menu == 'Add Expense':
    st.header("Add Expense")
    date = st.text_input("Date", placeholder="e.g. 2025-06-30")
    category = st.text_input("Category")
    description = st.text_input("Description", placeholder="e.g. Food with friends")
    amount_input = st.text_input("Amount", placeholder="e.g. 12.50")

    if st.button("Submit"):
        try:
            amount = float(amount_input)
            new_row = {'Date': date, 'Category': category, 'Description': description, 'Amount': amount}
            st.session_state.df.loc[len(st.session_state.df)] = new_row
            sync_data()
            st.success("Expense added and saved to your Google Sheet!")
        except ValueError:
            st.error("Please enter a valid number for Amount.")

# ---- View Expense ----
elif menu == 'View Expense':
    st.header("View Expenses")
    if st.session_state.df.empty:
        st.info("No expenses recorded yet.")
    else:
        st.dataframe(st.session_state.df)

        st.divider()

        # Overall total
        overall_total = st.session_state.df['Amount'].sum()
        st.metric(label="Overall Total Spent", value=f"${overall_total:,.2f}")

        st.divider()

        # Total by category
        st.subheader("Total by Category")
        category_totals = st.session_state.df.groupby('Category')['Amount'].sum().reset_index()
        category_totals.columns = ['Category', 'Total Spent']
        category_totals['Total Spent'] = category_totals['Total Spent'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(category_totals, hide_index=True)

# ---- View Summary ----
elif menu == 'View Summary':
    st.header("Summary by Category")
    if st.session_state.df.empty:
        st.info("No expenses recorded yet.")
    else:
        summary = st.session_state.df.groupby('Category')['Amount'].sum()
        st.bar_chart(summary)
        st.dataframe(summary)

# ---- Edit Expense ----
elif menu == 'Edit Expense':
    st.header("Edit Expense")
    if st.session_state.df.empty:
        st.info("No expenses to edit.")
    else:
        options = [
            f"{idx}: {row['Date']} | {row['Category']} | ${row['Amount']}"
            for idx, row in st.session_state.df.iterrows()
        ]
        selected = st.selectbox("Select expense to edit", options)
        idx_to_edit = int(selected.split(":")[0])
        row = st.session_state.df.loc[idx_to_edit]

        new_date = st.text_input("Date", value=str(row['Date']))
        new_category = st.text_input("Category", value=str(row['Category']))
        new_description = st.text_input("Description", value=str(row['Description']))
        new_amount_input = st.text_input("Amount", value=str(row['Amount']))

        if st.button("Save Changes"):
            try:
                new_amount = float(new_amount_input)
                st.session_state.df.loc[idx_to_edit, 'Date'] = new_date
                st.session_state.df.loc[idx_to_edit, 'Category'] = new_category
                st.session_state.df.loc[idx_to_edit, 'Description'] = new_description
                st.session_state.df.loc[idx_to_edit, 'Amount'] = new_amount
                sync_data()
                st.success("Expense updated and synced to Google Sheet!")
            except ValueError:
                st.error("Please enter a valid number for Amount.")

# ---- Delete Expense ----
elif menu == 'Delete Expense':
    st.header("Delete Expense")
    if st.session_state.df.empty:
        st.info("No expenses to delete.")
    else:
        options = [
            f"{idx}: {row['Date']} | {row['Category']} | ${row['Amount']}"
            for idx, row in st.session_state.df.iterrows()
        ]
        selected = st.selectbox("Select expense to delete", options)
        if st.button("Delete"):
            idx_to_remove = int(selected.split(":")[0])
            st.session_state.df = st.session_state.df.drop(idx_to_remove).reset_index(drop=True)
            sync_data()
            st.success("Expense deleted and synced!")
            st.rerun()

# ---- Save Data ----
elif menu == 'Save Data':
    sync_data()
    st.success("Data saved to your Google Sheet!")
