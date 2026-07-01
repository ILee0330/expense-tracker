import streamlit as st
import pandas as pd

st.set_page_config(page_title="Personal Expense Tracker", layout="centered")
st.title("💰 Personal Expense Tracker")

# ---- Initialize session state ----
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Date', 'Category', 'Description', 'Amount'])

# ---- Sidebar ----
menu = st.sidebar.radio(
    "Action",
    ['Add Expense', 'View Expense', 'View Summary', 'Edit Expense', 'Delete Expense']
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
            st.success("Expense added!")
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

        overall_total = st.session_state.df['Amount'].sum()
        st.metric(label="Overall Total Spent", value=f"${overall_total:,.2f}")

        st.divider()

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
                st.success("Expense updated!")
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
            st.success("Expense deleted!")
            st.rerun()
