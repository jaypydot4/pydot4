from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.chrome.options import Options
from urlparse import urlparse
from datetime import timedelta, date
import webbrowser
import argparse
import requests
import getpass
import sys
import time
import re
import csv
import Credentials


class NewJobDetails(object):
    def __init__(self, job_posted, job_title, job_description, job_company, job_location, job_applied):
        self.job = {}
        self.job["posted"] = job_posted
        self.job["title"] = job_title
        self.job["description"] = job_description
        self.job["company"] = job_company
        self.job["location"] = job_location
        self.job["applied"] = job_applied
        return

    def __getitem__(self, item):
        return self.job[item]


class JobHunt(object):

    def __init__(self, firstname, lastname, username, useremail, password, keyword, autoapply):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.useremail = useremail
        self.passwd = password
        self.keyword = keyword
        self.autoapply = autoapply
        self.base_url = 'http://sgcareers.com.sg/login'

        chromeOptions = Options()
        chromeOptions.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(chrome_options=chromeOptions)

        self.csv_filename = 'job_listing_sgcareers.csv'
        self.new_job = None
        self.table_headers = ["Date posted", "Job Title", "Description", "Company", "Location", "Applied"]
        self.csvwriter = None

        pattern = '(job_listing-[\d]+)'
        self.joblist_pattern = re.compile(pattern)

        self.day_posted_pattern = re.compile('day(s)?')
        return

    def __del__(self):
        if self.fileHandle is not None:
            self.fileHandle.close()
        return

    def open_base_url(self):
        #self.driver.maximize_window()
        self.driver.get(self.base_url)
        return

    def go_to_sign_in_page(self):
        self.driver.find_element_by_class_name('nav-item__link').click()
        return

    def fill_login_info(self):
        print('Fill-up log-in credentials')
        self.driver.find_element_by_id('user_login').send_keys(self.username)
        self.driver.find_element_by_id('user_pass').send_keys(self.passwd)
        self.driver.find_element_by_id('wp-submit').click()
        return

    def search_from_keyword_and_start(self):
        print('Searching job postings related to \"{}\"'.format(self.keyword))
        self.driver.find_element_by_name('search_keywords').send_keys(self.keyword)
        self.driver.find_element_by_class_name('search_submit').click()

        # WebDriverWait(self.driver, 30).until(
        #     expected_conditions.presence_of_element_located((By.CLASS_NAME, 'job_listings')))
        # print("Job list loaded")
        return

    def extract_soup_from_url(self, url):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except requests.exceptions.HTTPError as err:
            print("Invalid URL: %s" %url)
            print(err)
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)

        return soup

    def collect_job_urls(self):
        print('Collecting job postings...')
        self.job_url_list = []

        elems = self.driver.find_elements_by_xpath("//li[@data-href]")
        for elem in elems:
            if (urlparse(elem.get_attribute("data-href")).netloc == 'sgcareers.com.sg'):
                self.job_url_list.append(elem.get_attribute("data-href"))
        return self.job_url_list

    def process_get_actual_date(self, day_posted):
        date_posted_encoded = day_posted.encode('utf-8')
        num_days = self.day_posted_pattern.search(day_posted)

        today = date.today()
        if num_days is not None:
            days_ago = int(filter(str.isdigit, date_posted_encoded))
            if today - timedelta(days=days_ago) == 0:
                return str(today)
            else:
                return str(today - timedelta(days=days_ago))
        else:
            #print("Date of posting is more than a week ago: {}".format(date_posted_encoded))
            return None

    def extract_job_details(self, job_details):
        self.job_soup = self.extract_soup_from_url(job_details)

        title = self.job_soup.find("h1", {"class": "page-title"}).text.strip()
        posted = self.job_soup.find("li", {"class": "job-date-posted"}).text.strip()
        organization = self.job_soup.find("li", {"class": "job-company"}).text.strip()
        location = self.job_soup.find("a", {"rel": "tag"}).text.strip()
        details = self.job_soup.find("div", {"itemprop": "description"}).findAll("p")
        description = ""
        for entry in details:
            description += entry.text.strip().encode('utf-8') + "\n"

        # We need to determine when the job posting was posted based in num of days
        # because that's the only way we can determine the actual date of posting;
        # otherwise, a "x weeks" ago can be vague.  In this case, we dont record
        # the specific job posting.
        date_posted = self.process_get_actual_date(posted)
        if date_posted is not None:
            self.new_job = NewJobDetails(date_posted, title, description, organization, location, "NO")
        else:
            self.new_job = None

        return

    def create_or_open_csv(self):
        try:
            self.fileHandle = open(self.csv_filename, "r+")
            self.csvwriter = csv.DictWriter(self.fileHandle, fieldnames=self.table_headers)
            #self.fileHandle = open(self.csv_filename, "a+")
            print("Opening csv file")
        except IOError as e:
            self.fileHandle = open(self.csv_filename, "w+")
            self.csvwriter = csv.DictWriter(self.fileHandle, fieldnames=self.table_headers)
            self.csvwriter.writeheader()
            print("Creating new csv file")
        return True

    def has_similar_entry_in_file(self, job_posted, job_title, job_company):
        # start reading from beginning of file
        self.fileHandle.seek(0, 0)
        reader = csv.DictReader(self.fileHandle)
        for row in reader:
            file_posted = row[self.table_headers[0]]
            file_title = row[self.table_headers[1]]
            file_description = row[self.table_headers[2]]
            file_company = row[self.table_headers[3]]
            file_location = row[self.table_headers[4]]
            file_applied = row[self.table_headers[5]]

            if job_posted == file_posted and \
               job_title == file_title and \
               job_company == file_company:
                #print("Found same entry: {}, {}".format(file_title, file_company))
                return True

        return False

    def apply_job(self):
        self.job_soup.find('application_button').click()

        # open a link in a new window
        actions = ActionChains(self.driver)
        about = self.driver.find_element_by_link_text('About')
        actions.key_down(Keys.CONTROL).click(about).key_up(Keys.CONTROL).perform()

        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get("https://stackoverflow.com")
        return

    def scan_jobsite(self):
        try:
            print("Launching Google Chrome web browser...")
            self.open_base_url()

            # if menu is not displayed (because window size is too small to display them, then process it here)
            # if self.driver.find_element_by_class_name('icon-menu'):
            #     print('Found icon-menu')
            #     self.driver.find_element_by_class_name('icon-menu').click()
            #
            #     if self.driver.find_element_by_id('login-modal'):
            #         print('Found login')
            #         self.driver.find_element_by_id('login-modal').click()

            # fill-in login information
            self.fill_login_info()

            # click View Jobs
            if self.driver.find_element_by_id('menu-item-2191'):
                self.driver.find_element_by_id('menu-item-2191').click()

            self.search_from_keyword_and_start()

            # TODO: Change this "wait" implementation
            time.sleep(10)
            self.extract_soup_from_url(self.driver.current_url)
            self.collect_job_urls()

            if self.create_or_open_csv() is True:
                for job_details in self.job_url_list:
                    self.extract_job_details(job_details)

                    if self.new_job is not None:
                        if self.has_similar_entry_in_file(self.new_job["posted"],
                                                          self.new_job["title"],
                                                          self.new_job["company"]) is False:

                            #if self.autoapply is True:
                            #    self.apply_job()

                            # write new job posting to the csv file
                            print("New job posting: {} from {}".format(self.new_job["title"], self.new_job["company"]))

                            self.csvwriter.writerow({
                                self.table_headers[0]: self.new_job["posted"],
                                self.table_headers[1]: self.new_job["title"],
                                self.table_headers[2]: self.new_job["description"],
                                self.table_headers[3]: self.new_job["company"],
                                self.table_headers[4]: self.new_job["location"],
                                self.table_headers[5]: self.new_job["applied"]
                            })

                            self.fileHandle.flush()

                self.fileHandle.close()

        except ElementNotVisibleException as e:
            print(e)
        return


if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyword', required=True, help='Specific job title to search', type=str)
    parser.add_argument('-a', '--autoapply', choices=['true', 'yes', 'false', 'no'], default='no',
                            help='set TRUE / YES or FALSE / NO, if to auto-apply when job is found', type=str)
    parser.add_argument('-cv', '--resume', help='...', type=str)

    args = parser.parse_args()

    print("Please input basic details to log-in to http://sgcareers.com.sg")

    if args.autoapply.lower() == 'yes' or args.autoapply.lower() == 'true':
        #if 'resume' not in vars(args):
        if args.resume is None:
            print('Auto apply requires a link to your resume or CV')
            sys.exit(1)
        else:
            autoapply = True
            print('Auto apply is enabled')
    else:
        autoapply = False
        print('Auto apply is disabled')

    firstname = raw_input("First name: ")
    lastname = raw_input("Last name: ")
    username = raw_input("User name: ")
    useremail = raw_input("Email: ")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
        print("Invalid email address")
        sys.exit(1)

    password = getpass.win_getpass("User password: ")

    # firstname, lastname, username, useremail, password, keyword, autoapply = \
    #     Credentials.Credentials().get_credentials()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
        print("Invalid email address")
        sys.exit(1)

    ListJobs = JobHunt(firstname, lastname, username, useremail, password, args.keyword, autoapply)
    ListJobs.scan_jobsite()
