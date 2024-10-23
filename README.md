# Suno Music Bot

A Python-based automation bot for generating and saving music from suno.com with themed prompt variations.

## Features
- Automated music generation using Suno.ai
- Theme-based prompt generation
- Simple CLI interface for easy control
- Download management

## CLI Usage

The bot can be controlled using the following commands:

### Generate Music
```bash
# Generate music with a custom prompt
python cli.py generate --prompt "YOUR CUSTOM PROMPT"

# Generate multiple variations with auto-generated prompts
python cli.py generate --variations 3

# List downloaded music files
python cli.py list-downloads
```

### Options
- `--prompt, -p`: Custom prompt for music generation
- `--variations, -v`: Number of variations to generate (default: 1)

## Directory Structure
- `downloads/`: Generated music files
- `logs/`: Application logs
