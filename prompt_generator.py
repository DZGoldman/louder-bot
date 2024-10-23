from typing import List
from prompt_templates import PromptTemplateManager

class PromptGenerator:
    def __init__(self):
        self.template_manager = PromptTemplateManager()
        
    def generate_prompt(self, template_name: str = "crypto_meme") -> str:
        """
        Generate a prompt using the specified template.
        Falls back to crypto_meme template if the specified template doesn't exist.
        """
        prompt = self.template_manager.generate_prompt(template_name)
        if prompt is None:
            # Fallback to crypto_meme template
            prompt = self.template_manager.generate_prompt("crypto_meme")
        return prompt

    def get_prompt_variations(self, num_variations: int = 3, template_name: str = "crypto_meme") -> List[str]:
        """
        Generate multiple variations of prompts using the specified template.
        
        Args:
            num_variations: Number of variations to generate (default: 3)
            template_name: Name of the template to use (default: crypto_meme)
            
        Returns:
            List of generated prompt strings
        """
        return self.template_manager.generate_variations(template_name, num_variations)

    def list_available_templates(self) -> List[str]:
        """List all available template names."""
        return self.template_manager.list_templates()

    def create_custom_template(self, name: str, template: str, variations: dict) -> bool:
        """
        Create a new custom template.
        
        Args:
            name: Template name
            template: Template string with placeholders
            variations: Dictionary of variation lists for placeholders
            
        Returns:
            True if template was created successfully
        """
        try:
            self.template_manager.create_template(name, template, variations)
            return True
        except Exception:
            return False
