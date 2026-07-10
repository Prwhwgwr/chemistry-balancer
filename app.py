import streamlit as st
from chempy import balance_stoichiometry
import time
import extra_streamlit_components as stx
import gspread

# --- Page Configuration ---
st.set_page_config(page_title="🧪 Chemical Equation Balancer", page_icon="🧪", layout="centered", initial_sidebar_state="expanded")

# --- Hide Branding ---
hide_st_style = """
            <style>
            .stAppDeployButton {display:none !important;}
            .stDeployButton {display:none !important;}
            #MainMenu {display: none !important;}
            [data-testid="stViewerBadge"] {display: none !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

## --- 1. Initialize Cookie Manager ---
# cookie_manager =stx.CookieManager(key="cookie_manager")

# --- 2. Define Session State Variables ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "daily_balances" not in st.session_state:
    st.session_state.daily_balances = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "force_logout" not in st.session_state:
    st.session_state.force_logout = False

# --- 3. Cookie Verification Logic ---
time.sleep(0.1)
saved_user = cookie_manager.get(cookie="saved_username")

if saved_user and not st.session_state.force_logout:
    st.session_state.logged_in = True
    st.session_state.username = saved_user
    if "premium" in saved_user.lower():
        st.session_state.is_premium = True
elif st.session_state.force_logout:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.is_premium = False
    
# --- 4. Main App Logic ---
if not st.session_state.logged_in:
    # --- PHASE 1: LOGIN SCREEN ---
    st.title("🧪 Chemical Equation Balancer")
    st.markdown("### Welcome! Please log in to continue.")
    st.info("Don't have an account? Just type a username to create one instantly!")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username_input = st.text_input("Username:", placeholder="Enter any username...", key="login_input")
        
        if st.button("🚀 Enter Balancer App", use_container_width=True):
            if username_input.strip() == "":
                st.error("Please enter a username!")
            else:
                st.session_state.username = username_input.strip()
                st.session_state.logged_in = True
                st.session_state.force_logout = False
                
                if "premium" in st.session_state.username.lower():
                    st.session_state.is_premium = True
                else:
                    st.session_state.is_premium = False
                
                cookie_manager.set("saved_username", st.session_state.username, max_age=30*24*60*60)
                st.success(f"Welcome, {st.session_state.username}!")
                time.sleep(1)
                st.rerun()

else:
    # --- PHASE 2: THE ACTUAL APP (Sidebar is guaranteed here) ---
    
    # 1. ALWAYS DRAW SIDEBAR FIRST
    st.sidebar.title("👤 Profile")
    st.sidebar.write(f"**User:** {st.session_state.username}")
    
    if st.session_state.is_premium:
        st.sidebar.success("👑 Premium Active")
        st.sidebar.write("Enjoy unlimited balancing!")
    else:
        st.sidebar.info("🆓 Free Tier")
        st.sidebar.write(f"Balances used: {st.session_state.daily_balances} / 5")
        st.sidebar.write("Upgrade for unlimited access.")
        
    st.sidebar.divider()
    
    # LOGOUT BUTTON
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.force_logout = True
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_premium = False
        
        cookie_manager.delete("saved_username")
        
        st.sidebar.warning("Logging out...")
        time.sleep(0.5)
        st.rerun()

    # 2. MAIN CONTENT
    st.title("🧪 Chemical Equation Balancer")
    
    tab1, tab2, tab3 = st.tabs(["🧮 Balancer", "📜 History", "ℹ️ Help & Premium"])
    
    with tab1:
        if not st.session_state.is_premium:
            st.write(f"Daily Usage: {st.session_state.daily_balances} / 5")
            
        user_input = st.text_input("Enter Equation (Reactants -> Products):")
        
        if st.button("Balance Equation"):
            if not st.session_state.is_premium and st.session_state.daily_balances >= 5:
                st.error("🛑 Daily Limit Reached! Upgrade in the 'Help & Premium' tab.")
            else:
                try:
                    reac_side, prod_side = user_input.split("->")
                    reactants = set(f.strip() for f in reac_side.split("+") if f.strip())
                    products = set(f.strip() for f in prod_side.split("+") if f.strip())
                    reac_c, prod_c = balance_stoichiometry(reactants, products)
                    res = " + ".join([f"{reac_c[r]} {r}" for r in reactants]) + " -> " + " + ".join([f"{prod_c[p]} {p}" for p in products])
                    
                    st.session_state.history.insert(0, res)
                    if not st.session_state.is_premium:
                        st.session_state.daily_balances += 1
                    st.success(f"Balanced: {res}")
                except Exception as e:
                    st.error(f"Error: Make sure you use correct syntax (e.g. H2 + O2 -> H2O). Details: {e}")
                    
    with tab2:
        st.subheader("History")
        if not st.session_state.history:
            st.write("No equations balanced yet.")
        for h in st.session_state.history:
            st.write(h)
            
    with tab3:
        st.subheader("How to Use")
        st.write("Use standard chemical formulas (e.g., KMnO4 + HCl -> KCl + MnCl2 + H2O + Cl2).")
        
        st.subheader("👑 Get Premium")
        st.write("Want unlimited balances? Redeem a gift card code below!")
        
        redeem_code = st.text_input("Enter Gift Card Code:")
        
        if st.button("Redeem Code"):
            if redeem_code:
                try:
                    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
                    sh = gc.open("App Gift cards")
                    worksheet = sh.sheet1
                    
                    cell = worksheet.find(redeem_code.strip())
                    
                    if cell is None:
                        st.error("❌ Invalid Code! Please try again.")
                    else:
                        status = worksheet.cell(cell.row, 2).value
                        if status and status.lower() == 'used':
                            st.error("❌ This code has already been redeemed!")
                        else:
                            worksheet.update_cell(cell.row, 2, 'used')
                            worksheet.update_cell(cell.row, 3, st.session_state.username)
                            
                            st.session_state.is_premium = True
                            new_username = st.session_state.username + "_premium"
                            st.session_state.username = new_username
                            cookie_manager.set("saved_username", new_username, max_age=30*24*60*60)
                            
                            st.success("🎉 Success! You are now a Premium user!")
                            time.sleep(2)
                            st.rerun()
                except Exception as e:
                    st.error("Error connecting to database. Please check your secrets.")
            else:
                st.warning("Please enter a code.")

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.8rem;'>CREATED BY 🤍 PRANEEL BANERJEE</p>", unsafe_allow_html=True)