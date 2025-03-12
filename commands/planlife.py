import discord
from discord.ext import commands
import openai
import config  # Import shared config
import os
from commands.bot_errors import BotErrors  # Import the error handler
from commands.command_utils import command_mode

class PlanLife(commands.Cog):
    """Cog for generating an exaggerated but semi-realistic lifelong mission based on recent messages."""

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
    @command_mode("server")
    @BotErrors.require_role("Vetted")  # ✅ Updated to follow the latest spec
    async def planlife(self, ctx):
        """Generates a wildly exaggerated but somewhat realistic lifelong mission based on recent messages.

        **Usage:**
        `!planlife` → Generates a plan based on **your** recent messages in the current channel.

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response via DM.**
        """

        # ❌ Block DM mode but ensure the user gets feedback
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!planlife` command can only be used in a server.")
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

        prompt = f"Based on these recent activities: {messages}, create a wildly exaggerated but somewhat realistic lifelong mission."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a witty AI that humorously extends a user's recent activities into an exaggerated but semi-realistic lifelong mission."},
                    {"role": "user", "content": prompt}
                ],
            )

            mission = response.choices[0].message.content.strip()
            execution_feedback = (
                f"**Command Executed:** !planlife\n"
                f"**Channel:** {ctx.channel.name}\n"
                f"**Timestamp:** {ctx.message.created_at}\n\n"
                f"🌟 **Your Lifelong Mission:**\n{mission}"
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
            config.logger.error(f"Error generating planlife: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("An error occurred while planning your lifelong mission.")
            except discord.Forbidden:
                await ctx.send("An error occurred while planning your lifelong mission.")

async def setup(bot):
    await bot.add_cog(PlanLife(bot))
