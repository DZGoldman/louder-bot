import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_login_elements():
    analysis_file = Path("analysis/site_analysis.json")
    
    if not analysis_file.exists():
        logger.error("Analysis file not found")
        return
        
    try:
        with open(analysis_file) as f:
            data = json.load(f)
            
        logger.info(f"Analyzing site: {data['current_url']}")
        logger.info(f"Page title: {data['title']}")
        
        # Search for login-related elements
        login_selectors = []
        
        # Look through all elements
        for elem_type, elements in data['elements'].items():
            for elem in elements:
                # Check various attributes for login-related text
                text = elem.get('text', '').lower()
                href = elem.get('href', '').lower()
                aria = elem.get('aria_label', '').lower()
                cls = elem.get('class', '').lower()
                
                # Skip if element is not displayed
                if not elem.get('is_displayed', False):
                    continue
                    
                # Build potential selectors
                if any(term in text + href + aria for term in ['sign in', 'login', 'log in']):
                    if elem_type == 'links' and href:
                        login_selectors.append(f"//a[contains(@href, '{href}')]")
                    elif elem_type == 'buttons':
                        if text:
                            login_selectors.append(f"//button[contains(text(), '{text}')]")
                        if aria:
                            login_selectors.append(f"//button[contains(@aria-label, '{aria}')]")
                    elif cls:
                        login_selectors.append(f"//*[contains(@class, '{cls}')]")
        
        # Log findings
        logger.info(f"\nFound {len(login_selectors)} potential login selectors:")
        for selector in login_selectors:
            logger.info(f"- {selector}")
            
        return login_selectors
            
    except Exception as e:
        logger.error(f"Error analyzing login elements: {e}")
        return None

if __name__ == "__main__":
    analyze_login_elements()
