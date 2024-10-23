import click
import json
import logging
from main import SunoMusicBot
from prompt_generator import PromptGenerator

@click.group()
def cli():
    """Suno Music Bot CLI - Generate AI music with ease"""
    pass

@cli.command()
@click.option('--prompt', '-p', help='Custom prompt for music generation')
@click.option('--variations', '-v', default=1, help='Number of variations to generate')
@click.option('--template', '-t', default='crypto_meme', help='Template to use for generation')
def generate(prompt, variations, template):
    """Generate music with a custom prompt, template, or auto-generated prompts"""
    bot = None
    try:
        bot = SunoMusicBot()
        bot.login()
        
        if prompt:
            click.echo(f"Generating music with custom prompt: {prompt}")
            bot.generate_music(prompt)
        else:
            prompt_gen = PromptGenerator()
            prompts = prompt_gen.get_prompt_variations(num_variations=variations, template_name=template)
            click.echo(f"Generating {variations} music variations using template: {template}")
            
            with click.progressbar(prompts) as bar:
                for prompt in bar:
                    click.echo(f"\nUsing prompt: {prompt}")
                    bot.generate_music(prompt)
        
        click.echo("Music generation completed! Check the downloads folder.")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
    finally:
        if bot:
            bot.close()

@cli.command()
def list_templates():
    """List all available prompt templates"""
    prompt_gen = PromptGenerator()
    templates = prompt_gen.list_available_templates()
    
    click.echo("\nAvailable Templates:")
    click.echo("-" * 50)
    
    for template in templates:
        click.echo(f"- {template}")
    
    click.echo(f"\nTotal templates: {len(templates)}")

@cli.command()
@click.argument('name')
@click.argument('template')
@click.argument('variations_file')
def create_template(name, template, variations_file):
    """Create a new prompt template"""
    try:
        with open(variations_file, 'r') as f:
            variations = json.load(f)
        
        prompt_gen = PromptGenerator()
        if prompt_gen.create_custom_template(name, template, variations):
            click.echo(f"Template '{name}' created successfully!")
        else:
            click.echo("Failed to create template", err=True)
            
    except Exception as e:
        click.echo(f"Error creating template: {str(e)}", err=True)

@cli.command()
def list_downloads():
    """List all generated music files in the downloads directory"""
    from pathlib import Path
    downloads = Path("downloads").glob("*.wav")
    
    click.echo("\nGenerated Music Files:")
    click.echo("-" * 50)
    
    count = 0
    for file in downloads:
        click.echo(f"- {file.name}")
        count += 1
    
    if count == 0:
        click.echo("No music files found in downloads directory.")
    else:
        click.echo(f"\nTotal files: {count}")

if __name__ == '__main__':
    cli()
