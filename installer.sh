#!/usr/bin/env bash

# Default variables
REPO="https://github.com/xteam-cloner/xteam-urbot.git"
CURRENT_DIR="$(pwd)"
ENV_FILE_PATH=".env"
DIR="/root/xteam-cloner" # Default installation directory

# Parse command-line arguments
while [ $# -gt 0 ]; do
    case "$1" in
    --dir=*)
        DIR="${1#*=}"
        ;;
    --branch=*)
        BRANCH="${1#*=}"
        ;;
    --env-file=*)
        ENV_FILE_PATH="${1#*=}"
        ;;
    --no-root)
        NO_ROOT=true
        ;;
    *)
        echo "Error: Unknown parameter passed: $1" >&2
        exit 1
        ;;
    esac
    shift
done

# Function to check and install dependencies
check_dependencies() {
    echo "Checking dependencies..."

    # Check for Python 3.8 or higher
    if ! command -v python3 &>/dev/null; then
        echo -e "Error: Python3 isn't installed. Please install python3.8 or higher to run this bot." >&2
        exit 1
    fi

    local python_major=$(python3 -c "import sys; print(sys.version_info[0])")
    local python_minor=$(python3 -c "import sys; print(sys.version_info[1])")

    if [[ "$python_major" -lt 3 ]] || ([[ "$python_major" -eq 3 ]] && [[ "$python_minor" -lt 8 ]]); then
        echo -e "Error: Python 3.8 or higher is required to run this bot. Found Python $python_major.$python_minor." >&2
        exit 1
    fi

    # Check for other dependencies and install if missing
    if command -v apt-get &>/dev/null; then # Debian/Ubuntu based systems
        echo -e "Checking for Debian/Ubuntu dependencies..."
        # Check if any of ffmpeg, mediainfo, neofetch, git is NOT installed
        if ! dpkg -s ffmpeg mediainfo neofetch git &>/dev/null; then
            echo -e "Installing missing dependencies (python3, python3-pip, ffmpeg, mediainfo, neofetch, git)..."
            sudo apt-get -qq update || echo "Warning: apt-get update failed, continuing anyway."
            sudo apt-get install -qq python3 python3-pip ffmpeg mediainfo neofetch git -y || { echo "Error: Failed to install apt dependencies." >&2; exit 1; }
        fi
    elif command -v pacman &>/dev/null; then # Arch Linux based systems
        echo -e "Checking for Arch Linux dependencies..."
        # Check if any of ffmpeg, mediainfo, neofetch, git is NOT installed
        if ! pacman -Q ffmpeg mediainfo neofetch git &>/dev/null; then
            echo -e "Installing missing dependencies (python, python-pip, git, ffmpeg, mediainfo, neofetch)..."
            sudo pacman -Sy python python-pip git ffmpeg mediainfo neofetch --noconfirm || { echo "Error: Failed to install pacman dependencies." >&2; exit 1; }
        fi
    else
        echo -e "Unknown OS/package manager. Checking if dependencies are manually installed." >&2
        if ! command -v ffmpeg &>/dev/null || ! command -v mediainfo &>/dev/null || ! command -v neofetch &>/dev/null || ! command -v git &>/dev/null; then
            echo -e "Error: Some dependencies (ffmpeg, mediainfo, neofetch, git) aren't installed. Please install them manually." >&2
            exit 1
        fi
    fi
}

# Function to clone or update the repository
clone_repo() {
    # Ensure DIR exists and is a valid directory
    mkdir -p "$DIR" || { echo "Error: Could not create directory $DIR." >&2; exit 1; }

    if [ -d "$DIR/.git" ]; then
        echo -e "Updating Ultroid ${BRANCH:-main}... "
        ( # Use a subshell to avoid changing the current directory for the rest of the script
            cd "$DIR" || { echo "Error: Could not change to directory $DIR." >&2; exit 1; }
            git pull || { echo "Error: Git pull failed." >&2; exit 1; }
            local currentbranch="$(git rev-parse --abbrev-ref HEAD)"
            local effective_branch="${BRANCH:-main}" # Use provided branch or default to main

            if [[ "$currentbranch" != "$effective_branch" ]]; then
                echo -e "Switching to branch ${effective_branch}... "
                git checkout "$effective_branch" || { echo "Error: Git checkout failed." >&2; exit 1; }
            fi
        )
    else
        # If DIR exists but isn't a git repo, or if it doesn't exist, clone it.
        # Check if directory is not empty to warn user about potential data loss
        if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR")" ]; then
            echo "Warning: $DIR exists and is not an xteam-urbot git repository. Contents will be removed before cloning."
            # Consider adding a user prompt for confirmation here if data loss is a concern.
            rm -rf "$DIR" || { echo "Error: Failed to remove directory $DIR." >&2; exit 1; }
            mkdir -p "$DIR" || { echo "Error: Could not re-create directory $DIR." >&2; exit 1; }
        fi

        local effective_branch="${BRANCH:-main}"
        echo -e "Cloning Ultroid ${effective_branch}... "
        git clone -b "$effective_branch" "$REPO" "$DIR" || { echo "Error: Git clone failed." >&2; exit 1; }
    fi

    # Handle addons subdirectory if it exists within the cloned repo
    if [ -d "$DIR/addons" ]; then
        (
            cd "$DIR/addons" || { echo "Error: Could not change to addons directory." >&2; exit 1; }
            echo "Updating addons..."
            git pull || echo "Warning: Git pull for addons failed." # Not critical to exit here
        )
    fi
}

# Function to install Python requirements
install_requirements() {
    echo -e "\n\nInstalling Python requirements... "
    # Upgrade pip first
    pip3 install -q --upgrade pip || { echo "Error: Failed to upgrade pip." >&2; exit 1; }
    # Install main requirements
    pip3 install -q --no-cache-dir -r "$DIR/requirements.txt" || { echo "Error: Failed to install main requirements." >&2; exit 1; }
    # Install optional requirements
    pip3 install -q -r "$DIR/resources/startup/optional-requirements.txt" || { echo "Error: Failed to install optional requirements." >&2; exit 1; }
}

# Function for Railway-specific dependency
railways_dep() {
    if [ -n "$RAILWAY_STATIC_URL" ]; then # Check if variable is set and not empty
        echo -e "Installing YouTube dependency for Railway..."
        pip3 install -q yt-dlp || echo "Warning: Failed to install yt-dlp."
    fi
}

# Function for miscellaneous installations
misc_install() {
    if [ -n "$SETUP_PLAYWRIGHT" ]; then
        echo -e "Installing playwright..."
        pip3 install playwright || echo "Warning: Failed to install playwright."
        playwright install || echo "Warning: Failed to install playwright browsers."
    fi
    if [ -n "$OKTETO_TOKEN" ]; then
        echo -e "Installing Okteto-CLI..."
        curl https://get.okteto.com -sSfL | sh || echo "Warning: Failed to install Okteto-CLI."
    elif [ -n "$VCBOT" ]; then
        echo -e "Setting up VCBOT..."
        if [ -d "$DIR/vcbot" ]; then
            (
                cd "$DIR/vcbot" || { echo "Error: Could not change to vcbot directory." >&2; exit 1; }
                git pull || echo "Warning: Git pull for VcBot failed."
            )
        else
            echo -e "Cloning VCBOT..."
            git clone https://github.com/TeamUltroid/VcBot "$DIR/vcbot" || echo "Warning: Failed to clone VcBot."
        fi
        pip3 install pytgcalls==3.0.0.dev23 || echo "Warning: Failed to install pytgcalls."
        pip3 install av -q --no-binary av || echo "Warning: Failed to install av."
    fi
}

# Function for database dependencies
dep_install() {
    echo -e "\n\nInstalling DB Requirements..."
    if [ -n "$MONGO_URI" ]; then
        echo -e "   Installing MongoDB Requirements..."
        pip3 install -q pymongo[srv] || echo "Warning: Failed to install MongoDB requirements."
    elif [ -n "$DATABASE_URL" ]; then
        echo -e "   Installing PostgreSQL Requirements..."
        pip3 install -q psycopg2-binary || echo "Warning: Failed to install PostgreSQL requirements."
    elif [ -n "$REDIS_URI" ]; then
        echo -e "   Installing Redis Requirements..."
        pip3 install -q redis hiredis || echo "Warning: Failed to install Redis requirements."
    fi
}

# Main setup function
main() {
    echo -e "Starting Ultroid Setup..."

    # Source environment variables if ENV_FILE_PATH exists
    if [ -f "$ENV_FILE_PATH" ]; then
        echo "Sourcing environment variables from $ENV_FILE_PATH..."
        set -a # Automatically export all variables subsequently defined
        # This sed command is complex but handles quoted values.
        # If your .env is simple KEY=VALUE, `source "$ENV_FILE_PATH"` is enough.
        source <(cat "$ENV_FILE_PATH" | sed -e '/^#/d;/^\s*$/d' -e "s/'/'\\\''/g" -e "s/=\(.*\)/='\1'/g") || { echo "Error: Failed to source environment file." >&2; exit 1; }
        set +a # Stop automatically exporting variables
        # Copy .env to the installation directory if the bot expects it there
        cp "$ENV_FILE_PATH" "$DIR/.env" || echo "Warning: Failed to copy .env file to $DIR."
    fi

    check_dependencies # Check and install OS-level dependencies
    clone_repo         # Clone or update the bot's repository
    install_requirements # Install Python dependencies from requirements files
    railways_dep       # Install Railway-specific dependencies (if applicable)
    dep_install        # Install database dependencies (if applicable)
    misc_install       # Install other miscellaneous dependencies (playwright, vcbot, etc.)

    echo -e "\n\nSetup Completed."
}

# Determine execution context (root/sudo vs. non-root)
if [ -n "$NO_ROOT" ]; then # If --no-root flag is provided
    echo -e "Running with non-root privileges..."
    main
    exit 0
else
    # Check OS type
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     machine="Linux";;
        Darwin*)    machine="Mac";;
        CYGWIN*)    machine="Cygwin";;
        MINGW*)     machine="MinGw";;
        *)          machine="UNKNOWN:${unameOut}";;
    esac

    if [[ "$machine" != "Linux" ]]; then
        echo -e "Warning: This script is primarily designed for Linux. Running on $machine might lead to unexpected behavior." >&2
        # Decide if you want to exit here or proceed with a warning
        # exit 1
    fi

    # Check if sudo is installed and prompt for password
    if ! command -v sudo &>/dev/null; then
        echo -e "Error: Sudo isn't installed. Please install sudo to run this bot with elevated privileges." >&2
        exit 1
    fi
    # Request sudo access upfront
    sudo echo "Sudo permission granted. Proceeding with setup." || { echo "Error: Sudo permission denied. Exiting." >&2; exit 1; }
    main
fi
