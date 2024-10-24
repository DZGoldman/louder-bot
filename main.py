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
from selenium.webdriver.common.action_chains import ActionChains
from prompt_generator import PromptGenerator
from cloud_storage import CloudStorageManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/udio_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoginError(Exception):
    """Custom exception for login failures"""
    pass

class UdioMusicBot:
    def __init__(self, use_cloud_storage: bool = False, headless: bool = False, max_retries: int = 3):
        self.downloads_dir = Path("downloads")
        self.logs_dir = Path("logs")
        self.downloads_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.prompt_generator = PromptGenerator()
        self.cloud_storage = CloudStorageManager() if use_cloud_storage else None
        self.headless = headless
        self.max_retries = max_retries
        
        # Validate credentials with strict checking
        self.email = str(os.getenv("GOOGLE_EMAIL", "")).strip()
        self.password = str(os.getenv("GOOGLE_PASSWORD", "")).strip()
        
        if not self.email or not self.password:
            raise ValueError("Google credentials not found or empty in environment variables")
        
        self.setup_driver()

    def wait_for_page_load(self, timeout=90):
        """Wait for page to fully load with dynamic content handling."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.driver.execute_script('return document.readyState')
                if state == 'complete':
                    # Check for dynamic content loading
                    try:
                        self.driver.execute_script(
                            'return window.performance.timing.loadEventEnd > 0'
                        )
                        time.sleep(2)  # Extra wait for dynamic content
                        return True
                    except:
                        time.sleep(1)
                        continue
                time.sleep(1)
            return False
        except Exception as e:
            logger.warning(f"Error waiting for page load: {str(e)}")
            return False

    def wait_and_click(self, selectors, element_name="element", timeout=45):
        """Enhanced element clicking with improved reliability and logging."""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                logger.debug(f"Attempting to click {element_name} with selector: {selector}")
                
                # Wait for element with extended timeout
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                
                # Log element state for debugging
                logger.debug(f"Element found: {element.tag_name}, "
                           f"Text: {element.text}, "
                           f"Classes: {element.get_attribute('class')}")
                
                # Ensure element is in viewport
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});"
                    "window.scrollBy(0, -window.innerHeight / 4);",
                    element
                )
                time.sleep(2)  # Extended wait after scroll
                
                # Verify element is still valid
                if not element.is_displayed() or not element.is_enabled():
                    logger.warning(f"Element not interactable after scroll")
                    continue
                
                # Try multiple click methods with validation
                click_successful = False
                for click_method in [
                    lambda: element.click(),
                    lambda: self.driver.execute_script("arguments[0].click();", element),
                    lambda: element.send_keys(Keys.RETURN),
                    lambda: ActionChains(self.driver).move_to_element(element).click().perform()
                ]:
                    try:
                        click_method()
                        click_successful = True
                        break
                    except:
                        continue
                
                if click_successful:
                    logger.info(f"Successfully clicked {element_name}")
                    return True
                    
            except Exception as e:
                logger.warning(f"Failed with selector {selector}: {e}")
                self.save_screenshot(f"click_failure_{element_name}.png")
                continue
        
        logger.error(f"All selectors failed for {element_name}")
        return False

    def handle_google_oauth(self):
        """Enhanced Google OAuth process with improved window handling and retries."""
        try:
            # Store initial window handle
            main_window = self.driver.current_window_handle
            logger.debug(f"Main window handle: {main_window}")
            
            # Wait longer after clicking Google button
            time.sleep(10)
            
            # Extended wait for Google login window with retries
            start_time = time.time()
            timeout = 60  # Extended timeout
            google_window = None
            retry_count = 0
            max_retries = 3
            
            while time.time() - start_time < timeout and retry_count < max_retries:
                try:
                    windows = self.driver.window_handles
                    logger.debug(f"Current window handles: {windows}")
                    
                    if len(windows) > 1:
                        # Try each window until we find the Google login
                        for window in windows:
                            if window != main_window:
                                try:
                                    self.driver.switch_to.window(window)
                                    current_url = self.driver.current_url
                                    logger.debug(f"Window {window} URL: {current_url}")
                                    
                                    # Check multiple Google OAuth URL patterns
                                    if any(domain in current_url.lower() for domain in [
                                        'accounts.google.com',
                                        'myaccount.google.com',
                                        'google.com/signin',
                                        'gds.google.com'
                                    ]):
                                        google_window = window
                                        logger.info(f"Found Google login window: {current_url}")
                                        break
                                except Exception as e:
                                    logger.warning(f"Error checking window {window}: {e}")
                                    continue
                        
                        if google_window:
                            break
                        
                        # If window not found, try clicking the Google button again
                        if retry_count < max_retries - 1:
                            logger.info("Google window not found, retrying...")
                            self.driver.switch_to.window(main_window)
                            google_selectors = [
                                "//button[contains(., 'Continue with Google')]",
                                "//button[contains(., 'Sign in with Google')]",
                                "//button[contains(@class, 'google')]"
                            ]
                            if self.wait_and_click(google_selectors, "Google login button retry"):
                                time.sleep(5)
                            retry_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error handling windows: {e}")
                
                time.sleep(2)
                logger.debug("Waiting for Google window...")
            
            if not google_window:
                logger.error("Google login window not found after retries")
                self.save_screenshot("google_window_not_found.png")
                return False
            
            # Switch to Google window and handle login
            self.driver.switch_to.window(google_window)
            
            # Handle email input with retry
            for _ in range(3):
                try:
                    email_selectors = [
                        "//input[@type='email']",
                        "//input[@name='identifier']",
                        "//input[contains(@aria-label, 'mail')]"
                    ]
                    
                    for selector in email_selectors:
                        try:
                            email_field = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            email_field.clear()
                            time.sleep(1)
                            email_field.send_keys(self.email)
                            time.sleep(1)
                            email_field.send_keys(Keys.RETURN)
                            logger.info("Email entered successfully")
                            break
                        except:
                            continue
                    break
                except Exception as e:
                    logger.warning(f"Email input attempt failed: {e}")
                    time.sleep(2)
            else:
                logger.error("Failed to enter email after 3 attempts")
                self.save_screenshot("email_input_failure.png")
                return False
            
            # Handle password input with retry
            time.sleep(5)  # Extended wait for password field
            for _ in range(3):
                try:
                    password_selectors = [
                        "//input[@type='password']",
                        "//input[@name='password']",
                        "//input[contains(@aria-label, 'assword')]"
                    ]
                    
                    for selector in password_selectors:
                        try:
                            password_field = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            password_field.clear()
                            time.sleep(1)
                            password_field.send_keys(self.password)
                            time.sleep(1)
                            password_field.send_keys(Keys.RETURN)
                            logger.info("Password entered successfully")
                            break
                        except:
                            continue
                    break
                except Exception as e:
                    logger.warning(f"Password input attempt failed: {e}")
                    time.sleep(2)
            else:
                logger.error("Failed to enter password after 3 attempts")
                self.save_screenshot("password_input_failure.png")
                return False
            
            # Enhanced OAuth completion check
            logger.info("Waiting for OAuth completion...")
            oauth_complete = False
            start_time = time.time()
            while time.time() - start_time < 45:  # Extended timeout
                try:
                    current_handles = self.driver.window_handles
                    if len(current_handles) == 1:
                        self.driver.switch_to.window(current_handles[0])
                        oauth_complete = True
                        logger.info("OAuth process completed successfully")
                        break
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Error checking window handles: {e}")
                    time.sleep(1)
            
            if not oauth_complete:
                logger.error("OAuth process timed out")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Google OAuth failed: {str(e)}")
            self.save_screenshot("google_oauth_failure.png")
            return False

    def setup_driver(self):
        """Set up Chrome WebDriver with maximum stability settings."""
        try:
            chrome_options = Options()
            
            # Essential settings
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # Enhanced stability settings
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--enable-automation')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-browser-side-navigation')
            chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
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
            
            # Initialize WebDriver with increased timeouts
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(90)
            self.wait = WebDriverWait(self.driver, 45)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def login(self):
        """Enhanced login process with improved reliability."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.info(f"Starting login attempt {retry_count + 1}/{self.max_retries}")
                
                # Load homepage with enhanced retry
                for _ in range(3):
                    try:
                        self.driver.get("https://www.udio.com/home")
                        if self.wait_for_page_load():
                            break
                        time.sleep(3)
                    except:
                        time.sleep(3)
                        continue
                
                time.sleep(5)  # Extended wait for dynamic content
                
                # Updated sign-in selectors with exact Tailwind CSS classes
                sign_in_selectors = [
                    "//button[contains(@class, 'inline-flex') and contains(@class, 'items-center') and contains(@class, 'justify-center') and contains(@class, 'whitespace-nowrap')]",
                    "//button[contains(@class, 'bg-white/5') and contains(@class, 'text-white')]",
                    # Fallback selectors
                    "//button[text()='Sign In']",
                    "//button[contains(., 'Sign In')]",
                    "//div[@role='button'][contains(., 'Sign In')]"
                ]
                
                if not self.wait_and_click(sign_in_selectors, "Sign in button", timeout=60):
                    raise LoginError("Could not find or click Sign in button")
                
                time.sleep(5)  # Extended wait for modal
                
                # Updated Google login button selectors
                google_selectors = [
                    "//button[contains(., 'Continue with Google')]",
                    "//button[contains(., 'Sign in with Google')]",
                    "//button[contains(@class, 'google')]",
                    "//button[.//img[contains(@src, 'google')]]",
                    # Fallback selectors
                    "//button[contains(., 'Google')]",
                    "//div[@role='button'][contains(., 'Google')]"
                ]
                
                if not self.wait_and_click(google_selectors, "Google login button", timeout=60):
                    raise LoginError("Could not find or click Google login button")
                
                time.sleep(3)
                
                if not self.handle_google_oauth():
                    raise LoginError("Google OAuth process failed")
                
                # Enhanced login verification
                logger.info("Verifying login success...")
                start_time = time.time()
                verification_timeout = 60
                
                while time.time() - start_time < verification_timeout:
                    try:
                        current_url = self.driver.current_url
                        logger.debug(f"Current URL: {current_url}")
                        
                        if "/home" in current_url or "/dashboard" in current_url:
                            # Verify logged-in state
                            try:
                                logged_in = self.driver.execute_script(
                                    "return document.body.innerHTML.includes('Sign Out') || "
                                    "document.body.innerHTML.includes('Logout') || "
                                    "document.body.innerHTML.includes('Profile')"
                                )
                                if logged_in:
                                    logger.info("Login successful!")
                                    return True
                            except:
                                pass
                        
                        time.sleep(2)
                    except:
                        time.sleep(2)
                        continue
                
                raise LoginError("Login verification failed")
                
            except Exception as e:
                logger.error(f"Login attempt {retry_count + 1} failed: {str(e)}")
                self.save_screenshot(f"login_failure_{retry_count + 1}.png")
                retry_count += 1
                
                if retry_count >= self.max_retries:
                    raise LoginError(f"Login failed after {self.max_retries} attempts")
                
                time.sleep(5)
                
                try:
                    self.close()
                except:
                    logger.warning("Error while closing WebDriver, ignoring...")
                finally:
                    self.setup_driver()
        
        return False

    def save_screenshot(self, filename):
        """Save a screenshot for debugging purposes."""
        try:
            filepath = self.logs_dir / filename
            self.driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}")

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    bot = None
    try:
        bot = UdioMusicBot(headless=False)
        bot.login()
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        if bot:
            bot.close()
