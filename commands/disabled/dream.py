import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler

class DreamAnalysis(commands.Cog):
    """Cog for analyzing and interpreting dreams."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    @commands.command()
    async def dream(self, ctx, *, description: str):
        """Analyze a dream and provide an interpretation.
        
        Usage:
        `!dream I was flying over the ocean` → Returns a dream interpretation.
        """
        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # In Server Mode, enforce role restrictions and forbidden channel checks
        if not is_dm:
            if not BotErrors.require_role("Vetted")(ctx):  # Ensure correct role handling
                return
            if await BotErrors.check_forbidden_channel(ctx):
                return

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes and interprets dreams."},
                    {"role": "user", "content": f"Please analyze this dream and provide an interpretation:\n\n{description}"}
                ],
            )

            analysis = response.choices[0].message.content.strip()

            config.logger.info(f"Dream analyzed: {description[:50]}...")

            # Generate standard header message
            header = (
                f"📌 **Command Executed:** `!dream`\n"
                f"📍 **Channel:** {ctx.channel.name if not is_dm else 'Direct Message'}\n"
                f"⏳ **Timestamp:** {ctx.message.created_at}\n\n"
            )

            # Determine where to send the response
            if is_dm:
                await ctx.send(header + f"💭 **Dream Interpretation:**\n{analysis}")
            else:
                try:
                    dm_channel = await ctx.author.create_dm()
                    await dm_channel.send(header + f"💭 **Dream Interpretation:**\n{analysis}\n\n_(Sent via DM for privacy)_")
                    await ctx.message.delete()
                except discord.Forbidden:
                    await ctx.send(
                        header + f"💭 **Dream Interpretation:**\n{analysis}\n\n_(Could not send a DM. Please enable DMs from server members.)_"
                    )

        except Exception as e:
            config.logger.error(f"Error analyzing dream: {e}")
            await ctx.send("An error occurred while analyzing the dream.")

async def setup(bot):
    await bot.add_cog(DreamAnalysis(bot))

    command = bot.get_command("dream")
    if command:
        command.command_mode = "both"