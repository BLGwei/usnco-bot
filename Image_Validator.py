import os
import pytesseract
from PIL import Image
import re
from collections import defaultdict

def validate_question_images(image_folder):
    """
    Validates question images by checking:
    1. If the question number in the image matches the filename
    2. If the image contains all 4 options (A, B, C, D)
    3. If the image dimensions are within expected ranges
    4. If the text content meets minimum length requirements
    
    Args:
        image_folder (str): Path to folder containing question images
        
    Returns:
        dict: Dictionary of potentially problematic images and their issues
    """
    issues = defaultdict(list)
    
    # Expected patterns
    question_pattern = r"^\d{1,2}\."  # Matches question numbers like "1.", "2.", etc.
    option_pattern = r"\([A-D]\)"     # Matches (A), (B), (C), (D)
    
    # Reasonable dimension ranges (adjust based on your needs)
    MIN_WIDTH = 300
    MAX_WIDTH = 3000
    MIN_HEIGHT = 100
    MAX_HEIGHT = 2000
    MIN_TEXT_LENGTH = 25  # Minimum characters expected in a complete question
    
    for filename in os.listdir(image_folder):
        if not filename.endswith('.png'):
            continue
            
        filepath = os.path.join(image_folder, filename)
        
        try:
            # Extract expected question number from filename
            expected_num = re.search(r'\d{6}(\d+)', filename).group(1)
            
            # Open and check image dimensions
            with Image.open(filepath) as img:
                width, height = img.size
                
                if width < MIN_WIDTH or width > MAX_WIDTH:
                    issues[filename].append(f"Unusual width: {width}px")
                if height < MIN_HEIGHT or height > MAX_HEIGHT:
                    issues[filename].append(f"Unusual height: {height}px")
                
                # Extract text from image
                text = pytesseract.image_to_string(img)
                
                # Check for minimum text length
                if len(text) < MIN_TEXT_LENGTH:
                    issues[filename].append(f"Text too short ({len(text)} chars)")
                
                # Validate question number
                found_numbers = re.findall(question_pattern, text)
                if not found_numbers:
                    issues[filename].append("No question number found")
                else:
                    question_num = found_numbers[0].replace('.', '')
                    if question_num != expected_num:
                        issues[filename].append(
                            f"Question number mismatch: expected {expected_num}, found {question_num}"
                        )
                
                # Check for all options
                options = re.findall(option_pattern, text)
                if len(options) != 4:
                    issues[filename].append(
                        f"Missing options: found {len(options)}/4 options"
                    )
                    
                # Check for truncated text indicators
                if any(indicator in text.lower() for indicator in ['...', '…', 'cont']):
                    issues[filename].append("Possible truncated text detected")
                    
                # Check text distribution
                lines = text.split('\n')
                if len(lines) < 4:
                    issues[filename].append("Too few lines of text")
                    
                # Calculate text density
                text_density = len(text) / (width * height)
                if text_density < 0.0001:  # Adjust threshold as needed
                    issues[filename].append("Low text density - possible blank areas")
                
        except Exception as e:
            issues[filename].append(f"Error processing image: {str(e)}")
    
    return dict(issues)

def generate_validation_report(validation_results, output_file='validation_report.txt'):
    """
    Generates a detailed report of validation issues.
    
    Args:
        validation_results (dict): Results from validate_question_images
        output_file (str): Path to save the report
    """
    with open(output_file, 'w') as f:
        f.write("Question Image Validation Report\n")
        f.write("=" * 30 + "\n\n")
        
        if not validation_results:
            f.write("No issues found!")
            return
            
        for filename, issues in validation_results.items():
            f.write(f"\nImage: {filename}\n")
            f.write("-" * 20 + "\n")
            for issue in issues:
                f.write(f"- {issue}\n")
            f.write("\n")

def main():
    # Example usage
    image_folder = "output_images"  # Adjust to your image folder path
    results = validate_question_images(image_folder)
    
    # Generate report
    generate_validation_report(results)
    
    # Print summary
    print(f"\nValidation complete. Found issues in {len(results)} images.")
    if results:
        print("Please check validation_report.txt for details.")
        
        # Print most common issues
        all_issues = [issue for issues in results.values() for issue in issues]
        issue_counts = defaultdict(int)
        for issue in all_issues:
            issue_type = issue.split(':')[0]
            issue_counts[issue_type] += 1
            
        print("\nMost common issues:")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"- {issue_type}: {count} occurrences")

if __name__ == "__main__":
    main()