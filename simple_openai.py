#!/usr/bin/env python3
"""
Advanced OpenAI Module - Enhanced AI features with GPT-4o (latest), system prompts, conversation memory, and real-time information
"""

import os
import requests
import json
import time
from datetime import datetime
from collections import defaultdict
import uuid

class RealTimeInfo:
    """Real-time information service integration"""
    
    def __init__(self):
        self.weather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.crypto_api_key = os.environ.get('CRYPTO_API_KEY')
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.stocks_api_key = os.environ.get('STOCKS_API_KEY')
    
    def get_weather(self, city="New York"):
        """Get current weather for a city"""
        if not self.weather_api_key:
            return f"Weather data unavailable (API key not configured)"
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                return f"Current weather in {city}: {temp}°C, {description}, Humidity: {humidity}%"
            else:
                return f"Weather data unavailable for {city}"
        except Exception as e:
            return f"Weather data unavailable: {str(e)}"
    
    def get_time(self, timezone="UTC"):
        """Get current time for a timezone"""
        try:
            from datetime import datetime, timezone
            import pytz
            
            if timezone == "UTC":
                utc_time = datetime.now(timezone.utc)
                return f"Current UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                tz = pytz.timezone(timezone)
                local_time = datetime.now(tz)
                return f"Current time in {timezone}: {local_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except ImportError:
            utc_time = datetime.utcnow()
            return f"Current UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception as e:
            return f"Time data unavailable: {str(e)}"
    
    def get_crypto_price(self, symbol="BTC"):
        """Get current cryptocurrency price"""
        if not self.crypto_api_key:
            return f"Crypto data unavailable (API key not configured)"
        
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if symbol.lower() in data:
                    price = data[symbol.lower()]['usd']
                    return f"Current {symbol.upper()} price: ${price:,.2f} USD"
                else:
                    return f"Price data unavailable for {symbol.upper()}"
            else:
                return f"Crypto data unavailable for {symbol.upper()}"
        except Exception as e:
            return f"Crypto data unavailable: {str(e)}"
    
    def get_news(self, topic="technology", limit=3):
        """Get latest news on a topic"""
        if not self.news_api_key:
            return f"News data unavailable (API key not configured)"
        
        try:
            url = f"https://newsapi.org/v2/top-headlines?q={topic}&apiKey={self.news_api_key}&pageSize={limit}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                if articles:
                    news_summary = f"Latest {topic} news:\n"
                    for i, article in enumerate(articles[:limit], 1):
                        title = article.get('title', 'No title')
                        news_summary += f"{i}. {title}\n"
                    return news_summary.strip()
                else:
                    return f"No recent news found for {topic}"
            else:
                return f"News data unavailable for {topic}"
        except Exception as e:
            return f"News data unavailable: {str(e)}"
    
    def get_stock_price(self, symbol="AAPL"):
        """Get current stock price"""
        if not self.stocks_api_key:
            return f"Stock data unavailable (API key not configured)"
        
        try:
            # Using Alpha Vantage API as an example
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.stocks_api_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                if quote:
                    price = quote.get('05. price', 'N/A')
                    change = quote.get('09. change', 'N/A')
                    change_percent = quote.get('10. change percent', 'N/A')
                    return f"Current {symbol} stock: ${price} (Change: {change}, {change_percent})"
                else:
                    return f"Stock data unavailable for {symbol}"
            else:
                return f"Stock data unavailable for {symbol}"
        except Exception as e:
            return f"Stock data unavailable: {str(e)}"

class AdvancedOpenAI:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.claude_api_key = os.environ.get('CLAUDE_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.conversation_history = {}
        self.real_time = RealTimeInfo()
        
        # Enhanced system prompts with real-time capabilities
        self.system_prompts = {
            'default': "You are a helpful, intelligent AI assistant with expertise in various fields. You can access real-time information like weather, time, news, and more. Provide detailed, accurate, and engaging responses.",
            'creative': "You are a creative and imaginative AI assistant. Think outside the box and provide innovative solutions and ideas. You can access real-time data to enhance your creative responses.",
            'professional': "You are a professional and formal AI assistant. Provide precise, well-structured, and business-appropriate responses. Use real-time information when relevant to business discussions.",
            'friendly': "You are a warm, friendly, and approachable AI assistant. Make users feel comfortable and engaged in conversation. Share real-time information in a friendly, helpful way.",
            'educational': "You are an educational AI assistant. Explain complex topics clearly, provide examples, and help users learn effectively. Use real-time information to make learning more relevant and current."
        }
        
        # Available AI models and providers
        self.available_models = {
            'openai': {
                'gpt-4o': {'name': 'GPT-4o', 'description': 'Latest and most capable model', 'max_tokens': 4096, 'cost_per_1k': 0.005},
                'gpt-4-turbo': {'name': 'GPT-4 Turbo', 'description': 'Fast and powerful', 'max_tokens': 4096, 'cost_per_1k': 0.01},
                'gpt-3.5-turbo': {'name': 'GPT-3.5 Turbo', 'description': 'Fast and cost-effective', 'max_tokens': 4096, 'cost_per_1k': 0.0005}
            },
            'claude': {
                'claude-3-5-sonnet': {'name': 'Claude 3.5 Sonnet', 'description': 'Anthropic\'s latest model', 'max_tokens': 4096, 'cost_per_1k': 0.003},
                'claude-3-haiku': {'name': 'Claude 3 Haiku', 'description': 'Fast and efficient', 'max_tokens': 4096, 'cost_per_1k': 0.00025}
            },
            'gemini': {
                'gemini-1.5-pro': {'name': 'Gemini 1.5 Pro', 'description': 'Google\'s latest AI model', 'max_tokens': 8192, 'cost_per_1k': 0.0025}
            }
        }
        
        self.default_model = "gpt-4o"  # Latest GPT-4 Turbo (GPT-4o)
        self.fallback_model = "gpt-4-turbo"  # Fallback to GPT-4 Turbo
        self.default_provider = "openai"
    
    def get_available_models(self):
        """Get list of available AI models with details"""
        return self.available_models
    
    def get_model_info(self, provider, model):
        """Get information about a specific model"""
        if provider in self.available_models and model in self.available_models[provider]:
            return self.available_models[provider][model]
        return None
    
    def call_ai_model(self, message, user_id="default", personality="default", 
                      max_tokens=1000, temperature=0.7, use_memory=True, 
                      provider="openai", model=None):
        """
        Call different AI models based on provider and model selection
        """
        if provider == "openai":
            return self.call_openai(message, user_id, personality, max_tokens, temperature, use_memory, model)
        elif provider == "claude":
            return self.call_claude(message, user_id, personality, max_tokens, temperature, use_memory, model)
        elif provider == "gemini":
            return self.call_gemini(message, user_id, personality, max_tokens, temperature, use_memory, model)
        else:
            return {"success": False, "error": f"Unsupported provider: {provider}"}
    
    def call_openai(self, message, user_id="default", personality="default", 
                    max_tokens=1000, temperature=0.7, use_memory=True, model=None):
        """
        OpenAI API call with enhanced real-time capabilities
        """
        try:
            if not self.api_key:
                return {"success": False, "error": "No OpenAI API key found"}
            
            # Use specified model or default
            if not model:
                model = self.default_model
            
            # Validate model
            if model not in self.available_models['openai']:
                model = self.default_model
            
            # Get system prompt based on personality
            system_prompt = self.system_prompts.get(personality, self.system_prompts['default'])
            
            # Add real-time information capabilities
            system_prompt += "\n\nYou can access real-time information. If users ask about current weather, time, news, crypto prices, or stock prices, you can provide this information. Use the following format for real-time data:\n- Weather: Ask for city name\n- Time: Ask for timezone (e.g., UTC, America/New_York)\n- News: Ask for topic (e.g., technology, sports)\n- Crypto: Ask for symbol (e.g., BTC, ETH)\n- Stocks: Ask for symbol (e.g., AAPL, GOOGL)"
            
            # Prepare messages array
            messages = [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            # Add conversation history if memory is enabled
            if use_memory:
                conversation = self.get_conversation_context(user_id)
                for msg in conversation[-10:]:  # Last 10 messages for context
                    if msg["role"] in ["user", "assistant"]:
                        messages.insert(-1, {"role": msg["role"], "content": msg["content"]})
            
            # Prepare API request
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Add to conversation history
                self.add_to_conversation(user_id, "user", message)
                self.add_to_conversation(user_id, "assistant", ai_response)
                
                return {
                    "success": True, 
                    "response": ai_response,
                    "model_used": model,
                    "provider": "openai",
                    "tokens_used": result['usage']['total_tokens'],
                    "conversation_length": len(self.get_conversation_context(user_id)),
                    "real_time_data": None
                }
            else:
                return {"success": False, "error": f"OpenAI API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def call_claude(self, message, user_id="default", personality="default", 
                    max_tokens=1000, temperature=0.7, use_memory=True, model=None):
        """
        Claude API call using Anthropic's API
        """
        try:
            if not self.claude_api_key:
                return {"success": False, "error": "No Claude API key found"}
            
            # Use specified model or default
            if not model:
                model = "claude-3-5-sonnet"
            
            # Validate model
            if model not in self.available_models['claude']:
                model = "claude-3-5-sonnet"
            
            # Get system prompt based on personality
            system_prompt = self.system_prompts.get(personality, self.system_prompts['default'])
            
            # Prepare messages array for Claude
            messages = [
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            # Add conversation history if memory is enabled
            if use_memory:
                conversation = self.get_conversation_context(user_id)
                for msg in conversation[-10:]:  # Last 10 messages for context
                    if msg["role"] in ["user", "assistant"]:
                        messages.insert(-1, {"role": msg["role"], "content": msg["content"]})
            
            # Prepare API request for Claude
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "system": system_prompt
            }
            
            headers = {
                "x-api-key": self.claude_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['content'][0]['text'].strip()
                
                # Add to conversation history
                self.add_to_conversation(user_id, "user", message)
                self.add_to_conversation(user_id, "assistant", ai_response)
                
                return {
                    "success": True, 
                    "response": ai_response,
                    "model_used": model,
                    "provider": "claude",
                    "tokens_used": result['usage']['input_tokens'] + result['usage']['output_tokens'],
                    "conversation_length": len(self.get_conversation_context(user_id)),
                    "real_time_data": None
                }
            else:
                return {"success": False, "error": f"Claude API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def call_gemini(self, message, user_id="default", personality="default", 
                     max_tokens=1000, temperature=0.7, use_memory=True, model=None):
        """
        Google Gemini API call
        """
        try:
            if not self.gemini_api_key:
                return {"success": False, "error": "No Gemini API key found"}
            
            # Use specified model or default
            if not model:
                model = "gemini-1.5-pro"
            
            # Validate model
            if model not in self.available_models['gemini']:
                model = "gemini-1.5-pro"
            
            # Get system prompt based on personality
            system_prompt = self.system_prompts.get(personality, self.system_prompts['default'])
            
            # Prepare content for Gemini
            content = [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nUser message: {message}"
                        }
                    ]
                }
            ]
            
            # Add conversation history if memory is enabled
            if use_memory:
                conversation = self.get_conversation_context(user_id)
                for msg in conversation[-10:]:  # Last 10 messages for context
                    if msg["role"] in ["user", "assistant"]:
                        content.append({
                            "parts": [
                                {
                                    "text": f"{msg['role'].title()}: {msg['content']}"
                                }
                            ]
                        })
            
            # Prepare API request for Gemini
            data = {
                "contents": content,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Add to conversation history
                self.add_to_conversation(user_id, "user", message)
                self.add_to_conversation(user_id, "assistant", ai_response)
                
                return {
                    "success": True, 
                    "response": ai_response,
                    "model_used": model,
                    "provider": "gemini",
                    "tokens_used": result['usageMetadata']['totalTokenCount'],
                    "conversation_length": len(self.get_conversation_context(user_id)),
                    "real_time_data": None
                }
            else:
                return {"success": False, "error": f"Gemini API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def call_openai_with_image(self, message, image_data, user_id="default", personality="default", 
                               max_tokens=1000, temperature=0.7, use_memory=True):
        """
        OpenAI API call with image analysis using GPT-4 Vision
        """
        try:
            if not self.api_key:
                return {"success": False, "error": "No API key found"}
            
            # Get system prompt based on personality
            system_prompt = self.system_prompts.get(personality, self.system_prompts['default'])
            system_prompt += "\n\nYou are now analyzing an image. Please provide detailed, accurate analysis of what you see in the image. Be specific about objects, people, text, colors, actions, and any other relevant details. If the user asks a specific question about the image, answer it thoroughly based on what you can observe."
            
            # Prepare messages array with image
            messages = [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ]
            
            # Add conversation history if memory is enabled
            if use_memory:
                conversation = self.get_conversation_context(user_id)
                for msg in conversation[-5:]:  # Last 5 messages for context (shorter for image analysis)
                    if msg["role"] in ["user", "assistant"]:
                        messages.insert(-1, {"role": msg["role"], "content": msg["content"]})
            
            # Use GPT-4o model (latest and best for images)
            data = {
                "model": "gpt-4o",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120  # Longer timeout for image analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Add to conversation history
                self.add_to_conversation(user_id, "user", f"[Image Analysis Request] {message}")
                self.add_to_conversation(user_id, "assistant", ai_response)
                
                return {
                    "success": True, 
                    "response": ai_response,
                    "model_used": "gpt-4o",
                    "provider": "openai",
                    "tokens_used": result['usage']['total_tokens'],
                    "conversation_length": len(self.get_conversation_context(user_id)),
                    "image_analyzed": True
                }
            else:
                return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_conversation_context(self, user_id):
        """Get conversation history for a user"""
        return self.conversation_history.get(user_id, [])
    
    def add_to_conversation(self, user_id, role, content):
        """Add a message to conversation history"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 messages to prevent memory issues
        if len(self.conversation_history[user_id]) > 50:
            self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
    
    def clear_conversation(self, user_id):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
    
    def get_real_time_info(self, query_type, **kwargs):
        """Get real-time information based on query type"""
        if query_type == "weather":
            city = kwargs.get('city', 'New York')
            return self.real_time.get_weather(city)
        elif query_type == "time":
            timezone = kwargs.get('timezone', 'UTC')
            return self.real_time.get_time(timezone)
        elif query_type == "crypto":
            symbol = kwargs.get('symbol', 'BTC')
            return self.real_time.get_crypto_price(symbol)
        elif query_type == "news":
            topic = kwargs.get('topic', 'technology')
            limit = kwargs.get('limit', 3)
            return self.real_time.get_news(topic, limit)
        elif query_type == "stocks":
            symbol = kwargs.get('symbol', 'AAPL')
            return self.real_time.get_stock_price(symbol)
        else:
            return f"Unknown query type: {query_type}"

# Backward compatibility function
def call_openai_direct(message, max_tokens=500, temperature=0.7):
    """Legacy function for backward compatibility"""
    ai = AdvancedOpenAI()
    return ai.call_openai_advanced(message, max_tokens=max_tokens, temperature=temperature)

if __name__ == "__main__":
    # Test the advanced features
    ai = AdvancedOpenAI()
    
    print("Testing Advanced OpenAI Features with Real-Time Information:")
    print("=" * 60)
    
    # Test different personalities
    personalities = ai.get_available_personalities()
    print(f"Available personalities: {personalities}")
    
    # Test real-time capabilities
    capabilities = ai.get_real_time_capabilities()
    print(f"\nReal-time capabilities: {list(capabilities.keys())}")
    
    # Test conversation memory
    result = ai.call_openai_advanced("Hello, what's your name?", user_id="test_user", personality="friendly")
    print(f"\nFirst response: {result}")
    
    result2 = ai.call_openai_advanced("Do you remember my name?", user_id="test_user", personality="friendly")
    print(f"\nSecond response: {result2}")
    
    # Test conversation context
    context = ai.get_conversation_context("test_user")
    print(f"\nConversation context: {len(context)} messages")
