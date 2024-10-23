import os
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from prompt_generator import PromptGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/suno_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunoMusicBot:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.logs_dir = Path("logs")
        self.downloads_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.prompt_generator = PromptGenerator()
        self.setup_driver()

    def setup_driver(self):
        """Initialize the Chrome WebDriver with required options."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Removed headless mode for better interaction
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set up downloads directory
        prefs = {
            "download.default_directory": str(self.downloads_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)  # Increased timeout
            logger.info("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def wait_and_click(self, selector, timeout=30):
        """Helper method to wait for an element and click it."""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {selector}")
            return False

    def login(self):
        """Login to suno.ai using browser automation."""
        try:
            logger.info("Navigating to Suno.ai login page...")
            self.driver.get("https://suno.ai")
            
            # Wait for and click the login button
            if not self.wait_and_click("button[data-testid='login-button']"):
                raise TimeoutException("Could not find login button")
            
            logger.info("Waiting for user to complete authentication...")
            # Wait for successful login (dashboard redirection)
            self.wait.until(
                EC.url_contains("suno.ai/dashboard")
            )
            logger.info("Successfully logged in to Suno.ai")
            
        except TimeoutException as e:
            logger.error(f"Login timeout: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise

    def generate_music(self, prompt: str):
        """Generate music using the provided prompt."""
        try:
            # Navigate to creation page
            self.driver.get("https://suno.ai/create")
            logger.info(f"Generating music with prompt: {prompt}")
            
            # Wait for prompt input field
            prompt_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='Write a prompt']"))
            )
            prompt_input.clear()
            prompt_input.send_keys(prompt)
            
            # Click generate button
            if not self.wait_and_click("button[type='submit']"):
                raise TimeoutException("Could not find generate button")
            
            # Wait for generation to complete
            logger.info("Waiting for music generation to complete...")
            download_selector = "button[aria-label='Download']"
            if not self.wait_and_click(download_selector):
                raise TimeoutException("Music generation failed or timed out")
            
            # Wait for download to complete
            time.sleep(5)
            logger.info(f"Successfully generated music for prompt: {prompt}")
            
        except TimeoutException as e:
            logger.error(f"Generation timeout: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

def main():
    bot = None
    try:
        bot = SunoMusicBot()
        bot.login()
        
        # Generate 3 variations of prompts and create music for each
        prompts = bot.prompt_generator.get_prompt_variations(num_variations=3)
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"Processing prompt {i} of {len(prompts)}")
            bot.generate_music(prompt)
            time.sleep(3)  # Brief pause between generations
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        if bot:
            bot.close()

if __name__ == "__main__":
    main()
