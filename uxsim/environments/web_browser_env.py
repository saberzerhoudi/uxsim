import asyncio
import json
import logging
import os
import time
import traceback
import re
from typing import Any, Dict, List, Optional, Callable

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException
)

from ..core.types import Action, Observation, ActionType
from ..core.exceptions import EnvironmentException
from .base_env import BaseEnvironment

logger = logging.getLogger(__name__)


class WebBrowserEnv(BaseEnvironment):
    """Real web browser environment using Selenium"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.driver = None
        # Check environment variable first, then config, with True as default
        self.headless = os.getenv("HEADLESS", "true").lower() != "false"
        if "headless" in config:
            self.headless = config["headless"]
        self.start_url = config.get("start_url", "https://www.google.com")
        self.recipes = config.get("recipes", [])
        self.max_wait_time = config.get("max_wait_time", 10)
        self.current_url = ""
        self.clickables = {}
        self.inputs = {}
        self.selects = {}
        
    async def _setup_driver(self):
        """Initialize the Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                # These options are safe for headless mode
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
            else:
                # For GUI mode, use minimal options to avoid conflicts
                logger.info("Setting up Chrome in GUI mode (non-headless)")
            
            # Common options for both modes
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            
            # Additional options for stability
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver with webdriver-manager for automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_window_size(1280, 720)
            
            logger.info(f"Chrome WebDriver initialized successfully (headless: {self.headless})")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise EnvironmentException(f"Failed to setup browser: {e}")
    
    async def observe(self) -> Observation:
        """Get current observation from the browser"""
        try:
            if not self.driver:
                await self._setup_driver()
                
            # Wait for page to load
            WebDriverWait(self.driver, self.max_wait_time).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Get page content
            page_content = self.driver.page_source
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # Process page with recipes to extract interactions
            await self._process_page_with_recipes()
            
            # Create observation
            observation = Observation(
                page_content=self._extract_text_content(),
                url=current_url,
                clickables=list(self.clickables.values()),
                inputs=list(self.inputs.values()),
                selects=list(self.selects.values()),
                metadata={
                    "title": page_title,
                    "page_length": len(page_content)
                }
            )
            
            self.current_url = current_url
            logger.info(f"Observed page: {current_url}")
            
            return observation
            
        except Exception as e:
            logger.error(f"Error observing environment: {e}")
            return Observation(
                error_message=f"Failed to observe environment: {e}",
                url=self.current_url
            )
    
    async def step(self, action: Action) -> Observation:
        """Execute action and return new observation"""
        try:
            if not self.driver:
                raise EnvironmentException("Browser not initialized")
            
            error_message = None
            
            # Execute action based on type
            if action.type == ActionType.SEARCH:
                await self._execute_search(action.parameters.get("query", ""))
            elif action.type == ActionType.CLICK:
                await self._execute_click(action.parameters.get("element_id", ""))
            elif action.type == ActionType.TYPE:
                await self._execute_type(
                    action.parameters.get("element_id", ""),
                    action.parameters.get("text", "")
                )
            elif action.type == ActionType.SELECT:
                await self._execute_select(
                    action.parameters.get("element_id", ""),
                    action.parameters.get("value", "")
                )
            elif action.type == ActionType.BACK:
                self.driver.back()
            elif action.type == ActionType.WAIT:
                wait_time = action.parameters.get("time", 2)
                await asyncio.sleep(wait_time)
            elif action.type == ActionType.STOP:
                logger.info("Agent requested to stop")
            else:
                error_message = f"Unknown action type: {action.type}"
            
            # Wait for page to stabilize after action
            await asyncio.sleep(1)
            
            # Get new observation
            observation = await self.observe()
            if error_message:
                observation.error_message = error_message
                
            return observation
            
        except Exception as e:
            logger.error(f"Error executing action {action.type}: {e}")
            return Observation(
                error_message=f"Failed to execute action: {e}",
                url=self.current_url
            )
    
    async def reset(self) -> Observation:
        """Reset environment to initial state"""
        try:
            if self.driver:
                self.driver.quit()
                
            await self._setup_driver()
            self.driver.get(self.start_url)
            
            # Clear state
            self.clickables = {}
            self.inputs = {}
            self.selects = {}
            
            return await self.observe()
            
        except Exception as e:
            logger.error(f"Error resetting environment: {e}")
            raise EnvironmentException(f"Failed to reset environment: {e}")
    
    async def close(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    async def _process_page_with_recipes(self):
        """Process current page using recipes to extract interactive elements"""
        try:
            # Clear previous elements
            self.clickables = {}
            self.inputs = {}
            self.selects = {}
            
            current_url = self.driver.current_url
            
            # Try to find matching recipe
            matching_recipe = None
            for recipe in self.recipes:
                if self._matches_recipe(recipe, current_url):
                    matching_recipe = recipe
                    break
            
            if matching_recipe:
                logger.info(f"Using recipe for URL: {current_url}")
                await self._process_recipe(matching_recipe)
            else:
                # Fallback to generic element discovery
                await self._process_generic_elements()
                
        except Exception as e:
            logger.warning(f"Error processing page with recipes: {e}")
            # Fallback to generic processing
            await self._process_generic_elements()
    
    def _matches_recipe(self, recipe: Dict[str, Any], url: str) -> bool:
        """Check if a recipe matches the current URL"""
        match_method = recipe.get("match_method", "url")
        match_pattern = recipe.get("match", "")
        
        if match_method == "url":
            return match_pattern in url
        elif match_method == "text":
            # For text matching, check if specific element exists
            match_selector = recipe.get("match_text", "")
            if match_selector:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, match_selector)
                    return len(elements) > 0
                except:
                    return False
        
        return False
    
    async def _process_recipe(self, recipe: Dict[str, Any]):
        """Process page using UXAgent-style recipe"""
        try:
            children = recipe.get("children", [])
            for child in children:
                await self._process_recipe_element(child, "")
                
        except Exception as e:
            logger.warning(f"Error processing recipe: {e}")
    
    async def _process_recipe_element(self, element_spec: Dict[str, Any], parent_path: str):
        """Process a single element from recipe specification using UXAgent's approach"""
        try:
            selector = element_spec.get("selector", "")
            if not selector:
                return
            
            # Find elements matching selector
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception as e:
                logger.debug(f"Invalid selector '{selector}': {e}")
                return
            
            for i, element in enumerate(elements[:10]):  # Limit to first 10 matches
                try:
                    # Generate element ID using UXAgent pattern
                    element_name = element_spec.get("name", "")
                    if element_name:
                        element_id = f"{parent_path}_{element_name}_{i}" if parent_path else f"{element_name}_{i}"
                    else:
                        element_id = f"{parent_path}_{selector}_{i}".replace(" ", "_").replace("#", "").replace(".", "")
                    
                    # Clean element ID
                    element_id = element_id.replace(" ", "_").replace("#", "").replace(".", "").replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                    
                    # Handle clickable elements (UXAgent pattern)
                    if element_spec.get("clickable", False):
                        if not element_name:
                            logger.warning("Clickable element must have a name")
                            continue
                            
                        # Get click target element (may be different from matched element)
                        click_element = element
                        if element_spec.get("click_selector"):
                            try:
                                click_targets = element.find_elements(By.CSS_SELECTOR, element_spec["click_selector"])
                                if click_targets:
                                    click_element = click_targets[0]
                            except:
                                pass
                        
                        # Get text content
                        text = self._get_element_text(element, element_spec)
                        
                        # Register as clickable
                        self.clickables[element_id] = {
                            "name": element_name,
                            "text": text or element.get_attribute("title") or element.get_attribute("aria-label") or "",
                            "id": element_id,
                            "tag": element.tag_name,
                            "element": click_element  # Store the actual clickable element
                        }
                        
                        logger.debug(f"Registered clickable: {element_id} -> {element_name}")
                    
                    # Handle input elements (including submit buttons)
                    if element.tag_name.lower() in ["input", "textarea", "button"]:
                        input_type = element.get_attribute("type") or "text"
                        placeholder = element.get_attribute("placeholder") or ""
                        name = element_name or element_id
                        
                        # For submit/button types, register as both input and clickable
                        if input_type in ["submit", "button"] or element.tag_name.lower() == "button":
                            # Also register as clickable if not already done
                            if element_id not in self.clickables:
                                text = self._get_element_text(element, element_spec) or element.get_attribute("value") or "Submit"
                                self.clickables[element_id] = {
                                    "name": name,
                                    "text": text,
                                    "id": element_id,
                                    "tag": element.tag_name,
                                    "element": element
                                }
                                logger.debug(f"Auto-registered submit button as clickable: {element_id}")
                        
                        # Register as input
                        self.inputs[element_id] = {
                            "name": name,
                            "type": input_type,
                            "placeholder": placeholder,
                            "id": element_id,
                            "element": element
                        }
                    
                    # Handle select elements 
                    if element.tag_name.lower() == "select":
                        name = element_name or element_id
                        options = []
                        
                        try:
                            option_elements = element.find_elements(By.TAG_NAME, "option")
                            for option in option_elements:
                                option_value = option.get_attribute("value") or option.text
                                options.append({
                                    "value": option_value,
                                    "text": option.text,
                                    "selected": option.is_selected()
                                })
                        except Exception as e:
                            logger.debug(f"Error processing select options: {e}")
                        
                        self.selects[element_id] = {
                            "name": name,
                            "id": element_id,
                            "options": options,
                            "element": element
                        }
                    
                    # Process children recursively (UXAgent pattern)
                    children = element_spec.get("children", [])
                    for child in children:
                        await self._process_recipe_element(child, element_id)
                        
                except StaleElementReferenceException:
                    logger.debug(f"Stale element reference for element {i}")
                    continue
                except Exception as e:
                    logger.debug(f"Error processing element {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in _process_recipe_element: {e}")
    
    def _get_element_text(self, element, element_spec: Dict[str, Any]) -> str:
        """Extract text from element based on recipe specification (UXAgent approach)"""
        try:
            # UXAgent pattern: check for text extraction specifications
            if element_spec.get("add_text", False):
                text = ""
                
                # Use text_selector if specified
                if element_spec.get("text_selector"):
                    try:
                        text_elements = element.find_elements(By.CSS_SELECTOR, element_spec["text_selector"])
                        if text_elements:
                            text = text_elements[0].text.strip()
                        else:
                            text = element.text.strip()
                    except:
                        text = element.text.strip()
                        
                # Use text_js if specified (UXAgent feature)
                elif element_spec.get("text_js"):
                    try:
                        text = self.driver.execute_script(element_spec["text_js"], element)
                    except:
                        text = element.text.strip()
                        
                # Default to element text
                else:
                    text = element.text.strip()
                
                # Apply text formatting if specified
                if element_spec.get("text_format") and "{}" in element_spec["text_format"]:
                    text = element_spec["text_format"].format(text)
                
                # Clean up text (UXAgent does this)
                text = re.sub(r'\s+', ' ', text).strip() if text else ""
                
                return text or element.get_attribute("title") or element.get_attribute("aria-label") or ""
            
            # Fallback to basic text extraction
            return element.get_attribute("aria-label") or element.get_attribute("title") or element.text.strip()
                
        except Exception as e:
            logger.debug(f"Error getting element text: {e}")
            return ""
    
    async def _process_generic_elements(self):
        """Fallback generic element processing (original implementation)"""
        try:
            # Find clickable elements
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, [onclick], [role='button']")
            for i, element in enumerate(clickable_elements[:20]):  # Limit to first 20
                try:
                    text = element.text.strip() or element.get_attribute("title") or element.get_attribute("aria-label") or f"clickable_{i}"
                    if text and len(text) > 0:
                        element_id = f"clickable_{i}_{text[:30].replace(' ', '_')}"
                        self.clickables[element_id] = {
                            "name": element_id,
                            "text": text[:100],
                            "id": element_id,
                            "tag": element.tag_name,
                            "element": element
                        }
                except StaleElementReferenceException:
                    continue
            
            # Find input elements
            input_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search'], input[type='email'], textarea")
            for i, element in enumerate(input_elements):
                try:
                    name = element.get_attribute("name") or element.get_attribute("id") or f"input_{i}"
                    placeholder = element.get_attribute("placeholder") or ""
                    input_type = element.get_attribute("type") or "text"
                    
                    element_id = f"input_{i}_{name}"
                    self.inputs[element_id] = {
                        "name": element_id,
                        "type": input_type,
                        "placeholder": placeholder,
                        "id": element_id,
                        "element": element
                    }
                except StaleElementReferenceException:
                    continue
            
            # Find select elements
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select")
            for i, element in enumerate(select_elements):
                try:
                    name = element.get_attribute("name") or element.get_attribute("id") or f"select_{i}"
                    element_id = f"select_{i}_{name}"
                    
                    options = []
                    option_elements = element.find_elements(By.TAG_NAME, "option")
                    for option in option_elements:
                        options.append({
                            "value": option.get_attribute("value") or option.text,
                            "text": option.text
                        })
                    
                    self.selects[element_id] = {
                        "name": element_id,
                        "id": element_id,
                        "options": options,
                        "element": element
                    }
                except StaleElementReferenceException:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error in generic element processing: {e}")
    
    def _extract_text_content(self) -> str:
        """Extract clean text content from the page"""
        try:
            # Remove script and style elements
            self.driver.execute_script("""
                var scripts = document.querySelectorAll('script, style');
                for (var i = 0; i < scripts.length; i++) {
                    scripts[i].remove();
                }
            """)
            
            # Get body text
            body = self.driver.find_element(By.TAG_NAME, "body")
            text_content = body.text
            
            # Clean up text
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            return '\n'.join(lines[:100])  # Limit to first 100 lines
            
        except Exception as e:
            logger.warning(f"Error extracting text content: {e}")
            return "Error extracting page content"
    
    async def _execute_search(self, query: str):
        """Execute search action"""
        try:
            # Look for search input with broader selectors
            search_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='search'], input[name*='search'], input[id*='search'], input[placeholder*='search' i], "
                "input[name='q'], input[title*='search' i], input[class*='search' i], textarea[name='q']")
            
            if search_inputs:
                search_input = search_inputs[0]
                search_input.clear()
                search_input.send_keys(query)
                
                # Look for search button with broader selectors
                search_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                    "button[type='submit'], input[type='submit'], button[name*='search'], "
                    "*[role='button'][aria-label*='search' i], input[name='btnG'], "
                    "button[aria-label*='search' i], *[title*='search' i][role='button']")
                
                if search_buttons:
                    search_buttons[0].click()
                else:
                    # Try pressing Enter
                    from selenium.webdriver.common.keys import Keys
                    search_input.send_keys(Keys.RETURN)
                    
                logger.info(f"Executed search for: {query}")
            else:
                raise EnvironmentException("No search input found on page")
                
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            raise EnvironmentException(f"Search failed: {e}")
    
    async def _execute_click(self, element_id: str):
        """Execute click action"""
        try:
            if element_id in self.clickables:
                element = self.clickables[element_id]["element"]
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                await asyncio.sleep(0.5)
                
                # Click element
                element.click()
                logger.info(f"Clicked element: {element_id}")
            elif element_id in self.inputs:
                # Check if it's a submit button in inputs
                input_element = self.inputs[element_id]
                if input_element.get("type") == "submit":
                    element = input_element["element"]
                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    await asyncio.sleep(0.5)
                    
                    # Click submit button
                    element.click()
                    logger.info(f"Clicked submit button: {element_id}")
                else:
                    raise EnvironmentException(f"Element {element_id} is not clickable")
            else:
                raise EnvironmentException(f"Clickable element not found: {element_id}")
                
        except Exception as e:
            logger.error(f"Error clicking element {element_id}: {e}")
            raise EnvironmentException(f"Click failed: {e}")
    
    async def _execute_type(self, element_id: str, text: str):
        """Execute type action"""
        try:
            if element_id in self.inputs:
                element = self.inputs[element_id]["element"]
                element.clear()
                element.send_keys(text)
                logger.info(f"Typed '{text}' into element: {element_id}")
            else:
                raise EnvironmentException(f"Input element not found: {element_id}")
                
        except Exception as e:
            logger.error(f"Error typing into element {element_id}: {e}")
            raise EnvironmentException(f"Type failed: {e}")
    
    async def _execute_select(self, element_id: str, value: str):
        """Execute select action"""
        try:
            if element_id in self.selects:
                element = self.selects[element_id]["element"]
                from selenium.webdriver.support.select import Select
                select = Select(element)
                select.select_by_value(value)
                logger.info(f"Selected '{value}' from element: {element_id}")
            else:
                raise EnvironmentException(f"Select element not found: {element_id}")
                
        except Exception as e:
            logger.error(f"Error selecting from element {element_id}: {e}")
            raise EnvironmentException(f"Select failed: {e}") 