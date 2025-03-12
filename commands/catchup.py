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
    async def catchup(self, ctx):
        """Summarizes recent discussions across all whitelisted channels."""

        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Delete the command message from the channel to reduce clutter
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if the bot lacks permission to delete messages

        # Send DM execution header
        header_message = f"""
📢 **Command Executed: `!catchup`**
📅 **Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📝 **Fetching recent discussions... Please wait.**
        """
        try:
            await ctx.author.send(header_message)
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't send you a DM. Please check your privacy settings.")
            return

        # Fetch the config manager dynamically
        config_manager = self.bot.get_cog("ConfigManager")
        if not config_manager:
            await ctx.author.send("⚠️ Configuration system is not available. Please try again later.")
            return

        # Fetch allowed channels from config_manager
        allowed_channels = await config_manager.get_command_whitelist("catchup")

        # Summarize across all whitelisted channels
        user_messages = defaultdict(lambda: {"medical": [], "distress": [], "stress": [], "positive": [], "general": []})
        time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

        for channel_name in allowed_channels:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
            if not channel:
                continue  # Skip if the channel doesn't exist

            try:
                async for message in channel.history(after=time_threshold, limit=100):
                    if message.author.bot:
                        continue  

                    # Ensure categories exist before appending messages
                    if "general" not in user_messages[message.author.display_name]:
                        user_messages[message.author.display_name]["general"] = []

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

            # Format the summary for better readability
            formatted_summary = f"""
📜 **Here's a summary of recent discussions:**

🛑 **Medical emergencies, crises, or major loss:**  
{self.format_category(summary, "Medical emergencies, crises, or major loss")}

💔 **Deep emotional distress, relapses, or mental health struggles:**  
{self.format_category(summary, "Deep emotional distress, relapses, or mental health struggles")}

⚡ **General stressors:**  
{self.format_category(summary, "General stressors")}

🎉 **Positive news and miscellaneous updates:**  
{self.format_category(summary, "Positive news and miscellaneous updates")}
"""

            await ctx.author.send(formatted_summary)
        except Exception as e:
            await ctx.author.send(f"❌ Error generating summary: {e}")

    def format_category(self, summary, category_name):
        """Extracts a specific category section from the AI-generated summary."""
        if category_name in summary:
            section_start = summary.find(category_name)
            section_end = summary.find("\n", section_start)
            return summary[section_start:section_end].strip()
        return "• No messages in this category."

async def setup(bot):
    await bot.add_cog(Catchup(bot))
    command = bot.get_command("catchup")
    if command:
        command.command_mode = "server"
