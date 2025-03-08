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

# Define a command for mood analysis
@bot.command()
async def mood(ctx, user: discord.Member = None, limit: int = 10):
    """Analyze recent messages and suggest possible emotions for a specific user or the whole channel."""
    if limit > 100:
        limit = 100  # Ensure the limit does not exceed 100
    try:
        messages = []
        async for message in ctx.channel.history(limit=limit):
            if user is None or message.author == user:
                messages.append(f"{message.author.name}: {message.content}")

        if not messages:
            await ctx.send("No messages found for the specified user.")
            return

        # Create a prompt for emotion analysis
        prompt = (
            "Analyze the emotions in this conversation and suggest how the participants might be feeling:\n\n" +
            "\n".join(messages) +
            "\n\nGive a concise emotional summary."
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an AI that analyzes emotions in conversations."},
                      {"role": "user", "content": prompt}]
        )

        mood_analysis = response["choices"][0]["message"]["content"].strip()
        await ctx.send(f"💡 Mood Analysis: {mood_analysis}")

    except Exception as e:
        logging.error(f"Error analyzing mood: {e}")
        await ctx.send("An error occurred while analyzing the mood.")

# Start the Discord bot
def run_bot():
    logging.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
