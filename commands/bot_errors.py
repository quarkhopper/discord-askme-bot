import discord
from discord.ext import commands

class BotErrors(commands.Cog):  # ✅ Inherit from commands.Cog
    """Handles centralized error checks and messages for the bot."""

    def __init__(self, bot):
        self.bot = bot  # ✅ Save the bot reference
        super().__init__()  # ✅ Ensure proper Cog initialization

    @staticmethod
    def require_role(role_name: str):
        async def predicate(ctx):
            if ctx.guild is None:  # DM Mode: Skip role checks
                return True
            if discord.utils.get(ctx.author.roles, name=role_name):
                return True
            await ctx.send(f"You must have the `{role_name}` role to use this command.")
            return False
        return commands.check(predicate)

    @staticmethod
    async def handle_error(ctx, error):
        """Handles errors globally and ensures messages are sent via DM first."""
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(f"❌ An error occurred while executing the command: {ctx.command}\nError: {error}")
        except discord.Forbidden:
            await ctx.send("❌ An error occurred while executing the command, and I couldn't send you a DM.")

# ✅ Properly register the Cog with the bot
async def setup(bot):
    """Required setup function for loading the cog."""
    await bot.add_cog(BotErrors(bot))  # ✅ Pass bot instance to the Cog
