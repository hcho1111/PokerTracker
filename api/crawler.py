from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
import pickle

import time
import random


def DownloadLedger(url: str, downloads_path: str, chromedriver_path: str):
    """
    Automatically download CSV with logs, names by providing a csv URL

    INPUTS:
    ------

    url - (str) url for ledger you wish to download
    downloads_path - (str) path to send downloaded csv files
    chromedriver_path - (str) path where webdriver for google chrome is located.
    """
    # initialize path for downloads and chrome driver
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": downloads_path}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
    driver.get(url)
    driver.maximize_window()

    # specified XPath for buttons of interest
    bottom_button_XPATH = "/html/body/div/div/div[1]/div[3]/div[6]"
    ledger_button_XPATH = (
        "/html/body/div[1]/div/div[1]/div[3]/div[2]/div/div[2]/div[2]/button[3]"
    )
    download_ledger_XPATH = (
        "/html/body/div/div/div[1]/div[3]/div[2]/div/div[2]/div[2]/div"
    )

    # click first button for showing modal overlay
    bottom_button = driver.find_element(By.XPATH, bottom_button_XPATH)
    bottom_button.click()

    # click ledger button in modal overlay
    ledger_button = bottom_button.find_element(By.XPATH, ledger_button_XPATH)
    ledger_button.click()

    # download the ledger csv
    download_ledger = ledger_button.find_element(By.XPATH, download_ledger_XPATH)
    time.sleep(random.randint(3, 8))
    driver.close()
