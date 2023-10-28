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
    print('indeed')
    print(jobs)
    return jobs, errors


def linkedin(url, city=None, language=None):
    jobs = []
    errors = []
    if url:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            main_div = soup.find('div', 'base-serp-page__content')
            job_lst = main_div.find_all('li')
            if job_lst:
                for job in job_lst:
                    title = job.find('h3', 'base-search-card__title').get_text(strip=True)
                    a_element = job.find('div', class_='base-card').find('a', class_='base-card__full-link')

                    href = a_element.get('href')
                    content = ''
                    company = job.find('h4', 'base-search-card__subtitle').get_text(strip=True)

                    jobs.append({'title': title, 'url': href,
                                 'description': content, 'company': company,
                                 'city_id': city, 'language_id': language,
                                 'search_source': 'www.linkedin.com'})
            else:
                errors.append({'url': url, 'title': "Div does not exists"})
        else:
            errors.append({'url': url, 'title': "Page do not response"})
    return jobs, errors


def dice(url, city=None, language=None):
    jobs = []
    errors = []
    domain = 'https://www.dice.com/job-detail/'
    parsing = True
    page = 1

    while parsing:
        driver.get(url)
        time.sleep(5)
        html = driver.page_source
        if html:
            soup = BS(html, 'html.parser')
            job_cards = soup.find_all('div', 'card search-card')
            for job in job_cards:
                job_title = job.find('h5')
                title = job_title.a.text.strip()
                a_tag = job_title.find('a')
                href = a_tag.get('id')
                company_el = job.find('div', 'card-company')
                company = company_el.a.text.strip()
                content = job.find('div', {'data-cy': 'card-summary'}).get_text(strip=True)
                jobs.append({'title': title, 'url': domain + href,
                             'description': content, 'company': company,
                             'city_id': city, 'language_id': language,
                             'search_source': 'www.dice.com'})
        else:
            errors.append({'url': url, 'title': "Page do not response"})

        try:
            button = driver.find_element(By.CSS_SELECTOR, 'li.pagination-next.page-item.ng-star-inserted')
            if 'disabled' in button.get_attribute('class'):
                parsing = False
            elif page > 15:
                parsing = False
            else:
                page += 1
                url = f'https://www.dice.com/jobs?q=python&countryCode=US&radius=30&radiusUnit=mi&page={page}&pageSize=100&filters.postedDate=ONE&language=en'

        except NoSuchElementException:
            parsing = False
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
    print('flexjobs')
    print(jobs)
    return jobs, errors


def builtin(url, city=None, language=None):
    jobs = []
    errors = []
    domain = 'https://builtin.com'
    if url:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            main_div = soup.find('div', 'd-flex gap-sm flex-column')
            job_lst = main_div.find_all('div', attrs={'data-id': 'job-card'})
            if job_lst:
                for job in job_lst:
                    title = job.find('h2').get_text(strip=True)
                    href_el = job.find('h2').find('a')
                    href = href_el.get('href') if href_el else ''
                    content = ''
                    company_el = job.find('div', attrs={'data-id': 'company-title'})
                    company = company_el.find('span').get_text(strip=True)

                    jobs.append({'title': title, 'url': domain + href,
                                 'description': content, 'company': company,
                                 'city_id': city, 'language_id': language,
                                 'search_source': 'www.builtin.com'})
            else:
                errors.append({'url': url, 'title': "Div does not exists"})
        else:
            errors.append({'url': url, 'title': "Page do not response"})
    return jobs, errors


def themuse(url, city=None, language=None):
    jobs = []
    errors = []
    domain = 'https://www.themuse.com/'
    if url:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            job_lst = soup.find_all('div', 'JobCard_jobCardClickable__ZR6Sk JobCard_jobCard__jQyRD')
            if job_lst:
                for job in job_lst:
                    title = job.find('h2').get_text(strip=True)

                    href_el = job.find('a', 'JobCard_viewJobLink__Gesny')
                    href = href_el.get('href') if href_el else ''
                    content = ''
                    company_el = job.find('div', 'JobCard_companyLocation__KBfg2')
                    company = company_el.find('a').get_text(strip=True)

                    jobs.append({'title': title, 'url': domain + href,
                                 'description': content, 'company': company,
                                 'city_id': city, 'language_id': language,
                                 'search_source': 'www.themuse.com'})
            else:
                errors.append({'url': url, 'title': "Div does not exists"})
        else:
            errors.append({'url': url, 'title': "Page do not response"})
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
            if 'data-jobid' in job.attrs:
                job_id = job['data-jobid']
                title_element = job.find('a', id='job-title-'+job_id)
                title = title_element.text if title_element else ''
                href = title_element['href'] if title_element else ''
                company_info = job.find('div', class_='EmployerProfile_employerInfo__EehaI')
                if company_info:
                    for span in company_info.find_all('span'):
                        span.extract()
                    company = company_info.get_text(strip=True)
                else:
                    company = ''

                jobs.append({'title': title, 'url': domain + href,
                            'description': '', 'company': company,
                            'city_id': city, 'language_id': language,
                            'search_source': 'www.glassdoor.com'})
            else:
                errors.append({'title': "data-jobid attribute missing"})
    else:
        errors.append({'url': url, 'title': "Page do not response"})    
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
    print('ladders')
    return jobs, errors


def test_parser(parser_func, url):
    jobs, errors = parser_func(url)
    return jobs, errors

if __name__ == '__main__':
    urls = {
        indeed: 'https://www.indeed.com/jobs?q=python+developer&sc=0kf%3Aexplvl%28ENTRY_LEVEL%29%3B&fromage=1',
        linkedin: 'https://www.linkedin.com/jobs/search/?currentJobId=3728890924&f_E=1%2C2%2C3&f_T=25169&f_TPR=r86400&keywords=python%20developer&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD',
        flexjobs: 'https://www.flexjobs.com/search?search=Python&location=&search_type=detailed+search&srt=date',
        builtin: 'https://builtin.com/jobs/entry-level/mid-level?search=python',
        themuse: 'https://www.themuse.com/search/keyword/python/',
        dice: 'https://www.dice.com/jobs?q=python&countryCode=US&radius=30&radiusUnit=mi&page=1&pageSize=100&filters.postedDate=ONE&language=en&eid=qpw_,sw_0',
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
