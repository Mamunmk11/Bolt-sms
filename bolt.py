#!/usr/bin/env python3
"""
Bolt SMS - Automatic OTP Monitor Bot (Railway Compatible)
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
import requests
import phonenumbers
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ========== CONFIGURATION ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

# Second bot configuration
BOT_TOKEN_2 = "8639902314:AAENcAdowvvpHnU75UpLMcGRJ24yVizFMZg"
CHAT_ID_2 = "-1003818275876"

# Platform emoji mapping
PLATFORM_EMOJIS = {
    "WHATSAPP": {"short": "WS", "emoji_id": "5226815671261763813"},
    "TELEGRAM": {"short": "TG", "emoji_id": "5267139126339084336"},
    "FACEBOOK": {"short": "FB", "emoji_id": "5269492171416832604"},
    "INSTAGRAM": {"short": "IG", "emoji_id": "5226815671261763813"},
    "GMAIL": {"short": "GM", "emoji_id": "5226815671261763813"},
    "APPLE": {"short": "AP", "emoji_id": "5226815671261763813"},
    "OTHER": {"short": "OT", "emoji_id": "5226815671261763813"}
}

IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None
# =================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class OTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = set()
        self.total_otps_sent = 0
        self.is_monitoring = True
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.refresh_counter = 0
        
        logger.info("Bolt SMS OTP Monitor Bot Initialized")
    
    def get_country_flag_and_code(self, phone_number):
        try:
            parsed = phonenumbers.parse(phone_number, None)
            country_code = parsed.country_code
            country_flags = {1:"🇺🇸",44:"🇬🇧",91:"🇮🇳",92:"🇵🇰",880:"🇧🇩",263:"🇿🇼"}
            flag = country_flags.get(country_code, "🌍")
            return flag, f"#{country_code}"
        except:
            return "🌍", "#0"
    
    def send_otp_custom_format(self, country_flag, country_code, platform, number, otp):
        try:
            platform_info = PLATFORM_EMOJIS.get(platform.upper(), PLATFORM_EMOJIS["OTHER"])
            platform_logo = f'<tg-emoji emoji-id="{platform_info["emoji_id"]}">{platform_info["short"]}</tg-emoji>'
            
            message = (
                f"╭────────────────────╮\n"
                f"│ {country_flag} {country_code} {platform_logo} {number} │\n"
                f"╰────────────────────╯"
            )
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"{otp}", "copy_text": {"text": otp}}],
                    [
                        {"text": "🚀 Number Panel", "url": "https://t.me/RTX_Number_Bot"},
                        {"text": "⚙️ Main Channel", "url": "https://t.me/TR_TECH_ZONE"}
                    ]
                ]
            }
            
            logger.info(f"Sending OTP {otp} to {CHAT_ID_2}")
            
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN_2}/sendMessage",
                json={
                    "chat_id": CHAT_ID_2,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard
                },
                timeout=10
            )
            
            logger.info(f"Response: {response.status_code} - {response.text[:200]}")
            
            if response.status_code == 200:
                logger.info(f"✅ OTP sent: {otp}")
                return True
            else:
                logger.error(f"❌ Failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def setup_browser(self):
        try:
            chrome_options = Options()
            if IS_RAILWAY:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-setuid-sandbox')
                chrome_options.add_argument('--remote-debugging-port=9222')
                chrome_options.binary_location = "/usr/bin/google-chrome"
                service = Service(executable_path="/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Browser opened on Railway")
            else:
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                chrome_options.add_argument('--start-maximized')
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Browser opened on Local PC")
            return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False
    
    def solve_captcha(self):
        try:
            captcha_text = self.driver.find_element(By.XPATH, "//div[contains(text(), 'What is')]").text
            match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
            if match:
                result = int(match.group(1)) + int(match.group(2))
                captcha_input = self.driver.find_element(By.NAME, "capt")
                captcha_input.clear()
                captcha_input.send_keys(str(result))
                return True
            return False
        except:
            return False
    
    def auto_login(self):
        try:
            logger.info("Logging in...")
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            time.sleep(1)
            self.solve_captcha()
            time.sleep(1)
            
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_btn.click()
            time.sleep(5)
            
            current_url = self.driver.current_url
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("LOGIN SUCCESSFUL!")
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                return True
            else:
                logger.error("Login failed!")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_platform(self, message, client):
        msg_lower = message.lower()
        if 'telegram' in msg_lower:
            return "TELEGRAM"
        elif 'facebook' in msg_lower or 'fb' in msg_lower:
            return "FACEBOOK"
        elif 'apple' in msg_lower or 'icloud' in msg_lower:
            return "APPLE"
        elif 'whatsapp' in msg_lower:
            return "WHATSAPP"
        else:
            return "OTHER"
    
    def extract_otp(self, message):
        """Extract OTP - supports #12345, code 12345, is 12345 formats"""
        if not isinstance(message, str):
            return None
        
        logger.info(f"Checking message: {message[:80]}")
        
        # Pattern 1: #16010 (Facebook)
        match = re.search(r'#(\d{4,8})', message)
        if match:
            code = match.group(1)
            logger.info(f"Found OTP via #: {code}")
            return code
        
        # Pattern 2: code 47543 or CODE 47543
        match = re.search(r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,8})', message)
        if match:
            code = match.group(1)
            logger.info(f"Found OTP via code: {code}")
            return code
        
        # Pattern 3: is 342761
        match = re.search(r'is[:\s]*(\d{4,8})', message)
        if match:
            code = match.group(1)
            logger.info(f"Found OTP via is: {code}")
            return code
        
        # Pattern 4: any 4-8 digit number
        numbers = re.findall(r'\b(\d{4,8})\b', message)
        for num in numbers:
            if not num.startswith(('263', '880', '1', '44')):
                logger.info(f"Found OTP via fallback: {num}")
                return num
        
        logger.info("No OTP found")
        return None
    
    def get_sms(self):
        try:
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    message_text = cols[5].text.strip()
                    if not message_text.startswith('REG-PS'):
                        sms_list.append({
                            'time': cols[0].text.strip(),
                            'phone': cols[2].text.strip(),
                            'client': cols[4].text.strip(),
                            'message': message_text
                        })
            if sms_list:
                logger.info(f"Found {len(sms_list)} SMS messages")
            return sms_list
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def monitor(self):
        logger.info("Starting OTP monitor...")
        
        while self.is_monitoring:
            try:
                sms_list = self.get_sms()
                
                for sms in sms_list:
                    otp = self.extract_otp(sms['message'])
                    if otp:
                        sms_id = f"{sms['phone']}_{otp}"
                        if sms_id not in self.processed_otps:
                            platform = self.extract_platform(sms['message'], sms['client'])
                            flag, country_code = self.get_country_flag_and_code(sms['phone'])
                            
                            logger.info(f"📱 NEW OTP: {otp} from {platform}")
                            
                            if self.send_otp_custom_format(flag, country_code, platform, sms['phone'], otp):
                                self.processed_otps.add(sms_id)
                                self.total_otps_sent += 1
                                logger.info(f"Total sent: {self.total_otps_sent}")
                            
                            await asyncio.sleep(0.5)
                
                # Refresh every 1.5 seconds
                self.refresh_counter += 1
                if self.refresh_counter >= 3:
                    self.driver.refresh()
                    self.refresh_counter = 0
                    await asyncio.sleep(1.5)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def run(self):
        print("\n" + "="*50)
        print("BOLT SMS - OTP MONITOR BOT")
        print("="*50)
        
        if not self.setup_browser():
            return
        if not self.auto_login():
            return
        
        print("\n✅ Bot Started! Monitoring...\n")
        await self.monitor()

async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\nBot stopped!")

if __name__ == "__main__":
    asyncio.run(main())