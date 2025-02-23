import json
import os
from typing import Dict, List, Set

def validate_question(question: Dict) -> Set[str]:
    """
    Validates a single question and returns a set of missing or empty fields.
    
    Args:
        question (dict): Question dictionary containing fields to validate
        
    Returns:
        set: Set of field names that are missing or empty
    """
    missing_fields = set()
    
    # Required fields to check
    required_fields = {
        'number': str,
        'text': str,
        'options': dict,
        'correct_answer': str,
        'question_id': str,
        'image_path': str
    }
    
    # Check for missing fields
    for field, expected_type in required_fields.items():
        if field not in question:
            missing_fields.add(f"missing_{field}")
            continue
            
        value = question[field]
        
        # Check if field is empty or wrong type
        if field == 'options':
            if not isinstance(value, dict):
                missing_fields.add(f"invalid_options_type")
            else:
                # Only check if options A, B, C, D exist, but don't validate their content
                for option in ['A', 'B', 'C', 'D']:
                    if option not in value:
                        missing_fields.add(f"missing_option_{option}")
        elif field != 'text':  # Skip empty check for text field
            if not isinstance(value, expected_type) or not str(value).strip():
                missing_fields.add(f"empty_{field}")
    
    return missing_fields

def analyze_questions_folder(folder_path: str) -> Dict[str, List[Dict]]:
    """
    Analyzes all JSON files in the specified folder for questions with missing fields.
    
    Args:
        folder_path (str): Path to folder containing question JSON files
        
    Returns:
        dict: Dictionary mapping file names to lists of problematic questions
    """
    results = {}
    
    for filename in os.listdir(folder_path):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(folder_path, filename)
        problematic_questions = []
        
        try:
            with open(file_path, 'r') as f:
                questions = json.load(f)
                
            for i, question in enumerate(questions, 1):
                missing_fields = validate_question(question)
                
                if missing_fields:
                    problematic_questions.append({
                        'question_number': question.get('number', f'Unknown-{i}'),
                        'missing_fields': list(missing_fields),
                        'question_data': question
                    })
            
            if problematic_questions:
                results[filename] = problematic_questions
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            
    return results

def print_validation_report(results: Dict[str, List[Dict]]) -> None:
    """
    Prints a formatted report of the validation results.
    
    Args:
        results (dict): Dictionary of validation results
    """
    if not results:
        print("No issues found in any question files.")
        return
        
    print("\nValidation Report:")
    print("=" * 80)
    
    total_questions_with_issues = 0
    
    for filename, problems in results.items():
        print(f"\nFile: {filename}")
        print(f"Number of questions with issues: {len(problems)}")
        print("-" * 80)
        
        total_questions_with_issues += len(problems)
        
        for problem in problems:
            print(f"\nQuestion {problem['question_number']}:")
            print(f"Issues found: {', '.join(problem['missing_fields'])}")
            print("Question data:")
            print(json.dumps(problem['question_data'], indent=2))
            
    print("\n" + "=" * 80)
    print(f"Total questions with issues across all files: {total_questions_with_issues}")

def main():
    folder_path = "final_questions"  # Change this to your folder path
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return
        
    results = analyze_questions_folder(folder_path)
    print_validation_report(results)
    
    # Save results to a file
    with open('validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        print("\nDetailed results have been saved to 'validation_results.json'")

if __name__ == "__main__":
    main()