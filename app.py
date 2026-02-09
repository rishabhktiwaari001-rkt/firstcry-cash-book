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

# --- ADMIN TOOLS (SIDEBAR) ---
st.sidebar.header("🛠️ Admin Controls")
if st.sidebar.button("🗑️ Reset All History"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        st.sidebar.success("History cleared! You can now start fresh.")
    else:
        st.sidebar.info("No history file found.")

st.sidebar.markdown("---")
st.sidebar.header("Step 1: Sync POS Data")
uploaded_file = st.sidebar.file_uploader("Upload 'Daywise Report.csv'", type="csv")

st.title("🏦 FirstCry Automated Cashbook & Audit")
st.markdown("---")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📊 Monthly Variance Dashboard"])

if uploaded_file:
    # --- RIGOROUS DATA CLEANING ---
    df_pos = pd.read_csv(uploaded_file)
    # Remove hidden spaces from column headers
    df_pos.columns = [col.strip() for col in df_pos.columns]
    # Remove hidden spaces from date values
    df_pos['Date'] = df_pos['Date'].astype(str).str.strip()
    
    with tab1:
        st.header("Daily Cash Reconciliation")
        with st.form("audit_form"):
            audit_date = st.date_input("Select Audit Date", datetime.now())
            
            # Collection Entry
            st.subheader("1. Manager Collection Entry (Actuals)")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash Collected (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("Actual UPI Collected (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Actual Card Collected (₹)", min_value=0.0, step=1.0)
            
            # Manual Billing
            st.markdown("---")
            st.subheader("2. Manual Billing (Not in POS)")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Mode", ["None", "Cash", "UPI", "Card"])

            # Denominations
            st.markdown("---")
            st.subheader("3. Physical Cash Denominations")
            col_den, col_bank = st.columns(2)
            with col_den:
                n500 = st.number_input("500 x", min_value=0, step=1)
                n200 = st.number_input("200 x", min_value=0, step=1)
                n100 = st.number_input("100 x", min_value=0, step=1)
                n50 = st.number_input("50 x", min_value=0, step=1)
                n20 = st.number_input("20 x", min_value=0, step=1)
                n10 = st.number_input("10 x", min_value=0, step=1)
                c5 = st.number_input("5 x", min_value=0, step=1)
                c2 = st.number_input("2 x", min_value=0, step=1)
                c1 = st.number_input("1 x", min_value=0, step=1)
            
            with col_bank:
                bank_dep = st.number_input("Bank Deposit (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify, Save & Show Variance")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            # Find the row in the cleaned POS data
            pos_row = df_pos[df_pos['Date'].str.contains(search_date)]
            
            if pos_row.empty:
                st.error(f"❌ Date '{search_date}' not found in the uploaded report.")
            else:
                # Safer Extraction
                p_cash = pos_row.iloc[0]['ReceivedCashAmount']
                p_upi = pos_row.iloc[0]['WalletAmount']
                p_card = pos_row.iloc[0]['CardAmount']

                # Adjust for Manual Bills
                exp_cash = p_cash + (manual_amt if manual_mode == "Cash" else 0)
                exp_upi = p_upi + (manual_amt if manual_mode == "UPI" else 0)
                exp_card = p_card + (manual_amt if manual_mode == "Card" else 0)

                # Physical Total
                physical = (n500*500)+(n200*200)+(n100*100)+(n50*50)+(n20*20)+(n10*10)+(c5*5)+(c2*2)+(c1*1)
                
                # Save to History
                save_entry({
                    "Date": search_date,
                    "Actual_Cash": mgr_cash, "POS_Cash_Exp": exp_cash,
                    "Actual_UPI": mgr_upi, "POS_UPI_Exp": exp_upi,
                    "Actual_Card": mgr_card, "POS_Card_Exp": exp_card,
                    "Physical_Drawer": physical, "Bank_Deposit": bank_dep
                })
                
                # --- VISUAL VARIANCE REPORT ---
                st.markdown("---")
                st.header("Daily Audit Report")
                
                v1, v2, v3 = st.columns(3)
                v1.metric("Cash vs POS", f"₹{mgr_cash}", f"{round(mgr_cash - exp_cash, 2)} Var", delta_color="inverse")
                v2.metric("UPI vs POS", f"₹{mgr_upi}", f"{round(mgr_upi - exp_upi, 2)} Var", delta_color="inverse")
                v3.metric("Card vs POS", f"₹{mgr_card}", f"{round(mgr_card - exp_card, 2)} Var", delta_color="inverse")
                
                if physical == mgr_cash:
                    st.success(f"✅ Drawer Tally: Matches (₹{physical})")
                    if mgr_cash == exp_cash: st.balloons()
                else:
                    st.error(f"⚠️ Drawer Mismatch: Physical ₹{physical} vs Entered ₹{mgr_cash}")

    with tab2:
        st.header("Monthly Actuals vs POS Comparison")
        if os.path.isfile(HISTORY_FILE):
            h_df = pd.read_csv(HISTORY_FILE)
            
            # Key check for safety
            needed = ['Actual_Cash', 'POS_Cash_Exp', 'Actual_UPI', 'POS_UPI_Exp']
            if not all(k in h_df.columns for k in needed):
                st.error("⚠️ History file format error. Please click 'Reset All History' in the sidebar.")
            else:
                # Calculate Variances
                h_df['Cash_Var'] = h_df['Actual_Cash'] - h_df['POS_Cash_Exp']
                h_df['UPI_Var'] = h_df['Actual_UPI'] - h_df['POS_UPI_Exp']
                h_df['Card_Var'] = h_df['Actual_Card'] - h_df['POS_Card_Exp']
                h_df['Drawer_Diff'] = h_df['Physical_Drawer'] - h_df['Actual_Cash']

                st.dataframe(h_df.style.background_gradient(cmap='RdYlGn', subset=['Cash_Var', 'UPI_Var', 'Card_Var']), use_container_width=True)
        else:
            st.info("No entries yet. Submit an audit to see history.")
else:
    st.warning("Please upload the POS Report CSV in the sidebar.")
