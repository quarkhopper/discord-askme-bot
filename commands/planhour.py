import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler

class PlanHour(commands.Cog):
    """Cog for generating a humorous plan for the next hour based on recent messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Initialize OpenAI client

    async def fetch_user_messages(self, ctx, limit=10):
        """Fetch the last `limit` messages from the user in the current channel."""
        messages = []
        async for message in ctx.channel.history(limit=limit):
            if message.author == ctx.author and not message.content.startswith("!"):
                messages.append(message.content)
        return messages

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict to users with "Peoples" role
    async def planhour(self, ctx):
        """Generates a mildly absurd but plausible plan for the next hour based on recent messages.
        
        Usage:
        `!planhour` → Extends your recent activities into a fun prediction.
        """
        if await BotErrors.check_forbidden_channel(ctx):  # Use the centralized check
            return

        messages = await self.fetch_user_messages(ctx)
        if not messages:
            await ctx.send("I couldn't find enough recent messages to make a plan!")
            return

        prompt = f"Based on these recent activities: {messages}, create a humorous but plausible plan for the next hour."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a witty AI that humorously extends a user's recent activities into exaggerated but plausible plans."},
                    {"role": "user", "content": prompt}
                ],
            )

            plan = response.choices[0].message.content.strip()
            await ctx.send(f"🕒 **Your Next Hour Plan:**\n{plan}")

        except Exception as e:
            config.logger.error(f"Error generating planhour: {e}")
            await ctx.send("An error occurred while planning your next hour.")

async def setup(bot):
    await bot.add_cog(PlanHour(bot))
