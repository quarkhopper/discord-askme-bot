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

# Define the channel restriction
FORBIDDEN_CHANNELS = ["general"]  # List of restricted channel names

# Log when bot is ready
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# Helper function to check if the command is in a forbidden channel
def is_forbidden_channel(ctx):
    return ctx.channel.name in FORBIDDEN_CHANNELS

# Define the help command
@bot.command(name="commands")
async def commands(ctx):
    """Displays a list of available commands."""
    if is_forbidden_channel(ctx):
        return
    
    help_text = "**Available Commands:**\n"
    help_text += "`!commands` - Displays this help message.\n"
    help_text += "`!chat [message]` - Talk to the bot and get AI-generated responses.\n"
    help_text += "`!image [prompt]` - Generate an image using OpenAI's DALL·E API.\n"
    help_text += "`!mood [@user]` - Analyze the mood of a user or the last 10 messages.\n"
    help_text += "`!clearafter [text]` - Deletes all messages after a given text (up to 100 messages).\n"
    await ctx.send(help_text)

# Define a command for text interaction with OpenAI
@bot.command()
async def chat(ctx, *, message: str):
    """A simple command to interact with OpenAI"""
    if is_forbidden_channel(ctx):
        return
    
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
    if is_forbidden_channel(ctx):
        return
    
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
async def mood(ctx, user: discord.Member = None):
    """Analyze the mood of a specific user or the last 10 messages in general."""
    if is_forbidden_channel(ctx):
        return
    
    try:
        messages = []
        limit = 10  # Always fetch 10 messages
        
        async for message in ctx.channel.history(limit=100):  # Search up to 100 messages to find 10 from the user
            if user is None or message.author == user or message.author.name == user.name:
                messages.append(f"{message.author.display_name}: {message.content}")
                if len(messages) >= 10:
                    break

        if not messages:
            await ctx.send("No messages found for the specified user.")
            return

        # Create a prompt for emotion analysis
        prompt = (
            "Analyze the emotions in this conversation and suggest how the participant might be feeling:\n\n" +
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

# Define a command to clear messages after a given partial string
@bot.command()
async def clearafter(ctx, *, text: str):
    """Deletes all messages after the given partial string (up to 100 messages)."""
    if is_forbidden_channel(ctx):
        return
    
    try:
        target_message = None
        async for message in ctx.channel.history(limit=100):
            if text in message.content:
                target_message = message
                break

        if not target_message:
            await ctx.send("❌ No messages found containing the specified text.")
            return

        messages_after = [m async for m in ctx.channel.history(limit=100) if m.created_at > target_message.created_at]
        
        if messages_after:
            await ctx.channel.delete_messages(messages_after[:min(len(messages_after), 99)])
            await ctx.send(f"✅ Deleted {len(messages_after[:99])} messages after the specified text.")
        else:
            await ctx.send("❌ No messages to delete after the specified text.")
    except Exception as e:
        logging.error(f"Error clearing messages: {e}")
        await ctx.send("An error occurred while clearing messages.")

# Start the Discord bot
def run_bot():
    logging.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
