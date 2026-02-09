import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Store Cash Auditor", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Cashbook Audit & Performance Dashboard")
st.markdown("---")

# 1. SIDEBAR: POS DATA SYNC
st.sidebar.header("📊 Step 1: Data Sync")
uploaded_file = st.sidebar.file_uploader("Upload Today's Daywise Report (CSV)", type="csv")

# Create Tabs
tab1, tab2 = st.tabs(["📝 Daily Entry & Audit", "📈 Monthly Dashboard"])

if uploaded_file:
    # Load and Clean Data
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df['Date'] = df['Date'].astype(str).str.strip()

    with tab1:
        st.header("Daily Audit Entry")
        with st.form("audit_form"):
            audit_date = st.date_input("Audit Date", datetime.now())
            
            # Row 1: Manager Entry
            st.subheader("1. Manager Collection Entry")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Cash in Drawer (Actual) (₹)", min_value=0.0, step=1.0)
            mgr_upi = c2.number_input("UPI/Wallet Total (Actual) (₹)", min_value=0.0, step=1.0)
            mgr_card = c3.number_input("Card Sales Total (Actual) (₹)", min_value=0.0, step=1.0)
            
            # Row 2: Manual Billing
            st.markdown("---")
            st.subheader("2. Manual Billing (Not in POS)")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Sale Amount (₹)", min_value=0.0, step=1.0)
            manual_mode = m_col2.selectbox("Payment Mode for Manual Sale", ["None", "Cash", "UPI", "Card"])

            # Row 3: Denominations
            st.markdown("---")
            st.subheader("3. Physical Cash Denominations")
            
            col_notes, col_coins = st.columns(2)
            with col_notes:
                st.write("**Currency Notes**")
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
                st.write(" ") # Spacer
                bank_dep = st.number_input("Amount Deposited to Bank today (₹)", min_value=0.0, step=1.0)

            submit = st.form_submit_button("Verify & Run Audit")

        if submit:
            search_date = audit_date.strftime("%d-%m-%Y")
            pos_row = df[df['Date'].str.contains(audit_date.strftime("%d-%m-%Y"))]
            
            if pos_row.empty:
                st.error(f"❌ Error: Date {search_date} not found in the uploaded report.")
            else:
                # 1. System Calculations (POS + Manual)
                pos_cash = pos_row.iloc[0]['ReceivedCashAmount']
                pos_upi = pos_row.iloc[0]['WalletAmount']
                pos_card = pos_row.iloc[0]['CardAmount']

                # Adjust expectations based on manual billing
                expected_cash = pos_cash + (manual_amt if manual_mode == "Cash" else 0)
                expected_upi = pos_upi + (manual_amt if manual_mode == "UPI" else 0)
                expected_card = pos_card + (manual_amt if manual_mode == "Card" else 0)

                # 2. Physical Cash Calculation
                note_val = (n500*500) + (n200*200) + (n100*100) + (n50*50) + (n20*20) + (n10*10)
                coin_val = (c5*5) + (c2*2) + (c1*1)
                total_physical = note_val + coin_val

                st.markdown("---")
                st.header("Step 3: Audit Results")

                # Results: Tally Check
                if total_physical == mgr_cash:
                    st.success(f"✅ Cash Drawer Tally: PERFECT. Physical cash matches Manager entry (₹{total_physical}).")
                else:
                    st.error(f"❌ Cash Drawer Mismatch! Physical: ₹{total_physical} vs Entry: ₹{mgr_cash}. Gap: ₹{round(total_physical - mgr_cash, 2)}")

                # Comparison Metrics
                r1, r2, r3 = st.columns(3)
                r1.metric("Cash (POS+Manual)", f"₹{mgr_cash}", f"{round(mgr_cash - expected_cash, 2)} Var", delta_color="inverse")
                r2.metric("UPI (POS+Manual)", f"₹{mgr_upi}", f"{round(mgr_upi - expected_upi, 2)} Var", delta_color="inverse")
                r3.metric("Card (POS+Manual)", f"₹{mgr_card}", f"{round(mgr_card - expected_card, 2)} Var", delta_color="inverse")
                
                if (mgr_cash == expected_cash) and (total_physical == mgr_cash):
                    st.balloons()

    with tab2:
        st.header("Monthly Performance Dashboard")
        st.write("Summary of all store activities based on the current POS report.")
        
        # Clean data for display
        display_df = df[['Date', 'TotalBills', 'ReceivedCashAmount', 'WalletAmount', 'CardAmount', 'TotalPrice']].copy()
        display_df.columns = ['Date', 'Bills', 'Cash (₹)', 'UPI (₹)', 'Card (₹)', 'Total Sales (₹)']
        
        st.dataframe(display_df, use_container_width=True)

        st.markdown("---")
        # Summary Statistics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Sales", f"₹{round(df['TotalPrice'].sum(), 2)}")
        m2.metric("Total Cash", f"₹{round(df['ReceivedCashAmount'].sum(), 2)}")
        m3.metric("Total Bills", f"{df['TotalBills'].sum()}")
        m4.metric("Avg Bill Value", f"₹{round(df['TotalPrice'].sum() / df['TotalBills'].sum(), 2)}")

else:
    st.warning("Please upload the Daywise Report CSV in the sidebar to view the dashboard.")
