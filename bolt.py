#!/usr/bin/env python3
"""
Bolt SMS - DEBUG VERSION (With Telegram Test)
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

class DebugOTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = set()
        self.total_otps_sent = 0
        self.is_monitoring = True
        
        logger.info("="*50)
        logger.info("🔧 DEBUG BOT INITIALIZED")
        logger.info("="*50)
        
        # Test Telegram connection immediately
        self.test_telegram_connection()
    
    def test_telegram_connection(self):
        """Test if Telegram bot is working"""
        try:
            logger.info("📡 Testing Telegram connection...")
            
            # Test 1: Get bot info
            response = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data['result'].get('username')
                    logger.info(f"✅ Telegram bot connected! Bot: @{bot_name}")
                else:
                    logger.error(f"❌ Bot error: {data}")
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
            
            # Test 2: Send test message
            logger.info("📤 Sending test message to group...")
            test_response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": GROUP_CHAT_ID,
                    "text": "🤖 Bot is starting up! Testing connection...",
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if test_response.status_code == 200:
                logger.info("✅ Test message sent successfully!")
            else:
                logger.error(f"❌ Failed to send test message: {test_response.status_code}")
                logger.error(f"Response: {test_response.text}")
                
        except Exception as e:
            logger.error(f"❌ Telegram test error: {e}")
    
    def send_telegram_message(self, message, otp=None):
        """Send message to Telegram"""
        try:
            if otp:
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
                        "reply_markup": keyboard
                    },
                    timeout=10
                )
            else:
                response = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": GROUP_CHAT_ID,
                        "text": message,
                        "parse_mode": "HTML"
                    },
                    timeout=10
                )
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent: {message[:50]}...")
                return True
            else:
                logger.error(f"❌ Send failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return False
    
    def setup_browser(self):
        try:
            logger.info("🌐 Setting up browser...")
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
            logger.error(f"❌ Browser error: {e}")
            return False
    
    def solve_captcha(self):
        try:
            captcha_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'What is')]")
            if captcha_elements:
                captcha_text = captcha_elements[0].text
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
            logger.info("✅ Username entered")
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("✅ Password entered")
            
            time.sleep(2)
            self.solve_captcha()
            time.sleep(1)
            
            # Submit form
            form = self.driver.find_element(By.TAG_NAME, "form")
            form.submit()
            logger.info("✅ Form submitted")
            
            time.sleep(8)
            current_url = self.driver.current_url
            logger.info(f"📍 Current URL: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
                self.logged_in = True
                
                # Send login success message
                self.send_telegram_message("✅ Bot Login Successful! Starting monitor...")
                
                self.driver.get(SMS_PAGE_URL)
                time.sleep(8)
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed!")
                self.send_telegram_message("❌ Login Failed! Please check credentials.")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        if not isinstance(message, str):
            return None
        
        patterns = [
            r'#(\d{4,8})',
            r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,8})',
            r'is[:\s]*(\d{4,8})',
            r'(\d{4,8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                otp = match.group(1)
                if not otp.startswith(('263', '880', '1', '44', '91')):
                    return otp
        return None
    
    def get_sms(self):
        try:
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
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
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def monitor(self):
        logger.info("🚀 Starting OTP monitor...")
        
        # Send started message
        self.send_telegram_message(f"🚀 Bot Started!\n👤 User: {USERNAME}\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        
        while self.is_monitoring:
            try:
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = self.extract_otp(sms['message'])
                        if otp:
                            sms_id = f"{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                logger.info(f"🆕 NEW OTP FOUND! {otp} - {sms['client']}")
                                
                                # Send OTP message
                                msg = f"🔐 OTP: {otp}\n📱 Phone: {sms['phone'][:4]}****{sms['phone'][-4:]}\n📱 Platform: {sms['client']}"
                                
                                if self.send_telegram_message(msg, otp):
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    logger.info(f"✅ OTP #{self.total_otps_sent} sent")
                                
                                await asyncio.sleep(0.5)
                
                await asyncio.sleep(3)  # Check every 3 seconds
                
                # Refresh every 15 seconds
                self.driver.refresh()
                logger.debug("🔄 Browser refreshed")
                await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        print("\n" + "="*60)
        print("🤖 DEBUG OTP BOT - TEST VERSION")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"📱 Telegram Chat ID: {GROUP_CHAT_ID}")
        print("="*60)
        
        # Send startup message
        self.send_telegram_message("🤖 Bot is initializing...")
        
        print("\n🔧 Setting up browser...")
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        print("\n🔐 Logging in...")
        if not self.auto_login():
            print("❌ Login failed!")
            return
        
        print("\n✅ Login successful!")
        
        print("\n" + "="*60)
        print("🚀 Starting OTP Monitor...")
        print("="*60)
        print("📱 Checking for new OTPs...")
        print("💾 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = DebugOTPBot()
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