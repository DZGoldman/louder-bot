import click
import json
import logging
from main import SunoMusicBot
from prompt_generator import PromptGenerator
from cloud_storage import CloudStorageManager

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

@cli.command()
def list_cloud_files():
    """List all files stored in cloud storage"""
    try:
        storage = CloudStorageManager()
        files = storage.list_files()
        
        click.echo("\nCloud Storage Files:")
        click.echo("-" * 50)
        
        if not files:
            click.echo("No files found in cloud storage.")
            return
            
        for file in files:
            click.echo(f"- {file}")
        click.echo(f"\nTotal files: {len(files)}")
        
    except Exception as e:
        click.echo(f"Error listing cloud files: {str(e)}", err=True)

@cli.command()
@click.argument('file_path')
def upload_to_cloud(file_path):
    """Upload a specific file to cloud storage"""
    try:
        storage = CloudStorageManager()
        url = storage.upload_file(file_path)
        click.echo(f"File uploaded successfully!")
        click.echo(f"Public URL: {url}")
    except Exception as e:
        click.echo(f"Error uploading file: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
