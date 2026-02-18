#LOGIC FOR ADVICES AND ANALYSIS
#{from here

import re
import pandas as pd

MERCHANT_APP= { #FOOD
                "Food": "Food",
               "swiggy": "Food",
               "zomato": "Food",
               "dominos": "Food",
               "pizza hut": "Food",
               "kfc": "Food",
               "restaurant": "Food",

    # TRAVEL
    "uber": "Travel",
    "ola": "Travel",
    "rapido": "Travel",
    "fuel": "Travel",
    "petrol": "Travel",
    "diesel": "Travel",

    # UTILITIES
    "electricity": "Utilities",
    "water bill": "Utilities",
    "recharge": "Utilities",
    "mobile bill": "Utilities",
    "wifi": "Utilities",

    # SUBSCRIPTIONS
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "amazon prime": "Subscriptions",
    "youtube": "Subscriptions",

    # BANK & TRANSFER
    "upi": "Transfers",
    "imps": "Transfers",
    "neft": "Transfers",

    # CASH
    "atm": "Cash Withdrawal"
}





#Categorizing expenses of csv
def categorize_expense(description):

    # protect against NaN / None / non-text values
    if description is None:
        return "Miscellaneous"

    desc = str(description).lower().strip()


    if desc == "":
        return "Miscellaneous"

    #Merchant detection
    for keyword, category in MERCHANT_APP.items():
        if keyword in desc:
            return category

    #Detect personal transfers (names)
    if re.fullmatch(r"[a-zA-Z]+",desc) and len(desc) <20:
        return "Transfers"

    #Detect numeric numeric merchant codes
    if any(char.isdigit() for char in desc) and len(desc) < 10:
        return "Transfers"
        
    return "Miscellaneous"

def detect_subscription(description, history):
    desc=str(description).lower()
    for past in history:
        if past.lower() == desc:
            return True
        return False

def learn_user_category(description, category, save_mapping):
    save_mapping(description.lower(), category)
    
def expense_exists(existing_expenses, category, amount):

    category = category.strip().lower()
    amount = round(float(amount), 2)

    for cat, amt in existing_expenses:
        if cat.strip().lower() == category and round(float(amt), 2) == amount:
            return True
    return False

def process_csv(file, user_id,get_expenses, add_expense):
    df=pd.read_csv(file)
    df.columns = [str(col).strip().lower() for col in df.columns]

    existing = get_expenses(user_id)
    added_count=0
    # possible columns used by banks
    description_cols = [
        "description", "narration", "remarks",
        "details", "transaction details", "mode"
    ]

    amount_cols = [
        "amount", "withdrawal", "debit", "spent"
    ]

    desc_col = next((c for c in description_cols if c in df.columns), None)
    amt_col = next((c for c in amount_cols if c in df.columns), None)

    if not amt_col:
        return "invalid", 0

    for _, row in df.iterrows():

        amount = row.get(amt_col, 0)

        if pd.isna(amount):
            continue

        amount = float(amount)

        # skip income
        if amount > 0:
            continue

        # combine text fields for smarter detection
        text_parts = []

        for col in description_cols:
            if col in df.columns:
                value = row.get(col)
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)

        description = " ".join(text_parts)

        category = categorize_expense(description)
        amount_clean = round(abs(amount), 2)

        if not expense_exists(existing, category, amount_clean):
            add_expense(user_id, category, amount_clean)
            added_count += 1

    return "success", added_count


#REAL TIME FINANCIAL SNAPSHOT
def calculate_health_score(income, total_expense, category_totals):
    if income<=0:
        return 0
    savings_percent=((income-total_expense)/income) * 100
    health_score=100
    if total_expense>income:
        health_score-=40
    if savings_percent<10:
        health_score-=30
    elif savings_percent<20:
        health_score-=15
    
    for total in category_totals.values():
        percent =((total/income)) * 100
        if percent>50:
            health_score-=15
        elif percent>30:
            health_score-=5
    return max(0, min(health_score,100))

# REAL-TIME RISK DETECTION
def detect_risks(income, total_expense, category_totals):
    risks=[]
    if income<=0:
        return risks
    savings_percent=((income-total_expense)/income) * 100

    if total_expense>income:  #Overspendig risk
        risks.append(("Overspending", 90))   #severity=90
    
    if savings_percent<10:    #Low savings risk
        risks.append(("Critically low savings", 70))
    elif savings_percent<20:
        risks.append(("Moderate savings risk",50))

    for category,total in category_totals.items(): #Category dominance risk
        percent=(total/income)*100
        if percent> 50:
            risks.append((f"{category} Spending Extremely High", 60))
        elif percent>30:
            risks.append((f"{category} Spending High", 40))
    return risks

# RECOMMENDATION ACTION ENGINE    
def generate_recommendation(highest_risk, income, total_expense, category_totals):    
    risk_type=highest_risk[0]

    if risk_type == 'Overspending':
        overspend_amount= total_expense-income  
        return (f"You are overspending by **₹{overspend_amount:.0f}**." , "Reduce discretionary spending immediately to restore balance.")

    if risk_type == "Critically low savings":
        target_savings = income * 0.2
        required_cut = target_savings - (income - total_expense)
        return (f"You need to reduce spending by **₹{required_cut:.0f}** to reach a healthy 20% rate." , "Identify non-essential expenses and cut at least 10–15%.")

    if "Spending" in risk_type:
        for category, total in category_totals.items():
            percent=(total/income) * 100
            if percent > 30:
                suggested_reduction= total *0.1
                return (f"Your spending on category **{category}** is High." , f"Reduce it by approximately **₹{suggested_reduction:.0f}** to rebalance your budget")
                break
    return (" Financial Status Stable", "No major financial risks detected.")
#to here}


def run_simulation(mode, income, total_expense, category_totals, reduction_percent, category=None):
    if income <=0:
        return None
    if mode == "overspending":
        return simulate_overspending(income, total_expense, category_totals)
    elif mode == "low savings":
        return simulate_low_savings(income, total_expense, category_totals,reduction_percent)
    elif mode == "category" and category is not None:
        return simulate_category(income, total_expense, category_totals, reduction_percent, category)
    elif mode == "optimization":
        return simulate_optimization(income, total_expense, category_totals, reduction_percent)

    return None

def simulate_overspending(income, total_expense, category_totals):
    new_total_expense= income
    new_savings_percent=0
    new_health_score=calculate_health_score(income,new_total_expense,category_totals)

    return {"type": "overspending","message": "If you eliminate overspending" ,"new_savings_percent":new_savings_percent, "new_health_score":new_health_score}

def simulate_low_savings(income, total_expense, category_totals, reduction_percent):
    reduced_amount = total_expense * (reduction_percent / 100)
    new_total_expense = total_expense - reduced_amount
    new_savings = income - new_total_expense
    new_savings_percent = (new_savings / income) * 100

    new_health_score = calculate_health_score(
        income,
        new_total_expense,
        category_totals
    )

    return {"type": "low_savings","message": f"If you reduce overall expenses by {reduction_percent}%:","new_savings_percent": new_savings_percent,"new_health_score": new_health_score}

def simulate_category(income, total_expense, category_totals, reduction_percent, category):
    reduced_amount= category_totals[category] * (reduction_percent/100)
    updated_categories= {k: (v -reduced_amount if k==category else v) for k,v in category_totals.items()} 
    new_total_expense=total_expense-reduced_amount
    new_savings=income-new_total_expense
    new_savings_percent=(new_savings/income) * 100

    new_health_score= calculate_health_score(income,new_total_expense,category_totals)

    return  {"type": "category", "message": f"If you reduce {category} by {reduction_percent}%:","new_savings_percent": new_savings_percent,"new_health_score": new_health_score}

def simulate_optimization(income, total_expense, category_totals, reduction_percent):

    reduced_amount = total_expense * (reduction_percent / 100)
    new_total_expense = total_expense - reduced_amount
    new_savings = income - new_total_expense
    new_savings_percent = (new_savings / income) * 100

    new_health_score = calculate_health_score(income,new_total_expense,category_totals)

    return {"type": "optimization","message": f"If you reduce overall expenses by {reduction_percent}%:","new_savings_percent": new_savings_percent,"new_health_score": new_health_score}


def projection_savings(income, total_expense, months=3):
    monthly_savings= income -total_expense
    projected_amount= monthly_savings * months
    return {'monthly_savings': monthly_savings, 'projected_amount': projected_amount}


