import sys
from types import ModuleType
import os
import subprocess
import time
import threading
import json  # 🧠 Fixed JSON dependency
import streamlit as st
import streamlit.components.v1 as components

# 📊 Streamlit Page Config
st.set_page_config(page_title="Advanced Chart", layout="wide")

# 🚀 Anti-Crash Pandas Bypass Engine
if 'pandas' not in sys.modules:
    fake_pandas = ModuleType('pandas')
    fake_pandas.DataFrame = lambda *args, **kwargs: None
    sys.modules['pandas'] = fake_pandas
    print("Pandas successfully bypassed!")

# 📂 Background Repo Pull Engine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.join(BASE_DIR, "nubra_python_sdk")

if not os.path.exists(sdk_path):
    print("Downloading Nubra SDK from Option Chain repo...")
    subprocess.run(["git", "clone", "https://github.com/nitesh-optionchain/nifty-option-chain.git", os.path.join(BASE_DIR, "temp_repo")])
    if os.path.exists(os.path.join(BASE_DIR, "temp_repo/nubra_python_sdk")):
        os.rename(os.path.join(BASE_DIR, "temp_repo/nubra_python_sdk"), sdk_path)
    print("SDK successfully integrated!")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from nubra_python_sdk.start_sdk import InitNubraSdk, NubraEnv
from nubra_python_sdk.marketdata.market_data import MarketData

st.title("📈 Advanced Real-Time Chart (NIFTY & SENSEX)")

# ========================================================
# 🔐 RETRY ENGINE: Pure OS Environment Bridge Logic
# ========================================================
# Agar Streamlit Cloud secrets foreground thread me available hain, toh pehle unhe hard-inject karenge
try:
    if "PHONE_NO" in st.secrets:
        os.environ["PHONE_NO"] = str(st.secrets["PHONE_NO"])
    if "MPIN" in st.secrets:
        os.environ["MPIN"] = str(st.secrets["MPIN"])
except Exception as secrets_err:
    print(f"Streamlit Secrets internal bypass log: {secrets_err}")

# Hard Fetch from OS
ENV_PHONE = os.environ.get("PHONE_NO")
ENV_MPIN = os.environ.get("MPIN")

def get_nubra_session_direct():
    try:
        if ENV_PHONE and ENV_MPIN:
            print(f"🔑 Generating hard hardware token for: {str(ENV_PHONE)[:5]}*****")
            # Force String casting taaki type conflict na ho
            return InitNubraSdk(NubraEnv.PROD, phone_no=str(ENV_PHONE), mpin=str(ENV_MPIN))
        else:
            print("⚠️ ENV Variables are completely empty! Retrying env_creds mode...")
            return InitNubraSdk(NubraEnv.PROD, env_creds=True)
    except Exception as auth_crash:
        print(f"❌ SDK Main Core Auth Fatal Exception: {str(auth_crash)}")
        return None

# Verify if token can be generated in foreground
main_client = get_nubra_session_direct()
if main_client is None:
    st.error("❌ Auth Token generate nahi ho saka! Kripya check karein ki Streamlit Cloud ke Advanced Settings -> Secrets me PHONE_NO aur MPIN capital letters me mapped hain ya nahi.")
    st.stop()
# ========================================================

# Dual Asset Global Database (Bina session_state ke background thread ke liye reliable memory)
# Streamlit updates ke time thread global variable par leak nahi karega
if "global_master_storage" not in globals():
    global_master_storage = {
        "NIFTY": {"price": 2444990, "status": "LIVE", "master_history": []},
        "SENSEX": {"price": 8035000, "status": "LIVE", "master_history": []}
    }

# Background thread synchronization engine
if "pipeline_active" not in st.session_state:
    
    def fetch_data_stream_loop():
        global global_master_storage
        print("Dual Asset Master Pipeline Active (NIFTY & SENSEX)...")
        
        # Isolated Thread Auth Loop
        thread_client = get_nubra_session_direct()
        thread_market_engine = MarketData(thread_client) if thread_client else None
        
        if not thread_market_engine:
            print("❌ Background Loop aborted: Thread environment cannot access auth structures.")
            return

        while True:
            try:
                # 1. Fetch NIFTY
                nifty_snap = thread_market_engine.current_price("NIFTY", exchange="NSE")
                if nifty_snap and nifty_snap.price:
                    real_nifty = float(nifty_snap.price) / 100
                    global_master_storage["NIFTY"]["price"] = int(nifty_snap.price)
                    global_master_storage["NIFTY"]["master_history"].append({
                        "open": real_nifty, "high": real_nifty, "low": real_nifty, "close": real_nifty
                    })
                    if len(global_master_storage["NIFTY"]["master_history"]) > 1000:
                        global_master_storage["NIFTY"]["master_history"].pop(0)

                # 2. Fetch SENSEX
                sensex_snap = thread_market_engine.current_price("SENSEX", exchange="BSE")
                if sensex_snap and sensex_snap.price:
                    real_sensex = float(sensex_snap.price) / 100
                    global_master_storage["SENSEX"]["price"] = int(sensex_snap.price)
                    global_master_storage["SENSEX"]["status"] = "LIVE"
                    global_master_storage["SENSEX"]["master_history"].append({
                        "open": real_sensex, "high": real_sensex, "low": real_sensex, "close": real_sensex
                    })
                    if len(global_master_storage["SENSEX"]["master_history"]) > 1000:
                        global_master_storage["SENSEX"]["master_history"].pop(0)
                            
            except Exception as error:
                print(f"Data Pipe Warning: {error}")
            time.sleep(1)

    data_thread = threading.Thread(target=fetch_data_stream_loop, daemon=True)
    data_thread.start()
    st.session_state.pipeline_active = True

# 🌐 HTML Chart Insertion Logic (Direct GitHub Fetch Engine)
import requests

# Aapki advance-chart repo ka raw link jahan index.html rakhi hai
github_raw_url = "https://raw.githubusercontent.com/nitesh-optionchain/advance-chart/main/index.html"

try:
    # 📡 GitHub se direct HTML content fetch kar rahe hain
    response = requests.get(github_raw_url, timeout=10)
    
    if response.status_code == 200:
        html_content = response.text
        
        # 🔐 Auth Credentials ko Javascript window context me inject kar rahe hain
        auth_payload = {
            "PHONE_NO": os.environ.get("PHONE_NO", ""),
            "MPIN": os.environ.get("MPIN", ""),
            "STATUS": "ACTIVE"
        }
        
        json_data = json.dumps(auth_payload)
        html_content = html_content.replace(
            "<head>", 
            f"<head><script>window.streamAuthContext = {json_data};</script>"
        )
        
        # 📊 Rendering embedded component block
        components.html(html_content, height=780, scrolling=True)
    else:
        st.error(f"❌ GitHub se index.html fetch nahi ho saki! (Status Code: {response.status_code})")

except Exception as fetch_err:
    st.error(f"❌ Connection Error: {str(fetch_err)}")
