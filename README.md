# 🤖 Wizard AI - AI Chatbot

A modern, production-ready AI chatbot built with Flask and OpenAI's GPT models.

## ✨ Features

- **🤖 AI-Powered Chat**: Integrated with OpenAI's GPT-3.5-turbo model
- **🌐 Web Interface**: Clean, responsive chat interface
- **🔒 Security**: Rate limiting, input validation, and secure API key handling
- **📱 RESTful API**: JSON-based API for easy integration
- **🚀 Production Ready**: Configured for Heroku deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key
- Git

### Local Development
1. Clone the repository
2. Set up virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with your OpenAI API key
5. Run: `python app.py`
6. Open: `http://localhost:8080`

## 🌐 API Endpoints

- **POST** `/api/chat` - Chat with AI
- **GET** `/debug` - Check system status
- **GET** `/test-simple-openai` - Test OpenAI service

## 🚀 Deployment

### Deploy to Heroku
```bash
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_api_key_here
heroku config:set FLASK_ENV=production
git push heroku main
```

## 🔒 Security

- Rate limiting: 10 requests per minute per IP
- Input validation and sanitization
- Secure environment variable handling
- No sensitive data in code

---

**Ready to deploy!** 🚀
