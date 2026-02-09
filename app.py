import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Store Cash Auditor", layout="centered")

st.title("💳 Store Cashbook & Audit")
st.info("Upload the POS report and enter today's collections (including manual bills) to tally.")

# 1. POS REPORT UPLOAD
st.sidebar.header("Step 1: POS Sync")
uploaded_file = st.sidebar.file_uploader("Upload Today's Report (CSV)", type="csv")

# 2. MANAGER INPUT SECTION
st.header("Step 2: Manager Daily Entry")
with st.form("cash_form"):
    audit_date = st.date_input("Select Audit Date", datetime.now())
    
    # Standard POS collections
    st.subheader("POS Collections")
    c1, c2, c3 = st.columns(3)
    mgr_cash = c1.number_input("Cash in Drawer (₹)", min_value=0.0, step=1.0)
    mgr_upi = c2.number_input("UPI/Wallet Total (₹)", min_value=0.0, step=1.0)
    mgr_card = c3.number_input("Card Total (₹)", min_value=0.0, step=1.0)
    
    # NEW: Manual Billing Section
    st.markdown("---")
    st.subheader("Manual Billing (Sales not in POS)")
    m_col1, m_col2 = st.columns(2)
    manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
    manual_mode = m_col2.selectbox("Payment Mode for Manual Sale", ["None", "Cash", "UPI", "Card"])
    
    st.markdown("---")
    st.subheader("Denominations (Notes Count)")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        n500 = d_col1.number_input("500s", min_value=0, step=1)
        n200 = d_col1.number_input("200s", min_value=0, step=1)
        n100 = d_col1.number_input("100s", min_value=0, step=1)
    with d_col2:
        n50 = d_col2.number_input("50s", min_value=0, step=1)
        n20 = d_col2.number_input("20s", min_value=0, step=1)
        n10 = d_col2.number_input("10s", min_value=0, step=1)
    
    coins = st.number_input("Coins Total Value (₹)", min_value=0.0, step=1.0)
    bank_dep = st.number_input("Bank Deposit Amount (₹)", min_value=0.0, step=1.0)

    submit = st.form_submit_button("Verify & Tally")

# 3. AUDIT LOGIC
if submit:
    if not uploaded_file:
        st.warning("Please upload the POS Report in the sidebar first!")
    else:
        # Load data
        df = pd.read_csv(uploaded_file)
        formatted_date = audit_date.strftime("%d-%m-%Y")
        
        # Searching for the row matching the date
        pos_row = df[df.iloc[:, 0].astype(str).str.contains(audit_date.strftime("%d-%m-%Y"))]
        
        if pos_row.empty:
            st.error(f"Data for {formatted_date} not found in the report.")
        else:
            # Extract figures (Adjust column names/indices as per your specific report format)
            pos_cash = pos_row.iloc[0]['ReceivedCashAmount']
            pos_upi = pos_row.iloc[0]['WalletAmount']
            pos_card = pos_row.iloc[0]['CardAmount']
            
            # Adjust POS figures to include Manual Sales
            expected_cash = pos_cash + (manual_amt if manual_mode == "Cash" else 0)
            expected_upi = pos_upi + (manual_amt if manual_mode == "UPI" else 0)
            expected_card = pos_card + (manual_amt if manual_mode == "Card" else 0)
            
            # Physical Cash Calculation
            physical_calc = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10) + coins
            
            st.markdown("---")
            st.header("Step 3: Audit Results")
            
            # 1. Drawer Tally (Actual physical vs Manager's manual entry)
            drawer_diff = physical_calc - mgr_cash
            if drawer_diff == 0:
                st.success(f"✅ Cash Drawer Tally: PERFECT (₹{physical_calc})")
            else:
                st.error(f"❌ Cash Drawer Mismatch: ₹{drawer_diff}")

            # 2. POS + Manual vs Entry Comparison
            st.subheader("System (POS + Manual) vs Actual Entry")
            c1, c2, c3 = st.columns(3)
            c1.metric("Cash", f"₹{mgr_cash}", f"{round(mgr_cash - expected_cash, 2)} Var", delta_color="inverse")
            c2.metric("UPI", f"₹{mgr_upi}", f"{round(mgr_upi - expected_upi, 2)} Var", delta_color="inverse")
            c3.metric("Card", f"₹{mgr_card}", f"{round(mgr_card - expected_card, 2)} Var", delta_color="inverse")
            
            if (mgr_cash == expected_cash) and (drawer_diff == 0):
                st.balloons()
