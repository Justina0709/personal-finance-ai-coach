import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

#Hence, UI → calls → Engine
#That is called: Separation of Concerns
from financial_engine import process_csv
from financial_engine import (calculate_health_score,detect_risks,generate_recommendation)
from financial_engine import run_simulation, projection_savings
from database import create_tables, add_expense, get_expenses, delete_all_expenses,save_income, get_income
from database import register_user, login_user
from database import update_category



create_tables()

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if st.session_state.user_id is None:
    st.title("Login or Register")
    option= st.radio("Choose Option", ["Login", "Register"])
    username=st.text_input("Username")
    password=st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists.")
    if option == "Login":
        if st.button("Login"):
            user_id = login_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    st.stop()



st.markdown("""
<style>

/* Card container spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Professional metric card styling */
.stMetric {
    padding: 18px;
    border-radius: 14px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background-color: rgba(16, 185, 129, 0.08); /* subtle blue tint */
    backdrop-filter: blur(4px);
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Personal Finance AI Coach",
    page_icon="💰",
    layout="wide")
# st.write("Welcome! This app will help you track expenses and savings")


st.markdown("""
<style>
[data-testid="metric-container"] {
    border-radius: 12px;
    padding: 15px;
    background-color: rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)




st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"user_id": None}))


saved_income=get_income(st.session_state.user_id)
income = st.number_input("Enter Monthly income (₹)",min_value=0.0,value=float(saved_income),step=500.0)

if income!=saved_income:
    save_income(st.session_state.user_id,income)

st.divider() #draws a horitzontal line
st.write("Add an expense:")
#EXPENSE INPUTS

category=st.text_input("Expense category (e.g., Food, Rent, Grocery, Travel)")
amount_text=st.text_input("Expense Amount (₹)")

# BUTTON TO ADD EXPENSE

if st.button("Add Expense"):
    try:
        amount = int(amount_text)

        if category.strip() == "" or amount <= 0:
            st.warning("Please enter a valid expense.")
        else:
            add_expense(st.session_state.user_id,category, amount)
            st.success("Expense added successfully!")

    except ValueError:
        st.warning("Expense amount must be a number.")
if st.button ("Clear All Expenses"):
    delete_all_expenses()
    st.success("All expenses cleared")




# ===== UPLOAD CSV =====

st.divider()
st.subheader("Upload Bank Statement (CSV)")
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    status, count = process_csv(
        uploaded_file,
        st.session_state.user_id,
        get_expenses,
        add_expense
    )
    if status == "invalid":
        st.error("Could not detect expense column")
    else:
        st.success(f"{count} expenses imported successfully!")
    

# DISPLAY ALL EXPENSES
st.subheader("All Expenses")
expenses= get_expenses(st.session_state.user_id)
total_expense=0
if expenses:
    for category,amount in expenses:
        st.write(f"{category} : ₹{amount}")
        total_expense+=amount
else:
    st.write("No expenses added yet.")

st.divider()

#KPI Summary Cards

st.subheader("Financial Overview")
col1,col2,col3= st.columns(3)
 
with col1:
    st.metric("Monthly Income", f"₹{income:.0f}")
with col2:
    st.metric("Total Expenses", f"₹{total_expense:.0f}")
with col3:
    savings=income-total_expense
    st.metric("Monthly Savings", f"₹{savings:.0f}")

st.divider()
st.subheader("Edit Categories")

expenses = get_expenses(st.session_state.user_id)

if expenses:

    category_options = [
        "Food","Travel","Shopping","Utilities",
        "Subscriptions","Rent","Transfers",
        "Cash Withdrawal","Miscellaneous"
    ]

    for i, (category, amount) in enumerate(expenses):

        col1, col2, col3 = st.columns([3,2,1])

        with col1:
            st.write(f"{category} — ₹{amount}")

        with col2:
            new_category = st.selectbox(
                "Change",
                category_options,
                index=category_options.index(category)
                if category in category_options else len(category_options)-1,
                key=f"category_amount_{i}"
            )

        with col3:
            if st.button("Update", key=f"update_btn_{i}"):
                update_category(
                    st.session_state.user_id,
                    category,
                    amount,
                    new_category
                )
                st.success("Updated!")
                st.rerun()

else:
    st.write("No expenses available.")

# Monthly insights
st.divider()
st.subheader("Monthly insights")
expenses= get_expenses(st.session_state.user_id)

category_totals={}
total_expense=0
for category, amount in expenses:
    category_totals[category] = category_totals.get(category, 0) +amount
    total_expense += amount

if category_totals:
    top_category= max(category_totals, key= category_totals.get)
    col1,col2=st.columns(2)
    with col1: 
        st.metric("Top Spending category", top_category)
    with col2:
         st.metric("Total Expenses",f"₹{total_expense:.0f}")
    if income>0:
        savings_rate=((income-total_expense)/income)*100
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
else:
    st.info("No expense data available")

st.subheader("Category Spending Analysis (% of Income)")
if category_totals:
    fig, ax = plt.subplots()
    ax.pie(
        category_totals.values(),
        labels=category_totals.keys(),
        autopct="%1.1f%%",
        startangle=90
    )
    ax.axis("equal")
    st.pyplot(fig)




st.subheader("Category-wise Expense Summary")
category_totals={}
for category,amount in expenses:
    category_totals[category] = category_totals.get(category, 0) + amount

if category_totals:
    for cat, total in category_totals.items():
        st.write(f"{cat}: ₹{total}")
else:
    st.write("No expenses to summarize.")


#SUMMARY SECTION
st.subheader("Expense Sumamry")
st.metric(" Total expense:", total_expense)
remaining=income-total_expense
st.metric(" Remaining balance:",remaining)

st.divider()
st.subheader("Expense Distribution (Bar Chart)")

if category_totals:
    st.bar_chart(category_totals)
else:
    st.write("No data available for chart.")

# COACH FEEDBACK
st.divider()
st.subheader("AI Finance Feedback")

if income > 0:
    savings_percent=((income - total_expense) / income) * 100

    # Rule 1: Overspending
    if total_expense > income:
        st.error("⚠️ You are spending more than your income. Immediate action needed!")

    # Rule 2: Low savings
    elif savings_percent < 20:
        st.warning("💡 Your savings are below 20%. Consider reducing non-essential expenses.")

    else:
        st.success("✅ Great job! You are maintaining healthy savings.")



#Separate User Interface (UI) for recommendation
st.divider()
st.subheader("AI Financial Advisor")
if income>0:
    health_score=calculate_health_score(income, total_expense, category_totals)
    
    st.write(f"💰 Income: ₹{income}")
    st.write(f"💸 Total Expenses: ₹{total_expense}")
    st.write(f"💵 Savings: ₹{income-total_expense}")
    st.write(f"📈 Savings Rate: {savings_percent:.1f}%")

    st.write("#### Financial Health Score")
    st.progress(health_score/100)
    st.metric(" Health Score ", f"{health_score}/100")

    risks=detect_risks(income, total_expense, category_totals)
    if risks:
        highest_risk=max(risks, key=lambda x: x[1])
        message, recommendation=generate_recommendation(highest_risk,income,total_expense, category_totals)
        risk_name=highest_risk[0]
        def get_risk_style(risk_name):
            if risk_name == "Overspending":
                return st.error
            if risk_name == "Critically Low Savings":
                return st.error
            if risk_name == "Moderate Savings Risk":
                return st.warning
            if "Spending" in risk_name:
                return st.warning
            return st.info
        
        display_function=get_risk_style(risk_name)
        display_function(f"Primary Risk: {risk_name}")
        
        st.write(f"{message}")
        st.info(f"💡 Recommendation: {recommendation}")
    
    else:
        st.success(" Your Financial Status is Stable")
        st.write("No major financial risks detected.")

else:
    st.write("Enter income to enable financial analysis.")

#SIMULATION
st.divider()

st.write("#### Adjust simulation:")
reduction_percent= st.slider("Select reduction percentage",min_value=1, max_value=30, value=10,step=1)

simulation_result= None
if income > 0 and category_totals:
    if risks:
        risk_name=highest_risk[0]
        if risk_name == "Overspending":
            mode= 'overspending'
            category_name=None
        elif risk_name in ["Critically low savings", "Moderate savings risk"]:
            mode= 'low_savings'
            category_name=None
        elif 'Spending' in risk_name:
            mode= 'category'
            category_name= highest_risk[0].replace(" High Spending","")        
    
        simulation_result = run_simulation(
        mode=mode,
        income=income,
        total_expense=total_expense,
        category_totals=category_totals,
        reduction_percent=reduction_percent,
        category=category_name
        )

    if simulation_result:
        new_savings_percent= simulation_result["new_savings_percent"]
        new_health_score=simulation_result["new_health_score"]

        st.subheader("What-If Simulation")
        st.write(simulation_result["message"])

        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Current")
            st.write(f"Savings Rate: {((income - total_expense)/income)*100:.1f}%")
            st.write(f"Health Score: {calculate_health_score(income, total_expense, category_totals)}")

        with col2:
            st.write("#### After Simulation")
            st.write(f"Savings Rate: {new_savings_percent:.1f}%")
            st.write(f"Health Score: {new_health_score}")

    else:
        st.success("Your finances are stable.")

        simulation_result = run_simulation(
        mode="optimization",
        income=income,
        total_expense=total_expense,
        category_totals=category_totals,
        reduction_percent=reduction_percent
        )
        
        st.write(simulation_result["message"])

        if simulation_result:
            new_savings_percent = simulation_result["new_savings_percent"]
            new_health_score = simulation_result["new_health_score"]

            col1, col2 = st.columns(2)

            with col1:
                st.write("#### Current")
                st.write(f"Savings Rate: {((income - total_expense)/income)*100:.1f}%")
                st.write(f"Health Score: {calculate_health_score(income, total_expense, category_totals)}")

            with col2:
                st.write(f"#### If overall expenses reduced by {reduction_percent}%")
                st.write(f"Savings Rate: {new_savings_percent:.1f}%")
                st.write(f"Health Score: {new_health_score}")
        
        

# Future Projection
st.divider()
st.subheader("3-Month Financial Projection")

if income>0:
    projection= projection_savings(income, total_expense, months=3)
    monthly_savings= projection["monthly_savings"]
    projected_savings_3m=projection["projected_amount"]

    if monthly_savings < 0:
        st.error("⚠️ If current spending continues, you will accumulate losses over the next 3 months.")
        st.write(f"Projected 3-month deficit: ₹{abs(projected_savings_3m):.0f}")
    else:
        st.success("📈 If current pattern continues:")
        st.write(f"Projected 3-Month Savings: ₹{projected_savings_3m:.0f}")
        if (monthly_savings/income) < 0.2:
            st.warning("Savings growth is positive but below ideal 20% target.")
        else:
            st.info("Savings growth is on a healthy trajectory.")





