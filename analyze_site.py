import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_suno_site():
    """Analyze the Suno.com site structure and save relevant selectors."""
    driver = None
    try:
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        logger.info("Analyzing Suno.com site structure...")
        driver.get("https://www.suno.com")
        
        # Wait for page load and dynamic content
        time.sleep(5)
        
        # Find all interactive elements with additional selectors
        selectors_to_check = {
            'login_buttons': {
                'xpath': [
                    "//button[contains(@class, 'bg-primary') and contains(text(), 'Sign')]",
                    "//button[contains(@class, 'text-primary-foreground') and contains(text(), 'Sign')]",
                    "//div[contains(@class, 'flex') and contains(text(), 'Sign')]",
                    "//a[contains(text(), 'Sign')]"
                ],
                'attributes': ['class', 'id', 'text', 'aria-label', 'type', 'href']
            },
            'email_fields': {
                'xpath': [
                    "//input[@type='email']",
                    "//input[contains(@class, 'form-input')][@type='email']",
                    "//input[contains(@name, 'email')]",
                    "//input[contains(@placeholder, 'email')]"
                ],
                'attributes': ['class', 'id', 'placeholder', 'type', 'name']
            },
            'continue_buttons': {
                'xpath': [
                    "//button[contains(@class, 'bg-primary')]",
                    "//button[contains(text(), 'Continue')]",
                    "//button[@type='submit']"
                ],
                'attributes': ['class', 'id', 'text', 'type']
            }
        }
        
        site_analysis = {
            'current_url': driver.current_url,
            'title': driver.title,
            'elements': {}
        }
        
        for elem_type, config in selectors_to_check.items():
            site_analysis['elements'][elem_type] = []
            
            for xpath in config['xpath']:
                elements = driver.find_elements(By.XPATH, xpath)
                
                for elem in elements:
                    try:
                        elem_info = {
                            'xpath': xpath,
                            'tag_name': elem.tag_name,
                            'is_displayed': elem.is_displayed(),
                            'location': {'x': elem.location['x'], 'y': elem.location['y']},
                            'attributes': {}
                        }
                        
                        # Get specified attributes
                        for attr in config['attributes']:
                            if attr == 'text':
                                elem_info['attributes'][attr] = elem.text
                            else:
                                elem_info['attributes'][attr] = elem.get_attribute(attr)
                        
                        # Get full HTML for debugging
                        elem_info['html'] = elem.get_attribute('outerHTML')
                        
                        site_analysis['elements'][elem_type].append(elem_info)
                    except Exception as e:
                        logger.warning(f"Error analyzing element: {str(e)}")
                        continue
        
        # Try clicking the sign in button to analyze modal
        sign_in_button = None
        for xpath in selectors_to_check['login_buttons']['xpath']:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for elem in elements:
                    if elem.is_displayed() and "Sign" in elem.text:
                        sign_in_button = elem
                        break
                if sign_in_button:
                    break
            except Exception:
                continue
                
        if sign_in_button:
            logger.info("Found Sign In button, clicking to analyze modal...")
            sign_in_button.click()
            time.sleep(2)
            
            # Analyze modal content
            site_analysis['modal'] = {
                'url': driver.current_url,
                'elements': {}
            }
            
            for elem_type, config in selectors_to_check.items():
                if elem_type != 'login_buttons':  # Skip login buttons for modal
                    site_analysis['modal']['elements'][elem_type] = []
                    
                    for xpath in config['xpath']:
                        elements = driver.find_elements(By.XPATH, xpath)
                        
                        for elem in elements:
                            try:
                                if elem.is_displayed():
                                    elem_info = {
                                        'xpath': xpath,
                                        'tag_name': elem.tag_name,
                                        'is_displayed': True,
                                        'location': {'x': elem.location['x'], 'y': elem.location['y']},
                                        'attributes': {}
                                    }
                                    
                                    for attr in config['attributes']:
                                        if attr == 'text':
                                            elem_info['attributes'][attr] = elem.text
                                        else:
                                            elem_info['attributes'][attr] = elem.get_attribute(attr)
                                            
                                    elem_info['html'] = elem.get_attribute('outerHTML')
                                    site_analysis['modal']['elements'][elem_type].append(elem_info)
                            except Exception as e:
                                logger.warning(f"Error analyzing modal element: {str(e)}")
                                continue
        
        # Save analysis results
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)
        
        with open(analysis_dir / "suno_site_analysis.json", 'w') as f:
            json.dump(site_analysis, f, indent=2)
            
        logger.info(f"Analysis complete. Current URL: {site_analysis['current_url']}")
        logger.info(f"Page title: {site_analysis['title']}")
        logger.info("Element counts:")
        for elem_type, elements in site_analysis['elements'].items():
            visible_elements = [e for e in elements if e.get('is_displayed', False)]
            logger.info(f"- {elem_type}: {len(elements)} (visible: {len(visible_elements)})")
            
            # Log details of visible elements
            for elem in visible_elements:
                logger.debug(f"  Visible {elem_type}:")
                logger.debug(f"    XPath: {elem['xpath']}")
                logger.debug(f"    Text: {elem['attributes'].get('text', '')}")
                logger.debug(f"    Classes: {elem['attributes'].get('class', '')}")
                
        if 'modal' in site_analysis:
            logger.info("\nModal analysis:")
            for elem_type, elements in site_analysis['modal']['elements'].items():
                visible_elements = [e for e in elements if e.get('is_displayed', False)]
                logger.info(f"- {elem_type}: {len(visible_elements)} visible elements")
                for elem in visible_elements:
                    logger.debug(f"  {elem_type}:")
                    logger.debug(f"    XPath: {elem['xpath']}")
                    logger.debug(f"    Attributes: {elem['attributes']}")
            
    except Exception as e:
        logger.error(f"Error analyzing site: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    analyze_suno_site()
