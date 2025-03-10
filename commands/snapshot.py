import discord
from discord.ext import commands
import openai
import os
from commands.bot_errors import BotErrors  # Import the error handler


class Snapshot(commands.Cog):
    """Cog for generating an AI image prompt from recent channel messages."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @commands.command()
    @BotErrors.require_role("Peoples")  # Restrict command usage to users with the "Peoples" role
    async def snapshot(self, ctx, channel: discord.TextChannel = None):
        """Generates an AI image prompt based on the last 10 messages in a channel.

        Usage:
        `!snapshot` → Uses the current channel's last 10 messages.
        `!snapshot #channel-name` → Uses the last 10 messages from the specified channel.
        """

        if await BotErrors.check_forbidden_channel(ctx):  # Prevents command use in #general
            return

        # Default to the current channel if no channel is provided
        if channel is None:
            channel = ctx.channel

        # Notify the user that the bot is processing
        waiting_message = await ctx.send(f"Analyzing recent messages in {channel.mention}... Please wait.")

        # Fetch the last 10 messages
        messages = []
        try:
            async for message in channel.history(limit=10):
                if not message.author.bot:  # Ignore bot messages
                    messages.append(f"{message.author.name}: {message.content}")
        except discord.Forbidden:
            await waiting_message.edit(content=f"I don’t have permission to read {channel.mention}.")
            return

        if not messages:
            await waiting_message.edit(content=f"No recent messages found in {channel.mention}.")
            return

        # Generate an image prompt using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
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
            image_prompt = response.choices[0].message.content

            # Send the generated prompt
            await waiting_message.edit(content=f"🎨 **Here's your AI-generated image prompt:**\n*{image_prompt}*")

        except Exception as e:
            await waiting_message.edit(content=f"Error generating image prompt: {e}")


async def setup(bot):
    await bot.add_cog(Snapshot(bot))
