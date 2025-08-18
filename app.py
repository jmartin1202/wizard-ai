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
    """Debug endpoint to check API key and client status"""
    api_key = os.environ.get('OPENAI_API_KEY')
    logger.info(f"Debug endpoint: API key exists: {bool(api_key)}")
    
    try:
        client = get_openai_client()
        if client == "external_service":
            # Test simple_openai module
            try:
                from simple_openai import AdvancedOpenAI
                ai = AdvancedOpenAI()
                ai_status = {
                    'module_loaded': True,
                    'api_key_exists': bool(ai.api_key),
                    'api_key_preview': ai.api_key[:20] + "..." if ai.api_key else None,
                    'available_models': ai.get_available_models()
                }
            except Exception as e:
                ai_status = {
                    'module_loaded': False,
                    'error': str(e)
                }
            
            return jsonify({
                'api_key_exists': bool(api_key),
                'client_key': api_key[:20] + "..." if api_key else None,
                'client_created': True,
                'client_type': 'external_service',
                'simple_openai_status': ai_status,
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
def chat():
    """Chat endpoint with model selection"""
    if is_rate_limited(request.remote_addr):
        return jsonify({'error': 'Rate limit exceeded. Please wait a moment.'}), 429
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        personality = data.get('personality', 'default')
        use_memory = data.get('use_memory', True)
        provider = data.get('provider', 'openai')
        model = data.get('model', None)
        
        # Generate user ID if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # Initialize AI with model selection
        try:
            from simple_openai import AdvancedOpenAI
            ai = AdvancedOpenAI()
            
            # Log API key status
            logger.info(f"AI initialized for chat, API key exists: {bool(ai.api_key)}")
            logger.info(f"Using provider: {provider}, model: {model}")
            
            # Get AI response with selected model
            response = ai.call_ai_model(
                message=message,
                user_id=user_id,
                personality=personality,
                use_memory=use_memory,
                provider=provider,
                model=model
            )
            
            logger.info(f"AI response received: {response}")
            
        except ImportError as e:
            logger.error(f"Failed to import simple_openai: {e}")
            return jsonify({'error': 'AI module import failed'}), 500
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")
            return jsonify({'error': 'AI initialization failed'}), 500
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'response': response['response'],
                'personality': personality,
                'model_used': response.get('model_used', 'Unknown'),
                'provider': response.get('provider', 'Unknown'),
                'tokens_used': response.get('tokens_used', 0),
                'conversation_length': response.get('conversation_length', 0)
            })
        else:
            error_msg = response.get('error', 'Unknown error occurred') if response else 'No response from AI'
            logger.error(f"AI error: {error_msg}")
            return jsonify({'error': error_msg}), 400
            
    except Exception as e:
        logger.error(f'Chat error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat-with-image', methods=['POST'])
def chat_with_image():
    """Chat endpoint with image analysis"""
    if is_rate_limited(request.remote_addr):
        return jsonify({'error': 'Rate limit exceeded. Please wait a moment.'}), 429
    
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'image_data' not in data:
            return jsonify({'error': 'Message and image data are required'}), 400
        
        message = data['message']
        image_data = data['image_data']
        personality = data.get('personality', 'default')
        use_memory = data.get('use_memory', True)
        
        # Generate user ID if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # Initialize AI with image analysis
        try:
            from simple_openai import AdvancedOpenAI
            ai = AdvancedOpenAI()
            
            # Log API key status
            logger.info(f"AI initialized for image analysis, API key exists: {bool(ai.api_key)}")
            
            # Get AI response with image
            response = ai.call_openai_with_image(
                message=message,
                image_data=image_data,
                user_id=user_id,
                personality=personality,
                use_memory=use_memory
            )
            
            logger.info(f"AI image analysis response received: {response}")
            
        except ImportError as e:
            logger.error(f"Failed to import simple_openai: {e}")
            return jsonify({'error': 'AI module import failed'}), 500
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")
            return jsonify({'error': 'AI initialization failed'}), 500
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'response': response['response'],
                'personality': personality,
                'model_used': response.get('model_used', 'GPT-4o'),
                'provider': response.get('provider', 'openai'),
                'tokens_used': response.get('tokens_used', 0),
                'conversation_length': response.get('conversation_length', 0),
                'image_analyzed': True
            })
        else:
            error_msg = response.get('error', 'Unknown error occurred') if response else 'No response from AI'
            logger.error(f"AI image analysis error: {error_msg}")
            return jsonify({'error': error_msg}), 400
            
    except Exception as e:
        logger.error(f'Chat with image error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat-with-document', methods=['POST'])
def chat_with_document():
    """Chat endpoint with document analysis"""
    if is_rate_limited(request.remote_addr):
        return jsonify({'error': 'Rate limit exceeded. Please wait a moment.'}), 429
    
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'document_data' not in data:
            return jsonify({'error': 'Message and document data are required'}), 400
        
        message = data['message']
        document_data = data['document_data']
        document_name = data.get('document_name', 'Document')
        personality = data.get('personality', 'default')
        use_memory = data.get('use_memory', True)
        
        # Generate user ID if not exists
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # Initialize AI with document analysis
        try:
            from simple_openai import AdvancedOpenAI
            ai = AdvancedOpenAI()
            
            # Log API key status
            logger.info(f"AI initialized for document analysis, API key exists: {bool(ai.api_key)}")
            
            # Create enhanced message with document context
            enhanced_message = f"Document: {document_name}\n\nDocument Content:\n{document_data}\n\nUser Question: {message}"
            
            # Get AI response with document context
            response = ai.call_openai_advanced(
                message=enhanced_message,
                user_id=user_id,
                personality=personality,
                use_memory=use_memory
            )
            
            logger.info(f"AI document analysis response received: {response}")
            
        except ImportError as e:
            logger.error(f"Failed to import simple_openai: {e}")
            return jsonify({'error': 'AI module import failed'}), 500
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")
            return jsonify({'error': 'AI initialization failed'}), 500
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'response': response['response'],
                'personality': personality,
                'model_used': response.get('model_used', 'GPT-4o'),
                'provider': response.get('provider', 'openai'),
                'tokens_used': response.get('tokens_used', 0),
                'conversation_length': response.get('conversation_length', 0),
                'document_analyzed': True,
                'document_name': document_name
            })
        else:
            error_msg = response.get('error', 'Unknown error occurred') if response else 'No response from AI'
            logger.error(f"AI document analysis error: {error_msg}")
            return jsonify({'error': error_msg}), 400
            
    except Exception as e:
        logger.error(f'Chat with document error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

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
