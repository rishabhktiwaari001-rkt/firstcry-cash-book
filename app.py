import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="FirstCry Store Auditor", layout="wide")

# --- CONNECT TO GOOGLE SHEET (DIRECT METHOD) ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_worksheet():
    try:
        # Load credentials directly from the secrets you already added
        secrets = dict(st.secrets["connections"]["gsheets"])
        
        # Clean up the dict to match what google expects (remove the 'spreadsheet' key for auth)
        creds_dict = {k: v for k, v in secrets.items() if k != "spreadsheet"}
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open using the URL in your secrets
        sheet_url = secrets["spreadsheet"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

def get_history():
    sheet = get_worksheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_entry_to_sheet(new_entry):
    try:
        sheet = get_worksheet()
        # Convert dictionary values to a list in the correct order
        headers = [
            "Date", "Shift", "Manager", 
            "Actual_Cash", "POS_Cash_Exp", "Cash_Var", 
            "Actual_UPI", "POS_UPI_Exp", "UPI_Var", 
            "Actual_Card", "POS_Card_Exp", "Card_Var", 
            "Physical_Drawer", "Drawer_Diff", "Bank_Deposit"
        ]
        row_values = [new_entry.get(h, "") for h in headers]
        sheet.append_row(row_values)
        return True
    except Exception as e:
        st.error(f"Save Failed: {e}")
        return False

# --- COLORING FUNCTION ---
def color_variance(val):
    color = ''
    if isinstance(val, (int, float)):
        if val < -0.1: 
            color = 'background-color: #ffcccc; color: black'
        elif val > 0.1: 
            color = 'background-color: #ccffcc; color: black'
    return color

# --- UI START ---
st.title("🏦 FirstCry Cloud Cashbook")
st.markdown("---")

# SIDEBAR
st.sidebar.header("Step 1: Sync POS Data")
uploaded_file = st.sidebar.file_uploader("Upload 'Daywise Report.csv'", type="csv")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# TABS
tab1, tab2 = st.tabs(["📝 Daily Entry", "📊 Monthly Dashboard"])

if uploaded_file:
    try:
        df_pos = pd.read_csv(uploaded_file)
        df_pos.columns = [col.strip() for col in df_pos.columns]
        df_pos['Date'] = df_pos['Date'].astype(str).str.strip()
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()
    
    with tab1:
        st.header("Daily Audit")
        with st.form("audit_form"):
            col_date, col_shift, col_mgr = st.columns(3)
            audit_date = col_date.date_input("Date", datetime.now())
            shift_type = col_shift.selectbox("Audit Type", ["Day End Closing", "8:00 PM Handover"])
            mgr_name = col_mgr.text_input("Manager Name")

            st.markdown("---")
            st.subheader("1. Actual Collections")
            c1, c2, c3 = st.columns(3)
            mgr_cash = c1.number_input("Actual Cash (₹)", min_value=0.0)
            mgr_upi = c2.number_input("Actual UPI (₹)", min_value=0.0)
            mgr_card = c3.number_input("Actual Card (₹)", min_value=0.0)
            
            st.subheader("2. Manual Billing")
            m_col1, m_col2 = st.columns(2)
            manual_amt = m_col1.number_input("Manual Amt (₹)", min_value=0.0)
            manual_mode = m_col2.selectbox("Mode", ["None", "Cash", "UPI", "Card"])

            st.subheader("3. Physical Count")
            col_den, col_bank = st.columns(2)
            with col_den:
                st.write("Notes & Coins")
                n500 = st.number_input("500 x", 0); n200 = st.number_input("200 x", 0)
                n100 = st.number_input("100 x", 0); n50 = st.number_input("50 x", 0)
                n20 = st.number_input("20 x", 0); n10 = st.number_input("10 x", 0)
                c5 = st.number_input("Coin 5 x", 0); c2 = st.number_input("Coin 2 x", 0); c1 = st.number_input("Coin 1 x", 0)
            
            with col_bank:
                bank_dep = st.number_input("Bank Deposit (₹)", min_value=0.0)

            submit = st.form_submit_button("Verify & Save to Google Sheet")

        if submit:
            if not mgr_name:
                st.error("⚠️ Please enter Manager Name!")
            else:
                search_date = audit_date.strftime("%d-%m-%Y")
                pos_row = df_pos[df_pos['Date'].str.contains(search_date)]
                
                if pos_row.empty:
                    st.error(f"❌ Date {search_date} not found in POS Report.")
                else:
                    p_cash = pos_row.iloc[0]['ReceivedCashAmount']
                    p_upi = pos_row.iloc[0]['WalletAmount']
                    p_card = pos_row.iloc[0]['CardAmount']

                    exp_cash = p_cash + (manual_amt if manual_mode == "Cash" else 0)
                    exp_upi = p_upi + (manual_amt if manual_mode == "UPI" else 0)
                    exp_card = p_card + (manual_amt if manual_mode == "Card" else 0)

                    physical = (n500*500)+(n200*200)+(n100*100)+(n50*50)+(n20*20)+(n10*10)+(c5*5)+(c2*2)+(c1*1)
                    
                    entry = {
                        "Date": search_date,
                        "Shift": shift_type,
                        "Manager": mgr_name,
                        "Actual_Cash": mgr_cash, "POS_Cash_Exp": exp_cash, "Cash_Var": mgr_cash - exp_cash,
                        "Actual_UPI": mgr_upi, "POS_UPI_Exp": exp_upi, "UPI_Var": mgr_upi - exp_upi,
                        "Actual_Card": mgr_card, "POS_Card_Exp": exp_card, "Card_Var": mgr_card - exp_card,
                        "Physical_Drawer": physical, "Drawer_Diff": physical - mgr_cash,
                        "Bank_Deposit": bank_dep
                    }
                    
                    if save_entry_to_sheet(entry):
                        st.success("✅ Saved to Google Sheet!")
                        st.balloons()

    with tab2:
        st.header("Monthly Cloud Dashboard")
        try:
            h_df = get_history()
            
            if not h_df.empty:
                # Force numeric types to prevent "sum" errors
                cols_to_numeric = ['Actual_Cash', 'POS_Cash_Exp', 'Cash_Var', 'UPI_Var', 'Card_Var', 'Drawer_Diff', 'Bank_Deposit']
                for col in cols_to_numeric:
                    if col in h_df.columns:
                        h_df[col] = pd.to_numeric(h_df[col], errors='coerce').fillna(0)

                display_cols = ['Date', 'Shift', 'Manager', 'Actual_Cash', 'POS_Cash_Exp', 'Cash_Var', 'UPI_Var', 'Card_Var', 'Drawer_Diff', 'Bank_Deposit']
                available_cols = [c for c in display_cols if c in h_df.columns]
                
                st.dataframe(
                    h_df[available_cols].style.applymap(color_variance, subset=['Cash_Var', 'UPI_Var', 'Card_Var', 'Drawer_Diff']),
                    use_container_width=True
                )
                
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                # Safe summing
                cash_sum = h_df['Cash_Var'].sum() if 'Cash_Var' in h_df.columns else 0
                upi_sum = h_df['UPI_Var'].sum() if 'UPI_Var' in h_df.columns else 0
                dep_sum = h_df['Bank_Deposit'].sum() if 'Bank_Deposit' in h_df.columns else 0
                
                m1.metric("Net Cash Var", f"₹{round(cash_sum, 2)}", delta_color="inverse")
                m2.metric("Net UPI Var", f"₹{round(upi_sum, 2)}", delta_color="inverse")
                m3.metric("Bank Deposits", f"₹{round(dep_sum, 2)}")
            else:
                st.info("No data found in Google Sheet. Add your first entry!")
        except Exception as e:
            st.warning(f"Connecting to Sheet... Error: {e}")
else:
    st.warning("Please upload the POS Report CSV in the sidebar.")
