import random
from typing import List

class PromptGenerator:
    def __init__(self):
        # Base prompt that will be included in every generation
        self.BASE_PROMPT = "CRYPTO, MEME, HYPERPOP, INTERNET, YOUTHFUL, 2024"
        
        # Additional words that can be randomly added
        self.ADDITIONAL_WORDS = [
            "VIRAL",
            "TRENDING",
            "AESTHETIC",
            "DIGITAL",
            "GLITCH",
            "FUTURE",
            "REMIX",
            "VIBE",
            "CULTURE"
        ]

    def generate_prompt(self) -> str:
        """
        Generate a prompt that always includes the base prompt plus 1-3 random additional words.
        Returns a string with all words joined by commas.
        """
        # Determine how many additional words to use (1-3)
        num_additional = random.randint(1, 3)
        
        # Randomly select the specified number of additional words
        selected_words = random.sample(self.ADDITIONAL_WORDS, num_additional)
        
        # Combine base prompt with selected additional words
        full_prompt = f"{self.BASE_PROMPT}, {', '.join(selected_words)}"
        
        return full_prompt

    def get_prompt_variations(self, num_variations: int = 3) -> List[str]:
        """
        Generate multiple variations of prompts.
        
        Args:
            num_variations: Number of variations to generate (default: 3)
            
        Returns:
            List of generated prompt strings
        """
        return [self.generate_prompt() for _ in range(num_variations)]
