# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session
import os
from datetime import datetime
import logging
from collections import defaultdict
import time
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables are loaded automatically on Heroku

# Configure logging
logging.basicConfig(level=logging.INFO, format='INFO:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def get_openai_client():
    """Get OpenAI client instance - using external service"""
    # Get API key directly from environment each time
    api_key = os.environ.get('OPENAI_API_KEY')
    logger.info(f"get_openai_client called, OPENAI_API_KEY exists: {bool(api_key)}")
    
    if not api_key:
        logger.warning("No OPENAI_API_KEY found")
        return None
    
    try:
        # Use external service to avoid import issues
        logger.info("Using external OpenAI service")
        return "external_service"  # Return service marker
        
    except Exception as e:
        logger.error(f'Failed to initialize OpenAI service: {e}')
        return None

# Initialize client
client = get_openai_client()
if client:
    logger.info('OpenAI API key loaded successfully')
    logger.info(f'Client object: {client}')
    logger.info(f'Client type: {type(client)}')
else:
    logger.warning('OpenAI client not available. AI features will be disabled.')
    logger.info(f'Client value: {client}')

# Rate limiting
RATE_LIMIT = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
request_counts = defaultdict(list)

def is_rate_limited(client_ip):
    """Check if client is rate limited"""
    now = time.time()
    # Remove old requests outside the window
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] 
                                if now - req_time < RATE_LIMIT_WINDOW]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return True
    
    request_counts[client_ip].append(now)
    return False

# Main routes
@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/debug')
def debug():
    """Debug endpoint to check API key and client status"""
    api_key = os.environ.get('OPENAI_API_KEY')
    logger.info(f"Debug endpoint: API key exists: {bool(api_key)}")
    
    try:
        client = get_openai_client()
        if client == "external_service":
            return jsonify({
                'api_key_exists': bool(api_key),
                'client_created': True,
                'client_type': 'external_service',
                'error': None
            })
        else:
            return jsonify({
                'api_key_exists': bool(api_key),
                'client_created': False,
                'client_type': 'none',
                'error': 'Client creation failed'
            })
    except Exception as e:
        return jsonify({
            'api_key_exists': bool(api_key),
            'client_created': False,
            'client_type': 'error',
            'error': str(e)
        })

@app.route('/test-simple-openai')
def test_simple_openai():
    """Test endpoint for simple OpenAI module"""
    try:
        # Test the simple OpenAI module directly
        from simple_openai import call_openai_direct
        
        result = call_openai_direct("Say hello", max_tokens=20, temperature=0.7)
        
        return jsonify({
            'success': result.get('success'),
            'response': result.get('response'),
            'error': result.get('error')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': str(type(e))
        })

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        # Get OpenAI client for this request
        client = get_openai_client()
        
        # Debug logging
        logger.info(f'Client variable value: {client}')
        logger.info(f'Client type: {type(client)}')
        
        # Rate limiting
        client_ip = request.remote_addr
        if is_rate_limited(client_ip):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        message = data.get('message', '').strip()
        personality = data.get('personality', 'default')
        use_memory = data.get('use_memory', True)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(message) > 2000:  # Increased from 1000
            return jsonify({'error': 'Message too long (max 2000 characters)'}), 400
        
        # Generate AI response using advanced features
        if client and client != "external_service":
            logger.info('Client is available, attempting to generate AI response')
            try:
                response = client.chat.completions.create(
                    model='gpt-4',
                    messages=[{'role': 'user', 'content': message}],
                    max_tokens=1000,  # Increased from 500
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content.strip()
                logger.info(f'AI response generated for user: {client_ip}')
            except Exception as e:
                logger.error(f'Unexpected OpenAI error: {e}')
                return jsonify({'error': 'AI service error'}), 500
        elif client == "external_service":
            logger.info('Using external OpenAI service with advanced features')
            try:
                # Import and use the advanced OpenAI module
                from simple_openai import AdvancedOpenAI
                
                # Initialize advanced AI with user session
                user_id = session.get('user_id', str(uuid.uuid4()))
                if 'user_id' not in session:
                    session['user_id'] = user_id
                
                ai = AdvancedOpenAI()
                
                logger.info(f'Calling advanced OpenAI service for user: {user_id}, personality: {personality}')
                result = ai.call_openai_advanced(
                    message, 
                    user_id=user_id, 
                    personality=personality,
                    max_tokens=1000,  # Increased token limit
                    temperature=0.7,
                    use_memory=use_memory
                )
                
                if result.get('success'):
                    ai_response = result['response']
                    model_used = result.get('model_used', 'unknown')
                    tokens_used = result.get('tokens_used', 0)
                    conv_length = result.get('conversation_length', 0)
                    
                    logger.info(f'AI response generated for user: {user_id} (advanced service)')
                    logger.info(f'Response length: {len(ai_response)}')
                    logger.info(f'Model used: {model_used}, Tokens: {tokens_used}, Context: {conv_length}')
                    
                    return jsonify({
                        'response': ai_response,
                        'timestamp': datetime.now().isoformat(),
                        'ai_generated': True,
                        'model_used': model_used,
                        'tokens_used': tokens_used,
                        'conversation_length': conv_length,
                        'personality': personality
                    })
                else:
                    logger.error(f'Advanced service error: {result.get("error")}')
                    return jsonify({'error': 'AI service temporarily unavailable'}), 503
                    
            except ImportError as e:
                logger.error(f'Failed to import advanced service: {e}')
                return jsonify({'error': 'AI service configuration error'}), 500
            except Exception as e:
                logger.error(f'Unexpected error with advanced service: {e}')
                logger.error(f'Error type: {type(e)}')
                logger.error(f'Error details: {str(e)}')
                import traceback
                logger.error(f'Traceback: {traceback.format_exc()}')
                return jsonify({'error': 'AI service error'}), 500
        else:
            logger.warning('Client is None, AI features unavailable')
            ai_response = 'AI features are currently unavailable. Please check your configuration.'
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'ai_generated': True
        })
        
    except Exception as e:
        logger.error(f'Unexpected error in chat_api: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/personalities', methods=['GET'])
def get_personalities():
    """Get available AI personalities"""
    try:
        from simple_openai import AdvancedOpenAI
        ai = AdvancedOpenAI()
        personalities = ai.get_available_personalities()
        return jsonify({
            'success': True,
            'personalities': personalities,
            'current_personality': session.get('personality', 'default')
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
