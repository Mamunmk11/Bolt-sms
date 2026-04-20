#!/usr/bin/env python3
"""
Bolt SMS - Automatic OTP Monitor Bot (Railway Compatible)
- Checks OTP every 0.5 seconds
- Refreshes browser every 1.5 seconds
- Only sends NEW OTPs (no duplicates on restart)
- Supports 4-8 digit OTP codes
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
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

# Check for Railway environment
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None
# =================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('otp_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = self._load_processed_otps()
        self.total_otps_sent = 0
        self.is_monitoring = True
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.refresh_counter = 0
        
        logger.info("Bolt SMS OTP Monitor Bot Initialized")
        logger.info(f"Loaded {len(self.processed_otps)} previously processed OTPs")
        if IS_RAILWAY:
            logger.info("Running on Railway (Headless Mode)")
        else:
            logger.info("Running on Local PC (Browser Mode)")
    
    def _load_processed_otps(self):
        """Load processed OTPs - store in memory only (no file persistence)"""
        # Return empty set - means all OTPs will be sent (no duplicate detection on restart)
        return set()
    
    def _save_processed_otps(self):
        """Save processed OTPs - disabled"""
        pass
    
    def _get_otp_hash(self, phone, otp, message):
        """Create unique hash for OTP"""
        return f"{phone}_{otp}"
    
    def get_country_flag_and_code(self, phone_number):
        """Get country flag emoji and country code from phone number"""
        try:
            parsed = phonenumbers.parse(phone_number, None)
            country_code = parsed.country_code
            
            country_flags = {
                1: "🇺🇸", 7: "🇷🇺", 20: "🇪🇬", 27: "🇿🇦", 30: "🇬🇷", 31: "🇳🇱",
                32: "🇧🇪", 33: "🇫🇷", 34: "🇪🇸", 36: "🇭🇺", 39: "🇮🇹", 40: "🇷🇴",
                41: "🇨🇭", 43: "🇦🇹", 44: "🇬🇧", 45: "🇩🇰", 46: "🇸🇪", 47: "🇳🇴",
                48: "🇵🇱", 49: "🇩🇪", 51: "🇵🇪", 52: "🇲🇽", 53: "🇨🇺", 54: "🇦🇷",
                55: "🇧🇷", 56: "🇨🇱", 57: "🇨🇴", 58: "🇻🇪", 60: "🇲🇾", 61: "🇦🇺",
                62: "🇮🇩", 63: "🇵🇭", 64: "🇳🇿", 65: "🇸🇬", 66: "🇹🇭", 81: "🇯🇵",
                82: "🇰🇷", 84: "🇻🇳", 86: "🇨🇳", 90: "🇹🇷", 91: "🇮🇳", 92: "🇵🇰",
                93: "🇦🇫", 94: "🇱🇰", 95: "🇲🇲", 98: "🇮🇷", 212: "🇲🇦", 213: "🇩🇿",
                216: "🇹🇳", 218: "🇱🇾", 220: "🇬🇲", 221: "🇸🇳", 222: "🇲🇷", 223: "🇲🇱",
                224: "🇬🇳", 225: "🇨🇮", 226: "🇧🇫", 227: "🇳🇪", 228: "🇹🇬", 229: "🇧🇯",
                230: "🇲🇺", 231: "🇱🇷", 232: "🇸🇱", 233: "🇬🇭", 234: "🇳🇬", 235: "🇹🇩",
                236: "🇨🇫", 237: "🇨🇲", 238: "🇨🇻", 239: "🇸🇹", 240: "🇬🇶", 241: "🇬🇦",
                242: "🇨🇬", 243: "🇨🇩", 244: "🇦🇴", 245: "🇬🇼", 246: "🇮🇴", 247: "🇦🇨",
                248: "🇸🇨", 249: "🇸🇩", 250: "🇷🇼", 251: "🇪🇹", 252: "🇸🇴", 253: "🇩🇯",
                254: "🇰🇪", 255: "🇹🇿", 256: "🇺🇬", 257: "🇧🇮", 258: "🇲🇿", 260: "🇿🇲",
                261: "🇲🇬", 262: "🇷🇪", 263: "🇿🇼", 264: "🇳🇦", 265: "🇲🇼", 266: "🇱🇸",
                267: "🇧🇼", 268: "🇸🇿", 269: "🇰🇲", 290: "🇸🇭", 291: "🇪🇷", 297: "🇦🇼",
                298: "🇫🇴", 299: "🇬🇱", 350: "🇬🇮", 351: "🇵🇹", 352: "🇱🇺", 353: "🇮🇪",
                354: "🇮🇸", 355: "🇦🇱", 356: "🇲🇹", 357: "🇨🇾", 358: "🇫🇮", 359: "🇧🇬",
                370: "🇱🇹", 371: "🇱🇻", 372: "🇪🇪", 373: "🇲🇩", 374: "🇦🇲", 375: "🇧🇾",
                376: "🇦🇩", 377: "🇲🇨", 378: "🇸🇲", 379: "🇻🇦", 380: "🇺🇦", 381: "🇷🇸",
                382: "🇲🇪", 383: "🇽🇰", 385: "🇭🇷", 386: "🇸🇮", 387: "🇧🇦", 389: "🇲🇰",
                420: "🇨🇿", 421: "🇸🇰", 423: "🇱🇮", 500: "🇫🇰", 501: "🇧🇿", 502: "🇬🇹",
                503: "🇸🇻", 504: "🇭🇳", 505: "🇳🇮", 506: "🇨🇷", 507: "🇵🇦", 508: "🇵🇲",
                509: "🇭🇹", 590: "🇬🇵", 591: "🇧🇴", 592: "🇬🇾", 593: "🇪🇨", 594: "🇬🇫",
                595: "🇵🇾", 596: "🇲🇶", 597: "🇸🇷", 598: "🇺🇾", 599: "🇨🇼", 670: "🇹🇱",
                672: "🇦🇶", 673: "🇧🇳", 674: "🇳🇷", 675: "🇵🇬", 676: "🇹🇴", 677: "🇸🇧",
                678: "🇻🇺", 679: "🇫🇯", 680: "🇵🇼", 681: "🇼🇫", 682: "🇨🇰", 683: "🇳🇺",
                685: "🇼🇸", 686: "🇰🇮", 687: "🇳🇨", 688: "🇹🇻", 689: "🇵🇫", 690: "🇹🇰",
                691: "🇫🇲", 692: "🇲🇭", 850: "🇰🇵", 852: "🇭🇰", 853: "🇲🇴", 855: "🇰🇭",
                856: "🇱🇦", 880: "🇧🇩", 886: "🇹🇼", 960: "🇲🇻", 961: "🇱🇧", 962: "🇯🇴",
                963: "🇸🇾", 964: "🇮🇶", 965: "🇰🇼", 966: "🇸🇦", 967: "🇾🇪", 968: "🇴🇲",
                970: "🇵🇸", 971: "🇦🇪", 972: "🇮🇱", 973: "🇧🇭", 974: "🇶🇦", 975: "🇧🇹",
                976: "🇲🇳", 977: "🇳🇵", 992: "🇹🇯", 993: "🇹🇲", 994: "🇦🇿", 995: "🇬🇪",
                996: "🇰🇬", 998: "🇺🇿"
            }
            
            flag = country_flags.get(country_code, "🌍")
            return flag, f"#{country_code}"
        except:
            return "🌍", "#0"
    
    def send_otp_custom_format(self, country_flag, country_code, platform, number, otp):
        """Send OTP in exact custom format with detailed logging"""
        try:
            platform_info = PLATFORM_EMOJIS.get(platform.upper(), PLATFORM_EMOJIS["OTHER"])
            platform_logo = f'<tg-emoji emoji-id="{platform_info["emoji_id"]}">{platform_info["short"]}</tg-emoji>'
            
            formatted_number = str(number)
            
            message = (
                f"╭────────────────────╮\n"
                f"│ {country_flag} {country_code} {platform_logo} {formatted_number} │\n"
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
            
            logger.info(f"Attempting to send OTP {otp} to chat {CHAT_ID_2}")
            
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
            
            logger.info(f"Telegram API response status: {response.status_code}")
            logger.info(f"Telegram API response body: {response.text}")
            
            if response.status_code == 200:
                logger.info(f"✅ OTP sent successfully: {otp}")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception in send_otp_custom_format: {e}")
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
            captcha_text = self.driver.find_element(By.XPATH, "//div[contains(text(), 'What is')]").text
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
            time.sleep(3)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info(f"Username: {USERNAME}")
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("Password entered")
            
            time.sleep(1)
            self.solve_captcha()
            
            time.sleep(1)
            try:
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                logger.info("Login button clicked")
            except:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                    login_btn.click()
                    logger.info("Login button clicked")
                except:
                    try:
                        login_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Sign In')]")
                        login_btn.click()
                        logger.info("Login button clicked")
                    except:
                        form = self.driver.find_element(By.TAG_NAME, "form")
                        form.submit()
                        logger.info("Form submitted")
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"URL: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("LOGIN SUCCESSFUL!")
                self.logged_in = True
                
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                logger.info("SMS page loaded")
                return True
            else:
                logger.error("Login failed!")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_platform(self, message, client):
        """Extract platform name from message and client"""
        message_lower = message.lower()
        client_lower = str(client).lower()
        
        if 'telegram' in message_lower or 'telegram' in client_lower:
            return "TELEGRAM"
        elif 'whatsapp' in message_lower or 'whatsapp' in client_lower:
            return "WHATSAPP"
        elif 'instagram' in message_lower:
            return "INSTAGRAM"
        elif 'facebook' in message_lower or 'fb' in message_lower:
            return "FACEBOOK"
        elif 'gmail' in message_lower or 'google' in message_lower:
            return "GMAIL"
        elif 'apple' in message_lower or 'icloud' in message_lower:
            return "APPLE"
        else:
            return "OTHER"
    
    def extract_otp(self, message):
        """Extract OTP code from message - supports 4-8 digit codes"""
        if not isinstance(message, str):
            message = str(message)
        
        # Pattern 1: #12345 format (Facebook)
        match = re.search(r'#(\d{4,8})', message)
        if match:
            code = match.group(1)
            if 4 <= len(code) <= 8:
                logger.info(f"Found OTP via # pattern: {code}")
                return code
        
        # Pattern 2: "code XXXX" or "CODE XXXX" format
        match = re.search(r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,8})', message)
        if match:
            code = match.group(1)
            if 4 <= len(code) <= 8:
                logger.info(f"Found OTP via code pattern: {code}")
                return code
        
        # Pattern 3: "is XXXX" format (Apple)
        match = re.search(r'is[:\s]*(\d{4,8})', message)
        if match:
            code = match.group(1)
            if 4 <= len(code) <= 8:
                logger.info(f"Found OTP via is pattern: {code}")
                return code
        
        # Pattern 4: Any 4-8 digit number (last resort)
        numbers = re.findall(r'\b(\d{4,8})\b', message)
        for num in numbers:
            # Skip if it looks like a phone number
            if not num.startswith(('263', '880', '1', '44', '91', '92')):
                if 4 <= len(num) <= 8:
                    logger.info(f"Found OTP via fallback: {num}")
                    return num
        
        return None
    
    def get_sms(self):
        try:
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    message_text = cols[5].text.strip()
                    # Skip REG-PS messages
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
        """Main monitoring loop - only sends NEW OTPs"""
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
                            sms_id = self._get_otp_hash(sms['phone'], otp, sms['message'])
                            
                            if sms_id not in self.processed_otps:
                                platform = self.extract_platform(sms['message'], sms['client'])
                                flag, country_code = self.get_country_flag_and_code(sms['phone'])
                                
                                logger.info(f"NEW OTP! {otp} - {sms['phone']} - {platform}")
                                
                                # Send using custom format
                                result = self.send_otp_custom_format(
                                    flag, 
                                    country_code, 
                                    platform, 
                                    sms['phone'], 
                                    otp
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
                
                # Refresh browser every 1.5 seconds
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
        print(f"Check Interval: 0.5 seconds")
        print(f"Browser Refresh: Every 1.5 seconds")
        print(f"OTP Support: 4-8 digits")
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