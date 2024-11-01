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

if __name__ == '__main__':
    cli()
