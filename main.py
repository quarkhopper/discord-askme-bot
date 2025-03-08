import discord
import openai
import os
from fastapi import FastAPI
from discord.ext import commands
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# FastAPI setup
app = FastAPI()

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Allows access to the content of messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Define a simple FastAPI route for health check
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Define a command for the Discord bot
@bot.command()
async def chat(ctx, *, message: str):
    """A simple command to interact with OpenAI"""
    response = openai.Completion.create(
        engine="text-davinci-003",  # Or whichever model you want to use
        prompt=message,
        max_tokens=150
    )
    await ctx.send(response.choices[0].text.strip())

# Start the Discord bot
def run_bot():
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    # Run bot in a separate thread to prevent blocking the FastAPI server
    threading.Thread(target=run_bot).start()
