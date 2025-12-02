#!/usr/bin/env python3
"""
Simplified Multi-Client Ultroid Launcher v2
Uses working directories but with minimal setup
"""
import os
import subprocess
import sys
import shutil

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

REQUIRED_VARS = ["API_ID", "API_HASH", "SESSION", "MONGO_URI"]

def has_client_config(client_num):
    """Check if client has all required config"""
    suffix = "" if client_num == 1 else str(client_num - 1)
    for var in REQUIRED_VARS:
        if not os.environ.get(var + suffix):
            return False
    return True

def setup_client_dir(client_num, base_dir):
    """Minimal setup for client directory"""
    client_dir = os.path.join(base_dir, f"client_{client_num}")
    os.makedirs(client_dir, exist_ok=True)
    
    # Only create symlinks for essential directories
    for dir_name in ["plugins", "resources", "assistant", "strings", "addons"]:
        src = os.path.join(base_dir, dir_name)
        dst = os.path.join(client_dir, dir_name)
        
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                if sys.platform != "win32":
                    os.symlink(os.path.abspath(src), dst)
                else:
                    # Windows: copy instead of symlink
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
            except Exception:
                pass
    
    # Copy .env
    if os.path.exists(".env"):
        shutil.copy(".env", os.path.join(client_dir, ".env"))
    
    return client_dir

def start_client(client_num):
    """Start a client"""
    if not has_client_config(client_num):
        suffix = "" if client_num == 1 else str(client_num - 1)
        missing = [v for v in REQUIRED_VARS if not os.environ.get(v + suffix)]
        print(f"✗ Client {client_num}: Missing {', '.join(missing)}")
        return None
    
    print(f"✓ Client {client_num}: Starting...")
    
    base_dir = os.getcwd()
    client_dir = setup_client_dir(client_num, base_dir)
    
    # Build environment
    env = os.environ.copy()
    suffix = "" if client_num == 1 else str(client_num - 1)
    
    # Get values
    api_id = os.environ.get(f"API_ID{suffix}") or os.environ.get("API_ID")
    api_hash = os.environ.get(f"API_HASH{suffix}") or os.environ.get("API_HASH")
    session = os.environ.get(f"SESSION{suffix}") or os.environ.get("SESSION")
    mongo_uri = os.environ.get(f"MONGO_URI{suffix}") or os.environ.get("MONGO_URI")
    
    # Unique database
    db_name = f"UltroidDB{client_num}"
    if mongo_uri.endswith('/'):
        env["MONGO_URI"] = f"{mongo_uri}{db_name}"
    else:
        env["MONGO_URI"] = f"{mongo_uri}/{db_name}"
    
    # Optional vars
    if os.environ.get(f"LOG_CHANNEL{suffix}"):
        env["LOG_CHANNEL"] = os.environ.get(f"LOG_CHANNEL{suffix}")
    elif os.environ.get("LOG_CHANNEL"):
        env["LOG_CHANNEL"] = os.environ.get("LOG_CHANNEL")
    
    if os.environ.get(f"BOT_TOKEN{suffix}"):
        env["BOT_TOKEN"] = os.environ.get(f"BOT_TOKEN{suffix}")
    elif os.environ.get("BOT_TOKEN"):
        env["BOT_TOKEN"] = os.environ.get("BOT_TOKEN")
    
    env["PYTHONPATH"] = base_dir
    
    # Note: The .restart command will work correctly because:
    # - Working directory (client_dir) is preserved by os.execl()
    # - Environment variables (PYTHONPATH, MONGO_URI, etc.) are preserved
    # - sys.argv arguments (API_ID, API_HASH, SESSION) are preserved
    # The restart function in pyUltroid/fns/helper.py handles this automatically
    
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "xteam", api_id, api_hash, session, "", ""],
            cwd=client_dir,
            env=env,
        )
        print(f"  → Started (PID: {proc.pid})")
        return proc
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Multi-Client Ultroid Launcher v2 (Simplified)")
    print("=" * 60)
    print()
    
    processes = []
    for i in range(1, 6):
        proc = start_client(i)
        if proc:
            processes.append((i, proc))
        print()
    
    if not processes:
        print("✗ No clients started. Check your .env file.")
        sys.exit(1)
    
    print("=" * 60)
    print(f"✓ {len(processes)} client(s) running")
    for num, proc in processes:
        print(f"  Client {num}: PID {proc.pid}")
    print("=" * 60)
    print("\nPress Ctrl+C to exit (clients keep running)")
    
    try:
        import time
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nExiting. Clients still running.")
        print("Stop with: pkill -f xteam")

if __name__ == "__main__":
    main()
