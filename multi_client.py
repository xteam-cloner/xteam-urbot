import os
import subprocess
import sys
import time
from dotenv import load_dotenv
from xteam.db import UltroidDB

# Inisialisasi Database (Tanpa try)
udB = UltroidDB()
load_dotenv() 

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
REQUIRED_VARS = ["API_ID", "API_HASH", "SESSION"]

def _launch(suffix):
    env_vars = {}
    client_id = suffix if suffix else "1" 
    
    for var in REQUIRED_VARS:
        full_var_name = var + suffix
        # Ambil dari Database (prioritas untuk Multi-Client), baru .env
        value = udB.get_key(full_var_name) or os.environ.get(full_var_name)
        
        # Fallback API_ID/HASH ke akun utama jika slot tambahan tidak punya
        if not value and var in ["API_ID", "API_HASH"]:
            value = udB.get_key(var) or os.environ.get(var)

        if not value:
            return False 
        
        env_vars[var] = str(value)

    print(f"🚀 Memulai Client {client_id}...")
    
    process_env = os.environ.copy()
    process_env.update(env_vars)
    # CLIENT_ID dikirim agar bot tahu ini session ke berapa
    process_env['CLIENT_ID'] = client_id 
    process_env['PYTHONPATH'] = f"{process_env.get('PYTHONPATH', '')}:{BASE_DIR}"
    
    subprocess.Popen(
        [sys.executable, "-m", "xteam"],
        cwd=BASE_DIR, 
        env=process_env, 
        close_fds=True,
    )
    return True

# Jalankan Client 1 (Utama) dan Client 2-5
active = 0
for i in [""] + [str(x) for x in range(2, 6)]:
    if _launch(i):
        active += 1
        time.sleep(2)

print(f"✅ Berhasil menjalankan {active} client.")

while True:
    time.sleep(3600)
    
