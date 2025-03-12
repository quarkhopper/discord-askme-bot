import discord
from discord.ext import commands
import openai
import os
import logging
from commands.bot_errors import BotErrors  # Use the standardized error handler

class UserChat(commands.Cog):
    """Handles direct DM conversations with the bot when no command is used."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def get_member_in_guild(self, user: discord.User):
        """Retrieves the member object for a user in a mutual guild, if available."""
        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id)
                if member:
                    return member  # Fast retrieval if the member is already cached
                
                # Fetch member as fallback (avoids unnecessary API calls)
                return await guild.fetch_member(user.id)
            except (discord.NotFound, discord.Forbidden):
                continue  # Skip if member isn't in the guild or bot lacks permission
            except Exception as e:
                logging.exception(f"Error fetching member {user.id} in {guild.name}: {e}")
                continue
        return None  # No mutual guilds found

    async def process_dm_message(self, message: discord.Message):
        """Processes a DM message that does not start with a command."""
        if message.author.bot:
            return  # Ignore bot messages

        # Verify user is in a mutual guild and has the "Vetted" role
        member = await self.get_member_in_guild(message.author)
        if not member:
            await message.channel.send("⚠️ I can only chat with users who share a server with me.")
            return

        if not BotErrors.require_role("Vetted")(member):
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
            logging.exception(f"UserChat Error: {e}")
            await message.channel.send("⚠️ Sorry, something went wrong while processing your message.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercepts non-command DM messages."""
        if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("!"):
            await self.process_dm_message(message)

async def setup(bot):
    await bot.add_cog(UserChat(bot))
