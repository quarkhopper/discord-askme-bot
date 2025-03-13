# Discord AskMe Bot - Design Notes & Guidelines

## Overview
The AskMe bot is a Discord bot designed to facilitate community interactions with a structured command system.
It is built using Python and the discord.py library, hosted on Railway. This document serves as a reference for
ensuring design consistency and efficient synchronization across multiple development environments.

# Bot Architecture

## File Structure
```
discord-askme-bot/
├── main.py
├── Procfile
├── requirements.txt
├── commands/
│   ├── bot_errors.py
│   ├── catchup.py
│   ├── chat.py
│   ├── commands.py
│   ├── config_manager.py
│   ├── guide.py
│   ├── image.py
│   ├── message_utils.py
│   ├── mood.py
│   ├── nounlib.py
│   ├── planhour.py
│   ├── planlife.py
│   ├── snapshot.py
│   ├── talkto.py
│   ├── user_chat.py
│   └── disabled/
│       ├── (archived command files)
├── docs/
│   ├── update_strategy.md
```

## Main Components
- `main.py`: Handles bot initialization, event listening, and command registration.
- `config_manager.py`: Manages dynamic command configurations, including channel whitelists.
- `commands/`: Contains individual command implementations, each as a separate module.
- `bot_errors.py`: Centralized error handling.

## Bot Initialization Flow
1. Initialize `discord.ext.commands.Bot`.
2. Load environment variables and `config_manager.py`.
3. Register event listeners and load command cogs.
4. Run the bot using `bot.run(TOKEN)`.

---

# Command Execution Modes

## DM Mode
- Commands execute without user or channel context.
- Commands that normally default to the current channel will use the bot’s DM history with the user instead.
- Role restrictions do not apply in DM mode.
- Users must be a member of at least one Discord server that the bot is also a member of.
- Useful for:
  - Commands like `!chat`, which accept a string argument and do not depend on a channel.
  - Commands like `!clear`, which allow users to manage their own DM history.

## Server Mode
- Commands operate within a Discord server, using the existing rules and restrictions.
- Users must meet the following requirements to use any command in Server Mode:
  - Be a member of the same Discord server as the bot.
  - Have the **"Vetted"** role assigned to them in that server.
- Commands use the current server channel by default unless specified otherwise.
- Standard command behaviors apply, including message deletion, DM feedback, and error handling.

---

# Command Structure

## Standard Command Guidelines

### Command Execution Mode Tagging
- Each command must specify its execution mode as `"server"`, `"dm"`, or `"both"`.
- This tagging should be included in the command file’s setup function:
  ```python
  async def setup(bot):
      await bot.add_cog(CommandClass(bot))
      command = bot.get_command("command_name")
      if command:
          command.command_mode = "server"  # Can be "server", "dm", or "both"
  ```

### General Command Rules
- All commands should be defined inside **Cogs**.
- Use `@commands.command()` to define commands.
- Implement role restrictions where necessary (see Section 3.2).
- Ensure proper parsing of user and channel arguments (see Section 5.2).
- Include an error handler for each command to ensure smooth user experience.
- **All command feedback should be sent as a DM to the user.**
- **Command execution must include a DM header with:**
  - 📢 **Command Executed:** `<command>`
  - 📅 **Date**
  - 📝 **Processing status**
- **If the DM is successfully sent, delete the original command message.**
- **If the DM cannot be sent, display an error message in the channel, but do NOT send the full response there.**
- **Bot-generated command responses must never be posted in the server channel** to prevent clutter.
- **Final status messages** (e.g., `"✅ Done!"`) should be sent for commands with long processing times.
- **Long responses **must be split into chunks** to avoid exceeding Discord’s 2000-character limit.**
---

# Dynamic Command Configurations

## `config_manager.py`
- `config_manager.py` is responsible for **retrieving dynamic command settings** from the `#bot-config` channel.
- **Command-specific settings** (such as processing whitelists) are stored as JSON messages inside `#bot-config`.
- Any command that references channels **must check `config_manager.py` dynamically** instead of hardcoding them.

### Example JSON Format in `#bot-config`
```json
{
  "catchup": {
    "processing_whitelist": [
      "general",
      "story-time",
      "crisis-chat"
    ]
  }
}
```
- Commands must query `config_manager.py` at runtime to get the latest allowed channels.
- **Commands should NOT assume all channels are available**—whitelists dictate usage.

---

# Common Development Issues & Fixes

### **Commands Must Delete Their Invocation Messages**
@ISSUE  
Some commands leave clutter by failing to delete the user’s command message.

@FIX  
Ensure `ctx.message.delete()` runs **before** processing starts.  
```python
try:
    await ctx.message.delete()
except discord.Forbidden:
    pass  # Ignore if bot lacks permission
```

---

### **Final Notes**
- The bot's role is **to facilitate structured and engaging conversations, not just provide information.**
- **AI responses should feel natural and useful—not robotic.**
- **Any major command refactor should be documented here.**

🚀 **Guidelines are now up to date!**
