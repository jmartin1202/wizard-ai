# 🚀 Deployment Guide: Wizard AI to GitHub & Heroku

## 📋 Prerequisites

- [Git](https://git-scm.com/) installed
- [GitHub](https://github.com/) account
- [Heroku](https://heroku.com/) account
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed

## 🌐 Step 1: Push to GitHub

### 1.1 Initialize Git
```bash
git init
git add .
git commit -m "Initial commit: Wizard AI chatbot"
```

### 1.2 Connect to GitHub
```bash
git remote add origin https://github.com/jmartin1202/wizard-ai.git
git branch -M main
git push -u origin main
```

## 🚀 Step 2: Deploy to Heroku

### 2.1 Login to Heroku
```bash
heroku login
```

### 2.2 Create Heroku app
```bash
heroku create your-app-name
```

### 2.3 Set environment variables
```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key_here
heroku config:set FLASK_ENV=production
```

### 2.4 Deploy
```bash
git push heroku main
```

### 2.5 Open your app
```bash
heroku open
```

## 🔑 Environment Variables

Set these in Heroku:
- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_ENV`: Set to `production`

## 🐛 Troubleshooting

Check logs: `heroku logs --tail`
Restart app: `heroku restart`

---

**Need Help?** Check [Heroku Documentation](https://devcenter.heroku.com/)
