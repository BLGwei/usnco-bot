import pytesseract
from PIL import Image
import re
import os
from ExamImages import save_individual_question_images_with_ids

def validate_and_adjust_image_crop(image_path, expected_question_num):
    """
    Validates a question image using OCR to check for subsequent question numbers
    and adjusts the crop if needed.
    
    Args:
        image_path (str): Path to the question image
        expected_question_num (int): The current question number
        
    Returns:
        tuple: (needs_adjustment: bool, adjustment_amount: int)
    """
    try:
        # Open the image
        img = Image.open(image_path)
        width, height = img.size
        
        # Extract text from image
        text = pytesseract.image_to_string(img)
        
        # Look for any question numbers after the expected one
        next_question_pattern = r"(?<!\d)" + str(expected_question_num + 1) + r"\."
        
        if re.search(next_question_pattern, text):
            print(f"Found next question {expected_question_num + 1} in image {image_path}")
            
            # Create slices of the image to find where the next question starts
            num_slices = 10
            slice_height = height // num_slices
            
            # Search from bottom up to find where the next question appears
            for i in range(num_slices - 1, 0, -1):
                slice_y = i * slice_height
                slice_img = img.crop((0, slice_y, width, slice_y + slice_height))
                slice_text = pytesseract.image_to_string(slice_img)
                
                if re.search(next_question_pattern, slice_text):
                    # Found the slice containing the next question
                    adjustment_y = slice_y - 20  # Add 20px padding
                    
                    # Crop and save the adjusted image
                    adjusted_img = img.crop((0, 0, width, adjustment_y))
                    adjusted_img.save(image_path)
                    
                    print(f"Adjusted image {image_path} to remove question {expected_question_num + 1}")
                    return True, adjustment_y
        
        return False, None
        
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return False, None

def batch_validate_and_adjust_images(folder_path):
    """
    Process all question images in a folder to validate and adjust crops.
    
    Args:
        folder_path (str): Path to folder containing question images
    
    Returns:
        dict: Statistics about adjustments made
    """
    stats = {
        'total_processed': 0,
        'adjustments_made': 0,
        'errors': 0
    }
    
    for filename in os.listdir(folder_path):
        if not filename.endswith('.png'):
            continue
            
        try:
            # Extract question number from filename (format: YYYYQQ.png)
            question_num = int(filename.split('.')[0][-2:])
            image_path = os.path.join(folder_path, filename)
            
            needs_adjustment, _ = validate_and_adjust_image_crop(image_path, question_num)
            
            stats['total_processed'] += 1
            if needs_adjustment:
                stats['adjustments_made'] += 1
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            stats['errors'] += 1
            continue
    
    return stats

def integrate_ocr_validation(save_individual_question_images_with_ids):
    """
    Wrapper function to add OCR validation to the existing image saving process.
    """
    def wrapped_save_images(*args, **kwargs):
        # Call original function
        question_images = save_individual_question_images_with_ids(*args, **kwargs)
        
        # Validate and adjust all saved images
        for question_id, image_path in question_images.items():
            try:
                # Extract question number from question_id
                question_num = int(question_id[-2:])
                validate_and_adjust_image_crop(image_path, question_num)
            except Exception as e:
                print(f"Error validating {question_id}: {str(e)}")
                continue
        
        return question_images
    
    return wrapped_save_images

# Example usage:
if __name__ == "__main__":
    # Wrap the original save function with OCR validation
    save_with_validation = integrate_ocr_validation(save_individual_question_images_with_ids)
    
    # Use the wrapped function instead of the original

    
    # Or process existing images
    stats = batch_validate_and_adjust_images("output_images")
    print(f"""
    Processing complete:
    - Total images processed: {stats['total_processed']}
    - Adjustments made: {stats['adjustments_made']}
    - Errors encountered: {stats['errors']}
    """)