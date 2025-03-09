from discord.ext import commands
import config as config  # Import shared config

def setup(bot):
    # Define a command to clear messages after a matched message
    @bot.command()
    async def clearafter(ctx, *, text: str):  # Now clears one extra message back
        """Clears all messages after a matched message using the logic from match and clear."""
        if config.is_forbidden_channel(ctx):
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
            config.logging.error(f"Error clearing messages after match: {e}")
            await ctx.send("An error occurred while clearing messages.")