import discord
import openai
import os
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True  # Allows access to the content of messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Log when bot is ready
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# Define a command for text interaction with OpenAI
@bot.command()
async def chat(ctx, *, message: str):
    """A simple command to interact with OpenAI"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or another model you want to use
            messages=[{"role": "user", "content": message}],
        )
        await ctx.send(response['choices'][0]['message']['content'].strip())
    except Exception as e:
        logging.error(f"Error interacting with OpenAI: {e}")
        await ctx.send("An error occurred while processing your request.")

# Define a command for image generation
@bot.command()
async def image(ctx, *, prompt: str):
    """Generate an image using OpenAI's DALL·E API"""
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response["data"][0]["url"]
        await ctx.send(image_url)
    except Exception as e:
        logging.error(f"Error generating image: {e}")
        await ctx.send("An error occurred while generating the image.")

# Start the Discord bot
def run_bot():
    logging.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
