import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

st.set_page_config(page_title="Personal Expense Tracker", layout="centered")
st.title("💰 Personal Expense Tracker")

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")
conn.commit()


# =========================
# HELPER FUNCTIONS
# =========================
def load_data():
    return pd.read_sql_query("SELECT * FROM expenses", conn)


def add_expense(date, category, description, amount):
    c.execute(
        "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
        (date, category, description, amount)
    )
    conn.commit()


def update_expense(expense_id, date, category, description, amount):
    c.execute("""
        UPDATE expenses
        SET date=?, category=?, description=?, amount=?
        WHERE id=?
    """, (date, category, description, amount, expense_id))
    conn.commit()


def delete_expense(expense_id):
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()


df = load_data()


# =========================
# SIDEBAR MENU
# =========================
menu = st.sidebar.radio(
    "Navigation",
    ['Dashboard', 'Add Expense', 'View Expense', 'Edit Expense', 'Delete Expense']
)

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    st.header("📊 Financial Dashboard")

    df = load_data()

    if df.empty:
        st.info("No expenses recorded yet.")
    else:

        overall_total = df['amount'].sum()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Total Expenses", f"${overall_total:,.2f}")

        with col2:
            st.metric("🧾 Transactions", len(df))

        with col3:
            avg = overall_total / len(df)
            st.metric("📈 Avg Expense", f"${avg:,.2f}")

        st.divider()

        left, right = st.columns(2)

        # CATEGORY PIE
        with left:
            category_summary = df.groupby('category')['amount'].sum()

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')

            ax.pie(
                category_summary,
                labels=category_summary.index,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': 'white'}
            )

            ax.set_title("Categories", color="white")

            st.pyplot(fig)

        # MONTHLY PIE
        with right:
            df['date'] = pd.to_datetime(df['date'])

            monthly_summary = df.groupby(df['date'].dt.strftime('%B %Y'))['amount'].sum()

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')

            ax.pie(
                monthly_summary,
                labels=monthly_summary.index,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': 'white'}
            )

            ax.set_title("Monthly Spending", color="white")

            st.pyplot(fig)

        st.divider()
        st.subheader("Recent Transactions")
        st.dataframe(df.tail(10))


# =========================
# ADD EXPENSE
# =========================
elif menu == "Add Expense":
    st.header("Add Expense")

    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date")
        category = st.text_input("Category")
        description = st.text_input("Description")
        amount_input = st.text_input("Amount")

        submitted = st.form_submit_button("Submit")

        if submitted:
            try:
                amount = float(amount_input)
                add_expense(str(date), category, description, amount)
                st.success("Expense added!")
            except:
                st.error("Invalid amount")


# =========================
# VIEW EXPENSES
# =========================
elif menu == "View Expense":
    st.header("View Expenses")

    df = load_data()

    st.dataframe(df.drop(columns=["id"]))


# =========================
# EDIT EXPENSE
# =========================
elif menu == "Edit Expense":
    st.header("Edit Expense")
    df = load_data()

    options = df.apply(
        lambda row: f"{row['id']} | {row['date']} | {row['category']} | ${row['amount']}",
        axis=1
    )

    selected = st.selectbox("Select", options)
    expense_id = int(selected.split("|")[0])

    row = df[df['id'] == expense_id].iloc[0]

    if st.button("Save Changes"):
        update_expense(
            expense_id,
            row['date'],
            row['category'],
            row['description'],
            row['amount']
        )
        st.success("Updated!")


# =========================
# DELETE EXPENSE
# =========================
elif menu == "Delete Expense":
    st.header("Delete Expense")

    df = load_data()

    options = df.apply(
        lambda row: f"{row['id']} | {row['date']} | {row['category']} | ${row['amount']}",
        axis=1
    )

    selected = st.selectbox("Select", options)
    expense_id = int(selected.split("|")[0])

    if st.button("Delete"):
        delete_expense(expense_id)
        st.success("Deleted!")
        st.rerun()
