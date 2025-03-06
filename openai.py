import openai
import os
import pandas as pd
from datetime import datetime
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
import smtplib

# ✅ OpenAI API Key
openai.api_key = "your_openai_api_key"  # Replace with your actual API key

# ✅ Email Credentials
EMAIL_USERNAME = "satishgupta@apsit.edu.in"
EMAIL_PASSWORD = "aonw xhex ffxx zzhz"  # Replace with your App Password

# ✅ Logging setup
file_handler = logging.FileHandler("test_results.log", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# ✅ Ensure screenshots folder exists
screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)


# 🔹 Function to Generate Test Cases Using OpenAI
def generate_test_cases(feature_description):
    prompt = f"Generate test cases for the following feature:\n\nFeature: {feature_description}\n\nInclude positive and negative test cases with expected results."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        test_cases_text = response['choices'][0]['message']['content']
        print("Generated Test Cases:\n", test_cases_text)

        # Save test cases to CSV
        test_cases = test_cases_text.split("\n")
        test_cases_data = []
        for line in test_cases:
            if "Test Case" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    test_cases_data.append([parts[0], parts[1]])

        df = pd.DataFrame(test_cases_data, columns=["Test Case", "Description"])
        df.to_csv("generated_test_cases.csv", index=False)
        return df

    except Exception as e:
        logging.error(f"❌ Error generating test cases: {str(e)}")
        return None


# 🔹 Function to Read Test Cases from CSV
def read_test_cases(file_path):
    if not os.path.exists(file_path):
        logging.error("❌ Test cases file not found!")
        return []

    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")


# 🔹 Function to Log Results in CSV
def log_results_to_csv(test_case, status, message, screenshot_path=""):
    log_file = "test_results.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = pd.DataFrame([[timestamp, test_case, status, message, screenshot_path]],
                        columns=["Timestamp", "Test Case", "Status", "Message", "Screenshot"])

    if not os.path.exists(log_file):
        data.to_csv(log_file, index=False)
    else:
        data.to_csv(log_file, mode='a', header=False, index=False)


# 🔹 Function for Login Test
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

        # Answer security question
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "securityAnswer0"))).send_keys("a")
        sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        # Verify login success
        sleep(3)
        current_url = driver.current_url
        sleep(3)

        if expected_url in current_url:
            logging.info(f"✅ Login successful for {username}")
            log_results_to_csv(username, "Success", "Login Successful")
        else:
            screenshot_path = os.path.join(screenshot_dir, f"login_failure_{username}.png")
            driver.save_screenshot(screenshot_path)
            logging.error(f"❌ Login failed for {username}. Screenshot saved: {screenshot_path}")
            log_results_to_csv(username, "Failed", "URL Mismatch", screenshot_path)

    except Exception as e:
        screenshot_path = os.path.join(screenshot_dir, f"error_{username}.png")
        driver.save_screenshot(screenshot_path)
        logging.error(f"❌ Error during login for {username}: {str(e)}. Screenshot saved: {screenshot_path}")
        log_results_to_csv(username, "Error", str(e), screenshot_path)

    finally:
        driver.quit()


# 🔹 Function to Send Email with Test Report
def send_email_with_attachments(subject, body, to, file_paths=None):
    smtp_server = "smtp.gmail.com"
    port = 587

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['Subject'] = subject
    msg['To'] = ", ".join(to) if isinstance(to, list) else to

    msg.attach(MIMEText(body, 'html'))

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

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, to, msg.as_string())
        server.quit()
        logging.info("✅ Email sent successfully.")
    except Exception as e:
        logging.error(f"❌ Email Error: {e}")


# 🔹 Run Test Case Generation
test_cases_df = generate_test_cases("Login functionality with domain, username, password, and security question.")

# 🔹 Run Tests for Each Test Case
test_cases = read_test_cases("generated_test_cases.csv")
for case in test_cases:
    login_test(case["Test Case"], case["Description"], "password123", "https://demo.treds.in/dashboard")

# 🔹 Send Test Results Email
if os.path.exists("test_results.csv"):
    send_email_with_attachments(
        subject="Test Results Report",
        body="Please find attached the test results.",
        to=["triptimall98@gmail.com"],
        file_paths=["test_results.csv"]
    )