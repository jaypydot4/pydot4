from bs4 import BeautifulSoup
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import ElementNotVisibleException
from urlparse import urlparse
import webbrowser
import argparse
import requests
import getpass
from selenium.common.exceptions import ElementNotVisibleException
import sys
import time
import re
import Credentials
from pprint import pprint

import re

class JobHunt(object):

    def __init__(self, firstname, lastname, username, useremail, password, keyword):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.useremail = useremail
        self.passwd = password
        self.keyword = keyword
        self.base_url = 'http://sgcareers.com.sg/login'
        self.driver = webdriver.Chrome()

        pattern = '(job_listing-[\d]+)'
        self.joblist_pattern = re.compile(pattern)
        return

    def __del__(self):
        return

    def open_base_url(self):
        self.driver.maximize_window()
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
        #      expected_conditions.text_to_be_present_in_element_value((By.CLASS_NAME, self.joblist_pattern)))
        # print("Job list loaded")
        return

    def extract_soup_from_url(self, url):
        soup = None

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
                #print elem.get_attribute("data-href")
                self.job_url_list.append(elem.get_attribute("data-href"))
        return self.job_url_list

    def scan_jobsite(self):
        try:
            print("Launching default web browser...")
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


            time.sleep(10)
            self.extract_soup_from_url(self.driver.current_url)
            #print(job_list_soup)
            self.collect_job_urls()
            #pprint(job_list_soup.text)

            for job_details in self.job_url_list:
                job_soup = self.extract_soup_from_url(job_details)
                title = job_soup.find("h1", {"class":"page-title"}).text.strip()
                print(title)

        except ElementNotVisibleException as e:
            print(e)
        except:
            print("Invalid URL: {}".format(self.driver.current_url))
            sys.exit(1)
        return


if __name__ == "__main__":

    print("Please input basic details to log-in to http://sgcareers.com.sg")
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-k', '--keyword', required=True, help='Specific job title to search', type=str)
    # parser.add_argument('-a', '--autoapply', choices=['true', 'yes', 'false', 'no'], default='no',
    #                         help='set TRUE / YES or FALSE / NO, if to auto-apply when job is found', type=str)
    # parser.add_argument('-cv', '--resume', help='...', type=str)
    #
    # args = parser.parse_args()
    #
    # if args.autoapply.lower() == 'yes' or args.autoapply.lower() == 'true':
    #     #if 'resume' not in vars(args):
    #     if args.resume is None:
    #         print('Auto apply requires a link to your resume or CV')
    #         sys.exit(1)
    #     else:
    #         print('Auto apply is enabled')
    # else:
    #     print('Auto apply is disabled')

    # firstname = raw_input("First name: ")
    # lastname = raw_input("Last name: ")
    # useremail = raw_input("Email: ")
    # if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
    #     print("Invalid email address")
    #     sys.exit(1)
    #
    # password = getpass.win_getpass("User password: ")

    firstname, lastname, username, useremail, password, keyword = Credentials.Credentials().get_credentials()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
        print("Invalid email address")
        sys.exit(1)

    ListJobs = JobHunt(firstname, lastname, username, useremail, password, keyword)
    ListJobs.scan_jobsite()
