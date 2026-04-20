#!/usr/bin/env python3
"""
Bolt SMS - рж╕ржорзНржкрзВрж░рзНржг ржЕржЯрзЛржорзЗржЯрж┐ржХ OTP ржоржирж┐ржЯрж░ ржмржЯ (Railway ржЙржкржпрзЛржЧрзА)
- 0.5 рж╕рзЗржХрзЗржирзНржб ржкрж░ржкрж░ OTP ржЪрзЗржХ ржХрж░рзЗ
- ржкрзНрж░рждрж┐ 1.5 рж╕рзЗржХрзЗржирзНржб ржкрж░ржкрж░ ржмрзНрж░рж╛ржЙржЬрж╛рж░ рж░рж┐ржлрзНрж░рзЗрж╢ ржХрж░рзЗ
- ржЪрж╛рж▓рзБ рж╣ржУржпрж╝рж╛рж░ рж╕рж╛ржерзЗ рж╕рж╛ржерзЗ ржЖржЬржХрзЗрж░ рж╕ржм OTP ржлрж░ржУржпрж╝рж╛рж░рзНржб ржХрж░рзЗ
- ржбрзБржкрзНрж▓рж┐ржХрзЗржЯ OTP ржПржбрж╝рж╛ржпрж╝
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ========== ржХржиржлрж┐ржЧрж╛рж░рзЗрж╢ржи ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

# Railway ржП headless mode ржЪрж╛рж▓рж╛ржирзЛрж░ ржЬржирзНржп ржЪрзЗржХ
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
        
        logger.info("ЁЯдЦ Bolt SMS OTP Monitor Bot Initialized")
        if IS_RAILWAY:
            logger.info("ЁЯЪА Running on Railway (Headless Mode)")
        else:
            logger.info("ЁЯТ╗ Running on Local PC (Browser Mode)")
    
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
    
    def setup_browser(self):
        try:
            chrome_options = Options()
            
            if IS_RAILWAY:
                # Railway ржПрж░ ржЬржирзНржп Headless Mode
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-extensions')
                chrome_options.add_argument('--disable-setuid-sandbox')
                chrome_options.add_argument('--remote-debugging-port=9222')
                
                # Chrome binary path
                chrome_options.binary_location = "/usr/bin/google-chrome"
                
                # рж╕рж░рж╛рж╕рж░рж┐ ChromeDriver ржмрзНржпржмрж╣рж╛рж░ ржХрж░рзБржи (webdriver-manager ржЫрж╛ржбрж╝рж╛)
                service = Service(executable_path="/usr/local/bin/chromedriver")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("тЬЕ Browser opened on Railway (Headless Mode)")
            else:
                # рж▓рзЛржХрж╛рж▓ ржкрж┐рж╕рж┐рж░ ржЬржирзНржп
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                if not os.path.exists(chromedriver_path):
                    logger.error(f"тЭМ ChromeDriver not found at: {chromedriver_path}")
                    return False
                
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("тЬЕ Browser opened on Local PC")
            
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
                logger.info(f"ЁЯФН Captcha: {num1} + {num2} = {result}")
                
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
            logger.info("ЁЯФР Logging in...")
            
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info(f"тЬЕ Username: {USERNAME}")
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("тЬЕ Password entered")
            
            time.sleep(1)
            self.solve_captcha()
            
            time.sleep(1)
            try:
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                logger.info("тЬЕ Login button clicked")
            except:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                    login_btn.click()
                    logger.info("тЬЕ Login button clicked")
                except:
                    try:
                        login_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Sign In')]")
                        login_btn.click()
                        logger.info("тЬЕ Login button clicked")
                    except:
                        form = self.driver.find_element(By.TAG_NAME, "form")
                        form.submit()
                        logger.info("тЬЕ Form submitted")
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"ЁЯУН URL: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("тЬЕтЬЕтЬЕ LOGIN SUCCESSFUL! тЬЕтЬЕтЬЕ")
                self.logged_in = True
                
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                logger.info("ЁЯУ▒ SMS page loaded")
                return True
            else:
                logger.error("тЭМ Login failed!")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_platform(self, message, client):
        """ржорзЗрж╕рзЗржЬ ржПржмржВ ржХрзНрж▓рж╛ржпрж╝рзЗржирзНржЯ ржерзЗржХрзЗ ржкрзНрж▓рзНржпрж╛ржЯржлрж░рзНржорзЗрж░ ржирж╛ржо ржмрзЗрж░ ржХрж░рзЗ"""
        message_lower = message.lower()
        client_lower = str(client).lower()
        
        if 'telegram' in message_lower or 'telegram' in client_lower:
            return "ЁЯУи Telegram"
        elif 'whatsapp' in message_lower or 'whatsapp' in client_lower:
            return "ЁЯТЪ WhatsApp"
        elif 'instagram' in message_lower:
            return "ЁЯУ╕ Instagram"
        elif 'facebook' in message_lower or 'fb' in message_lower:
            return "ЁЯУШ Facebook"
        elif 'gmail' in message_lower or 'google' in message_lower:
            return "ЁЯУз Gmail"
        elif 'twitter' in message_lower or 'x.com' in message_lower:
            return "ЁЯРж Twitter/X"
        elif 'apple' in message_lower or 'icloud' in message_lower:
            return "ЁЯНО Apple"
        elif 'microsoft' in message_lower or 'outlook' in message_lower:
            return "ЁЯТ╗ Microsoft"
        elif 'amazon' in message_lower:
            return "ЁЯУж Amazon"
        elif 'paypal' in message_lower:
            return "ЁЯТ░ PayPal"
        elif 'binance' in message_lower or 'crypto' in message_lower:
            return "ЁЯУК Binance/Crypto"
        elif 'discord' in message_lower:
            return "ЁЯОо Discord"
        elif 'spotify' in message_lower:
            return "ЁЯО╡ Spotify"
        elif 'netflix' in message_lower:
            return "ЁЯУ║ Netflix"
        elif 'tiktok' in message_lower:
            return "ЁЯОм TikTok"
        elif 'signal' in message_lower:
            return "ЁЯФТ Signal"
        else:
            return "ЁЯУ▒ Other"
    
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
    
    def hide_phone(self, phone):
        phone_str = str(phone)
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
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
    
    async def send_telegram(self, msg):
        try:
            keyboard = [[
                InlineKeyboardButton("ЁЯУв Main Channel", url="https://t.me/updaterange"),
                InlineKeyboardButton("ЁЯдЦ Number Bot", url="https://t.me/Updateotpnew_bot"),
                InlineKeyboardButton("ЁЯСитАНЁЯТ╗ Developer", url="https://t.me/rana1132")
            ]]
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def send_all_today_otps(self):
        logger.info("ЁЯУд Sending today's OTPs...")
        
        sms_list = self.get_sms()
        if not sms_list:
            await self.send_telegram("ЁЯУн No OTPs found for today")
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                if sms_id not in self.processed_otps:
                    phone = self.hide_phone(sms['phone'])
                    platform = self.extract_platform(sms['message'], sms['client'])
                    
                    msg = f"""
ЁЯУЬ **Previous OTP**
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ

ЁЯУЕ **Time:** `{sms['time']}`
ЁЯУ▒ **Phone:** `{phone}`
{platform}

ЁЯФР **OTP Code:** `{otp}`

тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
ЁЯдЦ @updaterange
"""
                    if await self.send_telegram(msg):
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                        await asyncio.sleep(1)
        
        logger.info(f"тЬЕ Sent {otp_count} OTPs")
        self._save_processed_otps()
        
        await self.send_telegram(
            f"тЬЕ **Startup Complete!**\n"
            f"тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ\n"
            f"ЁЯУК **Today's OTPs:** {otp_count}\n"
            f"тЪб **Check Interval:** 0.5 seconds\n"
            f"ЁЯФД **Browser Refresh:** Every 1.5 seconds\n"
            f"ЁЯФД **Status:** Monitoring\n"
            f"тП░ **Started:** {datetime.now().strftime('%H:%M:%S')}\n"
            f"тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ"
        )
    
    async def monitor(self):
        logger.info("ЁЯЪА Starting OTP monitor (0.5 sec interval)...")
        logger.info("ЁЯФД Browser will refresh every 1.5 seconds")
        
        await self.send_telegram(f"тЬЕ Bot Started!\nUser: {USERNAME}")
        
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
                                phone = self.hide_phone(sms['phone'])
                                
                                logger.info(f"ЁЯЖХ NEW OTP! {sms['time']} - {phone} - {platform}")
                                
                                msg = f"""
ЁЯЖХ **NEW OTP!**
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ

ЁЯУЕ **Time:** `{sms['time']}`
ЁЯУ▒ **Phone:** `{phone}`
{platform}

ЁЯФР **OTP Code:** `{otp}`

ЁЯУЭ **Message:**
`{sms['message'][:300]}`

тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
ЁЯдЦ @updaterange
"""
                                if await self.send_telegram(msg):
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    self._save_processed_otps()
                                    logger.info(f"тЬЕ OTP #{self.total_otps_sent} sent")
                                    await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                # ржкрзНрж░рждрж┐ 1.5 рж╕рзЗржХрзЗржирзНржбрзЗ ржмрзНрж░рж╛ржЙржЬрж╛рж░ рж░рж┐ржлрзНрж░рзЗрж╢
                self.refresh_counter += 1
                if self.refresh_counter >= 3:
                    self.driver.refresh()
                    logger.debug("ЁЯФД Browser refreshed (1.5 seconds)")
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
        print("ЁЯдЦ BOLT SMS - OTP MONITOR BOT")
        print("="*60)
        print(f"ЁЯУЭ Username: {USERNAME}")
        print(f"ЁЯУ▒ Telegram: {GROUP_CHAT_ID}")
        print(f"тЪб Check Interval: 0.5 seconds")
        print(f"ЁЯФД Browser Refresh: Every 1.5 seconds")
        if IS_RAILWAY:
            print("ЁЯЪА Running on Railway (Headless Mode)")
        else:
            print("ЁЯТ╗ Running on Local PC")
        print("="*60)
        
        print("\nЁЯФз Setting up browser...")
        if not self.setup_browser():
            print("тЭМ Browser setup failed!")
            return
        
        print("\nЁЯФР Logging in...")
        if not self.auto_login():
            print("тЭМ Login failed!")
            await self.send_telegram("тЭМ **Login Failed!**")
            return
        
        print("\nтЬЕ Login successful!")
        
        print("\nЁЯУд Forwarding today's OTPs...")
        await self.send_all_today_otps()
        
        print("\n" + "="*60)
        print("ЁЯЪА Starting OTP Monitor...")
        print("="*60)
        print("тЪб Checking for new OTPs every 0.5 seconds")
        print("ЁЯФД Browser refreshing every 1.5 seconds")
        print("ЁЯУ▒ New OTPs will be forwarded immediately")
        if not IS_RAILWAY:
            print("ЁЯМР Browser window will stay open")
        print("ЁЯТ╛ Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\nЁЯЫС Bot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"ЁЯУК Total OTPs sent: {bot.total_otps_sent}")
        print("ЁЯСЛ Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())