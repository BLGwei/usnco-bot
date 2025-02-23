import json
import os
from typing import Dict, List
from question_models import Question, USNCOTopic

class TopicOrganizer:
    def __init__(self, questions_folder: str):
        """
        Initialize the topic organizer with a folder containing question JSON files.
        
        Args:
            questions_folder (str): Path to folder containing enriched question JSON files
        """
        self.questions_by_topic: Dict[USNCOTopic, List[Question]] = {
            topic: [] for topic in USNCOTopic
        }
        self.load_questions(questions_folder)
    
    def load_questions(self, folder_path: str) -> None:
        """Load and organize questions from JSON files by topic."""
        for filename in os.listdir(folder_path):
            if not filename.endswith('.json'):
                continue
                
            with open(os.path.join(folder_path, filename), 'r') as f:
                questions = json.load(f)
                
            for q in questions:
                try:
                    # Convert question number to int and get corresponding topic
                    question_num = int(q['number'])
                    topic = USNCOTopic.get_topic_for_number(question_num)
                    
                    # Add to both specific topic and random pool
                    self.questions_by_topic[topic].append(Question.from_json(q))
                    if topic != USNCOTopic.RANDOM:  # Only add to random if it's not already a random question
                        self.questions_by_topic[USNCOTopic.RANDOM].append(Question.from_json(q))
                except (ValueError, KeyError) as e:
                    print(f"Error processing question {q.get('number', 'unknown')}: {e}")
    
    def get_questions_by_topic(self, topic: USNCOTopic) -> List[Question]:
        """Get all questions for a specific topic."""
        return self.questions_by_topic.get(topic, [])
    
    def get_topic_distribution(self) -> Dict[USNCOTopic, int]:
        """Get the distribution of questions across topics."""
        return {
            topic: len(questions) 
            for topic, questions in self.questions_by_topic.items()
            if topic != USNCOTopic.RANDOM
        }