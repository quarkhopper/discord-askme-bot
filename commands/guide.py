import discord
from discord.ext import commands
import openai
import os
import asyncio

class Guide(commands.Cog):
    """Cog for handling the !guide command, providing channel summaries via DM."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.lock = asyncio.Lock()  # Prevents multiple API calls at once

    async def fetch_summary(self, channel_name, messages_text):
        """Handles OpenAI request with retries and rate limiting."""
        async with self.lock:
            for attempt in range(3):  # Retries if rate-limited
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": f"Summarize the recent discussion in #{channel_name}:\n{messages_text}"}]
                    )
                    return response.choices[0].message.content.strip()
                except openai.APIError as e:
                    if "rate limit" in str(e).lower():
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"[Guide] Rate limit hit, retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[Guide] OpenAI API error: {e}")
                        break
                except Exception as e:
                    print(f"[Guide] Unexpected error: {e}")
                    break
        return "⚠️ Unable to generate summary due to API issues."

    @commands.command()
    async def guide(self, ctx):
        """Provides an overview of key channels and their recent activity."""

        # Ensure command only runs in a server
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ This command can only be used in a server.")
            return

        # Verify user has "Vetted" role
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
            return

        # Delete the original command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if bot lacks permission

        # Fetch configuration dynamically
        config_manager = self.bot.get_cog("ConfigManager")
        if not config_manager:
            await ctx.send("⚠️ Configuration system is not available.")
            return

        # Fetch whitelisted channels for "guide"
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

            summary = await self.fetch_summary(channel.name, messages_text)
            summaries.append(f"📢 **Summary for #{channel.name}:**\n{summary}")

            await asyncio.sleep(1)  # **Rate limiting measure**

        # Compile the final response
        if summaries:
            final_message = "\n\n".join(summaries)
        else:
            final_message = "Fine, tbh."

        # Ensure message does not exceed 2000-character limit
        chunks = [final_message[i : i + 1900] for i in range(0, len(final_message), 1900)]

        # DM the user in chunks
        try:
            header = f"📢 **Command Executed:** `!guide`\n📅 **Date:** {discord.utils.utcnow()}\n📝 Fetching recent discussions...\n\n"
            await ctx.author.send(header)  # Send header separately
            for chunk in chunks:
                await ctx.author.send(chunk)
            await ctx.author.send("✅ !guide has finished processing. You're up to date!")
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't send you a DM. Please check your settings.")

async def setup(bot):
    """Load the cog into the bot and set execution mode."""
    await bot.add_cog(Guide(bot))
    command = bot.get_command("guide")
    if command:
        command.command_mode = "server"  # Explicitly mark this command as server-only
