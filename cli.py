import click
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
def generate(prompt, variations):
    """Generate music with a custom prompt or use auto-generated prompts"""
    bot = None
    try:
        bot = SunoMusicBot()
        bot.login()
        
        if prompt:
            click.echo(f"Generating music with custom prompt: {prompt}")
            bot.generate_music(prompt)
        else:
            prompt_gen = PromptGenerator()
            prompts = prompt_gen.get_prompt_variations(num_variations=variations)
            click.echo(f"Generating {variations} music variations...")
            
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
