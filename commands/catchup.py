import discord
from discord.ext import commands
import openai
import config
import os
import datetime
from collections import defaultdict
from commands.bot_errors import BotErrors  # Import the error handler

class Catchup(commands.Cog):
    """Cog for summarizing recent events across selected channels."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def eligible_channels(self, guild):
        """Returns a list of channels that have a pinned "+catchup" message."""
        eligible = []
        for channel in guild.text_channels:
            try:
                async for message in channel.pins():
                    if message.content.strip() == "+catchup":
                        eligible.append(channel)
                        break
            except discord.Forbidden:
                continue  # Ignore channels where the bot lacks permissions
        return eligible

    @commands.command()
    @BotErrors.require_role("Vetted")  # Restrict to users with "Vetted" role
    async def catchup(self, ctx, channel: discord.TextChannel = None):
        """Summarizes activity within eligible channels or a specified channel.
        
        Usage:
        `!catchup` → Summarizes recent discussions across eligible channels.
        `!catchup #channel` → Summarizes discussions in the specified channel.
        """

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        # Attempt to send the execution header via DM
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(
                f"📌 **Command Executed:** `!catchup`\n"
                f"📍 **Channel:** {channel.mention if channel else 'Eligible Channels'}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")
            return

        time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

        if channel:
            eligible = await self.eligible_channels(ctx.guild)
            if channel not in eligible:
                await dm_channel.send(f"⚠️ {channel.mention} is not an eligible channel for `!catchup`. ")
                return

            messages = []
            try:
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(message.content)
            except discord.Forbidden:
                await dm_channel.send(f"I don’t have permission to read {channel.mention}.")
                return

            if not messages:
                await dm_channel.send(f"No recent discussions found in {channel.mention}.")
                return

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following messages by topic."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await dm_channel.send(f"Here's what's been happening in {channel.mention}:\n\n{summary}")
            except Exception as e:
                await dm_channel.send(f"Error generating summary: {e}")
        else:
            eligible_channels = await self.eligible_channels(ctx.guild)
            user_messages = defaultdict(lambda: {"medical": [], "distress": [], "stress": [], "positive": []})

            for ch in eligible_channels:
                try:
                    async for message in ch.history(after=time_threshold, limit=100):
                        if message.author.bot:
                            continue  
                        user_messages[message.author.display_name]["general"].append(message.content)
                except discord.Forbidden:
                    continue  

            if not user_messages:
                await dm_channel.send("No significant messages in the past 24 hours.")
                return

            formatted_messages = []
            for user, categories in user_messages.items():
                for category, messages in categories.items():
                    if messages:
                        formatted_messages.append(f"{user}: {messages[0]}")
            
            token_limit = 12000  
            while sum(len(msg.split()) for msg in formatted_messages) > token_limit and len(formatted_messages) > 1:
                formatted_messages.pop(0)

            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": 
                            "Summarize the following Discord messages in a structured format with **four distinct categories**: \n"
                            "1) **Medical emergencies, crises, or major loss** – Prioritized first. \n"
                            "2) **Deep emotional distress, relapses, or mental health struggles** – Urgent emotional challenges. \n"
                            "3) **General stressors** – Minor frustrations, work stress, sleep issues. \n"
                            "4) **Positive news and miscellaneous updates** – Celebrations, achievements, casual moments."
                            "Ensure only one bullet point per user per category."
                        },
                        {"role": "user", "content": "\n".join(formatted_messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await dm_channel.send("Here's a summary of recent discussions:")
                await dm_channel.send(summary)
            except Exception as e:
                await dm_channel.send(f"Error generating summary: {e}")

async def setup(bot):
    await bot.add_cog(Catchup(bot))
    command = bot.get_command("catchup")
    if command:
        command.command_mode = "server"