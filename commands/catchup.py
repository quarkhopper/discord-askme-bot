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
        """Summarizes recent discussions across all whitelisted channels separately before collating the final summary."""

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

        # Set message threshold (last 24 hours)
        time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

        # Collect summaries per channel
        overall_summaries = []
        for channel_name in allowed_channels:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
            if not channel:
                continue  # Skip if the channel doesn't exist

            try:
                messages = []
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(f"{message.author.display_name}: {message.content}")

                if not messages:
                    continue  # Skip empty channels

                # Generate a concise, actionable summary
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": 
                            "Summarize the following Discord messages into at most **three sentences**. "
                            "Ignore trivial or unimportant discussions. "
                            "Only include conversations that require engagement, support, or meaningful discussion. "
                            "If there is nothing important, return an empty response."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                channel_summary = response.choices[0].message.content.strip()

                # If the summary is empty or generic, skip this channel
                if not channel_summary or channel_summary.lower() in ["no important discussions.", "nothing significant.", ""]:
                    continue

                # Store this for the final summary
                overall_summaries.append(f"📢 **{channel.name} Summary:** {channel_summary}")

                # Send per-channel summary immediately
                await ctx.author.send(f"📢 **Summary for `#{channel.name}`:**\n{channel_summary}")

            except discord.Forbidden:
                continue  
            except Exception as e:
                await ctx.author.send(f"❌ Error summarizing `#{channel_name}`: {e}")

        # Send the final overall summary
        if overall_summaries:
            final_summary = "\n\n".join(overall_summaries)
            await ctx.author.send(f"📜 **Final Catchup Summary:**\n{final_summary}")
        else:
            await ctx.author.send("No significant discussions were found in the past 24 hours.")

async def setup(bot):
    await bot.add_cog(Catchup(bot))
    command = bot.get_command("catchup")
    if command:
        command.command_mode = "server"
