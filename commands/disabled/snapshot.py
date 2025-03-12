import discord
from discord.ext import commands
import openai
import os
import asyncio
import config  # ✅ Ensures logging and error handling works properly
from commands.bot_errors import BotErrors  # Import the error handler

class Snapshot(commands.Cog):
    """Cog for generating an AI image based on recent channel messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_prompt(self, messages):
        """Runs OpenAI text completion in a background thread with strict truncation."""
        system_prompt = (
            "Create a vivid, creative, and visually interesting image prompt "
            "based on the following Discord messages. The prompt should describe an artistic scene "
            "that represents the conversation topics and themes in a unique and engaging way."
        )

        # ✅ Ensure total message length (including system prompt) stays ≤ 1000 chars
        max_length = 1000 - len(system_prompt) - 50  # Extra buffer for safety
        truncated_messages = []
        current_length = 0

        for msg in messages:
            if current_length + len(msg) > max_length:
                break
            truncated_messages.append(msg)
            current_length += len(msg)

        final_prompt = "\n".join(truncated_messages)

        return await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ]
        )

    async def generate_image(self, prompt):
        """Runs DALL·E image generation in a background thread."""
        return await asyncio.to_thread(
            self.openai_client.images.generate,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Standardized role requirement
    async def snapshot(self, ctx):
        """Generates an AI image based on the last 10 messages in the current channel.

        **Usage:**
        `!snapshot` → Uses the last 10 messages from the current channel.

        **Restrictions:**
        - ❌ **This command cannot be used in DMs.**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response via DM.**
        """

        # ❌ Block DM mode but ensure the user gets feedback
        if isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.send("❌ The `!snapshot` command can only be used in a server.")
            except discord.Forbidden:
                pass  # If DMs are disabled, fail silently
            return

        # ✅ Immediately delete the command message to avoid clutter
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass  # If message was already deleted, ignore

        # Check if command is in a forbidden channel
        if await BotErrors.check_forbidden_channel(ctx):
            return

        messages = []
        try:
            async for message in ctx.channel.history(limit=10):
                if not message.author.bot:
                    messages.append(f"{message.author.name}: {message.content}")
        except discord.Forbidden:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(f"❌ I don’t have permission to read messages in {ctx.channel.name}.")
            except discord.Forbidden:
                await ctx.send(f"❌ I don’t have permission to read messages in {ctx.channel.name}.")
            return

        if not messages:
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(f"❌ No recent messages found in {ctx.channel.name}.")
            except discord.Forbidden:
                await ctx.send(f"❌ No recent messages found in {ctx.channel.name}.")
            return

        try:
            # Generate the image prompt asynchronously
            response = await self.generate_prompt(messages)
            image_prompt = response.choices[0].message.content

            # Generate the image asynchronously
            dalle_response = await self.generate_image(image_prompt)
            image_url = dalle_response.data[0].url  

            execution_feedback = (
                f"**Command Executed:** !snapshot\n"
                f"**Channel:** {ctx.channel.name}\n"
                f"**Timestamp:** {ctx.message.created_at}\n\n"
                f"🎨 **AI-Generated Image:**\n*{image_prompt}*\n{image_url}"
            )

            # ✅ Send DM response instead of posting in the server
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send(execution_feedback)
            except discord.Forbidden:
                await ctx.send("❌ Could not send a DM. Please enable DMs from server members.")

        except Exception as e:
            config.logger.error(f"Error generating snapshot: {e}")
            try:
                dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()
                await dm_channel.send("An error occurred while generating the snapshot.")
            except discord.Forbidden:
                await ctx.send("An error occurred while generating the snapshot.")

Snapshot.snapshot.command_mode = "server"

async def setup(bot):
    await bot.add_cog(Snapshot(bot))

    command = bot.get_command("snapshot")
    if command:
        command.command_mode = "server"
