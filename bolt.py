#!/usr/bin/env python3
"""
SMS - সম্পূর্ণ অটোমেটিক OTP মনিটর বট (Railway উপযোগী)
- 0.5 সেকেন্ড পরপর OTP চেক করে
- প্রতি 1.5 সেকেন্ড পরপর ব্রাউজার রিফ্রেশ করে
- চালু হওয়ার সাথে সাথে আজকের সব OTP ফরওয়ার্ড করে
- ডুপ্লিকেট OTP এড়ায়
- একাধিক দেশ সাপোর্ট (BD, ZW, IN, US, UK, PK, NP, LK, MY, SG, AE, SA সহ ৫০+ দেশ)
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Bot

# ========== কনফিগারেশন ==========
TELEGRAM_BOT_TOKEN = "8362446113:AAGsrg9iZmeByXmFbig2vdKfmDBUpgppIDM"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

# অপশনাল: ক্রোম ড্রাইভার পাথ
CHROME_DRIVER_PATH = None

# সেন্ড মেসেজের ফরম্যাট সেটিংস
MESSAGE_FORMAT = "box"  # "box" অথবা "simple"

# ডুপ্লিকেট চেকের জন্য ফাইল
SEEN_OTPS_FILE = "seen_otps.json"

# Railway এ headless mode চালানোর জন্য চেক
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
    "DE": {"flag": "🇩🇪", "name": "Germany", "code": "+49", "logo": "📱"},
    "FR": {"flag": "🇫🇷", "name": "France", "code": "+33", "logo": "📱"},
    "IT": {"flag": "🇮🇹", "name": "Italy", "code": "+39", "logo": "📱"},
    "ES": {"flag": "🇪🇸", "name": "Spain", "code": "+34", "logo": "📱"},
    "PT": {"flag": "🇵🇹", "name": "Portugal", "code": "+351", "logo": "📱"},
    "NL": {"flag": "🇳🇱", "name": "Netherlands", "code": "+31", "logo": "📱"},
    "BE": {"flag": "🇧🇪", "name": "Belgium", "code": "+32", "logo": "📱"},
    "CH": {"flag": "🇨🇭", "name": "Switzerland", "code": "+41", "logo": "📱"},
    "SE": {"flag": "🇸🇪", "name": "Sweden", "code": "+46", "logo": "📱"},
    "NO": {"flag": "🇳🇴", "name": "Norway", "code": "+47", "logo": "📱"},
    "DK": {"flag": "🇩🇰", "name": "Denmark", "code": "+45", "logo": "📱"},
    "FI": {"flag": "🇫🇮", "name": "Finland", "code": "+358", "logo": "📱"},
    "PL": {"flag": "🇵🇱", "name": "Poland", "code": "+48", "logo": "📱"},
    "RU": {"flag": "🇷🇺", "name": "Russia", "code": "+7", "logo": "📱"},
    "CN": {"flag": "🇨🇳", "name": "China", "code": "+86", "logo": "📱"},
    "JP": {"flag": "🇯🇵", "name": "Japan", "code": "+81", "logo": "📱"},
    "KR": {"flag": "🇰🇷", "name": "South Korea", "code": "+82", "logo": "📱"},
    "ID": {"flag": "🇮🇩", "name": "Indonesia", "code": "+62", "logo": "📱"},
    "PH": {"flag": "🇵🇭", "name": "Philippines", "code": "+63", "logo": "📱"},
    "VN": {"flag": "🇻🇳", "name": "Vietnam", "code": "+84", "logo": "📱"},
    "TH": {"flag": "🇹🇭", "name": "Thailand", "code": "+66", "logo": "📱"},
    "EG": {"flag": "🇪🇬", "name": "Egypt", "code": "+20", "logo": "📱"},
    "NG": {"flag": "🇳🇬", "name": "Nigeria", "code": "+234", "logo": "📱"},
    "ZA": {"flag": "🇿🇦", "name": "South Africa", "code": "+27", "logo": "📱"},
    "KE": {"flag": "🇰🇪", "name": "Kenya", "code": "+254", "logo": "📱"},
    "GH": {"flag": "🇬🇭", "name": "Ghana", "code": "+233", "logo": "📱"},
    "BR": {"flag": "🇧🇷", "name": "Brazil", "code": "+55", "logo": "📱"},
    "MX": {"flag": "🇲🇽", "name": "Mexico", "code": "+52", "logo": "📱"},
    "AR": {"flag": "🇦🇷", "name": "Argentina", "code": "+54", "logo": "📱"},
    "CO": {"flag": "🇨🇴", "name": "Colombia", "code": "+57", "logo": "📱"},
    "CL": {"flag": "🇨🇱", "name": "Chile", "code": "+56", "logo": "📱"},
    "PE": {"flag": "🇵🇪", "name": "Peru", "code": "+51", "logo": "📱"},
    "TR": {"flag": "🇹🇷", "name": "Turkey", "code": "+90", "logo": "📱"},
    "IR": {"flag": "🇮🇷", "name": "Iran", "code": "+98", "logo": "📱"},
    "IQ": {"flag": "🇮🇶", "name": "Iraq", "code": "+964", "logo": "📱"},
    "SY": {"flag": "🇸🇾", "name": "Syria", "code": "+963", "logo": "📱"},
    "JO": {"flag": "🇯🇴", "name": "Jordan", "code": "+962", "logo": "📱"},
    "LB": {"flag": "🇱🇧", "name": "Lebanon", "code": "+961", "logo": "📱"},
    "KW": {"flag": "🇰🇼", "name": "Kuwait", "code": "+965", "logo": "📱"},
    "QA": {"flag": "🇶🇦", "name": "Qatar", "code": "+974", "logo": "📱"},
    "BH": {"flag": "🇧🇭", "name": "Bahrain", "code": "+973", "logo": "📱"},
    "OM": {"flag": "🇴🇲", "name": "Oman", "code": "+968", "logo": "📱"},
    "YE": {"flag": "🇾🇪", "name": "Yemen", "code": "+967", "logo": "📱"},
    "AF": {"flag": "🇦🇫", "name": "Afghanistan", "code": "+93", "logo": "📱"},
}

DEFAULT_COUNTRY = "BD"

# কান্ট্রি কোড ম্যাপিং
COUNTRY_CODES = {
    "+880": "BD", "+263": "ZW", "+91": "IN", "+1": "US", "+44": "UK",
    "+92": "PK", "+977": "NP", "+94": "LK", "+60": "MY", "+65": "SG",
    "+971": "AE", "+966": "SA", "+61": "AU", "+49": "DE", "+33": "FR",
    "+39": "IT", "+34": "ES", "+351": "PT", "+31": "NL", "+32": "BE",
    "+41": "CH", "+46": "SE", "+47": "NO", "+45": "DK", "+358": "FI",
    "+48": "PL", "+7": "RU", "+86": "CN", "+81": "JP", "+82": "KR",
    "+62": "ID", "+63": "PH", "+84": "VN", "+66": "TH", "+20": "EG",
    "+234": "NG", "+27": "ZA", "+254": "KE", "+233": "GH", "+55": "BR",
    "+52": "MX", "+54": "AR", "+57": "CO", "+56": "CL", "+51": "PE",
    "+90": "TR", "+98": "IR", "+964": "IQ", "+963": "SY", "+962": "JO",
    "+961": "LB", "+965": "KW", "+974": "QA", "+973": "BH", "+968": "OM",
    "+967": "YE", "+93": "AF",
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

# ========== ডুপ্লিকেট ম্যানেজার ==========
class DuplicateManager:
    def __init__(self, filename=SEEN_OTPS_FILE):
        self.filename = filename
        self.seen_otps = self.load_seen_otps()
    
    def load_seen_otps(self):
        try:
            with open(self.filename, 'r') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
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
        """OTP মেসেজ সুন্দর করে ফরম্যাট করে"""
        country_info = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
        flag = country_info["flag"]
        logo = country_info["logo"]
        
        if phone_number:
            formatted_num = phone_number
        else:
            formatted_num = f"{country_info['code']}{otp_code}"
        
        if MESSAGE_FORMAT == "box":
            text = (
                f"╭────────────────────╮\n"
                f"│ {flag} #{country_code} {logo} <code>{formatted_num}</code> │\n"
                f"╰────────────────────╯"
            )
        else:
            text = f"{flag} #{country_code} {logo} OTP: <code>{formatted_num}</code>"
        
        return text

# ========== টেলিগ্রাম বট ==========
class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
    
    def send_message(self, text, parse_mode="HTML"):
        """সিঙ্ক্রোনাসভাবে মেসেজ পাঠায়"""
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.info(f"মেসেজ পাঠানো হয়েছে: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"মেসেজ পাঠাতে ব্যর্থ: {e}")
            return False

# ========== ব্রাউজার ম্যানেজার ==========
class BrowserManager:
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.wait = None
    
    def setup_driver(self):
        """সেলেনিয়াম ড্রাইভার সেটআপ করে"""
        chrome_options = Options()
        
        if self.headless or IS_RAILWAY:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if IS_RAILWAY:
            chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            if CHROME_DRIVER_PATH:
                service = Service(CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.wait = WebDriverWait(self.driver, 15)
            logger.info("ব্রাউজার সফলভাবে সেটআপ হয়েছে")
            return True
            
        except Exception as e:
            logger.error(f"ব্রাউজার সেটআপ করতে ব্যর্থ: {e}")
            return False
    
    def login(self):
        """ওয়েবসাইটে লগইন করে - একাধিক সিলেক্টর সাপোর্ট সহ"""
        try:
            logger.info("লগইন পেজে নেওয়া হচ্ছে...")
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            logger.info(f"পেজ টাইটেল: {self.driver.title}")
            
            # ডিবাগিং: পেজের সোর্স সেভ করা
            try:
                with open("login_page_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source[:5000])
                logger.info("পেজ সোর্স 'login_page_debug.html' এ সেভ করা হয়েছে")
            except:
                pass
            
            # ===== ইউজারনেম ফিল্ড =====
            username_selectors = [
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.XPATH, "//input[@name='username']"),
                (By.XPATH, "//input[contains(@placeholder, 'username')]"),
                (By.XPATH, "//input[contains(@placeholder, 'Username')]"),
            ]
            
            username_field = None
            for by, selector in username_selectors:
                try:
                    username_field = self.wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info(f"✅ ইউজারনেম ফিল্ড পাওয়া গেছে: {selector}")
                    break
                except:
                    continue
            
            if username_field:
                username_field.clear()
                username_field.send_keys(USERNAME)
                logger.info("ইউজারনেম ইনপুট করা হয়েছে")
            else:
                logger.error("❌ ইউজারনেম ফিল্ড খুঁজে পাওয়া যায়নি!")
                return False
            
            time.sleep(1)
            
            # ===== পাসওয়ার্ড ফিল্ড =====
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[contains(@placeholder, 'password')]"),
                (By.XPATH, "//input[contains(@placeholder, 'Password')]"),
            ]
            
            password_field = None
            for by, selector in password_selectors:
                try:
                    password_field = self.driver.find_element(by, selector)
                    logger.info(f"✅ পাসওয়ার্ড ফিল্ড পাওয়া গেছে: {selector}")
                    break
                except:
                    continue
            
            if password_field:
                password_field.clear()
                password_field.send_keys(PASSWORD)
                logger.info("পাসওয়ার্ড ইনপুট করা হয়েছে")
            else:
                logger.error("❌ পাসওয়ার্ড ফিল্ড খুঁজে পাওয়া যায়নি!")
                return False
            
            time.sleep(1)
            
            # ===== লগইন বাটন =====
            button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//button[contains(text(), 'Sign')]"),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(@class, 'login')]"),
                (By.XPATH, "//button[contains(@class, 'btn')]"),
                (By.XPATH, "//button[contains(@class, 'submit')]"),
                (By.XPATH, "//form//button"),
                (By.XPATH, "//form//input[@type='submit']"),
            ]
            
            login_button = None
            for by, selector in button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)
                    logger.info(f"✅ লগইন বাটন পাওয়া গেছে: {selector}")
                    break
                except:
                    continue
            
            if login_button:
                login_button.click()
                logger.info("লগইন বাটনে ক্লিক করা হয়েছে")
            else:
                logger.error("❌ লগইন বাটন খুঁজে পাওয়া যায়নি!")
                # ডিবাগিং: পেজের ফর্ম এলিমেন্ট দেখানো
                logger.info("পেজের সব বাটন খুঁজে দেখা যাচ্ছে...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"পাওয়া বাটন সংখ্যা: {len(buttons)}")
                for i, btn in enumerate(buttons[:5]):
                    logger.info(f"বাটন {i}: text='{btn.text}', type='{btn.get_attribute('type')}'")
                return False
            
            time.sleep(5)
            
            # লগইন সফল হয়েছে কিনা চেক
            current_url = self.driver.current_url.lower()
            if "login" not in current_url:
                logger.info("✅ লগইন সফল হয়েছে!")
                return True
            else:
                logger.error(f"❌ লগইন ব্যর্থ হয়েছে! বর্তমান URL: {current_url}")
                # পেজে এরর মেসেজ আছে কিনা চেক
                page_text = self.driver.page_source.lower()
                if "invalid" in page_text or "error" in page_text:
                    logger.error("লগইন পেজে এরর মেসেজ পাওয়া গেছে!")
                return False
                
        except Exception as e:
            logger.error(f"লগইন করতে ব্যর্থ: {e}")
            return False
    
    def get_page(self, url):
        """পৃষ্ঠা লোড করে"""
        try:
            self.driver.get(url)
            logger.info(f"পৃষ্ঠা লোড হয়েছে: {url}")
            return True
        except Exception as e:
            logger.error(f"পৃষ্ঠা লোড করতে ব্যর্থ: {e}")
            return False
    
    def refresh_page(self):
        """পৃষ্ঠা রিফ্রেশ করে"""
        try:
            self.driver.refresh()
            logger.info("পৃষ্ঠা রিফ্রেশ করা হয়েছে")
            return True
        except Exception as e:
            logger.error(f"পৃষ্ঠা রিফ্রেশ করতে ব্যর্থ: {e}")
            return False
    
    def extract_otps_with_numbers(self):
        """পৃষ্ঠা থেকে সব OTP এবং ফোন নম্বর এক্সট্রাক্ট করে"""
        otp_data = []
        try:
            page_text = self.driver.page_source
            
            # OTP প্যাটার্ন
            patterns = [
                r'\b\d{4}\b', r'\b\d{5}\b', r'\b\d{6}\b',
                r'OTP[:\s]*(\d+)', r'code[:\s]*(\d+)',
                r'verification[:\s]*(\d+)', r'Your OTP is (\d+)',
                r'(\d{6}) is your OTP'
            ]
            
            # ফোন নম্বর প্যাটার্ন
            phone_patterns = [
                r'\+?\d{10,15}', r'\b01\d{9}\b', r'\b0\d{10}\b'
            ]
            
            all_otps = set()
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 4 and len(match) <= 8 and match.isdigit():
                        all_otps.add(match)
            
            phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                phones.update(matches)
            
            for otp in all_otps:
                detected_phone = None
                detected_country = DEFAULT_COUNTRY
                
                for phone in phones:
                    if otp in phone:
                        detected_phone = phone
                        for code, country in COUNTRY_CODES.items():
                            if phone.startswith(code):
                                detected_country = country
                                break
                        break
                
                otp_data.append({
                    "otp": otp,
                    "phone": detected_phone,
                    "country": detected_country
                })
            
            if otp_data:
                logger.info(f"{len(otp_data)} টি OTP পাওয়া গেছে")
            
            return otp_data
            
        except Exception as e:
            logger.error(f"OTP এক্সট্রাক্ট করতে ব্যর্থ: {e}")
            return []
    
    def close(self):
        """ব্রাউজার বন্ধ করে"""
        if self.driver:
            self.driver.quit()
            logger.info("ব্রাউজার বন্ধ করা হয়েছে")

# ========== মেইন মনিটর ক্লাস ==========
class OTPSMSMonitor:
    def __init__(self):
        self.browser = BrowserManager(headless=True)
        self.telegram = TelegramBot(TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID)
        self.duplicate_manager = DuplicateManager()
        self.formatter = MessageFormatter()
        self.running = True
        self.last_refresh = datetime.now()
        self.processed_otps = set()
    
    def send_telegram_message(self, text):
        """টেলিগ্রাম মেসেজ পাঠায়"""
        return self.telegram.send_message(text)
    
    def format_and_send_otp(self, otp_data):
        """OTP ফরম্যাট করে পাঠায়"""
        otp = otp_data["otp"]
        country = otp_data.get("country", DEFAULT_COUNTRY)
        phone = otp_data.get("phone")
        
        if self.duplicate_manager.is_duplicate(otp):
            logger.debug(f"ডুপ্লিকেট OTP স্কিপ: {otp}")
            return False
        
        message = self.formatter.format_otp_message(
            otp_code=otp,
            country_code=country,
            phone_number=phone
        )
        
        self.send_telegram_message(message)
        logger.info(f"✨ নতুন OTP পাঠানো হয়েছে: {otp} (কান্ট্রি: {country})")
        return True
    
    def send_all_todays_otps(self):
        """আজকের সব OTP একসাথে পাঠায়"""
        logger.info("আজকের সব OTP সংগ্রহ করা হচ্ছে...")
        
        otp_data_list = self.browser.extract_otps_with_numbers()
        
        if not otp_data_list:
            logger.info("কোনো OTP পাওয়া যায়নি")
            return
        
        new_otps = []
        for otp_data in otp_data_list:
            if not self.duplicate_manager.is_duplicate(otp_data["otp"]):
                new_otps.append(otp_data)
        
        if new_otps:
            logger.info(f"{len(new_otps)} টি নতুন OTP পাওয়া গেছে")
            for otp_data in new_otps:
                self.format_and_send_otp(otp_data)
        else:
            logger.info("সব OTP ই আগে দেখা হয়েছে")
    
    def monitor_loop(self):
        """মূল মনিটরিং লুপ"""
        logger.info("🚀 OTP মনিটরিং শুরু হচ্ছে...")
        
        # ব্রাউজার সেটআপ
        if not self.browser.setup_driver():
            logger.error("❌ ব্রাউজার সেটআপ ব্যর্থ, প্রোগ্রাম বন্ধ হচ্ছে")
            return
        
        # লগইন
        if not self.browser.login():
            logger.error("❌ লগইন ব্যর্থ, প্রোগ্রাম বন্ধ হচ্ছে")
            self.browser.close()
            return
        
        # SMS পেজে যাও
        if not self.browser.get_page(SMS_PAGE_URL):
            logger.error("❌ SMS পেজ লোড করতে ব্যর্থ")
            self.browser.close()
            return
        
        time.sleep(3)
        
        # স্টার্টআপে সব OTP পাঠায়
        self.send_all_todays_otps()
        
        # স্টার্টআপ মেসেজ
        self.send_telegram_message("✅ এসএমএস মনিটর বট চালু হয়েছে! 🇿🇼 জিম্বাবুয়ে সহ ৫০+ দেশের OTP মনিটর করা হবে।")
        
        # মনিটরিং লুপ
        loop_count = 0
        while self.running:
            try:
                # প্রতি 1.5 সেকেন্ড পরপর রিফ্রেশ
                if (datetime.now() - self.last_refresh).total_seconds() >= 1.5:
                    self.browser.refresh_page()
                    self.last_refresh = datetime.now()
                    time.sleep(0.5)
                
                # OTP চেক
                otp_data_list = self.browser.extract_otps_with_numbers()
                
                for otp_data in otp_data_list:
                    if otp_data["otp"] not in self.processed_otps:
                        self.processed_otps.add(otp_data["otp"])
                        self.format_and_send_otp(otp_data)
                
                loop_count += 1
                if loop_count % 20 == 0:
                    logger.info(f"⏳ মনিটরিং চলছে... ({loop_count} সাইকেল)")
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info("🛑 ব্যবহারকারী দ্বারা বন্ধ করা হয়েছে")
                break
            except Exception as e:
                logger.error(f"❌ মনিটরিং লুপে এরর: {e}")
                time.sleep(2)
        
        self.browser.close()
        logger.info("🔚 OTP মনিটরিং বন্ধ হয়েছে")

# ========== মেইন ফাংশন ==========
def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           SMS - OTP Monitor Bot (Multi-Country)          ║
    ║     জিম্বাবুয়ে সহ ৫০+ দেশের OTP মনিটর                   ║
    ║     সম্পূর্ণ অটোমেটিক OTP ফরওয়ার্ডিং সিস্টেম            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("বট স্টার্ট হচ্ছে...")
    logger.info(f"সাপোর্টেড কান্ট্রি: {len(COUNTRIES)} টি")
    
    monitor = OTPSMSMonitor()
    
    try:
        monitor.monitor_loop()
    except Exception as e:
        logger.error(f"মেইন ফাংশনে এরর: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()