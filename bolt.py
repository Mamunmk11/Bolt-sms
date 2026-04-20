#!/usr/bin/env python3
"""
SMS - সম্পূর্ণ অটোমেটিক OTP মনিটর বট (Railway উপযোগী)
- 0.5 সেকেন্ড পরপর OTP চেক করে
- প্রতি 1.5 সেকেন্ড পরপর ব্রাউজার রিফ্রেশ করে
- চালু হওয়ার সাথে সাথে আজকের সব OTP ফরওয়ার্ড করে
- ডুপ্লিকেট OTP এড়ায়
- একাধিক দেশ সাপোর্ট (BD, ZW, IN, US, UK, PK, NP, LK, MY, SG, AE, SA)
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

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

# ডিফল্ট কান্ট্রি
DEFAULT_COUNTRY = "BD"

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

# ========== কান্ট্রি ডিটেক্টর ==========
class CountryDetector:
    @staticmethod
    def detect_country_from_number(phone_number):
        """ফোন নম্বর থেকে কান্ট্রি ডিটেক্ট করে"""
        if not phone_number:
            return DEFAULT_COUNTRY
        
        # নম্বর থেকে কোড বের করা
        for code, country in COUNTRY_CODES.items():
            if phone_number.startswith(code):
                return country
        return DEFAULT_COUNTRY
    
    @staticmethod
    def detect_country_from_text(text):
        """টেক্সট থেকে কান্ট্রি ডিটেক্ট করে"""
        text_lower = text.lower()
        
        # কান্ট্রি নাম চেক
        for country_code, info in COUNTRIES.items():
            if info["name"].lower() in text_lower:
                return country_code
        
        # জিম্বাবুয়ের জন্য স্পেশাল চেক
        if "zimbabwe" in text_lower or "zw" in text_lower:
            return "ZW"
        
        return DEFAULT_COUNTRY

# কান্ট্রি কোড ম্যাপিং (ফোন নম্বরের জন্য)
COUNTRY_CODES = {
    "+880": "BD",
    "+263": "ZW",
    "+91": "IN",
    "+1": "US",
    "+44": "UK",
    "+92": "PK",
    "+977": "NP",
    "+94": "LK",
    "+60": "MY",
    "+65": "SG",
    "+971": "AE",
    "+966": "SA",
    "+61": "AU",
    "+49": "DE",
    "+33": "FR",
    "+39": "IT",
    "+34": "ES",
    "+351": "PT",
    "+31": "NL",
    "+32": "BE",
    "+41": "CH",
    "+46": "SE",
    "+47": "NO",
    "+45": "DK",
    "+358": "FI",
    "+48": "PL",
    "+7": "RU",
    "+86": "CN",
    "+81": "JP",
    "+82": "KR",
    "+62": "ID",
    "+63": "PH",
    "+84": "VN",
    "+66": "TH",
    "+20": "EG",
    "+234": "NG",
    "+27": "ZA",
    "+254": "KE",
    "+233": "GH",
    "+55": "BR",
    "+52": "MX",
    "+54": "AR",
    "+57": "CO",
    "+56": "CL",
    "+51": "PE",
    "+90": "TR",
    "+98": "IR",
    "+964": "IQ",
    "+963": "SY",
    "+962": "JO",
    "+961": "LB",
    "+965": "KW",
    "+974": "QA",
    "+973": "BH",
    "+968": "OM",
    "+967": "YE",
    "+93": "AF",
}

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
    def format_otp_message(otp_code, sender="SMS", country_code="BD", phone_number=None):
        """OTP মেসেজ সুন্দর করে ফরম্যাট করে - আপনার দেখানো স্টাইলে"""
        
        # কান্ট্রি ইনফো নাও
        country_info = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
        flag = country_info["flag"]
        logo = country_info["logo"]
        
        # ফোন নম্বর ফরম্যাট
        if phone_number:
            formatted_num = phone_number
        else:
            formatted_num = f"{country_info['code']}{otp_code}"
        
        if MESSAGE_FORMAT == "box":
            # আপনার দেখানো ফরম্যাটে
            text = (
                f"╭────────────────────╮\n"
                f"│ {flag} #{country_code} {logo} <code>{formatted_num}</code> │\n"
                f"╰────────────────────╯"
            )
        else:
            text = f"{flag} #{country_code} {logo} OTP: <code>{formatted_num}</code>"
        
        return text
    
    @staticmethod
    def format_otp_with_custom(otp_code, country_code="BD", custom_flag=None, custom_logo=None):
        """কাস্টম ফ্ল্যাগ ও লোগো সহ OTP মেসেজ"""
        
        country_info = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
        flag = custom_flag if custom_flag else country_info["flag"]
        logo = custom_logo if custom_logo else country_info["logo"]
        
        text = (
            f"╭────────────────────╮\n"
            f"│ {flag} #{country_code} {logo} <code>{otp_code}</code> │\n"
            f"╰────────────────────╯"
        )
        return text
    
    @staticmethod
    def format_bulk_message(otp_list, country_code="BD"):
        """একসাথে একাধিক OTP পাঠানোর জন্য"""
        if not otp_list:
            return None
        
        country_info = COUNTRIES.get(country_code, COUNTRIES[DEFAULT_COUNTRY])
        flag = country_info["flag"]
        
        if MESSAGE_FORMAT == "box":
            lines = ["╭────────────────────╮"]
            for otp in otp_list[:10]:
                lines.append(f"│ {flag} <code>{otp}</code> │")
            lines.append("╰────────────────────╯")
            return "\n".join(lines)
        else:
            return "\n".join([f"{flag} <code>{otp}</code>" for otp in otp_list[:10]])

# ========== টেলিগ্রাম বট ==========
class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
    
    async def send_message(self, text, parse_mode="HTML"):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.info(f"মেসেজ পাঠানো হয়েছে: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"মেসেজ পাঠাতে ব্যর্থ: {e}")
            return False
    
    def sync_send_message(self, text, parse_mode="HTML"):
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
            
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("ব্রাউজার সফলভাবে সেটআপ হয়েছে")
            return True
            
        except Exception as e:
            logger.error(f"ব্রাউজার সেটআপ করতে ব্যর্থ: {e}")
            return False
    
    def login(self):
        """ওয়েবসাইটে লগইন করে"""
        try:
            logger.info("লগইন পেজে নেওয়া হচ্ছে...")
            self.driver.get(LOGIN_URL)
            time.sleep(2)
            
            username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_field.send_keys(USERNAME)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(PASSWORD)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(3)
            
            if "login" not in self.driver.current_url.lower():
                logger.info("লগইন সফল হয়েছে!")
                return True
            else:
                logger.error("লগইন ব্যর্থ হয়েছে!")
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
                r'\b\d{4}\b',
                r'\b\d{5}\b',
                r'\b\d{6}\b',
                r'OTP[:\s]*(\d+)',
                r'code[:\s]*(\d+)',
                r'verification[:\s]*(\d+)',
                r'Your OTP is (\d+)',
                r'(\d{6}) is your OTP'
            ]
            
            # ফোন নম্বর প্যাটার্ন
            phone_patterns = [
                r'\+?\d{10,15}',
                r'\b01\d{9}\b',
                r'\b0\d{10}\b'
            ]
            
            all_otps = set()
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 4 and len(match) <= 8 and match.isdigit():
                        all_otps.add(match)
            
            # ফোন নম্বর খোঁজা
            phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                phones.update(matches)
            
            # OTP ডাটা তৈরি
            for otp in all_otps:
                # ফোন নম্বর ডিটেক্ট করার চেষ্টা
                detected_phone = None
                detected_country = DEFAULT_COUNTRY
                
                for phone in phones:
                    if otp in phone:
                        detected_phone = phone
                        # কান্ট্রি ডিটেক্ট
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
        """সিঙ্ক্রোনাসভাবে টেলিগ্রাম মেসেজ পাঠায়"""
        try:
            self.telegram.sync_send_message(text)
            return True
        except Exception as e:
            logger.error(f"টেলিগ্রামে পাঠাতে ব্যর্থ: {e}")
            return False
    
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
            sender="SMS",
            country_code=country,
            phone_number=phone
        )
        
        self.send_telegram_message(message)
        logger.info(f"নতুন OTP পাঠানো হয়েছে: {otp} (কান্ট্রি: {country})")
        return True
    
    def send_all_todays_otps(self):
        """আজকের সব OTP একসাথে পাঠায় (স্টার্টআপে)"""
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
        logger.info("OTP মনিটরিং শুরু হচ্ছে...")
        
        # ব্রাউজার সেটআপ
        if not self.browser.setup_driver():
            logger.error("ব্রাউজার সেটআপ ব্যর্থ, প্রোগ্রাম বন্ধ হচ্ছে")
            return
        
        # লগইন
        if not self.browser.login():
            logger.error("লগইন ব্যর্থ, প্রোগ্রাম বন্ধ হচ্ছে")
            self.browser.close()
            return
        
        # SMS পেজে যাও
        if not self.browser.get_page(SMS_PAGE_URL):
            logger.error("SMS পেজ লোড করতে ব্যর্থ")
            self.browser.close()
            return
        
        time.sleep(3)
        
        # স্টার্টআপে সব OTP পাঠায়
        self.send_all_todays_otps()
        
        # স্টার্টআপ মেসেজ
        self.send_telegram_message("✅ এসএমএস মনিটর বট চালু হয়েছে! জিম্বাবুয়ে সহ সকল দেশের OTP মনিটর করা হবে।")
        
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
                    logger.info(f"মনিটরিং চলছে... ({loop_count} সাইকেল)")
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info("ব্যবহারকারী দ্বারা বন্ধ করা হয়েছে")
                break
            except Exception as e:
                logger.error(f"মনিটরিং লুপে এরর: {e}")
                time.sleep(2)
        
        self.browser.close()
        logger.info("OTP মনিটরিং বন্ধ হয়েছে")

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