from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class StudentRecord(BaseModel):
    name: str
    email: EmailStr
    year_of_study: str
    branch: str

class ProcessingStatus(BaseModel):
    status: str
    message: str
    processed_count: int = 0
    total_count: int = 0
    timestamp: datetime = datetime.now()
    results: Optional[dict] = None  # Added to store summary/results

class EmailConfig(BaseModel):
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str
    sender_password: str
    subject: str = "Your Certificate"
    body_template: str = "Dear {name},\n\nPlease find your certificate attached.\n\nBest regards,\nCertificate Team"

class CertificateRequest(BaseModel):
    template_path: str
    excel_path: str
    email_config: EmailConfig
