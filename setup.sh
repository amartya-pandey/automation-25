#!/bin/bash

# Auto-Certy Setup Script
echo "🎓 Setting up Auto-Certy..."

# Create virtual environments
echo "📦 Creating virtual environments..."

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Frontend setup  
echo "Setting up frontend..."
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "Please edit .env file with your email credentials"
fi

echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "2. Frontend: cd frontend && source venv/bin/activate && streamlit run app.py"
