import discord
from discord.ext import commands
import openai
import os
import logging

class UserChat(commands.Cog):
    """Handles direct DM conversations with the bot when no command is used."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def has_vetted_role(self, user: discord.Member):
        """Checks if the user has the 'Vetted' role in any mutual server."""
        for guild in self.bot.guilds:
            member = guild.get_member(user.id) or await guild.fetch_member(user.id)
            if member and any(role.name == "Vetted" for role in member.roles):
                return True
        return False

    async def process_dm_message(self, message: discord.Message):
        """Processes a DM message that does not start with a command."""
        if message.author.bot:
            return  # Ignore bot messages

        # Ensure user is in at least one mutual server with the bot
        mutual_guilds = [guild for guild in self.bot.guilds if message.author in guild.members]
        if not mutual_guilds:
            await message.channel.send("⚠️ I can only chat with users who share a server with me.")
            return

        # Ensure user has the 'Vetted' role
        if not await self.has_vetted_role(message.author):
            await message.channel.send("⚠️ You must have the 'Vetted' role in a mutual server to chat with me.")
            return

        # Generate AI response
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message.content}]
            )
            reply = response.choices[0].message.content
            await message.channel.send(reply)
        except Exception as e:
            logging.error(f"UserChat Error: {e}")
            await message.channel.send("⚠️ Sorry, something went wrong while processing your message.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercepts non-command DM messages."""
        if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("!"):
            await self.process_dm_message(message)

async def setup(bot):
    await bot.add_cog(UserChat(bot))
