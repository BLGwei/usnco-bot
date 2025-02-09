import os
import re
from collections import defaultdict

"""
1. Goes through the folder with outputted images and parses test type, year and question numbers
2. Checks for missing question numbers
3. Generates a report showing:

- Which years and test types have missing files
- How many files are missing from each exam
- Which specific question numbers are missing

4. saved to file missing_files_report.txt
"""


def analyze_missing_files(root_dir):
    # Dictionary to store missing files for each year and test type
    missing_files = defaultdict(list)
    
    # Regular expression pattern for file names
    pattern = r"^([12])(\d{4})(\d{1,2})\.png$"
    
    # Walk through all subdirectories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Group files by year and test type
        files_by_group = defaultdict(list)
        
        for filename in filenames:
            if not filename.endswith('.png'):
                continue
                
            match = re.match(pattern, filename)
            if match:
                test_type, year, question = match.groups()
                key = (test_type, year)
                files_by_group[key].append(int(question))
        
        # Check for missing numbers in each group
        for (test_type, year), questions in files_by_group.items():
            questions.sort()
            test_type_name = "Local" if test_type == "1" else "National"
            
            # Check for missing numbers from 1 to 60
            expected_questions = set(range(1, 61))
            actual_questions = set(questions)
            missing = sorted(expected_questions - actual_questions)
            
            if missing:
                missing_files[(year, test_type_name)] = missing

    return missing_files

def generate_report(missing_files):
    # Sort by year and test type
    sorted_keys = sorted(missing_files.keys())
    
    report = []
    report.append("Missing Files Report:")
    report.append("=" * 50)
    
    for year, test_type in sorted_keys:
        missing = missing_files[(year, test_type)]
        report.append(f"\n{year} {test_type} Exam:")
        report.append(f"Total missing: {len(missing)}")
        report.append(f"Missing questions: {', '.join(map(str, missing))}")
        total_missing = 0  # Initialize total missing counter
    
    for year, test_type in sorted_keys:
        missing = missing_files[(year, test_type)]
        total_missing += len(missing)  # Add to total count
        report.append(f"\n{year} {test_type} Exam:")
        report.append(f"Total missing: {len(missing)}")
        report.append(f"Missing questions: {', '.join(map(str, missing))}")
    
    # Add total count to the end of the report
    report.append("\n" + "=" * 50)
    report.append(f"Total missing questions across all exams: {total_missing}")
    
    return "\n".join(report)

def main():
    # Replace with your actual directory path
    root_dir = "output_images"
    
    missing_files = analyze_missing_files(root_dir)
    report = generate_report(missing_files)
    print(report)
    
    # Optionally save to file
    with open("missing_files_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    main()
