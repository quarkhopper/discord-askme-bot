import discord
from discord.ext import commands
import openai
import os
import asyncio

class DreamAnalysis(commands.Cog):
    """Cog for analyzing and interpreting dreams."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.lock = asyncio.Lock()  # Prevents multiple API calls at once

    async def fetch_dream_analysis(self, description):
        """Handles OpenAI request with retries and rate limiting."""
        async with self.lock:
            for attempt in range(3):  # Retries if rate-limited
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an AI that analyzes and interprets dreams."},
                            {"role": "user", "content": f"Please analyze this dream and provide an interpretation:\n\n{description}"}
                        ],
                    )
                    return response.choices[0].message.content.strip()
                except openai.APIError as e:
                    if "rate limit" in str(e).lower():
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"[Dream] Rate limit hit, retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[Dream] OpenAI API error: {e}")
                        break
                except Exception as e:
                    print(f"[Dream] Unexpected error: {e}")
                    break
        return "⚠️ Unable to analyze the dream due to API issues."

    async def get_last_message(self, ctx):
        """Fetches the last message in the current context if no argument is provided."""
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        try:
            if is_dm:
                async for message in ctx.channel.history(limit=2):
                    if message.author != self.bot.user:
                        return message.content
            else:
                async for message in ctx.channel.history(limit=2):
                    if message.author != self.bot.user and message.id != ctx.message.id:
                        return message.content
        except discord.Forbidden:
            return None
        return None

    @commands.command()
    async def dream(self, ctx, *, description: str = None):
        """Analyze a dream and provide an interpretation.
        
        Usage:
        `!dream I was flying over the ocean` → Returns a dream interpretation.
        `!dream` (no argument) → Uses the last message in the history.
        """
        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # Delete the command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if bot lacks permission

        # If no description provided, fetch the last message
        if not description:
            description = await self.get_last_message(ctx)
            if not description:
                await ctx.send("⚠️ No previous message found to analyze. Please provide a dream description.")
                return

        # In Server Mode, enforce role restrictions
        if not is_dm:
            role = discord.utils.get(ctx.author.roles, name="Vetted")
            if not role:
                await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
                return

        # Fetch dream interpretation
        interpretation = await self.fetch_dream_analysis(description)

        # Format the response
        response = f"💭 **Dream Interpretation:**\n{interpretation}"

        # Send output based on execution mode
        if is_dm:
            try:
                header = (
                    f"📢 **Command Executed:** `!dream`\n"
                    f"📅 **Date:** {discord.utils.utcnow()}\n"
                    f"📝 Analyzing your dream...\n\n"
                )
                await ctx.send(header + response)
            except discord.Forbidden:
                await ctx.send("⚠️ I couldn't send you a DM. Please check your settings.")
        else:
            await ctx.send(response)  # Server mode sends output directly in the channel

# ✅ FIXED: Move `setup()` OUTSIDE the class
async def setup(bot):
    """Load the cog into the bot and set execution mode."""
    await bot.add_cog(DreamAnalysis(bot))
    command = bot.get_command("dream")
    if command:
        command.command_mode = "both"  # Supports both DM and server mode
