import json
import random
from pathlib import Path
from typing import Dict, List, Optional

class PromptTemplate:
    def __init__(self, name: str, template: str, variations: Dict[str, List[str]]):
        """
        Initialize a prompt template.
        
        Args:
            name: Template name
            template: Base template with placeholders like {genre}, {mood}, etc.
            variations: Dictionary of variation lists for each placeholder
        """
        self.name = name
        self.template = template
        self.variations = variations
    
    def generate(self) -> str:
        """Generate a prompt by filling in the template with random variations."""
        filled_template = self.template
        for key, values in self.variations.items():
            if f"{{{key}}}" in filled_template:
                filled_template = filled_template.replace(f"{{{key}}}", random.choice(values))
        return filled_template

class PromptTemplateManager:
    def __init__(self):
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        self._load_custom_templates()
    
    def _load_default_templates(self):
        """Load built-in default templates."""
        self.templates["crypto_meme"] = PromptTemplate(
            name="crypto_meme",
            template="CRYPTO, {genre}, {mood}, {theme}, INTERNET, YOUTHFUL, 2024, {style}",
            variations={
                "genre": ["HYPERPOP", "TRAP", "ELECTRONIC", "GLITCH"],
                "mood": ["ENERGETIC", "HYPE", "INTENSE", "PLAYFUL"],
                "theme": ["MEME", "VIRAL", "TRENDING", "CULTURE"],
                "style": ["DIGITAL", "FUTURISTIC", "AESTHETIC", "REMIX"]
            }
        )
        
        self.templates["chill_lofi"] = PromptTemplate(
            name="chill_lofi",
            template="{mood} LOFI, {instrument}, {theme}, {style}",
            variations={
                "mood": ["RELAXING", "CHILL", "PEACEFUL", "AMBIENT"],
                "instrument": ["PIANO", "GUITAR", "SYNTH", "BEATS"],
                "theme": ["STUDY", "FOCUS", "MEDITATION", "NATURE"],
                "style": ["MINIMAL", "ATMOSPHERIC", "DREAMY", "SMOOTH"]
            }
        )

    def _load_custom_templates(self):
        """Load custom templates from JSON files."""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    data = json.load(f)
                    self.templates[data["name"]] = PromptTemplate(
                        name=data["name"],
                        template=data["template"],
                        variations=data["variations"]
                    )
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

    def save_template(self, template: PromptTemplate):
        """Save a template to a JSON file."""
        template_data = {
            "name": template.name,
            "template": template.template,
            "variations": template.variations
        }
        
        with open(self.templates_dir / f"{template.name}.json", 'w') as f:
            json.dump(template_data, f, indent=2)

    def create_template(self, name: str, template: str, variations: Dict[str, List[str]]) -> PromptTemplate:
        """Create and save a new template."""
        new_template = PromptTemplate(name, template, variations)
        self.templates[name] = new_template
        self.save_template(new_template)
        return new_template

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())

    def generate_prompt(self, template_name: str) -> Optional[str]:
        """Generate a prompt using the specified template."""
        template = self.get_template(template_name)
        if template:
            return template.generate()
        return None

    def generate_variations(self, template_name: str, count: int = 3) -> List[str]:
        """Generate multiple variations using the specified template."""
        template = self.get_template(template_name)
        if not template:
            return []
        return [template.generate() for _ in range(count)]
