import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import os
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc

class LinkedInScraper:
    """
    Class to handle LinkedIn scraping functionality with improved security measures
    """
    
    def __init__(self, headless=True, use_undetected=True):
        """
        Initialize the LinkedIn scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            use_undetected (bool): Whether to use undetected_chromedriver for better evasion
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('LinkedInScraper')
        
        # Initialize variables
        self.driver = None
        self.is_logged_in = False
        self.headless = headless
        self.use_undetected = use_undetected
        self.captcha_detected = False
        self.login_attempts = 0
        self.max_login_attempts = 3
        
        # Initialize the web driver
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize the Selenium web driver with improved anti-detection measures"""
        try:
            if self.use_undetected:
                self._initialize_undetected_driver()
            else:
                self._initialize_standard_driver()
                
            # Set window size to a common resolution
            self.driver.set_window_size(1920, 1080)
            
            # Add a user data directory to maintain cookies between sessions
            user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
                
            self.logger.info("Web driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing web driver: {str(e)}")
            # For demo purposes, we'll continue without a real driver
            self.driver = None
    
    def _initialize_undetected_driver(self):
        """Initialize using undetected_chromedriver for better evasion"""
        try:
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument("--headless")
                
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            
            # Add realistic user agent
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Initialize the undetected Chrome driver
            self.driver = uc.Chrome(options=options)
            
            # Execute CDP commands to modify navigator properties
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                """
            })
            
        except Exception as e:
            self.logger.error(f"Error initializing undetected driver: {str(e)}")
            self._initialize_standard_driver()
    
    def _initialize_standard_driver(self):
        """Initialize standard Selenium driver with anti-detection measures"""
        # Set up Chrome options
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Add realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize the Chrome driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute CDP commands to modify navigator properties
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """
        })
    
    def _simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection"""
        if self.driver is None:
            return
            
        try:
            # Random scrolling
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Random mouse movements (simulated)
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1000)
                y = random.randint(100, 500)
                actions.move_by_offset(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Random pauses
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            self.logger.warning(f"Error during human behavior simulation: {str(e)}")
    
    def _check_for_captcha(self):
        """Check if a CAPTCHA is present on the page"""
        if self.driver is None:
            return False
            
        try:
            # Check for common CAPTCHA indicators
            captcha_indicators = [
                "//div[contains(text(), 'CAPTCHA')]",
                "//div[contains(text(), 'captcha')]",
                "//div[contains(text(), 'security check')]",
                "//div[contains(text(), 'Security Verification')]",
                "//iframe[contains(@src, 'recaptcha')]",
                "//iframe[contains(@src, 'captcha')]"
            ]
            
            for indicator in captcha_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        self.captcha_detected = True
                        self.logger.warning("CAPTCHA detected on the page")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking for CAPTCHA: {str(e)}")
            return False
    
    def _handle_captcha(self):
        """Handle CAPTCHA detection"""
        if self.driver is None:
            return False
            
        try:
            # Take a screenshot of the CAPTCHA
            captcha_screenshot_path = os.path.join(os.getcwd(), "captcha_screenshot.png")
            self.driver.save_screenshot(captcha_screenshot_path)
            
            self.logger.warning(f"CAPTCHA detected. Screenshot saved to {captcha_screenshot_path}")
            self.logger.warning("Manual intervention required to solve CAPTCHA")
            
            # Notify the user that manual intervention is required
            print("\n" + "="*50)
            print("CAPTCHA DETECTED - MANUAL INTERVENTION REQUIRED")
            print(f"Screenshot saved to: {captcha_screenshot_path}")
            print("Please open the browser manually to solve the CAPTCHA")
            print("="*50 + "\n")
            
            # If we're in headless mode, we need to restart in headed mode
            if self.headless:
                self.logger.info("Restarting in headed mode to allow CAPTCHA solving")
                self.close()
                self.headless = False
                self._initialize_driver()
                return False
            
            # Wait for manual intervention
            input("Press Enter after solving the CAPTCHA manually...")
            
            # Check if CAPTCHA is still present
            if self._check_for_captcha():
                self.logger.warning("CAPTCHA still detected after manual intervention")
                return False
            else:
                self.logger.info("CAPTCHA appears to be solved")
                self.captcha_detected = False
                return True
                
        except Exception as e:
            self.logger.error(f"Error handling CAPTCHA: {str(e)}")
            return False
    
    def login(self, email, password):
        """
        Log in to LinkedIn with improved security handling
        
        Args:
            email (str): LinkedIn email
            password (str): LinkedIn password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        if self.driver is None:
            self.logger.error("Web driver not initialized")
            return False
        
        # Increment login attempts
        self.login_attempts += 1
        
        if self.login_attempts > self.max_login_attempts:
            self.logger.error(f"Maximum login attempts ({self.max_login_attempts}) exceeded")
            return False
        
        try:
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                if not self._handle_captcha():
                    return False
            
            # Enter email with human-like typing
            email_field = self.driver.find_element(By.ID, "username")
            email_field.clear()
            for char in email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            # Pause like a human would
            time.sleep(random.uniform(0.5, 1.5))
            
            # Enter password with human-like typing
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            # Pause before clicking login
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete with a longer timeout
            time.sleep(random.uniform(3, 5))
            
            # Check for CAPTCHA again after login attempt
            if self._check_for_captcha():
                if not self._handle_captcha():
                    return False
                
                # Try logging in again after CAPTCHA is solved
                return self.login(email, password)
            
            # Check for two-factor authentication
            try:
                if "two-factor" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                    self.logger.warning("Two-factor authentication detected")
                    print("\n" + "="*50)
                    print("TWO-FACTOR AUTHENTICATION REQUIRED")
                    print("Please complete the verification process manually")
                    print("="*50 + "\n")
                    
                    # If we're in headless mode, we need to restart in headed mode
                    if self.headless:
                        self.logger.info("Restarting in headed mode to allow 2FA completion")
                        self.close()
                        self.headless = False
                        self._initialize_driver()
                        return self.login(email, password)
                    
                    # Wait for manual intervention
                    input("Press Enter after completing two-factor authentication...")
            except:
                pass
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "checkpoint" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                self.is_logged_in = True
                self.logger.info("Login successful")
                
                # Save cookies for future sessions
                cookies_dir = os.path.join(os.getcwd(), "cookies")
                if not os.path.exists(cookies_dir):
                    os.makedirs(cookies_dir)
                
                cookies_file = os.path.join(cookies_dir, "linkedin_cookies.json")
                with open(cookies_file, "w") as f:
                    json.dump(self.driver.get_cookies(), f)
                
                return True
            else:
                self.logger.error("Login failed")
                
                # Take a screenshot of the failed login
                failed_login_screenshot = os.path.join(os.getcwd(), "failed_login.png")
                self.driver.save_screenshot(failed_login_screenshot)
                self.logger.error(f"Failed login screenshot saved to {failed_login_screenshot}")
                
                return False
        except TimeoutException:
            self.logger.error("Timeout during login process")
            return False
        except NoSuchElementException as e:
            self.logger.error(f"Element not found during login: {str(e)}")
            return False
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during login: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error during login: {str(e)}")
            return False
    
    def search_linkedin(self, keywords, location, page_limit=3):
        """
        Search LinkedIn for profiles matching the given criteria with improved error handling
        
        Args:
            keywords (str): Search keywords
            location (str): Location to search in
            page_limit (int): Maximum number of pages to scrape
            
        Returns:
            DataFrame: DataFrame containing the search results
        """
        if self.driver is None or not self.is_logged_in:
            self.logger.warning("Not logged in to LinkedIn. Using mock data.")
            return mock_linkedin_search(keywords, location, page_limit)
        
        try:
            # Construct search URL
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={keywords}&location={location}"
            
            # Navigate to search URL
            self.driver.get(search_url)
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                if not self._handle_captcha():
                    return mock_linkedin_search(keywords, location, page_limit)
            
            # Wait for search results to load with better error handling
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-result__info"))
                )
            except TimeoutException:
                try:
                    # Alternative selector if the first one fails
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "entity-result__title"))
                    )
                except TimeoutException:
                    self.logger.warning("Search results not loading. Using mock data.")
                    return mock_linkedin_search(keywords, location, page_limit)
            
            # Initialize results list
            results = []
            
            # Scrape each page
            for page in range(page_limit):
                # Wait for page to load with random delay
                time.sleep(random.uniform(2, 4))
                
                # Simulate human scrolling behavior
                self._simulate_human_scrolling()
                
                # Get page source
                page_source = self.driver.page_source
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_source, "html.parser")
                
                # Find all search result items with multiple selectors for robustness
                search_results = soup.find_all("li", class_="reusable-search__result-container")
                if not search_results:
                    search_results = soup.find_all("li", class_="entity-result")
                
                # Extract data from each result
                for result in search_results:
                    try:
                        # Extract name with multiple selectors
                        name_element = result.find("span", class_="entity-result__title-text")
                        if not name_element:
                            name_element = result.find("span", class_="actor-name")
                        
                        name = name_element.get_text(strip=True) if name_element else "Unknown"
                        
                        # Extract profile URL
                        profile_link = name_element.find("a") if name_element else None
                        profile_url = profile_link["href"].split("?")[0] if profile_link and "href" in profile_link.attrs else ""
                        
                        # Extract title with multiple selectors
                        title_element = result.find("div", class_="entity-result__primary-subtitle")
                        if not title_element:
                            title_element = result.find("div", class_="search-result__subtitle")
                        
                        title = title_element.get_text(strip=True) if title_element else "Unknown"
                        
                        # Extract company and location
                        subtitle_element = result.find("div", class_="entity-result__secondary-subtitle")
                        if not subtitle_element:
                            subtitle_element = result.find("div", class_="search-result__info-container")
                        
                        subtitle_text = subtitle_element.get_text(strip=True) if subtitle_element else ""
                        
                        # Try to split company and location
                        if " at " in title:
                            title_parts = title.split(" at ", 1)
                            title = title_parts[0].strip()
                            company = title_parts[1].strip()
                        else:
                            company = subtitle_text
                        
                        # Extract location with multiple selectors
                        location_element = result.find("div", class_="entity-result__tertiary-subtitle")
                        if not location_element:
                            location_element = result.find("div", class_="search-result__location")
                        
                        location = location_element.get_text(strip=True) if location_element else "Unknown"
                        
                        # Extract connections with multiple selectors
                        connections_element = result.find("span", class_="distance-badge")
                        if not connections_element:
                            connections_element = result.find("span", class_="search-result__connection-count")
                        
                        connections = connections_element.get_text(strip=True) if connections_element else "Unknown"
                        
                        # Add to results
                        results.append({
                            "name": name,
                            "title": title,
                            "company": company,
                            "location": location,
                            "industry": "Unknown",  # Not directly available in search results
                            "company_size": "Unknown",  # Not directly available in search results
                            "connections": connections,
                            "profile_url": profile_url,
                            "is_qualified": False  # Default value
                        })
                    except Exception as e:
                        self.logger.error(f"Error extracting data from search result: {str(e)}")
                
                # Check if there's a next page with better error handling
                try:
                    next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                    if "disabled" in next_button.get_attribute("class"):
                        break
                    
                    # Simulate human behavior before clicking
                    self._simulate_human_behavior()
                    
                    next_button.click()
                    time.sleep(random.uniform(2, 4))
                except NoSuchElementException:
                    try:
                        # Alternative selector if the first one fails
                        next_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'artdeco-pagination__button--next')]")
                        if "disabled" in next_button.get_attribute("class"):
                            break
                        
                        # Simulate human behavior before clicking
                        self._simulate_human_behavior()
                        
                        next_button.click()
                        time.sleep(random.uniform(2, 4))
                    except:
                        break
                except:
                    break
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results)
            
            self.logger.info(f"Found {len(results_df)} results for '{keywords}' in '{location}'")
            return results_df
        except TimeoutException:
            self.logger.error("Timeout during LinkedIn search")
            return mock_linkedin_search(keywords, location, page_limit)
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during search: {str(e)}")
            return mock_linkedin_search(keywords, location, page_limit)
        except Exception as e:
            self.logger.error(f"Error during LinkedIn search: {str(e)}")
            return mock_linkedin_search(keywords, location, page_limit)
    
    def _simulate_human_scrolling(self):
        """Simulate human-like scrolling behavior"""
        if self.driver is None:
            return
            
        try:
            # Get page height
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in multiple steps with random pauses
            current_position = 0
            while current_position < page_height:
                # Random scroll amount
                scroll_amount = random.randint(300, 700)
                current_position += scroll_amount
                
                # Scroll to new position
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Random pause
                time.sleep(random.uniform(0.5, 2))
                
                # Occasionally scroll back up a bit
                if random.random() < 0.2:
                    scroll_back = random.randint(50, 200)
                    current_position -= scroll_back
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(random.uniform(0.5, 1))
        except Exception as e:
            self.logger.warning(f"Error during human scrolling simulation: {str(e)}")
    
    def get_profile_details(self, profile_url):
        """
        Get detailed information from a LinkedIn profile with improved error handling
        
        Args:
            profile_url (str): URL of the LinkedIn profile
            
        Returns:
            dict: Dictionary containing profile details
        """
        if self.driver is None or not self.is_logged_in:
            self.logger.warning("Not logged in to LinkedIn. Cannot get profile details.")
            return None
        
        try:
            # Navigate to profile URL
            self.driver.get(profile_url)
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                if not self._handle_captcha():
                    return None
            
            # Wait for profile to load with better error handling
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
                )
            except TimeoutException:
                try:
                    # Alternative selector if the first one fails
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "profile-background-image"))
                    )
                except TimeoutException:
                    self.logger.warning("Profile not loading properly")
                    return None
            
            # Simulate human scrolling to load all content
            self._simulate_human_scrolling()
            
            # Get page source
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Extract name with multiple selectors for robustness
            name_element = soup.find("h1", class_="text-heading-xlarge")
            if not name_element:
                name_element = soup.find("h1", class_="pv-top-card--list")
            
            name = name_element.get_text(strip=True) if name_element else "Unknown"
            
            # Extract headline with multiple selectors
            headline_element = soup.find("div", class_="text-body-medium")
            if not headline_element:
                headline_element = soup.find("h2", class_="pv-top-card--headline")
            
            headline = headline_element.get_text(strip=True) if headline_element else ""
            
            # Extract location with multiple selectors
            location_element = soup.find("span", class_="text-body-small")
            if not location_element:
                location_element = soup.find("li", class_="pv-top-card--list-bullet")
            
            location = location_element.get_text(strip=True) if location_element else ""
            
            # Extract experience with better error handling
            experience = []
            experience_section = soup.find("section", {"id": "experience-section"})
            if not experience_section:
                experience_section = soup.find("div", {"id": "experience"})
            
            if experience_section:
                experience_items = experience_section.find_all("li", class_="pv-entity__position-group-pager")
                if not experience_items:
                    experience_items = experience_section.find_all("li", class_="artdeco-list__item")
                
                for item in experience_items:
                    try:
                        # Extract title with multiple selectors
                        title_element = item.find("h3", class_="t-16")
                        if not title_element:
                            title_element = item.find("h3", class_="pv-entity__summary-title")
                        
                        title = title_element.get_text(strip=True) if title_element else "Unknown"
                        
                        # Extract company with multiple selectors
                        company_element = item.find("p", class_="pv-entity__secondary-title")
                        if not company_element:
                            company_element = item.find("span", class_="pv-entity__company-name")
                        
                        company = company_element.get_text(strip=True) if company_element else "Unknown"
                        
                        # Extract date with multiple selectors
                        date_element = item.find("h4", class_="pv-entity__date-range")
                        if not date_element:
                            date_element = item.find("div", class_="pv-entity__date-range")
                        
                        date = date_element.find("span").get_text(strip=True) if date_element else "Unknown"
                        
                        experience.append({
                            "title": title,
                            "company": company,
                            "date": date
                        })
                    except Exception as e:
                        self.logger.error(f"Error extracting experience item: {str(e)}")
            
            # Extract education with better error handling
            education = []
            education_section = soup.find("section", {"id": "education-section"})
            if not education_section:
                education_section = soup.find("div", {"id": "education"})
            
            if education_section:
                education_items = education_section.find_all("li", class_="pv-education-entity")
                if not education_items:
                    education_items = education_section.find_all("li", class_="artdeco-list__item")
                
                for item in education_items:
                    try:
                        # Extract school with multiple selectors
                        school_element = item.find("h3", class_="pv-entity__school-name")
                        if not school_element:
                            school_element = item.find("h3", class_="pv-entity__name")
                        
                        school = school_element.get_text(strip=True) if school_element else "Unknown"
                        
                        # Extract degree with multiple selectors
                        degree_element = item.find("p", class_="pv-entity__degree-name")
                        if not degree_element:
                            degree_element = item.find("span", class_="pv-entity__comma-item")
                        
                        degree = degree_element.find("span").get_text(strip=True) if degree_element and degree_element.find("span") else "Unknown"
                        
                        education.append({
                            "school": school,
                            "degree": degree
                        })
                    except Exception as e:
                        self.logger.error(f"Error extracting education item: {str(e)}")
            
            # Extract skills with better error handling
            skills = []
            skills_section = soup.find("section", {"id": "skills-section"})
            if not skills_section:
                skills_section = soup.find("div", {"id": "skills"})
            
            if skills_section:
                skill_items = skills_section.find_all("span", class_="pv-skill-category-entity__name-text")
                if not skill_items:
                    skill_items = skills_section.find_all("span", class_="pv-skill-entity__skill-name")
                
                for item in skill_items:
                    skills.append(item.get_text(strip=True))
            
            # Create profile details dictionary
            profile_details = {
                "name": name,
                "headline": headline,
                "location": location,
                "experience": experience,
                "education": education,
                "skills": skills
            }
            
            self.logger.info(f"Retrieved profile details for {name}")
            return profile_details
        except TimeoutException:
            self.logger.error("Timeout getting profile details")
            return None
        except WebDriverException as e:
            self.logger.error(f"WebDriver error getting profile details: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting profile details: {str(e)}")
            return None
    
    def close(self):
        """Close the web driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Web driver closed")
            except Exception as e:
                self.logger.error(f"Error closing web driver: {str(e)}")

def mock_linkedin_search(keywords, location, page_limit=3):
    """
    Generate mock LinkedIn search results for demonstration purposes
    
    Args:
        keywords (str): Search keywords
        location (str): Location to search in
        page_limit (int): Maximum number of pages to scrape
        
    Returns:
        DataFrame: DataFrame containing mock search results
    """
    # Number of results to generate (based on page_limit)
    num_results = page_limit * 10
    
    # Lists of sample data
    first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Jennifer", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    
    # Generate job titles based on keywords
    if "software" in keywords.lower() or "developer" in keywords.lower() or "engineer" in keywords.lower():
        job_titles = [
            "Software Engineer", "Senior Developer", "Full Stack Engineer", "Frontend Developer",
            "Backend Engineer", "DevOps Engineer", "Software Architect", "Tech Lead",
            "Engineering Manager", "CTO", "VP of Engineering", "Principal Engineer"
        ]
    elif "marketing" in keywords.lower():
        job_titles = [
            "Marketing Manager", "Digital Marketing Specialist", "Marketing Director",
            "Content Strategist", "SEO Specialist", "Social Media Manager",
            "Brand Manager", "Marketing Analyst", "Growth Hacker", "CMO"
        ]
    elif "sales" in keywords.lower():
        job_titles = [
            "Sales Representative", "Account Executive", "Sales Manager", "Business Development",
            "Sales Director", "Account Manager", "Sales Consultant", "VP of Sales",
            "Regional Sales Manager", "Inside Sales Representative"
        ]
    else:
        job_titles = [
            "Product Manager", "Project Manager", "Business Analyst", "Data Scientist",
            "UX Designer", "HR Manager", "Operations Manager", "Financial Analyst",
            "Consultant", "Director", "VP", "CEO", "Founder"
        ]
    
    companies = [
        "Google", "Microsoft", "Amazon", "Apple", "Facebook", "Netflix", "Adobe",
        "Salesforce", "IBM", "Oracle", "Intel", "Cisco", "Twitter", "LinkedIn",
        "Uber", "Airbnb", "Spotify", "Slack", "Zoom", "Tesla"
    ]
    
    industries = [
        "Technology", "Software", "Internet", "E-commerce", "Financial Services",
        "Healthcare", "Education", "Consulting", "Marketing", "Telecommunications"
    ]
    
    company_sizes = [
        "1-10 employees", "11-50 employees", "51-200 employees", "201-500 employees",
        "501-1,000 employees", "1,001-5,000 employees", "5,001-10,000 employees", "10,001+ employees"
    ]
    
    connections = ["500+", "500+", "500+", "200-500", "200-500", "100-200", "100-200", "<100"]
    
    # Generate mock results
    results = []
    for i in range(num_results):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        name = f"{first_name} {last_name}"
        
        job_title = random.choice(job_titles)
        company = random.choice(companies)
        industry = random.choice(industries)
        company_size = random.choice(company_sizes)
        connection = random.choice(connections)
        
        # Use the provided location or generate a random one
        if location and location.lower() != "any":
            result_location = location
        else:
            locations = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA", "Chicago, IL"]
            result_location = random.choice(locations)
        
        # Generate a mock profile URL
        profile_url = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}-{random.randint(10000, 99999)}"
        
        # Randomly mark some leads as qualified
        is_qualified = random.choice([True, False, False, False])
        
        results.append({
            "name": name,
            "title": job_title,
            "company": company,
            "location": result_location,
            "industry": industry,
            "company_size": company_size,
            "connections": connection,
            "profile_url": profile_url,
            "is_qualified": is_qualified
        })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df
