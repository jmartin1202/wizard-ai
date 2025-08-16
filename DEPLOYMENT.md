# 🚀 Deployment Guide: AI Chatbot to GitHub & Heroku

This guide will walk you through deploying your AI chatbot to GitHub and then to Heroku.

## 📋 Prerequisites

- [Git](https://git-scm.com/) installed on your computer
- [GitHub](https://github.com/) account
- [Heroku](https://heroku.com/) account
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed

## 🔧 Step 1: Prepare Your Local Repository

### 1.1 Initialize Git (if not already done)
```bash
git init
```

### 1.2 Add your files
```bash
git add .
```

### 1.3 Make your first commit
```bash
git commit -m "Initial commit: AI Chatbot with OpenAI integration"
```

## 🌐 Step 2: Push to GitHub

### 2.1 Create a new repository on GitHub
1. Go to [GitHub](https://github.com/)
2. Click the "+" icon → "New repository"
3. Name it something like `wizard-ai`
4. Make it public or private (your choice)
5. **Don't** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### 2.2 Connect and push to GitHub
```bash
git remote add origin https://github.com/jmartin1202/wizard-ai.git
git branch -M main
git push -u origin main
```

## 🚀 Step 3: Deploy to Heroku

### 3.1 Login to Heroku CLI
```bash
heroku login
```

### 3.2 Create a new Heroku app
```bash
heroku create your-app-name
```
Replace `your-app-name` with a unique name for your app.

### 3.3 Set environment variables
```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key_here
heroku config:set FLASK_ENV=production
```

### 3.4 Deploy your app
```bash
git push heroku main
```

### 3.5 Open your app
```bash
heroku open
```

## 🔑 Step 4: Configure Environment Variables

In Heroku, you need to set these environment variables:

1. **OPENAI_API_KEY**: Your OpenAI API key
2. **FLASK_ENV**: Set to `production` for Heroku

### Set via Heroku Dashboard:
1. Go to your app on [Heroku Dashboard](https://dashboard.heroku.com/)
2. Click on "Settings" tab
3. Click "Reveal Config Vars"
4. Add each variable:
   - Key: `OPENAI_API_KEY`, Value: `sk-...`
   - Key: `FLASK_ENV`, Value: `production`

### Set via CLI:
```bash
heroku config:set OPENAI_API_KEY=sk-your-key-here
heroku config:set FLASK_ENV=production
```

## 📱 Step 5: Test Your Deployed App

1. Visit your Heroku app URL
2. Test the chat functionality
3. Check the debug endpoint: `https://your-app.herokuapp.com/debug`

## 🔄 Step 6: Continuous Deployment (Optional)

To automatically deploy when you push to GitHub:

1. In Heroku Dashboard, go to "Deploy" tab
2. Choose "GitHub" as deployment method
3. Connect your GitHub repository
4. Enable automatic deploys from the `main` branch

## 🐛 Troubleshooting

### Common Issues:

1. **Build fails**: Check that all dependencies are in `requirements.txt`
2. **App crashes**: Check Heroku logs with `heroku logs --tail`
3. **Environment variables not working**: Verify they're set correctly in Heroku
4. **Port issues**: The app automatically uses Heroku's `PORT` environment variable

### Check Logs:
```bash
heroku logs --tail
```

### Restart App:
```bash
heroku restart
```

## 📊 Monitoring

- **Heroku Dashboard**: Monitor app performance and errors
- **Logs**: Use `heroku logs --tail` for real-time monitoring
- **Metrics**: Check response times and error rates in Heroku dashboard

## 🔒 Security Notes

- Never commit your `.env` file to GitHub
- Use Heroku's environment variables for sensitive data
- The `.gitignore` file ensures sensitive files aren't committed
- Your OpenAI API key is secure in Heroku's environment variables

## 🎯 Next Steps

After successful deployment:
1. Set up a custom domain (optional)
2. Configure SSL certificates
3. Set up monitoring and alerts
4. Scale your app as needed

---

**Need Help?** Check the [Heroku Documentation](https://devcenter.heroku.com/) or [GitHub Help](https://help.github.com/)
