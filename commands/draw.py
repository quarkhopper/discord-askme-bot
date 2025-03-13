import discord
from discord.ext import commands
import asyncio
import os
import random
import re
from PIL import Image, ImageDraw

class DrawCommand(commands.Cog):
    """Cog for generating an abstract drawing based on a user prompt using structured shape interpretation."""

    def __init__(self, bot):
        self.bot = bot

    def interpret_prompt(self, prompt):
        """Analyze the prompt to extract abstract concepts and map them to shapes and structure."""
        concepts = []
        shapes = []
        colors = ["red", "yellow", "orange", "white", "cyan", "magenta", "lime"]  # Improved contrast

        # Define mappings from concepts to shapes
        concept_mapping = {
            "focus": "circle",
            "unity": "overlapping circles",
            "growth": "expanding rings",
            "stability": "rectangle",
            "strength": "triangle",
            "energy": "lines",
            "chaos": "randomly scattered shapes",
            "balance": "symmetrical elements",
            "connection": "interwoven lines",
            "creativity": "spiral",
            "power": "bold geometric forms",
            "nature": "organic, flowing shapes"
        }

        # Extract words from the prompt that indicate abstract concepts
        for word in re.findall(r'\w+', prompt.lower()):
            if word in concept_mapping:
                concepts.append(word)
                shapes.append(concept_mapping[word])

        # If no specific concepts are found, default to a variety of geometric forms
        if not shapes:
            shapes = random.choices(list(concept_mapping.values()), k=3)

        # Assign colors, ensuring at least one is available
        selected_colors = random.choices(colors, k=max(1, len(shapes)))

        return concepts, shapes, selected_colors

    def generate_drawing(self, prompt):
        """Generate an image using structured shape placement based on prompt analysis."""
        width, height = 512, 512
        image = Image.new("RGB", (width, height), "black")  # Black background
        draw = ImageDraw.Draw(image)

        concepts, shapes, colors = self.interpret_prompt(prompt)

        for i, shape in enumerate(shapes):
            color = colors[i % len(colors)]  # Cycle colors safely

            if shape == "circle":
                r = random.randint(30, 100)
                x, y = random.randint(r, width - r), random.randint(r, height - r)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline="white")

            elif shape == "overlapping circles":
                r = random.randint(30, 80)
                x, y = random.randint(r, width - r), random.randint(r, height - r)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline="white")
                draw.ellipse([x + 20, y - r, x + 20 + r, y + r], fill=color, outline="white")

            elif shape == "rectangle":
                w, h = random.randint(50, 150), random.randint(50, 150)
                x1, y1 = random.randint(0, width - w), random.randint(0, height - h)
                x2, y2 = x1 + w, y1 + h
                draw.rectangle([x1, y1, x2, y2], fill=color, outline="white")

            elif shape == "triangle":
                x1, y1 = random.randint(50, width - 50), random.randint(50, height - 50)
                x2, y2 = x1 + random.randint(-50, 50), y1 + random.randint(50, 100)
                x3, y3 = x1 + random.randint(-50, 50), y1 - random.randint(50, 100)
                draw.polygon([x1, y1, x2, y2, x3, y3], fill=color, outline="white")

            elif shape == "lines":
                for _ in range(random.randint(2, 5)):
                    x1, y1 = random.randint(0, width), random.randint(0, height)
                    x2, y2 = random.randint(0, width), random.randint(0, height)
                    draw.line([x1, y1, x2, y2], fill=color, width=3)

            elif shape == "spiral":
                cx, cy = random.randint(100, width - 100), random.randint(100, height - 100)
                r = 5
                for j in range(10):
                    x1, y1 = cx - r, cy - r
                    x2, y2 = cx + r, cy + r
                    draw.arc([x1, y1, x2, y2], start=0, end=360, fill=color)
                    r += 10

        # Save the image
        file_path = "drawing.png"
        image.save(file_path)
        return file_path, concepts, shapes, colors

    @commands.command()
    async def draw(self, ctx, *, prompt: str):
        """Generates a structured abstract drawing based on the user's conceptual prompt.
        
        **Usage:**
        `!draw a symbol of unity and balance` → Generates an abstract representation of those themes.
        """

        is_dm = isinstance(ctx.channel, discord.DMChannel)

        # Enforce role restriction in server mode
        if not is_dm:
            role = discord.utils.get(ctx.author.roles, name="Vetted")
            if not role:
                await ctx.send("⚠️ You must have the 'Vetted' role to use this command.")
                return

        # Acknowledge command execution
        please_wait = await ctx.send(f"⏳ Creating a structured drawing based on: `{prompt}`. Please wait...")

        # Delete the original command message in server mode
        if not is_dm:
            try:
                await ctx.message.delete()
            except discord.NotFound:
                pass  # Message already deleted

        # Generate the drawing
        file_path, concepts, shapes, colors = self.generate_drawing(prompt)

        # Delete "Please wait..." message
        await please_wait.delete()

        # Generate a description of what was drawn
        description = "🖌️ **Drawing Interpretation:**\n"
        if concepts:
            description += f"Based on your prompt, I interpreted the themes of `{', '.join(concepts)}` and represented them using:\n"
        else:
            description += "I generated abstract shapes based on the given prompt:\n"

        for i, shape in enumerate(shapes):
            description += f"- A `{shape}` filled with `{colors[i % len(colors)]}`.\n"

        # Send the image as a file
        with open(file_path, "rb") as file:
            drawing_file = discord.File(file, filename="drawing.png")
            embed = discord.Embed(title="🎨 AI-Generated Concept Drawing", description=description, color=discord.Color.blue())
            embed.set_image(url="attachment://drawing.png")
            await ctx.send(file=drawing_file, embed=embed)

        # Clean up the file
        os.remove(file_path)

# ✅ Set this command to work in both server and DM mode
async def setup(bot):
    await bot.add_cog(DrawCommand(bot))
    command = bot.get_command("draw")
    if command:
        command.command_mode = "both"
