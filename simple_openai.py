#!/usr/bin/env python3
"""
Advanced OpenAI Module - Enhanced AI features with GPT-4, system prompts, conversation memory, and real-time information
"""

import os
import requests
import json
from datetime import datetime
import hashlib
import time as time_module
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class RealTimeInfo:
    """Real-time information services"""
    
    def __init__(self):
        self.weather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.news_api_key = os.environ.get('NEWS_API_KEY')
    
    def get_current_time(self, timezone="UTC"):
        """Get current time for any timezone"""
        try:
            if timezone == "UTC":
                return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Use timezone API for other timezones
            response = requests.get(f"http://worldtimeapi.org/api/timezone/{timezone}")
            if response.status_code == 200:
                data = response.json()
                return data['datetime']
            else:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_weather(self, city="London"):
        """Get current weather for a city"""
        if not self.weather_api_key:
            return {"error": "Weather API key not configured"}
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                weather_info = {
                    "city": data['name'],
                    "country": data['sys']['country'],
                    "temperature": f"{data['main']['temp']}°C",
                    "feels_like": f"{data['main']['feels_like']}°C",
                    "humidity": f"{data['main']['humidity']}%",
                    "description": data['weather'][0]['description'],
                    "wind_speed": f"{data['wind']['speed']} m/s",
                    "timestamp": datetime.fromtimestamp(data['dt']).strftime("%H:%M:%S")
                }
                return weather_info
            else:
                return {"error": f"Weather data not available for {city}"}
        except Exception as e:
            return {"error": f"Weather service error: {str(e)}"}
    
    def get_crypto_price(self, coin="bitcoin"):
        """Get current cryptocurrency price"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if coin in data:
                    return {
                        "coin": coin.title(),
                        "usd": f"${data[coin]['usd']:,.2f}",
                        "eur": f"€{data[coin]['eur']:,.2f}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                else:
                    return {"error": f"Price not available for {coin}"}
            else:
                return {"error": "Crypto price service unavailable"}
        except Exception as e:
            return {"error": f"Crypto service error: {str(e)}"}
    
    def get_news_headlines(self, category="general", country="us"):
        """Get latest news headlines"""
        if not self.news_api_key:
            return {"error": "News API key not configured"}
        
        try:
            url = f"https://newsapi.org/v2/top-headlines?country={country}&category={category}&apiKey={self.news_api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])[:5]  # Top 5 headlines
                
                headlines = []
                for article in articles:
                    headlines.append({
                        "title": article['title'],
                        "source": article['source']['name'],
                        "published": article['publishedAt'][:10]  # Just the date
                    })
                
                return {
                    "category": category.title(),
                    "country": country.upper(),
                    "headlines": headlines,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
            else:
                return {"error": "News service unavailable"}
        except Exception as e:
            return {"error": f"News service error: {str(e)}"}
    
    def get_stock_price(self, symbol="AAPL"):
        """Get current stock price (using free API)"""
        try:
            # Using Alpha Vantage free tier (limited requests)
            api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                return {"error": "Stock API key not configured"}
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    return {
                        "symbol": symbol.upper(),
                        "price": f"${float(quote.get('05. price', 0)):.2f}",
                        "change": f"${float(quote.get('09. change', 0)):.2f}",
                        "change_percent": quote.get('10. change percent', '0%'),
                        "volume": quote.get('06. volume', '0'),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                else:
                    return {"error": f"Stock data not available for {symbol}"}
            else:
                return {"error": "Stock service unavailable"}
        except Exception as e:
            return {"error": f"Stock service error: {str(e)}"}

class AdvancedOpenAI:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
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
        self.default_model = "gpt-4"  # Upgrade to GPT-4
        self.fallback_model = "gpt-3.5-turbo"  # Fallback if GPT-4 unavailable
    
    def get_conversation_key(self, user_id):
        """Generate a unique conversation key for each user"""
        return hashlib.md5(f"{user_id}_{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()
    
    def add_to_conversation(self, user_id, role, content):
        """Add message to conversation history"""
        conv_key = self.get_conversation_key(user_id)
        if conv_key not in self.conversation_history:
            self.conversation_history[conv_key] = []
        
        # Keep only last 20 messages to manage memory
        if len(self.conversation_history[conv_key]) >= 20:
            self.conversation_history[conv_key] = self.conversation_history[conv_key][-19:]
        
        self.conversation_history[conv_key].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation_context(self, user_id):
        """Get conversation context for the user"""
        conv_key = self.get_conversation_key(user_id)
        return self.conversation_history.get(conv_key, [])
    
    def get_real_time_info(self, query):
        """Get real-time information based on user query"""
        query_lower = query.lower()
        
        # Weather queries - expanded detection
        if any(word in query_lower for word in ['weather', 'temperature', 'forecast', 'climate', 'hot', 'cold', 'rain', 'sunny', 'cloudy']):
            # Extract city name from query
            cities = ['London', 'New York', 'Tokyo', 'Paris', 'Sydney', 'Toronto', 'Berlin', 'Moscow', 'Los Angeles', 'Chicago', 'Miami', 'Seattle']
            for city in cities:
                if city.lower() in query_lower:
                    weather_data = self.real_time.get_weather(city)
                    if 'error' in weather_data:
                        # Provide fallback when API key is missing
                        return {
                            "city": city,
                            "country": "Unknown",
                            "temperature": "Data unavailable",
                            "feels_like": "Data unavailable", 
                            "humidity": "Data unavailable",
                            "description": "Weather data requires API key",
                            "wind_speed": "Data unavailable",
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "note": "OpenWeatherMap API key needed for live data"
                        }
                    return weather_data
            # Check for generic weather questions
            if any(word in query_lower for word in ['today', 'now', 'current', 'like']):
                weather_data = self.real_time.get_weather()
                if 'error' in weather_data:
                    return {
                        "city": "London",
                        "country": "UK", 
                        "temperature": "Data unavailable",
                        "feels_like": "Data unavailable",
                        "humidity": "Data unavailable", 
                        "description": "Weather data requires API key",
                        "wind_speed": "Data unavailable",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "note": "OpenWeatherMap API key needed for live data"
                    }
                return weather_data
            return self.real_time.get_weather()
        
        # Time queries - expanded detection
        elif any(word in query_lower for word in ['time', 'clock', 'hour', 'date', 'current time', 'what time', 'now']):
            if 'utc' in query_lower:
                return {"time": self.real_time.get_current_time("UTC"), "timezone": "UTC"}
            elif 'new york' in query_lower or 'est' in query_lower or 'eastern' in query_lower:
                return {"time": self.real_time.get_current_time("America/New_York"), "timezone": "EST"}
            elif 'london' in query_lower or 'gmt' in query_lower or 'british' in query_lower:
                return {"time": self.real_time.get_current_time("Europe/London"), "timezone": "GMT"}
            elif 'tokyo' in query_lower or 'japan' in query_lower or 'jst' in query_lower:
                return {"time": self.real_time.get_current_time("Asia/Tokyo"), "timezone": "JST"}
            elif 'paris' in query_lower or 'france' in query_lower or 'cet' in query_lower:
                return {"time": self.real_time.get_current_time("Europe/Paris"), "timezone": "CET"}
            else:
                return {"time": self.real_time.get_current_time(), "timezone": "Local"}
        
        # Crypto queries
        elif any(word in query_lower for word in ['bitcoin', 'crypto', 'cryptocurrency', 'eth', 'ethereum']):
            if 'bitcoin' in query_lower or 'btc' in query_lower:
                return self.real_time.get_crypto_price("bitcoin")
            elif 'ethereum' in query_lower or 'eth' in query_lower:
                return self.real_time.get_crypto_price("ethereum")
            else:
                return self.real_time.get_crypto_price("bitcoin")
        
        # News queries
        elif any(word in query_lower for word in ['news', 'headlines', 'latest', 'breaking']):
            if 'business' in query_lower:
                return self.real_time.get_news_headlines("business")
            elif 'technology' in query_lower or 'tech' in query_lower:
                return self.real_time.get_news_headlines("technology")
            elif 'sports' in query_lower:
                return self.real_time.get_news_headlines("sports")
            else:
                return self.real_time.get_news_headlines()
        
        # Stock queries
        elif any(word in query_lower for word in ['stock', 'market', 'price', 'trading']):
            stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
            for stock in stocks:
                if stock.lower() in query_lower:
                    return self.real_time.get_stock_price(stock)
            return self.real_time.get_stock_price("AAPL")  # Default to Apple
        
        return None
    
    def call_openai_advanced(self, message, user_id="default", personality="default", 
                            max_tokens=1000, temperature=0.7, use_memory=True):
        """
        Advanced OpenAI API call with conversation memory, system prompts, and real-time information
        """
        try:
            if not self.api_key:
                return {"success": False, "error": "No API key found"}
            
            # Check for real-time information requests
            real_time_data = self.get_real_time_info(message)
            
            # Get system prompt based on personality
            system_prompt = self.system_prompts.get(personality, self.system_prompts['default'])
            
            # Enhance system prompt with real-time capabilities
            if real_time_data:
                system_prompt += f"\n\nIMPORTANT: Real-time information is available for this query: {json.dumps(real_time_data, indent=2)}"
                system_prompt += "\n\nYou MUST use this real-time data to answer the user's question. Do NOT say you don't have access to real-time information."
                system_prompt += "\n\nIf the user asks about weather, time, crypto prices, news, or stocks, use the provided real-time data to give them current, accurate information."
                system_prompt += "\n\nAlways acknowledge that you're providing real-time data and include the timestamp when relevant."
            else:
                system_prompt += "\n\nYou have access to real-time information services for weather, time, crypto prices, news, and stocks."
                system_prompt += "\n\nIf a user asks about current conditions, prices, or time, you can access live data to provide accurate, up-to-date information."
            
            # Prepare messages array
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if memory is enabled
            if use_memory:
                conversation = self.get_conversation_context(user_id)
                for msg in conversation[-10:]:  # Last 10 messages for context
                    if msg["role"] in ["user", "assistant"]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Try GPT-4 first, fallback to GPT-3.5-turbo
            models_to_try = [self.default_model, self.fallback_model]
            
            for model in models_to_try:
                try:
                    data = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "presence_penalty": 0.1,  # Encourage diverse responses
                        "frequency_penalty": 0.1   # Reduce repetition
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=60  # Increased timeout for longer responses
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
                            "tokens_used": result['usage']['total_tokens'],
                            "conversation_length": len(self.get_conversation_context(user_id)),
                            "real_time_data": real_time_data
                        }
                    else:
                        if model == self.fallback_model:  # If both models fail
                            return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
                        continue  # Try next model
                        
                except requests.exceptions.Timeout:
                    if model == self.fallback_model:
                        return {"success": False, "error": "Request timeout"}
                    continue
                except Exception as e:
                    if model == self.fallback_model:
                        return {"success": False, "error": str(e)}
                    continue
            
            return {"success": False, "error": "All models failed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def change_personality(self, personality):
        """Change the AI personality"""
        if personality in self.system_prompts:
            return {"success": True, "personality": personality}
        else:
            return {"success": False, "error": "Invalid personality"}
    
    def get_available_personalities(self):
        """Get list of available AI personalities"""
        return list(self.system_prompts.keys())
    
    def clear_conversation(self, user_id):
        """Clear conversation history for a user"""
        conv_key = self.get_conversation_key(user_id)
        if conv_key in self.conversation_history:
            del self.conversation_history[conv_key]
        return {"success": True, "message": "Conversation cleared"}
    
    def get_real_time_capabilities(self):
        """Get list of available real-time information services"""
        return {
            "weather": "Current weather for cities worldwide",
            "time": "Current time in various timezones",
            "crypto": "Live cryptocurrency prices",
            "news": "Latest news headlines",
            "stocks": "Real-time stock market data"
        }

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
