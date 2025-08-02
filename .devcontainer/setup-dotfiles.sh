#!/bin/bash
set -e

# Setup dotfiles for the devcontainer user
# Checks for USER_DOTFILES_URL environment variable and clones/updates dotfiles repository

DOTFILES_DIR="$HOME/.dotfiles"

if [ -z "$USER_DOTFILES_URL" ]; then
    echo "USER_DOTFILES_URL not set, skipping dotfiles setup"
    exit 0
fi

echo "Setting up dotfiles from: $USER_DOTFILES_URL"

# Clone or update dotfiles repository
if [ -d "$DOTFILES_DIR" ]; then
    echo "Dotfiles directory exists, updating..."
    cd "$DOTFILES_DIR"
    git pull || {
        echo "Failed to update dotfiles repository"
        exit 1
    }
else
    echo "Cloning dotfiles repository..."
    git clone "$USER_DOTFILES_URL" "$DOTFILES_DIR" || {
        echo "Failed to clone dotfiles repository"
        exit 1
    }
    cd "$DOTFILES_DIR"
fi

# Look for and run install script
INSTALL_SCRIPTS=("install.sh" "install" "bootstrap.sh" "bootstrap" "setup.sh" "setup")

for script in "${INSTALL_SCRIPTS[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "Running install script: $script"
        ./"$script" || {
            echo "Install script failed, but continuing..."
        }
        break
    elif [ -f "$script" ]; then
        echo "Running install script: $script (making executable)"
        chmod +x "$script"
        ./"$script" || {
            echo "Install script failed, but continuing..."
        }
        break
    fi
done

echo "Dotfiles setup complete"
