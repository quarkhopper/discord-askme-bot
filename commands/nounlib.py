import discord
import asyncio
from discord.ext import commands
from commands.bot_errors import BotErrors

class NounLibs(commands.Cog):
    """Cog for generating absurd stories where one user unknowingly swaps the main noun."""

    def __init__(self, bot):
        self.bot = bot

    async def request_noun_from_user(self, target_user, ctx):
        try:
            dm_channel = target_user.dm_channel or await target_user.create_dm()
            await dm_channel.send(
                f"👋 Hey {target_user.name}! {ctx.author.name} is playing **NounLibs** and needs you to provide a noun! "
                "Please reply to this message with **a single noun or short phrase** (no articles like 'the' or 'a')."
            )

            def check(m):
                return m.author == target_user and isinstance(m.channel, discord.DMChannel)

            noun_message = await self.bot.wait_for("message", timeout=180.0, check=check)
            return noun_message.content.strip()

        except asyncio.TimeoutError:
            return None
        except discord.Forbidden:
            return None

    @staticmethod
    async def not_in_dm(ctx):
        """Prevents the command from running in DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ The `!nounlib` command can't be used in DMs.")
            return False
        return True

    @commands.command()
    @commands.check(not_in_dm)
    @BotErrors.require_role("Vetted")
    async def nounlib(self, ctx, target_user: discord.Member, *, user_noun: str):
        """Generates a story where one user's noun replaces another user's noun.

        **Usage:**
        `!nounlib @target_user noun`

        The provided noun should not include articles like 'the', 'a', or 'an'.
        """
        received_noun = await self.request_noun_from_user(target_user, ctx)
        if not received_noun:
            await ctx.author.send(f"⚠️ {target_user.name} did not respond in time or has DMs disabled.")
            return

        story_prompt = (
            f"Write an amusing and creative short story centered around a '{received_noun}'. "
            f"Replace all instances of the noun in the story with '{user_noun}'. Do not mention '{received_noun}'."
        )

        try:
            response = await self.bot.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative storyteller bot."},
                    {"role": "user", "content": story_prompt}
                ]
            )
            story = response.choices[0].message.content.strip()

            message = (
                f"🎭 **NounLibs Story!** 🎭\n\n"
                f"Originally about '{received_noun}', creatively replaced by '{user_noun}' by {ctx.author.name}:\n\n{story}"
            )

            for user in [ctx.author, target_user]:
                try:
                    dm_channel = user.dm_channel or await user.create_dm()
                    await dm_channel.send(message)
                except discord.Forbidden:
                    await ctx.send(f"⚠️ {user.name} has DMs disabled and couldn't receive the story.")

            await ctx.message.delete()

        except Exception as e:
            await ctx.author.send(f"⚠️ An error occurred generating the story: {str(e)}")
            await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(NounLibs(bot))
