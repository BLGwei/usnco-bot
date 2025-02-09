# In regex_patterns.py
import re

def get_footer_patterns():
    return {
        'exam_footer': r"Exam\s+after\s+March\s+31,\s*(?:20(?:0[0-9]|1[0-9]|2[0-4]))\s*Page\s*[3-7]",
        'exam_footer2' : r"for\s+use\s+as\s+a\s+USNCO\s*(Local|National)\s*Section\s*Exam\s*after\s*(?:March|April)\s*\d{1,2},\s*(?:20\d{2})?$",
        'page_property_footer': r"Page\s*[3-7]\s*Property\s*of\s*ACS\s*USN",
        'page_number': r'[Pp]age\s*[3-7]',
        'long_instruction': r"IONS\s*the\s*corresponding\s*space\s*on\s*the\s*answer\s*sheet\s*using\s*a\s*soft,\s*#2\s*de\s*to\s*change\s*an\s*answer,\s*erase\s*the\s*unwanted\s*mark\s*very\s*carefully\.\s*s\s*for\s*which\s*more\s*than\s*one\s*response\s*has\s*been\s*blackened\s*will\s*not\s*er\s*correctly\.\s*It\s*is\s*to\s*your\s*advantage\s*to\s*answer\s*every\s*question\.",
        'option_footer': r'\s*O?\s*[–-]\s*Not\s*for\s*use\s*as\s*USNCO\s*(National|Local)\s*Exam\s*after\s*(?:April|March)\s*\d{1,2},\s*(?:20\d{2})?$',
        'specific_footer1': r"Page 8 Property of ACS USN\nO \u2013 Not for use as USNCO National Exam after April 20, 2015",
        'specific_footer2': r"Property of ACS USNCO \u2013 Not for use as USNCO National Ex",
        'specific_footer3': r"m after April 20, 2015 Page 7",
        'specific_footer4': r"Exam after March 31, 2022\s+Page \d+",
        'specific_footer5': r"Not Valid as a Local USNCO Exam after April (?:1[5-9]|2[0-2]), (?:200[0-9]|201[0-9]|202[0-4])",
        'specific_footer6': r"Not for use as a USNCO Local Section Exam after April (?:1[5-9]|2[0-2])",
        'specific_footer7': r"Not Valid as a Local USNCO Exam after April (?:14|1[5-9]|2[0-2]), (?:200[0-9]|201[0-9]|202[0-4])",
        'specific_footer8': r"END OF TEST Not for use as a USNCO Local Section Exam after (?:1[1-9]|2[0-2]), (?:200[0-9]|201[0-9]|202[0-4])"

    }

def get_usnco_exam_footer_patterns():
    patterns = get_footer_patterns()
    return [
        patterns['exam_footer'],
        patterns['page_property_footer'],
        patterns['page_number'],
        patterns['long_instruction'],
        patterns['option_footer'],
        patterns['exam_footer2'],
        patterns['specific_footer1'],
        patterns['specific_footer2'],
        patterns['specific_footer3'],
        patterns['specific_footer4'],
        patterns['specific_footer5'],
        patterns['specific_footer6'],
        patterns['specific_footer7'],
        patterns['specific_footer8']
    ]