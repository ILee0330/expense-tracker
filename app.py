import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Personal Expense Tracker", layout="centered")
st.title("💰 Personal Expense Tracker")

# ---- Initialize session state ----
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(
        columns=['Date', 'Category', 'Description', 'Amount']
    )

# ---- Sidebar ----
menu = st.sidebar.radio(
    "Action",
    ['Add Expense', 'View Expense', 'View Summary', 'Edit Expense', 'Delete Expense']
)

# ---- Add Expense ----
if menu == 'Add Expense':
    st.header("Add Expense")

    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date")

        category = st.text_input(
            "Category",
            placeholder="Food, Gas, Entertainment, etc."
        )

        description = st.text_input(
            "Description",
            placeholder="e.g. Food with friends"
        )

        amount_input = st.text_input(
            "Amount",
            placeholder="e.g. 12.50"
        )

        submitted = st.form_submit_button("Submit")

        if submitted:
            try:
                amount = float(amount_input)

                if category.strip() == "":
                    st.error("Please enter a category.")
                else:
                    new_row = {
                        'Date': str(date),
                        'Category': category,
                        'Description': description,
                        'Amount': amount
                    }

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
        st.metric("Overall Total Spent", f"${overall_total:,.2f}")

        st.divider()

        st.subheader("Total by Category")

        category_totals = (
            st.session_state.df
            .groupby('Category')['Amount']
            .sum()
        )

        st.dataframe(category_totals)

        st.divider()

        st.subheader("Total by Month")

        monthly_df = st.session_state.df.copy()
        monthly_df['Date'] = pd.to_datetime(monthly_df['Date'])

        monthly_totals = (
            monthly_df
            .groupby(monthly_df['Date'].dt.strftime('%B %Y'))['Amount']
            .sum()
        )

        st.dataframe(monthly_totals)

# ---- View Summary ----
elif menu == 'View Summary':
    st.header("Summary")

    if st.session_state.df.empty:
        st.info("No expenses recorded yet.")
    else:

        chart_type = st.selectbox(
            "Choose Summary Type",
            ["Category Breakdown", "Monthly Breakdown"]
        )

        # ---------------- CATEGORY PIE ----------------
        if chart_type == "Category Breakdown":

            summary = st.session_state.df.groupby('Category')['Amount'].sum()

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')

            ax.pie(
                summary,
                labels=summary.index,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': 'white'}
            )

            ax.axis('equal')
            ax.set_title("Expense by Category", color='white')

            st.pyplot(fig)

            st.subheader("Category Totals")
            st.dataframe(summary)

        # ---------------- MONTHLY PIE ----------------
        else:

            monthly_df = st.session_state.df.copy()
            monthly_df['Date'] = pd.to_datetime(monthly_df['Date'])

            monthly_summary = (
                monthly_df
                .groupby(monthly_df['Date'].dt.strftime('%B %Y'))['Amount']
                .sum()
            )

            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.set_facecolor('#0E1117')

            ax.pie(
                monthly_summary,
                labels=monthly_summary.index,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': 'white'}
            )

            ax.axis('equal')
            ax.set_title("Expense by Month", color='white')

            st.pyplot(fig)

            st.subheader("Monthly Totals")
            st.dataframe(monthly_summary)

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

            st.session_state.df = (
                st.session_state.df
                .drop(idx_to_remove)
                .reset_index(drop=True)
            )

            st.success("Expense deleted!")
            st.rerun()
