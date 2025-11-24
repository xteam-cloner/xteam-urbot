import os
import subprocess
import sys
import time
from dotenv import load_dotenv

load_dotenv() 

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

REQUIRED_VARS = ["API_ID", "API_HASH", "SESSION"]
BASE_VARS = ["API_ID", "API_HASH"] 

def _check_and_launch(suffix):
    
    env_vars_to_pass = {}
    found_all = True
    client_id = suffix if suffix else "1" 
    
    print(f"Memeriksa konfigurasi untuk Klien ID {client_id}...")
    
    for var in REQUIRED_VARS:
        full_var_name = var + suffix
        value = os.environ.get(full_var_name)
        
        if not value:
            if suffix == "" and os.environ.get(var + "1"):
                 found_all = False
                 return False 
            
            found_all = False
            print(f"    ⚠️ Melewatkan Klien {client_id} karena '{full_var_name}' tidak ditemukan.")
            return False 
            
        env_vars_to_pass[var] = value

    if found_all:
        print(f"    ✅ Variabel ditemukan. Meluncurkan Klien {client_id}...")
        
        process_env = os.environ.copy()
        
        for base_var in BASE_VARS:
            base_value = os.environ.get(base_var)
            if base_value:
                process_env[base_var] = base_value 

        process_env.update(env_vars_to_pass)
        
        process_env['CLIENT_ID'] = client_id 
        
        # --- MODIFIKASI: Penetapan Nama Sesi Eksplisit (SESSION_NAME) ---
        if client_id == "1":
            process_env['SESSION_NAME'] = "asst" # asst.session
        elif client_id == "2":
            process_env['SESSION_NAME'] = "userbot" # userbot.session
        else:
            process_env['SESSION_NAME'] = f"ultroid_client_{client_id}"
        # ------------------------------------------------------------------

        # --- MODIFIKASI UNTUK PYTHONPATH (Tetap dipertahankan) ---
        current_pythonpath = process_env.get('PYTHONPATH', '')
        process_env['PYTHONPATH'] = f"{current_pythonpath}:{BASE_DIR}"
        # --------------------------------------------------------

        # CWD DITETAPKAN KE BASE_DIR UNTUK SEMUA KLIEN
        client_cwd = BASE_DIR
        
        # --- LOGIKA CWD UNIK DIHAPUS ---

        subprocess.Popen(
            [sys.executable, "-m", "pyUltroid"],
            stdin=None,
            stderr=None,
            stdout=None,
            # CWD selalu BASE_DIR
            cwd=client_cwd, 
            env=process_env,
            close_fds=True,
        )
        return True
    return False

# -------------------------------------------------------------

print("--- Starting Primary Client Check (ID 1) ---")
primary_client_launched = _check_and_launch("")

print("\n--- Starting Additional Client Check (ID 2 through 5) ---")
for i in range(2, 6): 
    _check_and_launch(str(i))

# -------------------------------------------------------------

try:
    print("\nLauncher remains active to keep PyUltroid client processes running.")
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    print("Launcher stopped manually.")
except Exception as er:
    print(f"Error in main loop: {er}")
    
