import discord
from discord.ext import commands
import openai
import os
import datetime
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
        """
        Usage: `!catchup`
        
        Summarizes recent discussions across all whitelisted channels.

        - Fetches discussions from the last 24 hours.
        - Summarizes only engaging conversations (ignoring trivial updates).
        - Sends results via DM to prevent server clutter.
        - Uses dynamically configured channel whitelists (via `config_manager.py`).
        """

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

                # **Generate a concise, actionable summary**
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": 
                            "Summarize the following Discord messages into at most **three sentences**. "
                            "Ignore trivial or unimportant discussions. "
                            "Ignore single-message exchanges unless they spark a broader discussion. "
                            "Ignore solo updates unless they received responses or engagement. "
                            "Only include conversations that require engagement, support, or meaningful discussion."},
                        {"role": "user", "content": "\n".join(messages)}
                    ]
                )
                refined_summary = response.choices[0].message.content.strip()

                # **Filter out non-engaging summaries**
                if refined_summary.upper() == "IGNORE":
                    continue  # Skip this channel

                # **Store summary without sending immediately**
                summary_text = f"📢 **Summary for `#{channel.name}`:**\n{refined_summary}"
                overall_summaries.append(summary_text)

            except discord.Forbidden:
                continue  
            except Exception as e:
                await ctx.author.send(f"❌ Error summarizing `#{channel_name}`: {e}")

        # **Send summaries only once at the end**
        if overall_summaries:
            final_summary = "\n\n".join(overall_summaries)

            # **Split long messages into chunks before sending**
            def split_into_chunks(text, max_length=2000):
                chunks = []
                while len(text) > max_length:
                    split_index = text[:max_length].rfind("\n")  # Try to break at the last newline
                    if split_index == -1:
                        split_index = max_length  # If no newline found, break at max length
                    chunks.append(text[:split_index])
                    text = text[split_index:].strip()
                chunks.append(text)  # Append remaining part
                return chunks

            for chunk in split_into_chunks(final_summary):
                await ctx.author.send(chunk)  # Send each chunk separately
        else:
            await ctx.author.send("✅ **`!catchup` complete. No significant discussions found.**")

        # **Final confirmation message**
        await ctx.author.send("✅ **`!catchup` has finished processing. You're up to date!**")

async def setup(bot):
    await bot.add_cog(Catchup(bot))
    command = bot.get_command("catchup")
    if command:
        command.command_mode = "server"
