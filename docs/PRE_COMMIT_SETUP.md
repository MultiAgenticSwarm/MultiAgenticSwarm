# Pre-commit Setup Fix

This document explains how to fix the pre-commit Python environment issue.

## Problem

The original error occurred because pre-commit was looking for a `python` executable, but only `python3` was available on the system:

```
Executable `python` not found
```

## Solution

The issue was fixed by:

1. **Creating a Python symlink** (if needed):
   ```bash
   ln -sf /usr/bin/python3 ~/.local/bin/python
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Simplifying the pre-commit configuration** to use local hooks instead of remote repositories that create their own virtual environments:
   ```yaml
   repos:
     - repo: local
       hooks:
         - id: black
           name: black
           entry: black
           language: system
           types: [python]
           args: [--line-length=88]
         - id: isort
           name: isort
           entry: isort
           language: system
           types: [python]
           args: [--profile=black]
   ```

## Benefits

- Uses the local Python environment instead of creating virtual environments
- Avoids Python version mismatch issues
- Faster execution since no virtual environment creation is needed
- More reliable on systems where `python` is not available but `python3` is

## Usage

After the fix, pre-commit works normally:

```bash
git add .
git commit -m "your commit message"
```

The hooks will automatically format your Python code with black and isort before committing.
