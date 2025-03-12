import discord
import json
from discord.ext import commands

class ConfigManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_channel_id = None  # Will be set dynamically
        self.command_config = {}  # In-memory config storage

    @commands.Cog.listener()
    async def on_ready(self):
        """Finds #bot-config dynamically and loads the latest config."""
        await self.find_config_channel()
        await self.load_latest_config()

    async def find_config_channel(self):
        """Searches for #bot-config across all guilds."""
        await self.bot.wait_until_ready()  # Ensure bot has full guild/channel data
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == "bot-config":  # Match by name
                    self.config_channel_id = channel.id
                    print(f"[ConfigManager] Found #bot-config in {guild.name} (ID: {channel.id})")
                    return  # Stop searching once found
        
        print("[ConfigManager] Could not find #bot-config in any server.")

    async def load_latest_config(self):
        """Fetches the most recent config message from the located #bot-config channel."""
        if not self.config_channel_id:
            print("[ConfigManager] No valid config channel found. Skipping config load.")
            return

        channel = self.bot.get_channel(self.config_channel_id)
        if not channel:
            print("[ConfigManager] Could not retrieve #bot-config channel by ID.")
            return

        async for message in channel.history(limit=1):
            await self.process_config_update(message.content)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detects new messages in #bot-config and updates config."""
        if message.channel.id == self.config_channel_id and message.author != self.bot.user:
            await self.process_config_update(message.content)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Detects edits to messages in #bot-config and updates config."""
        if after.channel.id == self.config_channel_id:
            await self.process_config_update(after.content)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Handles deletion of the latest config message by clearing in-memory config."""
        if message.channel.id == self.config_channel_id:
            self.command_config = {}
            print("[ConfigManager] Configuration deleted. Using empty config.")

    async def process_config_update(self, content):
        """Parses and updates the command configuration from JSON content."""
        try:
            new_config = json.loads(content)
            self.command_config = new_config  # Replace existing config
            print("[ConfigManager] Configuration updated successfully.")
        except json.JSONDecodeError:
            print("[ConfigManager] Failed to parse JSON. Check the format in #bot-config.")

    def get_command_whitelist(self, command_name):
        """Returns the list of allowed channels for a given command."""
        return self.command_config.get(command_name, {}).get("processing_whitelist", [])

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
