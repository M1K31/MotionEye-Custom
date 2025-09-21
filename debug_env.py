# debug_env.py
import sys
import os

print("Python executable:", sys.executable)
print("Virtual environment:", os.environ.get('VIRTUAL_ENV', 'Not set'))
print("Current working directory:", os.getcwd())