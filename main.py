# -----------------------------------------------------------
# Reads linkedin job offers through LinkedIn profile. Saves
# the data into dataframe and saves as csv file.
#
# (C) 2022 Vytautas Kraujalis, Lithuania
# email vytautas.kraujalis2@gmail.com
# -----------------------------------------------------------


# -----------------------------------------------------------
# References
# https://github.com/saulotp/linkedin-job-description-scrap/blob/main/LinkedinScrapping-updated.py
# https://medium.com/@kurumert/web-scraping-linkedin-job-page-with-selenium-python-e0b6183a5954
# -----------------------------------------------------------


# -----------------------------------------------------------
# Modules
from selenium import webdriver # needs additional chrom webdriver -- https://chromedriver.chromium.org/downloads
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import datetime
import pandas as pd
import time

# Custom files:
import credentials
# -----------------------------------------------------------


# -----------------------------------------------------------
# Program parameters
# Job position to look for and locale
position = "data scientist"
location = "lithuania"
#landing_page = f'https://www.linkedin.com/jobs/search/?currentJobId=3156228491&geoId=101464403&keywords={position.replace(" ", "%20")}&location={local}'

# How many pages are we gonna loop through
# TODO - make the program read the number of available pages
#number_of_pages = 20
# read linked in site (True) or read csv file (False) to get links?
read_linkedin = True
# -----------------------------------------------------------


# -----------------------------------------------------------
# Functions
def login_linkedin(email, password):
    """
    Searches for login and password inputs and send provided credentials.
    :param email: linkedin account email
    :param password: linkedin account password
    :return:
    """
    # Opening linkedin website
    driver.get('https://www.linkedin.com/login')
    # waiting load, lets wait a bit for the link to fully load
    time.sleep(2)

    # Accept cookies
    driver.find_element(By.XPATH, '/html/body/div/main/div[1]/div/section/div/div[2]/button[2]').click()

    # Provide credentials
    driver.find_element(By.ID, 'username').send_keys(email)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    driver.implicitly_wait(30)


def open_job_list_page(job_position, job_location):
    # Open default LinkedIn job list page
    driver.get('https://www.linkedin.com/jobs/')
    # Find the keywords/location search bars
    search_bars = driver.find_elements(By.CLASS_NAME, 'jobs-search-box__text-input')
    # Enter the job_position and job_location into search bars
    search_keywords = search_bars[0]
    search_keywords.send_keys(job_position)
    search_location = search_bars[3]
    search_location.send_keys(job_location)
    time.sleep(2)
    search_location.send_keys(Keys.RETURN)


def get_number_of_available_links():
    # Get the number of available links afer opening job list page
    jobs_block = driver.find_element(By.CLASS_NAME,'jobs-search-results-list')
    page_block = jobs_block.find_elements(By.CSS_SELECTOR, '.jobs-search-results-list__pagination')
    # A string of page numbers, example: 1 \n 2 \n 3 \n ... \n 22
    pages = page_block[0].text.splitlines()
    # Get the maximum page number as int
    max_page_number = int(pages[len(pages)-1])
    return max_page_number


def get_linkedin_job_links(job_position, job_location):
    """
    Reads the linkedin job offers and get links to them.
    :param number_of_pages: number of pages to be read. Before launching this function, please indicate the maximum pages to be read from LinkedIn (manual).
    :param landing_page: random LinkedIn job offer in the first page.
    :return: a list of job offer links.
    """
    # Opening jobs webpage
    open_job_list_page(job_position, job_location)
    # waiting load
    time.sleep(2)
    # Get the maximum number of available pages
    number_of_pages = get_number_of_available_links()
    # empty list for links
    links = []
    print('Links are being collected now.')
    try:
        print(f'\t {number_of_pages} page(s) are going to be scanned.')
        # TODO - sometimes, even tho linkedin shows 24 pages, the program fails after 18 pages where linkedin shows "no matches found"
        for page in range(1, number_of_pages + 1):
            print(f'\t\t Currently scanning page - {page}')
            # Open page
            driver.find_element(By.XPATH, f'//button[@aria-label="Page {page}"]').click()
            time.sleep(2)

            jobs_block = driver.find_element(By.CLASS_NAME,
                                             'jobs-search-results-list')  # 'jobs-search-results-list' #'scaffold-layout__list-container'
            jobs_list = jobs_block.find_elements(By.CSS_SELECTOR, '.jobs-search-results__list-item')

            for job in jobs_list:
                all_links = job.find_elements(By.TAG_NAME, 'a')
                for a in all_links:
                    if str(a.get_attribute('href')).startswith(
                            "https://www.linkedin.com/jobs/view") and a.get_attribute(
                            'href') not in links:
                        links.append(a.get_attribute('href'))
                    else:
                        pass
                # scroll down for each job element
                driver.execute_script("arguments[0].scrollIntoView();", job)

            time.sleep(3)
    except:
        pass
    print('Scanning complete.')
    print('Found ' + str(len(links)) + ' links for job offers')
    return links


def get_linkedin_job_offer_description_v2(urls):
    """
    Reads the general information and job description of provided links.
    :param urls: a list of links to job offers.
    :return: a dataframe with general information and job descriptions, as well as read datetime in UTC.
    """
    # TODO - error if 0 links provided
    # Start reading linkedin job offers
    # Create empty lists to store information
    job_titles = []
    company_names = []
    company_locations = []
    work_methods = []
    post_dates = []
    work_times = []
    job_descriptions = []

    # Visit each link one by one to scrape the information
    print('Visiting the links and collecting information just started.')
    for i in range(len(urls)):
        print(f'\t Currently visiting link - {i + 1}')
        try:
            # Open the url
            driver.get(urls[i])
            time.sleep(2)
            # Click See more.
            driver.find_element(By.CLASS_NAME, "artdeco-card__actions").click()
            time.sleep(2)
        except Exception:
            # if error appears while opening the page, continue to next url
            continue
        # Find the general information of the job offers
        # Sometimes there's more than 1 'p5' content, for now we'll take only the first one
        content = driver.find_elements(By.CLASS_NAME, 'p5')[0]
        print(f'\t\tGeneral job info. - IN-PROGRESS.')

        # We use "find_elements" to get empty list in case value is not found
        # Job Title
        job_title = content.find_elements(By.TAG_NAME, "h1")
        if len(job_title):
            job_titles.append(job_title[0].text)
        else:
            job_titles.append("")
            print(f'\t\t\tJob title was not found...')

        # Company Name
        company_name = content.find_elements(By.CLASS_NAME, "jobs-unified-top-card__company-name")
        if len(company_name):
            company_names.append(company_name[0].text)
        else:
            company_names.append("")
            print(f'\t\t\tCompany name was not found...')

        # Company Location
        company_location = content.find_elements(By.CLASS_NAME, "jobs-unified-top-card__bullet")
        if len(company_location):
            company_locations.append(company_location[0].text)
        else:
            company_locations.append("")
            print(f'\t\t\tCompany location was not found...')

        # Work Time
        work_time = content.find_elements(By.CLASS_NAME, "jobs-unified-top-card__job-insight")
        if len(work_time):
            work_times.append(work_time[0].text)
        else:
            work_times.append("")
            print(f'\t\t\tWork time was not found...')

        # Work Method
        work_method = content.find_elements(By.CLASS_NAME, "jobs-unified-top-card__workplace-type")
        if len(work_method):
            work_methods.append(work_method[0].text)
        else:
            work_methods.append("")
            print(f'\t\t\tWork method was not found...')

        # Post Date
        post_date = content.find_elements(By.CLASS_NAME, "jobs-unified-top-card__posted-date")
        if len(post_date):
            post_dates.append(post_date[0].text)
        else:
            post_dates.append("")
            print(f'\t\t\tPost date was not found...')

        print(f'\t\tGeneral job info. - DONE.')
        time.sleep(2)

        #
        print(f'\t\tJob description - IN-PROGRESS.')
        # select job description
        job_description = driver.find_elements(By.CLASS_NAME, 'jobs-description__content')[0]
        job_text = job_description.find_elements(By.CLASS_NAME, "jobs-box__html-content")
        if len(job_text):
            job_descriptions.append(job_text[0].text)
        else:
            job_descriptions.append("")
            print(f'\t\t\tJob description was not found...')
        print(f'\t\tJob description - DONE.')
        time.sleep(2)
    print(f'Finished reading {len(urls)} link(s).')
    # create a dataframe out of the results
    data = pd.DataFrame({'Date': post_dates,
                         'Company': company_names,
                         'Title': job_titles,
                         'Location': company_locations,
                         'Description': job_descriptions,
                         'WorkMethods': work_methods,
                         'WorkTimes': work_times,
                         'Link': urls,
                         'ReadDateTimeUTC': datetime.datetime.utcnow()
                         })
    # cleaning description column
    data['Description'] = data['Description'].str.replace('\n', ' ')
    return data
# -----------------------------------------------------------


# Open browser, this launches the chrome browser
driver = webdriver.Chrome(executable_path="chromedriver.exe")
# Maximizing browser window to avoid hidden elements
driver.set_window_size(1024, 600)
driver.maximize_window()

# login to linkedin
login_linkedin(credentials.email, credentials.password)

if read_linkedin:
    # Start reading linkedin job offer links
    links = get_linkedin_job_links(position, location)
    # Save the links
    job_offer_links = pd.DataFrame({'ReadDateTimeUTC': datetime.datetime.utcnow(),
                                    'Link': links,
                                    'SearchPosition': position,
                                    'SearchLocation': location
                                   }, index=range(0, len(links)))
    job_offer_links.to_csv('LinkedIn_Job_Links.csv', index = False)
else:
    links = pd.read_csv('LinkedIn_Job_Links.csv')
    links = links['Link']

# Read linkedin job offers
job_data = get_linkedin_job_offer_description_v2(links[0:2])
job_data.to_csv('LinkedIn_Jobs.csv', index = False)

# end the program and close the browser
driver.quit()