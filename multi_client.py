import os
import subprocess
import sys
import time
from dotenv import load_dotenv

# Hubungkan ke Database Internal Ultroid
try:
    from xteam.db import UltroidDB
    udB = UltroidDB()
except ImportError:
    udB = None

load_dotenv() 

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
REQUIRED_VARS = ["API_ID", "API_HASH", "SESSION"]

def _launch(suffix):
    env_vars = {}
    client_id = suffix if suffix else "1" 
    
    for var in REQUIRED_VARS:
        full_var_name = var + suffix
        # Ambil dari .env atau Database Ultroid
        value = os.environ.get(full_var_name) or (udB.get_key(full_var_name) if udB else None)
        
        # Fallback API_ID & HASH ke akun utama jika slot tambahan kosong
        if not value and var in ["API_ID", "API_HASH"]:
            value = os.environ.get(var) or (udB.get_key(var) if udB else None)

        if not value:
            return False 
        env_vars[var] = value

    print(f"🚀 Memulai Client {client_id}...")
    process_env = os.environ.copy()
    process_env.update(env_vars)
    process_env['CLIENT_ID'] = client_id 
    process_env['PYTHONPATH'] = f"{process_env.get('PYTHONPATH', '')}:{BASE_DIR}"
    
    subprocess.Popen(
        [sys.executable, "-m", "xteam"],
        cwd=BASE_DIR, env=process_env, close_fds=True,
    )
    return True

# Jalankan Client 1 sampai 5
for i in [""] + [str(x) for x in range(2, 6)]:
    _launch(i)

try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    print("Launcher Stopped.")
    
