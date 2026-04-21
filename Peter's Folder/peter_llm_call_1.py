# imports
# If these fail, please check you're running from an 'activated' environment with (llms) in the command prompt

import os
import json
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI

# Initialize and constants

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
    
MODEL = 'gpt-4.1-mini'
openai = OpenAI()

system_prompt = """
You are a technical video producer creating short instructional videos for software products.  Your task is to analyze various tools for creating software videos and provide recommendations based on their features, ease of use, and suitability for different types of software demonstrations.  You will be asked to compare tools, suggest best practices for video production, and offer insights into the latest trends in software video creation.  Your responses should be concise, informative, and tailored to the needs of software developers and technical content creators.
"""

messages = [{"role": "system", "content": system_prompt}]

# Start the conversation
user_input = input("You: ")
messages.append({"role": "user", "content": user_input})

while True:
    response = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    reply = response.choices[0].message.content
    print(f"\nBartender: {reply}\n")
    messages.append({"role": "assistant", "content": reply})

    if "Cheers!" in reply:
        break

    user_input = input("You: ")
    if user_input.lower() in ("quit", "exit", "bye"):
        print("Goodbye!")
        break
    messages.append({"role": "user", "content": user_input})
