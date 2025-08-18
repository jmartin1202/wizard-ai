# -*- coding: utf-8 -*-
import os
import json
import requests
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
import time
from collections import defaultdict
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
CORS(app)

# Rate limiting
rate_limits = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS_PER_WINDOW = 10

def check_rate_limit(user_id):
    """Check if user has exceeded rate limit"""
    current_time = time.time()
    user_requests = rate_limits[user_id]
    
    # Remove old requests outside the window
    user_requests[:] = [req_time for req_time in user_requests if current_time - req_time < RATE_LIMIT_WINDOW]
    
    if len(user_requests) >= MAX_REQUESTS_PER_WINDOW:
        return False
    
    user_requests.append(current_time)
    return True

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/manifest.json')
def manifest():
    """Serve the PWA manifest file"""
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    """Serve the service worker file"""
    return app.send_static_file('sw.js')

@app.route('/debug')
def debug():
    """Debug endpoint to test backend connectivity"""
    return jsonify({
        'status': 'Backend is running',
        'timestamp': time.time(),
        'environment': 'production' if os.environ.get('FLASK_ENV') == 'production' else 'development'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint supporting multiple AI models"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        model = data.get('model', 'gpt-4o')  # Default to GPT-4o
        use_memory = data.get('use_memory', True)
        
        # Check rate limit
        user_id = session.get('user_id', 'anonymous')
        if not check_rate_limit(user_id):
            return jsonify({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Route to appropriate AI model
        if model.startswith('gpt'):
            return chat_with_openai(message, model, use_memory)
        elif model.startswith('claude'):
            return chat_with_claude(message, model, use_memory)
        elif model.startswith('gemini'):
            return chat_with_gemini(message, model, use_memory)
        else:
            return jsonify({'success': False, 'error': f'Unsupported model: {model}'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat-with-image', methods=['POST'])
def chat_with_image():
    """Chat with image using multiple AI models"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        image_data = data.get('image_data', '')
        model = data.get('model', 'gpt-4o')  # Default to GPT-4o for image analysis
        use_memory = data.get('use_memory', True)
        
        # Check rate limit
        user_id = session.get('user_id', 'anonymous')
        if not check_rate_limit(user_id):
            return jsonify({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Route to appropriate AI model (only GPT-4o supports images currently)
        if model.startswith('gpt'):
            return chat_with_openai_image(message, image_data, use_memory)
        else:
            return jsonify({'success': False, 'error': f'Image analysis not supported for model: {model}'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat-with-document', methods=['POST'])
def chat_with_document():
    """Chat with document using multiple AI models"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        document_data = data.get('document_data', '')
        document_name = data.get('document_name', 'Document')
        model = data.get('model', 'gpt-4o')  # Default to GPT-4o
        use_memory = data.get('use_memory', True)
        
        # Check rate limit
        user_id = session.get('user_id', 'anonymous')
        if not check_rate_limit(user_id):
            return jsonify({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Route to appropriate AI model
        if model.startswith('gpt'):
            return chat_with_openai_document(message, document_data, document_name, use_memory)
        elif model.startswith('claude'):
            return chat_with_claude_document(message, document_data, document_name, use_memory)
        elif model.startswith('gemini'):
            return chat_with_gemini_document(message, document_data, document_name, use_memory)
        else:
            return jsonify({'success': False, 'error': f'Unsupported model: {model}'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compare-models', methods=['POST'])
def compare_models():
    """Compare responses from multiple AI models"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        models = data.get('models', ['gpt-4o', 'claude-3-sonnet', 'gemini-1.5-pro'])
        use_memory = data.get('use_memory', True)
        
        # Check rate limit
        user_id = session.get('user_id', 'anonymous')
        if not check_rate_limit(user_id):
            return jsonify({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Get responses from all models
        responses = {}
        for model in models:
            try:
                if model.startswith('gpt'):
                    response = chat_with_openai(message, model, use_memory)
                    if response[1] == 200:
                        responses[model] = response[0].get_json()['response']
                    else:
                        responses[model] = f"Error: {response[0].get_json()['error']}"
                elif model.startswith('claude'):
                    response = chat_with_claude(message, model, use_memory)
                    if response[1] == 200:
                        responses[model] = response[0].get_json()['response']
                    else:
                        responses[model] = f"Error: {response[0].get_json()['error']}"
                elif model.startswith('gemini'):
                    response = chat_with_gemini(message, model, use_memory)
                    if response[1] == 200:
                        responses[model] = response[0].get_json()['response']
                    else:
                        responses[model] = f"Error: {response[0].get_json()['error']}"
            except Exception as e:
                responses[model] = f"Error: {str(e)}"
        
        return jsonify({
            'success': True,
            'responses': responses,
            'message': message,
            'models_compared': models
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available AI models"""
    models = {
        'openai': [
            {'id': 'gpt-4o', 'name': 'GPT-4o', 'description': 'Latest OpenAI model with enhanced capabilities', 'supports_images': True},
            {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'description': 'Fast and efficient GPT-4 variant', 'supports_images': False},
            {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'description': 'Fast and cost-effective model', 'supports_images': False}
        ],
        'anthropic': [
            {'id': 'claude-3-sonnet', 'name': 'Claude 3.5 Sonnet', 'description': 'Anthropic\'s most capable model', 'supports_images': False},
            {'id': 'claude-3-haiku', 'name': 'Claude 3 Haiku', 'description': 'Fast and efficient Claude model', 'supports_images': False}
        ],
        'google': [
            {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro', 'description': 'Google\'s most advanced AI model', 'supports_images': False},
            {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash', 'description': 'Fast and efficient Gemini model', 'supports_images': False}
        ]
    }
    
    return jsonify({'success': True, 'models': models})

# OpenAI Integration
def chat_with_openai(message, model='gpt-4o', use_memory=True):
    """Chat with OpenAI models"""
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            tokens_used = result['usage']['total_tokens']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': model,
                'tokens_used': tokens_used,
                'provider': 'openai'
            })
        else:
            return jsonify({'success': False, 'error': f'OpenAI API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def chat_with_openai_image(message, image_data, use_memory=True):
    """Chat with OpenAI models using image input"""
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        data = {
            'model': 'gpt-4o',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': message},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_data}'}}
                    ]
                }
            ],
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            tokens_used = result['usage']['total_tokens']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': 'gpt-4o',
                'tokens_used': tokens_used,
                'provider': 'openai'
            })
        else:
            return jsonify({'success': False, 'error': f'OpenAI API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def chat_with_openai_document(message, document_data, document_name, use_memory=True):
    """Chat with OpenAI models using document input"""
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        enhanced_message = f"Document: {document_name}\n\nContent:\n{document_data}\n\nUser Question: {message}"
        
        data = {
            'model': 'gpt-4o',
            'messages': [{'role': 'user', 'content': enhanced_message}],
            'max_tokens': 1000,
            'temperature': 0.7
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            tokens_used = result['usage']['total_tokens']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': 'gpt-4o',
                'tokens_used': tokens_used,
                'provider': 'openai'
            })
        else:
            return jsonify({'success': False, 'error': f'OpenAI API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Claude Integration
def chat_with_claude(message, model='claude-3-sonnet', use_memory=True):
    """Chat with Claude models"""
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Anthropic API key not configured'}), 500
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # Map model names to Claude API format
        model_mapping = {
            'claude-3-sonnet': 'claude-3-5-sonnet-20241022',
            'claude-3-haiku': 'claude-3-haiku-20240307'
        }
        
        claude_model = model_mapping.get(model, 'claude-3-5-sonnet-20241022')
        
        data = {
            'model': claude_model,
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': message}]
        }
        
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['content'][0]['text']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': model,
                'provider': 'anthropic'
            })
        else:
            return jsonify({'success': False, 'error': f'Claude API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def chat_with_claude_document(message, document_data, document_name, use_memory=True):
    """Chat with Claude models using document input"""
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Anthropic API key not configured'}), 500
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        enhanced_message = f"Document: {document_name}\n\nContent:\n{document_data}\n\nUser Question: {message}"
        
        data = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': enhanced_message}]
        }
        
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['content'][0]['text']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': 'claude-3-sonnet',
                'provider': 'anthropic'
            })
        else:
            return jsonify({'success': False, 'error': f'Claude API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Gemini Integration
def chat_with_gemini(message, model='gemini-1.5-pro', use_memory=True):
    """Chat with Gemini models"""
    try:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Google API key not configured'}), 500
        
        # Map model names to Gemini API format
        model_mapping = {
            'gemini-1.5-pro': 'gemini-1.5-pro',
            'gemini-1.5-flash': 'gemini-1.5-flash'
        }
        
        gemini_model = model_mapping.get(model, 'gemini-1.5-pro')
        
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}'
        
        data = {
            'contents': [{
                'parts': [{'text': message}]
            }],
            'generationConfig': {
                'maxOutputTokens': 1000,
                'temperature': 0.7
            }
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'model': model,
                'provider': 'google'
            })
        else:
            return jsonify({'success': False, 'error': f'Gemini API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def chat_with_gemini_document(message, document_data, document_name, use_memory=True):
    """Chat with Gemini models using document input"""
    try:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Google API key not configured'}), 500
        
        enhanced_message = f"Document: {document_name}\n\nContent:\n{document_data}\n\nUser Question: {message}"
        
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}'
        
        data = {
            'contents': [{
                'parts': [{'text': enhanced_message}]
            }],
            'generationConfig': {
                'maxOutputTokens': 1000,
                'temperature': 0.7
            }
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            return jsonify({'success': True, 'response': ai_response, 'model': 'gemini-1.5-pro', 'provider': 'google'})
        else:
            return jsonify({'success': False, 'error': f'Gemini API error: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/personalities', methods=['GET'])
def get_personalities():
    """Get available AI personalities"""
    try:
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        personalities = ai.get_available_personalities()
        current_personality = session.get('personality', 'default')
        
        return jsonify({
            'success': True,
            'personalities': personalities,
            'current_personality': current_personality
        })
        
    except Exception as e:
        logger.error(f'Error getting personalities: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to get personalities'
        }), 500

@app.route('/api/personality', methods=['POST'])
def change_personality():
    """Change AI personality"""
    try:
        data = request.get_json()
        if not data or 'personality' not in data:
            return jsonify({'error': 'Personality is required'}), 400
        
        personality = data['personality']
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        result = ai.change_personality(personality)
        if result['success']:
            session['personality'] = personality
            return jsonify({
                'success': True,
                'personality': personality,
                'message': f'AI personality changed to {personality}'
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f'Error changing personality: {e}')
        return jsonify({'error': 'Failed to change personality'}), 500

@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    """Clear conversation history for current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'No user session found'}), 400
        
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        result = ai.clear_conversation(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'Error clearing conversation: {e}')
        return jsonify({'error': 'Failed to clear conversation'}), 500

@app.route('/api/conversation-info', methods=['GET'])
def get_conversation_info():
    """Get conversation information for current user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'No user session found'}), 400
        
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        context = ai.get_conversation_context(user_id)
        return jsonify({
            'success': True,
            'conversation_length': len(context),
            'user_id': user_id,
            'personality': session.get('personality', 'default')
        })
        
    except Exception as e:
        logger.error(f'Error getting conversation info: {e}')
        return jsonify({'error': 'Failed to get conversation info'}), 500

@app.route('/api/real-time-capabilities', methods=['GET'])
def get_real_time_capabilities():
    """Get available real-time information services"""
    try:
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        capabilities = ai.get_real_time_capabilities()
        return jsonify({
            'success': True,
            'capabilities': capabilities,
            'note': 'Some services require API keys to be configured'
        })
        
    except Exception as e:
        logger.error(f'Error getting real-time capabilities: {e}')
        return jsonify({'error': 'Failed to get real-time capabilities'}), 500

@app.route('/api/test-real-time/<service>', methods=['GET'])
def test_real_time_service(service):
    """Test a specific real-time service"""
    try:
        from simple_openai import RealTimeInfo
        rt = RealTimeInfo()
        
        if service == 'weather':
            result = rt.get_weather('London')
        elif service == 'time':
            result = {"time": rt.get_current_time(), "timezone": "Local"}
        elif service == 'crypto':
            result = rt.get_crypto_price('bitcoin')
        elif service == 'news':
            result = rt.get_news_headlines()
        elif service == 'stocks':
            result = rt.get_stock_price('AAPL')
        else:
            return jsonify({'error': 'Unknown service'}), 400
        
        return jsonify({
            'success': True,
            'service': service,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error testing real-time service {service}: {e}')
        return jsonify({'error': f'Failed to test {service} service'}), 500

@app.route('/api/models')
def get_models():
    """Get available AI models"""
    try:
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        models = ai.get_available_models()
        return jsonify({
            'success': True,
            'models': models,
            'default_provider': ai.default_provider,
            'default_model': ai.default_model
        })
    except Exception as e:
        logger.error(f'Error getting models: {e}')
        return jsonify({'error': 'Failed to get models'}), 500

@app.route('/api/real-time/<query_type>')
def get_real_time_info(query_type):
    """Get real-time information"""
    try:
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        
        # Get query parameters
        city = request.args.get('city', 'New York')
        timezone = request.args.get('timezone', 'UTC')
        symbol = request.args.get('symbol', 'BTC')
        topic = request.args.get('topic', 'technology')
        limit = request.args.get('limit', 3, type=int)
        
        # Get real-time information
        if query_type == 'weather':
            info = ai.get_real_time_info('weather', city=city)
        elif query_type == 'time':
            info = ai.get_real_time_info('time', timezone=timezone)
        elif query_type == 'crypto':
            info = ai.get_real_time_info('crypto', symbol=symbol)
        elif query_type == 'news':
            info = ai.get_real_time_info('news', topic=topic, limit=limit)
        elif query_type == 'stocks':
            info = ai.get_real_time_info('stocks', symbol=symbol)
        else:
            return jsonify({'error': 'Invalid query type'}), 400
        
        return jsonify({
            'success': True,
            'query_type': query_type,
            'data': info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Real-time info error: {e}')
        return jsonify({'error': 'Failed to get real-time information'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 8080))
    
    if debug_mode:
        logger.info('Starting Flask app in development mode')
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        logger.info('Starting Flask app in production mode')
        app.run(debug=False, host='0.0.0.0', port=port)
