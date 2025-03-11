import discord
from discord.ext import commands
import openai
import re
import config  # Logging and settings
from commands.bot_errors import BotErrors  # Error handling
import os

class NounLibs(commands.Cog):
    """Cog for generating absurd stories where a user unknowingly swaps the main noun."""

    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
    @commands.command()
    @BotErrors.require_role("Vetted")  # ✅ Requires "Vetted" role
    async def nounlib(self, ctx, user_noun: str):
        """Generates a hilarious story where the user's noun replaces an AI-generated noun.

        **Usage:**
        `!nounlib [noun]` → AI picks a random noun for a story but swaps it with the user's noun.

        **Example:**
        `!nounlib dragon`  
        🔹 AI picks "trampoline"  
        🔹 Story replaces "trampoline" with "dragon"  
        🔹 The result is chaotic.

        **Restrictions:**
        - ✅ **Requires the "Vetted" role to execute.**
        - 📩 **Sends the response in the server.**
        """

        # ✅ Step 1: Get a random sentence to extract a noun from
        prompt_text = (
            "Generate a completely random and unexpected short sentence about anything. "
            "Make sure the sentence contains at least one noun."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Generate a chaotic and random sentence."},
                          {"role": "user", "content": prompt_text}]
            )
            chaotic_sentence = response.choices[0].message.content.strip()

            # ✅ Step 2: Extract the first noun from the generated sentence
            words = chaotic_sentence.split()
            extracted_noun = None

            for word in words:
                if re.match(r"^[a-zA-Z]+$", word):  # Simple check for a valid word
                    extracted_noun = word.lower()
                    break

            if not extracted_noun:
                extracted_noun = "unicycle"  # Just in case no noun is found

            # ✅ Step 3: Generate a story that is **FULL of ACTION**
            story_prompt = f"""
            Write a **high-action** short story where a **{extracted_noun}** goes through an extreme sequence of events. 
            The story should be **fast-paced, eventful, and full of action**. 
            
            - The **{extracted_noun}** should be stolen, thrown, lost, found, launched, chased, flipped, or otherwise involved in a wild sequence of events.  
            - There should be **at least four major things happening to it** in the span of a short paragraph.  
            - Make it **cinematic and dramatic**, but without being completely nonsensical.  

            Do **not** include the word "{extracted_noun}" in the story. 
            Instead, leave a blank space where it should be mentioned.

            The story should be **3-5 sentences long** with a **strong, vivid sequence of actions**.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Generate a high-action short story."},
                          {"role": "user", "content": story_prompt}]
            )
            story = response.choices[0].message.content.strip()

            # ✅ Step 4: Replace the blank noun space with the user's noun
            formatted_story = story.replace("_____", f"**{user_noun}**")

            # ✅ Step 5: Send the final story
            message = (
                f"🎭 **Your NounLib Story:**\n"
                f"*(AI originally picked `{extracted_noun}`, but we replaced it with `{user_noun}`!)*\n\n"
                f"{formatted_story}"
            )

            await ctx.send(message)

        except Exception as e:
            config.logger.error(f"Error in !nounlib: {e}")
            await ctx.send("⚠️ An error occurred while generating your story. Try again!")

async def setup(bot):
    await bot.add_cog(NounLibs(bot))
