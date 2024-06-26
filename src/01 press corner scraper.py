'''
A scraper for digital policy speeches from the EU Press Corner (https://ec.europa.eu/commission/presscorner).
'''

# standard library
import os
import csv
import glob
import re
import openpyxl
import time
import math
import pandas as pd
import numpy as np 
from tqdm import tqdm

# web services
import requests 
from functools import reduce
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
from urllib.parse import urljoin
from striprtf.striprtf import rtf_to_text


def input_link():
     '''Function for user to input link to be scraped.'''
     input_link = str(input("Enter search link: \n"))
     return input_link

def load_page(input_link): 
    '''Function for loading html components of webpage.'''

    options = webdriver.ChromeOptions()
    #options.add_argument('--headless') 
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    driver.get(input_link)
    time.sleep(5) 
    scroll_pause_time = 5
    screen_height = driver.execute_script("return window.screen.height;")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup

def num_pages(soup):
    '''Function returning the number of search results pages to be scraped.
    In the EU Press Corner website, there are 10 unique search results per page.'''
    
    header = soup.find_all(class_="ecl-heading ecl-heading--h2 ecl-u-mb-m")[0]
    span = header.find('span')
    num_pages = span.text
    num_pages = math.ceil(int(re.sub(r'[()]', '', num_pages)) / 10)
    print(f"Number of pages: {num_pages}")
    return num_pages

def paged_results(page_range, input_link):
    '''Function returning the url of each page result.'''
    
    pages = []
    for i in page_range: 
        page = input_link + "&pagenumber=" + str(i)
        pages.append(page)
    return pages

def page_urls(input_link):
    '''Function returning the url of each search result.'''

    urls = []    
    soup = load_page(input_link)

    for parent in soup.find_all(class_="ecl-link ecl-list-item__link"):
        base = "https://ec.europa.eu/commission/presscorner/"
        link = parent.attrs['href']
        url = urljoin(base, link)
        urls.append(url)   
    return urls

def set_urls(links):
    '''Function returning a list of search result urls.'''

    url_set = []
    total_links = len(links)

    with tqdm(total=total_links, desc="Processing pages") as pbar:
        for link in links:
            set = page_urls(link)
            url_set.extend(set)
            pbar.update(1)
    return url_set

def extract_text(links):
    '''Function for extracting information from each search result.'''

    print(f"Number of links: {len(links)}")

    with tqdm(total=len(links), desc="Extracting text") as pbar:
        with open('raw.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["document", "title", "date", "location", "text", "link"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            for link in links:
                soup = load_page(link)
                title_elem = doc_elems = paragraph_elem = None

                try:
                    title_elem = soup.find(class_="ecl-heading ecl-heading--h1 ecl-u-color-white")
                    doc_elems = soup.find_all(class_="ecl-meta__item")
                    paragraph_elem = soup.find(class_="ecl-paragraph")

                except Exception as e:
                    print(f"Error on link {link}: {e}")

                title = title_elem.text if title_elem else np.nan
                paragraph = paragraph_elem.text if paragraph_elem else np.nan

                if doc_elems:
                    doc, date, loc = (elem.text if elem else np.nan for elem in doc_elems[:3])
                else:
                    doc, date, loc = np.nan, np.nan, np.nan

                writer.writerow({
                    "document": doc,
                    "title": title,
                    "date": date,
                    "location": loc,
                    "text": paragraph,
                    "link": str(link)
                })

                pbar.update(1)


# RUN 
link = input_link()
soup = load_page(link)
num_pages = num_pages(soup)

pages = paged_results(range(1, num_pages+1), link)
urls = set_urls(pages)
docs = extract_text(urls)
