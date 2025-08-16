# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import logging
from collections import defaultdict
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if len(message) > 1000:
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400
        
        # Generate AI response
        if client and client != "external_service":
            logger.info('Client is available, attempting to generate AI response')
            try:
                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{'role': 'user', 'content': message}],
                    max_tokens=500,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content.strip()
                logger.info(f'AI response generated for user: {client_ip}')
            except Exception as e:
                logger.error(f'Unexpected OpenAI error: {e}')
                return jsonify({'error': 'AI service error'}), 500
        elif client == "external_service":
            logger.info('Using external OpenAI service')
            try:
                # Import and use the simple OpenAI module
                from simple_openai import call_openai_direct
                
                logger.info('Calling simple OpenAI service...')
                result = call_openai_direct(message, max_tokens=500, temperature=0.7)
                
                if result.get('success'):
                    ai_response = result['response']
                    logger.info(f'AI response generated for user: {client_ip} (simple service)')
                    logger.info(f'Response length: {len(ai_response)}')
                else:
                    logger.error(f'Simple service error: {result.get("error")}')
                    return jsonify({'error': 'AI service temporarily unavailable'}), 503
                    
            except ImportError as e:
                logger.error(f'Failed to import simple service: {e}')
                return jsonify({'error': 'AI service configuration error'}), 500
            except Exception as e:
                logger.error(f'Unexpected error with simple service: {e}')
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
