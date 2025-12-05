"""
Main entry point for the application.
"""
import sys
import os

# Ensure the src directory is in the python path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import __name__ as package_name

def main():
    """
    Main function to run the application.
    """
    print(f"Hello from {package_name}!")

if __name__ == "__main__":
    main()

