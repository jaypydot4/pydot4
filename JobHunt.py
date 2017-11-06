from bs4 import BeautifulSoup
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import webbrowser
import requests
import getpass
import sys
import re

class JobHunt(object):

    def __init__(self, firstname, lastname, useremail, password):
        self.firstname = firstname
        self.lastname = lastname
        self.useremail = useremail
        self.passwd = password
        self.base_url = 'https://www.linkedin.com/jobs'
        self.driver = webdriver.Chrome()
        return

    def __del__(self):
        return

    def open_base_url(self):
        self.driver.get(self.base_url)
        return

    def go_to_sign_in_page(self):
        self.driver.find_element_by_class_name('nav-item__link').click()
        return

    def fill_login_info(self):

        useremail = self.driver.find_element_by_id('session_key-login')
        useremail.clear()
        useremail.send_keys(self.useremail)

        userpasswd = self.driver.find_element_by_id('session_password-login')
        userpasswd.clear()
        userpasswd.send_keys(self.passwd)

        login_button = self.driver.find_element_by_id('btn-primary')
        login_button.click()

        return

    def search_from_keywords(self):

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

    def scan_jobsite(self):
        try:
            self.open_base_url()
            if self.driver.current_url.find('redirect'):
                self.go_to_sign_in_page()

            print("Current URL: {}".format(self.driver.current_url))
            self.driver.find_element_by_class_name('sign-in-link').click()

            # fill-in login information
            self.fill_login_info()
        except:
            print("Invalid URL: {}".format(self.driver.current_url))
            sys.exit(1)
        return


if __name__ == "__main__":

    print("Please input basic details to log-in to www.linkedin.com")
    firstname = raw_input("First name: ")
    lastname = raw_input("Last name: ")
    useremail = raw_input("Email: ")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
        print("Invalid email address")
        sys.exit(1)

    password = getpass.win_getpass("User password: ")

    ListJobs = JobHunt(firstname, lastname, useremail, password)
    ListJobs.scan_jobsite()
