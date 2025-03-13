import discord
from discord.ext import commands
import openai
import os

class Guide(commands.Cog):
    """Cog for handling the !guide command, providing channel summaries via DM."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    async def guide(self, ctx):
        """Provides an overview of key channels and their recent activity."""

        # Ensure command is executed within a server
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server.")
            return

        # Verify the user has the "Vetted" role
        if not ctx.author.guild_permissions.administrator:  # Adjust as needed
            await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
            return

        # Delete the original command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if bot lacks permission

        # Fetch config manager dynamically (fixing issue)
        config_manager = self.bot.get_cog("ConfigManager")
        if not config_manager:
            await ctx.send("⚠️ Configuration system is not available. Please try again later.")
            return

        # Fetch whitelisted channels from config_manager under "guide"
        whitelisted_channels = await config_manager.get_command_whitelist("guide")
        if not whitelisted_channels:
            await ctx.send("⚠️ No channels are currently whitelisted for summaries.")
            return

        summaries = []
        for channel_name in whitelisted_channels:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
            if not channel:
                continue

            # Fetch recent messages for summarization
            messages = [msg async for msg in channel.history(limit=20)]
            messages_text = "\n".join(f"{msg.author.display_name}: {msg.content}" for msg in messages if msg.content)

            if not messages_text.strip():
                continue  # Skip empty channels

            # Send request to OpenAI
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Summarize the following discussion in {channel.name}:\n{messages_text}"}]
                )
                summary = response.choices[0].message.content
                summaries.append(f"📢 **Summary for #{channel.name}:**\n{summary}")

            except Exception as e:
                summaries.append(f"⚠️ Error summarizing #{channel.name}: {e}")

        # Compile final response
        if summaries:
            final_message = "\n\n".join(summaries)
        else:
            final_message = "⚠️ No significant discussions found in the whitelisted channels."

        # DM the user
        try:
            header = f"📢 **Command Executed:** `!guide`\n📅 **Date:** {discord.utils.utcnow()}\n📝 Fetching recent discussions...\n\n"
            await ctx.author.send(header + final_message)
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't send you a DM. Please check your settings.")

async def setup(bot):
    """Load the cog into the bot."""
    await bot.add_cog(Guide(bot))

    command = bot.get_command("guide")
    if command:
        command.command_mode = "server"
