import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import hashlib
import os

st.write("Database location:", os.path.abspath("expenses.db"))
# =========================
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# =========================
st.set_page_config(page_title="Personal Expense Tracker", layout="centered")

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")

conn.commit()
# Add user_id column if database was created before login system
try:
    c.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")
    conn.commit()
except:
    pass

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# LOGIN SYSTEM
# =========================
if st.session_state.user is None:

    st.title("🔐 Login System")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            try:
                c.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (new_user, hash_password(new_pass))
                )
                conn.commit()
                st.success("Account created!")
            except:
                st.error("Username already exists")

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute(
                "SELECT id, username FROM users WHERE username=? AND password=?",
                (username, hash_password(password))
            )

            user = c.fetchone()

            if user:
                st.session_state.user = user[1]
                st.session_state.user_id = user[0]
                st.rerun()
            else:
                st.error("Invalid login")
    with st.expander("Forgot Password?"):
        reset_user = st.text_input("Username", key="reset_username")
        new_password = st.text_input("New Password", type="password", key="reset_new_password")

        if st.button("Reset Password", key="reset_button"):
            c.execute(
                "UPDATE users SET password=? WHERE username=?",
                (hash_password(new_password), reset_user)
            )
        conn.commit()
        st.success("Password updated (if username exists)")
    st.stop()

# =========================
# LOGOUT
# =========================
st.sidebar.write(f"Logged in as: {st.session_state.user}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.user_id = None
    st.rerun()

st.title("💰 Personal Expense Tracker")

# =========================
# HELPER FUNCTIONS
# =========================
def load_data():
    try:
        return pd.read_sql_query(
            "SELECT * FROM expenses WHERE user_id=?",
            conn,
            params=(st.session_state.user_id,)
        )
    except:
        return pd.read_sql_query(
            "SELECT * FROM expenses",
            conn
        )

def add_expense(date, category, description, amount):
    c.execute(
        "INSERT INTO expenses (user_id, date, category, description, amount) VALUES (?, ?, ?, ?, ?)",
        (st.session_state.user_id, date, category, description, amount)
    )
    conn.commit()

def update_expense(expense_id, date, category, description, amount):
    c.execute("""
        UPDATE expenses
        SET date=?, category=?, description=?, amount=?
        WHERE id=? AND user_id=?
    """, (date, category, description, amount, expense_id, st.session_state.user_id))
    conn.commit()

def delete_expense(expense_id):
    c.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (expense_id, st.session_state.user_id)
    )
    conn.commit()

# =========================
# LOAD DATA
# =========================
df = load_data()

# =========================
# SIDEBAR
# =========================
menu = st.sidebar.radio(
    "Navigation",
    ['Dashboard', 'Add Expense', 'View Expense', 'Edit Expense', 'Delete Expense']
)

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    if df.empty:
        st.info("No expenses recorded yet.")
    else:

        total = df['amount'].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total", f"${total:,.2f}")
        with col2:
            st.metric("Transactions", len(df))
        with col3:
            st.metric("Average", f"${total/len(df):,.2f}")

        st.divider()

        left, right = st.columns(2)

        with left:
            cat = df.groupby('category')['amount'].sum()

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')
            ax.pie(cat, labels=cat.index, autopct='%1.1f%%',
                   textprops={'color': 'white'})
            ax.set_title("Categories", color="white")
            st.pyplot(fig)

        with right:
            df['date'] = pd.to_datetime(df['date'])
            month = df.groupby(df['date'].dt.strftime('%B %Y'))['amount'].sum()

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')
            ax.pie(month, labels=month.index, autopct='%1.1f%%',
                   textprops={'color': 'white'})
            ax.set_title("Monthly", color="white")
            st.pyplot(fig)

        st.subheader("Recent")
        st.dataframe(df.tail(10))

# =========================
# ADD
# =========================
elif menu == "Add Expense":

    st.header("Add Expense")

    with st.form("form", clear_on_submit=True):
        date = st.date_input("Date")
        categories = [
        "Food",
        "Transport",
        "Rent",
        "Entertainment",
        "Utilities",
        "Shopping",
        "Health",
        "Other"
    ]

        cat = st.selectbox("Category", categories)
        desc = st.text_input("Description")
        amt = st.text_input("Amount")

        if st.form_submit_button("Submit"):
            try:
                add_expense(str(date), cat, desc, float(amt))
                st.success("Added!")
            except:
                st.error("Invalid amount")

# =========================
# VIEW
# =========================
elif menu == "View Expense":
    st.header("View Expenses")
    st.dataframe(
    df.drop(
        columns=["id", "user_id"],
        errors="ignore"
    )
)

# =========================
# EDIT
# =========================
elif menu == "Edit Expense":

    st.header("Edit Expense")

    if df.empty:
        st.info("No expenses to edit.")

    else:
        options = {
            f"{row['date']} | {row['category']} | ${row['amount']}": row['id']
            for _, row in df.iterrows()
        }

        selected = st.selectbox(
            "Select Expense",
            list(options.keys())
        )

        expense_id = options[selected]

        row = df[df["id"] == expense_id].iloc[0]

        new_date = st.text_input("Date", str(row["date"]))
        new_cat = st.text_input("Category", row["category"])
        new_desc = st.text_input("Description", row["description"])
        new_amt = st.text_input("Amount", str(row["amount"]))

        if st.button("Save Changes"):
            update_expense(
                expense_id,
                new_date,
                new_cat,
                new_desc,
                float(new_amt)
            )
            st.success("Updated!")
            st.rerun()
# =========================
# DELETE
# =========================
elif menu == "Delete Expense":

    st.header("Delete Expense")

    if df.empty:
        st.info("No expenses to delete.")

    else:
        options = {
            f"{row['date']} | {row['category']} | ${row['amount']}": row['id']
            for _, row in df.iterrows()
        }

        selected = st.selectbox(
            "Select Expense",
            list(options.keys())
        )

        expense_id = options[selected]

        if st.button("Delete"):
            delete_expense(expense_id)
            st.success("Deleted!")
            st.rerun()
