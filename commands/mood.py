@commands.command()
@BotErrors.require_role("Vetted")  # ✅ Standardized role requirement
async def mood(self, ctx, *args):
    """Analyze the mood of a specific user or the last 10 messages in the specified channel.
    
    **Usage:**
    `!mood` → Analyzes the current channel.
    `!mood @User` → Analyzes @User's messages in the current channel.
    `!mood #general` → Analyzes messages in #general.
    `!mood @User #general` → Analyzes @User's messages in #general.

    **Restrictions:**
    - ❌ **This command cannot be used in DMs.**
    """

    # ❌ Block DM mode but ensure the user gets feedback
    if isinstance(ctx.channel, discord.DMChannel):
        try:
            await ctx.send("❌ The `!mood` command can only be used in a server.")
        except discord.Forbidden:
            pass  # In case the user has DMs disabled
        return

    # Check if command is in a forbidden channel
    if await BotErrors.check_forbidden_channel(ctx):
        return

    user = None
    channel = ctx.channel  # Default to current channel

    # Resolve optional user and channel arguments
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

    messages = await self.fetch_messages(ctx, user=user, channel=channel)
    if not messages:
        await ctx.send("No messages found for the specified user or channel.")
        return

    prompt = (
        "Analyze the emotions in this conversation and suggest how the participant might be feeling:\n\n" +
        "\n".join(messages) +
        "\n\nGive a concise emotional summary."
    )

    try:
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that analyzes emotions in conversations."},
                {"role": "user", "content": prompt}
            ],
        )
        
        mood_analysis = response.choices[0].message.content.strip()
        config.logger.info(f"Mood analysis result: {mood_analysis}")
        await ctx.send(f"💡 Mood Analysis: {mood_analysis}")

    except Exception as e:
        config.logger.error(f"Error analyzing mood: {e}")
        await ctx.send("An error occurred while analyzing the mood.")
