import discord
from discord.ext import commands
import openai
import os
import datetime
from collections import defaultdict
from commands.bot_errors import BotErrors
from commands.config_manager import ConfigManager  # Import the config manager

class Catchup(commands.Cog):
    """Cog for summarizing recent events across selected channels."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Vetted")  # Restrict to users with "Vetted" role
    async def catchup(self, ctx, channel: discord.TextChannel = None):
        """Summarizes activity within whitelisted channels or a specified channel.
        
        Usage:
        `!catchup` → Summarizes recent discussions across allowed channels.
        `!catchup #channel` → Summarizes discussions in the specified channel.
        """

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Fetch the config manager dynamically
        config_manager = self.bot.get_cog("ConfigManager")
        if not config_manager:
            await ctx.send("⚠️ Configuration system is not available. Please try again later.")
            return

        # Fetch allowed channels from config_manager
        allowed_channels = await config_manager.get_command_whitelist("catchup")

        if channel:
            # If a specific channel is provided, check if it's whitelisted
            if channel.name not in allowed_channels:
                await ctx.author.send(f"⚠️ {channel.mention} is not an allowed channel for `!catchup`.")
                return

            messages = []
            time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
            try:
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(message.content)
            except discord.Forbidden:
                await ctx.author.send(f"I don’t have permission to read {channel.mention}.")
                return

            if not messages:
                await ctx.author.send(f"No recent discussions found in {channel.mention}.")
                return

            try:
                response = config_manager.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following messages by topic."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                summary = response.choices[0].message.content
                await ctx.author.send(f"Here's what's been happening in {channel.mention}:\n\n{summary}")
            except Exception as e:
                await ctx.author.send(f"Error generating summary: {e}")
        else:
            # If no specific channel is provided, summarize across all whitelisted channels
            user_messages = defaultdict(lambda: {"medical": [], "distress": [], "stress": [], "positive": []})
            time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

            for channel_name in allowed_channels:
                channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
                if not channel:
                    continue  # Skip if the channel doesn't exist

                try:
                    async for message in channel.history(after=time_threshold, limit=100):
                        if message.author.bot:
                            continue  
                        user_messages[message.author.display_name]["general"].append(message.content)
                except discord.Forbidden:
                    continue  

            if not user_messages:
                await ctx.author.send("No significant messages in the past 24 hours.")
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
                response = config_manager.openai_client.chat.completions.create(
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
                await ctx.author.send("Here's a summary of recent discussions:")
                await ctx.author.send(summary)
            except Exception as e:
                await ctx.author.send(f"Error generating summary: {e}")

async def setup(bot):
    await bot.add_cog(Catchup(bot))
    command = bot.get_command("catchup")
    if command:
        command.command_mode = "server"
