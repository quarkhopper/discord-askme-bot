import discord
from discord.ext import commands
import pytz
from datetime import datetime
import config  # Ensure this contains logging and necessary settings
from commands.bot_errors import BotErrors  # Error handling

class Timezones(commands.Cog):
    """Cog for displaying local times for unique time zones of server members."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def not_in_dm(ctx):
        """Prevents the command from running in DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ The `!timezones` command can only be used in a server.")
            return False  # ✅ Prevents command execution
        return True

    @commands.command()
    @commands.check(not_in_dm)  # ✅ Ensure correct reference to static method
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def timezones(self, ctx):
        """Displays the local time for each distinct time zone in the server.

        **Usage:**
        `!timezones` → Shows a list of unique time zones where users are located, with the current time in each.

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response via DM.**
        """

        # ✅ Immediately delete the command message to avoid clutter
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass  # If message was already deleted, ignore

        # Check if command is in a forbidden channel
        if await BotErrors.check_forbidden_channel(ctx):
            return

        # Dictionary to store unique time zones
        timezones = {}

        # Iterate through server members to collect time zones
        for member in ctx.guild.members:
            if member.bot:
                continue  # Skip bots

            # Assuming users' time zones are stored in a custom attribute
            tz_name = getattr(member, "timezone", None)
            if tz_name and tz_name in pytz.all_timezones:
                if tz_name not in timezones:
                    timezones[tz_name] = datetime.now(pytz.timezone(tz_name)).strftime("%Y-%m-%d %I:%M %p")

        if not timezones:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("⚠️ No users in this server have a registered time zone.")
            except discord.Forbidden:
                await ctx.send("⚠️ No users in this server have a registered time zone.")
            return

        # Format the time zone output
        timezone_list = "\n".join(f"🕒 **{tz}** → {time}" for tz, time in sorted(timezones.items()))

        execution_feedback = (
            f"**Command Executed:** !timezones\n"
            f"**Channel:** {ctx.channel.name}\n"
            f"**Timestamp:** {ctx.message.created_at}\n\n"
            f"🌎 **Current Local Times for Unique Time Zones:**\n{timezone_list}"
        )

        # ✅ Send the output via DM
        try:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
            await dm_channel.send(execution_feedback)
        except discord.Forbidden:
            await ctx.send("❌ Could not send a DM. Please enable DMs from server members.")

async def setup(bot):
    await bot.add_cog(Timezones(bot))
