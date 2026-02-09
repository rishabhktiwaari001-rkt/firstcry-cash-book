import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FirstCry Store Auditor", layout="wide")

# --- DATABASE LOGIC ---
# This creates a file to store all manager entries permanently
HISTORY_FILE = "cashbook_history.csv"

def save_entry(data):
    file_exists = os.path.isfile(HISTORY_FILE)
    df_history = pd.DataFrame([data])
    df_history.to_csv(HISTORY_FILE, mode='a', index=False, header=not file_exists)

# --- APP INTERFACE ---
st.title("🏦 FirstCry Automated Cashbook")
st.markdown("---")

# 1. SIDEBAR: POS DATA SYNC
st.sidebar.header("Step 1: Admin POS Sync")
uploaded_file = st.sidebar.file_uploader("Upload Today's Daywise Report (CSV)", type="csv")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📊 Monthly Cashbook Report"])

if uploaded_file:
    df_pos = pd.read_csv(uploaded_file)
    df_pos.columns = df_pos.columns.str.strip()
    df_pos['Date'] = df_pos['Date'].astype(str).str.strip()

    with tab1:
        st.header("Today's Cash Reconciliation")
        with st.form("audit_form"):
            audit_date = st.date_input("Audit Date", datetime.now())
            
            # Collection Entry
            st.subheader("1. Manager Collection Entry")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash in Drawer (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("Actual UPI Collected (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Actual Card Collected (₹)", min_value=0.0, step=1.0)
            
            # Manual Billing
            st.markdown("---")
            st.subheader("2. Manual Billing (Sales not in POS)")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Mode", ["None", "Cash", "UPI", "Card"])

            # Denominations
            st.markdown("---")
            st.subheader("3. Physical Cash Denominations")
            col_notes, col_coins = st.columns(2)
            with col_notes:
                st.write("**Notes**")
                n500 = st.number_input("500 x", min_value=0, step=1)
                n200 = st.number_input("200 x", min_value=0, step=1)
                n100 = st.number_input("100 x", min_value=0, step=1)
                n50 = st.number_input("50 x", min_value=0, step=1)
                n20 = st.number_input("20 x", min_value=0, step=1)
                n10 = st.number_input("10 x", min_value=0, step=1)
            
            with col_coins:
                st.write("**Coins**")
                c5 = st.number_input("5 x", min_value=0, step=1)
                c2 = st.number_input("2 x", min_value=0, step=1)
                c1 = st.number_input("1 x", min_value=0, step=1)
                st.write("---")
                bank_dep = st.number_input("Bank Deposit (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify & Save to Cashbook")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            pos_row = df_pos[df_pos['Date'].str.contains(audit_date.strftime("%d-%m-%Y"))]
            
            if pos_row.empty:
                st.error(f"Date {search_date} not found in POS report.")
            else:
                # Calculations
                note_total = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10)
                coin_total = (c5*5) + (c2*2) + (c1*1)
                grand_physical = note_total + coin_total
                
                # Save Data
                entry_data = {
                    "Date": search_date,
                    "Actual_Cash": mgr_cash,
                    "Actual_UPI": mgr_upi,
                    "Actual_Card": mgr_card,
                    "Manual_Amt": manual_amt,
                    "Manual_Mode": manual_mode,
                    "Physical_Drawer": grand_physical,
                    "Bank_Deposit": bank_dep,
                    "Timestamp": datetime.now()
                }
                save_entry(entry_data)
                
                st.success(f"✅ Data saved to Monthly Cashbook! Physical Count: ₹{grand_physical}")
                st.balloons()

    with tab2:
        st.header("Actual Cashbook vs POS Report")
        
        if os.path.isfile(HISTORY_FILE):
            # Load Manager Actuals
            df_actuals = pd.read_csv(HISTORY_FILE)
            
            # Merge with POS Data
            # Note: We take the latest POS report uploaded and compare
            comparison_df = df_actuals.merge(df_pos[['Date', 'ReceivedCashAmount', 'WalletAmount', 'CardAmount']], on="Date", how="left")
            
            # Rename for Clarity
            comparison_df = comparison_df.rename(columns={
                'ReceivedCashAmount': 'POS_Cash',
                'WalletAmount': 'POS_UPI',
                'CardAmount': 'POS_Card'
            })

            # Create the Side-by-Side Display
            # Logic: Compare Mgr Actuals + Manual vs POS
            st.write("### Monthly Comparison Table")
            st.dataframe(comparison_df[['Date', 'Actual_Cash', 'POS_Cash', 'Actual_UPI', 'POS_UPI', 'Actual_Card', 'POS_Card', 'Physical_Drawer', 'Bank_Deposit']], use_container_width=True)
            
            # Monthly Summary Metrics
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Actual Cash", f"₹{round(comparison_df['Actual_Cash'].sum(), 2)}")
            m2.metric("Total Bank Deposits", f"₹{round(comparison_df['Bank_Deposit'].sum(), 2)}")
            m3.metric("Total Physical in Drawer", f"₹{round(comparison_df['Physical_Drawer'].sum(), 2)}")
        else:
            st.info("No entries found yet. Complete a Daily Audit to see the Monthly Dashboard.")

else:
    st.warning("Please upload the Daywise Report CSV in the sidebar to begin.")
