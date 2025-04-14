import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

class LinkedInScraper:
    """
    Class to handle LinkedIn scraping functionality
    """
    
    def __init__(self, headless=True):
        """
        Initialize the LinkedIn scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
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
        
        # Initialize the web driver
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize the Selenium web driver"""
        try:
            # Set up Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.info("Web driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing web driver: {str(e)}")
            # For demo purposes, we'll continue without a real driver
            self.driver = None
    
    def login(self, email, password):
        """
        Log in to LinkedIn
        
        Args:
            email (str): LinkedIn email
            password (str): LinkedIn password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        if self.driver is None:
            self.logger.error("Web driver not initialized")
            return False
        
        try:
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter email
            email_field = self.driver.find_element(By.ID, "username")
            email_field.clear()
            email_field.send_keys(email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                self.is_logged_in = True
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed")
                return False
        except Exception as e:
            self.logger.error(f"Error during login: {str(e)}")
            return False
    
    def search_linkedin(self, keywords, location, page_limit=3):
        """
        Search LinkedIn for profiles matching the given criteria
        
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
            
            # Wait for search results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-result__info"))
            )
            
            # Initialize results list
            results = []
            
            # Scrape each page
            for page in range(page_limit):
                # Wait for page to load
                time.sleep(2)
                
                # Get page source
                page_source = self.driver.page_source
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_source, "html.parser")
                
                # Find all search result items
                search_results = soup.find_all("li", class_="reusable-search__result-container")
                
                # Extract data from each result
                for result in search_results:
                    try:
                        # Extract name
                        name_element = result.find("span", class_="entity-result__title-text")
                        name = name_element.get_text(strip=True) if name_element else "Unknown"
                        
                        # Extract profile URL
                        profile_link = name_element.find("a") if name_element else None
                        profile_url = profile_link["href"].split("?")[0] if profile_link and "href" in profile_link.attrs else ""
                        
                        # Extract title
                        title_element = result.find("div", class_="entity-result__primary-subtitle")
                        title = title_element.get_text(strip=True) if title_element else "Unknown"
                        
                        # Extract company and location
                        subtitle_element = result.find("div", class_="entity-result__secondary-subtitle")
                        subtitle_text = subtitle_element.get_text(strip=True) if subtitle_element else ""
                        
                        # Try to split company and location
                        if " at " in title:
                            title_parts = title.split(" at ", 1)
                            title = title_parts[0].strip()
                            company = title_parts[1].strip()
                        else:
                            company = subtitle_text
                        
                        # Extract location
                        location_element = result.find("div", class_="entity-result__tertiary-subtitle")
                        location = location_element.get_text(strip=True) if location_element else "Unknown"
                        
                        # Extract connections
                        connections_element = result.find("span", class_="distance-badge")
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
                
                # Check if there's a next page
                try:
                    next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                    if "disabled" in next_button.get_attribute("class"):
                        break
                    next_button.click()
                    time.sleep(2)
                except:
                    break
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results)
            
            self.logger.info(f"Found {len(results_df)} results for '{keywords}' in '{location}'")
            return results_df
        except Exception as e:
            self.logger.error(f"Error during LinkedIn search: {str(e)}")
            return pd.DataFrame()
    
    def get_profile_details(self, profile_url):
        """
        Get detailed information from a LinkedIn profile
        
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
            
            # Wait for profile to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
            )
            
            # Get page source
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Extract name
            name_element = soup.find("h1", class_="text-heading-xlarge")
            name = name_element.get_text(strip=True) if name_element else "Unknown"
            
            # Extract headline
            headline_element = soup.find("div", class_="text-body-medium")
            headline = headline_element.get_text(strip=True) if headline_element else ""
            
            # Extract location
            location_element = soup.find("span", class_="text-body-small")
            location = location_element.get_text(strip=True) if location_element else ""
            
            # Extract experience
            experience = []
            experience_section = soup.find("section", {"id": "experience-section"})
            if experience_section:
                experience_items = experience_section.find_all("li", class_="pv-entity__position-group-pager")
                for item in experience_items:
                    try:
                        title_element = item.find("h3", class_="t-16")
                        title = title_element.get_text(strip=True) if title_element else "Unknown"
                        
                        company_element = item.find("p", class_="pv-entity__secondary-title")
                        company = company_element.get_text(strip=True) if company_element else "Unknown"
                        
                        date_element = item.find("h4", class_="pv-entity__date-range")
                        date = date_element.find("span").get_text(strip=True) if date_element else "Unknown"
                        
                        experience.append({
                            "title": title,
                            "company": company,
                            "date": date
                        })
                    except Exception as e:
                        self.logger.error(f"Error extracting experience item: {str(e)}")
            
            # Extract education
            education = []
            education_section = soup.find("section", {"id": "education-section"})
            if education_section:
                education_items = education_section.find_all("li", class_="pv-education-entity")
                for item in education_items:
                    try:
                        school_element = item.find("h3", class_="pv-entity__school-name")
                        school = school_element.get_text(strip=True) if school_element else "Unknown"
                        
                        degree_element = item.find("p", class_="pv-entity__degree-name")
                        degree = degree_element.find("span").get_text(strip=True) if degree_element else "Unknown"
                        
                        education.append({
                            "school": school,
                            "degree": degree
                        })
                    except Exception as e:
                        self.logger.error(f"Error extracting education item: {str(e)}")
            
            # Extract skills
            skills = []
            skills_section = soup.find("section", {"id": "skills-section"})
            if skills_section:
                skill_items = skills_section.find_all("span", class_="pv-skill-category-entity__name-text")
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
