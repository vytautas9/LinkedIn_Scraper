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
import datetime
import pandas as pd
import time

# Custom files:
import credentials
# -----------------------------------------------------------


# -----------------------------------------------------------
# Program parameters
# Job position to look for and locale
position = "machine learning"
location = "lithuania"

# read linked in site (True) or read csv file (False) to get links?
read_linkedin = True
# -----------------------------------------------------------


# -----------------------------------------------------------
# Functions
def login_linkedin(email, password):
    """
    Searches for login and password inputs and send provided credentials.
    :param email: LinkedIn account email
    :param password: LinkedIn account password
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
    """
    Opens the LinkedIn job offers page based on provided job position and job location
    :param job_position: string - job position
    :param job_location: string - job location
    """
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


def get_number_of_available_pages():
    """
    Gets the maximum number of available links at the current webpage of job lists
    :return: integer - maximum number of available pages
    """
    # Get the number of available links after opening job list page
    jobs_block = driver.find_element(By.CLASS_NAME,'jobs-search-results-list')
    page_block = jobs_block.find_elements(By.CSS_SELECTOR, '.jobs-search-results-list__pagination')

    # A string of page numbers, example: 1 \n 2 \n 3 \n ... \n 22
    pages = page_block[0].text.splitlines()

    # Get the maximum page number as int
    max_page_number = int(pages[len(pages)-1])
    return max_page_number


def get_linkedin_job_links(job_position, job_location, old_job_links):
    """
    Reads the linkedin job offers dynamically based on provided job position and job location and get links to them.
    Only unique list of jobs will be saved based on job_id from old_job_links.
    :param job_position: a job position string
    :param job_location: a job location string
    :param old_job_links: a dataframe of old job links, ids and read datetimes
    :return: a dataframe object consisting of read datetime in UTC, job links and job ids.
    """
    # A list of old job ids
    old_ids = old_job_links['job_id'].tolist()

    # Opening jobs webpage
    open_job_list_page(job_position, job_location)
    time.sleep(2)

    # Get the maximum number of available pages
    number_of_pages = get_number_of_available_pages()

    # empty dataframe for links and job ids
    job_links = pd.DataFrame(columns=['DateTimeReadUTC','job_id','job_link'])

    # Empty counter for the number of job offers and unique number of job offers
    number_of_links = 0
    number_of_unique_links = 0

    # TODO - also print which search keywords are being passed
    print('Links are being collected now.')
    try:
        print(f'\t {number_of_pages} page(s) are going to be scanned.')
        # TODO - sometimes, even tho linkedin shows 24 pages, the program fails after 18 pages where linkedin shows "no matches found"
        for page in range(1, number_of_pages + 1):
            print(f'\t\t Currently scanning page - {page}')
            # Open page
            driver.find_element(By.XPATH, f'//button[@aria-label="Page {page}"]').click()
            time.sleep(2)

            jobs_block = driver.find_element(By.CLASS_NAME, 'jobs-search-results-list')
            jobs_list = jobs_block.find_elements(By.CSS_SELECTOR, '.jobs-search-results__list-item')

            for job in jobs_list:
                job_id = job.get_attribute('data-occludable-job-id')
                link = f'https://www.linkedin.com/jobs/view/{job_id}'
                number_of_links += 1
                if link not in job_links['job_link'] and job_id not in old_ids:
                    number_of_unique_links += 1
                    data = {
                        'DateTimeReadUTC': datetime.datetime.utcnow(),
                        'job_id': job_id,
                        'job_link': link
                    }
                    job_links = pd.concat([job_links, pd.DataFrame(data, index=[number_of_unique_links-1])], ignore_index=True)
                else:
                    pass
                driver.execute_script("arguments[0].scrollIntoView();", job)

            time.sleep(3)
    except:
        print(f'\tError at page - {page}')
    print('Scanning complete.')
    if number_of_links > 0:
        print('Found ' + str(number_of_links) + ' links for job offers')
        print('Out of those links, ' + str(number_of_unique_links) + ' are unique links which we do not already have')
        if len(old_ids) and number_of_unique_links > 0:
            print('Those links will be appended to already existing list of ' + str(len(old_ids)) + ' links')
            job_links = pd.concat([job_links, old_job_links], ignore_index=True)
        else:
            pass
    else:
        print('No links were found.')
    return job_links


def get_linkedin_job_offer_description(job_links, old_job_data):
    """
    Reads the general information and job description of provided links. Links that were already read and saved in csv
    are not going to be read again based on the old_job_data dataframe
    :param job_links: a dataframe with job_id and job_link for jobs which should be read
    :param old_job_data: old dataframe of job_data, existing job_ids are not going to be read again
    :return: a dataframe with general information and job descriptions of provided links + old job data
    """
    # TODO - error if 0 links provided

    urls = job_links['job_link'].tolist()
    all_job_ids = job_links['job_id'].tolist()
    old_job_ids = old_job_data['job_id'].tolist()

    # Start reading linkedin job offers
    # Create empty lists to store information
    job_ids = []
    job_links = []
    job_titles = []
    company_names = []
    company_locations = []
    work_methods = []
    post_dates = []
    work_times = []
    job_descriptions = []
    readDateTimesUTC = []

    # Visit each link one by one to scrape the information
    print('Visiting the links and collecting information just started.')
    print(f'{len(urls)} link(s) are going to be read.')
    for i in range(len(urls)):
        print(f'\t Currently visiting link - {i + 1}')
        # TODO - also, in addition to the number of the link being read, also show a job_id

        # Based on the provided job_id, check if this job description has not been read already,
        # If it has been - skip to the next link, otherwise read it
        if str(all_job_ids[i]) in old_job_ids:
            print(f'\t\tJob description has been already read previously... Skipping...')
            continue
        else:
            pass

        try:
            # Open the url
            driver.get(urls[i])
            time.sleep(2)
            # Click See more.
            driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Click to see more description"]').click()
            time.sleep(2)
        except Exception:
            # if error appears while opening the page, continue to next url
            continue
        # Find the general information of the job offers

        # Sometimes there's more than 1 'p5' content, for now we'll take only the first one
        content = driver.find_elements(By.CLASS_NAME, 'p5')[0]
        print(f'\t\tGeneral job info. - IN-PROGRESS.')

        readDateTimesUTC.append(datetime.datetime.utcnow())

        # We take the job id and job link from the provided dataframe
        job_ids.append(all_job_ids[i])
        job_links.append(urls[i])

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
    print(f'Finished reading {len(job_links)} link(s).')
    # create a dataframe out of the results
    # TODO - standardize job_data column names
    data = pd.DataFrame({'Date': post_dates,
                         'job_id': job_ids,
                         'Company': company_names,
                         'Title': job_titles,
                         'Location': company_locations,
                         'Description': job_descriptions,
                         'WorkMethods': work_methods,
                         'WorkTimes': work_times,
                         'Link': job_links,
                         'ReadDateTimeUTC': readDateTimesUTC
                         })
    data = pd.concat([data, old_job_data], ignore_index=True)
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
    # See if there's already a list of read links, if yes, read it
    # Otherwise create an empty dataframe object
    try:
        job_links = pd.read_csv('LinkedIn_Job_Links.csv', dtype={'DateTimeReadUTC': 'string',
                                                                 'job_id': 'string',
                                                                 'job_link': 'string'})
    except FileNotFoundError:
        job_links = pd.DataFrame(columns=['DateTimeReadUTC', 'job_id', 'job_link'])

    # Start reading LinkedIn job offer links
    job_links = get_linkedin_job_links(position, location, job_links)
    # Save the job links
    job_links.to_csv('LinkedIn_Job_Links.csv', index=False)
else:
    job_links = pd.read_csv('LinkedIn_Job_Links.csv')

# See if there's already a list of read job descriptions, if yes, read it
# Otherwise create an empty dataframe object
# TODO - standardize job_data column names
try:
    job_data = pd.read_csv('LinkedIn_Jobs.csv', sep=';', dtype={'job_id': 'string'})
except FileNotFoundError:
    job_data = pd.DataFrame(columns=['Date', 'job_id', 'Company', 'Title', 'Location', 'Description',
                                     'WorkMethods', 'WorkTimes', 'Link', 'ReadDateTimeUTC'])

# Read linkedin job offers
job_data = get_linkedin_job_offer_description(job_links, job_data)
job_data.to_csv('LinkedIn_Jobs.csv', sep=';', index=False)

# end the program and close the browser
driver.quit()