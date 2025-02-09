import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import os
import json
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import datetime
import csv
from discord import ui
from discord.interactions import Interaction

@dataclass
class Question:
    text: str
    options: Dict[str, str]
    correct_answer: str
    number: str
    question_id: Optional[str] = None
    image_path: Optional[str] = None
    
    @property
    def exam_type(self) -> str:
        if not self.question_id:
            return "Unknown"
        return "Local" if self.question_id[0] == "1" else "National"
    
    @property
    def exam_year(self) -> str:
        if not self.question_id:
            return "Unknown"
        return self.question_id[1:5]
    
    @classmethod
    def from_json(cls, data: dict) -> 'Question':
        cleaned_data = {
            'text': data.get('text', ''),
            'options': data.get('options', {}),
            'correct_answer': data.get('correct_answer', ''),
            'number': str(data.get('number', '')),
            'question_id': data.get('question_id'),
            'image_path': data.get('image_path')
        }
        return cls(**cleaned_data)

class ReportModal(ui.Modal, title="Report Question Error"):
    error_description = ui.TextInput(
        label="Please describe the error",
        style=discord.TextStyle.paragraph,
        placeholder="What's wrong with this question?",
        required=True,
        max_length=1000
    )

    def __init__(self, question: Question, parent_view: discord.ui.View):
        super().__init__()
        self.question = question
        self.parent_view = parent_view

    async def on_submit(self, interaction: Interaction):
        try:
            await interaction.response.defer()
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report_data = {
                'timestamp': timestamp,
                'user_name': str(interaction.user),
                'user_id': str(interaction.user.id),
                'question_id': self.question.question_id,
                'exam_type': self.question.exam_type,
                'exam_year': self.question.exam_year,
                'question_number': self.question.number,
                'error_description': self.error_description.value
            }
            
            await self.log_report(report_data)
            
            # Stop the timer if it's running
            if hasattr(self.parent_view, 'timer_task') and self.parent_view.timer_task:
                self.parent_view.stop_timer()
            
            # Create a new embed with the same data
            old_embed = interaction.message.embeds[0]
            new_embed = discord.Embed(
                title=old_embed.title,
                description=old_embed.description
            )
            
            # Copy over the non-status fields
            for field in old_embed.fields:
                if field.name != "Status":
                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
            
            # Add the report notification field
            new_embed.add_field(
                name="Status",
                value="⚠️ This question has been reported and disabled.",
                inline=False
            )
            
            # Create a new view with disabled buttons
            combined_view = discord.ui.View()
            
            # Add all original buttons (disabled)
            for item in self.parent_view.children:
                if isinstance(item, Button) and not isinstance(item, ReportButton):
                    new_button = Button(
                        style=item.style,
                        label=item.label,
                        disabled=True
                    )
                    combined_view.add_item(new_button)
            
            # Add new question button
            bot = interaction.client
            new_question_view = NewQuestionView(bot)
            for item in new_question_view.children:
                combined_view.add_item(item)
            
            # Edit the original message
            await interaction.message.edit(embed=new_embed, view=combined_view)
            
            # Send confirmation as followup
            await interaction.followup.send(
                "Thank you for your report! This question has been disabled and we'll review it as soon as possible.",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error in report submission: {str(e)}")
            await interaction.followup.send(
                f"An error occurred while processing your report: {str(e)}",
                ephemeral=True
            )
                
    async def log_report(self, report_data: dict):
        os.makedirs('reports', exist_ok=True)
        file_path = 'reports/error_reports.csv'
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=report_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(report_data)

class ReportButton(ui.Button):
    def __init__(self, question: Question, parent_view: discord.ui.View):
        super().__init__(
            label="Report Error",
            style=discord.ButtonStyle.danger,
            custom_id="report_error"
        )
        self.question = question
        self.parent_view = parent_view  # Changed from self.view to self.parent_view

    async def callback(self, interaction: Interaction):
        modal = ReportModal(self.question, self.parent_view)  # Use parent_view here
        await interaction.response.send_modal(modal)

# Update the NewQuestionView to include the report button
class NewQuestionView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.add_new_question_button()
        
    def add_new_question_button(self):
        button = Button(
            label="New USNCO Question",
            style=discord.ButtonStyle.primary,
            custom_id="new_question"
        )
        
        async def button_callback(interaction: discord.Interaction):
            await self.handle_new_question(interaction)
        
        button.callback = button_callback
        self.add_item(button)
    
    async def handle_new_question(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        quiz_cog = self.bot.get_cog('QuizCommands')
        if not quiz_cog:
            await interaction.followup.send("❌ Failed to load quiz commands.", ephemeral=True)
            return
            
        # Get a random question directly
        if not quiz_cog.bot.questions:
            await interaction.followup.send("No questions available.", ephemeral=True)
            return
            
        question = random.choice(quiz_cog.bot.questions)
        embed = quiz_cog._create_question_embed(question)
        view = BuzzView(question)
        
        # Send the message and get the reference
        if question.image_path:
            file = discord.File(
                question.image_path,
                filename=os.path.basename(question.image_path)
            )
            message = await interaction.followup.send(
                embed=embed,
                file=file,
                view=view,
                wait=True  # Make sure to wait for the message
            )
        else:
            message = await interaction.followup.send(
                embed=embed,
                view=view,
                wait=True  # Make sure to wait for the message
            )
        
        # Important: Set the message property on the view
        view.message = message
        
        # Cancel any existing timer before starting a new one
        if hasattr(view, 'timer_task') and view.timer_task:
            view.timer_task.cancel()
        
        # Start the new timer
        view.timer_task = asyncio.create_task(view.start_timer())
            
class TimedView(View):
    def __init__(self, timeout=120):
        super().__init__(timeout=timeout)
        self.message: Optional[discord.Message] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.remaining_time = timeout
        self.timer_running = True
        self.update_interval = 1  # Default update interval in seconds
    
    async def start_timer(self):
        try:
            while self.timer_running and self.remaining_time > 0:
                await asyncio.sleep(self.update_interval)
                self.remaining_time -= self.update_interval
                if self.message and self.timer_running:
                    embed = self.message.embeds[0]
                    self.update_timer_field(embed)
                    await self.message.edit(embed=embed)
            
            if self.timer_running:  # If we reached 0 naturally
                await self.handle_timeout()
        except Exception as e:
            print(f"Timer error: {e}")

    def update_timer_field(self, embed: discord.Embed):
        timer_field_index = None
        for i, field in enumerate(embed.fields):
            if field.name == "Time Remaining":
                timer_field_index = i
                break
        
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        timer_text = f"`{minutes}:{seconds:02d}`"
        
        if timer_field_index is not None:
            embed.set_field_at(timer_field_index, name="Time Remaining", value=timer_text, inline=True)
        else:
            embed.add_field(name="Time Remaining", value=timer_text, inline=True)

    async def handle_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            embed = self.message.embeds[0]
            embed.add_field(name="Status", value="⏰ Time's up!", inline=False)

            bot = self.message._state._get_client()  # Dynamically get bot instance
            new_question_view = NewQuestionView(bot)
            await self.message.edit(embed=embed, view=new_question_view)

        self.stop()

    def stop_timer(self):
        self.timer_running = False
        if self.timer_task:
            self.timer_task.cancel()

class BuzzView(TimedView):
    def __init__(self, question: Question):
        super().__init__(timeout=120)
        self.question = question
        self.add_buzz_button()
        self.add_item(ReportButton(question, self))
    
    def add_buzz_button(self):
        buzz_button = Button(
            label="BUZZ!",
            style=discord.ButtonStyle.success,
            custom_id="buzz"
        )
        buzz_button.callback = self.handle_buzz
        self.add_item(buzz_button)
    
    async def handle_buzz(self, interaction: discord.Interaction):
        self.stop_timer()
        
        embed = interaction.message.embeds[0]
        
        # Update timer field to show 5 seconds
        timer_field_index = None
        for i, field in enumerate(embed.fields):
            if field.name == "Time Remaining":
                timer_field_index = i
                break
        
        if timer_field_index is not None:
            embed.set_field_at(timer_field_index, name="Time Remaining", value="`0:05`", inline=True)
        else:
            embed.add_field(name="Time Remaining", value="`0:05`", inline=True)
        
        # Add the options to the embed
        for option, text in self.question.options.items():
            embed.add_field(name=f"Option {option}", value=text, inline=False)
        
        # Switch to answer choice view
        answer_view = QuestionView(self.question, timeout=5)
        answer_view.message = interaction.message
        answer_view.remaining_time = 5
        answer_view.update_interval = 1
        
        await interaction.response.edit_message(embed=embed, view=answer_view)
        
        answer_view.timer_task = asyncio.create_task(answer_view.start_timer())
    
    async def handle_timeout(self):
        if self.message:
            # Disable the BUZZ button but keep it visible
            for item in self.children:
                item.disabled = True
                if isinstance(item, Button):
                    item.style = discord.ButtonStyle.secondary  # Grey out the button
            
            embed = self.message.embeds[0]
            
            # Add timeout message with the correct answer
            embed.add_field(
                name="Status", 
                value=f"⏰ Time's up! The correct answer was **{self.question.correct_answer}**", 
                inline=False
            )
            
            # Add the options to the embed
            for option, text in self.question.options.items():
                embed.add_field(name=f"Option {option}", value=text, inline=False)
            
            # Color the correct answer button
            for item in self.children:
                if isinstance(item, Button):
                    item.disabled = True
                    if item.label == self.question.correct_answer:
                        item.style = discord.ButtonStyle.success

            bot = self.message._state._get_client()
            new_question_view = NewQuestionView(bot)
            
            # Combine the disabled original view with the new question button
            combined_view = discord.ui.View()
            for item in self.children:
                combined_view.add_item(item)
            for item in new_question_view.children:
                combined_view.add_item(item)
            
            await self.message.edit(embed=embed, view=combined_view)

        self.stop()

class QuestionView(TimedView):
    def __init__(self, question: Question, timeout=120):
        super().__init__(timeout=timeout)
        self.question = question
        self.answer_selected = False
        self._create_buttons()
        self.add_item(ReportButton(question, self))
    
    def _create_buttons(self):
        for option in ["A", "B", "C", "D"]:
            button = Button(
                label=option,
                style=discord.ButtonStyle.secondary,
                custom_id=f"option_{option.lower()}"
            )
            button.callback = lambda i, opt=option: self.handle_response(i, opt)
            self.add_item(button)
            
    async def handle_response(self, interaction: discord.Interaction, selected_option: str):
        if self.answer_selected:
            return

        self.answer_selected = True
        self.stop_timer()
        correct_answer = self.question.correct_answer
        is_correct = selected_option == correct_answer
        
        # Update button colors
        for child in self.children:
            if isinstance(child, Button) and not isinstance(child, ReportButton):  # Don't disable report button
                if child.label == correct_answer:
                    child.style = discord.ButtonStyle.success
                elif child.label == selected_option and not is_correct:
                    child.style = discord.ButtonStyle.danger
                child.disabled = True

        embed = interaction.message.embeds[0]
        verdict = "✅ Correct!" if is_correct else f"❌ Incorrect! The correct answer was **{correct_answer}**"
        
        embed.add_field(name="Your Answer", value=selected_option, inline=True)
        embed.add_field(name="Verdict", value=verdict, inline=True)
        
        # Add new question button
        bot = interaction.client
        new_question_view = NewQuestionView(bot)
        
        # Combine the disabled answer buttons with the new question button
        combined_view = discord.ui.View()
        for item in self.children:
            combined_view.add_item(item)
        for item in new_question_view.children:
            combined_view.add_item(item)
        
        await interaction.response.edit_message(embed=embed, view=combined_view)

    async def handle_timeout(self):
        if self.message:
            correct_answer = self.question.correct_answer
            
            # Update button colors and disable them
            for child in self.children:
                if isinstance(child, Button):  # Don't disable report button
                    child.disabled = True
                    if child.label == correct_answer:
                        child.style = discord.ButtonStyle.success
            
            embed = self.message.embeds[0]
            embed.add_field(
                name="Status", 
                value=f"⏰ Time's up! The correct answer was **{correct_answer}**.", 
                inline=False
            )

            # Add new question button
            bot = self.message._state._get_client()
            new_question_view = NewQuestionView(bot)
            
            # Combine the disabled answer buttons with the new question button
            combined_view = discord.ui.View()
            for item in self.children:
                combined_view.add_item(item)
            for item in new_question_view.children:
                combined_view.add_item(item)
            
            await self.message.edit(embed=embed, view=combined_view)

        self.stop()

class USNCOQuizBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.questions: List[Question] = []
        
    async def setup_hook(self):
        print(f"Current working directory: {os.getcwd()}")  # Debug: Print current directory
        self.questions = self._load_questions("final_questions")
        print(f"Loaded {len(self.questions)} questions")  # Debug: Print number of questions loaded
        await self.tree.sync()
        
    def _load_questions(self, folder: str) -> List[Question]:
        questions = []
        try:
            print(f"Attempting to load questions from folder: {folder}")  # Debug: Print folder path
            files = os.listdir(folder)
            print(f"Found {len(files)} files in folder")  # Debug: Print number of files found
            
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(folder, file)
                    print(f"Processing file: {file_path}")  # Debug: Print each file being processed
                    try:
                        with open(file_path, "r", encoding='utf-8') as f:
                            questions_data = json.load(f)
                            print(f"Found {len(questions_data)} questions in {file}")  # Debug: Print questions found in file
                            for q in questions_data:
                                try:
                                    question = Question.from_json(q)
                                    questions.append(question)
                                except Exception as e:
                                    print(f"Error parsing question in {file}: {e}")
                    except Exception as e:
                        print(f"Error reading file {file}: {e}")
        except Exception as e:
            print(f"Error accessing folder {folder}: {e}")
        
        print(f"Total questions loaded: {len(questions)}")  # Debug: Print final count
        return questions
    async def on_ready(self):
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name='USNCO Practice'
        )
        await self.change_presence(activity=activity)
        print(f"{self.user} is ready! Loaded {len(self.questions)} questions.")

class QuizCommands(commands.Cog):
    def __init__(self, bot: USNCOQuizBot):
        self.bot = bot

    @app_commands.command(name="question", description="Get a random USNCO practice question")
    async def question(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.bot.questions:
            await interaction.followup.send("No questions available.")
            return

        question = random.choice(self.bot.questions)
        embed = self._create_question_embed(question)
        view = BuzzView(question)
        
        if question.image_path:
            if not os.path.exists(question.image_path):
                await interaction.followup.send("Error: Question image not found.")
                return
                
            file = discord.File(
                question.image_path,
                filename=os.path.basename(question.image_path)
            )
            message = await interaction.followup.send(
                embed=embed,
                file=file,
                view=view,
                wait=True
            )
        else:
            message = await interaction.followup.send(
                embed=embed,
                view=view,
                wait=True
            )
        
        view.message = message
        view.timer_task = asyncio.create_task(view.start_timer())
        
    def _create_question_embed(self, question: Question) -> discord.Embed:
        embed = discord.Embed(
            title=f"Question ID: `{question.question_id or 'Unknown'}`",
            description=(
                f"**Exam Type:** `{question.exam_type}`\n"
                f"**Year:** `{question.exam_year}`\n"
                f"**Question Number:** `{question.number}`\n\n"
                f"{question.text}"
            )
        )

        if question.image_path:
            embed.set_image(url=f"attachment://{os.path.basename(question.image_path)}")
        
        # Add initial timer field
        embed.add_field(name="Time Remaining", value="2:00", inline=True)
        
        return embed

async def main():
    bot = USNCOQuizBot()
    async with bot:
        await bot.add_cog(QuizCommands(bot))
        token = os.getenv('BOTTOKEN')
        if not token:
            try:
                from apikeys import BOTTOKEN
                token = BOTTOKEN
            except ImportError:
                raise ValueError("Bot token not found in environment variables or apikeys.py")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())