#!/bin/bash

# Fix for pre-commit Python executable issue
# This creates a symlink so that 'python' points to 'python3'

# Check if python command exists
if ! command -v python &> /dev/null; then
    echo "Creating python symlink to python3..."
    
    # Create a local bin directory if it doesn't exist
    mkdir -p ~/.local/bin
    
    # Create symlink
    ln -sf /usr/bin/python3 ~/.local/bin/python
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    echo "Python symlink created. You may need to restart your terminal or run: source ~/.bashrc"
else
    echo "Python command already exists"
fi

# Check if it works
echo "Testing python command:"
python --version
