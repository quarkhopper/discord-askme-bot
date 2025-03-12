import discord
from discord.ext import commands, tasks
import openai
import os
import logging
import time  # Used for session timeout

class UserChat(commands.Cog):
    """Handles direct DM conversations with the bot when no command is used, with short-term memory."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_memory = {}  # Stores temporary conversation context
        self.memory_timeout = 28800  # 8 hours (in seconds)
        self.cleanup_sessions.start()  # Starts session cleanup task

    def cog_unload(self):
        """Ensures cleanup task is stopped when cog is unloaded."""
        self.cleanup_sessions.cancel()

    async def get_member_in_guild(self, user: discord.User):
        """Retrieves the member object for a user in a mutual guild, if available."""
        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id) or await guild.fetch_member(user.id)
                if member:
                    return member
            except (discord.NotFound, discord.Forbidden):
                continue  # Skip if member isn't in the guild or bot lacks permission
            except Exception as e:
                logging.exception(f"Error fetching member {user.id} in {guild.name}: {e}")
                continue
        return None  # No mutual guilds found

    def has_vetted_role(self, member: discord.Member):
        """Checks if the user has the 'Vetted' role in the guild."""
        return any(role.name == "Vetted" for role in member.roles)

    async def process_dm_message(self, message: discord.Message):
        """Processes a DM message that does not start with a command."""
        if message.author.bot:
            return  # Ignore bot messages

        # Verify user is in a mutual guild
        member = await self.get_member_in_guild(message.author)
        if not member:
            await message.channel.send("⚠️ I can only chat with users who share a server with me.")
            return

        # Verify user has the 'Vetted' role
        if not self.has_vetted_role(member):
            await message.channel.send("⚠️ You must have the 'Vetted' role in a mutual server to chat with me.")
            return

        user_id = message.author.id

        # Check if user wants to forget conversation
        if message.content.lower().strip() in ["forget this", "forget everything"]:
            if user_id in self.session_memory:
                del self.session_memory[user_id]
                await message.channel.send("🧹 I’ve forgotten our conversation.")
            else:
                await message.channel.send("🧹 There's nothing to forget right now.")
            return

        # Retrieve or initialize user session memory
        if user_id not in self.session_memory:
            self.session_memory[user_id] = {"messages": [], "last_active": time.time()}

        session = self.session_memory[user_id]

        # Append user message to context
        session["messages"].append({"role": "user", "content": message.content})
        session["last_active"] = time.time()  # Update last activity time

        # Keep only the last few messages (limit to prevent overflow)
        session["messages"] = session["messages"][-10:]

        # Generate AI response using conversation history
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=session["messages"]
            )
            reply = response.choices[0].message.content
            await message.channel.send(reply)

            # Append bot response to memory
            session["messages"].append({"role": "assistant", "content": reply})

        except Exception as e:
            logging.exception(f"UserChat Error: {e}")
            await message.channel.send("⚠️ Sorry, something went wrong while processing your message.")

    @tasks.loop(minutes=5)
    async def cleanup_sessions(self):
        """Removes inactive sessions after timeout (8 hours)."""
        current_time = time.time()
        to_remove = [user_id for user_id, session in self.session_memory.items() if current_time - session["last_active"] > self.memory_timeout]
        for user_id in to_remove:
            del self.session_memory[user_id]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercepts non-command DM messages."""
        if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("!"):
            await self.process_dm_message(message)

async def setup(bot):
    await bot.add_cog(UserChat(bot))
