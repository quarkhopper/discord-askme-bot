import discord
from discord.ext import commands
import openai
import os
from datetime import datetime, timedelta
from commands.bot_errors import BotErrors  # Import the error handler
from commands.command_utils import command_mode

class Guide(commands.Cog):
    """Cog for providing a focused and concise server guide."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @command_mode("server")
    async def guide(self, ctx):
        """Provides a brief summary of the 5 most active channels, based on recent activity.
        
        **Note:** This command **only works in servers** and results are sent via DM.
        """

        # Prevent command execution in DMs
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Enforce role restrictions and forbidden channel checks
        if not BotErrors.require_role("Vetted")(ctx):
            return
        if await BotErrors.check_forbidden_channel(ctx):
            return

        # Attempt to send the execution header via DM
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!guide`\n"
                f"📍 **Server:** {ctx.guild.name}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )
            await ctx.message.delete()  # Delete command message after DM is sent
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return  # Stop execution if DM cannot be sent

        time_threshold = datetime.utcnow() - timedelta(days=1)
        channel_activity = {}

        # Gather channel activity data
        for channel in ctx.guild.text_channels:
            try:
                unique_users = set()
                latest_message_time = None
                async for message in channel.history(limit=50):
                    if not message.author.bot:
                        unique_users.add(message.author.id)
                        latest_message_time = message.created_at

                if latest_message_time:
                    channel_activity[channel] = {
                        "last_message": latest_message_time,
                        "unique_posters": len(unique_users),
                    }

            except discord.Forbidden:
                continue  # Skip channels the bot lacks permissions for

        # Sort channels by recent activity
        most_active_channels = sorted(
            channel_activity.items(),
            key=lambda item: (item[1]["last_message"], item[1]["unique_posters"]),
            reverse=True
        )[:5]  # Get top 5 most active channels

        if not most_active_channels:
            await dm_channel.send("No active channels found in the last 24 hours.")
            return

        guide_message = "**Here are the 5 most active channels!** 🔥\n\n"
        summaries = []

        for channel, activity in most_active_channels:
            channel_summary = channel.topic if channel.topic else f"A space for discussions related to {channel.name.replace('-', ' ')}."

            # Fetch recent messages for summarization
            messages = []
            async for message in channel.history(limit=30):
                if not message.author.bot:
                    messages.append(f"{message.author.name}: {message.content}")

            if messages:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following recent Discord messages in 1-2 sentences."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                recent_activity = response.choices[0].message.content
            else:
                recent_activity = "No recent discussions."

            summaries.append(f"**#{channel.name}**\n📌 {channel_summary}\n🔍 *Lately, users have been discussing:* {recent_activity}\n")

        guide_message += "\n".join(summaries)

        # Split message if needed (Discord max length = 2000 characters)
        max_length = 2000
        parts = [guide_message[i:i + max_length] for i in range(0, len(guide_message), max_length)]

        for part in parts:
            await dm_channel.send(part)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Sends a fun but informative DM to new members, introducing the bot and explaining server expectations."""
        welcome_message = (
            f"**Beep boop! 🤖 Welcome, {member.name}, to {member.guild.name}!** 🎉\n\n"
            "I am your friendly server bot, here to help (and definitely not plotting world domination 🤫).\n\n"
            "To get started, you need to **check in and get the 'Vetted' role** before you can use bot commands.\n\n"
            "**Here’s a quick overview of key channels:**\n"
        )

        for channel in member.guild.text_channels[:5]:  # Limit DM to first 5 channels
            topic = channel.topic if channel.topic else f"A channel for discussions related to {channel.name.replace('-', ' ')}."
            welcome_message += f"**#{channel.name}** - {topic}\n"

        welcome_message += (
            "\n🔹 **First Steps:**\n"
            "✔️ Check in and get the 'Vetted' role.\n"
            "✔️ Say hi in **#general** and get to know the community!\n\n"
            "Enjoy your stay, and remember—I’m always watching. 👀 (Just kidding… or am I? 😏)"
        )

        try:
            await member.send(welcome_message)
        except discord.Forbidden:
            print(f"Could not send a DM to {member.name}.")


async def setup(bot):
    await bot.add_cog(Guide(bot))
