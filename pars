from fake_useragent import UserAgent
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
import time
import requests
import os, sys
import datetime as dt
import re
from selenium.webdriver.common.by import By

proj = os.path.dirname(os.path.abspath('manage.py'))
sys.path.append(proj)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "usa_job_last.settings")

import django
django.setup()

from scraping.models import Vacancy

ua = UserAgent()
headers = {'User-Agent': ua.random}

# local config
# service = Service()
# chrome_options = webdriver.ChromeOptions()
# # chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--no-sandbox")
# driver = webdriver.Chrome(service=service, options=chrome_options)

# deploy config
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')
chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH")
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


def save_jobs_to_database(jobs):
    skip_keywords = ['lead', 'senior', 'engineer']
    no_skip_keywords_keywords = ['python', 'django', 'flask', 'python/django']
    for job_data in jobs:
        title = job_data['title'].lower()
        if not any(keyword in title for keyword in skip_keywords) and any(keyword in title for keyword in no_skip_keywords_keywords):
            url = job_data['url']
            if not Vacancy.objects.filter(url=url).exists():
                job = Vacancy(
                    url=url,
                    title=job_data['title'],
                    company=job_data['company'],
                    description=job_data['description'],
                    search_source=job_data['search_source']
                )
                print(job)
                job.save()

def is_valid_job(title):
    keywords = ['python', 'django', 'flask', 'python/django']
    return any(keyword in title.lower() for keyword in keywords)


def indeed(url, city=None, language=None):
    driver.get(url)
    time.sleep(5)
    html = driver.page_source

    domain = 'https://www.indeed.com'
    jobs = []
    errors = []

    try:
        if html:
            soup = BS(html, 'html.parser')
            main_div = soup.find('div', 'mosaic-provider-jobcards')
            li_list = main_div.find_all('li', 'eu4oa1w0')

            for item in li_list:
                title = item.find('h2')
                if title:
                    title_link = title.find('a')
                    if title_link:
                        href = title_link['href']
                        content = item.ul.text

                        company_el = item.find('span', 'companyName')
                        if company_el:
                            company = company_el.text

                        jobs.append({'title': title.text if title else None,
                                     'url': domain + href if href else None,
                                     'description': content if content else None,
                                     'company': company if company else None,
                                        'search_source': 'www.indeed.com'})
        else:
            errors.append({'url': url, 'title': "HTML is empty"})
    except Exception as e:
        errors.append({'url': url, 'title': str(e)})
    print('indeed completed')
    print(jobs)
    return jobs, errors



def flexjobs(url, city=None, language=None):
    jobs = []
    errors = []
    domain = 'https://www.flexjobs.com'
    if url:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            job_lst = soup.find_all('li', 'm-0 row job clickable')
            if job_lst:
                for job in job_lst:
                    title = job.get('data-title')
                    if is_valid_job(title):
                        href_el = job.find('a', 'job-title job-link')
                        href = href_el['href']
                        company = ''
                        content_el = job.find('div', 'job-description')
                        content = content_el.get_text(strip=True) if content_el else ''
                        jobs.append({'title': title, 'url': domain + href,
                                     'description': content, 'company': company,
                                     'city_id': city, 'language_id': language,
                                     'search_source': 'www.flexjobs.com'})
            else:
                errors.append({'url': url, 'title': "Div does not exists"})
        else:
            errors.append({'url': url, 'title': "Page do not response"})
    print('flexjobs completed')
    print(jobs)
    return jobs, errors


def glassdoor(url, city=None, language=None):
    rating_pattern = re.compile(r'(\d+\.\d\s★|\d+\s★)')
    jobs = []
    errors = []
    domain = 'https://www.glassdoor.com'
    driver.get(url)
    time.sleep(5)

    html = driver.page_source
    if html:
        soup = BS(html, 'html.parser')
        job_lst = soup.find_all('li', 'JobsList_jobListItem__JBBUV')
        for job in job_lst:
            job_id = job['data-jobid']
            title_element = job.find('a', id='job-title-'+job_id)
            title = title_element.text if title_element else ''
            href = title_element['href'] if title_element else ''
            company_gx72iw = job.find('div', 'css-gx72iw')

            if company_gx72iw:
                if company_gx72iw.find('div', 'd-flex css-1sohcmw'):
                    company = company_gx72iw.find('div', 'css-8wag7x').text.strip()
                else:
                    company = company_gx72iw.find('div', 'css-1bgdn7m').text.strip()
            else:
                company = ''
            company = re.sub(rating_pattern, '', company)
            jobs.append({'title': title, 'url': domain + href,
                         'description': '', 'company': company,
                         'city_id': city, 'language_id': language,
                         'search_source': 'www.glassdoor.com'})
        else:
            errors.append({'url': url, 'title': "Div does not exists"})
    else:
        errors.append({'url': url, 'title': "Page do not response"})

    print('glassdoor completed')
    print(jobs)
    return jobs, errors


def ladders(url, city=None, language=None):
    page = 1
    domain = 'https://www.theladders.com'
    jobs = []
    errors = []
    parsing = True
    while parsing:
        upd_url = f'{url}&page={page}'
        driver.get(upd_url)
        time.sleep(5)
        html = driver.page_source
        if html:
            soup = BS(html, 'html.parser')
            main_div = soup.find('div', 'job-list-pagination-jobs')
            if main_div:
                job_cards = main_div.find_all('div', 'guest-job-card-container')
                if job_cards:
                    for job in job_cards:
                        job_title = job.find('div', 'job-card-text-container')
                        title_el = job_title.find('p', 'job-link-wrapper')
                        title = title_el.a.text.strip()
                        href = title_el.a['href']
                        company = job.find('span', 'job-card-company-name').get_text(strip=True)
                        content = job.find('p', 'job-card-description').get_text(strip=True)

                        jobs.append({'title': title, 'url': domain + href,
                                     'description': content, 'company': company,
                                     'city_id': city, 'language_id': language,
                                     'search_source': 'www.theladders.com'})

                else:
                    errors.append({'url': upd_url, 'title': "No job cards found"})
            else:
                errors.append({'url': upd_url, 'title': "No main_div found"})
        else:
            errors.append({'url': upd_url, 'title': "Page do not respond"})

        try:
            button = driver.find_element(By.CSS_SELECTOR, 'div.pagination-nav-link.next')
            if button.is_enabled():
                page += 1
            else:
                parsing = False
        except NoSuchElementException:
            parsing = False
    print('ladders completed')
    return jobs, errors


def test_parser(parser_func, url):
    jobs, errors = parser_func(url)
    return jobs, errors

if __name__ == '__main__':
    urls = {
        indeed: 'https://www.indeed.com/jobs?q=python+developer&sc=0kf%3Aexplvl%28ENTRY_LEVEL%29%3B&fromage=1',
        flexjobs: 'https://www.flexjobs.com/search?search=Python&location=&search_type=detailed+search&srt=date',
        glassdoor: 'https://www.glassdoor.com/Job/python-developer-jobs-SRCH_KO0,16.htm?fromAge=1&maxSalary=97000&minSalary=73000',
        ladders: 'https://www.theladders.com/jobs/searchresults-jobs?keywords=python%20developer&remoteFlags=Remote&remoteFlags=Hybrid&remoteFlags=In-Person&order=PUBLICATION_DATE&daysPublished=1&yearsExperience=1'

    }

    all_jobs = []
    all_errors = []

    for parser_func, url in urls.items():
        try:
            jobs, errors = test_parser(parser_func, url)
            all_jobs.extend(jobs)
            all_errors.extend(errors)
        except Exception as e:
            print(f"Error in {parser_func.__name__}: {str(e)}")

    save_jobs_to_database(all_jobs)
    ex_day = dt.date.today() - dt.timedelta(30)
    Vacancy.objects.filter(timestamp__lte=ex_day).delete()
    driver.quit()
