from bs4 import BeautifulSoup
from pprint import pprint
from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
import webbrowser
import requests
import getpass
import sys
import re

class JobHunt(object):

    def __init__(self, useremail, password):
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

    def sign_in(self):
        username = self.driver.find_element_by_link_text('Sign in')
        username.clear()
        username.send_keys(self.useremail)

        passwd = self.driver.find_element_by_class_name('login-password')
        passwd.clear()
        passwd.send_keys(self.passwd)

        login_button = self.driver.find_element_by_class_name('login submit-button')
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
        self.open_base_url()
        self.sign_in()



        return

if __name__ == "__main__":

    useremail = raw_input("Enter email: ")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", useremail):
        print("Invalid email address")
        sys.exit(1)

    password = getpass.win_getpass("User password: ")

    ListJobs = JobHunt(useremail, password)
    ListJobs.scan_jobsite()
