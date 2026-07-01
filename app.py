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
    "Action",
    ['Add Expense', 'View Expense', 'View Summary', 'Edit Expense', 'Delete Expense']
)


# =========================
# ADD EXPENSE
# =========================
if menu == 'Add Expense':
    st.header("Add Expense")

    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date")
        category = st.text_input("Category", placeholder="Food, Gas, Entertainment, etc")
        description = st.text_input("Description", placeholder="Food with friends")
        amount_input = st.text_input("Amount")

        submitted = st.form_submit_button("Submit")

        if submitted:
            try:
                amount = float(amount_input)

                if category.strip() == "":
                    st.error("Category required.")
                else:
                    add_expense(str(date), category, description, amount)
                    st.success("Expense added!")

            except ValueError:
                st.error("Invalid amount.")


# =========================
# VIEW EXPENSES
# =========================
elif menu == 'View Expense':
    st.header("View Expenses")

    df = load_data()

    if df.empty:
        st.info("No expenses yet.")
    else:
        st.dataframe(df.drop(columns=["id"]))

        st.metric("Total Spent", f"${df['amount'].sum():,.2f}")

        st.subheader("By Category")
        st.dataframe(df.groupby("category")["amount"].sum())

        st.subheader("By Month")
        df['date'] = pd.to_datetime(df['date'])
        monthly = df.groupby(df['date'].dt.strftime('%B %Y'))['amount'].sum()
        st.dataframe(monthly)


# =========================
# SUMMARY
# =========================
elif menu == 'View Summary':
    st.header("Summary")

    df = load_data()

    if df.empty:
        st.info("No data.")
    else:
        choice = st.selectbox("View", ["Category", "Monthly"])

        df['date'] = pd.to_datetime(df['date'])

        if choice == "Category":
            summary = df.groupby("category")["amount"].sum()

            fig, ax = plt.subplots()
            ax.pie(summary, labels=summary.index, autopct='%1.1f%%')
            ax.set_title("By Category")

            st.pyplot(fig)
            st.dataframe(summary)

        else:
            monthly = df.groupby(df['date'].dt.strftime('%B %Y'))['amount'].sum()

            fig, ax = plt.subplots()
            ax.pie(monthly, labels=monthly.index, autopct='%1.1f%%')
            ax.set_title("By Month")

            st.pyplot(fig)
            st.dataframe(monthly)


# =========================
# EDIT EXPENSE
# =========================
elif menu == 'Edit Expense':
    st.header("Edit Expense")

    df = load_data()

    if df.empty:
        st.info("No data.")
    else:
        options = df.apply(
            lambda row: f"{row['id']} | {row['date']} | {row['category']} | ${row['amount']}",
            axis=1
        )

        selected = st.selectbox("Select", options)
        expense_id = int(selected.split("|")[0].strip())

        row = df[df['id'] == expense_id].iloc[0]

        new_date = st.text_input("Date", row['date'])
        new_category = st.text_input("Category", row['category'])
        new_description = st.text_input("Description", row['description'])
        new_amount = st.text_input("Amount", str(row['amount']))

        if st.button("Save Changes"):
            try:
                update_expense(
                    expense_id,
                    new_date,
                    new_category,
                    new_description,
                    float(new_amount)
                )
                st.success("Updated!")
            except ValueError:
                st.error("Invalid amount")


# =========================
# DELETE EXPENSE
# =========================
elif menu == 'Delete Expense':
    st.header("Delete Expense")

    df = load_data()

    if df.empty:
        st.info("No data.")
    else:
        options = df.apply(
            lambda row: f"{row['id']} | {row['date']} | {row['category']} | ${row['amount']}",
            axis=1
        )

        selected = st.selectbox("Select", options)
        expense_id = int(selected.split("|")[0].strip())

        if st.button("Delete"):
            delete_expense(expense_id)
            st.success("Deleted!")
            st.rerun()
