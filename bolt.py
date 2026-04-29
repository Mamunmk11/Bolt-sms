#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Monitor Bot (Fixed Alert Handler)
- Handles DataTables Ajax errors automatically
- 2 second browser refresh
- Country flags with short codes
- Clickable OTP button
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, UnexpectedAlertPresentException, NoAlertPresentException

# ========== CONFIGURATION ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== COUNTRY DATA ==========
COUNTRIES = {
    '880': ('🇧🇩', '#BD'), '91': ('🇮🇳', '#IN'), '1': ('🇺🇸', '#US'),
    '44': ('🇬🇧', '#UK'), '61': ('🇦🇺', '#AU'), '86': ('🇨🇳', '#CN'),
    '81': ('🇯🇵', '#JP'), '49': ('🇩🇪', '#DE'), '33': ('🇫🇷', '#FR'),
    '7': ('🇷🇺', '#RU'), '55': ('🇧🇷', '#BR'), '92': ('🇵🇰', '#PK'),
    '94': ('🇱🇰', '#LK'), '977': ('🇳🇵', '#NP'), '966': ('🇸🇦', '#SA'),
    '971': ('🇦🇪', '#AE'), '20': ('🇪🇬', '#EG'), '27': ('🇿🇦', '#ZA'),
    '234': ('🇳🇬', '#NG'), '263': ('🇿🇼', '#ZW'), '90': ('🇹🇷', '#TR'),
    '64': ('🇳🇿', '#NZ'), '46': ('🇸🇪', '#SE'), '47': ('🇳🇴', '#NO'),
    '45': ('🇩🇰', '#DK'), '358': ('🇫🇮', '#FI'), '32': ('🇧🇪', '#BE'),
    '41': ('🇨🇭', '#CH'), '43': ('🇦🇹', '#AT'), '34': ('🇪🇸', '#ES'),
    '351': ('🇵🇹', '#PT'), '39': ('🇮🇹', '#IT'), '48': ('🇵🇱', '#PL'),
    '420': ('🇨🇿', '#CZ'), '36': ('🇭🇺', '#HU'), '40': ('🇷🇴', '#RO'),
    '30': ('🇬🇷', '#GR'), '353': ('🇮🇪', '#IE'), '31': ('🇳🇱', '#NL'),
}

PLATFORM_NAMES = {
    'whatsapp': ('💚', 'WhatsApp'), 'telegram': ('🪁', 'Telegram'),
    'facebook': ('📘', 'Facebook'), 'instagram': ('📸', 'Instagram'),
    'gmail': ('📧', 'Gmail'), 'apple': ('🍎', 'Apple'), 'binance': ('📊', 'Binance'),
}

class OTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = set()
        self.total_otps_sent = 0
        self.is_monitoring = True
        self.refresh_counter = 0
        
        logger.info("🤖 Complete OTP Bot Initialized")
    
    def get_country_info(self, phone_number):
        try:
            clean_number = re.sub(r'\D', '', str(phone_number))
            sorted_codes = sorted(COUNTRIES.keys(), key=len, reverse=True)
            for code in sorted_codes:
                if clean_number.startswith(code):
                    return COUNTRIES[code]
            return "🌍", "#??"
        except:
            return "🌍", "#??"
    
    def get_platform_info(self, client_name, message):
        combined = f"{client_name} {message}".lower()
        for key, (emoji, name) in PLATFORM_NAMES.items():
            if key in combined:
                return emoji, name
        if client_name and client_name.strip():
            return "📱", client_name.strip()
        return "📱", "Other"
    
    def hide_phone(self, phone):
        phone_str = re.sub(r'\D', '', str(phone))
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
    def handle_alert(self):
        """Handle any alert popups - KEY FIX FOR THE ERROR"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            logger.warning(f"⚠️ Alert detected: {alert_text}")
            alert.accept()
            time.sleep(2)
            return True
        except NoAlertPresentException:
            return False
        except Exception as e:
            logger.error(f"Alert handling error: {e}")
            return False
    
    def send_otp_to_telegram(self, country_flag, country_code, platform_emoji, platform_name, masked_number, otp):
        try:
            message = f"{country_flag} {country_code} {platform_emoji} {platform_name} {masked_number}"
            
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
                logger.info(f"✅ OTP sent: {otp} for {platform_name}")
                return True
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
                chrome_options.binary_location = "/usr/bin/google-chrome"
                service = Service(executable_path="/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Browser opened on Railway")
            else:
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Browser opened on Local PC")
            
            return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False
    
    def solve_captcha(self):
        try:
            captcha_text = None
            for xpath in ["//div[contains(text(), 'What is')]", "//label[contains(text(), 'What is')]"]:
                try:
                    captcha_text = self.driver.find_element(By.XPATH, xpath).text
                    if captcha_text:
                        break
                except:
                    continue
            
            if captcha_text:
                match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                if match:
                    result = int(match.group(1)) + int(match.group(2))
                    captcha_input = self.driver.find_element(By.NAME, "capt")
                    captcha_input.clear()
                    captcha_input.send_keys(str(result))
                    logger.info(f"✅ Captcha solved: {match.group(1)} + {match.group(2)} = {result}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Captcha error: {e}")
            return False
    
    def auto_login(self):
        try:
            logger.info("🔐 Logging in...")
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
            
            form = self.driver.find_element(By.TAG_NAME, "form")
            form.submit()
            
            time.sleep(8)
            current_url = self.driver.current_url
            
            if 'agent' in current_url or 'Dashboard' in current_url or 'SMS' in current_url:
                logger.info("✅ LOGIN SUCCESSFUL!")
                self.logged_in = True
                self.driver.get(SMS_PAGE_URL)
                time.sleep(8)
                self.handle_alert()
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        if not isinstance(message, str):
            return None
        
        patterns = [
            r'#(\d{4,10})',
            r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,10})',
            r'is[:\s]*(\d{4,10})',
            r'(\d{4,10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                otp = match.group(1)
                if not otp.startswith(('263', '880', '1', '44', '91', '92', '234')):
                    return otp
        return None
    
    def get_sms(self):
        """Get SMS with alert handling - FIXED"""
        try:
            self.handle_alert()
            time.sleep(0.5)
            
            try:
                rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
                if not rows:
                    logger.warning("No rows found, refreshing...")
                    self.driver.refresh()
                    time.sleep(3)
                    self.handle_alert()
                    rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            except UnexpectedAlertPresentException:
                self.handle_alert()
                return []
            
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 5:
                    message_text = cols[4].text.strip() if len(cols) > 4 else ""
                    if message_text and not message_text.startswith('REG-'):
                        sms_list.append({
                            'time': cols[0].text.strip(),
                            'phone': cols[1].text.strip(),
                            'client': cols[2].text.strip(),
                            'message': message_text
                        })
            
            if sms_list:
                logger.info(f"📊 Found {len(sms_list)} SMS messages")
            return sms_list
            
        except UnexpectedAlertPresentException:
            self.handle_alert()
            return []
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def monitor(self):
        logger.info("🚀 Starting OTP monitor (0.5 sec interval)...")
        logger.info("🔄 Browser will refresh every 2 seconds")
        
        while self.is_monitoring:
            try:
                self.handle_alert()
                start_time = time.time()
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = self.extract_otp(sms['message'])
                        if otp:
                            sms_id = f"{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                country_flag, country_code = self.get_country_info(sms['phone'])
                                platform_emoji, platform_name = self.get_platform_info(sms['client'], sms['message'])
                                masked_number = self.hide_phone(sms['phone'])
                                
                                logger.info(f"🆕 NEW OTP! {otp} - {platform_name}")
                                
                                result = self.send_otp_to_telegram(
                                    country_flag, country_code, platform_emoji, 
                                    platform_name, masked_number, otp
                                )
                                
                                if result:
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                
                                await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                self.refresh_counter += 1
                if self.refresh_counter >= 4:
                    self.driver.refresh()
                    logger.debug("🔄 Browser refreshed (2 seconds)")
                    self.refresh_counter = 0
                    await asyncio.sleep(2)
                    
            except UnexpectedAlertPresentException:
                logger.warning("Alert during monitor, handling...")
                self.handle_alert()
                await asyncio.sleep(2)
            except WebDriverException as e:
                logger.error(f"Driver error: {e}")
                logger.info("Reconnecting...")
                try:
                    self.driver.quit()
                    time.sleep(3)
                    self.setup_browser()
                    self.driver.get(SMS_PAGE_URL)
                    await asyncio.sleep(5)
                except:
                    pass
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def run(self):
        print("\n" + "="*60)
        print("🤖 BOLT SMS - OTP MONITOR BOT")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"⚡ Check Interval: 0.5 seconds")
        print(f"🔄 Browser Refresh: Every 2 seconds")
        print("="*60)
        
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        if not self.auto_login():
            print("❌ Login failed!")
            return
        
        print("\n✅ Login successful!")
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"📊 Total OTPs sent: {bot.total_otps_sent}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())