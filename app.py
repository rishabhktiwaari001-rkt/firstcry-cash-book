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
    # Ensure we save with headers only the first time
    df_history.to_csv(HISTORY_FILE, mode='a', index=False, header=not file_exists)

# --- SIDEBAR TOOLS ---
st.sidebar.header("🛠️ Admin Tools")
if st.sidebar.button("Delete History (Clear App Data)"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        st.sidebar.success("History deleted! You can start fresh.")
    else:
        st.sidebar.info("No history file found.")

st.sidebar.markdown("---")
st.sidebar.header("Step 1: Admin POS Sync")
uploaded_file = st.sidebar.file_uploader("Upload 'Daywise Report.csv'", type="csv")

st.title("🏦 FirstCry Automated Cashbook & Audit")
st.markdown("---")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📊 Monthly Variance Dashboard"])

if uploaded_file:
    # --- AUTOMATIC CLEANING TO PREVENT KEY ERRORS ---
    df_pos = pd.read_csv(uploaded_file)
    # 1. Strip spaces from column names
    df_pos.columns = df_pos.columns.str.strip()
    # 2. Strip spaces from the Date column values
    df_pos['Date'] = df_pos['Date'].astype(str).str.strip()
    
    with tab1:
        st.header("Today's Cash Reconciliation")
        with st.form("audit_form"):
            audit_date = st.date_input("Audit Date", datetime.now())
            
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash Collected (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("Actual UPI Collected (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Actual Card Collected (₹)", min_value=0.0, step=1.0)
            
            st.markdown("---")
            st.subheader("Manual Billing / Note Counts")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Mode", ["None", "Cash", "UPI", "Card"])

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

            submit = st.form_submit_button("Verify & Save to Cashbook")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            # Using .str.contains to handle any weird formatting
            pos_row = df_pos[df_pos['Date'].str.contains(search_date)]
            
            if pos_row.empty:
                st.error(f"Date {search_date} not found in the uploaded POS report.")
            else:
                # Calculations
                p_cash = pos_row.iloc[0]['ReceivedCashAmount']
                p_upi = pos_row.iloc[0]['WalletAmount']
                p_card = pos_row.iloc[0]['CardAmount']

                exp_cash = p_cash + (manual_amt if manual_mode == "Cash" else 0)
                exp_upi = p_upi + (manual_amt if manual_mode == "UPI" else 0)
                exp_card = p_card + (manual_amt if manual_mode == "Card" else 0)

                physical = (n500*500)+(n200*200)+(n100*100)+(n50*50)+(n20*20)+(n10*10)+(c5*5)+(c2*2)+(c1*1)
                
                # Save Data with Consistent Keys
                save_entry({
                    "Date": search_date,
                    "Actual_Cash": mgr_cash, "POS_Cash_Exp": exp_cash,
                    "Actual_UPI": mgr_upi, "POS_UPI_Exp": exp_upi,
                    "Actual_Card": mgr_card, "POS_Card_Exp": exp_card,
                    "Physical_Drawer": physical, "Bank_Deposit": bank_dep
                })
                
                st.markdown("---")
                st.header("Daily Variance Audit")
                v1, v2, v3 = st.columns(3)
                v1.metric("Cash vs POS", f"₹{mgr_cash}", f"{round(mgr_cash - exp_cash, 2)} Var", delta_color="inverse")
                v2.metric("UPI vs POS", f"₹{mgr_upi}", f"{round(mgr_upi - exp_upi, 2)} Var", delta_color="inverse")
                v3.metric("Card vs POS", f"₹{mgr_card}", f"{round(mgr_card - exp_card, 2)} Var", delta_color="inverse")
                
                if physical == mgr_cash and mgr_cash == exp_cash:
                    st.balloons()
                elif physical != mgr_cash:
                    st.warning(f"Drawer Mismatch: Physical is ₹{physical} but you entered ₹{mgr_cash}")

    with tab2:
        st.header("Monthly Actuals vs POS (Comparison)")
        if os.path.isfile(HISTORY_FILE):
            h_df = pd.read_csv(HISTORY_FILE)
            
            # --- SAFETY CHECK FOR KEY ERRORS ---
            required_cols = ['Actual_Cash', 'POS_Cash_Exp', 'Actual_UPI', 'POS_UPI_Exp', 'Actual_Card', 'POS_Card_Exp']
            if not all(col in h_df.columns for col in required_cols):
                st.error("The history file format is old. Please click 'Delete History' in the sidebar and submit a new entry.")
            else:
                h_df['Cash_Var'] = h_df['Actual_Cash'] - h_df['POS_Cash_Exp']
                h_df['UPI_Var'] = h_df['Actual_UPI'] - h_df['POS_UPI_Exp']
                h_df['Card_Var'] = h_df['Actual_Card'] - h_df['POS_Card_Exp']
                h_df['Drawer_Diff'] = h_df['Physical_Drawer'] - h_df['Actual_Cash']

                st.dataframe(h_df.style.background_gradient(cmap='RdYlGn', subset=['Cash_Var', 'UPI_Var', 'Card_Var']), use_container_width=True)
        else:
            st.info("No history yet. Submit an audit to see the dashboard.")
else:
    st.warning("Please upload the Daywise Report CSV in the sidebar.")
