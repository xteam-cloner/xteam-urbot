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
    
    print(f"Checking the configuration for the Client ID {client_id}...")
    
    for var in REQUIRED_VARS:
        full_var_name = var + suffix
        value = os.environ.get(full_var_name)
        
        if not value:
            if suffix == "" and os.environ.get(var + "1"):
                 found_all = False
                 return False 
            
            found_all = False
            return False 
            
        env_vars_to_pass[var] = value

    if found_all:
        print(f"✅ Variable found. Launching Client {client_id}...")
        
        process_env = os.environ.copy()
        
        for base_var in BASE_VARS:
            base_value = os.environ.get(base_var)
            if base_value:
                process_env[base_var] = base_value 

        process_env.update(env_vars_to_pass)
        
        process_env['CLIENT_ID'] = client_id 
        
        if client_id == "1":
            process_env['SESSION_NAME'] = "Client" 
        elif client_id == "2":
            process_env['SESSION_NAME'] = "userbot" 
        else:
            process_env['SESSION_NAME'] = f"ultroid_client_{client_id}"
        
        current_pythonpath = process_env.get('PYTHONPATH', '')
        process_env['PYTHONPATH'] = f"{current_pythonpath}:{BASE_DIR}"
        
        client_cwd = BASE_DIR
        
        subprocess.Popen(
            [sys.executable, "-m", "xteam"],
            stdin=None,
            stderr=None,
            stdout=None,
            cwd=client_cwd, 
            env=process_env,
            close_fds=True,
        )
        return True
    return False

primary_client_launched = _check_and_launch("")

for i in range(2, 6): 
    _check_and_launch(str(i))

try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    print("Launcher stopped manually.")
except Exception as er:
    print(f"Error in main loop: {er}")
    
