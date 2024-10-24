import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
from pathlib import Path

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
        chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        logger.info("Analyzing Suno.com site structure...")
        driver.get("https://suno.com")
        
        # Wait for page load
        driver.implicitly_wait(10)
        
        # Find all possible login-related elements
        selectors_to_check = {
            'links': "//a",
            'buttons': "//button",
            'divs': "//div[@role='button']"
        }
        
        site_analysis = {
            'current_url': driver.current_url,
            'title': driver.title,
            'elements': {}
        }
        
        for name, selector in selectors_to_check.items():
            elements = driver.find_elements(By.XPATH, selector)
            site_analysis['elements'][name] = []
            
            for elem in elements:
                try:
                    elem_info = {
                        'tag_name': elem.tag_name,
                        'text': elem.text,
                        'class': elem.get_attribute('class'),
                        'href': elem.get_attribute('href') if elem.tag_name == 'a' else None,
                        'id': elem.get_attribute('id'),
                        'aria_label': elem.get_attribute('aria-label'),
                        'is_displayed': elem.is_displayed(),
                        'location': {'x': elem.location['x'], 'y': elem.location['y']}
                    }
                    site_analysis['elements'][name].append(elem_info)
                except:
                    continue
        
        # Save analysis results
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)
        
        with open(analysis_dir / "site_analysis.json", 'w') as f:
            json.dump(site_analysis, f, indent=2)
            
        logger.info(f"Analysis complete. Current URL: {site_analysis['current_url']}")
        logger.info(f"Page title: {site_analysis['title']}")
        logger.info("Element counts:")
        for elem_type, elements in site_analysis['elements'].items():
            logger.info(f"- {elem_type}: {len(elements)}")
            
    except Exception as e:
        logger.error(f"Error analyzing site: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    analyze_suno_site()
