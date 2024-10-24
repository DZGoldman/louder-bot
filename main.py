import os
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from prompt_generator import PromptGenerator
from cloud_storage import CloudStorageManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/suno_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoginError(Exception):
    """Custom exception for login failures"""
    pass

class SunoMusicBot:
    def __init__(self, use_cloud_storage: bool = False, headless: bool = False, max_retries: int = 3):
        self.downloads_dir = Path("downloads")
        self.logs_dir = Path("logs")
        self.downloads_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.prompt_generator = PromptGenerator()
        self.cloud_storage = CloudStorageManager() if use_cloud_storage else None
        self.headless = False  # Force non-headless mode for stability
        self.max_retries = max_retries
        
        self.email = str(os.getenv("GOOGLE_EMAIL", "")).strip()
        self.password = str(os.getenv("GOOGLE_PASSWORD", "")).strip()
        
        if not self.email or not self.password:
            raise ValueError("Google credentials not found in environment variables")
        
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome WebDriver with maximum stability settings."""
        try:
            chrome_options = Options()
            
            # Essential stability settings
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # Prevent detection
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Additional stability settings
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--remote-debugging-port=9222')  # Enable DevTools Protocol
            
            # Download preferences
            prefs = {
                "download.default_directory": str(self.downloads_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "credentials_enable_service": True,
                "profile.password_manager_enabled": True,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Initialize WebDriver with longer timeouts
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(90)
            self.wait = WebDriverWait(self.driver, 45)
            
            # Set window size explicitly
            self.driver.set_window_size(1920, 1080)
            self.driver.set_window_position(0, 0)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def wait_for_page_load(self, timeout=90):
        """Wait for page to fully load with improved timeout."""
        try:
            return self.wait.until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            logger.warning(f"Error waiting for page load: {str(e)}")
            return False

    def wait_and_click(self, selector, description="element", timeout=45):
        """Wait for element with improved stability and multiple click attempts."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Wait for element presence
                element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                
                # Ensure element is in viewport
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    element
                )
                time.sleep(2)  # Wait for scroll and animations
                
                # Wait for clickability
                element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                
                # Try multiple click methods
                try:
                    element.click()
                except:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                    except:
                        # Final attempt: send Enter key
                        element.send_keys(Keys.RETURN)
                
                logger.info(f"Successfully clicked {description} (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to click {description} after {max_attempts} attempts: {str(e)}")
                    return False
                logger.warning(f"Click attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        return False

    def handle_google_oauth(self):
        """Handle Google OAuth with improved stability and window management."""
        try:
            # Wait for window handles with retry
            max_retries = 3
            for attempt in range(max_retries):
                time.sleep(3)
                windows = self.driver.window_handles
                
                if len(windows) > 1:
                    # Try to find Google login window
                    for window in windows:
                        self.driver.switch_to.window(window)
                        if "accounts.google.com" in self.driver.current_url:
                            logger.info("Found Google login window")
                            break
                    else:
                        # If not found, use the last window
                        self.driver.switch_to.window(windows[-1])
                    break
                    
                if attempt == max_retries - 1:
                    raise Exception("Google login window not found")
                    
                logger.info(f"Waiting for Google window (attempt {attempt + 1})")
            
            # Handle email input with retry
            logger.info("Looking for email input field...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "identifier"))
            )
            email_field.clear()
            time.sleep(1)
            email_field.send_keys(self.email)
            time.sleep(1)
            email_field.send_keys(Keys.RETURN)
            logger.info("Email entered successfully")
            
            # Wait for password field with explicit timeout
            time.sleep(3)
            logger.info("Looking for password input field...")
            password_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            time.sleep(1)
            password_field.send_keys(self.password)
            time.sleep(1)
            password_field.send_keys(Keys.RETURN)
            logger.info("Password entered successfully")
            
            # Wait for OAuth completion and switch back
            time.sleep(5)
            self.driver.switch_to.window(windows[0])
            return True
            
        except Exception as e:
            logger.error(f"Google OAuth failed: {str(e)}")
            self.save_screenshot("google_oauth_failure.png")
            return False

    def verify_login(self, timeout=45):
        """Verify successful login with improved checks."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.current_url
                    if "/dashboard" in current_url or "/create" in current_url or "/studio" in current_url:
                        logger.info(f"Login verified - Current URL: {current_url}")
                        return True
                except:
                    # Handle potential DevTools disconnection
                    logger.warning("Error checking URL, retrying...")
                time.sleep(2)
            logger.error("Login verification timeout")
            return False
        except Exception as e:
            logger.error(f"Login verification failed: {str(e)}")
            return False

    def login(self):
        """Improved login process with enhanced stability and error handling."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.info(f"Starting login attempt {retry_count + 1}/{self.max_retries}")
                
                # Load Suno homepage
                self.driver.get("https://suno.ai")
                if not self.wait_for_page_load():
                    raise LoginError("Page load timeout")
                
                time.sleep(3)  # Wait for initial animations
                
                # Click Sign In button with exact selector
                sign_in_selector = "//button[text()='Sign in' and contains(@class, 'bottom')]"
                if not self.wait_and_click(sign_in_selector, "Sign in button"):
                    raise LoginError("Could not find or click Sign in button")
                
                time.sleep(3)  # Wait for modal animation
                
                # Click Google login button (third auth button)
                google_selector = "(//*[contains(@class, 'auth-button')])[3]"
                if not self.wait_and_click(google_selector, "Google login button"):
                    raise LoginError("Could not find or click Google login button")
                
                time.sleep(3)  # Wait for OAuth window
                
                # Handle Google OAuth process
                if not self.handle_google_oauth():
                    raise LoginError("Google OAuth process failed")
                
                # Verify login success with longer timeout
                if self.verify_login(timeout=45):
                    logger.info("Login successful!")
                    return True
                
                raise LoginError("Login verification failed")
                
            except Exception as e:
                logger.error(f"Login attempt {retry_count + 1} failed: {str(e)}")
                self.save_screenshot(f"login_failure_{retry_count + 1}.png")
                retry_count += 1
                
                if retry_count >= self.max_retries:
                    raise LoginError(f"Login failed after {self.max_retries} attempts")
                
                time.sleep(5)  # Wait before retry
                
                try:
                    # Clean up and restart WebDriver
                    self.close()
                except:
                    logger.warning("Error while closing WebDriver, ignoring...")
                finally:
                    self.setup_driver()
        
        return False

    def save_screenshot(self, filename):
        """Save a screenshot with error handling."""
        try:
            filepath = self.logs_dir / filename
            self.driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}")

    def close(self):
        """Clean up resources with improved error handling."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    bot = None
    try:
        bot = SunoMusicBot(headless=False)
        bot.login()
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
    finally:
        if bot:
            bot.close()
