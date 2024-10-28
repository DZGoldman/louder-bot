import os
import time
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Union
# import undetected_chromedriver as webdriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from email_client import get_link_from_email
from prompt_generator import generate_prompt 

from fake_useragent import UserAgent
import random

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
        if not self.email:
             raise ("GOOGLE_EMAIL env variable not provided")

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


            ua = UserAgent()
            user_agent = ua.random
            chrome_options.add_argument(f'user-agent={user_agent}')


            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            self.driver.set_page_load_timeout(30)

            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def wait_and_click(self, selectors: Union[str, List[str]], element_name: str = "element", timeout: int = 20, target_text: str="") -> bool:
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

                    # if target_text:
                    #     if element.text != target_text: 
                    #         logger.debug(f"Skipping element with text: {element.text}")
                    #         continue
                    #     else:
                    #         logger.info(f"Element with text: {element.text} found")
                    
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
                continue_button_selectors = [
                    "//button[@type='submit']",

                ]
                
                if not self.wait_and_click(continue_button_selectors, "Continue/Login button"):
                    raise LoginError("Could not find or click Continue/Login button")
                
                logger.info("Successfully clicked continue/login button")
                time.sleep(8)
                logger.info("Getting link from email:")
                link = get_link_from_email()
                logger.info("Succesfully retrieved link from email")
                self.driver.get(link)
                logger.info(f"Navigated to page: {self.driver.current_url}")
                return True

            except Exception as e:
                 logger.error(f"Login error: {str(e)}")


    def create_song(self):
        # once successfully logged in...
        retry_count = 0
        self.random_mouse_movement()
        while retry_count < self.max_retries:
            logger.info(f"On page: {self.driver.current_url}")
            try:
                prompt_field_selector =  "//input[@type='prompt']"
                time.sleep(5)

                prompt_field = WebDriverWait(self.driver, 30).until(
                                    EC.presence_of_element_located((By.XPATH, prompt_field_selector))
                                )
                if prompt_field.is_displayed():
                    logger.info(f"Found prompt field")
                else:
                    # TODO
                    print("no field found")

                prompt_field.clear()
                time.sleep(1)
                self.random_mouse_movement()
                slow_type(prompt_field,generate_prompt())
                self.random_mouse_movement()
                time.sleep(3)

                self.wait_and_click("//button[contains(text(), 'Create')]", "Create song button")
                               
                logger.info("Successfully create")
                # captcha? dead end?
                time.sleep(30)
                return True
            except Exception as e:
                 logger.error(f"Create song error: {str(e)}")

    def random_mouse_movement(self, duration=3):
        try:
            action = ActionChains(self.driver)
            start_time = time.time()
            
            # Get the size of the window
            width = self.driver.execute_script("return window.innerWidth")
            height = self.driver.execute_script("return window.innerHeight")

            while time.time() - start_time < duration:
                # Generate random x and y coordinates within the window's bounds
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                
                # Move the mouse to a new location
                action.move_by_offset(x, y).perform()
                
                # Reset the action chain and add a random delay
                action.reset_actions()
                time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.error(f"Mouse movement failed: {str(e)}")


    def slow_type(element, text, delay_range=(0.1, 0.3)):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*delay_range))

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

        bot.create_song()
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        logger.debug(f"Stack trace: {traceback.format_exc()}")
    finally:
        if bot:
            bot.close()
