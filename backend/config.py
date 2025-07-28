"""
Configuration for backend settings.
"""
import os

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads")))

os.makedirs(UPLOAD_DIR, exist_ok=True)
