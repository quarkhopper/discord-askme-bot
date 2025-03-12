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
            await self.process_config_update(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detects new messages in #bot-config and updates config."""
        if message.channel.id == self.config_channel_id and message.author != self.bot.user:
            await self.process_config_update(message)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Detects edits to messages in #bot-config and updates config."""
        if after.channel.id == self.config_channel_id:
            await self.process_config_update(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Handles deletion of the latest config message by clearing in-memory config."""
        if message.channel.id == self.config_channel_id:
            self.command_config = {}
            print("[ConfigManager] Configuration deleted. Using empty config.")

    async def process_config_update(self, message):
        """Parses and updates the command configuration from a JSON message, fixing issues when necessary."""
        content = message.content.strip()
        try:
            new_config = json.loads(content)  # Try parsing first
            self.command_config = new_config  # Replace existing config
            print("[ConfigManager] Configuration updated successfully.")
        except json.JSONDecodeError:
            print("[ConfigManager] Invalid JSON detected. Attempting to correct format...")

            # Attempt to fix JSON formatting
            fixed_content = self.fix_json_format(content)
            if fixed_content:
                try:
                    corrected_config = json.loads(fixed_content)  # Verify corrected JSON
                    self.command_config = corrected_config  # Apply the corrected config
                    print("[ConfigManager] JSON format corrected and configuration updated.")

                    # Edit the original message to update with fixed JSON
                    await message.edit(content=f"```json\n{fixed_content}\n```")
                    print("[ConfigManager] Updated #bot-config with corrected JSON.")
                except json.JSONDecodeError:
                    print("[ConfigManager] Automatic correction failed. Manual review needed.")
            else:
                print("[ConfigManager] Could not generate a corrected JSON format.")

    def fix_json_format(self, raw_json):
        """Attempts to fix common JSON formatting issues."""
        try:
            parsed_json = json.loads(raw_json)  # If it's already valid, return as formatted string
        except json.JSONDecodeError:
            # Attempt simple fixes (e.g., replacing smart quotes, fixing commas)
            raw_json = raw_json.replace("“", "\"").replace("”", "\"")  # Fix smart quotes
            raw_json = raw_json.replace("’", "'").replace("‘", "'")  # Fix apostrophes

            try:
                parsed_json = json.loads(raw_json)  # Retry parsing
            except json.JSONDecodeError:
                return None  # If still broken, give up

        return json.dumps(parsed_json, indent=4)  # Return properly formatted JSON

    def get_command_whitelist(self, command_name):
        """Returns the list of allowed channels for a given command."""
        return self.command_config.get(command_name, {}).get("processing_whitelist", [])

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
