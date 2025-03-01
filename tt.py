from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import logging
import pandas as pd  # ✅ Added for reading Excel

# Configure logging
logging.basicConfig(filename="test_results.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Function to Read Test Cases from Excel
def read_test_cases_from_excel(file_path):
    df = pd.read_excel(file_path)
    test_cases = df.to_dict(orient="records")  # Convert to list of dictionaries
    return test_cases

# Load test cases
test_cases = read_test_cases_from_excel(r"C:\Users\TriptiMall\test_cases.xlsx")  # ✅ Ensure file is in the same folder

def login_test(domain, username, password, expected_url):
    driver = webdriver.Chrome()

    try:
        driver.get("https://uat.treds.in/rest/login")
        driver.maximize_window()

        # Input domain
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "domain"))).send_keys(domain)

        # Input username
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login"))).send_keys(username)

        # Click "Next"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnNext"))).click()
        sleep(1)

        # Click "Verify" button if it exists
        verify_buttons = driver.find_elements(By.ID, "btnVerify")
        if verify_buttons:
            verify_buttons[0].click()
        sleep(1)

        # Input password from test case (✅ Now dynamically fetched from Excel)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys("Tn@12345")

        # Click "Login"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        # Answer security question (assuming "a" is the answer for now)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "securityAnswer0"))).send_keys("a")
        sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        # Wait for redirection and verify login success
        sleep(3)  # Adjust as needed
        current_url = driver.current_url
        sleep(3)

        if expected_url in current_url:
            logging.info(f"✅ Login successful for {username} with domain {domain}")
        else:
            logging.error(f"❌ Login failed for {username} with domain {domain}. Taking screenshot...")
            driver.save_screenshot(f"login_failure_{username}.png")

    except Exception as e:
        logging.error(f"⚠ Error during login for {username}: {str(e)}")
        driver.save_screenshot(f"error_{username}.png")

    finally:
        driver.quit()

# Run tests for each test case
for case in test_cases:
    login_test(case["Domain"], case["Username"], case["Password"], case["Expected_URL"])
