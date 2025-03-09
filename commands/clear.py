from discord.ext import commands
import config as config  # Import shared config

def setup(bot):
    # Define a command to clear up to 100 recent messages
    @bot.command()
    async def clear(ctx, limit: int = 100):
        """Clears up to 100 recent messages."""
        if config.is_forbidden_channel(ctx):
            return
        
        try:
            # modified to clear messages not counting the command also 
            deleted = await ctx.channel.purge(limit=min(limit + 1, 100))
            await ctx.send(f"✅ Cleared {len(deleted - 1)} messages.", delete_after=3)
        except Exception as e:
            config.logging.error(f"Error clearing messages: {e}")
            await ctx.send("An error occurred while clearing messages.")
