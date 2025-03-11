import discord
from discord.ext import commands
import json
import pytz
import config  # Ensure logging and necessary settings
from commands.bot_errors import BotErrors  # Error handling

TIMEZONE_FILE = "timezones.json"  # File to store user time zones

class TimezoneManager(commands.Cog):
    """Cog for managing user time zones and displaying local times."""

    def __init__(self, bot):
        self.bot = bot
        self.timezones = self.load_timezones()

    def load_timezones(self):
        """Loads stored time zones from a JSON file."""
        try:
            with open(TIMEZONE_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}  # Return empty dictionary if file does not exist or is corrupt

    def save_timezones(self):
        """Saves the current time zones to a JSON file."""
        with open(TIMEZONE_FILE, "w") as f:
            json.dump(self.timezones, f, indent=4)

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def settimezone(self, ctx, timezone: str):
        """Sets a user's time zone.

        **Usage:**
        `!settimezone [timezone]` → Registers your preferred time zone.

        **Example:**
        `!settimezone America/New_York`

        **Restrictions:**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends confirmation via DM.**
        """

        # ✅ Validate the time zone
        if timezone not in pytz.all_timezones:
            await ctx.send("❌ Invalid time zone. Please provide a valid time zone from the IANA database (e.g., `America/New_York`).")
            return

        # ✅ Store the time zone
        self.timezones[str(ctx.author.id)] = timezone
        self.save_timezones()

        # ✅ Confirm to the user via DM
        try:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
            await dm_channel.send(f"✅ Your time zone has been set to **{timezone}**.")
        except discord.Forbidden:
            await ctx.send(f"✅ Your time zone has been set to **{timezone}**.")

    @commands.command()
    @commands.check(lambda ctx: not isinstance(ctx.channel, discord.DMChannel))  # ✅ Prevent execution in DMs
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def timezones(self, ctx):
        """Displays the local time for each unique time zone registered by users.

        **Usage:**
        `!timezones` → Shows a list of unique time zones registered by users.

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

        # ✅ Get unique time zones from registered users
        timezones = {}
        for user_id, tz_name in self.timezones.items():
            if tz_name in pytz.all_timezones and tz_name not in timezones:
                local_time = pytz.timezone(tz_name).localize(datetime.now()).strftime("%Y-%m-%d %I:%M %p")
                timezones[tz_name] = local_time

        if not timezones:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("⚠️ No users have registered a time zone yet. Use `!settimezone [timezone]` to add yours.")
            except discord.Forbidden:
                await ctx.send("⚠️ No users have registered a time zone yet. Use `!settimezone [timezone]` to add yours.")
            return

        # ✅ Format the time zone output
        timezone_list = "\n".join(f"🕒 **{tz}** → {time}" for tz, time in sorted(timezones.items()))

        execution_feedback = (
            f"**Command Executed:** !timezones\n"
            f"**Channel:** {ctx.channel.name}\n"
            f"**Timestamp:** {ctx.message.created_at}\n\n"
            f"🌎 **Current Local Times for Registered Time Zones:**\n{timezone_list}"
        )

        # ✅ Send the output via DM
        try:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
            await dm_channel.send(execution_feedback)
        except discord.Forbidden:
            await ctx.send("❌ Could not send a DM. Please enable DMs from server members.")

async def setup(bot):
    await bot.add_cog(TimezoneManager(bot))
