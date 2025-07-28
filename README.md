# Auto-Certy: Automated College Certificate Generator & Mailer

A web-based SaaS application that automates the generation and distribution of personalized certificates for college students. Users upload an Excel sheet containing student details, and the system generates personalized certificates and emails them to each student.

## Features

- **Streamlit Frontend**: Easy-to-use web interface for file uploads and monitoring
- **FastAPI Backend**: Robust API with background processing
- **Automated Certificate Generation**: Creates personalized PDF certificates
- **Bulk Email Sending**: Automatically emails certificates to students
- **Progress Tracking**: Real-time status updates and progress monitoring
- **Template Support**: Use custom PDF templates or default certificate design

## Tech Stack

- **Frontend**: Streamlit (Python)
- **Backend**: FastAPI with Uvicorn ASGI server
- **Certificate Generation**: ReportLab, FPDF
- **Excel Processing**: Pandas, OpenPyXL
- **Email Sending**: SMTP (supports Gmail, Outlook, etc.)
- **File Handling**: Async file operations

## Project Structure

```
auto-certy/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── certificate.py    # Certificate generation logic
│   ├── emailer.py        # Email sending functionality
│   ├── models.py         # Pydantic data models
│   └── requirements.txt  # Backend dependencies
├── frontend/
│   ├── app.py            # Streamlit application
│   └── requirements.txt  # Frontend dependencies
├── uploads/              # Temporary file storage
├── generated_certificates/ # Generated certificate storage
├── .env.example          # Environment variables template
├── .gitignore
└── README.md
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd auto-certy
```

### 2. Set Up Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set Up Frontend

```bash
cd ../frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env file with your email credentials
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI backend will be available at `http://localhost:8000`

### 2. Start the Frontend Application

```bash
cd frontend
source venv/bin/activate
streamlit run app.py
```

The Streamlit frontend will be available at `http://localhost:8501`

## Usage

### 1. Prepare Your Excel File

Your Excel file should contain these columns (case-insensitive):
- **Name** (or Student_Name, Full_Name)
- **Email** (or Email_ID, Email_Address)
- **Year_of_Study** (or Year, Academic_Year) 
- **Branch** (or Department, Course)

### 2. Configure Email Settings

For Gmail users:
1. Enable 2-factor authentication
2. Generate an App Password: Google Account → Security → App passwords
3. Use the app password instead of your regular password

### 3. Generate Certificates

1. Upload your Excel file
2. Optionally upload a PDF template
3. Configure email settings
4. Click "Generate & Send Certificates"
5. Monitor progress in real-time

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /upload-files` - Upload Excel and template files
- `POST /process-certificates` - Start certificate generation and email sending
- `GET /status/{task_id}` - Get processing status
- `GET /health` - Health check

## Configuration

### Email Providers

The application supports various SMTP providers:

**Gmail**:
- SMTP Server: `smtp.gmail.com`
- Port: `587`
- Use App Password

**Outlook/Hotmail**:
- SMTP Server: `smtp-mail.outlook.com` 
- Port: `587`

**Yahoo**:
- SMTP Server: `smtp.mail.yahoo.com`
- Port: `587`

### Certificate Templates

- Default template generates a professional-looking certificate
- Custom PDF templates are supported
- Templates should accommodate variable text placement

## Development

### Adding New Features

1. Backend changes go in the `backend/` directory
2. Frontend changes go in the `frontend/` directory
3. Follow FastAPI and Streamlit best practices
4. Add appropriate error handling and logging

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend testing
cd frontend  
streamlit run app.py
```

## Security Considerations

- Email passwords are handled securely and not stored
- Uploaded files are cleaned up after processing
- Use environment variables for sensitive configuration
- Enable HTTPS in production
- Validate all file uploads

## Deployment

### Production Deployment

1. Use production ASGI server (Gunicorn with Uvicorn workers)
2. Set up reverse proxy (Nginx)
3. Configure SSL certificates
4. Use environment variables for all configuration
5. Set up proper logging and monitoring

### Docker Deployment

```dockerfile
# Example Dockerfile for backend
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Backend Connection Error**: Ensure FastAPI server is running on port 8000
2. **Email Authentication Error**: Check credentials and use app passwords for Gmail
3. **File Upload Error**: Verify file formats (.xlsx, .xls for Excel)
4. **Missing Columns Error**: Ensure Excel file has required columns

### Logs

Check application logs for detailed error information:
- Backend logs appear in the terminal running uvicorn
- Frontend logs appear in the Streamlit interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable  
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please create an issue on the GitHub repository or contact the development team.

## Changelog

### Version 1.0.0
- Initial release
- Basic certificate generation and email functionality
- Streamlit frontend interface
- FastAPI backend with async processing
- Support for Excel file parsing
- Default PDF certificate template
