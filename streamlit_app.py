import streamlit as st
import pandas as pd
import json
from datetime import datetime
from scraper import (
    fetch_html_selenium,
    save_raw_data,
    html_to_markdown_with_readability,
    setup_selenium,
    generate_unique_folder_name
)
from pagination_detector import detect_pagination_elements
from urllib.parse import urlparse
from assets import PRICING
import os

# Initialize Streamlit app
st.set_page_config(page_title="Web Scraper By Adarsh", page_icon="😎", layout="wide")
st.title("Web Scraper By Adarsh 😎")

# Initialize session state variables
if 'scraping_state' not in st.session_state:
    st.session_state['scraping_state'] = 'idle'  # Possible states: 'idle', 'waiting', 'scraping', 'completed'
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'driver' not in st.session_state:
    st.session_state['driver'] = None

# Sidebar components
st.sidebar.title("Web Scraper Settings")

# API Keys
with st.sidebar.expander("API Keys", expanded=False):
    st.session_state['openai_api_key'] = st.text_input("OpenAI API Key", type="password")
    st.session_state['gemini_api_key'] = st.text_input("Gemini API Key", type="password")
    st.session_state['groq_api_key'] = st.text_input("Groq API Key", type="password")

# Model selection
model_selection = st.sidebar.selectbox("Select Model", options=list(PRICING.keys()), index=0)

# URL input
url_input = st.sidebar.text_input("Enter URL(s) separated by whitespace")
# Process URLs
urls = url_input.strip().split()
num_urls = len(urls)

# Main action button
if st.sidebar.button("LAUNCH SCRAPER", type="primary"):
    if url_input.strip() == "":
        st.error("Please enter at least one URL.")
    else:
        # Set up scraping parameters in session state
        st.session_state['urls'] = url_input.strip().split()
        st.session_state['model_selection'] = model_selection
        # Always enable pagination (no toggle needed)
        st.session_state['use_pagination'] = True
        st.session_state['pagination_details'] = ""  # No input needed for pagination details
        st.session_state['scraping_state'] = 'scraping'

# Scraping logic
if st.session_state['scraping_state'] == 'scraping':
    with st.spinner('Scraping in progress...'):
        # Perform scraping
        output_folder = os.path.join('output', generate_unique_folder_name(st.session_state['urls'][0]))
        os.makedirs(output_folder, exist_ok=True)

        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0
        all_data = []
        pagination_info_all_urls = {}

        # Scrape for each URL separately
        for i, url in enumerate(st.session_state['urls'], start=1):
            # Fetch HTML
            raw_html = fetch_html_selenium(url, attended_mode=False)
            markdown = html_to_markdown_with_readability(raw_html)
            save_raw_data(markdown, output_folder, f'rawData_{i}.md')

            # Detect pagination (always enabled)
            if st.session_state['use_pagination']:
                pagination_data, token_counts, pagination_price = detect_pagination_elements(
                    url, st.session_state['pagination_details'], st.session_state['model_selection'], markdown
                )
                page_urls = pagination_data.get("page_urls", []) if isinstance(pagination_data, dict) else pagination_data.page_urls
                
                # Store pagination data for each URL
                pagination_info_all_urls[url] = {
                    "page_urls": page_urls,
                    "token_counts": token_counts,
                    "price": pagination_price
                }

        # Clean up driver if used
        if st.session_state.get('driver'):
            st.session_state['driver'] = None

    # Display pagination URLs for each URL
    if pagination_info_all_urls:
        for url, pagination_info in pagination_info_all_urls.items():
            st.write(f"### Pagination URLs Detected for URL: {url}")
            pagination_urls_array = [f'"{page_url}"' for page_url in pagination_info['page_urls']]
            pagination_urls_string = f"PRODUCT_URLS = [{', '.join(pagination_urls_array)}]"
            st.write(pagination_urls_string)