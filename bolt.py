#!/usr/bin/env python3
"""
Bolt SMS - Automatic OTP Monitor Bot (Railway Compatible)
- Checks OTP every 0.5 seconds
- Refreshes browser every 1.5 seconds
- Forwards all OTPs from today on startup
- Duplicate OTP detection
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

# Second bot configuration (for custom format)
BOT_TOKEN_2 = "8639902314:AAENcAdowvvpHnU75UpLMcGRJ24yVizFMZg"
CHAT_ID_2 = "-1003818275876"

# Platform emoji mapping
PLATFORM_EMOJIS = {
    "WHATSAPP": {"short": "WS", "emoji_id": "5226815671261763813"},
    "TELEGRAM": {"short": "TG", "emoji_id": "5267139126339084336"},
    "FACEBOOK": {"short": "FB", "emoji_id": "5269492171416832604"},
    "INSTAGRAM": {"short": "IG", "emoji_id": "5226815671261763813"},
    "GMAIL": {"short": "GM", "emoji_id": "5226815671261763813"},
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
        
        patterns = [
            r'\b\d{4}\b', r'\b\d{5}\b', r'\b\d{6}\b',
            r'code[:\s]*\d+', r'OTP[:\s]*\d+',
            r'Telegram code[:\s]*\d+',
            r'WhatsApp code[:\s]*[\d-]+',
        ]
        self.otp_regex = re.compile('|'.join(patterns), re.IGNORECASE)
        
        logger.info("Bolt SMS OTP Monitor Bot Initialized")
        if IS_RAILWAY:
            logger.info("Running on Railway (Headless Mode)")
        else:
            logger.info("Running on Local PC (Browser Mode)")
    
    def _load_processed_otps(self):
        try:
            if os.path.exists('processed_otps.json'):
                with open('processed_otps.json', 'r') as f:
                    data = json.load(f)
                cutoff = datetime.now() - timedelta(hours=24)
                return {k for k, v in data.items() if datetime.fromisoformat(v) > cutoff}
        except:
            pass
        return set()
    
    def _save_processed_otps(self):
        try:
            data = {otp_id: datetime.now().isoformat() for otp_id in self.processed_otps}
            with open('processed_otps.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def get_country_flag_and_code(self, phone_number):
        """Get country flag emoji and country code from phone number"""
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone_number, None)
            country_code = parsed.country_code
            
            # Country code to flag mapping
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
            return flag, f"+{country_code}"
        except:
            return "🌍", ""
    
    def send_otp_custom_format(self, country_flag, country_code, platform, number, otp):
        """
        Send OTP in exact custom format - no extra text
        """
        try:
            # Platform logo
            platform_info = PLATFORM_EMOJIS.get(platform.upper(), PLATFORM_EMOJIS["OTHER"])
            platform_logo = f'<tg-emoji emoji-id="{platform_info["emoji_id"]}">{platform_info["short"]}</tg-emoji>'
            
            # Use full number without masking
            formatted_number = str(number)
            
            # Create message - ONLY the box
            message = (
                f"╭────────────────────╮\n"
                f"│ {country_flag} {country_code} {platform_logo} {formatted_number} │\n"
                f"╰────────────────────╯"
            )
            
            # Buttons
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"{otp}", "copy_text": {"text": otp}}],
                    [
                        {"text": "🚀 Number Panel", "url": "https://t.me/RTX_Number_Bot"},
                        {"text": "⚙️ Main Channel", "url": "https://t.me/TR_TECH_ZONE"}
                    ]
                ]
            }
            
            # Send to second chat using requests
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
            
            if response.status_code == 200:
                logger.info(f"Custom format OTP sent: {otp}")
                return True
            else:
                logger.error(f"Failed to send: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Custom format error: {e}")
            return False
    
    def setup_browser(self):
        try:
            chrome_options = Options()
            
            if IS_RAILWAY:
                # Railway Headless Mode
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
                # Local PC
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
        elif 'twitter' in message_lower or 'x.com' in message_lower:
            return "OTHER"
        elif 'apple' in message_lower or 'icloud' in message_lower:
            return "OTHER"
        elif 'microsoft' in message_lower or 'outlook' in message_lower:
            return "OTHER"
        elif 'amazon' in message_lower:
            return "OTHER"
        elif 'paypal' in message_lower:
            return "OTHER"
        elif 'binance' in message_lower or 'crypto' in message_lower:
            return "OTHER"
        elif 'discord' in message_lower:
            return "OTHER"
        elif 'spotify' in message_lower:
            return "OTHER"
        elif 'netflix' in message_lower:
            return "OTHER"
        elif 'tiktok' in message_lower:
            return "OTHER"
        elif 'signal' in message_lower:
            return "OTHER"
        else:
            return "OTHER"
    
    def extract_otp(self, message):
        if not isinstance(message, str):
            message = str(message)
        
        patterns = [
            (r'code[:\s]*(\d+)', 'code'),
            (r'OTP[:\s]*(\d+)', 'OTP'),
            (r'Telegram code[:\s]*(\d+)', 'Telegram'),
            (r'WhatsApp code[:\s]*([\d-]+)', 'WhatsApp'),
            (r'verification code[:\s]*(\d+)', 'verification'),
            (r'\b(\d{4})\b', '4 digit'),
            (r'\b(\d{5})\b', '5 digit'),
            (r'\b(\d{6})\b', '6 digit'),
        ]
        
        for pattern, name in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
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
                    sms_list.append({
                        'time': cols[0].text.strip(),
                        'phone': cols[2].text.strip(),
                        'client': cols[4].text.strip(),
                        'message': cols[5].text.strip()
                    })
            return sms_list
        except:
            return []
    
    async def send_startup_message(self):
        """Send startup notification to both chats"""
        try:
            startup_msg = "✅ Bot Started!"
            
            # Send to first chat
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=startup_msg,
                parse_mode="HTML"
            )
            
            # Send to second chat
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN_2}/sendMessage",
                json={
                    "chat_id": CHAT_ID_2,
                    "text": startup_msg,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
        except Exception as e:
            logger.error(f"Startup message error: {e}")
    
    async def send_all_today_otps(self):
        logger.info("Sending today's OTPs...")
        
        sms_list = self.get_sms()
        if not sms_list:
            await self.send_startup_message()
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                if sms_id not in self.processed_otps:
                    platform = self.extract_platform(sms['message'], sms['client'])
                    flag, country_code = self.get_country_flag_and_code(sms['phone'])
                    
                    # Send with custom format
                    if self.send_otp_custom_format(
                        flag, 
                        country_code, 
                        platform, 
                        sms['phone'], 
                        otp
                    ):
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                        await asyncio.sleep(1)
        
        logger.info(f"Sent {otp_count} OTPs")
        self._save_processed_otps()
        await self.send_startup_message()
    
    async def monitor(self):
        logger.info("Starting OTP monitor (0.5 sec interval)...")
        logger.info("Browser will refresh every 1.5 seconds")
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                        
                        if sms_id not in self.processed_otps:
                            otp = self.extract_otp(sms['message'])
                            if otp:
                                platform = self.extract_platform(sms['message'], sms['client'])
                                flag, country_code = self.get_country_flag_and_code(sms['phone'])
                                
                                logger.info(f"NEW OTP! {sms['time']} - {sms['phone']} - {platform}")
                                
                                # Send using custom format
                                if self.send_otp_custom_format(
                                    flag, 
                                    country_code, 
                                    platform, 
                                    sms['phone'], 
                                    otp
                                ):
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    self._save_processed_otps()
                                    logger.info(f"OTP #{self.total_otps_sent} sent")
                                    await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                # Refresh browser every 1.5 seconds
                self.refresh_counter += 1
                if self.refresh_counter >= 3:
                    self.driver.refresh()
                    logger.debug("Browser refreshed (1.5 seconds)")
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
        
        print("\nForwarding today's OTPs...")
        await self.send_all_today_otps()
        
        print("\n" + "="*60)
        print("Starting OTP Monitor...")
        print("="*60)
        print("Checking for new OTPs every 0.5 seconds")
        print("Browser refreshing every 1.5 seconds")
        print("New OTPs will be forwarded immediately")
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