from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import logging
import pandas as pd
import os
from datetime import datetime
import smtplib

# Create a FileHandler with UTF-8 encoding
file_handler = logging.FileHandler("test_results.log", encoding="utf-8")

# Set the logging format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Ensure screenshots folder exists
screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)


# Function to Read Test Cases from Excel
def read_test_cases_from_excel(file_path):
    df = pd.read_excel(file_path, engine="openpyxl")  # Use openpyxl explicitly
    test_cases = df.to_dict(orient="records")  # Convert to list of dictionaries
    return test_cases


# Function to Log Results in CSV
def log_results_to_csv(domain, username, status, message, screenshot_path=""):
    log_file = "test_results.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = pd.DataFrame([[timestamp, domain, username, status, message, screenshot_path]],
                        columns=["Timestamp", "Domain", "Username", "Status", "Message", "Screenshot"])

    # Append data without rewriting the header
    if not os.path.exists(log_file):
        data.to_csv(log_file, index=False)
    else:
        data.to_csv(log_file, mode='a', header=False, index=False)


# Load test cases
test_cases = read_test_cases_from_excel("C:\\python\\learningselenium\\test_cases.xlsx")


# Function for Login Test
def login_test(domain, username, password, expected_url):
    driver = webdriver.Chrome()
    try:
        driver.get("https://demo.treds.in/rest/login")
        driver.maximize_window()

        # Input domain
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "domain"))).send_keys(domain)

        # Input username
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login"))).send_keys(username)

        # Click "Next"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnNext"))).click()
        sleep(1)

        # Click "Verify" button if exists
        verify_buttons = driver.find_elements(By.ID, "btnVerify")
        if verify_buttons:
            verify_buttons[0].click()
        sleep(1)

        # Use Password from Test Case
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(password)

        # Click "Login"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        # Answer security question (assuming "a" is the answer)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "securityAnswer0"))).send_keys("a")
        sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        # Wait for redirection and verify login success
        sleep(3)
        current_url = driver.current_url
        sleep(3)

        if expected_url in current_url:
            logging.info(f"Login successful for {username} with domain {domain}")
            log_results_to_csv(domain, username, "Success", "Login Successful")
        else:
            screenshot_path = os.path.join(screenshot_dir,
                                           f"login_failure_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.error(f"Login failed for {username} with domain {domain}. Screenshot saved: {screenshot_path}")
            log_results_to_csv(domain, username, "Failed", "URL Mismatch", screenshot_path)

    except Exception as e:
        screenshot_path = os.path.join(screenshot_dir,
                                       f"error_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        driver.save_screenshot(screenshot_path)
        logging.error(f"Error during login for {username}: {str(e)}. Screenshot saved: {screenshot_path}")
        log_results_to_csv(domain, username, "Error", str(e), screenshot_path)

    finally:
        driver.quit()


# Function to Send Email with Attachments
def send_email_with_multiple_attachments(subject, body, to, file_paths=None, cc=None, bcc=None):
    smtp_server = "smtp.gmail.com"
    port = 587  # TLS Port
    username = "satishgupta@apsit.edu.in"
    password = "aonw xhex ffxx zzhz"  # Replace with your App Password

    msg = MIMEMultipart()
    msg['From'] = username
    msg['Subject'] = subject
    msg['To'] = ", ".join(to) if isinstance(to, list) else to

    if cc:
        msg['Cc'] = ", ".join(cc)
    if bcc:
        msg['Bcc'] = ", ".join(bcc)  # BCC won't be visible in headers

    msg.attach(MIMEText(body, 'html'))

    # Attach files if provided
    if file_paths:
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
                msg.attach(part)
            else:
                logging.warning(f"⚠ File not found: {file_path}")

    # Send Email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(username, password)

        all_recipients = list(to if isinstance(to, list) else [to]) + \
                         list(cc if cc else []) + \
                         list(bcc if bcc else [])

        server.sendmail(username, all_recipients, msg.as_string())
        server.quit()

        logging.info("✅ Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        logging.error("❌ Authentication failed. Ensure you are using the correct App Password.")
    except smtplib.SMTPException as e:
        logging.error(f"❌ SMTP Error: {e}")
    except Exception as e:
        logging.error(f"❌ General Error: {e}")


# Run tests for each test case
for case in test_cases:
    login_test(case["Domain"], case["Username"], case["Password"], case["Expected_URL"])

# Send email only if failures or errors occurred
if os.path.exists("test_results.csv"):
    df_results = pd.read_csv("test_results.csv")
    if df_results["Status"].str.contains("Failed|Error").any():
        send_email_with_multiple_attachments(
            subject="Test Results - Failures Detected",
            body="Please find attached the test results.",
            to=["triptimall98@gmail.com","satishdineshgupta@gmail.com"],
            file_paths=["test_results.csv"]
        )
