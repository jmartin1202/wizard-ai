# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import re
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    print('Warning: OPENAI_API_KEY not found. AI features will be disabled.')

# Main routes
@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate AI response
        if client:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': message}]
            )
            ai_response = response.choices[0].message.content.strip()
        else:
            ai_response = 'AI features are currently unavailable.'
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'ai_generated': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
