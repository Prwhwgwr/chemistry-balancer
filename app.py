import streamlit as st
import extra_streamlit_components as stx
from chempy import balance_stoichiometry
import time
import gspread

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
# CRITICAL FIX: Defined perfectly flush left, no caching to avoid warnings!
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
# Give the cookie manager a tiny bit of time to fetch cookies
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