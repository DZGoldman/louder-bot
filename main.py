import os
import time
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Union
import undetected_chromedriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

from email_client import get_link_from_email
from prompt_generator import generate_prompt 

from fake_useragent import UserAgent
import random
import argparse


parser = argparse.ArgumentParser(description="A simple command line argument example.")

parser.add_argument('--headless', type=bool)
args = parser.parse_args()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/udio_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

download_dir = os.getcwd() + "/song_downloads/"

def count_files_in_directory(directory):
    return sum(1 for entry in os.listdir(directory) if os.path.isfile(os.path.join(directory, entry)))

class LoginError(Exception):
    """Custom exception for login failures"""
    pass

class UdioMusicBot:
    def __init__(self, headless: bool = False, max_retries: int = 5, stealth = True):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        self.headless = headless
        self.stealth = stealth
        self.max_retries = max_retries
        
        # Get credentials from environment
        self.email = os.getenv("GOOGLE_EMAIL", "").strip()
        if not self.email:
             raise Exception("GOOGLE_EMAIL env variable not provided")

        logger.info(f"Initializing UdioMusicBot with email: {self.email[:3]}...{self.email[-10:]}")
        self.setup_driver()
        self.driver = None
        
    def setup_driver(self):
        download_dir = os.getcwd() + "/song_downloads/"  # Adjust to your desired path
        try:
            chrome_options = Options()
            # Set capabilities
            capabilities = {
                "browserName": "chrome",
                "goog:chromeOptions": {
                    "prefs": {
                        "download.default_directory": download_dir,
                        "download.prompt_for_download": False,
                        "download.directory_upgrade": True,
                        "safebrowsing.enabled": True
                    }
                }
            }

            if self.headless:
                chrome_options.add_argument('--headless=new')

            if self.stealth:
                self.driver = undetected_chromedriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, desired_capabilities=capabilities)
            else:
                prefs = {
                    "download.default_directory": download_dir, 
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True
                }
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_experimental_option("prefs", prefs)

                # Initialize the WebDriver
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


            self.driver.set_window_size(1620, 1080)
            self.driver.set_page_load_timeout(120)

            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")

    def try_click(self, element):
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
                logger.info(f"Successfully clicked element using {method_name}")
                time.sleep(1)
                return True
            except Exception as e:
                logger.debug(f"{method_name} failed: {str(e)}")
                continue

    def wait_and_click(self, selectors: Union[str, List[str]], element_name: str = "element", timeout: int = 20, wait_time = 5) -> bool:
        if isinstance(selectors, str):
            selectors = [selectors]
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            for selector in selectors:
                try:
                    logger.debug(f"Looking for {element_name} with selector: {selector}")
                    element = WebDriverWait(self.driver, wait_time).until(
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
                time.sleep(3)  # Wait for dynamic content
                
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
                time.sleep(5)
                for i in range(1, 4):
                    try:
                        logger.info(f"Getting link from email: attempt {i}")
                        link = get_link_from_email()
                        logger.info("Succesfully retrieved link from email")
                        # TODO: click resend if needed
                        self.driver.get(link)
                        logger.info(f"Navigated to page: {self.driver.current_url}")
                        return True
                    except Exception as e:
                        logger.error("Could not get link from email; clicking resend and tryign again")
                        self.wait_and_click(continue_button_selectors, "Continue/Login button")
                        time.sleep(5)
                        

            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                retry_count+=1 



    def create_song(self):
        # once successfully logged in...
        # TODO: navigate to home if needed 
        
        retry_count = 0
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
                    raise Exception("Prompt field not found")

                prompt_field.clear()
                time.sleep(1)
                prompt = generate_prompt()
                logger.info(f"Prompt: {prompt}")
                self.slow_type(prompt_field,prompt)
                time.sleep(3)

                self.wait_and_click("//button[contains(text(), 'Create')]", "Create song button")
                               
                logger.info("Successfully create")
                time.sleep(2)
                return len(self.driver.find_elements(By.XPATH, "//button[@aria-label='like']"))
            except Exception as e:
                 logger.error(f"Create song error: {str(e)}")
                 retry_count+=1 
        return False
    def get_latest_song_sharable_link(self, previous_likes=0):
         # TODO: navigate to home if needed 
        #  TODO: retries? 

        if previous_likes:
            total_wait_time_seconds = 60 * 15
            time_between_attempts_seconds = 10
            attempts_left = total_wait_time_seconds / time_between_attempts_seconds

            like_elements = self.driver.find_elements(By.XPATH, "//button[@aria-label='like']")
            while len(like_elements) == previous_likes and attempts_left:
                print(f"Still only {len(like_elements)} found; waiting {time_between_attempts_seconds} seconds")
                # self.driver.save_screenshot(f'screenshots/{int(time.time())}.png')
                time.sleep(time_between_attempts_seconds)
                like_elements = self.driver.find_elements(By.XPATH, "//button[@aria-label='like']")
            print(f"{len(like_elements)} found")

        first_like_element = self.driver.find_elements(By.XPATH, "//button[@aria-label='like']")[0]
        dropdown =  first_like_element.find_element(By.XPATH, "parent::*/following-sibling::*[1]")

        # sanity check
        if dropdown.get_attribute("aria-haspopup") != "menu":
            logger.error("Failed aria-haspopup sanity check")

        self.try_click(dropdown)
        time.sleep(2)
        # share_button = self.driver.find_element(By.XPATH, "//div[@role='menuitem' and text()='Share']")
        self.wait_and_click("//div[@role='menuitem' and text()='Share']")
        time.sleep(2)

        link_spans = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'https://www.udio.com/songs/')]")
        # sanity check
        if len(link_spans) > 1:
            logger.error("Failed span sanity check")
            # TODO: handle

        return link_spans[0].text

    def download_song(self, share_url):
        self.driver.get(share_url)
        time.sleep(3)

        self.wait_and_click("//button[@title='Download media']")
        logger.info("Clicked 'Download media'")
        time.sleep(2)
        
        self.wait_and_click("//button/div[text()='Generate Video']")
        logger.info("Clicked 'Generate Video'")

        file_count_pre_download = count_files_in_directory(download_dir)
        
        self.wait_and_click('//button[count(*)=2 and *[1][name()="svg"] and *[2][name()="div" and text()="Download"]]', wait_time = 300)
        logger.info("Clicked 'Download'")

        file_count_download = count_files_in_directory(download_dir)
        logger.info("Waiting for download")
        for _ in range(0,100):
            if count_files_in_directory(download_dir) > file_count_pre_download:
                logger.info("Done")
                return
            else:
                time.sleep(5)
        raise Exception("Download failed?")


    def slow_type(self, element, text, delay_range=(0.1, 0.2)):
        element.send_keys(text)
        # TODO

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
    stealth_bot = None
    reg_bot = None
    start_time = time.time()
    out = None
    
    try:
        stealth_bot = UdioMusicBot(headless=bool(args.headless))
        if stealth_bot.login():
            logger.info("Login successful")
        else:
            logger.error("Login failed")
        
        likes = stealth_bot.create_song()
        if likes == False:
            logger.error("Create song failed")  
        else:
            sharable_link = stealth_bot.get_latest_song_sharable_link(likes)
            stealth_bot.close()
            reg_bot = UdioMusicBot(headless=bool(args.headless), stealth = False )
            reg_bot.download_song(sharable_link)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        logger.debug(f"Stack trace: {traceback.format_exc()}")
    finally:
        if stealth_bot:
            print("closing stealth_bot now:")
            stealth_bot.close()
        if reg_bot:
            print("closing reg_bot now:")
            reg_bot.close()
        if out:
            out.release()  # Release the video file
            
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
      

        print(f"Total time: {minutes} minutes and {seconds} seconds")

