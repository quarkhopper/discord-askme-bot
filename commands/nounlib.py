import discord
from discord.ext import commands
import openai
import asyncio
import os
import config
from commands.bot_errors import BotErrors

class NounLibs(commands.Cog):
    """Cog for generating absurd stories where one user unknowingly swaps the main noun."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def request_noun_from_user(self, target_user, ctx):
        """Sends a DM asking for a noun and waits for a response."""
        try:
            dm_channel = target_user.dm_channel or await target_user.create_dm()
            await dm_channel.send(
                f"👋 Hey {target_user.name}! {ctx.author.name} is playing **NounLibs** and needs you to provide a noun!\n\n"
                "**Reply with a single noun or short phrase (without articles like 'the' or 'a').**"
            )

            def check(m):
                return m.author == target_user and isinstance(m.channel, discord.DMChannel)

            response = await ctx.bot.wait_for("message", check=check, timeout=180)  # 180 seconds
            return response.content.strip()

        except asyncio.TimeoutError:
            return None
        except discord.Forbidden:
            return None

    @staticmethod
    async def not_in_dm(ctx):
        """Prevents the command from running in DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!nounlib` command can only be used in a server.")
            except discord.Forbidden:
                pass
            return False
        return True

    @commands.command()
    @commands.check(not_in_dm)
    @BotErrors.require_role("Vetted")
    async def nounlib(self, ctx, target_user: discord.Member, *, user_noun: str):
        """Generates a story where one user's noun replaces another user's noun.

        **Usage:**
        `!nounlib [@user] [noun phrase]` → DMs @user for a noun, generates a story, and swaps nouns.

        **Example:**
        `!nounlib @MidlevelNPC flying toaster`
        🔹 @MidlevelNPC provides a noun (e.g., "pogo stick")
        🔹 AI generates a story about "pogo stick"
        🔹 All "pogo stick" references are replaced with "flying toaster"
        🔹 The final story is DMed to **both** users.

        **Restrictions:**
        - ✅ **Must be used in a server (not DMs).**
        - ✅ **Requires the "Vetted" role.**
        - 📩 **Final story is sent via DM to both users.**
        """

        received_noun = await self.request_noun_from_user(target_user, ctx)
        if not received_noun:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(f"⚠️ {target_user.name} didn't respond in time or has DMs disabled.")
            except discord.Forbidden:
                pass
            return

        story_prompt = f"""
        Write a **well-developed short story** where a **{received_noun}** is central.
        - Introduce the **{received_noun}** within the first two sentences.
        - Keep the **{received_noun}** important throughout.
        - Have clear events leading to a conclusion.
        - About 10 sentences long.

        ⚠️ Important Rules:
        - Refer to the noun explicitly as `REPLACE-THIS-WORD`.
        - Avoid synonyms or descriptors.
        - Do not refer to it indirectly (like 'object' or 'thing').
        - Never include the actual word '{received_noun}' in the story.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate a creative short story."},
                    {"role": "user", "content": story_prompt}
                ]
            )
            story = response.choices[0].message.content.strip()

            formatted_story = story.replace("REPLACE-THIS-WORD", f"{user_noun}")

            message = (
                f"🎭 **Your NounLib Story:**\n"
                f"*(Originally about `{received_noun}`, swapped with `{user_noun}`!)*\n\n"
                f"{formatted_story}"
            )

            for user in [ctx.author, target_user]:
                try:
                    dm_channel = user.dm_channel or await user.create_dm()
                    await dm_channel.send(message)
                except discord.Forbidden:
                    pass

        except Exception as e:
            config.logger.error(f"Error in !nounlib: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("⚠️ An error occurred while generating your story. Please try again.")
            except discord.Forbidden:
                pass

        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

async def setup(bot):
    await bot.add_cog(NounLibs(bot))
