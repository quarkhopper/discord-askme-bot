import discord
from discord.ext import commands
import openai
import re
import asyncio
import os
import config  # Logging and settings
from commands.bot_errors import BotErrors  # Error handling

class NounLibs(commands.Cog):
    """Cog for generating absurd stories where one user unknowingly swaps the main noun."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def request_noun_from_user(self, target_user, ctx):
        """Sends a DM to the target user asking for a noun and waits for their response."""
        try:
            dm_channel = target_user.dm_channel or await target_user.create_dm()
            await dm_channel.send(
                f"👋 Hey {target_user.name}! {ctx.author.name} is playing **NounLibs** and needs you to provide a noun! "
                "Please reply to this message with **a single noun or short phrase**."
            )

            def check(m):
                return m.author == target_user and isinstance(m.channel, discord.DMChannel)

            response = await ctx.bot.wait_for("message", check=check, timeout=60)  # Wait 60 seconds
            return response.content.strip()

        except asyncio.TimeoutError:
            return None
        except discord.Forbidden:
            return None  # If DMs are disabled

    @staticmethod
    async def not_in_dm(ctx):
        """Prevents the command from running in DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!nounlib` command can only be used in a server.")
            except discord.Forbidden:
                pass  # Fail silently if DMs are disabled
            return False
        return True

    @commands.command()
    @commands.check(not_in_dm)  # ✅ Ensures command is only used in a server
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def nounlib(self, ctx, target_user: discord.Member, *, user_noun: str):
        """Generates a story where one user's noun replaces another user's noun.

        **Usage:**
        `!nounlib [@user] [noun phrase]` → DMs @user for a noun, generates a story for that noun, and swaps it with the provided noun phrase.

        **Example:**
        `!nounlib @MidlevelNPC flying toaster`
        🔹 @MidlevelNPC is asked for a noun (e.g., "pogo stick")
        🔹 AI generates a story about "pogo stick"
        🔹 All "pogo stick" references are replaced with "flying toaster"
        🔹 The final story is DMed to **both** users.

        **Restrictions:**
        - ✅ **Must be used in a server (not DMs).**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Final story is sent via DM to both users.**
        """

        # ✅ Step 1: Ask the target user for a noun via DM
        received_noun = await self.request_noun_from_user(target_user, ctx)
        if not received_noun:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(f"⚠️ {target_user.name} did not respond in time or has DMs disabled.")
            except discord.Forbidden:
                pass  # Fail silently if DMs are disabled
            return

        # ✅ Step 2: Generate a **longer 10-sentence story** for the noun
        story_prompt = f"""
        Write a **well-developed short story** where a **{received_noun}** is the central object of interest.
        The story should:
        - Introduce the **{received_noun}** **within the first two sentences**.
        - Keep the **{received_noun}** important from beginning to end.
        - Have a natural progression with **clear events leading to a conclusion**.
        - Be **about 10 sentences long**.

        ⚠️ **Important Rules:**
        - Do **not** replace the noun with any synonyms, descriptors, or alternative names.  
        - Do **not** refer to it as an "object," "statue," "figure," or anything other than exactly what it is.  
        - The noun should always be referred to as `REPLACE-THIS-WORD`.  
        - Avoid any implied assumptions about the noun’s nature.  

        Do **not** include the word "{received_noun}" in the story. 
        Instead, replace it with `REPLACE-THIS-WORD` exactly as written.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Generate a well-structured short story."},
                          {"role": "user", "content": story_prompt}]
            )
            story = response.choices[0].message.content.strip()

            # ✅ Step 3: Replace the placeholder "REPLACE-THIS-WORD" with the first user's noun
            formatted_story = story.replace("REPLACE-THIS-WORD", f"**{user_noun}**")

            # ✅ Step 4: DM the final story to both users
            message = (
                f"🎭 **Your NounLib Story:**\n"
                f"*(Originally written about `{received_noun}`, but swapped with `{user_noun}`!)*\n\n"
                f"{formatted_story}"
            )

            for user in [ctx.author, target_user]:  # DM both the requester and the noun provider
                try:
                    dm_channel = user.dm_channel or await user.create_dm()
                    await dm_channel.send(message)
                except discord.Forbidden:
                    pass  # Fail silently if DMs are disabled

        except Exception as e:
            config.logger.error(f"Error in !nounlib: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("⚠️ An error occurred while generating your story. Try again!")
            except discord.Forbidden:
                pass  # Fail silently if DMs are disabled

        # ✅ Step 5: Immediately delete the command message in the server (to avoid clutter)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass  # If already deleted, ignore

async def setup(bot):
    await bot.add_cog(NounLibs(bot))
