import os
import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
import pickle
import base64

class BrowserAutomation:
    """Browser automation service using Selenium WebDriver"""
    
    def __init__(self):
        self.driver = None
        self.session_file = 'browser_session.pkl'
        self.logger = logging.getLogger(__name__)
        
    def _setup_driver(self, user_agent=None, proxy=None):
        """Setup Chrome WebDriver with options"""
        try:
            chrome_options = Options()
            
            # Basic Chrome options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Set user agent if provided
            if user_agent:
                chrome_options.add_argument(f'--user-agent={user_agent}')
            else:
                # Default user agent to avoid detection
                default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                chrome_options.add_argument(f'--user-agent={default_ua}')
            
            # Set proxy if provided
            if proxy:
                chrome_options.add_argument(f'--proxy-server={proxy}')
            
            # Additional anti-detection measures
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to use headless mode
            chrome_options.add_argument('--headless')
            
            # Find Chromium binary location
            try:
                chromium_path = subprocess.check_output(['which', 'chromium'], text=True).strip()
                chrome_options.binary_location = chromium_path
                self.logger.info(f"Using Chromium at: {chromium_path}")
            except subprocess.CalledProcessError:
                self.logger.warning("Could not find Chromium binary, using default")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {str(e)}")
            return False
    
    def _human_like_typing(self, element, text):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(0.05 + (0.1 * hash(char) % 10) / 100)  # Random delay
    
    def _save_session(self):
        """Save browser session cookies"""
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                with open(self.session_file, 'wb') as f:
                    pickle.dump(cookies, f)
                self.logger.info("Browser session saved")
        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")
    
    def _load_session(self):
        """Load browser session cookies"""
        try:
            if os.path.exists(self.session_file) and self.driver:
                with open(self.session_file, 'rb') as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.logger.info("Browser session loaded")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load session: {str(e)}")
        return False
    
    def login_and_capture(self, website_url, username, password, user_agent=None, proxy=None):
        """Login to website and capture page content"""
        try:
            # Setup driver
            if not self._setup_driver(user_agent, proxy):
                return False, "Failed to initialize browser", ""
            
            # Navigate to website
            self.logger.info(f"Navigating to {website_url}")
            self.driver.get(website_url)
            
            # Try to load existing session first
            self._load_session()
            self.driver.refresh()
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if already logged in
            if self._is_logged_in():
                self.logger.info("Already logged in, capturing page content")
                return True, "Already logged in", self._capture_page_content()
            
            # Look for login form elements
            login_success = self._attempt_login(username, password)
            
            if login_success:
                self._save_session()
                # Capture content immediately after successful login
                page_content = self._capture_page_content()
                
                # If we get a page expired error, try to refresh or navigate to dashboard
                if "page expired" in base64.b64decode(page_content).decode('utf-8').lower():
                    self.logger.warning("Page expired after login, attempting to navigate to dashboard")
                    try:
                        # Try common dashboard URLs
                        base_url = "/".join(website_url.split("/")[:3])
                        dashboard_urls = [
                            base_url + "/dashboard",
                            base_url + "/home",
                            base_url + "/main",
                            base_url
                        ]
                        
                        for url in dashboard_urls:
                            self.driver.get(url)
                            time.sleep(2)
                            new_content = self._capture_page_content()
                            decoded_content = base64.b64decode(new_content).decode('utf-8').lower()
                            if "page expired" not in decoded_content and "419" not in decoded_content:
                                self.logger.info(f"Successfully navigated to {url}")
                                page_content = new_content
                                break
                    except Exception as e:
                        self.logger.error(f"Failed to navigate to dashboard: {e}")
                
                return True, "Login successful", page_content
            else:
                return False, "Login failed - could not find login form or authentication failed", ""
                
        except TimeoutException:
            return False, "Page load timeout", ""
        except WebDriverException as e:
            return False, f"WebDriver error: {str(e)}", ""
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False, f"Unexpected error: {str(e)}", ""
    
    def _attempt_login(self, username, password):
        """Attempt to find and fill login form"""
        try:
            # Common login form selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[name="login"]',
                'input[name="user"]',
                'input[type="email"]',
                'input[type="text"]',
                'input[id*="username"]',
                'input[id*="email"]',
                'input[id*="login"]',
                'input[placeholder*="username"]',
                'input[placeholder*="Username"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]',
                '#username',
                '#email',
                '#login',
                '.username',
                '.email'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id*="password"]',
                '#password'
            ]
            
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button[name="login"]',
                'button[name="submit"]',
                'button[value*="log"]',
                'button[value*="Log"]',
                'button',
                '.login-button',
                '.submit-button',
                '#login-button',
                '#submit',
                'input[value*="log"]',
                'input[value*="Log"]'
            ]
            
            username_element = None
            password_element = None
            submit_element = None
            
            # Find username field
            for selector in username_selectors:
                try:
                    username_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found username field with selector: {selector}")
                    break
                except:
                    continue
            
            # Find password field
            for selector in password_selectors:
                try:
                    password_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found password field with selector: {selector}")
                    break
                except:
                    continue
            
            # Find submit button
            for selector in submit_selectors:
                try:
                    submit_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Found submit button with selector: {selector}")
                    break
                except:
                    continue
            
            if not username_element or not password_element:
                self.logger.error("Could not find username or password field")
                return False
            
            # Fill the form with human-like behavior
            self.logger.info("Filling login form")
            
            # Click and fill username
            username_element.click()
            time.sleep(0.5)
            username_element.clear()
            self._human_like_typing(username_element, username)
            
            # Click and fill password
            time.sleep(0.5)
            password_element.click()
            time.sleep(0.5)
            password_element.clear()
            self._human_like_typing(password_element, password)
            
            # Submit form
            time.sleep(1)
            if submit_element:
                submit_element.click()
            else:
                # Try submitting via Enter key
                password_element.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check for error indicators first
            if "page expired" in page_source or "419" in page_source or "error" in page_source:
                self.logger.warning("Detected page expiration, attempting to navigate to dashboard")
                # Try to navigate to a dashboard or main page
                try:
                    base_url = "/".join(current_url.split("/")[:3])
                    dashboard_urls = [
                        base_url + "/dashboard",
                        base_url + "/home",
                        base_url + "/main",
                        base_url
                    ]
                    
                    for url in dashboard_urls:
                        self.driver.get(url)
                        time.sleep(2)
                        new_source = self.driver.page_source.lower()
                        if "page expired" not in new_source and "419" not in new_source:
                            self.logger.info(f"Successfully navigated to {url}")
                            return True
                except Exception as e:
                    self.logger.error(f"Failed to navigate to dashboard: {e}")
            
            # Check for login indicators or absence of login form
            if self._is_logged_in():
                self.logger.info("Login appears successful - found logout indicators")
                return True
            elif "login" not in page_source or "username" not in page_source or "password" not in page_source:
                self.logger.info("Login appears successful - login form no longer present")
                return True
            elif "welcome" in page_source or "dashboard" in page_source or "profile" in page_source:
                self.logger.info("Login appears successful - found success indicators")
                return True
            else:
                self.logger.error("Login failed - login form still present")
                return False
                
        except Exception as e:
            self.logger.error(f"Login attempt failed: {str(e)}")
            return False
    
    def _is_logged_in(self):
        """Check if user is logged in by looking for common indicators"""
        try:
            # Common indicators of being logged in
            logged_in_indicators = [
                'a[href*="logout"]',
                'a[href*="signout"]',
                'button[name="logout"]',
                '.logout',
                '.user-profile',
                '.user-menu',
                '.dashboard',
                '[data-testid="logout"]'
            ]
            
            for indicator in logged_in_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element.is_displayed():
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False
    
    def _capture_page_content(self):
        """Capture the current page content"""
        try:
            # Wait for page to fully load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source
            page_source = self.driver.page_source
            
            # Encode as base64 for safe transmission
            encoded_content = base64.b64encode(page_source.encode('utf-8')).decode('utf-8')
            
            return encoded_content
            
        except Exception as e:
            self.logger.error(f"Error capturing page content: {str(e)}")
            return ""
    
    def refresh_page(self, website_url):
        """Refresh the current page and capture content"""
        try:
            if not self.driver:
                return False, "Browser not initialized", ""
            
            self.driver.refresh()
            time.sleep(3)
            
            page_content = self._capture_page_content()
            return True, "Page refreshed successfully", page_content
            
        except Exception as e:
            self.logger.error(f"Error refreshing page: {str(e)}")
            return False, f"Refresh failed: {str(e)}", ""
    
    def is_active(self):
        """Check if browser is active"""
        try:
            return self.driver is not None and self.driver.session_id is not None
        except:
            return False
    
    def is_session_valid(self):
        """Check if current session is valid"""
        try:
            if not self.driver:
                return False
            
            # Try to get current URL
            current_url = self.driver.current_url
            return current_url is not None and current_url != "data:,"
            
        except:
            return False
    
    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("Browser cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
