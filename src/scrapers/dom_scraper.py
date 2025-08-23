"""
DOM Scraper module for UI Manual Validator

This module provides functionality to scrape and analyze DOM elements
for UI validation purposes.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time
import json

logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Information about a scraped DOM element"""
    tag_name: str
    attributes: Dict[str, str]
    text_content: str
    inner_html: str
    xpath: str
    css_selector: str
    bounding_rect: Dict[str, float]
    is_visible: bool
    is_enabled: bool
    parent_info: Optional[Dict[str, str]] = None
    children_count: int = 0


@dataclass
class PageInfo:
    """Information about the scraped page"""
    url: str
    title: str
    viewport_size: Dict[str, int]
    elements: List[ElementInfo]
    timestamp: str
    load_time: float


class DOMScraper:
    """Scraper for DOM elements and page information"""

    def __init__(self, driver=None, implicit_wait: int = 10):
        """
        Initialize the DOM scraper
        
        Args:
            driver: WebDriver instance (Selenium, Playwright, etc.)
            implicit_wait: Implicit wait time in seconds
        """
        self.driver = driver
        self.implicit_wait = implicit_wait
        self.scraped_elements = []

    def set_driver(self, driver):
        """Set or update the WebDriver instance"""
        self.driver = driver

    def scrape_page(self, url: Optional[str] = None) -> PageInfo:
        """
        Scrape the entire page for element information
        
        Args:
            url: Optional URL to navigate to before scraping
            
        Returns:
            PageInfo object containing page and element data
        """
        if not self.driver:
            raise ValueError("WebDriver not initialized. Use set_driver() first.")

        start_time = time.time()
        
        if url:
            self.driver.get(url)
            time.sleep(2)  # Allow page to load

        # Get page information
        current_url = self.driver.current_url
        title = self.driver.title
        viewport_size = self._get_viewport_size()
        
        # Scrape all elements
        elements = self._scrape_all_elements()
        
        load_time = time.time() - start_time
        
        page_info = PageInfo(
            url=current_url,
            title=title,
            viewport_size=viewport_size,
            elements=elements,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            load_time=load_time
        )
        
        return page_info

    def find_elements_by_criteria(self, criteria: Dict[str, Any]) -> List[ElementInfo]:
        """
        Find elements matching specific criteria
        
        Args:
            criteria: Dictionary containing search criteria
                     - tag: HTML tag name
                     - class: CSS class name
                     - id: Element ID
                     - text: Text content (partial match)
                     - visible_only: Boolean to filter visible elements only
                     
        Returns:
            List of ElementInfo objects matching criteria
        """
        if not self.driver:
            raise ValueError("WebDriver not initialized. Use set_driver() first.")

        matching_elements = []
        
        # Build CSS selector based on criteria
        selector_parts = []
        
        if 'tag' in criteria:
            selector_parts.append(criteria['tag'])
        else:
            selector_parts.append('*')
            
        if 'id' in criteria:
            selector_parts.append(f'#{criteria["id"]}')
            
        if 'class' in criteria:
            selector_parts.append(f'.{criteria["class"]}')
            
        css_selector = ''.join(selector_parts)
        
        try:
            elements = self.driver.find_elements("css selector", css_selector)
            
            for element in elements:
                element_info = self._extract_element_info(element)
                
                # Apply additional filters
                if 'text' in criteria:
                    if criteria['text'].lower() not in element_info.text_content.lower():
                        continue
                        
                if criteria.get('visible_only', False) and not element_info.is_visible:
                    continue
                    
                matching_elements.append(element_info)
                
        except Exception as e:
            logger.error(f"Error finding elements with criteria {criteria}: {e}")
            
        return matching_elements

    def scrape_element_by_selector(self, selector: str, selector_type: str = 'css') -> Optional[ElementInfo]:
        """
        Scrape a specific element by selector
        
        Args:
            selector: CSS selector or XPath expression
            selector_type: Type of selector ('css' or 'xpath')
            
        Returns:
            ElementInfo object or None if element not found
        """
        if not self.driver:
            raise ValueError("WebDriver not initialized. Use set_driver() first.")

        try:
            if selector_type.lower() == 'xpath':
                element = self.driver.find_element("xpath", selector)
            else:
                element = self.driver.find_element("css selector", selector)
                
            return self._extract_element_info(element)
            
        except Exception as e:
            logger.warning(f"Element not found with {selector_type} selector '{selector}': {e}")
            return None

    def get_form_elements(self) -> List[ElementInfo]:
        """
        Get all form elements on the page
        
        Returns:
            List of ElementInfo objects for form elements
        """
        form_selectors = [
            'input', 'textarea', 'select', 'button',
            '[contenteditable="true"]', '[role="button"]',
            '[role="textbox"]', '[role="combobox"]'
        ]
        
        form_elements = []
        for selector in form_selectors:
            elements = self.find_elements_by_criteria({'tag': selector.split('[')[0]})
            form_elements.extend(elements)
            
        return form_elements

    def get_navigation_elements(self) -> List[ElementInfo]:
        """
        Get all navigation elements on the page
        
        Returns:
            List of ElementInfo objects for navigation elements
        """
        nav_selectors = [
            'a', 'nav', '[role="navigation"]',
            '[role="menubar"]', '[role="menu"]',
            '.nav', '.navbar', '.menu'
        ]
        
        nav_elements = []
        for selector in nav_selectors:
            if selector.startswith('.'):
                elements = self.find_elements_by_criteria({'class': selector[1:]})
            elif selector.startswith('['):
                # Handle attribute selectors
                continue  # Skip for now, would need more complex parsing
            else:
                elements = self.find_elements_by_criteria({'tag': selector})
            nav_elements.extend(elements)
            
        return nav_elements

    def _scrape_all_elements(self) -> List[ElementInfo]:
        """Scrape all elements on the page"""
        elements = []
        
        try:
            # Get all elements with any tag
            all_elements = self.driver.find_elements("css selector", "*")
            
            for element in all_elements:
                try:
                    element_info = self._extract_element_info(element)
                    elements.append(element_info)
                except Exception as e:
                    logger.debug(f"Error extracting info for element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping all elements: {e}")
            
        return elements

    def _extract_element_info(self, element) -> ElementInfo:
        """Extract information from a WebDriver element"""
        try:
            # Basic element information
            tag_name = element.tag_name
            attributes = {}
            
            # Try to get common attributes
            common_attrs = ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'alt', 'title']
            for attr in common_attrs:
                value = element.get_attribute(attr)
                if value:
                    attributes[attr] = value
            
            # Get text content
            text_content = element.text or ''
            inner_html = element.get_attribute('innerHTML') or ''
            
            # Generate XPath and CSS selector
            xpath = self._generate_xpath(element)
            css_selector = self._generate_css_selector(element)
            
            # Get bounding rectangle
            rect = element.rect
            bounding_rect = {
                'x': rect['x'],
                'y': rect['y'],
                'width': rect['width'],
                'height': rect['height']
            }
            
            # Check visibility and enabled state
            is_visible = element.is_displayed()
            is_enabled = element.is_enabled()
            
            # Get parent information
            parent_info = self._get_parent_info(element)
            
            # Count children
            children = element.find_elements("css selector", "*")
            children_count = len(children)
            
            return ElementInfo(
                tag_name=tag_name,
                attributes=attributes,
                text_content=text_content,
                inner_html=inner_html,
                xpath=xpath,
                css_selector=css_selector,
                bounding_rect=bounding_rect,
                is_visible=is_visible,
                is_enabled=is_enabled,
                parent_info=parent_info,
                children_count=children_count
            )
            
        except Exception as e:
            logger.error(f"Error extracting element info: {e}")
            raise

    def _generate_xpath(self, element) -> str:
        """Generate XPath for an element"""
        try:
            # Use JavaScript to generate XPath
            xpath_script = """
            function getElementXPath(element) {
                if (element.id !== '') {
                    return 'id("' + element.id + '")';
                }
                if (element === document.body) {
                    return element.tagName;
                }
                var ix = 0;
                var siblings = element.parentNode.childNodes;
                for (var i = 0; i < siblings.length; i++) {
                    var sibling = siblings[i];
                    if (sibling === element) {
                        return getElementXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            return getElementXPath(arguments[0]);
            """
            return self.driver.execute_script(xpath_script, element)
        except:
            return f"//{element.tag_name}"

    def _generate_css_selector(self, element) -> str:
        """Generate CSS selector for an element"""
        try:
            # Simple CSS selector generation
            tag = element.tag_name.lower()
            
            # Try ID first
            element_id = element.get_attribute('id')
            if element_id:
                return f"{tag}#{element_id}"
            
            # Try class
            class_name = element.get_attribute('class')
            if class_name:
                classes = class_name.strip().split()
                if classes:
                    return f"{tag}.{'.'.join(classes)}"
            
            return tag
            
        except:
            return element.tag_name.lower()

    def _get_parent_info(self, element) -> Optional[Dict[str, str]]:
        """Get basic information about the parent element"""
        try:
            parent = element.find_element("xpath", "..")
            if parent:
                return {
                    'tag_name': parent.tag_name,
                    'id': parent.get_attribute('id') or '',
                    'class': parent.get_attribute('class') or ''
                }
        except:
            pass
        return None

    def _get_viewport_size(self) -> Dict[str, int]:
        """Get the current viewport size"""
        try:
            size = self.driver.get_window_size()
            return {
                'width': size['width'],
                'height': size['height']
            }
        except:
            return {'width': 0, 'height': 0}

    def export_scraped_data(self, output_path: str, data: Union[PageInfo, List[ElementInfo]]):
        """
        Export scraped data to JSON file
        
        Args:
            output_path: Path to save the JSON file
            data: PageInfo object or list of ElementInfo objects
        """
        try:
            if isinstance(data, PageInfo):
                # Convert PageInfo to dict
                export_data = {
                    'url': data.url,
                    'title': data.title,
                    'viewport_size': data.viewport_size,
                    'timestamp': data.timestamp,
                    'load_time': data.load_time,
                    'elements': [self._element_to_dict(elem) for elem in data.elements]
                }
            else:
                # List of ElementInfo objects
                export_data = {
                    'elements': [self._element_to_dict(elem) for elem in data],
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'count': len(data)
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Scraped data exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting scraped data: {e}")

    def _element_to_dict(self, element: ElementInfo) -> Dict[str, Any]:
        """Convert ElementInfo to dictionary for JSON serialization"""
        return {
            'tag_name': element.tag_name,
            'attributes': element.attributes,
            'text_content': element.text_content,
            'inner_html': element.inner_html[:500] + '...' if len(element.inner_html) > 500 else element.inner_html,
            'xpath': element.xpath,
            'css_selector': element.css_selector,
            'bounding_rect': element.bounding_rect,
            'is_visible': element.is_visible,
            'is_enabled': element.is_enabled,
            'parent_info': element.parent_info,
            'children_count': element.children_count
        }