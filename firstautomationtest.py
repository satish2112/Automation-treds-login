from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep

def login_and_enter():
    # Initialize WebDriver (assuming ChromeDriver is in your PATH)
    driver = webdriver.Chrome()

    try:
        # Open the login page
        driver.get("https://uat.treds.in/rest/login")

        # Wait for the domain input field to be visible, then input domain
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "domain"))).send_keys("AC0000082")

        # Input the login username
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login"))).send_keys("ADMIN")

        # Click the "Next" button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnNext"))).click()

        # Pause briefly to ensure the next page loads
        sleep(1)

        # Input the password
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys("Rxil@2022")

        # Click the "Login" button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

        # Wait for the first page after login to load by checking for a dashboard heading or menu
        #WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "https://demo.treds.in/rest/home")))

        # Perform any interaction with the first page after login here
        # For example, let's click on the "Profile" button
        #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Profile"))).click()

        # Short wait to ensure the action completes
        sleep(3)

    finally:
        # Close the browser after finishing
        driver.quit()

# Call the function
login_and_enter()
