"""
Utility functions for file handling, validation, and error responses.
"""
import os
from fastapi import UploadFile, HTTPException
from typing import Optional
from backend.logger import get_logger

# I'm importing the logger so can use it throughout this file.
logger = get_logger()

# File validation

def validate_excel_file(excel_file: UploadFile) -> None:
    if not excel_file or not excel_file.filename:
        raise http_error(400, "No Excel/CSV file uploaded. Please select a file.")
    if not excel_file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise http_error(400, "Excel file must be .xlsx, .xls, or .csv format.")

async def read_and_save_file(file: UploadFile, path: str) -> int:
    content = await file.read()
    if not content:
        raise http_error(400, f"Uploaded file {file.filename} is empty.")
    with open(path, 'wb') as f:
        f.write(content)
    # Whenever need to log something, just use logger.info or logger.error and I'll handle the rest.
    logger.info(f"Saved file: {path} ({len(content)} bytes)")
    return len(content)

# Error handling

def http_error(status_code: int, detail: str) -> HTTPException:
    logger.error(f"Upload error: {detail}")
    return HTTPException(status_code=status_code, detail=detail)
