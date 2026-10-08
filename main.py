from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

USERNAME = "kerbeus069"
PASSWORD = "zekrom21"

# Optional: keep browser open after script ends
options = Options()
options.add_experimental_option("detach", True)

def open_game():
    browser = webdriver.Chrome(options=options)
    browser.get("https://play.pokemonshowdown.com/")
    return browser


def wait_for_choose_name(browser):
    return WebDriverWait(browser, 15).until(
        lambda current_driver: next(
            (
                button
                for button in current_driver.find_elements(
                    By.XPATH,
                    "//button[@name='login' and "
                    "(normalize-space()='Choose username' or "
                    "normalize-space()='Choose name')]",
                )
                if button.is_displayed() and button.is_enabled()
            ),
            False,
        )
    )


driver = open_game()

try:
    choose_username = wait_for_choose_name(driver)
except NoSuchWindowException:
    driver = open_game()
    choose_username = wait_for_choose_name(driver)
choose_username.click()

username_field = WebDriverWait(driver, 15).until(
    EC.visibility_of_element_located(
        (By.XPATH, "//input[@name='username' or @placeholder='Username:']")
    )
)
username_field.send_keys(USERNAME)

confirm_username = WebDriverWait(driver, 15).until(
    lambda current_driver: next(
        (
            button
            for button in current_driver.find_elements(
                By.XPATH,
                "//*[contains(@class, 'buttonbar')]//button["
                "normalize-space()='Choose username' or "
                "normalize-space()='Choose name']",
            )
            if button.is_displayed() and button.is_enabled()
        ),
        False,
    )
)
confirm_username.click()

password_field = WebDriverWait(driver, 15).until(
    EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='password' or @placeholder='Password:']")
    )
)
password_field.send_keys(PASSWORD)

login_button = WebDriverWait(driver, 15).until(
    lambda current_driver: next(
        (
            button
            for button in current_driver.find_elements(
                By.XPATH,
                "//button[normalize-space()='Log in']"
            )
            if button.is_displayed() and button.is_enabled()
        ),
        False,
    )
)

print("Found login button:", login_button.text)

login_button.click()


# Keep the browser open long enough to see the result.
time.sleep(2)

# Uncomment the line below if you want to close the browser automatically
# driver.quit()