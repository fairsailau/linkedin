import os
import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime
from linkedin_scraper import LinkedInScraper, mock_linkedin_search
from data_manager import DataManager
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="LinkedIn Lead Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'leads' not in st.session_state:
    st.session_state.leads = pd.DataFrame(columns=[
        'name', 'title', 'company', 'location', 'industry', 
        'company_size', 'connections', 'profile_url', 'is_qualified'
    ])
if 'filters' not in st.session_state:
    st.session_state.filters = []
if 'current_job' not in st.session_state:
    st.session_state.current_job = None
if 'linkedin_credentials' not in st.session_state:
    st.session_state.linkedin_credentials = {"email": "", "password": ""}
if 'use_real_scraping' not in st.session_state:
    st.session_state.use_real_scraping = False
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = None
if 'storage_type' not in st.session_state:
    st.session_state.storage_type = "file"
if 'theme' not in st.session_state:
    st.session_state.theme = "light"
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Dashboard"

# Mock user credentials (in a real app, this would be stored securely)
USERS = {
    "admin": "password123",
    "demo": "demo123"
}

# Function to initialize LinkedIn scraper
def initialize_scraper(use_real_scraping=False):
    if st.session_state.scraper is not None:
        st.session_state.scraper.close()
    
    st.session_state.scraper = LinkedInScraper(headless=True)
    st.session_state.use_real_scraping = use_real_scraping

# Function to initialize data manager
def initialize_data_manager(storage_type="file"):
    st.session_state.data_manager = DataManager(storage_type=storage_type)
    st.session_state.storage_type = storage_type
    
    # Load data from storage
    if storage_type == "file" or storage_type == "database":
        leads = st.session_state.data_manager.load_leads()
        if not leads.empty:
            st.session_state.leads = leads
        
        search_history = st.session_state.data_manager.load_search_history()
        if search_history:
            st.session_state.search_history = search_history
        
        filters = st.session_state.data_manager.load_filters()
        if filters:
            st.session_state.filters = filters

# Function to scrape LinkedIn profiles
def scrape_linkedin(keywords, location, page_limit):
    """Scrape LinkedIn profiles based on search criteria"""
    st.info(f"Searching LinkedIn for '{keywords}' in '{location}'...")
    
    # Check if we should use real scraping or mock data
    if st.session_state.use_real_scraping and st.session_state.scraper:
        # Initialize progress bar
        progress_bar = st.progress(0)
        
        # Check if we need to log in
        if not st.session_state.scraper.is_logged_in:
            email = st.session_state.linkedin_credentials.get("email", "")
            password = st.session_state.linkedin_credentials.get("password", "")
            
            if email and password:
                with st.spinner("Logging in to LinkedIn..."):
                    login_success = st.session_state.scraper.login(email=email, password=password)
                    if not login_success:
                        st.error("Failed to log in to LinkedIn. Please check your credentials.")
                        return pd.DataFrame()
            else:
                st.error("LinkedIn credentials not set. Please configure them in Settings.")
                return pd.DataFrame()
        
        # Perform the search with progress updates
        try:
            # We'll update progress manually since we can't track exact progress
            for i in range(page_limit):
                progress_bar.progress((i + 1) / page_limit)
                time.sleep(0.5)  # Simulate progress
            
            # Perform the actual search
            leads_df = st.session_state.scraper.search_linkedin(keywords, location, page_limit)
            
            # Complete the progress bar
            progress_bar.progress(1.0)
            
            return leads_df
        except Exception as e:
            st.error(f"Error during LinkedIn search: {str(e)}")
            return pd.DataFrame()
    else:
        # Use mock data for demonstration
        progress_bar = st.progress(0)
        for i in range(page_limit):
            # Simulate page scraping
            time.sleep(0.5)
            progress_bar.progress((i + 1) / page_limit)
        
        return mock_linkedin_search(keywords, location, page_limit)

# Function to filter leads based on criteria
def filter_leads(leads_df, filter_criteria):
    """Filter leads based on specified criteria"""
    filtered_df = leads_df.copy()
    
    if filter_criteria.get('job_titles'):
        titles = [t.strip().lower() for t in filter_criteria['job_titles'].split(',')]
        filtered_df = filtered_df[filtered_df['title'].str.lower().apply(
            lambda x: any(title in x.lower() for title in titles)
        )]
    
    if filter_criteria.get('companies'):
        companies = [c.strip().lower() for c in filter_criteria['companies'].split(',')]
        filtered_df = filtered_df[filtered_df['company'].str.lower().apply(
            lambda x: any(company in x.lower() for company in companies)
        )]
    
    if filter_criteria.get('industries'):
        industries = [i.strip().lower() for i in filter_criteria['industries'].split(',')]
        filtered_df = filtered_df[filtered_df['industry'].str.lower().apply(
            lambda x: any(industry in x.lower() for industry in industries)
        )]
    
    if filter_criteria.get('locations'):
        locations = [l.strip().lower() for l in filter_criteria['locations'].split(',')]
        filtered_df = filtered_df[filtered_df['location'].str.lower().apply(
            lambda x: any(location in x.lower() for location in locations)
        )]
    
    if filter_criteria.get('min_connections') == '500+':
        filtered_df = filtered_df[filtered_df['connections'] == '500+']
    elif filter_criteria.get('min_connections') == '200-500':
        filtered_df = filtered_df[filtered_df['connections'].isin(['500+', '200-500'])]
    elif filter_criteria.get('min_connections') == '100-200':
        filtered_df = filtered_df[filtered_df['connections'].isin(['500+', '200-500', '100-200'])]
    
    if filter_criteria.get('qualified_only'):
        filtered_df = filtered_df[filtered_df['is_qualified'] == True]
    
    return filtered_df

# Login page
def show_login_page():
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 class='main-header' style='text-align: center;'>LinkedIn Lead Scraper</h1>", unsafe_allow_html=True)
        
        # Create a card for the login form
        st.markdown("""
        <div class="card" style="padding: 2rem; max-width: 400px; margin: 0 auto;">
            <h2 style="text-align: center; margin-bottom: 2rem;">Login</h2>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        # Add some space
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Center the login button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            login_button = st.button("Login", use_container_width=True)
        
        if login_button:
            if username in USERS and USERS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                
                # Initialize the scraper and data manager
                initialize_scraper(use_real_scraping=False)
                initialize_data_manager(storage_type="file")
                
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class='footer'>
        <p>For demonstration purposes, use:</p>
        <p>Username: <code>demo</code> | Password: <code>demo123</code></p>
        <p>© 2025 LinkedIn Lead Scraper | Version 1.0.0</p>
    </div>
    """, unsafe_allow_html=True)

# Dashboard page
def show_dashboard():
    # Create a container for the header
    with st.container():
        st.markdown("<h1 class='main-header'>LinkedIn Lead Scraper</h1>", unsafe_allow_html=True)
    
    # Create a horizontal navigation bar
    tabs = ["Dashboard", "Search LinkedIn", "Manage Leads", "Create Filters", "Analytics", "Settings"]
    
    # Create columns for each tab
    cols = st.columns(len(tabs))
    
    # Display tabs
    for i, tab in enumerate(tabs):
        if st.session_state.active_tab == tab:
            cols[i].markdown(f"""
            <div style="
                padding: 10px; 
                text-align: center; 
                border-bottom: 2px solid var(--primary-color); 
                font-weight: bold;
                color: var(--primary-color);
                cursor: pointer;
            ">{tab}</div>
            """, unsafe_allow_html=True)
        else:
            if cols[i].button(tab, key=f"tab_{tab}", use_container_width=True):
                st.session_state.active_tab = tab
                st.rerun()
    
    # Add a separator
    st.markdown("<hr style='margin-top: 0; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    # Display the active tab content
    if st.session_state.active_tab == "Dashboard":
        show_dashboard_page()
    elif st.session_state.active_tab == "Search LinkedIn":
        show_search_page()
    elif st.session_state.active_tab == "Manage Leads":
        show_leads_page()
    elif st.session_state.active_tab == "Create Filters":
        show_filters_page()
    elif st.session_state.active_tab == "Analytics":
        show_analytics_page()
    elif st.session_state.active_tab == "Settings":
        show_settings_page()
    
    # Add a sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="
            padding: 15px; 
            background-color: var(--light-bg); 
            border-radius: 5px; 
            margin-bottom: 20px;
            text-align: center;
        ">
            <h3 style="margin-top: 0;">Welcome, {st.session_state.username}!</h3>
            <div class="status-indicator status-active" style="display: inline-block;"></div> Active
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Quick Actions")
        
        if st.button("New Search", use_container_width=True):
            st.session_state.active_tab = "Search LinkedIn"
            st.rerun()
        
        if st.button("View All Leads", use_container_width=True):
            st.session_state.active_tab = "Manage Leads"
            st.rerun()
        
        if st.button("Create Filter", use_container_width=True):
            st.session_state.active_tab = "Create Filters"
            st.rerun()
        
        st.markdown("### Data Management")
        
        if st.button("Save All Data", use_container_width=True):
            if st.session_state.data_manager:
                with st.spinner("Saving data..."):
                    st.session_state.data_manager.save_leads(st.session_state.leads)
                    st.session_state.data_manager.save_search_history(st.session_state.search_history)
                    st.session_state.data_manager.save_filters(st.session_state.filters)
                    st.success("All data saved successfully!")
            else:
                st.error("Data manager not initialized. Please check settings.")
        
        st.markdown("### Theme")
        theme = st.selectbox("Select Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
        if theme.lower() != st.session_state.theme:
            st.session_state.theme = theme.lower()
            st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True):
            # Clean up resources
            if st.session_state.scraper:
                st.session_state.scraper.close()
                st.session_state.scraper = None
            
            # Save data before logout
            if st.session_state.data_manager:
                st.session_state.data_manager.save_leads(st.session_state.leads)
                st.session_state.data_manager.save_search_history(st.session_state.search_history)
                st.session_state.data_manager.save_filters(st.session_state.filters)
            
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()

# Dashboard page content
def show_dashboard_page():
    st.markdown("<h2 class='sub-header'>Dashboard</h2>", unsafe_allow_html=True)
    
    # Calculate statistics
    if not st.session_state.leads.empty and st.session_state.data_manager:
        stats = st.session_state.data_manager.get_lead_statistics(st.session_state.leads)
    else:
        stats = {
            'total_leads': len(st.session_state.leads),
            'qualified_leads': len(st.session_state.leads[st.session_state.leads['is_qualified'] == True]) if not st.session_state.leads.empty else 0,
            'qualification_rate': 0,
            'top_companies': {},
            'top_titles': {},
            'top_locations': {},
            'connections_distribution': {}
        }
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Searches</div>
        </div>
        """.format(len(st.session_state.search_history)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Total Leads</div>
        </div>
        """.format(stats['total_leads']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Qualified Leads</div>
        </div>
        """.format(stats['qualified_leads']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}%</div>
            <div class='metric-label'>Qualification Rate</div>
        </div>
        """.format(stats['qualification_rate']), unsafe_allow_html=True)
    
    # Create two columns for charts and recent activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<h3 class='sub-header'>Lead Overview</h3>", unsafe_allow_html=True)
        
        # Create a simple chart if we have leads
        if not st.session_state.leads.empty:
            # Create a pie chart for qualified vs unqualified
            fig = go.Figure(data=[go.Pie(
                labels=['Qualified', 'Unqualified'],
                values=[stats['qualified_leads'], stats['total_leads'] - stats['qualified_leads']],
                hole=.3,
                marker_colors=['#0077B5', '#86888a']
            )])
            
            fig.update_layout(
                title="Qualified vs Unqualified Leads",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a bar chart for top companies
            if stats['top_companies']:
                companies = list(stats['top_companies'].keys())[:5]
                counts = list(stats['top_companies'].values())[:5]
                
                fig = go.Figure(data=[go.Bar(
                    x=companies,
                    y=counts,
                    marker_color='#0077B5'
                )])
                
                fig.update_layout(
                    title="Top Companies",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No leads data available. Start by searching for leads on LinkedIn.")
    
    with col2:
        st.markdown("<h3 class='sub-header'>Recent Activity</h3>", unsafe_allow_html=True)
        
        if st.session_state.search_history:
            for search in reversed(st.session_state.search_history[-5:]):
                st.markdown(f"""
                <div class='card'>
                    <strong>Search:</strong> {search['keywords']} in {search['location']}<br>
                    <strong>Date:</strong> {search['date']}<br>
                    <strong>Results:</strong> {search['results']} leads found
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent activity. Start by searching for leads on LinkedIn.")
    
    # Quick actions
    st.markdown("<h3 class='sub-header'>Quick Actions</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("New Search", key="dashboard_new_search", use_container_width=True):
            st.session_state.active_tab = "Search LinkedIn"
            st.rerun()
    
    with col2:
        if st.button("View All Leads", key="dashboard_view_leads", use_container_width=True):
            st.session_state.active_tab = "Manage Leads"
            st.rerun()
    
    with col3:
        if st.button("View Analytics", key="dashboard_analytics", use_container_width=True):
            st.session_state.active_tab = "Analytics"
            st.rerun()

# Search page content
def show_search_page():
    st.markdown("<h2 class='sub-header'>Search LinkedIn</h2>", unsafe_allow_html=True)
    
    # Display warning about LinkedIn scraping
    if not st.session_state.use_real_scraping:
        st.warning("""
        **Note:** You are currently using mock data for demonstration purposes. 
        To use real LinkedIn data, please configure your LinkedIn credentials in Settings 
        and enable real scraping. Be aware that scraping LinkedIn may violate their Terms of Service.
        """)
    
    # Create a card for the search form
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input("Keywords (e.g., 'software engineer python')")
        
        with col2:
            location = st.text_input("Location (e.g., 'San Francisco')")
        
        page_limit = st.slider("Number of pages to scrape", 1, 10, 3)
        
        # Center the search button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_submitted = st.form_submit_button("Start Search", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if search_submitted and keywords and location:
        # Perform the search
        new_leads = scrape_linkedin(keywords, location, page_limit)
        
        if not new_leads.empty:
            # Clean data if data manager is available
            if st.session_state.data_manager:
                new_leads = st.session_state.data_manager.clean_data(new_leads)
            
            # Update session state
            if not st.session_state.leads.empty:
                st.session_state.leads = pd.concat([st.session_state.leads, new_leads]).reset_index(drop=True)
            else:
                st.session_state.leads = new_leads
            
            # Add to search history
            search_entry = {
                'keywords': keywords,
                'location': location,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'results': len(new_leads)
            }
            st.session_state.search_history.append(search_entry)
            
            # Save data if data manager is available
            if st.session_state.data_manager:
                st.session_state.data_manager.save_leads(st.session_state.leads)
                st.session_state.data_manager.save_search_history(st.session_state.search_history)
            
            st.success(f"Search completed! Found {len(new_leads)} leads.")
            
            # Display results
            st.markdown("<h3 class='sub-header'>Search Results</h3>", unsafe_allow_html=True)
            
            # Create a more visually appealing display of leads
            for i, lead in new_leads.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class='profile-card'>
                        <div class='profile-header'>
                            <div class='profile-info'>
                                <div class='profile-name'>{lead['name']}</div>
                                <div class='profile-title'>{lead['title']}</div>
                                <div class='profile-location'>{lead['location']}</div>
                            </div>
                            <div>
                                <span class='badge badge-{'success' if lead['is_qualified'] else 'light'}'>
                                    {'Qualified' if lead['is_qualified'] else 'Unqualified'}
                                </span>
                            </div>
                        </div>
                        <div class='profile-section'>
                            <div class='profile-section-item'>
                                <div class='profile-section-item-title'>Company: {lead['company']}</div>
                                <div class='profile-section-item-subtitle'>Industry: {lead['industry']}</div>
                                <div class='profile-section-item-subtitle'>Company Size: {lead['company_size']}</div>
                                <div class='profile-section-item-subtitle'>Connections: {lead['connections']}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <a href='{lead['profile_url']}' target='_blank' style='color: var(--primary-color); text-decoration: none;'>
                                View Profile →
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Export options
            st.markdown("<h3 class='sub-header'>Export Results</h3>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export as CSV", key="search_export_csv", use_container_width=True):
                    if st.session_state.data_manager:
                        export_path = st.session_state.data_manager.export_leads(new_leads, format="csv")
                        if export_path:
                            with open(export_path, "r") as f:
                                csv_data = f.read()
                            
                            st.download_button(
                                label="Download CSV",
                                data=csv_data,
                                file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv"
                            )
                    else:
                        csv = new_leads.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
            
            with col2:
                if st.button("Export as Excel", key="search_export_excel", use_container_width=True):
                    if st.session_state.data_manager:
                        export_path = st.session_state.data_manager.export_leads(new_leads, format="excel")
                        if export_path:
                            with open(export_path, "rb") as f:
                                excel_data = f.read()
                            
                            st.download_button(
                                label="Download Excel",
                                data=excel_data,
                                file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        # Create a temporary Excel file
                        excel_file = f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        new_leads.to_excel(excel_file, index=False)
                        
                        # Read the file and provide download button
                        with open(excel_file, "rb") as f:
                            excel_data = f.read()
                        
                        st.download_button(
                            label="Download Excel",
                            data=excel_data,
                            file_name=excel_file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        # Clean up the temporary file
                        os.remove(excel_file)
            
            with col3:
                if st.button("Export as JSON", key="search_export_json", use_container_width=True):
                    if st.session_state.data_manager:
                        export_path = st.session_state.data_manager.export_leads(new_leads, format="json")
                        if export_path:
                            with open(export_path, "r") as f:
                                json_data = f.read()
                            
                            st.download_button(
                                label="Download JSON",
                                data=json_data,
                                file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                mime="application/json"
                            )
                    else:
                        json_data = new_leads.to_json(orient='records', indent=4)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                            mime="application/json"
                        )
        else:
            st.error("No leads found. Please try different search criteria or check your LinkedIn credentials.")

# Leads page content
def show_leads_page():
    st.markdown("<h2 class='sub-header'>Manage Leads</h2>", unsafe_allow_html=True)
    
    if st.session_state.leads.empty:
        st.info("No leads found. Start by searching for leads on LinkedIn.")
        
        # Add a button to go to search page
        if st.button("Go to Search", use_container_width=True):
            st.session_state.active_tab = "Search LinkedIn"
            st.rerun()
        
        return
    
    # Filters
    st.markdown("<h3 class='sub-header'>Filter Leads</h3>", unsafe_allow_html=True)
    
    with st.expander("Filter Options", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            filter_title = st.text_input("Filter by Job Title")
            filter_company = st.text_input("Filter by Company")
            filter_qualified = st.checkbox("Show only qualified leads")
        
        with col2:
            filter_industry = st.text_input("Filter by Industry")
            filter_location = st.text_input("Filter by Location")
            filter_connections = st.selectbox(
                "Minimum Connections",
                options=["Any", "500+", "200-500", "100-200"]
            )
        
        # Apply filters
        filtered_df = st.session_state.leads.copy()
        
        if filter_title:
            filtered_df = filtered_df[filtered_df['title'].str.contains(filter_title, case=False)]
        
        if filter_company:
            filtered_df = filtered_df[filtered_df['company'].str.contains(filter_company, case=False)]
        
        if filter_industry:
            filtered_df = filtered_df[filtered_df['industry'].str.contains(filter_industry, case=False)]
        
        if filter_location:
            filtered_df = filtered_df[filtered_df['location'].str.contains(filter_location, case=False)]
        
        if filter_connections != "Any":
            if filter_connections == "500+":
                filtered_df = filtered_df[filtered_df['connections'] == '500+']
            elif filter_connections == "200-500":
                filtered_df = filtered_df[filtered_df['connections'].isin(['500+', '200-500'])]
            elif filter_connections == "100-200":
                filtered_df = filtered_df[filtered_df['connections'].isin(['500+', '200-500', '100-200'])]
        
        if filter_qualified:
            filtered_df = filtered_df[filtered_df['is_qualified'] == True]
    
    # Display filtered leads
    st.markdown("<h3 class='sub-header'>Leads</h3>", unsafe_allow_html=True)
    st.write(f"Showing {len(filtered_df)} of {len(st.session_state.leads)} leads")
    
    # Add tabs for different views
    lead_tabs = ["Card View", "Table View"]
    lead_view_tab = st.radio("Select View", lead_tabs, horizontal=True)
    
    # Add a button to view profile details
    if not filtered_df.empty:
        if lead_view_tab == "Card View":
            # Display leads as cards
            for i, lead in filtered_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class='profile-card'>
                        <div class='profile-header'>
                            <div class='profile-info'>
                                <div class='profile-name'>{lead['name']}</div>
                                <div class='profile-title'>{lead['title']}</div>
                                <div class='profile-location'>{lead['location']}</div>
                            </div>
                            <div>
                                <span class='badge badge-{'success' if lead['is_qualified'] else 'light'}'>
                                    {'Qualified' if lead['is_qualified'] else 'Unqualified'}
                                </span>
                            </div>
                        </div>
                        <div class='profile-section'>
                            <div class='profile-section-item'>
                                <div class='profile-section-item-title'>Company: {lead['company']}</div>
                                <div class='profile-section-item-subtitle'>Industry: {lead['industry']}</div>
                                <div class='profile-section-item-subtitle'>Company Size: {lead['company_size']}</div>
                                <div class='profile-section-item-subtitle'>Connections: {lead['connections']}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <a href='{lead['profile_url']}' target='_blank' style='color: var(--primary-color); text-decoration: none;'>
                                View Profile →
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Display the dataframe with an edit option for is_qualified
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "profile_url": st.column_config.LinkColumn("Profile URL"),
                    "is_qualified": st.column_config.CheckboxColumn("Qualified?"),
                    "notes": st.column_config.TextColumn("Notes", width="large")
                }
            )
            
            # Save changes to the main dataframe
            if not edited_df.equals(filtered_df):
                for index, row in edited_df.iterrows():
                    original_index = st.session_state.leads.index[
                        (st.session_state.leads['name'] == row['name']) & 
                        (st.session_state.leads['profile_url'] == row['profile_url'])
                    ].tolist()
                    
                    if original_index:
                        st.session_state.leads.loc[original_index[0], 'is_qualified'] = row['is_qualified']
                        
                        # Update notes if available
                        if 'notes' in row and 'notes' in st.session_state.leads.columns:
                            st.session_state.leads.loc[original_index[0], 'notes'] = row['notes']
                
                # Save changes if data manager is available
                if st.session_state.data_manager:
                    st.session_state.data_manager.save_leads(st.session_state.leads)
                
                st.success("Changes saved successfully!")
        
        # Profile details section
        st.markdown("<h3 class='sub-header'>Profile Details</h3>", unsafe_allow_html=True)
        
        selected_profile = st.selectbox(
            "Select a profile to view details",
            options=filtered_df['name'].tolist(),
            format_func=lambda x: f"{x} - {filtered_df[filtered_df['name'] == x]['title'].iloc[0]}"
        )
        
        if selected_profile and st.button("View Profile Details", key="view_profile_details"):
            selected_row = filtered_df[filtered_df['name'] == selected_profile].iloc[0]
            profile_url = selected_row['profile_url']
            
            with st.spinner("Fetching profile details..."):
                if st.session_state.use_real_scraping and st.session_state.scraper and st.session_state.scraper.is_logged_in:
                    # Get real profile details
                    profile_details = st.session_state.scraper.get_profile_details(profile_url)
                else:
                    # Generate mock profile details
                    profile_details = {
                        'name': selected_row['name'],
                        'headline': selected_row['title'] + " at " + selected_row['company'],
                        'location': selected_row['location'],
                        'experience': [
                            {'title': selected_row['title'], 'company': selected_row['company'], 'date': "2020 - Present"},
                            {'title': "Previous Role", 'company': "Previous Company", 'date': "2018 - 2020"}
                        ],
                        'education': [
                            {'school': "University of Example", 'degree': "Bachelor's Degree, Computer Science"}
                        ],
                        'skills': ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                    }
                
                # Display profile details
                if profile_details:
                    st.markdown(f"""
                    <div class='profile-card'>
                        <div class='profile-header'>
                            <div class='profile-info'>
                                <div class='profile-name'>{profile_details.get('name', 'Unknown')}</div>
                                <div class='profile-title'>{profile_details.get('headline', '')}</div>
                                <div class='profile-location'>{profile_details.get('location', '')}</div>
                            </div>
                            <div>
                                <span class='badge badge-{'success' if selected_row.get('is_qualified', False) else 'light'}'>
                                    {'Qualified' if selected_row.get('is_qualified', False) else 'Unqualified'}
                                </span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Experience section
                    if profile_details.get('experience'):
                        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
                        st.markdown("<div class='profile-section-title'>Experience</div>", unsafe_allow_html=True)
                        
                        for exp in profile_details.get('experience'):
                            st.markdown(f"""
                            <div class='profile-section-item'>
                                <div class='profile-section-item-title'>{exp.get('title', '')}</div>
                                <div class='profile-section-item-subtitle'>{exp.get('company', '')}</div>
                                <div class='profile-section-item-date'>{exp.get('date', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Education section
                    if profile_details.get('education'):
                        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
                        st.markdown("<div class='profile-section-title'>Education</div>", unsafe_allow_html=True)
                        
                        for edu in profile_details.get('education'):
                            st.markdown(f"""
                            <div class='profile-section-item'>
                                <div class='profile-section-item-title'>{edu.get('school', '')}</div>
                                <div class='profile-section-item-subtitle'>{edu.get('degree', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Skills section
                    if profile_details.get('skills'):
                        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
                        st.markdown("<div class='profile-section-title'>Skills</div>", unsafe_allow_html=True)
                        
                        st.markdown("<div class='skill-tags'>", unsafe_allow_html=True)
                        for skill in profile_details.get('skills'):
                            st.markdown(f"<div class='skill-tag'>{skill}</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Actions section
                    st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
                    st.markdown("<div class='profile-section-title'>Actions</div>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Get current qualification status
                        is_qualified = selected_row.get('is_qualified', False)
                        
                        if st.button("Mark as " + ("Unqualified" if is_qualified else "Qualified"), key="toggle_qualified"):
                            # Find the lead in the main dataframe
                            original_index = st.session_state.leads.index[
                                (st.session_state.leads['name'] == selected_row['name']) & 
                                (st.session_state.leads['profile_url'] == selected_row['profile_url'])
                            ].tolist()
                            
                            if original_index:
                                # Toggle qualification status
                                st.session_state.leads.loc[original_index[0], 'is_qualified'] = not is_qualified
                                
                                # Save changes if data manager is available
                                if st.session_state.data_manager:
                                    st.session_state.data_manager.save_leads(st.session_state.leads)
                                
                                st.success(f"Marked as {('Unqualified' if is_qualified else 'Qualified')}")
                                st.rerun()
                    
                    with col2:
                        if st.button("View LinkedIn Profile", key="view_linkedin"):
                            st.markdown(f"<a href='{profile_url}' target='_blank'>Open LinkedIn Profile</a>", unsafe_allow_html=True)
                    
                    # Notes section
                    st.markdown("<div class='profile-section-title'>Notes</div>", unsafe_allow_html=True)
                    
                    # Add notes
                    notes = selected_row.get('notes', '')
                    new_notes = st.text_area("Add or update notes", value=notes, key="profile_notes")
                    
                    if st.button("Save Notes", key="save_notes"):
                        # Find the lead in the main dataframe
                        original_index = st.session_state.leads.index[
                            (st.session_state.leads['name'] == selected_row['name']) & 
                            (st.session_state.leads['profile_url'] == selected_row['profile_url'])
                        ].tolist()
                        
                        if original_index:
                            # Ensure notes column exists
                            if 'notes' not in st.session_state.leads.columns:
                                st.session_state.leads['notes'] = ''
                            
                            # Update notes
                            st.session_state.leads.loc[original_index[0], 'notes'] = new_notes
                            
                            # Save changes if data manager is available
                            if st.session_state.data_manager:
                                st.session_state.data_manager.save_leads(st.session_state.leads)
                            
                            st.success("Notes saved successfully!")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("Could not retrieve profile details.")
    
    # Export options
    st.markdown("<h3 class='sub-header'>Export Leads</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export as CSV", key="leads_export_csv", use_container_width=True):
            if st.session_state.data_manager:
                export_path = st.session_state.data_manager.export_leads(filtered_df, format="csv")
                if export_path:
                    with open(export_path, "r") as f:
                        csv_data = f.read()
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
            else:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("Export as Excel", key="leads_export_excel", use_container_width=True):
            if st.session_state.data_manager:
                export_path = st.session_state.data_manager.export_leads(filtered_df, format="excel")
                if export_path:
                    with open(export_path, "rb") as f:
                        excel_data = f.read()
                    
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                # Create a temporary Excel file
                excel_file = f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                filtered_df.to_excel(excel_file, index=False)
                
                # Read the file and provide download button
                with open(excel_file, "rb") as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Clean up the temporary file
                os.remove(excel_file)
    
    with col3:
        if st.button("Export as JSON", key="leads_export_json", use_container_width=True):
            if st.session_state.data_manager:
                export_path = st.session_state.data_manager.export_leads(filtered_df, format="json")
                if export_path:
                    with open(export_path, "r") as f:
                        json_data = f.read()
                    
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
            else:
                json_data = filtered_df.to_json(orient='records', indent=4)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"linkedin_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )

# Filters page content
def show_filters_page():
    st.markdown("<h2 class='sub-header'>Create Filters</h2>", unsafe_allow_html=True)
    
    # Create new filter
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("New Filter")
    
    with st.form("filter_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            filter_name = st.text_input("Filter Name")
            job_titles = st.text_input("Job Titles (comma-separated)")
            companies = st.text_input("Companies (comma-separated)")
        
        with col2:
            industries = st.text_input("Industries (comma-separated)")
            locations = st.text_input("Locations (comma-separated)")
            min_connections = st.selectbox(
                "Minimum Connections",
                options=["Any", "500+", "200-500", "100-200"]
            )
        
        qualified_only = st.checkbox("Qualified leads only")
        
        # Center the create button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            filter_submitted = st.form_submit_button("Create Filter", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if filter_submitted and filter_name:
        # Create new filter
        new_filter = {
            'name': filter_name,
            'job_titles': job_titles,
            'companies': companies,
            'industries': industries,
            'locations': locations,
            'min_connections': min_connections,
            'qualified_only': qualified_only,
            'date_created': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        st.session_state.filters.append(new_filter)
        
        # Save filters if data manager is available
        if st.session_state.data_manager:
            st.session_state.data_manager.save_filters(st.session_state.filters)
        
        st.success(f"Filter '{filter_name}' created successfully!")
    
    # Display existing filters
    st.markdown("<h3 class='sub-header'>Saved Filters</h3>", unsafe_allow_html=True)
    
    if not st.session_state.filters:
        st.info("No filters created yet.")
    else:
        # Create a grid layout for filters
        cols = st.columns(2)
        
        for i, filter_item in enumerate(st.session_state.filters):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='card'>
                    <h4>{filter_item['name']}</h4>
                    <p><small>Created: {filter_item['date_created']}</small></p>
                    <p><strong>Job Titles:</strong> {filter_item['job_titles'] or 'Any'}</p>
                    <p><strong>Companies:</strong> {filter_item['companies'] or 'Any'}</p>
                    <p><strong>Industries:</strong> {filter_item['industries'] or 'Any'}</p>
                    <p><strong>Locations:</strong> {filter_item['locations'] or 'Any'}</p>
                    <p><strong>Minimum Connections:</strong> {filter_item['min_connections']}</p>
                    <p><strong>Qualified Only:</strong> {'Yes' if filter_item['qualified_only'] else 'No'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"Apply Filter", key=f"apply_{i}", use_container_width=True):
                        # Apply filter to leads
                        filter_criteria = {
                            'job_titles': filter_item['job_titles'],
                            'companies': filter_item['companies'],
                            'industries': filter_item['industries'],
                            'locations': filter_item['locations'],
                            'min_connections': filter_item['min_connections'],
                            'qualified_only': filter_item['qualified_only']
                        }
                        
                        filtered_leads = filter_leads(st.session_state.leads, filter_criteria)
                        
                        st.session_state.filtered_leads = filtered_leads
                        st.success(f"Filter applied! Found {len(filtered_leads)} matching leads.")
                        
                        # Display filtered leads
                        st.dataframe(filtered_leads, use_container_width=True)
                        
                        # Export options
                        if not filtered_leads.empty:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                csv = filtered_leads.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                    mime="text/csv"
                                )
                            
                            with col2:
                                # Create a temporary Excel file
                                excel_file = f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                                filtered_leads.to_excel(excel_file, index=False)
                                
                                # Read the file and provide download button
                                with open(excel_file, "rb") as f:
                                    excel_data = f.read()
                                
                                st.download_button(
                                    label="Download Excel",
                                    data=excel_data,
                                    file_name=excel_file,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                
                                # Clean up the temporary file
                                os.remove(excel_file)
                            
                            with col3:
                                json_data = filtered_leads.to_json(orient='records', indent=4)
                                st.download_button(
                                    label="Download JSON",
                                    data=json_data,
                                    file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                    mime="application/json"
                                )
                
                with col2:
                    if st.button(f"Delete Filter", key=f"delete_{i}", use_container_width=True):
                        st.session_state.filters.pop(i)
                        
                        # Save filters if data manager is available
                        if st.session_state.data_manager:
                            st.session_state.data_manager.save_filters(st.session_state.filters)
                        
                        st.experimental_rerun()

# Analytics page content
def show_analytics_page():
    st.markdown("<h2 class='sub-header'>Analytics</h2>", unsafe_allow_html=True)
    
    if st.session_state.leads.empty:
        st.info("No leads data available for analytics. Start by searching for leads on LinkedIn.")
        
        # Add a button to go to search page
        if st.button("Go to Search", key="analytics_go_search", use_container_width=True):
            st.session_state.active_tab = "Search LinkedIn"
            st.rerun()
        
        return
    
    # Calculate statistics
    if st.session_state.data_manager:
        stats = st.session_state.data_manager.get_lead_statistics(st.session_state.leads)
    else:
        # Calculate basic statistics manually
        total_leads = len(st.session_state.leads)
        qualified_leads = len(st.session_state.leads[st.session_state.leads['is_qualified'] == True])
        qualification_rate = round((qualified_leads / total_leads) * 100, 2) if total_leads > 0 else 0
        
        # Calculate top companies
        top_companies = st.session_state.leads['company'].value_counts().head(5).to_dict()
        
        # Calculate top titles
        top_titles = st.session_state.leads['title'].value_counts().head(5).to_dict()
        
        # Calculate top locations
        top_locations = st.session_state.leads['location'].value_counts().head(5).to_dict()
        
        # Calculate connections distribution
        connections_distribution = st.session_state.leads['connections'].value_counts().to_dict()
        
        stats = {
            'total_leads': total_leads,
            'qualified_leads': qualified_leads,
            'qualification_rate': qualification_rate,
            'top_companies': top_companies,
            'top_titles': top_titles,
            'top_locations': top_locations,
            'connections_distribution': connections_distribution
        }
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Total Leads</div>
        </div>
        """.format(stats['total_leads']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Qualified Leads</div>
        </div>
        """.format(stats['qualified_leads']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}%</div>
            <div class='metric-label'>Qualification Rate</div>
        </div>
        """.format(stats['qualification_rate']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Searches</div>
        </div>
        """.format(len(st.session_state.search_history)), unsafe_allow_html=True)
    
    # Create tabs for different analytics views
    analytics_tabs = ["Overview", "Companies", "Job Titles", "Locations", "Search History"]
    analytics_tab = st.radio("Analytics View", analytics_tabs, horizontal=True)
    
    if analytics_tab == "Overview":
        # Create a pie chart for qualified vs unqualified
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure(data=[go.Pie(
                labels=['Qualified', 'Unqualified'],
                values=[stats['qualified_leads'], stats['total_leads'] - stats['qualified_leads']],
                hole=.3,
                marker_colors=['#0077B5', '#86888a']
            )])
            
            fig.update_layout(
                title="Qualified vs Unqualified Leads",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Create a bar chart for connections distribution
            connections_df = pd.DataFrame({
                'Connections': list(stats['connections_distribution'].keys()),
                'Count': list(stats['connections_distribution'].values())
            })
            
            fig = px.bar(
                connections_df,
                x='Connections',
                y='Count',
                color='Count',
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                title="Connections Distribution",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif analytics_tab == "Companies":
        if stats['top_companies']:
            # Create a bar chart for top companies
            companies = list(stats['top_companies'].keys())
            counts = list(stats['top_companies'].values())
            
            fig = px.bar(
                x=companies,
                y=counts,
                labels={'x': 'Company', 'y': 'Count'},
                color=counts,
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                title="Top Companies",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a table with company details
            st.markdown("<h3 class='sub-header'>Company Details</h3>", unsafe_allow_html=True)
            
            company_data = []
            for company in companies:
                company_leads = st.session_state.leads[st.session_state.leads['company'] == company]
                qualified_count = len(company_leads[company_leads['is_qualified'] == True])
                qualification_rate = round((qualified_count / len(company_leads)) * 100, 2)
                
                company_data.append({
                    'Company': company,
                    'Total Leads': len(company_leads),
                    'Qualified Leads': qualified_count,
                    'Qualification Rate': f"{qualification_rate}%"
                })
            
            company_df = pd.DataFrame(company_data)
            st.dataframe(company_df, use_container_width=True)
        else:
            st.info("No company data available.")
    
    elif analytics_tab == "Job Titles":
        if stats['top_titles']:
            # Create a bar chart for top job titles
            titles = list(stats['top_titles'].keys())
            counts = list(stats['top_titles'].values())
            
            fig = px.bar(
                x=titles,
                y=counts,
                labels={'x': 'Job Title', 'y': 'Count'},
                color=counts,
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                title="Top Job Titles",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a table with job title details
            st.markdown("<h3 class='sub-header'>Job Title Details</h3>", unsafe_allow_html=True)
            
            title_data = []
            for title in titles:
                title_leads = st.session_state.leads[st.session_state.leads['title'] == title]
                qualified_count = len(title_leads[title_leads['is_qualified'] == True])
                qualification_rate = round((qualified_count / len(title_leads)) * 100, 2)
                
                title_data.append({
                    'Job Title': title,
                    'Total Leads': len(title_leads),
                    'Qualified Leads': qualified_count,
                    'Qualification Rate': f"{qualification_rate}%"
                })
            
            title_df = pd.DataFrame(title_data)
            st.dataframe(title_df, use_container_width=True)
        else:
            st.info("No job title data available.")
    
    elif analytics_tab == "Locations":
        if stats['top_locations']:
            # Create a bar chart for top locations
            locations = list(stats['top_locations'].keys())
            counts = list(stats['top_locations'].values())
            
            fig = px.bar(
                x=locations,
                y=counts,
                labels={'x': 'Location', 'y': 'Count'},
                color=counts,
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                title="Top Locations",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a table with location details
            st.markdown("<h3 class='sub-header'>Location Details</h3>", unsafe_allow_html=True)
            
            location_data = []
            for location in locations:
                location_leads = st.session_state.leads[st.session_state.leads['location'] == location]
                qualified_count = len(location_leads[location_leads['is_qualified'] == True])
                qualification_rate = round((qualified_count / len(location_leads)) * 100, 2)
                
                location_data.append({
                    'Location': location,
                    'Total Leads': len(location_leads),
                    'Qualified Leads': qualified_count,
                    'Qualification Rate': f"{qualification_rate}%"
                })
            
            location_df = pd.DataFrame(location_data)
            st.dataframe(location_df, use_container_width=True)
        else:
            st.info("No location data available.")
    
    elif analytics_tab == "Search History":
        if st.session_state.search_history:
            # Create a dataframe from search history
            search_df = pd.DataFrame(st.session_state.search_history)
            
            # Display search history metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # Create a bar chart for search keywords
                keywords_counts = {}
                for search in st.session_state.search_history:
                    keywords = search['keywords']
                    if keywords in keywords_counts:
                        keywords_counts[keywords] += 1
                    else:
                        keywords_counts[keywords] = 1
                
                keywords_df = pd.DataFrame({
                    'Keywords': list(keywords_counts.keys()),
                    'Count': list(keywords_counts.values())
                })
                
                fig = px.bar(
                    keywords_df,
                    x='Keywords',
                    y='Count',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(
                    title="Search Keywords",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Create a bar chart for search locations
                location_counts = {}
                for search in st.session_state.search_history:
                    location = search['location']
                    if location in location_counts:
                        location_counts[location] += 1
                    else:
                        location_counts[location] = 1
                
                location_df = pd.DataFrame({
                    'Location': list(location_counts.keys()),
                    'Count': list(location_counts.values())
                })
                
                fig = px.bar(
                    location_df,
                    x='Location',
                    y='Count',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(
                    title="Search Locations",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display search history table
            st.markdown("<h3 class='sub-header'>Search History</h3>", unsafe_allow_html=True)
            st.dataframe(search_df, use_container_width=True)
        else:
            st.info("No search history available.")
    
    # Export analytics
    st.markdown("<h3 class='sub-header'>Export Analytics</h3>", unsafe_allow_html=True)
    
    if st.button("Export Analytics Report", key="export_analytics", use_container_width=True):
        # Create a report with all analytics data
        report = f"""
        # LinkedIn Lead Scraper Analytics Report
        Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        
        ## Key Metrics
        - Total Leads: {stats['total_leads']}
        - Qualified Leads: {stats['qualified_leads']}
        - Qualification Rate: {stats['qualification_rate']}%
        - Total Searches: {len(st.session_state.search_history)}
        
        ## Top Companies
        {pd.DataFrame({'Company': list(stats['top_companies'].keys()), 'Count': list(stats['top_companies'].values())}).to_string(index=False)}
        
        ## Top Job Titles
        {pd.DataFrame({'Title': list(stats['top_titles'].keys()), 'Count': list(stats['top_titles'].values())}).to_string(index=False)}
        
        ## Top Locations
        {pd.DataFrame({'Location': list(stats['top_locations'].keys()), 'Count': list(stats['top_locations'].values())}).to_string(index=False)}
        
        ## Connections Distribution
        {pd.DataFrame({'Connections': list(stats['connections_distribution'].keys()), 'Count': list(stats['connections_distribution'].values())}).to_string(index=False)}
        
        ## Qualification Analysis
        {pd.DataFrame({'Status': ['Qualified', 'Unqualified'], 'Count': [stats['qualified_leads'], stats['total_leads'] - stats['qualified_leads']]}).to_string(index=False)}
        """
        
        # Provide download button for the report
        st.download_button(
            label="Download Report",
            data=report,
            file_name=f"linkedin_analytics_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# Settings page content
def show_settings_page():
    st.markdown("<h2 class='sub-header'>Settings</h2>", unsafe_allow_html=True)
    
    # Create tabs for different settings
    settings_tabs = ["LinkedIn", "Data Storage", "Account", "Application", "About"]
    settings_tab = st.radio("Settings", settings_tabs, horizontal=True)
    
    if settings_tab == "LinkedIn":
        st.markdown("<h3 class='sub-header'>LinkedIn Settings</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.warning("""
        **Important:** Scraping LinkedIn may violate their Terms of Service. 
        Use at your own risk and consider using LinkedIn's official API where possible.
        """)
        
        email = st.text_input("LinkedIn Email", value=st.session_state.linkedin_credentials.get("email", ""))
        password = st.text_input("LinkedIn Password", type="password", value=st.session_state.linkedin_credentials.get("password", ""))
        
        use_real_scraping = st.checkbox("Enable real LinkedIn scraping", value=st.session_state.use_real_scraping)
        
        if st.button("Save LinkedIn Settings", key="save_linkedin_settings", use_container_width=True):
            st.session_state.linkedin_credentials = {"email": email, "password": password}
            
            # Update scraper settings
            initialize_scraper(use_real_scraping=use_real_scraping)
            
            st.success("LinkedIn settings saved successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif settings_tab == "Data Storage":
        st.markdown("<h3 class='sub-header'>Data Storage Settings</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        storage_type = st.radio(
            "Storage Type",
            options=["file", "database"],
            index=0 if st.session_state.storage_type == "file" else 1,
            horizontal=True
        )
        
        if storage_type == "database":
            db_path = st.text_input("Database Path", value="linkedin_leads.db")
        else:
            data_dir = st.text_input("Data Directory", value="data")
        
        if st.button("Save Storage Settings", key="save_storage_settings", use_container_width=True):
            # Initialize data manager with new settings
            if storage_type == "database":
                initialize_data_manager(storage_type=storage_type)
            else:
                initialize_data_manager(storage_type=storage_type)
            
            st.success("Storage settings saved successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Data management
        st.markdown("<h3 class='sub-header'>Data Management</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Search History", key="clear_search_history", use_container_width=True):
                st.session_state.search_history = []
                
                # Save empty search history if data manager is available
                if st.session_state.data_manager:
                    st.session_state.data_manager.save_search_history([])
                
                st.success("Search history cleared!")
            
            if st.button("Clear All Leads", key="clear_leads", use_container_width=True):
                st.session_state.leads = pd.DataFrame(columns=[
                    'name', 'title', 'company', 'location', 'industry', 
                    'company_size', 'connections', 'profile_url', 'is_qualified'
                ])
                
                # Save empty leads if data manager is available
                if st.session_state.data_manager:
                    st.session_state.data_manager.save_leads(st.session_state.leads)
                
                st.success("All leads cleared!")
        
        with col2:
            if st.button("Clear All Filters", key="clear_filters", use_container_width=True):
                st.session_state.filters = []
                
                # Save empty filters if data manager is available
                if st.session_state.data_manager:
                    st.session_state.data_manager.save_filters([])
                
                st.success("All filters cleared!")
            
            if st.button("Reset All Data", key="reset_data", use_container_width=True):
                st.session_state.search_history = []
                st.session_state.leads = pd.DataFrame(columns=[
                    'name', 'title', 'company', 'location', 'industry', 
                    'company_size', 'connections', 'profile_url', 'is_qualified'
                ])
                st.session_state.filters = []
                
                # Save empty data if data manager is available
                if st.session_state.data_manager:
                    st.session_state.data_manager.save_search_history([])
                    st.session_state.data_manager.save_leads(st.session_state.leads)
                    st.session_state.data_manager.save_filters([])
                
                st.success("All data reset successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif settings_tab == "Account":
        st.markdown("<h3 class='sub-header'>Account Settings</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password", use_container_width=True):
                if current_password != USERS[st.session_state.username]:
                    st.error("Current password is incorrect")
                elif new_password != confirm_password:
                    st.error("New passwords do not match")
                elif not new_password:
                    st.error("New password cannot be empty")
                else:
                    # In a real app, this would update the password in a database
                    USERS[st.session_state.username] = new_password
                    st.success("Password changed successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif settings_tab == "Application":
        st.markdown("<h3 class='sub-header'>Application Settings</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        default_page_limit = st.slider("Default page limit", 1, 10, 3)
        auto_qualify = st.checkbox("Auto-qualify leads based on criteria")
        enable_notifications = st.checkbox("Enable browser notifications")
        
        theme = st.selectbox("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
        
        if st.button("Save Application Settings", key="save_app_settings", use_container_width=True):
            # Update theme
            if theme.lower() != st.session_state.theme:
                st.session_state.theme = theme.lower()
                st.rerun()
            
            st.success("Application settings saved successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif settings_tab == "About":
        st.markdown("<h3 class='sub-header'>About</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='card'>
            <h4>LinkedIn Lead Scraper</h4>
            <p>Version 1.0.0</p>
            <p>This application helps you find and manage quality leads from LinkedIn.</p>
            <p>Built with Streamlit and Python.</p>
            <p>© 2025 LinkedIn Lead Scraper</p>
        </div>
        """, unsafe_allow_html=True)

# Main app logic
def main():
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
