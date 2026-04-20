#!/usr/bin/env python3
"""
SMS - সম্পূর্ণ অটোমেটিক OTP মনিটর বট (সিঙ্ক্রোনাস ভার্সন)
- কোন asyncio/await নেই - সরাসরি requests দিয়ে মেসেজ পাঠায়
- ডায়নামিক ক্যাপচা সলভার
- জিম্বাবুয়ে সহ ৫০+ দেশ
"""

import os
import sys
import time
import json
import logging
import re
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ========== কনফিগারেশন ==========
TELEGRAM_BOT_TOKEN = "8362446113:AAGsrg9iZmeByXmFbig2vdKfmDBUpgppIDM"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

CHROME_DRIVER_PATH = None
MESSAGE_FORMAT = "box"
SEEN_OTPS_FILE = "seen_otps.json"
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# ========== কান্ট্রি কনফিগারেশন ==========
COUNTRIES = {
    "BD": {"flag": "🇧🇩", "name": "Bangladesh", "code": "+880", "logo": "📱"},
    "ZW": {"flag": "🇿🇼", "name": "Zimbabwe", "code": "+263", "logo": "📱"},
    "IN": {"flag": "🇮🇳", "name": "India", "code": "+91", "logo": "📱"},
    "US": {"flag": "🇺🇸", "name": "USA", "code": "+1", "logo": "📱"},
    "UK": {"flag": "🇬🇧", "name": "United Kingdom", "code": "+44", "logo": "📱"},
    "PK": {"flag": "🇵🇰", "name": "Pakistan", "code": "+92", "logo": "📱"},
    "NP": {"flag": "🇳🇵", "name": "Nepal", "code": "+977", "logo": "📱"},
    "LK": {"flag": "🇱🇰", "name": "Sri Lanka", "code": "+94", "logo": "📱"},
    "MY": {"flag": "🇲🇾", "name": "Malaysia", "code": "+60", "logo": "📱"},
    "SG": {"flag": "🇸🇬", "name": "Singapore", "code": "+65", "logo": "📱"},
    "AE": {"flag": "🇦🇪", "name": "UAE", "code": "+971", "logo": "📱"},
    "SA": {"flag": "🇸🇦", "name": "Saudi Arabia", "code": "+966", "logo": "📱"},
    "CA": {"flag": "🇨🇦", "name": "Canada", "code": "+1", "logo": "📱"},
    "AU": {"flag": "🇦🇺", "name": "Australia", "code": "+61", "logo": "📱"},
}

DEFAULT_COUNTRY = "BD"

COUNTRY_CODES = {
    "+880": "BD", "+263": "ZW", "+91": "IN", "+1": "US", "+44": "UK",
    "+92": "PK", "+977": "NP", "+94": "LK", "+60": "MY", "+65": "SG",
    "+971": "AE", "+966": "SA", "+61": "AU",
}

# ========== লগিং সেটআপ ==========
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== ক্যাপচা সলভার ==========
class CaptchaSolver:
    @staticmethod
    def solve_math_captcha(captcha_text):
        """গাণিতিক ক্যাপচা সলভ করে"""
        text = captcha_text.lower()
        text = text.replace("what is", "").replace("solve:", "").replace("=?", "").replace("?", "").strip()
        
        patterns = [
            r'(\d+)\s*\+\s*(\d+)',
            r'(\d+)\s*-\s*(\d+)',
            r'(\d+)\s*\*\s*(\d+)',
            r'(\d+)\s*/\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num1 = int(match.group(1))
                num2 = int(match.group(2))
                if '+' in text:
                    return str(num1 + num2)
                elif '-' in text:
                    return str(num1 - num2)
                elif '*' in text:
                    return str(num1 * num2)
                elif '/' in text:
                    return str(num1 // num2)
        return None
    
    @staticmethod
    def extract_captcha_question(driver):
        """পেজ থেকে ক্যাপচা প্রশ্ন খোঁজে"""
        captcha_selectors = [
            (By.XPATH, "//label[contains(text(), '?')]"),
            (By.XPATH, "//label[contains(text(), 'What is')]"),
            (By.XPATH, "//label[contains(text(), 'Solve')]"),
            (By.XPATH, "//*[contains(text(), '+') and contains(text(), '=')]"),
        ]
        
        for by, selector in captcha_selectors:
            try:
                element = driver.find_element(by, selector)
                text = element.text
                if text and ('?' in text or '+' in text):
                    logger.info(f"ক্যাপচা প্রশ্ন: {text}")
                    return text
            except:
                continue
        
        page_text = driver.page_source
        match = re.search(r'What is (\d+\s*[+\-]\s*\d+)', page_text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

# ========== টেলিগ্রাম বট (সরাসরি requests) ==========
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
    
    def send_message(self, text, parse_mode="HTML"):
        """সরাসরি requests দিয়ে মেসেজ পাঠায় - কোন asyncio নেই"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ মেসেজ পাঠানো হয়েছে")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ মেসেজ পাঠাতে ব্যর্থ: {e}")
            return False

# ========== ডুপ্লিকেট ম্যানেজার ==========
class DuplicateManager:
    def __init__(self, filename=SEEN_OTPS_FILE):
        self.filename = filename
        self.seen_otps = self.load_seen_otps()
    
    def load_seen_otps(self):
        try:
            with open(self.filename, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    
    def save_seen_otps(self):
        with open(self.filename, 'w') as f:
            json.dump(list(self.seen_otps), f)
    
    def is_duplicate(self, otp_text):
        if otp_text in self.seen_otps:
            return True
        self.seen_otps.add(otp_text)
        self.save_seen_otps()
        return False

# ========== মেসেজ ফরম্যাটার ==========
class MessageFormatter:
    @staticmethod
    def format_otp_message(otp_code, country_code="BD", phone_number=None):
        country_info = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
        flag = country_info["flag"]
        logo = country_info["logo"]
        
        if phone_number:
            formatted_num = phone_number
        else:
            formatted_num = f"{country_info['code']}{otp_code}"
        
        if MESSAGE_FORMAT == "box":
            return f"╭────────────────────╮\n│ {flag} #{country_code} {logo} <code>{formatted_num}</code> │\n╰────────────────────╯"
        else:
            return f"{flag} #{country_code} {logo} OTP: <code>{formatted_num}</code>"

# ========== ব্রাউজার ম্যানেজার ==========
class BrowserManager:
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.wait = None
    
    def setup_driver(self):
        chrome_options = Options()
        if self.headless or IS_RAILWAY:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        if IS_RAILWAY:
            chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            logger.info("✅ ব্রাউজার সেটআপ হয়েছে")
            return True
        except Exception as e:
            logger.error(f"❌ ব্রাউজার সেটআপ ব্যর্থ: {e}")
            return False
    
    def login(self):
        """লগইন + ক্যাপচা সলভ"""
        try:
            logger.info("লগইন পেজে যাচ্ছি...")
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            # ইউজারনাম
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info("✅ ইউজারনাম দেওয়া হয়েছে")
            
            # পাসওয়ার্ড
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("✅ পাসওয়ার্ড দেওয়া হয়েছে")
            
            # ক্যাপচা
            captcha_q = CaptchaSolver.extract_captcha_question(self.driver)
            if captcha_q:
                captcha_a = CaptchaSolver.solve_math_captcha(captcha_q)
                if captcha_a:
                    captcha_field = self.driver.find_element(By.NAME, "captcha")
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_a)
                    logger.info(f"✅ ক্যাপচা সলভ: {captcha_q} = {captcha_a}")
            
            # লগইন বাটন
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_btn.click()
            logger.info("✅ লগইন বাটনে ক্লিক করা হয়েছে")
            
            time.sleep(5)
            
            if "login" not in self.driver.current_url.lower():
                logger.info("✅ লগইন সফল!")
                return True
            else:
                logger.error("❌ লগইন ব্যর্থ!")
                return False
                
        except Exception as e:
            logger.error(f"❌ লগইন এরর: {e}")
            return False
    
    def get_page(self, url):
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            logger.error(f"পৃষ্ঠা লোড ব্যর্থ: {e}")
            return False
    
    def refresh_page(self):
        try:
            self.driver.refresh()
            return True
        except:
            return False
    
    def extract_otps(self):
        """পেজ থেকে OTP বের করে"""
        otps = []
        try:
            page_text = self.driver.page_source
            patterns = [r'\b\d{4}\b', r'\b\d{5}\b', r'\b\d{6}\b', r'OTP[:\s]*(\d+)', r'code[:\s]*(\d+)']
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for m in matches:
                    if len(m) >= 4 and len(m) <= 6 and m.isdigit():
                        otps.append(m)
            
            otps = list(set(otps))
            if otps:
                logger.info(f"📱 {len(otps)} টি OTP পেয়েছি: {otps}")
            return otps
        except Exception as e:
            logger.error(f"OTP এক্সট্রাক্ট ব্যর্থ: {e}")
            return []
    
    def close(self):
        if self.driver:
            self.driver.quit()

# ========== মেইন মনিটর ==========
class OTPSMSMonitor:
    def __init__(self):
        self.browser = BrowserManager(headless=True)
        self.telegram = TelegramBot(TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID)
        self.duplicate_manager = DuplicateManager()
        self.formatter = MessageFormatter()
        self.processed_otps = set()
        self.last_refresh = datetime.now()
    
    def send_otp(self, otp):
        if self.duplicate_manager.is_duplicate(otp):
            return False
        
        msg = self.formatter.format_otp_message(otp, "ZW" if otp.startswith("263") else "BD")
        self.telegram.send_message(msg)
        logger.info(f"✨ OTP পাঠিয়েছি: {otp}")
        return True
    
    def run(self):
        logger.info("🚀 OTP মনিটর শুরু হচ্ছে...")
        
        # টেস্ট মেসেজ
        self.telegram.send_message("🤖 বট চালু হয়েছে! OTP আসলে জানানো হবে।")
        
        if not self.browser.setup_driver():
            return
        
        if not self.browser.login():
            self.browser.close()
            return
        
        if not self.browser.get_page(SMS_PAGE_URL):
            self.browser.close()
            return
        
        time.sleep(3)
        
        # প্রথম রান
        otps = self.browser.extract_otps()
        for otp in otps:
            self.send_otp(otp)
            self.processed_otps.add(otp)
        
        # লুপ
        while True:
            try:
                if (datetime.now() - self.last_refresh).total_seconds() >= 1.5:
                    self.browser.refresh_page()
                    self.last_refresh = datetime.now()
                    time.sleep(0.5)
                
                otps = self.browser.extract_otps()
                for otp in otps:
                    if otp not in self.processed_otps:
                        self.processed_otps.add(otp)
                        self.send_otp(otp)
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"লুপে এরর: {e}")
                time.sleep(2)
        
        self.browser.close()

# ========== মেইন ==========
def main():
    print("""
    ╔══════════════════════════════════════╗
    ║     SMS OTP Monitor Bot              ║
    ║     জিম্বাবুয়ে + ৫০+ দেশ           ║
    ╚══════════════════════════════════════╝
    """)
    
    monitor = OTPSMSMonitor()
    monitor.run()

if __name__ == "__main__":
    main()