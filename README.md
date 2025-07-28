# Auto-Certy: Automated College Certificate Generator & Mailer

Auto-Certy is a Python-based system for generating and distributing personalized certificates using custom templates and student data from CSV/Excel files. It features a Streamlit UI for layout editing and preview, and a FastAPI backend for automation and bulk processing.

## Features
- **Interactive Certificate Layout Editor**: Use Streamlit to visually adjust text positions, fonts, and colors, with real-time PDF preview.
- **Custom PDF Templates**: Overlay certificate data on your own template backgrounds.
- **Batch Certificate Generation**: Generate certificates for all students in a CSV/Excel file.
- **Automated Email Sending**: Send certificates to students via email.
- **Robust Error Handling**: Clear feedback for template, data, and email issues.
- **Configurable via JSON**: All layout settings are stored in `certificate_config.json`.
- **Modern Python Tooling**: Uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python environment and dependency management.

## Project Structure
```
auto-certy/
├── backend/
│   ├── main.py                # FastAPI backend
│   ├── certificate.py         # Certificate generation logic
│   ├── edit_certificate_config.py # Streamlit config editor & preview
│   ├── requirements.txt       # Backend dependencies
│   └── certificate_config.json# Certificate layout config
├── frontend/
│   ├── app.py                 # Streamlit frontend (OCR, manual entry, etc.)
│   └── requirements.txt       # Frontend dependencies
├── uploads/                   # Uploaded files
├── generated_certificates/    # Output certificates
├── README.md
└── ...
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended for Python package management)
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd auto-certy
```

### 2. Set Up Backend (with uv)
```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Set Up Frontend (with uv)
```bash
cd ../frontend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 4. Configure Environment Variables
Edit any required `.env` files for email credentials, etc.

## Running the Application

### 1. Start the Backend Server
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Streamlit Certificate Config Editor
```bash
streamlit run edit_certificate_config.py
```

### 3. Start the Frontend Application
```bash
cd ../frontend
source .venv/bin/activate
streamlit run app.py
```

## Usage
- Use the Streamlit config editor to visually adjust certificate layout and preview results.
- Upload your student CSV/Excel file and template PDF.
- Generate certificates and send emails via the backend or frontend UI.

## Modern Python Environment: uv
This project recommends [uv](https://github.com/astral-sh/uv) for creating virtual environments and installing dependencies. uv is much faster and more reliable than pip and venv.
- Create a new environment: `uv venv`
- Install dependencies: `uv pip install -r requirements.txt`

## Troubleshooting
- If the certificate preview does not render, check your template PDF path and validity.
- For font issues, ensure the specified fonts are available on your system.
- For email issues, verify credentials and SMTP settings.

## License
MIT

## Support
Open an issue or contact the maintainers via GitHub.
