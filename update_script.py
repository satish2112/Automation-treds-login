import os
import logging
import smtplib
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
api_key_env = os.getenv('GOOGLE_API_KEY')

genai.configure(api_key=api_key_env)
model = genai.GenerativeModel("gemini-1.5-pro-latest")


# ✅ Function to Send Email with Attachments
def send_email_with_attachments(subject, body, to, file_paths=None):
    logging.info("📧 Preparing to send email...")
    smtp_server = "smtp.gmail.com"
    port = 587
    username = "satishgupta@apsit.edu.in"
    password = "aonw xhex ffxx zzhz"  # ⚠️ Use app password for security

    msg = MIMEMultipart()
    msg['From'] = username
    msg['Subject'] = subject
    msg['To'] = ", ".join(to) if isinstance(to, list) else to
    msg.attach(MIMEText(body, 'html'))

    if file_paths:
        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
                msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, to, msg.as_string())
        server.quit()
        logging.info("✅ Email sent successfully.")
    except Exception as e:
        logging.error(f"❌ Email Error: {e}")


# ✅ Function to Test Login
def login_test(domain, username, password, expected_outcome):
    logging.info(f"🔍 Running login test for {username}")
    driver = webdriver.Chrome()
    os.makedirs("screenshots", exist_ok=True)

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
        sleep(3)

        current_url = driver.current_url
        if expected_outcome.lower() in current_url.lower():
            logging.info(f"✅ Login successful for {username} with domain {domain}")
        else:
            screenshot_path = os.path.join("screenshots",
                                           f"failure_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(screenshot_path)
            logging.error(f"❌ Login failed for {username}. Screenshot saved: {screenshot_path}")
    except Exception as e:
        logging.error(f"❌ Error during login for {username}: {str(e)}")
    finally:
        driver.quit()


# ✅ AI-Powered Test Case Generation
def generate_test_cases():
    if model is None:
        logging.error("❌ AI model not initialized.")
        return

    logging.info("🤖 Generating test cases using AI...")
    prompt = """
    Generate at least 5 test cases for login functionality.
    Include positive and negative scenarios.
    Provide test cases in the format:
    Domain,Username,Password,Expected Outcome
    """

    try:
        response = model.generate_content(prompt)
        if response and response.text:
            logging.info("✅ AI-generated test cases received.")
            test_cases_file = "generated_test_cases.csv"

            # Ensure correct CSV format
            lines = response.text.split('\n')
            formatted_lines = [line.replace('|', ',').strip() for line in lines if line.count(',') == 3]

            if len(formatted_lines) > 1:
                with open(test_cases_file, "w") as f:
                    f.write('\n'.join(formatted_lines))
                logging.info(f"✅ Test cases saved in {test_cases_file}")
            else:
                logging.error("❌ AI did not return valid test cases.")
        else:
            logging.error("❌ AI failed to generate test cases.")
    except Exception as e:
        logging.error(f"❌ Error generating test cases: {str(e)}")


# ✅ Execute Tests
def main():
    logging.info("🚀 Starting automation script...")
    generate_test_cases()

    if os.path.exists("generated_test_cases.csv"):
        try:
            test_cases = pd.read_csv("generated_test_cases.csv").to_dict(orient="records")
            for case in test_cases:
                login_test(case["Domain"], case["Username"], case["Password"], case["Expected Outcome"])
        except pd.errors.ParserError:
            logging.error("❌ CSV formatting error. Please check the AI-generated file.")

    if os.path.exists("generated_test_cases.csv"):
        send_email_with_attachments(
            subject="Automated Test Case Execution Report",
            body="Please find attached the generated test cases.",
            to=["triptimall98@gmail.com","satishdineshgupta@gmail.com"],
            file_paths=["generated_test_cases.csv"]
        )


if __name__ == "__main__":
    main()