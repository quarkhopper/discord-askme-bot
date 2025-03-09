import discord
from discord.ext import commands
import config  # Import shared config
from commands.bot_errors import BotErrors  # Import the error handler

class MessageUtils(commands.Cog):
    """Cog for message management commands (clear, match, clearafter)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def clear(self, ctx, limit: int = None):
        """Clears a specified number of recent messages (default: 1, max: 100)."""
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        limit = 1 if limit is None else min(limit, 100)

        try:
            deleted = await ctx.channel.purge(limit=limit + 1)
            await ctx.send(f"✅ Cleared {len(deleted) - 1} messages.", delete_after=3)
        except Exception as e:
            config.logger.error(f"Error clearing messages: {e}")
            await ctx.send("An error occurred while clearing messages.")

    @commands.command()
    async def match(self, ctx, *, text: str):
        """Finds a message that matches a partial string and reports its position in history."""
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        try:
            count = -1
            async for message in ctx.channel.history(limit=100):
                if message.id == ctx.message.id:
                    continue  
                count += 1
                if text in message.content:
                    await ctx.send(f"🔎 Found message {count + 1} messages ago: `{message.content}` (by {message.author.display_name})")
                    return count  
            
            await ctx.send("❌ No messages found containing the specified text.")
            return None
        except Exception as e:
            config.logger.error(f"Error finding message: {e}")
            await ctx.send("An error occurred while searching for messages.")
            return None

    @commands.command()
    async def clearafter(self, ctx, *, text: str):
        """Clears all messages after a matched message using the logic from match and clear."""
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        try:
            count = await self.match(ctx, text=text)  # Call match command within Cog
            if count is None:
                return  

            deleted = await ctx.channel.purge(limit=count + 2)  # Deletes messages *after* the match
            await ctx.send(f"✅ Cleared {len(deleted)} messages after `{text}`.", delete_after=3)
        except Exception as e:
            config.logger.error(f"Error clearing messages after match: {e}")
            await ctx.send("An error occurred while clearing messages.")


async def setup(bot):
    await bot.add_cog(MessageUtils(bot))
