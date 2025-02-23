from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class USNCOTopic(Enum):
    RANDOM = "Random Question"
    STOICHIOMETRY = "Stoichiometry and Solutions"
    DESCRIPTIVE = "Descriptive Chemistry and Laboratory"
    STATES = "States of Matter"
    THERMODYNAMICS = "Thermodynamics"
    KINETICS = "Kinetics"
    EQUILIBRIUM = "Equilibrium"
    REDOX = "Oxidation-Reduction"
    ATOMIC = "Atomic Structure and Periodicity"
    BONDING = "Bonding and Molecular Structure"
    ORGANIC = "Organic Chemistry and Biochemistry"

    @classmethod
    def get_topic_for_number(cls, question_number: int) -> 'USNCOTopic':
        """Returns the topic enum based on question number."""
        ranges = {
            (1, 6): cls.STOICHIOMETRY,
            (7, 12): cls.DESCRIPTIVE,
            (13, 18): cls.STATES,
            (19, 24): cls.THERMODYNAMICS,
            (25, 30): cls.KINETICS,
            (31, 36): cls.EQUILIBRIUM,
            (37, 42): cls.REDOX,
            (43, 48): cls.ATOMIC,
            (49, 54): cls.BONDING,
            (55, 60): cls.ORGANIC
        }
        
        for (start, end), topic in ranges.items():
            if start <= question_number <= end:
                return topic
        return cls.RANDOM

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