import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="FirstCry Store Auditor", layout="wide")

# --- DATABASE LOGIC ---
HISTORY_FILE = "cashbook_history.csv"

def save_entry(data):
    file_exists = os.path.isfile(HISTORY_FILE)
    df_history = pd.DataFrame([data])
    df_history.to_csv(HISTORY_FILE, mode='a', index=False, header=not file_exists)

st.title("🏦 FirstCry Automated Cashbook & Audit")
st.markdown("---")

# 1. SIDEBAR: POS DATA SYNC
st.sidebar.header("Step 1: Admin POS Sync")
uploaded_file = st.sidebar.file_uploader("Upload Today's Daywise Report (CSV)", type="csv")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📊 Monthly Variance Dashboard"])

if uploaded_file:
    # Read and rigorously clean the POS data
    df_pos = pd.read_csv(uploaded_file)
    df_pos.columns = df_pos.columns.str.strip()
    df_pos['Date'] = df_pos['Date'].astype(str).str.strip() # Remove the annoying spaces

    with tab1:
        st.header("Today's Cash Reconciliation")
        with st.form("audit_form"):
            audit_date = st.date_input("Audit Date", datetime.now())
            
            # Collection Entry
            st.subheader("1. Manager Collection Entry (What you actually received)")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash Collected (₹)", min_value=0.0, step=1.0)
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
                bank_dep = st.number_input("Bank Deposit Amount (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify, Save & Show Variance")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            # Filter POS data for selected date
            pos_row = df_pos[df_pos['Date'] == search_date]
            
            if pos_row.empty:
                st.error(f"❌ Date {search_date} not found in POS report. Check your date selection.")
            else:
                # Calculations
                pos_cash = pos_row.iloc[0]['ReceivedCashAmount']
                pos_upi = pos_row.iloc[0]['WalletAmount']
                pos_card = pos_row.iloc[0]['CardAmount']

                expected_cash = pos_cash + (manual_amt if manual_mode == "Cash" else 0)
                expected_upi = pos_upi + (manual_amt if manual_mode == "UPI" else 0)
                expected_card = pos_card + (manual_amt if manual_mode == "Card" else 0)

                note_total = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10)
                coin_total = (c5*5) + (c2*2) + (c1*1)
                grand_physical = note_total + coin_total
                
                # Save Data
                save_entry({
                    "Date": search_date,
                    "Actual_Cash": mgr_cash, "POS_Cash_Exp": expected_cash,
                    "Actual_UPI": mgr_upi, "POS_UPI_Exp": expected_upi,
                    "Actual_Card": mgr_card, "POS_Card_Exp": expected_card,
                    "Physical_Drawer": grand_physical, "Bank_Deposit": bank_dep
                })
                
                st.success(f"✅ Data Logged! Physical Tally: ₹{grand_physical}")

                # --- VISUAL VARIANCE DASHBOARD ---
                st.markdown("---")
                st.header("Daily Variance Audit")
                
                drawer_var = grand_physical - mgr_cash
                if drawer_var == 0:
                    st.info(f"✅ Drawer Match: Physical cash exactly matches entered amount.")
                else:
                    st.error(f"⚠️ Drawer Discrepancy: Physical cash is ₹{drawer_var} vs entered amount.")

                v1, v2, v3 = st.columns(3)
                v1.metric("CASH vs POS", f"₹{mgr_cash}", f"{round(mgr_cash - expected_cash, 2)} Var", delta_color="inverse")
                v2.metric("UPI vs POS", f"₹{mgr_upi}", f"{round(mgr_upi - expected_upi, 2)} Var", delta_color="inverse")
                v3.metric("CARD vs POS", f"₹{mgr_card}", f"{round(mgr_card - expected_card, 2)} Var", delta_color="inverse")
                
                if (mgr_cash == expected_cash) and (drawer_var == 0):
                    st.balloons()

    with tab2:
        st.header("Monthly Actuals vs POS Comparison")
        if os.path.isfile(HISTORY_FILE):
            h_df = pd.read_csv(HISTORY_FILE)
            
            # Recalculate Variances for the Table
            h_df['Cash_Var'] = h_df['Actual_Cash'] - h_df['POS_Cash_Exp']
            h_df['UPI_Var'] = h_df['Actual_UPI'] - h_df['POS_UPI_Exp']
            h_df['Card_Var'] = h_df['Actual_Card'] - h_df['POS_Card_Exp']
            h_df['Drawer_Tally'] = h_df['Physical_Drawer'] - h_df['Actual_Cash']

            # Define Table Columns
            table_cols = [
                'Date', 'Actual_Cash', 'POS_Cash_Exp', 'Cash_Var',
                'Actual_UPI', 'POS_UPI_Exp', 'UPI_Var',
                'Actual_Card', 'POS_Card_Exp', 'Card_Var',
                'Physical_Drawer', 'Drawer_Tally', 'Bank_Deposit'
            ]
            
            # Display Table with Highlighting
            st.dataframe(h_df[table_cols].style.background_gradient(cmap='RdYlGn', subset=['Cash_Var', 'UPI_Var', 'Card_Var']), use_container_width=True)

            st.markdown("---")
            sum_col1, sum_col2 = st.columns(2)
            sum_col1.metric("Net Monthly Cash Variance", f"₹{round(h_df['Cash_Var'].sum(), 2)}", delta_color="inverse")
            sum_col2.metric("Total Bank Deposits", f"₹{round(h_df['Bank_Deposit'].sum(), 2)}")
        else:
            st.info("No data in history. Please submit an audit entry first.")
else:
    st.warning("Please upload the POS Report CSV in the sidebar.")
