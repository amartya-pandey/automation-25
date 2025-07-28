from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import aiofiles
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from models import ProcessingStatus, EmailConfig
from certificate import CertificateGenerator
from emailer import EmailSender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auto-Certy API", description="Automated Certificate Generator and Mailer", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for processing status (use Redis/DB in production)
processing_status = {}
upload_dir = "../uploads"
os.makedirs(upload_dir, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Auto-Certy API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/upload-files")
async def upload_files(
    excel_file: UploadFile = File(...),
    template_file: Optional[UploadFile] = File(None)
):
    """Upload Excel file and optional template file."""
    try:
        # Validate file types
        if not excel_file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Excel file must be .xlsx or .xls format")
        
        if template_file and not template_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Template file must be PDF format")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Save Excel file
        excel_path = os.path.join(upload_dir, f"{task_id}_{excel_file.filename}")
        async with aiofiles.open(excel_path, 'wb') as f:
            content = await excel_file.read()
            await f.write(content)
        
        # Save template file if provided
        template_path = None
        if template_file:
            template_path = os.path.join(upload_dir, f"{task_id}_{template_file.filename}")
            async with aiofiles.open(template_path, 'wb') as f:
                content = await template_file.read()
                await f.write(content)
        
        # Initialize processing status
        processing_status[task_id] = ProcessingStatus(
            status="uploaded",
            message="Files uploaded successfully",
            processed_count=0,
            total_count=0
        )
        
        return {
            "task_id": task_id,
            "message": "Files uploaded successfully",
            "excel_file": excel_file.filename,
            "template_file": template_file.filename if template_file else None
        }
        
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-certificates")
async def process_certificates(
    background_tasks: BackgroundTasks,
    task_id: str = Form(...),
    sender_email: str = Form(...),
    sender_password: str = Form(...),
    email_subject: str = Form("Your Certificate"),
    email_body: str = Form("Dear {name},\n\nPlease find your certificate attached.\n\nBest regards,\nCertificate Team"),
    smtp_server: str = Form("smtp.gmail.com"),
    smtp_port: int = Form(587)
):
    """Start certificate generation and email sending process."""
    try:
        if task_id not in processing_status:
            raise HTTPException(status_code=404, detail="Task ID not found")
        
        # Update status
        processing_status[task_id].status = "processing"
        processing_status[task_id].message = "Starting certificate generation..."
        
        # Create email configuration
        email_config = EmailConfig(
            sender_email=sender_email,
            sender_password=sender_password,
            subject=email_subject,
            body_template=email_body,
            smtp_server=smtp_server,
            smtp_port=smtp_port
        )
        
        # Start background task
        background_tasks.add_task(
            process_certificates_background,
            task_id,
            email_config
        )
        
        return {
            "message": "Certificate processing started",
            "task_id": task_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error starting certificate processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_certificates_background(task_id: str, email_config: EmailConfig):
    """Background task to process certificates and send emails."""
    try:
        # Find uploaded files
        excel_files = [f for f in os.listdir(upload_dir) if f.startswith(task_id) and f.endswith(('.xlsx', '.xls'))]
        if not excel_files:
            processing_status[task_id].status = "error"
            processing_status[task_id].message = "Excel file not found"
            return
        
        excel_path = os.path.join(upload_dir, excel_files[0])
        
        # Initialize certificate generator
        cert_generator = CertificateGenerator()
        
        # Parse Excel file
        processing_status[task_id].message = "Parsing Excel file..."
        students = cert_generator.parse_excel(excel_path)
        processing_status[task_id].total_count = len(students)
        
        # Generate certificates
        processing_status[task_id].message = "Generating certificates..."
        certificate_paths = cert_generator.generate_all_certificates(students)
        
        # Update progress
        processing_status[task_id].processed_count = len(certificate_paths)
        processing_status[task_id].message = "Certificates generated. Sending emails..."
        
        # Send emails
        email_sender = EmailSender(email_config)
        
        # Test email connection first
        if not email_sender.test_email_connection():
            processing_status[task_id].status = "error"
            processing_status[task_id].message = "Email connection failed. Please check your credentials."
            return
        
        # Send bulk emails
        email_results = email_sender.send_bulk_emails(students, certificate_paths)
        
        # Update final status
        processing_status[task_id].status = "completed"
        processing_status[task_id].message = f"Process completed. Sent {email_results['success_count']} emails successfully, {email_results['failure_count']} failed."
        processing_status[task_id].processed_count = email_results['success_count']
        
        # Store detailed results
        processing_status[task_id].results = email_results
        
    except Exception as e:
        logger.error(f"Error in background processing: {e}")
        processing_status[task_id].status = "error"
        processing_status[task_id].message = f"Processing failed: {str(e)}"

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get processing status for a task."""
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task ID not found")
    
    status = processing_status[task_id]
    return {
        "task_id": task_id,
        "status": status.status,
        "message": status.message,
        "processed_count": status.processed_count,
        "total_count": status.total_count,
        "timestamp": status.timestamp,
        "results": getattr(status, 'results', None)
    }

@app.get("/tasks")
async def list_tasks():
    """List all processing tasks."""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": status.status,
                "message": status.message,
                "timestamp": status.timestamp
            }
            for task_id, status in processing_status.items()
        ]
    }

@app.delete("/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Clean up files and status for a completed task."""
    try:
        # Remove from processing status
        if task_id in processing_status:
            del processing_status[task_id]
        
        # Clean up uploaded files
        for filename in os.listdir(upload_dir):
            if filename.startswith(task_id):
                os.remove(os.path.join(upload_dir, filename))
        
        # Clean up generated certificates
        cert_dir = "../generated_certificates"
        if os.path.exists(cert_dir):
            for filename in os.listdir(cert_dir):
                if task_id in filename:
                    os.remove(os.path.join(cert_dir, filename))
        
        return {"message": "Task cleaned up successfully"}
        
    except Exception as e:
        logger.error(f"Error cleaning up task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
