# Discord AskMe Bot - Design Notes & Guidelines

## 1. Overview

The AskMe bot is a Discord bot designed to facilitate community interactions with a structured command system. It is built using Python and the `discord.py` library, hosted on Railway. This document serves as a reference for ensuring design consistency and efficient synchronization across multiple development environments.

---

## 2. Bot Architecture

### 2.1 File Structure

```
discord-askme-bot/
├── config.py              # Bot configuration and environment variables
├── main.py                # Entry point for the bot
├── Procfile               # Railway process definition
├── requirements.txt       # Dependencies
├── commands/              # Directory for command implementations
│   ├── bot_errors.py      # Global error handling
│   ├── catchup.py         # !catchup command
│   ├── chat.py            # !chat command
│   ├── dream.py           # !dream command
│   ├── guide.py           # !guide command
│   ├── image.py           # !image command
│   ├── mood.py            # !mood command
│   ├── planhour.py        # !planhour command
│   ├── planlife.py        # !planlife command
│   ├── snapshot.py        # !snapshot command
│   ├── talkto.py          # !talkto command
│   ├── message_utils.py   # Shared message processing utilities
├── guidelines.md          # Design guidelines and bot documentation
└── .git/                  # Git repository metadata
```

### 2.2 Main Components

- **`main.py`**: Handles bot initialization, event listening, and command registration.
- **`config.py`**: Manages environment variables, tokens, and other settings.
- **`commands/` directory**: Contains individual command implementations, each as a separate module.
- **`message_utils.py`**: Provides helper functions for processing Discord messages.
- **`bot_errors.py`**: Centralized error handling.

### 2.3 Bot Initialization Flow

1. Load configuration from `config.py`.
2. Initialize `discord.ext.commands.Bot`.
3. Register event listeners and load command cogs.
4. Run the bot using `bot.run(TOKEN)`.

---

## 3. Command Execution Modes

All commands must support **two execution modes**: **DM Mode** and **Server Mode**.

### 3.1 DM Mode

- Commands execute **without user or channel context**.
- Commands that normally default to the current channel will use **the bot’s DM history with the user** instead.
- **Role restrictions do not apply** in DM mode.
- Users must be **a member of at least one Discord server** that the bot is also a member of.
- Useful for:
  - Commands like `!chat`, which accept a **string argument** and do not depend on a channel.
  - Commands like `!clear`, which allow users to manage **their own DM history**.

### 3.2 Server Mode

- Commands operate **within a Discord server**, using the **existing rules and restrictions**.
- **Users must meet the following requirements to use any command in Server Mode:**
  - Be a **member of the same Discord server** as the bot.
  - Have the **"Vetted" role** assigned to them in that server.
- Commands use **the current server channel** by default, unless specified otherwise.
- Standard command behaviors apply, including **message deletion, DM feedback, and error handling**.

---

## 4. Command Structure

### 4.1 Commands as Cogs

Commands are implemented as **Cogs**, which allows modularity and better organization.

Each command file is structured as follows:

```python
import discord
from discord.ext import commands

class CommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="command_name")
    async def execute(self, ctx, *args):
        """Handles the command logic.
        
        Usage:
        `!command_name <arguments>` → Description of what the command does.
        """
        # Send DM with execution details
        try:
            dm_channel = await ctx.author.create_dm()
            await dm_channel.send(f"**Command Executed:** command_name
**Channel:** {ctx.channel.name}
**Timestamp:** {ctx.message.created_at}")
            
            # Command-specific logic here
            await dm_channel.send("Response message")
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("Could not send a DM. Please enable DMs from server members.")
        except Exception as e:
            await ctx.send("An error occurred.")

    @execute.error
    async def execute_error(self, ctx, error):
        await ctx.send("An error occurred.")

# Required setup function for bot to load the cog
def setup(bot):
    bot.add_cog(CommandCog(bot))
```

### 4.2 Standard Command Guidelines

- **All commands should be defined inside Cogs**.
- **Use `@commands.command()` to define commands**.
- **Implement role restrictions where necessary** (see Section 3.2).
- **Ensure proper parsing of user and channel arguments** (see Section 5.2).
- **Include an `error handler` for each command** to ensure smooth user experience.
- **All command feedback should be sent as a DM to the user**.
- **A header message should be sent before command execution, including command name, channel, and timestamp**.
- **If the DM is successfully sent, delete the original command message**.
- **If the DM cannot be sent, display an error message in the channel**.
- **Errors should be sent as a DM first, falling back to the channel if DMs are disabled.**
- **Role restriction failure messages should also be sent as DMs first, then fallback to the channel if needed.**
- **All commands must include a usage statement in the docstring, explaining the command syntax and expected arguments.**

---

## 5. Common Development Issues & Fixes

### 5.1 TypeError: `object Context can't be used in 'await' expression`
#### Issue:
Occurs when mistakenly `await`ing a synchronous function like `require_role()`.
#### Fix:
Remove `await` from the function call:
```python
if not BotErrors.require_role("Vetted")(ctx):  # Correct usage
    return
```
Instead of:
```python
if not await BotErrors.require_role("Vetted")(ctx):  # Incorrect usage
    return
```

### 5.2 Correctly Parsing Optional User and Channel Arguments
#### Issue:
Parsing an optional username and channel name from command arguments can be tricky, leading to incorrect resolutions.
#### Fix:
Use the pattern from `mood.py`, which:
- Iterates through `args`, attempting to resolve each as either a **user** or a **channel**.
- Prioritizes matching users first, then channels.
- Defaults to the **current channel** if no channel argument is provided.
```python
for arg in args:
    resolved_user = await self.resolve_member(ctx, arg)
    if resolved_user:
        user = resolved_user
        continue
    
    resolved_channel = await self.resolve_channel(ctx, arg)
    if resolved_channel:
        channel = resolved_channel
        continue
```

### 5.3 Debugging `chat.py` - Membership Verification
#### Issue:
The bot incorrectly flagged valid server members as not being in the server.
#### Fix:
- Use `await ctx.guild.fetch_member(ctx.author.id)` instead of `ctx.guild.get_member(ctx.author.id)`.
- Catch `discord.NotFound` separately to avoid misinterpreting other errors.
- Use a **backup check** with `ctx.guild.get_member(ctx.author.id)`.
```python
try:
    member = await ctx.guild.fetch_member(ctx.author.id)
    if not member:
        member = ctx.guild.get_member(ctx.author.id)  # Backup check
    if not member:
        await ctx.send("You must be a member of the same Discord server as the bot to use this command.")
        return
except discord.NotFound:
    await ctx.send("You must be a member of the same Discord server as the bot to use this command.")
    return
except Exception as e:
    await ctx.send("An error occurred while verifying your membership.")
    return
```
This ensures that membership checks are **more reliable** and **prevent false negatives** when validating users.

---

