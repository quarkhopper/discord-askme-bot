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
                print(f"[Debug] Skipping channel {channel_name}: Not found")
                continue  # Skip if the channel doesn't exist

            try:
                messages = []
                async for message in channel.history(after=time_threshold, limit=200):
                    if not message.author.bot:
                        messages.append(f"{message.author.display_name}: {message.content}")

                if not messages:
                    continue  # Skip empty channels

                # Log the messages before sending
                print(f"[Debug] Messages collected from {channel.name}:", messages)

                # Generate a summary for this channel
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Summarize the following Discord messages into a single paragraph."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                channel_summary = response.choices[0].message.content.strip()

                # Store this for the final summary
                overall_summaries.append(f"📢 **{channel.name} Summary:** {channel_summary}")

                # Send per-channel summary immediately
                await ctx.author.send(f"📢 **Summary for `#{channel.name}`:**\n{channel_summary}")

            except discord.Forbidden:
                print(f"[Debug] No permission to read {channel.name}")
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
