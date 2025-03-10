import discord
from discord.ext import commands
import openai
import os
import asyncio
from commands.bot_errors import BotErrors  # Import the error handler


class Snapshot(commands.Cog):
    """Cog for generating an AI image based on recent channel messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_prompt(self, messages):
        """Runs OpenAI text completion in a background thread."""
        return await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Create a vivid, creative, and visually interesting image prompt "
                               "based on the following Discord messages. The prompt should describe an artistic scene "
                               "that represents the conversation topics and themes in a unique and engaging way."
                },
                {"role": "user", "content": "\n".join(messages)}
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
    @BotErrors.require_role("Peoples")  # Restrict command usage to users with the "Peoples" role
    async def snapshot(self, ctx, channel: discord.TextChannel = None):
        """Generates an AI image based on the last 10 messages in a channel.

        Usage:
        `!snapshot` → Uses the current channel's last 10 messages.
        `!snapshot #channel-name` → Uses the last 10 messages from the specified channel.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        if channel is None:
            channel = ctx.channel

        waiting_message = await ctx.send(f"Analyzing recent messages in {channel.mention}... Please wait.")

        messages = []
        try:
            async for message in channel.history(limit=10):
                if not message.author.bot:
                    messages.append(f"{message.author.name}: {message.content}")
        except discord.Forbidden:
            await waiting_message.edit(content=f"I don’t have permission to read {channel.mention}.")
            return

        if not messages:
            await waiting_message.edit(content=f"No recent messages found in {channel.mention}.")
            return

        try:
            # Generate the image prompt asynchronously
            response = await self.generate_prompt(messages)
            image_prompt = response.choices[0].message.content

            # Generate the image asynchronously
            dalle_response = await self.generate_image(image_prompt)
            image_url = dalle_response.data[0].url  

            await waiting_message.edit(content=f"🎨 **Here's an AI-generated image based on {channel.mention}:**\n*{image_prompt}*\n{image_url}")

        except Exception as e:
            await waiting_message.edit(content=f"Error generating image: {e}")


async def setup(bot):
    await bot.add_cog(Snapshot(bot))
