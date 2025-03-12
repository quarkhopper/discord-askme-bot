import discord
import json
import re
from discord.ext import commands

class ConfigManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_channel_id = None  # Will be set dynamically
        self.command_config = {}  # In-memory config storage

    @commands.Cog.listener()
    async def on_ready(self):
        """Finds #bot-config dynamically and prepares for polling on demand."""
        await self.find_config_channel()

    async def find_config_channel(self):
        """Searches for #bot-config across all guilds."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == "bot-config":
                    self.config_channel_id = channel.id
                    print(f"[ConfigManager] Found #bot-config in {guild.name} (ID: {channel.id})")
                    return
        
        print("[ConfigManager] Could not find #bot-config in any server.")

    async def fetch_latest_config(self):
        """Fetches the most recent config message from #bot-config and updates the in-memory configuration."""
        if not self.config_channel_id:
            print("[ConfigManager] No valid config channel found. Skipping config load.")
            return

        channel = self.bot.get_channel(self.config_channel_id)
        if not channel:
            print("[ConfigManager] Could not retrieve #bot-config channel by ID.")
            return

        async for message in channel.history(limit=1):
            content = message.content.strip()

            # DEBUGGING: Log the raw message content
            print(f"[ConfigManager] Raw message content: {repr(content)}")

            if not content:
                print("[ConfigManager] Retrieved an empty message from #bot-config.")
                return

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
            # Remove non-printable characters (invisible Discord artifacts)
            raw_json = re.sub(r'[^\x20-\x7E\n\t]', '', raw_json)

            # Fix smart quotes and apostrophes
            raw_json = raw_json.replace("“", "\"").replace("”", "\"")
            raw_json = raw_json.replace("’", "'").replace("‘", "'")

            # Attempt parsing again
            parsed_json = json.loads(raw_json)
        except json.JSONDecodeError:
            return None  # If still broken, return failure
        
        return json.dumps(parsed_json, indent=4)  # Return properly formatted JSON

    async def get_command_whitelist(self, command_name):
        """Retrieves the latest configuration before returning the whitelist for a command."""
        await self.fetch_latest_config()  # Polls #bot-config for the latest data
        return self.command_config.get(command_name, {}).get("processing_whitelist", [])

async def setup(bot):
    await bot.add_cog(ConfigManager(bot))
