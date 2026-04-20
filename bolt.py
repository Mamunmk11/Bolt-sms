#!/usr/bin/env python3
"""
Bolt SMS - সম্পূর্ণ অটোমেটিক OTP মনিটর বট (Railway উপযোগী)
- 0.5 সেকেন্ড পরপর OTP চেক করে
- প্রতি 1.5 সেকেন্ড পরপর ব্রাউজার রিফ্রেশ করে
- চালু হওয়ার সাথে সাথে আজকের সব OTP ফরওয়ার্ড করে
- ডুপ্লিকেট OTP এড়ায়
"""

import os
import sys
import time
import json
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import requests

# ========== কনফিগারেশন (আপডেটেড) ==========
TELEGRAM_BOT_TOKEN = "8362446113:AAGsrg9iZmeByXmFbig2"  # আপনার নতুন টোকেন
GROUP_CHAT_ID = "-1001153782407"

# Bolt SMS সাইটের ইউআরএল (প্রয়োজনমতো পরিবর্তন করুন)
BOLT_SMS_URL = "https://boltsms.com/inbox"  # উদাহরণ URL

# অপশনাল: ক্রোম ড্রাইভার পাথ (Railway এ সাধারণত দরকার নেই)
CHROME_DRIVER_PATH = None  # None থাকলে PATH থেকে নেবে

# সেন্ড মেসেজের ফরম্যাট সেটিংস
MESSAGE_FORMAT = "box"  # "box" অথবা "simple"

# ডুপ্লিকেট চেকের জন্য ফাইল
SEEN_OTPS_FILE = "seen_otps.json"

# ========== লগিং সেটআপ ==========
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
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
    def format_otp_message(otp_code, sender="Bolt SMS", flag="📱", country_code="BD", logo="🔐"):
        """OTP মেসেজ সুন্দর করে ফরম্যাট করে"""
        formatted_num = otp_code
        
        if MESSAGE_FORMAT == "box":
            text = (
                f"╭────────────────────╮\n"
                f"│ {flag} #{country_code} {logo} <code>{formatted_num}</code> │\n"
                f"╰────────────────────╯"
            )
        else:
            text = f"{flag} #{country_code} {logo} OTP: <code>{formatted_num}</code>"
        
        return text
    
    @staticmethod
    def format_bulk_message(otp_list):
        """একসাথে একাধিক OTP পাঠানোর জন্য"""
        if not otp_list:
            return None
        
        if MESSAGE_FORMAT == "box":
            lines = ["╭────────────────────╮"]
            for otp in otp_list[:10]:
                lines.append(f"│ 📱 <code>{otp}</code> │")
            lines.append("╰────────────────────╯")
            return "\n".join(lines)
        else:
            return "\n".join([f"📱 <code>{otp}</code>" for otp in otp_list[:10]])

# ========== টেলিগ্রাম বট (সরাসরি requests ব্যবহার করে) ==========
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
    
    def send_message(self, text, parse_mode="HTML"):
        """সরাসরি requests ব্যবহার করে মেসেজ পাঠায়"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ মেসেজ পাঠানো হয়েছে: {text[:50]}...")
                return True
            else:
                logger.error(f"❌ টেলিগ্রাম এপি আই এরর: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ মেসেজ পাঠাতে ব্যর্থ: {e}")
            return False
    
    def test_connection(self):
        """বট টোকেন কাজ করছে কিনা টেস্ট করে"""
        url = f"https://api.telegram.org/bot{self.token}/getMe"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    logger.info(f"✅ বট সংযোগ সফল: @{data['result']['username']}")
                    return True
            logger.error(f"❌ বট টোকেন বৈধ নয়: {response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ সংযোগ টেস্ট ব্যর্থ: {e}")
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
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            if CHROME_DRIVER_PATH:
                service = Service(CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("✅ ব্রাউজার সফলভাবে সেটআপ হয়েছে")
            return True
            
        except Exception as e:
            logger.error(f"❌ ব্রাউজার সেটআপ করতে ব্যর্থ: {e}")
            return False
    
    def get_page(self, url):
        """পৃষ্ঠা লোড করে"""
        try:
            self.driver.get(url)
            logger.info(f"✅ পৃষ্ঠা লোড হয়েছে: {url}")
            return True
        except Exception as e:
            logger.error(f"❌ পৃষ্ঠা লোড করতে ব্যর্থ: {e}")
            return False
    
    def refresh_page(self):
        """পৃষ্ঠা রিফ্রেশ করে"""
        try:
            self.driver.refresh()
            logger.info("🔄 পৃষ্ঠা রিফ্রেশ করা হয়েছে")
            return True
        except Exception as e:
            logger.error(f"❌ পৃষ্ঠা রিফ্রেশ করতে ব্যর্থ: {e}")
            return False
    
    def extract_otps(self):
        """পৃষ্ঠা থেকে সব OTP এক্সট্রাক্ট করে"""
        otps = []
        try:
            page_text = self.driver.page_source
            
            patterns = [
                r'\b\d{4}\b',
                r'\b\d{5}\b',
                r'\b\d{6}\b',
                r'\b\d{7}\b',
                r'\b\d{8}\b',
                r'OTP[:\s]*(\d+)',
                r'code[:\s]*(\d+)',
                r'verification[:\s]*(\d+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                otps.extend(matches)
            
            otps = list(set(otps))
            if otps:
                logger.info(f"📱 {len(otps)} টি OTP পাওয়া গেছে")
            return otps
            
        except Exception as e:
            logger.error(f"❌ OTP এক্সট্রাক্ট করতে ব্যর্থ: {e}")
            return []
    
    def close(self):
        """ব্রাউজার বন্ধ করে"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 ব্রাউজার বন্ধ করা হয়েছে")

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
    
    def format_and_send_otp(self, otp, source="Bolt SMS"):
        """OTP ফরম্যাট করে পাঠায়"""
        if self.duplicate_manager.is_duplicate(otp):
            logger.debug(f"ডুপ্লিকেট OTP স্কিপ: {otp}")
            return False
        
        message = self.formatter.format_otp_message(
            otp_code=otp,
            sender=source,
            flag="📱",
            country_code="BD",
            logo="🔐"
        )
        
        self.send_telegram_message(message)
        logger.info(f"✨ নতুন OTP পাঠানো হয়েছে: {otp}")
        return True
    
    def send_all_todays_otps(self):
        """আজকের সব OTP একসাথে পাঠায় (স্টার্টআপে)"""
        logger.info("📥 আজকের সব OTP সংগ্রহ করা হচ্ছে...")
        
        otps = self.browser.extract_otps()
        
        if not otps:
            logger.info("📭 কোনো OTP পাওয়া যায়নি")
            return
        
        new_otps = []
        for otp in otps:
            if not self.duplicate_manager.is_duplicate(otp):
                new_otps.append(otp)
        
        if new_otps:
            logger.info(f"🎉 {len(new_otps)} টি নতুন OTP পাওয়া গেছে")
            for otp in new_otps:
                self.format_and_send_otp(otp)
        else:
            logger.info("📌 সব OTP ই আগে দেখা হয়েছে")
    
    def monitor_loop(self):
        """মূল মনিটরিং লুপ"""
        logger.info("🚀 OTP মনিটরিং শুরু হচ্ছে...")
        
        # বট টোকেন টেস্ট
        if not self.telegram.test_connection():
            logger.error("❌ বট টোকেন কাজ করছে না! স্ক্রিপ্ট বন্ধ হচ্ছে।")
            return
        
        # ব্রাউজার সেটআপ
        if not self.browser.setup_driver():
            logger.error("❌ ব্রাউজার সেটআপ ব্যর্থ, প্রোগ্রাম বন্ধ হচ্ছে")
            return
        
        # ওয়েবসাইট লোড
        if not self.browser.get_page(BOLT_SMS_URL):
            logger.error("❌ ওয়েবসাইট লোড করতে ব্যর্থ")
            self.browser.close()
            return
        
        time.sleep(3)
        
        # স্টার্টআপে সব OTP পাঠায়
        self.send_all_todays_otps()
        
        # স্টার্টআপ সফল মেসেজ
        self.send_telegram_message("✅ Bolt SMS মনিটর বট চালু হয়েছে! নতুন OTP আসলে আপনাকে জানানো হবে।")
        
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
                otps = self.browser.extract_otps()
                
                for otp in otps:
                    if otp not in self.processed_otps:
                        self.processed_otps.add(otp)
                        self.format_and_send_otp(otp)
                
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
    ╔══════════════════════════════════════╗
    ║      Bolt SMS - OTP Monitor Bot      ║
    ║    সম্পূর্ণ অটোমেটিক OTP মনিটর      ║
    ╚══════════════════════════════════════╝
    """)
    
    logger.info("বট স্টার্ট হচ্ছে...")
    
    monitor = OTPSMSMonitor()
    
    try:
        monitor.monitor_loop()
    except Exception as e:
        logger.error(f"মেইন ফাংশনে এরর: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()