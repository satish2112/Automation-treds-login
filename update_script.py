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
from openai import OpenAIError # ✅ Correct error handling

# ✅ Secure API Key Handling
openai.api_key = os.getenv("")  # Store in environment variable

# ✅ Secure Email Credentials
EMAIL_USERNAME = "satishgupta@apsit.edu.in"
EMAIL_PASSWORD = os.getenv("aonw xhex ffxx zzhz")  # Store password securely

# ✅ Logging setup
logging.basicConfig(filename="test_results.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Ensure screenshot directory exists
screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)


# 🔹 Function to Generate AI Test Cases
def generate_test_cases(feature_description):
    prompt = f"Generate test cases for:\n\nFeature: {feature_description}\n\nInclude positive and negative test cases."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        test_cases_text = response['choices'][0]['message']['content']
        test_cases_data = []

        # ✅ Parse test cases robustly
        for line in test_cases_text.split("\n"):
            parts = line.split("|")
            if len(parts) == 3:  # Expecting "Test Case | Input | Expected Output"
                test_cases_data.append(parts)

        if not test_cases_data:
            logging.error("❌ No valid test cases found!")
            return None

        # ✅ Save test cases
        df = pd.DataFrame(test_cases_data, columns=["Test Case", "Input", "Expected Output"])
        df.to_csv("generated_test_cases.csv", index=False)
        return df

    except OpenAIError as e:
        logging.error(f"❌ OpenAI API Error: {str(e)}")
        return None


# 🔹 Function to Run Login Test
def login_test(domain, username, password, expected_url):
    driver = webdriver.Chrome()
    try:
        driver.get("https://demo.treds.in/rest/login")
        driver.maximize_window()

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "domain"))).send_keys(domain)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnNext"))).click()
        sleep(1)

        verify_buttons = driver.find_elements(By.ID, "btnVerify")
        if verify_buttons:
            verify_buttons[0].click()
        sleep(1)

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "securityAnswer0"))).send_keys("a")
        sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        sleep(1)

        sleep(3)
        current_url = driver.current_url
        sleep(3)

        if expected_url in current_url:
            logging.info(f"✅ Login successful for {username}")
        else:
            screenshot_path = os.path.join(screenshot_dir, f"login_failure_{username}.png")
            driver.save_screenshot(screenshot_path)
            logging.error(f"❌ Login failed for {username}. Screenshot saved: {screenshot_path}")

    except Exception as e:
        screenshot_path = os.path.join(screenshot_dir, f"error_{username}.png")
        driver.save_screenshot(screenshot_path)
        logging.error(f"❌ Error during login for {username}: {str(e)}. Screenshot saved: {screenshot_path}")

    finally:
        driver.quit()


# 🔹 Function to Send Email
def send_email_with_attachments(subject, body, to, file_paths=None):
    smtp_server = "smtp.gmail.com"
    port = 587

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['Subject'] = subject
    msg['To'] = ", ".join(to) if isinstance(to, list) else to
    msg.attach(MIMEText(body, 'html'))

    if os.path.exists("test_results.csv"):
        df_results = pd.read_csv("test_results.csv")
        if df_results["Status"].str.contains("Failed|Error").any():
            send_email_with_attachments(
                subject="Test Results - Failures Detected",
                body="Please find attached the test results.",
                to=["triptimall98@gmail.com","satishdineshgupta@gmail.com"],
                file_paths=["test_results.csv"]
            )

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, to, msg.as_string())
        server.quit()
        logging.info("✅ Email sent successfully.")
    except Exception as e:
        logging.error(f"❌ Email Error: {e}")


# ✅ Run AI Test Case Generation
generate_test_cases("Login Page with username, domain, password, and security question.")
