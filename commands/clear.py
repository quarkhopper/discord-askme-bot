from discord.ext import commands
import config as config  # Import shared config

def setup(bot):
    # Define a command to clear messages with defaults and limits
    @bot.command()
    async def clear(ctx, limit: int = None):
        """Clears a specified number of recent messages (default: 1, max: 100)."""
        if config.is_forbidden_channel(ctx):
            return
        
        # Set default to 1 if not provided, and enforce a max limit of 100
        limit = 1 if limit is None else min(limit, 100)

        try:
            # Clear messages, making sure to remove the command message as well
            deleted = await ctx.channel.purge(limit=limit + 1)
            await ctx.send(f"✅ Cleared {len(deleted) - 1} messages.", delete_after=3)
        except Exception as e:
            config.logging.error(f"Error clearing messages: {e}")
            await ctx.send("An error occurred while clearing messages.")
