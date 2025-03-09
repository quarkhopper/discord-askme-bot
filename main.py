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
    help_text += "`!clear` - Clears up to 100 recent messages.\n"
    help_text += "`!match [text]` - Finds a message that matches a partial string and its position in history.\n"
    help_text += "`!clearafter [text]` - Clears all messages after a matched message.\n"
    await ctx.send(help_text)

# Define a command to clear up to 100 recent messages
@bot.command()
async def clear(ctx, limit: int = 100):
    """Clears up to 100 recent messages."""
    if is_forbidden_channel(ctx):
        return
    
    try:
        deleted = await ctx.channel.purge(limit=min(limit, 100))
        await ctx.send(f"✅ Cleared {len(deleted)} messages.", delete_after=3)
    except Exception as e:
        logging.error(f"Error clearing messages: {e}")
        await ctx.send("An error occurred while clearing messages.")

# Define a command to find a message matching a partial string and its position
@bot.command()
async def match(ctx, *, text: str):
    """Finds a message that matches a partial string and reports how many messages back it is, excluding the command message."""
    if is_forbidden_channel(ctx):
        return
    
    try:
        count = -1  # Start at -1 to ignore the command message itself
        async for message in ctx.channel.history(limit=100):
            if message.id == ctx.message.id:
                continue  # Skip the command message
            count += 1
            if text in message.content:
                await ctx.send(f"🔎 Found message {count} messages ago: `{message.content}` (by {message.author.display_name})")
                return count  # Return the message count for reuse
        
        await ctx.send("❌ No messages found containing the specified text.")
        return None
    except Exception as e:
        logging.error(f"Error finding message: {e}")
        await ctx.send("An error occurred while searching for messages.")
        return None

# Define a command to clear messages after a matched message
@bot.command()
async def clearafter(ctx, *, text: str):  # Now clears one extra message back
    """Clears all messages after a matched message using the logic from match and clear."""
    if is_forbidden_channel(ctx):
        return
    
    try:
        count = -1  # Start at -1 to ignore the command message itself
        async for message in ctx.channel.history(limit=100):
            if message.id == ctx.message.id:
                continue  # Skip the command message
            count += 1
            if text in message.content:
                break  # Stop at the first match
        
        if count == -1:
            await ctx.send("❌ No messages found containing the specified text.")
            return
        
        deleted = await ctx.channel.purge(limit=count + 1)
        await ctx.send(f"✅ Cleared {len(deleted)} messages after `{text}`.", delete_after=3)
    except Exception as e:
        logging.error(f"Error clearing messages after match: {e}")
        await ctx.send("An error occurred while clearing messages.")

# Start the Discord bot
def run_bot():
    logging.info("Starting Discord bot...")
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    run_bot()
