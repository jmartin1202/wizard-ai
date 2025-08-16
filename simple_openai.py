#!/usr/bin/env python3
"""
Simple OpenAI Module - Direct API calls without complex imports
"""

import os
import requests
import json
from dotenv import load_dotenv

def call_openai_direct(message, max_tokens=500, temperature=0.7):
    """
    Call OpenAI API directly using requests (no openai package needed)
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return {"success": False, "error": "No API key found"}
        
        # Prepare the request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Make the API call
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            return {"success": True, "response": ai_response}
        else:
            return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test the function
    result = call_openai_direct("Hello, how are you?")
    print(json.dumps(result, indent=2))
