import discord
from discord.ext import commands
import datetime
import config  # Logging and settings
from commands.bot_errors import BotErrors  # Error handling

class TimeNow(commands.Cog):
    """Cog for generating a Discord time tag for the current time."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def rightnow(self, ctx):
        """Generates a Discord time tag for the current UTC time.

        **Usage:**
        `!rightnow` → Creates a timestamp for the exact moment it was executed.

        **Output:**  
        🕒 Your time tag: `<t:1713181800:F>` (Copy and paste this!)

        **Restrictions:**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response in the channel.**
        """

        # ✅ Get the current UTC timestamp
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp = int(now.timestamp())

        # ✅ Generate the Discord-friendly time tag
        discord_time_tag = f"`<t:{timestamp}:F>`"

        message = (
            f"🕒 **Here’s your time tag:** {discord_time_tag}\n"
            f"📋 Copy and paste this anywhere in Discord to show the correct local time for each user."
        )

        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(TimeNow(bot))
