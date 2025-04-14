# LinkedIn Lead Scraper - Documentation

## Overview

LinkedIn Lead Scraper is a powerful application that helps you find and manage quality leads from LinkedIn. The application allows you to search for professionals based on keywords and location, manage your leads, create custom filters, and analyze your lead data with interactive visualizations.

## Features

- **LinkedIn Search**: Search for professionals on LinkedIn based on keywords and location
- **Lead Management**: View, filter, and manage your leads with qualification tracking
- **Custom Filters**: Create and save custom filters to quickly find relevant leads
- **Data Analytics**: Visualize your lead data with interactive charts and statistics
- **Data Export**: Export your leads in CSV, Excel, or JSON formats
- **Profile Details**: View detailed information about each lead's profile
- **Modern UI**: Clean, responsive interface that works on desktop and mobile devices

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Dependencies

The application requires the following Python packages:

```
streamlit
pandas
selenium
webdriver-manager
beautifulsoup4
requests-html
openpyxl
plotly
```

### Installation Steps

1. Clone the repository or download the source code
2. Navigate to the project directory
3. Install the required dependencies:

```bash
pip install streamlit pandas selenium webdriver-manager beautifulsoup4 requests-html openpyxl plotly
```

## Usage

### Starting the Application

To start the application, navigate to the project directory and run:

```bash
streamlit run app.py
```

This will start the application and open it in your default web browser. If it doesn't open automatically, you can access it at `http://localhost:8501`.

### Login

The application includes a simple login system for demonstration purposes. Use the following credentials:

- Username: `demo`
- Password: `demo123`

In a production environment, you would implement a more secure authentication system.

### Navigation

The application has a horizontal navigation bar at the top with the following sections:

1. **Dashboard**: Overview of your leads and recent activity
2. **Search LinkedIn**: Search for professionals on LinkedIn
3. **Manage Leads**: View, filter, and manage your leads
4. **Create Filters**: Create and save custom filters
5. **Analytics**: Visualize your lead data with interactive charts
6. **Settings**: Configure application settings

### Searching for Leads

1. Navigate to the "Search LinkedIn" page
2. Enter your search keywords (e.g., "software engineer python")
3. Enter a location (e.g., "San Francisco")
4. Select the number of pages to scrape
5. Click "Start Search"

The application will search LinkedIn and display the results. You can then export the results in various formats.

### Managing Leads

1. Navigate to the "Manage Leads" page
2. Use the filter options to find specific leads
3. View leads in either card view or table view
4. Click on a lead to view detailed profile information
5. Mark leads as qualified or unqualified
6. Add notes to leads for future reference
7. Export filtered leads in various formats

### Creating Filters

1. Navigate to the "Create Filters" page
2. Enter a name for your filter
3. Configure filter criteria (job titles, companies, industries, etc.)
4. Click "Create Filter"

You can then apply your saved filters to quickly find relevant leads.

### Analytics

1. Navigate to the "Analytics" page
2. View key metrics about your leads
3. Explore different analytics views (Overview, Companies, Job Titles, etc.)
4. Export analytics reports for sharing or record-keeping

### Settings

1. Navigate to the "Settings" page
2. Configure LinkedIn credentials (for real scraping)
3. Set data storage preferences
4. Manage application settings
5. Perform data management tasks

## LinkedIn Scraping

### Important Note

The application includes two modes for LinkedIn data:

1. **Mock Data Mode**: Uses generated data for demonstration purposes (default)
2. **Real Scraping Mode**: Uses actual LinkedIn data (requires LinkedIn credentials)

**Warning**: Scraping LinkedIn may violate their Terms of Service. Use real scraping at your own risk and consider using LinkedIn's official API where possible.

### Configuring Real Scraping

To use real LinkedIn data:

1. Navigate to the "Settings" page
2. Enter your LinkedIn email and password
3. Check the "Enable real LinkedIn scraping" option
4. Click "Save LinkedIn Settings"

## Data Storage

The application supports two types of data storage:

1. **File Storage**: Stores data in CSV and JSON files (default)
2. **Database Storage**: Stores data in an SQLite database

To change the storage type:

1. Navigate to the "Settings" page
2. Select your preferred storage type
3. Configure storage settings
4. Click "Save Storage Settings"

## Customization

### Theme

The application supports both light and dark themes. To change the theme:

1. Use the theme selector in the sidebar
2. Select "Light" or "Dark"

### Application Settings

You can customize various application settings:

1. Navigate to the "Settings" page
2. Adjust default page limit, auto-qualification settings, etc.
3. Click "Save Application Settings"

## Troubleshooting

### Common Issues

1. **Application won't start**: Ensure all dependencies are installed correctly
2. **LinkedIn login fails**: Check your credentials and network connection
3. **No search results**: Try different keywords or locations
4. **Data not saving**: Check storage settings and permissions

### Error Logging

The application includes comprehensive error logging. If you encounter issues:

1. Check the console output for error messages
2. Review the application logs for detailed information

## Development

### Project Structure

- `app.py`: Main application file
- `linkedin_scraper.py`: LinkedIn scraping functionality
- `data_manager.py`: Data processing and storage
- `styles.css`: Custom CSS styles

### Extending the Application

To add new features or modify existing ones:

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/)
- Uses [Selenium](https://selenium-python.readthedocs.io/) for web automation
- Uses [Plotly](https://plotly.com/python/) for data visualization
