from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pickle

import time 
import random


def WebCrawler(profile_path, profile_name, downloads_path, chromedriver_path):

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir = {profile_path}")    
    options.add_argument(f"--profile-directory= {profile_name}")
    options.add_experimental_option('detach', True)

    prefs = {"download.default_directory" : f"{downloads_path}"}
    options.add_experimental_option("prefs",prefs)
    
    #service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(options=options)

    # This inital navigation needs to come before setting cookies or a "invalid cookie domain" occurs.
    driver.get('https://plus.pokernow.club/')
    driver.maximize_window()
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        # Reload
        driver.get('https://plus.pokernow.club/')
    except Exception as e:
        print(e)
        print("No cookies to load")
        login = driver.find_element(By.XPATH, '//*[@id="content"]/a')
        login.click()

        #input username 
        inputbox = driver.find_element(By.XPATH, '//*[@id="user_login_form_email"]')
        inputbox.send_keys('cheng.david04@gmail.com')
        
        #click button 
        login_button = driver.find_element(By.XPATH, '//*[@id="new_user_login_form"]/input[3]')
        login_button.click()

        #login with code 
        code_to_input = input('Enter Code From Email:')
        confirmation_code_box = driver.find_element(By.XPATH, '//*[@id="user_login_code_form_code"]')
        confirmation_code_box.send_keys(code_to_input)
        login_button2 = driver.find_element(By.XPATH, '//*[@id="new_user_login_code_form"]/input[3]')
        login_button2.click()
    

    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    # once logged in, scrape all json files 

    #table = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '(//table)[1]'))).get_attribute("outerHTML")
    #game_table = WebDriverWait(driver, 20).until(EC.vivisibility_of_element_located((By.XPATH, '//*[@id="myGames"]/tbody')))

    time.sleep(5)
    game_table = driver.find_elements(By.XPATH, '//*[@id="myGames"]/tbody/*')

    for i in range(1, len(game_table) + 1): 
        time.sleep(1)
        game_table[i].click()
        time.sleep(1)
        download_button = driver.find_element(By.XPATH, '//*[@id="rowJson"]/td[2]/a')
        download_button.click()
        back_button = driver.find_element(By.XPATH, '//*[@id="pagetitle"]/div/div[1]/i')
        back_button.click()
        


profile_path = '/Users/cho/Library/Application Support/Google/Chrome'
profile_name = 'Profile 2'
chromedriver_path = '/Users/cho/Desktop/PokerTracker/chromedriver-mac-x64/chromedriver'
downloads_path = '/Users/cho/Desktop/PokerTracker/logs'

WebCrawler(profile_path, profile_name, downloads_path, chromedriver_path)






# def DownloadLedger(url: str, downloads_path: str, chromedriver_path: str):
#     """
#     Automatically download CSV with logs, names by providing a csv URL

#     INPUTS:
#     ------

#     url - (str) url for ledger you wish to download
#     downloads_path - (str) path to send downloaded csv files
#     chromedriver_path - (str) path where webdriver for google chrome is located.
#     """
#     # initialize path for downloads and chrome driver
#     options = webdriver.ChromeOptions()
#     prefs = {"download.default_directory": downloads_path}
#     options.add_experimental_option("prefs", prefs)
#     driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
#     driver.get(url)
#     driver.maximize_window()

#     # specified XPath for buttons of interest
#     bottom_button_XPATH = "/html/body/div/div/div[1]/div[3]/div[6]"
#     ledger_button_XPATH = (
#         "/html/body/div[1]/div/div[1]/div[3]/div[2]/div/div[2]/div[2]/button[3]"
#     )
#     download_ledger_XPATH = (
#         "/html/body/div/div/div[1]/div[3]/div[2]/div/div[2]/div[2]/div"
#     )

#     # click first button for showing modal overlay
#     bottom_button = driver.find_element(By.XPATH, bottom_button_XPATH)
#     bottom_button.click()

#     # click ledger button in modal overlay
#     ledger_button = bottom_button.find_element(By.XPATH, ledger_button_XPATH)
#     ledger_button.click()
    

#     # download the ledger csv
#     download_ledger = ledger_button.find_element(By.XPATH, download_ledger_XPATH)
#     time.sleep(random.randint(3,8))
#     driver.close()




# # step 1: log in 
# # step 2: nagivate to https://plus.pokernow.club 
# # step 3: select path 
# def scrape_json():  
#     driver = webdriver.Chrome()
        
#     # select table 
#     games = driver.find_elements_by_xpath('//*[@id="myGames"]/tbody')
#     for i in range(1, len(games) + 1): 

#         games[i].click() 
#         time.sleep(random.randint(1,8))

        

#     # step 3.1 - click //*[@id="myGames"]/tbody/tr[1]
#     # step 3.2 - click download 
#     # step 3.3 - click back to table and go to next element 

    
    
    