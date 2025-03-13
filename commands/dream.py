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

    @commands.command()
    async def dream(self, ctx, *, description: str):
        """Analyze a dream and provide an interpretation.
        
        Usage:
        `!dream I was flying over the ocean` → Returns a dream interpretation.
        """
        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # In Server Mode, enforce role restrictions
        if not is_dm:
            role = discord.utils.get(ctx.author.roles, name="Vetted")
            if not role:
                await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
                return

        # Send DM header before processing begins
        header = (
            f"📢 **Command Executed:** `!dream`\n"
            f"📅 **Date:** {discord.utils.utcnow()}\n"
            f"📝 Analyzing your dream...\n\n"
        )

        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(header)
        except discord.Forbidden:
            await ctx.send("⚠️ I couldn't send you a DM. Please check your settings.")
            return

        # Fetch dream interpretation
        interpretation = await self.fetch_dream_analysis(description)

        # Send results via DM
        try:
            await dm_channel.send(f"💭 **Dream Interpretation:**\n{interpretation}")
            if not is_dm:
                await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ Could not send a DM. Please enable DMs from server members.")

    async def setup(bot):
        """Load the cog into the bot and set execution mode."""
        await bot.add_cog(DreamAnalysis(bot))
        command = bot.get_command("dream")
        if command:
            command.command_mode = "both"  # Supports both DM and server mode
