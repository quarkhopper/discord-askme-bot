from fastapi import FastAPI
import openai
import discord
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI()

# Your OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Discord bot setup
client = discord.Client()

# Define your Discord bot commands or event handlers here
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
