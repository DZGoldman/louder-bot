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
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if not element.is_displayed():
                        logger.debug(f"Element found but not displayed: {selector}")
                        continue
                        
                    # Log element state
                    logger.debug(f"Element found - Tag: {element.tag_name}, Text: {element.text}, "
                               f"Location: {element.location}, Size: {element.size}")
                    
                    # Scroll into view and wait
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # Try multiple click methods
                    click_methods = [
                        (lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                         "ActionChains click"),
                        (lambda: self.driver.execute_script("arguments[0].click();", element),
                         "JavaScript click"),
                        (lambda: element.click(),
                         "Regular click")
                    ]
                    
                    for click_method, method_name in click_methods:
                        try:
                            logger.debug(f"Attempting {method_name}")
                            click_method()
                            logger.info(f"Successfully clicked {element_name} using {method_name}")
                            time.sleep(1)
                            return True
                        except Exception as e:
                            logger.debug(f"{method_name} failed: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {str(e)}")
                    # Log the current page state
                    logger.debug(f"Current URL: {self.driver.current_url}")
                    logger.debug(f"Page title: {self.driver.title}")
                    continue
                    
            time.sleep(1)
            
        logger.error(f"Failed to click {element_name} after {timeout} seconds")
        return False

    def login(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                logger.info(f"Starting login attempt {retry_count + 1}/{self.max_retries}")
                
                # Load homepage
                self.driver.get("https://www.udio.com")
                logger.info(f"Loaded homepage: {self.driver.current_url}")
                time.sleep(5)  # Wait for dynamic content
                
                # Log page state
                logger.debug(f"Page title: {self.driver.title}")
                logger.debug(f"Current URL: {self.driver.current_url}")
                
                # Updated sign in button selectors with additional options
                sign_in_selectors = [
                    "//button[contains(text(), 'Log')]",
                    "//button[contains(text(), 'Sign')]",
                    "//a[contains(text(), 'Log')]",
                    "//a[contains(text(), 'Sign')]",
                    "//div[contains(@class, 'login')]//button",
                    "//div[contains(@class, 'sign-in')]//button",
                    "//button[contains(@class, 'login')]",
                    "//button[contains(@class, 'sign-in')]"
                ]
                
                if not self.wait_and_click(sign_in_selectors, "Sign in button"):
                    # Try to find any visible buttons for debugging
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.debug("Visible buttons on page:")
                    for btn in buttons:
                        if btn.is_displayed():
                            logger.debug(f"Button text: {btn.text}, class: {btn.get_attribute('class')}")
                    raise LoginError("Could not find or click Sign in button")
                
                time.sleep(3)
                logger.info("Successfully clicked sign in button")
                
                # Updated email field selectors
                email_field_selectors = [
                    "//input[@type='email']",
                    "//input[contains(@name, 'email')]",
                    "//input[contains(@placeholder, 'mail')]",
                    "//input[contains(@id, 'email')]",
                    "//input[contains(@class, 'email')]"
                ]
                
                email_field = None
                for selector in email_field_selectors:
                    try:
                        email_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if email_field.is_displayed():
                            logger.info(f"Found email field with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Email field selector failed: {selector} - {str(e)}")
                        continue
                
                if not email_field:
                    # Log all input fields for debugging
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    logger.debug("Visible input fields:")
                    for inp in inputs:
                        if inp.is_displayed():
                            logger.debug(f"Input type: {inp.get_attribute('type')}, "
                                       f"name: {inp.get_attribute('name')}, "
                                       f"id: {inp.get_attribute('id')}")
                    raise LoginError("Email field not found")
                
                # Enter email
                email_field.clear()
                time.sleep(1)
                email_field.send_keys(self.email)
                logger.info("Successfully entered email")
                time.sleep(1)

                # Updated password field selectors
                password_field_selectors = [
                    "//input[@type='password']",
                    "//input[contains(@name, 'password')]",
                    "//input[contains(@placeholder, 'assword')]",
                    "//input[contains(@id, 'password')]",
                    "//input[contains(@class, 'password')]"
                ]
                
                password_entered = False
                for selector in password_field_selectors:
                    try:
                        password_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if password_field.is_displayed():
                            password_field.clear()
                            time.sleep(1)
                            password_field.send_keys(self.password)
                            logger.info("Successfully entered password")
                            password_entered = True
                            time.sleep(1)
                            break
                    except Exception as e:
                        logger.debug(f"Password field selector failed: {selector} - {str(e)}")
                        continue
                
                # Updated continue/login button selectors
                continue_button_selectors = [
                    "//button[contains(text(), 'Log')]",
                    "//button[contains(text(), 'Sign')]",
                    "//button[@type='submit']",
                    "//input[@type='submit']",
                    "//button[contains(@class, 'login')]",
                    "//button[contains(@class, 'sign-in')]",
                    "//button[contains(@class, 'submit')]"
                ]
                
                if not self.wait_and_click(continue_button_selectors, "Continue/Login button"):
                    raise LoginError("Could not find or click Continue/Login button")
                
                logger.info("Successfully clicked continue/login button")
                
                # Wait for successful login with enhanced checks
                success_indicators = [
                    EC.url_contains("/dashboard"),
                    EC.url_contains("/home"),
                    EC.url_contains("/studio"),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'user')]")),
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'user')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'profile')]"))
                ]
                
                for indicator in success_indicators:
                    try:
                        WebDriverWait(self.driver, 10).until(indicator)
                        logger.info(f"Login verified with indicator: {indicator}")
                        return True
                    except Exception as e:
                        logger.debug(f"Login verification indicator failed: {str(e)}")
                        continue
                
                # If we reach here, login verification failed
                logger.error("Login verification failed")
                logger.debug(f"Current URL after login attempt: {self.driver.current_url}")
                logger.debug(f"Page title after login attempt: {self.driver.title}")
                
                raise LoginError("Login verification failed")
                
            except Exception as e:
                logger.error(f"Login attempt {retry_count + 1} failed: {str(e)}")
                logger.debug(f"Stack trace: {traceback.format_exc()}")
                retry_count += 1
                
                if retry_count >= self.max_retries:
                    logger.error(f"Login failed after {self.max_retries} attempts")
                    raise LoginError(f"Login failed after {self.max_retries} attempts")
                
                self.restart_session()
                time.sleep(5)
        
        return False

    def restart_session(self):
        try:
            self.close()
        except Exception as e:
            logger.error(f"Error during session restart: {str(e)}")
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
        logger.debug(f"Stack trace: {traceback.format_exc()}")
    finally:
        if bot:
            bot.close()
