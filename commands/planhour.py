@commands.command()
async def planhour(self, ctx, *args):
    """Generates a mildly absurd but plausible plan for the next hour based on recent messages.

    Usage:
    `!planhour` → Generates a plan based on **your** recent messages in the current channel.
    `!planhour @User` → Generates a plan based on **@User's** messages in the current channel.
    `!planhour #general` → Generates a plan based on recent messages in **#general**.
    `!planhour @User #general` → Generates a plan for **@User's** messages in **#general**.
    """
    if config.is_forbidden_channel(ctx):
        return

    user = ctx.author  # Default to executing user
    channel = ctx.channel  # Default to current channel

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

    messages = await self.fetch_user_messages(ctx, user=user, channel=channel)
    if not messages:
        await ctx.send(f"No recent messages found for {user.display_name} in {channel.mention}.")
        return

    prompt = f"Based on these recent activities: {messages}, create a humorous but plausible plan for the next hour."

    try:
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a witty AI that humorously extends a user's recent activities into exaggerated but plausible plans."},
                {"role": "user", "content": prompt}
            ],
        )

        plan = response.choices[0].message.content.strip()
        await ctx.send(f"🕒 **Your Next Hour Plan:**\n{plan}")

    except Exception as e:
        config.logger.error(f"Error generating planhour: {e}")
        await ctx.send("An error occurred while planning your next hour.")
