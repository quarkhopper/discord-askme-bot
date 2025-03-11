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

    async def fetch_user_messages(self, ctx, user: discord.Member, limit=10):
        """Fetch the last `limit` messages from the user in the current channel."""
        messages = []
        async for message in ctx.channel.history(limit=100):
            if message.author == user and not message.content.startswith("!"):
                messages.append(message.content)
                if len(messages) >= limit:
                    break
        return messages

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Standardized role requirement
    async def planhour(self, ctx):
        """Generates a mildly absurd but plausible plan for the next hour based on recent messages.

        **Usage:**
        `!planhour` → Generates a plan based on **your** recent messages in the current channel.

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response via DM.**
        """

        # ❌ Block DM mode but ensure the user gets feedback
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!planhour` command can only be used in a server.")
            except discord.Forbidden:
                pass  # If DMs are disabled, fail silently
            return

        # Check if command is in a forbidden channel
        if await BotErrors.check_forbidden_channel(ctx):
            return

        user = ctx.author  # Only considers the executing user
        messages = await self.fetch_user_messages(ctx, user=user)
        if not messages:
            await ctx.send(f"No recent messages found for {user.display_name}.")
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
            execution_feedback = (
                f"**Command Executed:** !planhour\n"
                f"**Channel:** {ctx.channel.name}\n"
                f"**Timestamp:** {ctx.message.created_at}\n\n"
                f"🕒 **Your Next Hour Plan:**\n{plan}"
            )

            # ✅ Send DM response instead of posting in the server
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(execution_feedback)
            except discord.Forbidden:
                await ctx.send("❌ Could not send a DM. Please enable DMs from server members.")

            # ✅ Delete the command message in the server
            await ctx.message.delete()

        except Exception as e:
            config.logger.error(f"Error generating planhour: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("An error occurred while planning your next hour.")
            except discord.Forbidden:
                await ctx.send("An error occurred while planning your next hour.")

async def setup(bot):
    await bot.add_cog(PlanHour(bot))
