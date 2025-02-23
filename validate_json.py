import json
import os
from pathlib import Path

def validate_json_file(file_path: str) -> tuple[bool, str, int]:
    """
    Validates a JSON file and returns validation status, error message, and line number if there's an error.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        tuple: (is_valid, error_message, line_number)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            json.loads(content)
            return True, "Valid JSON", 0
    except json.JSONDecodeError as e:
        # Get the problematic line
        lines = content.split('\n')
        line_number = e.lineno
        context_start = max(0, line_number - 3)
        context_end = min(len(lines), line_number + 2)
        
        context = "\n".join(f"Line {i+1}: {lines[i]}" for i in range(context_start, context_end))
        
        error_msg = (f"JSON Error: {str(e)}\n"
                    f"Error occurs around:\n{context}")
        return False, error_msg, line_number
    except Exception as e:
        return False, f"Error reading file: {str(e)}", 0

def validate_questions_folder(folder_path: str) -> None:
    """
    Validates all JSON files in the specified folder.
    
    Args:
        folder_path: Path to the folder containing JSON files
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return
        
    print(f"Validating JSON files in {folder_path}...")
    
    for file_path in folder.glob("*.json"):
        print(f"\nChecking {file_path.name}...")
        is_valid, error_msg, line_number = validate_json_file(str(file_path))
        
        if is_valid:
            print(f"✓ {file_path.name} is valid")
        else:
            print(f"✗ {file_path.name} has errors:")
            print(error_msg)

if __name__ == "__main__":
    folder_path = "final_questions"  # Change this to your questions folder path
    validate_questions_folder(folder_path)