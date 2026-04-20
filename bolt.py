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
from selenium.common.exceptions import WebDriverException, TimeoutException

# ========== CONFIGURATION ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

# Platform emoji mapping
PLATFORM_EMOJIS = {
    "TELEGRAM": "📨",
    "WHATSAPP": "💚",
    "FACEBOOK": "📘",
    "INSTAGRAM": "📸",
    "GMAIL": "📧",
    "APPLE": "🍎",
    "OTHER": "📱"
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
        self.refresh_counter = 0
        
        logger.info("Bolt SMS OTP Monitor Bot Initialized")
        if IS_RAILWAY:
            logger.info("Running on Railway (Headless Mode)")
        else:
            logger.info("Running on Local PC (Browser Mode)")
    
    def get_country_flag_and_code(self, phone_number):
        try:
            clean_number = re.sub(r'\D', '', str(phone_number))
            
            if clean_number.startswith('263'):
                return "🇿🇼", "#ZW"
            elif clean_number.startswith('880'):
                return "🇧🇩", "#BD"
            elif clean_number.startswith('91'):
                return "🇮🇳", "#IN"
            elif clean_number.startswith('92'):
                return "🇵🇰", "#PK"
            elif clean_number.startswith('1'):
                return "🇺🇸", "#US"
            elif clean_number.startswith('44'):
                return "🇬🇧", "#UK"
            elif clean_number.startswith('234'):
                return "🇳🇬", "#NG"
            else:
                return "🌍", "#??"
        except:
            return "🌍", "#??"
    
    def send_otp_to_telegram(self, country_flag, country_code, platform, number, otp):
        """Send OTP - Clean format without any extra characters"""
        try:
            platform_emoji = PLATFORM_EMOJIS.get(platform.upper(), "📱")
            
            # Clean number
            number_str = re.sub(r'\D', '', str(number))
            if len(number_str) >= 8:
                formatted_number = number_str[:4] + "****" + number_str[-4:]
            elif len(number_str) >= 4:
                formatted_number = number_str[:2] + "***" + number_str[-2:]
            else:
                formatted_number = number_str
            
            # Clean message - exactly as shown
            message = (
                "╭────────────────────╮\n"
                f"│ {country_flag} {country_code} {platform_emoji} {formatted_number} │\n"
                "╰────────────────────╯"
            )
            
            # Keyboard
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"{otp}", "copy_text": {"text": otp}}],
                    [
                        {"text": "🔢 Number Bot", "url": "https://t.me/Updateotpnew_bot"},
                        {"text": "📢 Main Channel", "url": "https://t.me/updaterange"}
                    ]
                ]
            }
            
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": GROUP_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ OTP sent: {otp}")
                return True
            else:
                logger.error(f"Failed: {response.status_code}")
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
                if not os.path.exists(chromedriver_path):
                    logger.error(f"ChromeDriver not found")
                    return False
                
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
            captcha_text = None
            try:
                captcha_text = self.driver.find_element(By.XPATH, "//div[contains(text(), 'What is')]").text
            except:
                try:
                    captcha_text = self.driver.find_element(By.XPATH, "//label[contains(text(), 'What is')]").text
                except:
                    pass
            
            if captcha_text:
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
            time.sleep(5)
            
            username_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
            time.sleep(2)
            self.solve_captcha()
            time.sleep(1)
            
            # Try to find login button
            try:
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
            except:
                try:
                    form = self.driver.find_element(By.TAG_NAME, "form")
                    form.submit()
                except:
                    logger.error("Could not find login button")
                    return False
            
            time.sleep(8)
            
            current_url = self.driver.current_url
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("LOGIN SUCCESSFUL!")
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                return True
            else:
                logger.error("Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_platform(self, message, client):
        msg = message.lower()
        if 'telegram' in msg:
            return "TELEGRAM"
        elif 'facebook' in msg or 'fb' in msg:
            return "FACEBOOK"
        elif 'apple' in msg or 'icloud' in msg:
            return "APPLE"
        elif 'whatsapp' in msg:
            return "WHATSAPP"
        else:
            return "OTHER"
    
    def extract_otp(self, message):
        if not isinstance(message, str):
            return None
        
        match = re.search(r'#(\d{4,8})', message)
        if match:
            return match.group(1)
        
        match = re.search(r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,8})', message)
        if match:
            return match.group(1)
        
        match = re.search(r'is[:\s]*(\d{4,8})', message)
        if match:
            return match.group(1)
        
        numbers = re.findall(r'\b(\d{4,8})\b', message)
        for num in numbers:
            if not num.startswith(('263', '880', '1', '44', '91', '92')):
                return num
        
        return None
    
    def get_sms(self):
        try:
            time.sleep(1)
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    msg = cols[5].text.strip()
                    if msg.startswith('REG-PS'):
                        continue
                    sms_list.append({
                        'time': cols[0].text.strip(),
                        'phone': cols[2].text.strip(),
                        'client': cols[4].text.strip(),
                        'message': msg
                    })
            
            if sms_list:
                logger.info(f"Found {len(sms_list)} SMS")
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
                            flag, code = self.get_country_flag_and_code(sms['phone'])
                            
                            logger.info(f"NEW OTP: {otp}")
                            
                            if self.send_otp_to_telegram(flag, code, platform, sms['phone'], otp):
                                self.processed_otps.add(sms_id)
                                self.total_otps_sent += 1
                            
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