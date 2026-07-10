import streamlit as st
import extra_streamlit_components as stx
from chempy import balance_stoichiometry
import time
import gspread
import re

# --- PAGE CONFIG ---
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

# --- 1. Initialize Cookie Manager ---
cookie_manager = stx.CookieManager(key="cookie_manager")

# --- 2. Define Session State Variables ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_premium" not in st.session_state:
    st.session_state.is_premium = False
if "balance_count" not in st.session_state:
    st.session_state.balance_count = 0
if 'force_logout' not in st.session_state:
    st.session_state.force_logout = False

# --- 3. Handle Auto-Login ---
time.sleep(0.1) 
saved_user = cookie_manager.get(cookie="saved_username")

if saved_user and not st.session_state.force_logout:
    st.session_state.logged_in = True
    st.session_state.username = saved_user
    st.session_state.is_premium = True
    st.session_state.balance_count = 999 

# --- 4. Database Setup ---
def init_db():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open("App Gift cards")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Database connection failed: {e}")
        return None

# --- 5. Custom CSS ---
st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 10px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .main-header {
            text-align: center;
            color: #2E86C1;
            font-size: 40px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .free-banner {
            background-color: #FFEB3B;
            color: #000;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
#                               SIDEBAR LOGIC
# ==============================================================================
with st.sidebar:
    st.title("🔑 Account Area")

    if not st.session_state.logged_in:
        # --- LOGIN FORM ---
        st.write("Enter a premium code to unlock unlimited balancing!")
        
        with st.form("login_form"):
            code_input = st.text_input("Enter Premium Code", type="password")
            submit_btn = st.form_submit_button("Login")

            if submit_btn:
                if code_input:
                    worksheet = init_db()
                    if worksheet:
                        with st.spinner("Verifying code..."):
                            search_code = code_input.strip()
                            # Compile regex to match the code exactly, ignoring case and surrounding whitespace
                            pattern = re.compile(r'^\s*' + re.escape(search_code) + r'\s*$', re.IGNORECASE)
                            
                            try:
                                # Find all cells matching the regex
                                found_cells = worksheet.findall(pattern)
                                
                                # Filter to ensure it's in column A (column 1)
                                valid_cells = [c for c in found_cells if c.col == 1]
                                
                                cell = valid_cells[0] if valid_cells else None
                            except Exception as e:
                                st.error(f"Error searching database: {e}")
                                cell = None
                                
                            if cell:
                                # Check status in Column B
                                status = worksheet.cell(cell.row, 2).value
                                
                                if status and status.lower() == "unused":
                                    # Mark as used in Column B
                                    worksheet.update_cell(cell.row, 2, 'used')
                                    # Generate a username based on the code (e.g., first 5 chars)
                                    generated_username = f"User_{search_code[:5]}"
                                    # Save username in Column C
                                    worksheet.update_cell(cell.row, 3, generated_username)
                                    
                                    # Set Session State
                                    st.session_state.logged_in = True
                                    st.session_state.username = generated_username
                                    st.session_state.is_premium = True
                                    st.session_state.balance_count = 999
                                    st.session_state.force_logout = False
                                    
                                    # Set Cookie
                                    cookie_manager.set("saved_username", generated_username, expires_at=None) 
                                    
                                    st.success("🎉 Premium Activated!")
                                    time.sleep(1)
                                    st.rerun()
                                elif status and status.lower() == "used":
                                    st.error("❌ This code has already been used.")
                                else:
                                    st.error("❌ Invalid code status in database.")
                            else:
                                st.error("❌ Invalid code. Please try again.")
                else:
                    st.warning("Please enter a code.")

    else:
        # --- LOGGED IN VIEW ---
        st.success(f"Welcome back, {st.session_state.username}!")
        st.write("✨ Premium Account Active ✨")
        st.write("Unlimited balancings unlocked.")
        
        if st.button("Logout"):
            cookie_manager.delete("saved_username")
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_premium = False
            st.session_state.balance_count = 0
            st.session_state.force_logout = True
            time.sleep(1)
            st.rerun()


# ==============================================================================
#                               MAIN PAGE LOGIC
# ==============================================================================

st.markdown('<p class="main-header">🧪 Chemical Equation Balancer</p>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.markdown('<div class="free-banner">🆓 Free Tier Active: You have 3 free balancings left.</div>', unsafe_allow_html=True)

# Main input for the equation
st.write("Enter an unbalanced chemical equation below (e.g., H2 + O2 -> H2O).")
equation_input = st.text_input("Equation:", placeholder="e.g., C6H12O6 + O2 -> CO2 + H2O")

if st.button("Balance Equation"):
    if not equation_input:
        st.warning("Please enter an equation to balance.")
    else:
        if not st.session_state.is_premium and st.session_state.balance_count >= 3:
            st.error("🔒 You have reached your free limit. Please enter a premium code in the sidebar to continue.")
        else:
            try:
                # Basic parsing to split reactants and products
                if "->" in equation_input:
                    reactants_str, products_str = equation_input.split("->")
                elif "=" in equation_input:
                    reactants_str, products_str = equation_input.split("=")
                else:
                    raise ValueError("Equation must contain '->' or '='")

                # Clean up the strings
                reactants_list = [r.strip() for r in reactants_str.split("+")]
                products_list = [p.strip() for p in products_str.split("+")]

                # Convert lists to dictionaries mapping molecules to initial counts
                reactants_set = set(reactants_list)
                products_set = set(products_list)

                # Balance the stoichiometry
                reac, prod = balance_stoichiometry(reactants_set, products_set)
                
                # Format the output beautifully
                balanced_reactants = " + ".join([f"{v}{k}" if v > 1 else k for k, v in reac.items()])
                balanced_products = " + ".join([f"{v}{k}" if v > 1 else k for k, v in prod.items()])
                
                balanced_equation = f"**{balanced_reactants} &rarr; {balanced_products}**"
                
                st.success("✅ Equation successfully balanced!")
                st.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>{balanced_equation}</h3>", unsafe_allow_html=True)
                
                if not st.session_state.is_premium:
                    st.session_state.balance_count += 1
                    remaining = 3 - st.session_state.balance_count
                    if remaining > 0:
                         st.info(f"You have {remaining} free uses remaining.")
                    else:
                         st.warning("You have used all your free uses. Unlock Premium for more!")

            except Exception as e:
                st.error("❌ Error balancing equation. Please check your syntax. Make sure molecules are spelled correctly and you use '->' or '='.")
                st.write(f"Details: {e}")