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


def WebCrawler(profile_path, profile_name, downloads_path, chromedriver_path):

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir = {profile_path}")
    options.add_argument(f"--profile-directory= {profile_name}")
    options.add_experimental_option("detach", True)

    prefs = {"download.default_directory": f"{downloads_path}"}
    options.add_experimental_option("prefs", prefs)

    # service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(options=options)

    # This inital navigation needs to come before setting cookies or a "invalid cookie domain" occurs.
    driver.get("https://plus.pokernow.club/")
    driver.maximize_window()
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        # Reload
        driver.get("https://plus.pokernow.club/")
    except Exception as e:
        print(e)
        print("No cookies to load")
        login = driver.find_element(By.XPATH, '//*[@id="content"]/a')
        login.click()

        # input username
        inputbox = driver.find_element(By.XPATH, '//*[@id="user_login_form_email"]')
        inputbox.send_keys("cheng.david04@gmail.com")

        # click button
        login_button = driver.find_element(
            By.XPATH, '//*[@id="new_user_login_form"]/input[3]'
        )
        login_button.click()

        # login with code
        code_to_input = input("Enter Code From Email:")
        confirmation_code_box = driver.find_element(
            By.XPATH, '//*[@id="user_login_code_form_code"]'
        )
        confirmation_code_box.send_keys(code_to_input)
        login_button2 = driver.find_element(
            By.XPATH, '//*[@id="new_user_login_code_form"]/input[3]'
        )
        login_button2.click()

    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    # once logged in, scrape all json files

    # table = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '(//table)[1]'))).get_attribute("outerHTML")
    # game_table = WebDriverWait(driver, 20).until(EC.vivisibility_of_element_located((By.XPATH, '//*[@id="myGames"]/tbody')))

    def get_game_table():
        # Wait until game_table loads
        while True:
            time.sleep(0.2)
            game_table = driver.find_elements(By.XPATH, '//*[@id="myGames"]/tbody/*')
            if len(game_table) > 0:
                return game_table

    def get_download_button():
        # Wait until Download button loads
        while True:
            time.sleep(0.2)
            try:
                return driver.find_element(By.XPATH, '//*[@id="rowJson"]/td[2]/a')
            except:
                pass

    game_table = get_game_table()
    for i in range(len(game_table)):
        # Have to retrieve the table each time because it refreshes on return (avoids stale element exception).
        # Command/Control clicking to open in new tab doesn't work either.
        ActionChains(driver).move_to_element(get_game_table()[i]).perform()
        get_game_table()[i].click()
        get_download_button().click()
        time.sleep(1)
        back_button = driver.find_element(By.XPATH, '//*[@id="pagetitle"]/div/div[1]/i')
        back_button.click()


profile_path = "/Users/cho/Library/Application Support/Google/Chrome"
profile_name = "Profile 2"
chromedriver_path = "/Users/cho/Desktop/PokerTracker/chromedriver-mac-x64/chromedriver"
downloads_path = "/Users/cho/Desktop/PokerTracker/logs"

WebCrawler(profile_path, profile_name, downloads_path, chromedriver_path)


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
