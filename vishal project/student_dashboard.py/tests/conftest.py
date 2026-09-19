"""
conftest.py
-----------
Ensures the student_dashboard/ directory (parent of tests/) is on sys.path
so that all test files can import the project modules without installing a package.
"""
import sys
import os

# Add parent directory (student_dashboard/) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
