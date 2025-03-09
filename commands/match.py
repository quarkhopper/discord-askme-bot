from discord.ext import commands
import config as config  # Import shared config

def setup(bot, openai_client):
    # Define a command to find a message matching a partial string and its position
    @bot.command()
    async def match(ctx, *, text: str):
        """Finds a message that matches a partial string and reports how many messages back it is, excluding the command message."""
        if config.is_forbidden_channel(ctx):
            return
        
        try:
            count = -1  # Start at -1 to ignore the command message itself
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue  # Skip the command message
                count += 1
                if text in message.content:
                    await ctx.send(f"🔎 Found message {count + 1} messages ago: `{message.content}` (by {message.author.display_name})")
                    return count  # Return the message count for reuse
            
            await ctx.send("❌ No messages found containing the specified text.")
            return None
        except Exception as e:
            config.logging.error(f"Error finding message: {e}")
            await ctx.send("An error occurred while searching for messages.")
            return None