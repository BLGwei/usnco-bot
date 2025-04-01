# USNCO BOT
This discord bot was built to make studying for the [USNCO exam](https://www.acs.org/education/olympiad.html) more fun and interactive
by allowing users to review USNCO questions in a competitive and Science Bowl-styled fashion.

It currently contains a database of `2000+` questions obtained through a Python script.

> [!NOTE]
> This bot is still in development and potentially contains bugs! the `/question` command might be changed to avoid conflict with other bots' commands.

## HOW IT WORKS
Upon calling the `/question` command, the USNCO discord bot sends out a discord embed which contains a random USNCO question in the following format:

### Question ID
+ format : `[Local or National Exam (1 or 2 respectively)] [Exam Year] [Question Number]` eg. a question ID of **1201820** refers to question number
**20** on the **2018** **local** exam.

### Question Contents 
+ parsed with the `pdfplumber` library.

### Time Remaining
+ When a new question is generated, users will get `2 minutes` to "buzz" the question, or attempt to answer it by clicking the "BUZZ!" button. Upon reaching `0 seconds`, users will not
be able to interact with the embed as the buttons will be disabled.
+ If a user "buzzes" before the 2 minutes are up, the embed is updated to allow the user to select an answer choice via buttons. Users will have `5 seconds` to select an answer choice.

### Question Options
+ answer choices A,B,C, and D.

### User Answer and Verdict
+ upon selecting an answer choice, the embed will update to display the answer choice selected along with the verdict.
+ > ❌ Incorrect!
  if the selected answer choice is wrong.
+ > ✅ Correct!
  if the selected answer choice is right.

### Image of the question
+ Each USNCO question in the bot's database has an image associated with it.
+ Obtained through a custom Python script.

### Buttons
+ Upon interaction, the **BUZZ** button will update the embed to remove itself and add 4 new buttons labeled with "A", "B", "C", and "D" for the answer choices.
+ Upon interaction, the **Answer Choice Buttons** will change color. The button corresponding to the correct answer choice will be green. If a wrong answer choice was selected, it's corresponding
button's color will be changed to red. All other answer choice buttons will remain grey.
+ Upon interaction, the **Report** button will prompt the user with a short-response form. Upon detailing an error/complaint and submitting, the response will be logged into a CSV file for manual review.

# FEATURES TO BE IMPLEMENTED
- [x] `/help` command which should send an embed containing the information above, but more brief and concise.
- [x] paramaters to the `/question` command (*eg. Stoich, Thermo, OChem*) to allow for practicing of
certain topics,
- [ ] extension to other exams (*eg USABO, AcDec*)

