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
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

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
        if IS_RAILWAY:
            logger.info("Running on Railway (Headless Mode)")
        else:
            logger.info("Running on Local PC (Browser Mode)")
    
    def get_country_flag_and_code(self, phone_number):
        try:
            parsed = phonenumbers.parse(phone_number, None)
            country_code = parsed.country_code
            
            country_flags = {
                1: "🇺🇸", 44: "🇬🇧", 91: "🇮🇳", 92: "🇵🇰", 
                880: "🇧🇩", 263: "🇿🇼", 234: "🇳🇬", 20: "🇪🇬",
                966: "🇸🇦", 971: "🇦🇪", 962: "🇯🇴", 965: "🇰🇼",
                974: "🇶🇦", 973: "🇧🇭", 968: "🇴🇲", 961: "🇱🇧"
            }
            flag = country_flags.get(country_code, "🌍")
            return flag, f"#{country_code}"
        except:
            return "🌍", "#0"
    
    async def send_otp_to_telegram(self, country_flag, country_code, platform, number, otp):
        """Send OTP to Telegram group - Fixed version without copy_text issue"""
        try:
            platform_info = PLATFORM_EMOJIS.get(platform.upper(), PLATFORM_EMOJIS["OTHER"])
            platform_logo = f'<tg-emoji emoji-id="{platform_info["emoji_id"]}">{platform_info["short"]}</tg-emoji>'
            
            message = (
                f"╭────────────────────╮\n"
                f"│ {country_flag} {country_code} {platform_logo} <code>{number}</code> │\n"
                f"╰────────────────────╯"
            )
            
            # Fixed buttons - using callback_data instead of copy_text
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=f"📋 {otp}", callback_data=f"copy_{otp}")],
                [
                    InlineKeyboardButton(text="🔢 Number Bot", url="https://t.me/Updateotpnew_bot"),
                    InlineKeyboardButton(text="📢 Main Channel", url="https://t.me/updaterange")
                ]
            ])
            
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            logger.info(f"✅ OTP sent: {otp}")
            return True
            
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
                logger.info("Browser opened on Railway (Headless Mode)")
            else:
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                if not os.path.exists(chromedriver_path):
                    logger.error(f"ChromeDriver not found at: {chromedriver_path}")
                    return False
                
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
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
                    try:
                        captcha_text = self.driver.find_element(By.CLASS_NAME, "captcha").text
                    except:
                        pass
            
            if captcha_text:
                match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                if match:
                    num1 = int(match.group(1))
                    num2 = int(match.group(2))
                    result = num1 + num2
                    logger.info(f"Captcha: {num1} + {num2} = {result}")
                    
                    captcha_input = self.driver.find_element(By.NAME, "capt")
                    captcha_input.clear()
                    captcha_input.send_keys(str(result))
                    return True
            return False
        except Exception as e:
            logger.error(f"Captcha error: {e}")
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
            logger.info(f"Username: {USERNAME}")
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("Password entered")
            
            time.sleep(2)
            self.solve_captcha()
            time.sleep(1)
            
            login_clicked = False
            
            try:
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                login_clicked = True
                logger.info("Login button clicked")
            except:
                pass
            
            if not login_clicked:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                    login_btn.click()
                    login_clicked = True
                    logger.info("Login button clicked")
                except:
                    pass
            
            if not login_clicked:
                try:
                    form = self.driver.find_element(By.TAG_NAME, "form")
                    form.submit()
                    login_clicked = True
                    logger.info("Form submitted")
                except:
                    pass
            
            if not login_clicked:
                logger.error("Could not find login button!")
                return False
            
            time.sleep(8)
            
            current_url = self.driver.current_url
            logger.info(f"URL after login: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url or 'SMS' in current_url:
                logger.info("LOGIN SUCCESSFUL!")
                self.logged_in = True
                
                self.driver.get(SMS_PAGE_URL)
                time.sleep(8)
                logger.info("SMS page loaded")
                return True
            else:
                logger.error("Login failed - wrong URL")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_platform(self, message, client):
        message_lower = message.lower()
        
        if 'telegram' in message_lower:
            return "TELEGRAM"
        elif 'facebook' in message_lower or 'fb' in message_lower:
            return "FACEBOOK"
        elif 'apple' in message_lower or 'icloud' in message_lower:
            return "APPLE"
        elif 'whatsapp' in message_lower:
            return "WHATSAPP"
        elif 'instagram' in message_lower:
            return "INSTAGRAM"
        elif 'gmail' in message_lower:
            return "GMAIL"
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
                    message_text = cols[5].text.strip()
                    if message_text.startswith('REG-PS'):
                        continue
                    
                    sms_list.append({
                        'time': cols[0].text.strip(),
                        'phone': cols[2].text.strip(),
                        'client': cols[4].text.strip(),
                        'message': message_text
                    })
            
            if sms_list:
                logger.info(f"Found {len(sms_list)} valid SMS messages")
            return sms_list
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def monitor(self):
        logger.info("Starting OTP monitor (0.5 sec interval)...")
        logger.info("Browser will refresh every 1.5 seconds")
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = self.extract_otp(sms['message'])
                        if otp:
                            sms_id = f"{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                platform = self.extract_platform(sms['message'], sms['client'])
                                flag, country_code = self.get_country_flag_and_code(sms['phone'])
                                
                                logger.info(f"📱 NEW OTP! {otp} - {sms['phone']} - {platform}")
                                
                                result = await self.send_otp_to_telegram(
                                    flag, country_code, platform, sms['phone'], otp
                                )
                                
                                if result:
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    logger.info(f"✅ Total OTPs sent: {self.total_otps_sent}")
                                else:
                                    logger.error(f"❌ Failed to send OTP {otp}")
                                    
                                await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                self.refresh_counter += 1
                if self.refresh_counter >= 3:
                    self.driver.refresh()
                    logger.debug("Browser refreshed")
                    self.refresh_counter = 0
                    await asyncio.sleep(1.5)
                    
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
        print("BOLT SMS - OTP MONITOR BOT")
        print("="*60)
        print(f"Username: {USERNAME}")
        print(f"Telegram Chat: {GROUP_CHAT_ID}")
        print(f"Check Interval: 0.5 seconds")
        print(f"Browser Refresh: Every 1.5 seconds")
        if IS_RAILWAY:
            print("Running on Railway (Headless Mode)")
        else:
            print("Running on Local PC")
        print("="*60)
        
        print("\nSetting up browser...")
        if not self.setup_browser():
            print("Browser setup failed!")
            return
        
        print("\nLogging in...")
        if not self.auto_login():
            print("Login failed!")
            return
        
        print("\nLogin successful!")
        
        print("\n" + "="*60)
        print("Starting OTP Monitor...")
        print("="*60)
        print("Checking for new OTPs every 0.5 seconds")
        print("Browser refreshing every 1.5 seconds")
        if not IS_RAILWAY:
            print("Browser window will stay open")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\nBot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"Total OTPs sent: {bot.total_otps_sent}")
        print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())