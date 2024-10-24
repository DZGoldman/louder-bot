import os
import time
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    def __init__(self, headless: bool = False, max_retries: int = 3):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        self.headless = headless
        self.max_retries = max_retries
        
        # Get credentials from environment
        self.email = os.getenv("GOOGLE_EMAIL", "").strip()
        self.password = os.getenv("GOOGLE_PASSWORD", "").strip()
        
        if not self.email or not self.password:
            raise ValueError("Email or password not found in environment variables")
            
        logger.info(f"Initializing UdioMusicBot with email: {self.email[:3]}...{self.email[-10:]}")
        self.setup_driver()

    def setup_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            self.driver.set_page_load_timeout(30)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def wait_and_click(self, selectors: Union[str, List[str]], element_name: str = "element", timeout: int = 20) -> bool:
        if isinstance(selectors, str):
            selectors = [selectors]
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            for selector in selectors:
                try:
                    logger.debug(f"Looking for {element_name} with selector: {selector}")
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    
                    if not element.is_displayed():
                        continue
                        
                    # Scroll into view and wait
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(2)
                    
                    # Try multiple click methods
                    click_methods = [
                        lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                        lambda: self.driver.execute_script("arguments[0].click();", element),
                        lambda: element.click()
                    ]
                    
                    for click_method in click_methods:
                        try:
                            click_method()
                            time.sleep(2)
                            return True
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
                    
            time.sleep(1)
            
        logger.error(f"Failed to click {element_name}")
        return False

    def login(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.info(f"Starting login attempt {retry_count + 1}/{self.max_retries}")
                
                # Load homepage
                self.driver.get("https://www.udio.com/home")
                time.sleep(5)  # Wait for dynamic content
                
                # Sign in button selectors
                sign_in_selectors = [
                    "//button[contains(@class, 'bg-quaternary')]",
                    "//button[contains(@class, 'text-primary-foreground')]",
                    "//button[contains(text(), 'Sign')]",
                    "//button[contains(@class, 'flex') and contains(text(), 'Sign')]"
                ]
                
                if not self.wait_and_click(sign_in_selectors, "Sign in button"):
                    raise LoginError("Could not find or click Sign in button")
                
                time.sleep(3)
                
                # Find and fill email field
                email_field_selectors = [
                    "//input[@type='email']",
                    "//input[contains(@name, 'email')]",
                    "//input[contains(@class, 'form-input')]"
                ]
                
                email_field = None
                for selector in email_field_selectors:
                    try:
                        email_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if email_field.is_displayed():
                            break
                    except Exception:
                        continue
                
                if not email_field:
                    raise LoginError("Email field not found")
                
                # Enter email and password
                email_field.clear()
                time.sleep(1)
                email_field.send_keys(self.email)
                time.sleep(1)

                # Enter password if field exists
                password_field_selectors = [
                    "//input[@type='password']",
                    "//input[contains(@name, 'password')]"
                ]
                
                for selector in password_field_selectors:
                    try:
                        password_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if password_field.is_displayed():
                            password_field.clear()
                            time.sleep(1)
                            password_field.send_keys(self.password)
                            time.sleep(1)
                            break
                    except Exception:
                        continue
                
                # Click login/continue button
                continue_button_selectors = [
                    "//button[contains(@class, 'bg-quaternary')]",
                    "//button[contains(text(), 'Continue')]",
                    "//button[contains(text(), 'Login')]",
                    "//button[@type='submit']"
                ]
                
                if not self.wait_and_click(continue_button_selectors, "Continue/Login button"):
                    raise LoginError("Could not find or click Continue/Login button")
                
                # Wait for successful login
                WebDriverWait(self.driver, 20).until(
                    lambda driver: any(path in driver.current_url 
                                     for path in ["/dashboard", "/home", "/studio"])
                )
                
                logger.info("Successfully logged in")
                return True
                
            except Exception as e:
                logger.error(f"Login attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                
                if retry_count >= self.max_retries:
                    raise LoginError(f"Login failed after {self.max_retries} attempts")
                
                self.restart_session()
                time.sleep(5)
        
        return False

    def restart_session(self):
        try:
            self.close()
        except Exception:
            pass
        finally:
            time.sleep(2)
            self.setup_driver()

    def close(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    bot = None
    try:
        bot = UdioMusicBot(headless=False)
        if bot.login():
            logger.info("Login successful")
        else:
            logger.error("Login failed")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        if bot:
            bot.close()
