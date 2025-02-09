import pdfplumber
import re
import os
import json
from ExamImages import process_all_exams_for_image
from Regex_Patterns import get_footer_patterns, get_usnco_exam_footer_patterns

FOOTER_PATTERNS = get_footer_patterns()
USNCO_EXAM_FOOTER_PATTERNS = get_usnco_exam_footer_patterns()

def infer_superscripts(text):
    # Finds subscripts and changes them to normal numbers
    return re.sub(r"×\s*10\s*([+-]?\d+)", r"× 10^\1", text)

def reformat_hyphen_numbers(text):
    # Reformat patterns like '-8.', ']8.' or 'mol-1.' to prevent them from being misinterpreted as question numbers...

    # Reformat standalone hyphen-number-period patterns
    text = re.sub(r"-(\d+)\.", r"-(\1).", text)

    # Reformat standalone bracket-number-period patterns
    text = re.sub(r"\](\d+)\.", r"](\1).", text)

    # Handle cases like 'mol-1.' or 'kJ mol-1.'
    text = re.sub(r"(\w+)-(\d+)\.", r"\1-(\2).", text)

    return text

def remove_footer_from_option(text):
    # Remove footer text specifically from option D

    return re.sub(FOOTER_PATTERNS['option_footer'], '', text, flags=re.IGNORECASE).strip()

def remove_unwanted_text(text, page_number):
    # Removes instructions and footer text based on known patterns.

    patterns = []

    # page-specific patterns
    if page_number == 3:  # Page 3 instructions
        patterns.append(
            r"DIRECTIONS\s+ When you have selected your answer to each question, blacken the corresponding space on the answer sheet using a soft, #2 pencil\. Make a heavy, full mark, but no stray marks\. If you decide to change an answer, erase the unwanted mark very carefully\.\s+ There is only one correct answer to each question\. Any questions for which more than one response has been blackened will not\s+be counted\.  Your score is based solely on the number of questions you answer correctly\. It is to your advantage to answer every question\."
        )
    # Add footer patterns for odd and even pages
    if page_number % 2 == 1:  # Odd pages
        patterns.append(
            r"Property of ACS USNCO – Not for use as USNCO Local Sectio"
        )
    else:  # Even pages
        patterns.append(
            r"Page \d+ Property of ACS USNCO –"
        )
        patterns.append(r"ot for use as USNCO Local Section Exam after March 31, (200[0-9]|201[0-9]|202[0-2])")
        patterns.append(r"END OF TEST")

    # Remove all matches of these patterns
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    for pattern in USNCO_EXAM_FOOTER_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()



def clean_text_with_removal(page_text, page_number):
    """
    Cleans and standardizes text:
    - Removes instructions and footer text.
    - Infers superscripts for scientific notation.
    - Reformats problematic patterns.
    - Removes unnecessary line breaks and extra spaces.
    - Ensures consistent formatting for parsing.
    """
    # Step 1: Remove unwanted text (instructions and footers)
    text = remove_unwanted_text(page_text, page_number)

    # Step 2: Infer superscripts for scientific notation
    text = infer_superscripts(text)

    # Step 3: Reformat problematic patterns
    text = reformat_hyphen_numbers(text)

    # Step 4: Replace subscript characters with normal digits
    subscript_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    text = text.translate(subscript_map)

    # Step 5: Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # Step 6: Merge lines
    text = re.sub(r"\n(?!\d+\.\s|\(A\)|\(B\)|\(C\)|\(D\))", " ", text)

    # Step 7: Add consistent line breaks for questions and answer options
    text = re.sub(r"(\d+\.\s)", r"\n\1", text)  # Add newline before question numbers
    text = re.sub(r"(\(A\))", r"\n\1", text)    # Add newline before option A
    text = re.sub(r"(\(B\))", r"\n\1", text)    # Add newline before option B
    text = re.sub(r"(\(C\))", r"\n\1", text)    # Add newline before option C
    text = re.sub(r"(\(D\))", r"\n\1", text)    # Add newline before option D

    return text.strip()

def filter_non_questions(text):
    match = re.search(r"(\d+\..+)", text, re.DOTALL)
    return match.group(1) if match else ""

def parse_questions(block):

    # Parses a block of text representing a single question and its options.

    # Match the question number and text up to the options
    question_number_pattern = r"^(?!-)(\d{1,3})\.\s(.+?)(?=\s\(A\))"
    option_pattern = (
        r"\(A\)(.+?)\s*"
        r"\(B\)(.+?)\s*"
        r"\(C\)(.+?)\s*"
        r"\(D\)(.+?)(?=\s*\d+\.\s|$)"
    )

    # Match the question text
    question_match = re.search(question_number_pattern, block, re.DOTALL)
    if not question_match:
        print(f"DEBUG: Question not found in block:\n{block}")
        return None
    
    # Match the options
    options_match = re.search(option_pattern, block, re.DOTALL)
    if not options_match:
        print(f"DEBUG: Options not found for block:\n{block}")
        return None

    # Extract question details
    question_number = question_match.group(1).strip() if question_match else None
    question_text = question_match.group(2).strip() if question_match else None
    options = {
        "A": options_match.group(1).strip() if options_match else None,
        "B": options_match.group(2).strip() if options_match else None,
        "C": options_match.group(3).strip() if options_match else None,
        "D": remove_footer_from_option(options_match.group(4)) if options_match else None,
    }

    return {"number": question_number, "text": question_text, "options": options}

def extract_images_from_bbox(page, bbox):
    # Extracts an image from the given bounding box.

    image = page.within_bbox(bbox).to_image()
    return image

def extract_questions_from_page(page, page_number, left_bbox, right_bbox):

    # Extracts questions and their corresponding images from a single page.

    questions = []
    width = page.width
    height = page.height

    # Extract text from columns
    left_text = page.within_bbox(left_bbox).extract_text(y_tolerance=6) or ""
    right_text = page.within_bbox(right_bbox).extract_text(y_tolerance=6) or ""

    # Clean and merge text
    combined_text = (
        clean_text_with_removal(left_text, page_number)
        + "\n"
        + clean_text_with_removal(right_text, page_number)
    )

    # Use re.finditer() to match all questions and options in the text
    question_pattern = r"(\d{1,3})\.\s.+?(?=\n\d{1,3}\.\s|\Z)"
    matches = re.finditer(question_pattern, combined_text, re.DOTALL)

    for match in matches:
        question_block = match.group(0)  # Extract the matched question block
        parsed_question = parse_questions(question_block)
        if parsed_question:
            questions.append(parsed_question)



    return questions

def extract_questions(pdf_path):
    questions = []
    error_log = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages[2:-1], start=3):
            try:
                page_questions = extract_questions_from_page(page, page_number, 
                    (0, 0, page.width / 2, page.height), 
                    (page.width / 2, 0, page.width, page.height))
                questions.extend(page_questions)
            except Exception as e:
                error_log.append({
                    'page': page_number,
                    'error': str(e)
                })
    
    # Log errors for later review
    if error_log:
        with open('parsing_errors.json', 'w') as f:
            json.dump(error_log, f, indent=4)
    
    return questions

def extract_answer_key(pdf_path):
    answer_key = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[-1].extract_text()
        matches = re.findall(r"(\d+)\.\s([A-D])", text)
        for num, ans in matches:
            answer_key[int(num)] = ans
    return dict(sorted(answer_key.items()))

def associate_questions_with_answers(questions, answer_key):
    # Associates each parsed question with its correct answer using the answer key.

    print(f"DEBUG: Answer Key: {answer_key}")
    
    for question in questions:
        question_number = int(question["number"])  # Convert number to int for consistency
        correct_answer = answer_key.get(question_number)  # Fetch from answer_key
        question["correct_answer"] = correct_answer

        # Debugging output for validation
    print(f"DEBUG: Question {question['number']}: Correct Answer: {question.get('correct_answer')}")

    return questions






def process_all_exams(input_folder, output_folder):
    """
    Process all exam PDFs in a folder, parsing questions and associating answers.

    Args:
        input_folder (str): Path to the folder containing exam PDFs.
        output_folder (str): Path to save parsed question files.
    Returns:
        dict: A dictionary mapping exam file names to their parsed question data.
    """
    exam_results = {}

    for file_name in os.listdir(input_folder):
        if not file_name.endswith(".pdf"):
            continue  # Skip non-PDF files
        
        # Extract exam type and year from the file name
        try:
            base_name = os.path.splitext(file_name)[0]
            parts = base_name.split('-')
            exam_year = int(parts[0])  # Extract year
            exam_type = "local" if "local" in parts else "national"
        except (IndexError, ValueError):
            print(f"Skipping file {file_name}: Invalid naming format.")
            continue

        # Process the exam
        pdf_path = os.path.join(input_folder, file_name)
        questions = extract_questions(pdf_path)
        answer_key = extract_answer_key(pdf_path)
        final_questions = associate_questions_with_answers(questions, answer_key)

        # Save results
        exam_results[file_name] = final_questions
        output_file = os.path.join(output_folder, f"{base_name}_parsed.json")

        # Optionally, save as a JSON file

        with open(output_file, "w") as f:
            json.dump(final_questions, f, indent=4)
        print(f"Saved parsed questions for {file_name} to {output_file}")

    return exam_results

def enrich_question_data_with_images(parsed_questions_folder, image_mapping, output_folder):
    """
    Enrich parsed question JSON data with question IDs and associated image paths.

    Args:
        parsed_questions_folder (str): Path to the folder containing parsed question JSON files.
        image_mapping (dict): Dictionary mapping question IDs to image paths.
        output_folder (str): Path to save the updated JSON files.
    """
    os.makedirs(output_folder, exist_ok=True)

    for json_file in os.listdir(parsed_questions_folder):
        if not json_file.endswith(".json"):
            continue

        # Load the parsed questions
        json_path = os.path.join(parsed_questions_folder, json_file)
        with open(json_path, "r") as f:
            questions = json.load(f)

        # Enrich questions with IDs and image paths
        for question in questions:
            question_type = 1 if "local" in json_file else 2
            question_year = re.search(r"\d{4}", json_file).group()
            question_number = question.get("number", "0")

            # Generate question_id
            question_id = f"{question_type}{question_year}{question_number}"

            # Add image path if available
            if question_id in image_mapping:
                question["question_id"] = question_id
                question["image_path"] = image_mapping[question_id]

        # Save the enriched data
        output_path = os.path.join(output_folder, json_file)
        with open(output_path, "w") as f:
            json.dump(questions, f, indent=4)
        print(f"Updated JSON saved to: {output_path}")


input_folder = "olyexams"  # Folder containing all exam PDFs
output_folder = "parsed_questions"  # Folder to save parsed question results
os.makedirs(output_folder, exist_ok=True)

results = process_all_exams(input_folder, output_folder)
print("Processing complete!")



parsed_questions_folder = "parsed_questions"
output_folder2 = "final_questions"

# Import the image mapping from ExamImages.py
image_mapping = process_all_exams_for_image(input_folder, "output_images")
enrich_question_data_with_images(parsed_questions_folder="parsed_questions", image_mapping=image_mapping, output_folder="final_questions")