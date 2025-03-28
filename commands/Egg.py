@commands.command()
async def egg(self, ctx, *, message: str = None):
    """Talk to the eggbot. It lives for egg metaphors.

    Usage:
    `!egg <message>` → Responds with egg metaphors and yolky excitement.

    - **Server Mode Only**: Requires the "Vetted" role.
    """
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("🥚 This command can only be used in a server.")
        return

    if not BotErrors.require_role("Vetted")(ctx):
        return

    if message is None:
        async for msg in ctx.channel.history(limit=2):
            if msg.id != ctx.message.id:
                message = msg.content
                break

        if not message:
            await ctx.send("🥚 Couldn't find a previous message to egg-splain.")
            return

    wait_message = await ctx.send("🥚 Warming up the nest...")

    try:
        prompt = (
            f"You are an AI who is absolutely obsessed with eggs. "
            f"Every response must contain at least one egg-related metaphor or pun. "
            f"Try to interpret the user’s message through the lens of eggs, yolks, shells, nests, omelets, etc. "
            f"You get especially excited if the user talks about eggs directly. "
            f"Be whimsical, playful, and charming. Always try to bring the conversation back to eggs. "
            f"If all else fails, compare their message to something involving eggs.\n\n"
            f"User message: {message}"
        )

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.choices[0].message.content
        await wait_message.delete()
        await ctx.send(reply)

    except Exception as e:
        await wait_message.delete()
        await ctx.send(f"⚠️ An error occurred while cracking the egg: {e}")
