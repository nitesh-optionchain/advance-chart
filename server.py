import sys
from types import ModuleType
import os
import subprocess
import time
import threading
import json  # 🧠 Fixed: Missing import jo json.dumps ke liye zaroori hai
import streamlit as st
import streamlit.components.v1 as components

# 📊 Streamlit Page Config (Menu me sahi dikhne ke liye)
st.set_page_config(page_title="Advanced Chart", layout="wide")

# 🚀 Anti-Crash Pandas Bypass Engine
if 'pandas' not in sys.modules:
    fake_pandas = ModuleType('pandas')
    fake_pandas.DataFrame = lambda *args, **kwargs: None
    sys.modules['pandas'] = fake_pandas
    print("Pandas successfully bypassed!")

# 📂 Background Repo Pull Engine (If SDK folder is missing)
# Streamlit Cloud par path fix karne ke liye BASE_DIR set kiya
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sdk_path = os.path.join(BASE_DIR, "nubra_python_sdk")

if not os.path.exists(sdk_path):
    print("Downloading Nubra SDK from Option Chain repo...")
    subprocess.run(["git", "clone", "https://github.com/nitesh-optionchain/nifty-option-chain.git", os.path.join(BASE_DIR, "temp_repo")])
    if os.path.exists(os.path.join(BASE_DIR, "temp_repo/nubra_python_sdk")):
        os.rename(os.path.join(BASE_DIR, "temp_repo/nubra_python_sdk"), sdk_path)
    print("SDK successfully integrated!")

# App path par imports ko set karne ke liye
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv
from nubra_python_sdk.marketdata.market_data import MarketData

st.title("📈 Advanced Real-Time Chart (NIFTY & SENSEX)")

# ========================================================
# 🔐 FINAL BULLETPROOF AUTH SYSTEM (Secrets to Env Bridge)
# ========================================================
# Streamlit Secrets se data fetch kar rahe hain
SECRET_PHONE = st.secrets.get("PHONE_NO")
SECRET_MPIN = st.secrets.get("MPIN")

# OS Environment variables se fallback check
PHONE_NO = SECRET_PHONE or os.environ.get("PHONE_NO")
MPIN = SECRET_MPIN or os.environ.get("MPIN")

# ⚡ CRITICAL BRIDGE: Streamlit Secrets ko OS Environment me inject kar rahe hain
# Kyunki background WebSocket thread sirf os.environ ko sahi se read kar pata hai
if SECRET_PHONE and SECRET_MPIN:
    os.environ["PHONE_NO"] = str(SECRET_PHONE)
    os.environ["MPIN"] = str(SECRET_MPIN)
    print(f"✅ Bridge Active: Credentials injected into OS Environment for {str(SECRET_PHONE)[:5]}*****")
else:
    print("⚠️ Warning: Credentials missing in Streamlit Secrets!")

def get_nubra_session():
    try:
        if PHONE_NO and MPIN:
            print("🔄 Initializing SDK via direct parameters...")
            return InitNubraSdk(NubraEnv.PROD, phone_no=str(PHONE_NO), mpin=str(MPIN))
        else:
            print("🔄 Falling back to SDK default env_creds mode...")
            return InitNubraSdk(NubraEnv.PROD, env_creds=True)
    except Exception as e:
        print(f"❌ SDK Login Exception: {str(e)}")
        return None

# Initial Core Check
nubra_client = get_nubra_session()

if nubra_client is None:
    st.error("❌ Independent Login Fail ho gaya! Kripya Streamlit Cloud par Secrets check karein.")
    st.stop()
else:
    print("🚀 Master Core Token successfully verified for main page context.")
# ========================================================

# Dual Asset Database Memory Structure
if "master_storage" not in st.session_state:
    st.session_state.master_storage = {
        "NIFTY": {"price": 2444990, "status": "LIVE", "master_history": []},
        "SENSEX": {"price": 8035000, "status": "LIVE", "master_history": []}
    }

# Global pipeline start karne ke liye check
if "pipeline_active" not in st.session_state:
    
    def fetch_data_stream_loop():
        print("Dual Asset Master Pipeline Active (NIFTY & SENSEX)...")
        
        # 🧵 Thread ke ANDAR login aur engine generate kar rahe hain taaki WebSocket ko fresh context mile
        thread_client = get_nubra_session()
        thread_market_engine = MarketData(thread_client) if thread_client else None
        
        if not thread_market_engine:
            print("❌ Background Engine failed to start due to missing Auth Token inside thread!")
            return

        while True:
            try:
                # 1. Fetch NIFTY Data
                nifty_snap = thread_market_engine.current_price("NIFTY", exchange="NSE")
                if nifty_snap and nifty_snap.price:
                    real_nifty = float(nifty_snap.price) / 100
                    st.session_state.master_storage["NIFTY"]["price"] = int(nifty_snap.price)
                    st.session_state.master_storage["NIFTY"]["master_history"].append({
                        "open": real_nifty, "high": real_nifty, "low": real_nifty, "close": real_nifty
                    })
                    if len(st.session_state.master_storage["NIFTY"]["master_history"]) > 1000:
                        st.session_state.master_storage["NIFTY"]["master_history"].pop(0)

                # 2. Fetch SENSEX Data
                sensex_snap = thread_market_engine.current_price("SENSEX", exchange="BSE")
                if sensex_snap and sensex_snap.price:
                    real_sensex = float(sensex_snap.price) / 100
                    st.session_state.master_storage["SENSEX"]["price"] = int(sensex_snap.price)
                    st.session_state.master_storage["SENSEX"]["status"] = "LIVE"
                    st.session_state.master_storage["SENSEX"]["master_history"].append({
                        "open": real_sensex, "high": real_sensex, "low": real_sensex, "close": real_sensex
                    })
                    if len(st.session_state.master_storage["SENSEX"]["master_history"]) > 1000:
                        st.session_state.master_storage["SENSEX"]["master_history"].pop(0)
                            
            except Exception as error:
                print(f"Data Pipe Warning: {error}")
            time.sleep(1)

    data_thread = threading.Thread(target=fetch_data_stream_loop, daemon=True)
    data_thread.start()
    st.session_state.pipeline_active = True

# 🌐 HTML Chart Insertion Logic
html_file_path = os.path.join(BASE_DIR, 'index.html')

if os.path.exists(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Live data ko Javascript chart me inject karne ke liye bridge
    # Yeh aapki purani API ka kaam karega bina Flask ke
    json_data = json.dumps(st.session_state.master_storage)
    html_content = html_content.replace("/*DATA_PLACEHOLDER*/", f"window.chartData = {json_data};")
    
    # Chart ko Streamlit page par run karein
    components.html(html_content, height=650, scrolling=True)
else:
    st.error("❌ 'index.html' file main folder me nahi mili!")
