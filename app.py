import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FirstCry Cash Auditor", layout="wide")

# --- DATABASE LOGIC ---
HISTORY_FILE = "cashbook_history.csv"

def save_entry(data):
    file_exists = os.path.isfile(HISTORY_FILE)
    df_history = pd.DataFrame([data])
    df_history.to_csv(HISTORY_FILE, mode='a', index=False, header=not file_exists)

# --- UI HEADER ---
st.title("🏦 FirstCry Automated Cashbook & Audit")
st.markdown("---")

# 1. SIDEBAR: POS DATA SYNC
st.sidebar.header("Step 1: Admin POS Sync")
uploaded_file = st.sidebar.file_uploader("Upload Today's Daywise Report (CSV)", type="csv")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📊 Monthly Variance Dashboard"])

if uploaded_file:
    df_pos = pd.read_csv(uploaded_file)
    df_pos.columns = df_pos.columns.str.strip()
    df_pos['Date'] = df_pos['Date'].astype(str).str.strip()

    with tab1:
        st.header("Today's Cash Reconciliation")
        with st.form("audit_form"):
            audit_date = st.date_input("Audit Date", datetime.now())
            
            # Collection Entry
            st.subheader("1. Manager Collection Entry (Actual Collected)")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("Actual UPI (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Actual Card (₹)", min_value=0.0, step=1.0)
            
            # Manual Billing
            st.markdown("---")
            st.subheader("2. Manual Billing (Sales not in POS)")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Payment Mode for Manual Sale", ["None", "Cash", "UPI", "Card"])

            # Denominations
            st.markdown("---")
            st.subheader("3. Physical Cash Denominations (Notes & Coins)")
            col_notes, col_coins = st.columns(2)
            with col_notes:
                n500 = st.number_input("500 x", min_value=0, step=1)
                n200 = st.number_input("200 x", min_value=0, step=1)
                n100 = st.number_input("100 x", min_value=0, step=1)
                n50 = st.number_input("50 x", min_value=0, step=1)
                n20 = st.number_input("20 x", min_value=0, step=1)
                n10 = st.number_input("10 x", min_value=0, step=1)
            
            with col_coins:
                c5 = st.number_input("5 x", min_value=0, step=1)
                c2 = st.number_input("2 x", min_value=0, step=1)
                c1 = st.number_input("1 x", min_value=0, step=1)
                st.write("---")
                bank_dep = st.number_input("Amount Deposited in Bank (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify, Show Variance & Save")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            pos_row = df_pos[df_pos['Date'].str.contains(audit_date.strftime("%d-%m-%Y"))]
            
            if pos_row.empty:
                st.error(f"Date {search_date} not found in POS report.")
            else:
                # 1. System Expectations
                pos_cash = pos_row.iloc[0]['ReceivedCashAmount']
                pos_upi = pos_row.iloc[0]['WalletAmount']
                pos_card = pos_row.iloc[0]['CardAmount']

                expected_cash = pos_cash + (manual_amt if manual_mode == "Cash" else 0)
                expected_upi = pos_upi + (manual_amt if manual_mode == "UPI" else 0)
                expected_card = pos_card + (manual_amt if manual_mode == "Card" else 0)

                # 2. Denomination Total
                grand_physical = (n500*500)+(n200*200)+(n100*100)+(n50*50)+(n20*20)+(n10*10)+(c5*5)+(c2*2)+(c1*1)
                
                # 3. Save to History
                save_entry({
                    "Date": search_date,
                    "Actual_Cash": mgr_cash, "POS_Cash_Exp": expected_cash,
                    "Actual_UPI": mgr_upi, "POS_UPI_Exp": expected_upi,
                    "Actual_Card": mgr_card, "POS_Card_Exp": expected_card,
                    "Physical_Drawer": grand_physical, "Bank_Deposit": bank_dep
                })
                
                # 4. RESULTS (The Variance View you liked)
                st.markdown("---")
                st.header("Step 3: Audit & Variance Report")
                
                # Tally Check
                drawer_var = grand_physical - mgr_cash
                if drawer_var == 0:
                    st.success(f"✅ Cash Drawer Tally: PERFECT (₹{grand_physical})")
                else:
                    st.error(f"❌ Cash Drawer Mismatch: ₹{drawer_var} (Physical: {grand_physical} vs Entry: {mgr_cash})")

                # Metrics with Clear Variance
                v1, v2, v3 = st.columns(3)
                v1.metric("CASH Variance", f"₹{mgr_cash}", f"{round(mgr_cash - expected_cash, 2)} vs POS", delta_color="inverse")
                v2.metric("UPI Variance", f"₹{mgr_upi}", f"{round(mgr_upi - expected_upi, 2)} vs POS", delta_color="inverse")
                v3.metric("CARD Variance", f"₹{mgr_card}", f"{round(mgr_card - expected_card, 2)} vs POS", delta_color="inverse")
                
                if (mgr_cash == expected_cash) and (drawer_var == 0):
                    st.balloons()

    with tab2:
        st.header("Monthly Actuals vs POS (Side-by-Side Variance)")
        
        if os.path.isfile(HISTORY_FILE):
            history_df = pd.read_csv(HISTORY_FILE)
            
            # Calculate Variances for the table
            history_df['Cash_Var'] = history_df['Actual_Cash'] - history_df['POS_Cash_Exp']
            history_df['UPI_Var'] = history_df['Actual_UPI'] - history_df['POS_UPI_Exp']
            history_df['Card_Var'] = history_df['Actual_Card'] - history_df['POS_Card_Exp']
            history_df['Drawer_Tally'] = history_df['Physical_Drawer'] - history_df['Actual_Cash']

            # Display Table
            cols_to_show = [
                'Date', 
                'Actual_Cash', 'POS_Cash_Exp', 'Cash_Var',
                'Actual_UPI', 'POS_UPI_Exp', 'UPI_Var',
                'Actual_Card', 'POS_Card_Exp', 'Card_Var',
                'Physical_Drawer', 'Drawer_Tally', 'Bank_Deposit'
            ]
            
            st.dataframe(history_df[cols_to_show].style.applymap(
                lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x < 0 else ('background-color: #ccffcc' if isinstance(x, (int, float)) and x > 0 else ''),
                subset=['Cash_Var', 'UPI_Var', 'Card_Var', 'Drawer_Tally']
            ), use_container_width=True)

            st.markdown("---")
            # Summary
            s1, s2, s3 = st.columns(3)
            s1.metric("Total Monthly Sales (Actual)", f"₹{round(history_df['Actual_Cash'].sum() + history_df['Actual_UPI'].sum() + history_df['Actual_Card'].sum(), 2)}")
            s2.metric("Net Cash Variance", f"₹{round(history_df['Cash_Var'].sum(), 2)}", delta_color="inverse")
            s3.metric("Total Bank Deposits", f"₹{round(history_df['Bank_Deposit'].sum(), 2)}")
        else:
            st.info("No entries found yet. Complete an audit to see history.")

else:
    st.warning("Please upload the Daywise Report CSV in the sidebar.")
