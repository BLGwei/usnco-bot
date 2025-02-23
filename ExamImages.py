import pymupdf 
from PIL import Image
import os
import json
import re
import pdfplumber
from Regex_Patterns import get_footer_patterns, get_usnco_exam_footer_patterns
from Image_Validator import validate_question_images, generate_validation_report

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

    # Parses a block of text representing a single question and its options

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
        "D": options_match.group(4).strip() if options_match else None,
    }

    return {"number": question_number, "text": question_text, "options": options}


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

def close_gaps_between_bounding_boxes(blocks, gap_threshold=0):
    """
    Adjust bounding boxes to close significant gaps between them.

    Args:
        blocks (list): List of text blocks, each a tuple containing:
                       (x0, y0, x1, y1, text, block_no, page_no).
        gap_threshold (float): The maximum allowable gap between bounding boxes.
    Returns:
        list: List of adjusted bounding boxes.
    """
    adjusted_blocks = []
    for i, block in enumerate(blocks):
        if ValueError:
            pass
        x0, y0, x1, y1, text, block_no, page_no = block

        # If this is not the last block, check the gap with the next block
        if i < len(blocks) - 1:
            next_y0 = blocks[i + 1][1]  # y0 of the next block
            gap = next_y0 - y1  # Calculate the gap
            if y1 > 650:
                y1 += 35
            # If the gap exceeds the threshold, close it by extending the y2
            if gap > gap_threshold:
                y1 += 31 - gap  # Adjust y1 to close the gap
        
        
        # Append the adjusted block to the list
        adjusted_blocks.append((x0, y0, x1, y1 - 10, text, block_no, page_no))
    
    return adjusted_blocks

def adjust_x1_based_on_center(blocks, center_threshold=25, page_center=310, second_page_right = 700):
    """
    Adjust x1 coordinates based on distance from the center of the page, only for the left column.

    Args:
        blocks (list): List of text blocks, each a tuple containing:
                       (x0, y0, x1, y1, text, block_no, page_no).
        center_threshold (float): Maximum allowed distance from the page center.
        page_center (float): x-coordinate of the center of the page.
    Returns:
        list: List of adjusted bounding boxes.
    """
    adjusted_blocks = []
    
    for block in blocks:
        try:
            x0, y0, x1, y1, text, block_no, page_no = block
            
            # Check if the block belongs to the left column
            if page_center is not None and x0 < page_center:
                if abs(x1 - page_center) > center_threshold:
                    x1 = page_center  # Adjust x1 to the center of the page
            
            if page_center is not None and x0 > page_center:
                x1 = second_page_right
            
            # Append the adjusted block to the list
            adjusted_blocks.append((x0, y0, x1, y1, text, block_no, page_no))
        except ValueError as e:
            print(f"Skipping block due to unpacking error: {block} | Error: {e}")
            continue  # Skip this block and proceed to the next
    
    return adjusted_blocks



import pymupdf  # PyMuPDF
def is_bottom_question(blocks, current_block_index, page_height, threshold=50):
    """
    Determine if this is the last question on the page.
    """
    current_block = blocks[current_block_index]
    if not current_block:
        return False
        
    next_question_y = find_next_question_start(blocks, current_block_index)
    if next_question_y is None:
        return (page_height - current_block[3]) < threshold
    return False

def adjust_bounding_boxes(blocks, page_height):
    """
    Adjust bounding boxes to extend to the start of the next question.
    """
    adjusted_blocks = []
    question_pattern = r"^(?!-)(\d{1,3})\.\s"
    
    for i, block in enumerate(blocks):
        if not block:  # Skip empty blocks
            continue
            
        x0, y0, x1, y1, text, block_no, page_no = block
        
        if re.match(question_pattern, text.strip()):
            if is_bottom_question(blocks, i, page_height):
                adjusted_blocks.append(block)
                continue
                
            next_y = find_next_question_start(blocks, i)
            if next_y is not None:
                new_y1 = next_y - 18  # 5 pixel padding
                adjusted_blocks.append((x0, y0, x1, new_y1, text, block_no, page_no))
            else:
                adjusted_blocks.append(block)
        else:
            adjusted_blocks.append(block)
    
    return adjusted_blocks

def find_next_question_start(blocks, current_block_index):
    """
    Find the y-coordinate where the next question starts.
    """
    question_pattern = r"^(?!-)(\d{1,3})\.\s"
    current_block = blocks[current_block_index]
    current_x0 = current_block[0]  # Get x-coordinate of current block
    page_center = 310  # Approximate center of page
    
    # Determine if we're in left or right column
    in_left_column = current_x0 < page_center
    
    for i in range(current_block_index + 1, len(blocks)):
        if not blocks[i]:  # Skip empty blocks
            continue
            
        next_block = blocks[i]
        next_x0 = next_block[0]
        next_in_left = next_x0 < page_center
        
        # Only look for next question in same column
        if in_left_column != next_in_left:
            continue
            
        text = next_block[4].strip()
        if re.match(question_pattern, text):
            # Add debug output
            print(f"Found next question: {text}")
            print(f"Current question y1: {current_block[3]}")
            print(f"Next question y0: {next_block[1]}")
            return next_block[1]  # Return y0 of the next question
    return None

def adjust_bounding_boxes(blocks, page_height):
    """
    Adjust bounding boxes to extend to the start of the next question.
    """
    adjusted_blocks = []
    question_pattern = r"^(?!-)(\d{1,3})\.\s"
    page_center = 310  # Approximate center of page
    
    # First pass: identify all question blocks and their columns
    question_blocks = []
    for i, block in enumerate(blocks):
        if not block:  # Skip empty blocks
            continue
            
        text = block[4].strip()
        if re.match(question_pattern, text):
            x0 = block[0]
            in_left_column = x0 < page_center
            question_blocks.append((i, block, in_left_column))
    
    # Second pass: adjust blocks with awareness of column structure
    for i, block in enumerate(blocks):
        if not block:  # Skip empty blocks
            continue
            
        x0, y0, x1, y1, text, block_no, page_no = block
        
        if re.match(question_pattern, text.strip()):
            in_left_column = x0 < page_center
            
            if is_bottom_question(blocks, i, page_height):
                # For bottom questions, keep original block but ensure proper height
                if y1 > page_height - 50:  # Adjust if too close to bottom
                    y1 = page_height - 50
                adjusted_blocks.append((x0, y0, x1, y1, text, block_no, page_no))
                continue
                
            next_y = find_next_question_start(blocks, i)
            if next_y is not None:
                # Add more padding (10 pixels) to ensure separation
                new_y1 = next_y - 10
                
                # Ensure we're not creating an invalid bounding box
                if new_y1 > y0:
                    adjusted_blocks.append((x0, y0, x1, new_y1, text, block_no, page_no))
                else:
                    # If invalid, keep original
                    adjusted_blocks.append(block)
                    print(f"Warning: Invalid bounding box prevented for question in block {i}")
            else:
                # If no next question found, use original block
                adjusted_blocks.append(block)
        else:
            # Non-question blocks remain unchanged
            adjusted_blocks.append(block)
    
    return adjusted_blocks

def save_individual_question_images_with_ids(pdf_path, output_folder, exam_type, exam_year):
    """
    Modified version with additional debugging and validation.
    """
    question_number_pattern = r"^(?!-)(\d{1,3})\.\s"
    option_regex = r"\(A\)|\(B\)|\(C\)|\(D\)"
    question_images = {}

    with pymupdf.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf):
            if page_index == 0 or page_index == 1 or page_index == len(pdf) - 1:
                continue
            
            page_height = page.rect.height
            blocks = page.get_text("blocks")
            
            # Add debug output for blocks
            print(f"\nProcessing page {page_index + 1}")
            
            blocks = adjust_x1_based_on_center(blocks)
            blocks = adjust_bounding_boxes(blocks, page_height)
            adjusted_blocks = close_gaps_between_bounding_boxes(blocks)

            current_question_bbox = None
            current_question_text = ""
            
            for block in adjusted_blocks:
                if not block:
                    continue
                    
                text = block[4].strip()
                bbox = pymupdf.Rect(*block[:4])

                if re.match(question_number_pattern, text):
                    if current_question_bbox:
                        # Save previous question
                        question_id = f"{exam_type}{exam_year}{current_question_text.split('.')[0].strip()}"
                        save_path = os.path.join(output_folder, f"{question_id}.png")
                        
                        # Add debug output for bounding box
                        print(f"\nSaving question {question_id}")
                        print(f"Bounding box: {current_question_bbox}")
                        
                        save_image_from_bbox(page, current_question_bbox, save_path)
                        question_images[question_id] = save_path
                    
                    current_question_bbox = bbox
                    current_question_text = text
                    continue
                
                if current_question_bbox:
                    current_question_bbox = current_question_bbox.include_rect(bbox)
                    current_question_text += " " + text

            # Handle last question on page
            if current_question_bbox:
                question_id = f"{exam_type}{exam_year}{current_question_text.split('.')[0].strip()}"
                save_path = os.path.join(output_folder, f"{question_id}.png")
                save_image_from_bbox(page, current_question_bbox, save_path)
                question_images[question_id] = save_path

    return question_images

def save_image_from_bbox(page, bbox, save_path, dpi=300):
    """
    Save a cropped image of the specified bounding box.

    Args:
        page: The page from which to crop the image.
        bbox: Bounding box to crop.
        save_path (str): Path to save the cropped image.
        dpi (int): Resolution of the output image.
    """
    # Ensure bounding box is within page bounds
    page_width, page_height = page.rect.width, page.rect.height
    x0, y0, x1, y1 = bbox

    # Clamp bounding box coordinates
    x0 = max(0, min(x0, page_width))
    y0 = max(0, min(y0, page_height))
    x1 = max(0, min(x1, page_width))
    y1 = max(0, min(y1, page_height))

    # If the bounding box is invalid after clamping, skip it
    if x0 >= x1 or y0 >= y1:
        print(f"Skipping invalid bounding box: {bbox}")
        return

    # Render only the specified bounding box
    pix = page.get_pixmap(dpi=dpi, clip=(x0, y0, x1, y1))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Save the image
    img.save(save_path)
    print(f"Saved question image to: {save_path}")

def process_all_exams_for_image(input_folder, output_folder):
    """
    Process all exam PDFs in a given folder and classify them as local or national.

    Args:
        input_folder (str): Path to the folder containing exam PDFs.
        output_folder (str): Path to save question images.
    Returns:
        dict: A dictionary mapping question IDs to image paths.
    """
    exam_mappings = {}

    for file_name in os.listdir(input_folder):
        if not file_name.endswith(".pdf"):
            continue

        # Determine exam type based on the file name
        exam_type = 1 if "local" in file_name.lower() else 2 if "national" in file_name.lower() else 0
        if exam_type == 0:
            print(f"Skipping file {file_name}: Unable to determine exam type (local or national).")
            continue

        # Extract the year from the file name
        try:
            exam_year = int(re.search(r"\d{4}", file_name).group())
        except AttributeError:
            print(f"Skipping file {file_name}: Unable to extract year.")
            continue

        # Process each exam and save images
        pdf_path = os.path.join(input_folder, file_name)
        base_name = os.path.splitext(file_name)[0]
        exam_output_folder = os.path.join(output_folder, base_name)
        os.makedirs(exam_output_folder, exist_ok=True)

        # Generate question images and IDs
        question_images = save_individual_question_images_with_ids(
            pdf_path, exam_output_folder, exam_type, exam_year
        )
        exam_mappings.update(question_images)  # Combine mappings
    return exam_mappings



if __name__ == "__main__":
    input_folder = "olyexams"
    output_folder = "output_images"
    image_mapping = process_all_exams_for_image(input_folder, output_folder)

results = validate_question_images("D:\Downloads\discord bot\output_images")

# Generate detailed report
generate_validation_report(results)


