import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import json
from datetime import datetime
import random
from linkedin_scraper import LinkedInScraper
from data_manager import DataManager

# Set page configuration
st.set_page_config(
    page_title="LinkedIn Lead Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"
if "leads_df" not in st.session_state:
    st.session_state.leads_df = pd.DataFrame()
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "filters" not in st.session_state:
    st.session_state.filters = []
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "card"
if "linkedin_email" not in st.session_state:
    st.session_state.linkedin_email = ""
if "linkedin_password" not in st.session_state:
    st.session_state.linkedin_password = ""
if "use_real_scraping" not in st.session_state:
    st.session_state.use_real_scraping = False
if "headless_mode" not in st.session_state:
    st.session_state.headless_mode = True
if "use_undetected" not in st.session_state:
    st.session_state.use_undetected = True
if "storage_type" not in st.session_state:
    st.session_state.storage_type = "file"
if "db_path" not in st.session_state:
    st.session_state.db_path = "linkedin_leads.db"
if "data_dir" not in st.session_state:
    st.session_state.data_dir = "data"

# Initialize data manager
data_manager = DataManager(
    storage_type=st.session_state.storage_type,
    db_path=st.session_state.db_path,
    data_dir=st.session_state.data_dir
)

# Load data if available
if st.session_state.logged_in:
    if st.session_state.leads_df.empty:
        st.session_state.leads_df = data_manager.load_leads()
    if not st.session_state.search_history:
        st.session_state.search_history = data_manager.load_search_history()
    if not st.session_state.filters:
        st.session_state.filters = data_manager.load_filters()

# Login page
def show_login():
    st.markdown("<h1 class='linkedin-title'>LinkedIn Lead Scraper</h1>", unsafe_allow_html=True)
    st.markdown("<p class='linkedin-subtitle'>Find and manage quality leads from LinkedIn</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", key="login_button"):
            if username == "demo" and password == "demo123":
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("<p class='login-hint'>Use demo/demo123 for demonstration</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Main navigation
def show_navigation():
    st.markdown("<div class='navigation'>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("Dashboard", key="nav_dashboard"):
            st.session_state.current_page = "dashboard"
            st.experimental_rerun()
    
    with col2:
        if st.button("Search LinkedIn", key="nav_search"):
            st.session_state.current_page = "search"
            st.experimental_rerun()
    
    with col3:
        if st.button("Manage Leads", key="nav_leads"):
            st.session_state.current_page = "leads"
            st.experimental_rerun()
    
    with col4:
        if st.button("Create Filters", key="nav_filters"):
            st.session_state.current_page = "filters"
            st.experimental_rerun()
    
    with col5:
        if st.button("Analytics", key="nav_analytics"):
            st.session_state.current_page = "analytics"
            st.experimental_rerun()
    
    with col6:
        if st.button("Settings", key="nav_settings"):
            st.session_state.current_page = "settings"
            st.experimental_rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Sidebar
def show_sidebar():
    with st.sidebar:
        st.markdown("<h3>LinkedIn Lead Scraper</h3>", unsafe_allow_html=True)
        
        # Theme selector
        theme = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "light" else 1)
        if theme == "Light" and st.session_state.theme != "light":
            st.session_state.theme = "light"
            st.experimental_rerun()
        elif theme == "Dark" and st.session_state.theme != "dark":
            st.session_state.theme = "dark"
            st.experimental_rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Quick actions
        st.markdown("<h4>Quick Actions</h4>", unsafe_allow_html=True)
        
        if st.button("New Search", key="sidebar_search"):
            st.session_state.current_page = "search"
            st.experimental_rerun()
        
        if st.button("Export Leads", key="sidebar_export"):
            if st.session_state.leads_df.empty:
                st.warning("No leads to export")
            else:
                export_path = data_manager.export_leads(st.session_state.leads_df, format="csv")
                if export_path:
                    st.success(f"Leads exported to {export_path}")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Stats
        st.markdown("<h4>Lead Statistics</h4>", unsafe_allow_html=True)
        
        if not st.session_state.leads_df.empty:
            total_leads = len(st.session_state.leads_df)
            qualified_leads = len(st.session_state.leads_df[st.session_state.leads_df['is_qualified'] == True])
            
            st.markdown(f"<p>Total Leads: <strong>{total_leads}</strong></p>", unsafe_allow_html=True)
            st.markdown(f"<p>Qualified Leads: <strong>{qualified_leads}</strong></p>", unsafe_allow_html=True)
            
            if total_leads > 0:
                qualification_rate = round((qualified_leads / total_leads) * 100, 2)
                st.markdown(f"<p>Qualification Rate: <strong>{qualification_rate}%</strong></p>", unsafe_allow_html=True)
        else:
            st.markdown("<p>No leads available</p>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Logout
        if st.button("Logout", key="sidebar_logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

# Dashboard page
def show_dashboard():
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    
    # Overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Total Leads</h3>", unsafe_allow_html=True)
        total_leads = len(st.session_state.leads_df) if not st.session_state.leads_df.empty else 0
        st.markdown(f"<p class='dashboard-number'>{total_leads}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Qualified Leads</h3>", unsafe_allow_html=True)
        qualified_leads = len(st.session_state.leads_df[st.session_state.leads_df['is_qualified'] == True]) if not st.session_state.leads_df.empty else 0
        st.markdown(f"<p class='dashboard-number'>{qualified_leads}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Qualification Rate</h3>", unsafe_allow_html=True)
        if not st.session_state.leads_df.empty and len(st.session_state.leads_df) > 0:
            qualification_rate = round((qualified_leads / total_leads) * 100, 2)
            st.markdown(f"<p class='dashboard-number'>{qualification_rate}%</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='dashboard-number'>0%</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Recent Searches</h3>", unsafe_allow_html=True)
        recent_searches = len(st.session_state.search_history) if st.session_state.search_history else 0
        st.markdown(f"<p class='dashboard-number'>{recent_searches}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity and charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h2>Recent Activity</h2>", unsafe_allow_html=True)
        
        if st.session_state.search_history:
            st.markdown("<div class='activity-container'>", unsafe_allow_html=True)
            for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
                st.markdown(f"<div class='activity-item'>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Search:</strong> {search['keywords']} in {search['location']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Date:</strong> {search['date']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Results:</strong> {search['results']} leads</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p>No recent activity</p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h2>Lead Distribution</h2>", unsafe_allow_html=True)
        
        if not st.session_state.leads_df.empty:
            # Create a pie chart for qualified vs unqualified leads
            qualified_count = len(st.session_state.leads_df[st.session_state.leads_df['is_qualified'] == True])
            unqualified_count = len(st.session_state.leads_df[st.session_state.leads_df['is_qualified'] == False])
            
            fig = px.pie(
                values=[qualified_count, unqualified_count],
                names=['Qualified', 'Unqualified'],
                color=['#0077B5', '#ccc'],
                color_discrete_map="identity"
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<p>No data available for visualization</p>", unsafe_allow_html=True)
    
    # Recent leads
    st.markdown("<h2>Recent Leads</h2>", unsafe_allow_html=True)
    
    if not st.session_state.leads_df.empty:
        # Display the 5 most recent leads
        recent_leads = st.session_state.leads_df.head(5)
        
        st.markdown("<div class='leads-container'>", unsafe_allow_html=True)
        cols = st.columns(5)
        
        for i, (_, lead) in enumerate(recent_leads.iterrows()):
            with cols[i]:
                st.markdown("<div class='lead-card'>", unsafe_allow_html=True)
                st.markdown(f"<h3>{lead['name']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>{lead['title']}</strong></p>", unsafe_allow_html=True)
                st.markdown(f"<p>{lead['company']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>{lead['location']}</p>", unsafe_allow_html=True)
                
                if lead['is_qualified']:
                    st.markdown("<span class='badge qualified'>Qualified</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge unqualified'>Unqualified</span>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p>No leads available</p>", unsafe_allow_html=True)

# Search page
def show_search():
    st.markdown("<h1>Search LinkedIn</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='search-container'>", unsafe_allow_html=True)
        
        with st.form("search_form"):
            st.markdown("<h3>Search Parameters</h3>", unsafe_allow_html=True)
            
            keywords = st.text_input("Keywords (e.g., job title, skills)")
            location = st.text_input("Location")
            page_limit = st.slider("Number of pages to scrape", 1, 10, 3)
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button("Start Search")
            
            with col2:
                reset_button = st.form_submit_button("Reset")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if submit_button and keywords and location:
            with st.spinner("Searching LinkedIn..."):
                # Initialize LinkedIn scraper
                if st.session_state.use_real_scraping:
                    scraper = LinkedInScraper(
                        headless=st.session_state.headless_mode,
                        use_undetected=st.session_state.use_undetected
                    )
                    
                    # Login to LinkedIn
                    login_success = scraper.login(
                        st.session_state.linkedin_email,
                        st.session_state.linkedin_password
                    )
                    
                    if login_success:
                        # Search LinkedIn
                        results_df = scraper.search_linkedin(keywords, location, page_limit)
                        scraper.close()
                    else:
                        st.error("Failed to log in to LinkedIn. Please check your credentials.")
                        results_df = pd.DataFrame()
                else:
                    # Use mock data
                    from linkedin_scraper import mock_linkedin_search
                    results_df = mock_linkedin_search(keywords, location, page_limit)
                
                # Clean data
                results_df = data_manager.clean_data(results_df)
                
                # Update session state
                if not results_df.empty:
                    # Append new results to existing leads
                    if not st.session_state.leads_df.empty:
                        combined_df = pd.concat([st.session_state.leads_df, results_df])
                        st.session_state.leads_df = combined_df.drop_duplicates(subset=['profile_url'], keep='first').reset_index(drop=True)
                    else:
                        st.session_state.leads_df = results_df
                    
                    # Save leads
                    data_manager.save_leads(st.session_state.leads_df)
                    
                    # Update search history
                    search_entry = {
                        "keywords": keywords,
                        "location": location,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "results": len(results_df)
                    }
                    st.session_state.search_history.append(search_entry)
                    data_manager.save_search_history(st.session_state.search_history)
                    
                    st.success(f"Found {len(results_df)} leads matching your criteria")
                else:
                    st.error("No leads found. Please try different search criteria or check your LinkedIn credentials.")
    
    with col2:
        st.markdown("<div class='tips-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Search Tips</h3>", unsafe_allow_html=True)
        
        st.markdown("<ul>", unsafe_allow_html=True)
        st.markdown("<li>Use specific job titles for better results</li>", unsafe_allow_html=True)
        st.markdown("<li>Include skills or qualifications in keywords</li>", unsafe_allow_html=True)
        st.markdown("<li>Specify location for targeted results</li>", unsafe_allow_html=True)
        st.markdown("<li>Increase page limit for more results</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
        
        st.markdown("<h3>Example Searches</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='example-search'>", unsafe_allow_html=True)
        st.markdown("<p><strong>Keywords:</strong> Software Engineer Python</p>", unsafe_allow_html=True)
        st.markdown("<p><strong>Location:</strong> San Francisco</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='example-search'>", unsafe_allow_html=True)
        st.markdown("<p><strong>Keywords:</strong> Marketing Manager B2B</p>", unsafe_allow_html=True)
        st.markdown("<p><strong>Location:</strong> New York</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='example-search'>", unsafe_allow_html=True)
        st.markdown("<p><strong>Keywords:</strong> Sales Director SaaS</p>", unsafe_allow_html=True)
        st.markdown("<p><strong>Location:</strong> London</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Search results
    if not st.session_state.leads_df.empty:
        st.markdown("<h2>Search Results</h2>", unsafe_allow_html=True)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export as CSV"):
                export_path = data_manager.export_leads(st.session_state.leads_df, format="csv")
                if export_path:
                    st.success(f"Leads exported to {export_path}")
        
        with col2:
            if st.button("Export as Excel"):
                export_path = data_manager.export_leads(st.session_state.leads_df, format="excel")
                if export_path:
                    st.success(f"Leads exported to {export_path}")
        
        with col3:
            if st.button("Export as JSON"):
                export_path = data_manager.export_leads(st.session_state.leads_df, format="json")
                if export_path:
                    st.success(f"Leads exported to {export_path}")
        
        # Display results
        st.dataframe(st.session_state.leads_df)

# Leads page
def show_leads():
    st.markdown("<h1>Manage Leads</h1>", unsafe_allow_html=True)
    
    if st.session_state.leads_df.empty:
        st.markdown("<p>No leads available. Use the Search page to find leads.</p>", unsafe_allow_html=True)
        return
    
    # Filters
    st.markdown("<h3>Filter Leads</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        name_filter = st.text_input("Name", key="name_filter")
    
    with col2:
        title_filter = st.text_input("Job Title", key="title_filter")
    
    with col3:
        company_filter = st.text_input("Company", key="company_filter")
    
    with col4:
        location_filter = st.text_input("Location", key="location_filter")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        industry_filter = st.text_input("Industry", key="industry_filter")
    
    with col2:
        company_size_filter = st.text_input("Company Size", key="company_size_filter")
    
    with col3:
        connections_filter = st.text_input("Connections", key="connections_filter")
    
    with col4:
        qualified_filter = st.selectbox("Qualification", ["All", "Qualified", "Unqualified"], key="qualified_filter")
    
    # Apply filters
    filtered_df = st.session_state.leads_df.copy()
    
    if name_filter:
        filtered_df = filtered_df[filtered_df['name'].str.contains(name_filter, case=False)]
    
    if title_filter:
        filtered_df = filtered_df[filtered_df['title'].str.contains(title_filter, case=False)]
    
    if company_filter:
        filtered_df = filtered_df[filtered_df['company'].str.contains(company_filter, case=False)]
    
    if location_filter:
        filtered_df = filtered_df[filtered_df['location'].str.contains(location_filter, case=False)]
    
    if industry_filter:
        filtered_df = filtered_df[filtered_df['industry'].str.contains(industry_filter, case=False)]
    
    if company_size_filter:
        filtered_df = filtered_df[filtered_df['company_size'].str.contains(company_size_filter, case=False)]
    
    if connections_filter:
        filtered_df = filtered_df[filtered_df['connections'].str.contains(connections_filter, case=False)]
    
    if qualified_filter == "Qualified":
        filtered_df = filtered_df[filtered_df['is_qualified'] == True]
    elif qualified_filter == "Unqualified":
        filtered_df = filtered_df[filtered_df['is_qualified'] == False]
    
    # View options
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        view_mode = st.radio("View Mode", ["Card View", "Table View"], index=0 if st.session_state.view_mode == "card" else 1)
        if view_mode == "Card View" and st.session_state.view_mode != "card":
            st.session_state.view_mode = "card"
        elif view_mode == "Table View" and st.session_state.view_mode != "table":
            st.session_state.view_mode = "table"
    
    with col2:
        sort_by = st.selectbox("Sort By", ["Name", "Title", "Company", "Location", "Qualification"])
    
    with col3:
        st.markdown(f"<p class='filter-count'>{len(filtered_df)} leads found</p>", unsafe_allow_html=True)
    
    # Sort the filtered DataFrame
    if sort_by == "Name":
        filtered_df = filtered_df.sort_values(by="name")
    elif sort_by == "Title":
        filtered_df = filtered_df.sort_values(by="title")
    elif sort_by == "Company":
        filtered_df = filtered_df.sort_values(by="company")
    elif sort_by == "Location":
        filtered_df = filtered_df.sort_values(by="location")
    elif sort_by == "Qualification":
        filtered_df = filtered_df.sort_values(by="is_qualified", ascending=False)
    
    # Display leads
    if st.session_state.view_mode == "card":
        # Card view
        st.markdown("<div class='leads-grid'>", unsafe_allow_html=True)
        
        # Create rows with 3 cards each
        for i in range(0, len(filtered_df), 3):
            cols = st.columns(3)
            
            for j in range(3):
                if i + j < len(filtered_df):
                    lead = filtered_df.iloc[i + j]
                    
                    with cols[j]:
                        st.markdown("<div class='lead-card'>", unsafe_allow_html=True)
                        st.markdown(f"<h3>{lead['name']}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p><strong>{lead['title']}</strong></p>", unsafe_allow_html=True)
                        st.markdown(f"<p>{lead['company']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p>{lead['location']}</p>", unsafe_allow_html=True)
                        
                        if lead['is_qualified']:
                            st.markdown("<span class='badge qualified'>Qualified</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span class='badge unqualified'>Unqualified</span>", unsafe_allow_html=True)
                        
                        # Actions
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("View Profile", key=f"view_{i+j}"):
                                st.markdown(f"<p><strong>Profile URL:</strong> <a href='{lead['profile_url']}' target='_blank'>{lead['profile_url']}</a></p>", unsafe_allow_html=True)
                        
                        with col2:
                            if lead['is_qualified']:
                                if st.button("Unqualify", key=f"unqualify_{i+j}"):
                                    st.session_state.leads_df.loc[st.session_state.leads_df['profile_url'] == lead['profile_url'], 'is_qualified'] = False
                                    data_manager.save_leads(st.session_state.leads_df)
                                    st.experimental_rerun()
                            else:
                                if st.button("Qualify", key=f"qualify_{i+j}"):
                                    st.session_state.leads_df.loc[st.session_state.leads_df['profile_url'] == lead['profile_url'], 'is_qualified'] = True
                                    data_manager.save_leads(st.session_state.leads_df)
                                    st.experimental_rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Table view
        st.dataframe(filtered_df)
        
        # Lead details
        st.markdown("<h3>Lead Details</h3>", unsafe_allow_html=True)
        
        selected_lead = st.selectbox("Select a lead to view details", filtered_df['name'].tolist())
        
        if selected_lead:
            lead = filtered_df[filtered_df['name'] == selected_lead].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='lead-details'>", unsafe_allow_html=True)
                st.markdown(f"<h3>{lead['name']}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Title:</strong> {lead['title']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Company:</strong> {lead['company']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Location:</strong> {lead['location']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Industry:</strong> {lead['industry']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Company Size:</strong> {lead['company_size']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Connections:</strong> {lead['connections']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p><strong>Profile URL:</strong> <a href='{lead['profile_url']}' target='_blank'>{lead['profile_url']}</a></p>", unsafe_allow_html=True)
                
                if lead['is_qualified']:
                    st.markdown("<span class='badge qualified'>Qualified</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge unqualified'>Unqualified</span>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                # Actions
                if lead['is_qualified']:
                    if st.button("Mark as Unqualified"):
                        st.session_state.leads_df.loc[st.session_state.leads_df['profile_url'] == lead['profile_url'], 'is_qualified'] = False
                        data_manager.save_leads(st.session_state.leads_df)
                        st.experimental_rerun()
                else:
                    if st.button("Mark as Qualified"):
                        st.session_state.leads_df.loc[st.session_state.leads_df['profile_url'] == lead['profile_url'], 'is_qualified'] = True
                        data_manager.save_leads(st.session_state.leads_df)
                        st.experimental_rerun()
                
                # Notes
                notes = st.text_area("Notes", value=lead.get('notes', ''))
                
                if st.button("Save Notes"):
                    st.session_state.leads_df.loc[st.session_state.leads_df['profile_url'] == lead['profile_url'], 'notes'] = notes
                    data_manager.save_leads(st.session_state.leads_df)
                    st.success("Notes saved successfully")

# Filters page
def show_filters():
    st.markdown("<h1>Create Filters</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
        
        with st.form("filter_form"):
            st.markdown("<h3>Create New Filter</h3>", unsafe_allow_html=True)
            
            filter_name = st.text_input("Filter Name")
            
            st.markdown("<h4>Filter Criteria</h4>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                job_titles = st.text_area("Job Titles (one per line)")
                companies = st.text_area("Companies (one per line)")
            
            with col2:
                industries = st.text_area("Industries (one per line)")
                locations = st.text_area("Locations (one per line)")
            
            include_qualified = st.checkbox("Include Qualified Leads", value=True)
            include_unqualified = st.checkbox("Include Unqualified Leads", value=True)
            
            submit_button = st.form_submit_button("Create Filter")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if submit_button and filter_name:
            # Create filter
            filter_data = {
                "name": filter_name,
                "job_titles": [title.strip() for title in job_titles.split("\n") if title.strip()],
                "companies": [company.strip() for company in companies.split("\n") if company.strip()],
                "industries": [industry.strip() for industry in industries.split("\n") if industry.strip()],
                "locations": [location.strip() for location in locations.split("\n") if location.strip()],
                "include_qualified": include_qualified,
                "include_unqualified": include_unqualified
            }
            
            # Add to filters
            st.session_state.filters.append(filter_data)
            
            # Save filters
            data_manager.save_filters(st.session_state.filters)
            
            st.success(f"Filter '{filter_name}' created successfully")
    
    with col2:
        st.markdown("<div class='saved-filters'>", unsafe_allow_html=True)
        st.markdown("<h3>Saved Filters</h3>", unsafe_allow_html=True)
        
        if st.session_state.filters:
            for i, filter_data in enumerate(st.session_state.filters):
                st.markdown("<div class='filter-item'>", unsafe_allow_html=True)
                st.markdown(f"<h4>{filter_data['name']}</h4>", unsafe_allow_html=True)
                
                if st.button("Apply Filter", key=f"apply_{i}"):
                    # Apply the filter to leads
                    filtered_df = st.session_state.leads_df.copy()
                    
                    if filter_data['job_titles']:
                        title_mask = filtered_df['title'].apply(lambda x: any(title.lower() in x.lower() for title in filter_data['job_titles']))
                        filtered_df = filtered_df[title_mask]
                    
                    if filter_data['companies']:
                        company_mask = filtered_df['company'].apply(lambda x: any(company.lower() in x.lower() for company in filter_data['companies']))
                        filtered_df = filtered_df[company_mask]
                    
                    if filter_data['industries']:
                        industry_mask = filtered_df['industry'].apply(lambda x: any(industry.lower() in x.lower() for industry in filter_data['industries']))
                        filtered_df = filtered_df[industry_mask]
                    
                    if filter_data['locations']:
                        location_mask = filtered_df['location'].apply(lambda x: any(location.lower() in x.lower() for location in filter_data['locations']))
                        filtered_df = filtered_df[location_mask]
                    
                    qualification_mask = (filtered_df['is_qualified'] == True) if filter_data['include_qualified'] and not filter_data['include_unqualified'] else \
                                        (filtered_df['is_qualified'] == False) if not filter_data['include_qualified'] and filter_data['include_unqualified'] else \
                                        pd.Series([True] * len(filtered_df))
                    
                    filtered_df = filtered_df[qualification_mask]
                    
                    # Display results
                    st.session_state.filtered_leads = filtered_df
                    st.success(f"Filter applied: {len(filtered_df)} leads found")
                    
                    # Switch to leads page
                    st.session_state.current_page = "leads"
                    st.experimental_rerun()
                
                if st.button("Delete Filter", key=f"delete_{i}"):
                    # Remove filter
                    st.session_state.filters.pop(i)
                    
                    # Save filters
                    data_manager.save_filters(st.session_state.filters)
                    
                    st.success("Filter deleted successfully")
                    st.experimental_rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p>No saved filters</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Filter results
    if hasattr(st.session_state, 'filtered_leads') and not st.session_state.filtered_leads.empty:
        st.markdown("<h2>Filter Results</h2>", unsafe_allow_html=True)
        st.dataframe(st.session_state.filtered_leads)

# Analytics page
def show_analytics():
    st.markdown("<h1>Analytics</h1>", unsafe_allow_html=True)
    
    if st.session_state.leads_df.empty:
        st.markdown("<p>No leads available for analytics. Use the Search page to find leads.</p>", unsafe_allow_html=True)
        return
    
    # Get lead statistics
    stats = data_manager.get_lead_statistics(st.session_state.leads_df)
    
    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Companies", "Job Titles", "Locations"])
    
    with tab1:
        # Overview
        st.markdown("<h2>Overview</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("<div class='analytics-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Total Leads</h3>", unsafe_allow_html=True)
            st.markdown(f"<p class='analytics-number'>{stats['total_leads']}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='analytics-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Qualified Leads</h3>", unsafe_allow_html=True)
            st.markdown(f"<p class='analytics-number'>{stats['qualified_leads']}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='analytics-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Qualification Rate</h3>", unsafe_allow_html=True)
            st.markdown(f"<p class='analytics-number'>{stats['qualification_rate']}%</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Qualification chart
        st.markdown("<h3>Lead Qualification</h3>", unsafe_allow_html=True)
        
        fig = px.pie(
            values=[stats['qualified_leads'], stats['total_leads'] - stats['qualified_leads']],
            names=['Qualified', 'Unqualified'],
            color=['#0077B5', '#ccc'],
            color_discrete_map="identity"
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Connections distribution
        st.markdown("<h3>Connections Distribution</h3>", unsafe_allow_html=True)
        
        connections_df = pd.DataFrame({
            'Connections': list(stats['connections_distribution'].keys()),
            'Count': list(stats['connections_distribution'].values())
        })
        
        fig = px.bar(
            connections_df,
            x='Connections',
            y='Count',
            color_discrete_sequence=['#0077B5']
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Companies
        st.markdown("<h2>Companies</h2>", unsafe_allow_html=True)
        
        # Top companies chart
        st.markdown("<h3>Top Companies</h3>", unsafe_allow_html=True)
        
        companies_df = pd.DataFrame({
            'Company': list(stats['top_companies'].keys()),
            'Count': list(stats['top_companies'].values())
        })
        
        fig = px.bar(
            companies_df,
            x='Company',
            y='Count',
            color_discrete_sequence=['#0077B5']
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Company data
        st.markdown("<h3>Company Data</h3>", unsafe_allow_html=True)
        
        company_counts = st.session_state.leads_df['company'].value_counts().reset_index()
        company_counts.columns = ['Company', 'Count']
        
        st.dataframe(company_counts)
    
    with tab3:
        # Job Titles
        st.markdown("<h2>Job Titles</h2>", unsafe_allow_html=True)
        
        # Top job titles chart
        st.markdown("<h3>Top Job Titles</h3>", unsafe_allow_html=True)
        
        titles_df = pd.DataFrame({
            'Title': list(stats['top_titles'].keys()),
            'Count': list(stats['top_titles'].values())
        })
        
        fig = px.bar(
            titles_df,
            x='Title',
            y='Count',
            color_discrete_sequence=['#0077B5']
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Job title data
        st.markdown("<h3>Job Title Data</h3>", unsafe_allow_html=True)
        
        title_counts = st.session_state.leads_df['title'].value_counts().reset_index()
        title_counts.columns = ['Title', 'Count']
        
        st.dataframe(title_counts)
    
    with tab4:
        # Locations
        st.markdown("<h2>Locations</h2>", unsafe_allow_html=True)
        
        # Top locations chart
        st.markdown("<h3>Top Locations</h3>", unsafe_allow_html=True)
        
        locations_df = pd.DataFrame({
            'Location': list(stats['top_locations'].keys()),
            'Count': list(stats['top_locations'].values())
        })
        
        fig = px.bar(
            locations_df,
            x='Location',
            y='Count',
            color_discrete_sequence=['#0077B5']
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Location data
        st.markdown("<h3>Location Data</h3>", unsafe_allow_html=True)
        
        location_counts = st.session_state.leads_df['location'].value_counts().reset_index()
        location_counts.columns = ['Location', 'Count']
        
        st.dataframe(location_counts)

# Settings page
def show_settings():
    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["LinkedIn Settings", "Storage Settings", "Application Settings"])
    
    with tab1:
        # LinkedIn settings
        st.markdown("<h2>LinkedIn Settings</h2>", unsafe_allow_html=True)
        
        with st.form("linkedin_settings_form"):
            st.markdown("<p>Enter your LinkedIn credentials to enable real scraping</p>", unsafe_allow_html=True)
            
            linkedin_email = st.text_input("LinkedIn Email", value=st.session_state.linkedin_email)
            linkedin_password = st.text_input("LinkedIn Password", type="password", value=st.session_state.linkedin_password)
            
            use_real_scraping = st.checkbox("Enable real LinkedIn scraping", value=st.session_state.use_real_scraping)
            
            st.markdown("<h3>Advanced Settings</h3>", unsafe_allow_html=True)
            
            headless_mode = st.checkbox("Use headless mode (no visible browser)", value=st.session_state.headless_mode)
            use_undetected = st.checkbox("Use undetected mode (better for avoiding detection)", value=st.session_state.use_undetected)
            
            submit_button = st.form_submit_button("Save LinkedIn Settings")
        
        if submit_button:
            st.session_state.linkedin_email = linkedin_email
            st.session_state.linkedin_password = linkedin_password
            st.session_state.use_real_scraping = use_real_scraping
            st.session_state.headless_mode = headless_mode
            st.session_state.use_undetected = use_undetected
            
            st.success("LinkedIn settings saved successfully")
    
    with tab2:
        # Storage settings
        st.markdown("<h2>Storage Settings</h2>", unsafe_allow_html=True)
        
        with st.form("storage_settings_form"):
            storage_type = st.radio("Storage Type", ["File", "Database"], index=0 if st.session_state.storage_type == "file" else 1)
            
            if storage_type == "File":
                data_dir = st.text_input("Data Directory", value=st.session_state.data_dir)
            else:
                db_path = st.text_input("Database Path", value=st.session_state.db_path)
            
            submit_button = st.form_submit_button("Save Storage Settings")
        
        if submit_button:
            new_storage_type = storage_type.lower()
            
            if new_storage_type != st.session_state.storage_type:
                # Storage type changed, migrate data
                old_data_manager = data_manager
                
                if new_storage_type == "file":
                    new_data_manager = DataManager(storage_type="file", data_dir=data_dir)
                else:
                    new_data_manager = DataManager(storage_type="database", db_path=db_path)
                
                # Load data from old storage
                leads_df = old_data_manager.load_leads()
                search_history = old_data_manager.load_search_history()
                filters = old_data_manager.load_filters()
                
                # Save data to new storage
                if not leads_df.empty:
                    new_data_manager.save_leads(leads_df)
                
                if search_history:
                    new_data_manager.save_search_history(search_history)
                
                if filters:
                    new_data_manager.save_filters(filters)
                
                # Update session state
                st.session_state.storage_type = new_storage_type
                
                if new_storage_type == "file":
                    st.session_state.data_dir = data_dir
                else:
                    st.session_state.db_path = db_path
                
                # Update data manager
                global data_manager
                data_manager = new_data_manager
                
                st.success("Storage settings saved and data migrated successfully")
            else:
                # Only update paths
                if new_storage_type == "file":
                    st.session_state.data_dir = data_dir
                    data_manager.data_dir = data_dir
                else:
                    st.session_state.db_path = db_path
                    data_manager.db_path = db_path
                
                st.success("Storage settings saved successfully")
    
    with tab3:
        # Application settings
        st.markdown("<h2>Application Settings</h2>", unsafe_allow_html=True)
        
        with st.form("app_settings_form"):
            default_page_limit = st.slider("Default Page Limit", 1, 10, 3)
            auto_qualify = st.checkbox("Auto-qualify leads with specific criteria")
            
            if auto_qualify:
                auto_qualify_titles = st.text_area("Auto-qualify job titles (one per line)")
                auto_qualify_companies = st.text_area("Auto-qualify companies (one per line)")
            
            submit_button = st.form_submit_button("Save Application Settings")
        
        if submit_button:
            st.success("Application settings saved successfully")
        
        # Data management
        st.markdown("<h2>Data Management</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All Data"):
                # Export all data
                if not st.session_state.leads_df.empty:
                    export_path = data_manager.export_leads(st.session_state.leads_df, format="excel")
                    if export_path:
                        st.success(f"All data exported to {export_path}")
                else:
                    st.warning("No data to export")
        
        with col2:
            if st.button("Clear All Data"):
                # Confirm clear
                confirm = st.checkbox("I understand this will delete all leads, search history, and filters")
                
                if confirm:
                    # Clear all data
                    st.session_state.leads_df = pd.DataFrame()
                    st.session_state.search_history = []
                    st.session_state.filters = []
                    
                    # Save empty data
                    data_manager.save_leads(st.session_state.leads_df)
                    data_manager.save_search_history(st.session_state.search_history)
                    data_manager.save_filters(st.session_state.filters)
                    
                    st.success("All data cleared successfully")

# Main app
def main():
    # Apply theme
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        :root {
            --background-color: #121212;
            --text-color: #f0f0f0;
            --card-background: #1e1e1e;
            --primary-color: #0077B5;
            --secondary-color: #00a0dc;
            --border-color: #333;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        :root {
            --background-color: #f9f9f9;
            --text-color: #333;
            --card-background: #fff;
            --primary-color: #0077B5;
            --secondary-color: #00a0dc;
            --border-color: #ddd;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Check if logged in
    if not st.session_state.logged_in:
        show_login()
        return
    
    # Show navigation and sidebar
    show_navigation()
    show_sidebar()
    
    # Show current page
    if st.session_state.current_page == "dashboard":
        show_dashboard()
    elif st.session_state.current_page == "search":
        show_search()
    elif st.session_state.current_page == "leads":
        show_leads()
    elif st.session_state.current_page == "filters":
        show_filters()
    elif st.session_state.current_page == "analytics":
        show_analytics()
    elif st.session_state.current_page == "settings":
        show_settings()

if __name__ == "__main__":
    main()
