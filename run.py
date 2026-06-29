#!/usr/bin/env python3
"""
run.py

Top-level entry point. Run with: python run.py
"""

from app.main import app

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
