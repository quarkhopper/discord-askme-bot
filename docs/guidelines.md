# Discord AskMe Bot - Design Notes & Guidelines

## Overview
The AskMe bot is a Discord bot designed to facilitate community interactions with a structured command system.
It is built using Python and the discord.py library, hosted on Railway. This document serves as a reference for
ensuring design consistency and efficient synchronization across multiple development environments.


# Bot Architecture

## File Structure
```
discord-askme-bot/
├── config.py
├── main.py
├── Procfile
├── requirements.txt
├── commands/
│   ├── bot_errors.py
│   ├── catchup.py
│   ├── chat.py
│   ├── commands.py
│   ├── dream.py
│   ├── guide.py
│   ├── image.py
│   ├── message_utils.py
│   ├── mood.py
│   ├── nounlib.py
│   ├── planhour.py
│   ├── planlife.py
│   ├── snapshot.py
│   └── talkto.py
├── docs/
│   ├── coml_spec.txt
│   ├── guidelines.coml
│   └── update_strategy.md
```
## Main Components
- main.py: Handles bot initialization, event listening, and command registration.
- config.py: Manages environment variables, tokens, and other settings.
- commands/ directory: Contains individual command implementations, each as a separate module.
- message_utils.py: Provides helper functions for processing Discord messages.
- bot_errors.py: Centralized error handling.


## Bot Initialization Flow
1. Load configuration from config.py.
2. Initialize discord.ext.commands.Bot.
3. Register event listeners and load command cogs.
4. Run the bot using bot.run(TOKEN).


# Command Execution Modes

## DM Mode
- Commands execute without user or channel context.
- Commands that normally default to the current channel will use the bot’s DM history with the user instead.
- Role restrictions do not apply in DM mode.
- Users must be a member of at least one Discord server that the bot is also a member of.
- Useful for:
  - Commands like !chat, which accept a string argument and do not depend on a channel.
  - Commands like !clear, which allow users to manage their own DM history.


## Server Mode
- Commands operate within a Discord server, using the existing rules and restrictions.
- Users must meet the following requirements to use any command in Server Mode:
  - Be a member of the same Discord server as the bot.
  - Have the "Vetted" role assigned to them in that server.
- Commands use the current server channel by default, unless specified otherwise.
- Standard command behaviors apply, including message deletion, DM feedback, and error handling.


# Command Structure

## Commands as Cogs
Commands are implemented as Cogs, which allows modularity and better organization.
Each command file follows a structured format.


## Standard Command Guidelines
- All commands should be defined inside Cogs.
- Use @commands.command() to define commands.
- Implement role restrictions where necessary (see Section 3.2).
- Ensure proper parsing of user and channel arguments (see Section 5.2).
- Include an error handler for each command to ensure smooth user experience.
- All command feedback should be sent as a DM to the user.
- A header message should be sent before command execution, including command name, channel, and timestamp.
- If the DM is successfully sent, delete the original command message.
- If the DM cannot be sent, display an error message in the channel, but do not send the full response there.
- Bot-generated command responses must never be posted in the server channel to prevent clutter.
- Errors should be sent as a DM first, falling back to an error message in the channel if DMs are disabled.
- Role restriction failure messages should also be sent as DMs first, then fallback to the channel if needed.
- All commands must include a usage statement in the docstring, explaining the command syntax and expected arguments.
- The command message should always be deleted immediately before execution begins, regardless of processing time, to keep the server clean.


## OpenAI API Key Handling
- All commands that require OpenAI API access must retrieve the API key from an environment variable.
- The only correct way to initialize an OpenAI client is:
```python
import os
import openai

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```
- Do NOT store the API key directly in config.py or in the command file.
- If the API key is missing, the command should fail gracefully and log an error.


# Common Development Issues & Fixes

## TypeError: object Context can't be used in 'await' expression
@ISSUE
Occurs when mistakenly awaiting a synchronous function like require_role().


@FIX
Remove await from the function call:
```python
if not BotErrors.require_role("Vetted")(ctx):  # Correct usage
    return

Instead of:

if not await BotErrors.require_role("Vetted")(ctx):  # Incorrect usage
    return
```


## Correctly Parsing Optional User and Channel Arguments
@ISSUE
Parsing an optional username and channel name from command arguments can be tricky, leading to incorrect resolutions.


@FIX
Use the following pattern to resolve users and channels:
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

    await ctx.send(f"⚠️ Could not recognize `{arg}` as a valid user or channel.")
    return
```


## Debugging chat.py - Membership Verification
@ISSUE
The bot incorrectly flagged valid server members as not being in the server.


@FIX
Ensure correct fetching of members using fetch_member and backup checks with get_member.


## Preventing Unnecessary DM Sends in DM Mode
@ISSUE
Some commands attempt to send a DM even when they are already executed inside a DM.


@FIX
Check if ctx.channel is already a DM before attempting to send one.


## Commands Throw Errors Instead of Blocking DM Execution
@ISSUE
Commands should not process arguments if they are invalid due to execution in a DM.


@FIX
Use @commands.check() with a static method to prevent argument parsing in an invalid context.