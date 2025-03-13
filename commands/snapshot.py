import discord
from discord.ext import commands
import openai
import os
import asyncio

class Snapshot(commands.Cog):
    """Cog for generating an AI image based on recent messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.lock = asyncio.Lock()  # Prevents multiple API calls at once

    async def fetch_recent_messages(self, ctx):
        """Fetch the last 10 messages from either the current channel or DM history."""
        is_dm = isinstance(ctx.channel, discord.DMChannel)
        messages = []

        if is_dm:
            # Fetch last 10 messages in the DM history between the user and bot
            async for message in ctx.channel.history(limit=20):
                if message.author == ctx.author or message.author == self.bot.user:
                    messages.append(message.content)
                if len(messages) >= 10:
                    break
        else:
            # Fetch last 10 messages from the server channel
            async for message in ctx.channel.history(limit=10):
                if not message.author.bot:
                    messages.append(f"{message.author.display_name}: {message.content}")

        return messages if messages else None

    async def generate_prompt(self, messages):
        """Generate an AI image prompt based on message content."""
        system_prompt = (
            "Create a vivid, creative, and visually interesting image prompt "
            "based on the following Discord messages. The prompt should describe an artistic scene "
            "that represents the conversation topics and themes in a unique and engaging way."
        )

        final_prompt = "\n".join(messages)
        async with self.lock:
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": final_prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[Snapshot] OpenAI API error: {e}")
                return None

    async def generate_image(self, prompt):
        """Generate an AI image based on the prompt using OpenAI's DALL·E API."""
        async with self.lock:
            try:
                response = await self.openai_client.images.generate(
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )
                return response.data[0].url
            except Exception as e:
                print(f"[Snapshot] OpenAI Image API error: {e}")
                return None

    @commands.command()
    async def snapshot(self, ctx):
        """Generates an AI image based on the last 10 messages.

        **Usage:**
        `!snapshot` → Uses the last 10 messages from either the channel (server) or DM history.
        """

        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # Enforce role restriction only in server mode
        if not is_dm:
            role = discord.utils.get(ctx.author.roles, name="Vetted")
            if not role:
                await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
                return

        # Acknowledge command execution with a "Please wait..." message
        please_wait = await ctx.send("⏳ Generating an AI snapshot based on recent messages. Please wait...")

        # Delete the command message in server mode
        if not is_dm:
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass  # Ignore if already deleted

        # Fetch message history
        messages = await self.fetch_recent_messages(ctx)
        if not messages:
            await please_wait.delete()
            await ctx.send("⚠️ No recent messages found to analyze.")
            return

        # Generate the image prompt
        image_prompt = await self.generate_prompt(messages)
        if not image_prompt:
            await please_wait.delete()
            await ctx.send("⚠️ Failed to generate an image prompt.")
            return

        # Generate the image
        image_url = await self.generate_image(image_prompt)
        if not image_url:
            await please_wait.delete()
            await ctx.send("⚠️ Failed to generate an image.")
            return

        # Delete the "Please wait..." message
        await please_wait.delete()

        # Create an embed to display only the image
        embed = discord.Embed(title="📸 AI Snapshot", color=discord.Color.blue())
        embed.set_image(url=image_url)

        # Send the embedded image
        await ctx.send(embed=embed)

# ✅ Ensure this command works in both DM & Server mode
async def setup(bot):
    await bot.add_cog(Snapshot(bot))
    command = bot.get_command("snapshot")
    if command:
        command.command_mode = "both"
