#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Monitor Bot (Fixed Column Detection)
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
from selenium.common.exceptions import WebDriverException, NoAlertPresentException, UnexpectedAlertPresentException

# ========== CONFIGURATION ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None
PLATFORM_CACHE_FILE = "custom_platforms.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== COUNTRY DATA ==========
COUNTRIES = {
    '263': ('🇿🇼', '#ZW'), '880': ('🇧🇩', '#BD'), '91': ('🇮🇳', '#IN'),
    '1': ('🇺🇸', '#US'), '44': ('🇬🇧', '#UK'), '61': ('🇦🇺', '#AU'),
    '86': ('🇨🇳', '#CN'), '81': ('🇯🇵', '#JP'), '49': ('🇩🇪', '#DE'),
    '234': ('🇳🇬', '#NG'), '92': ('🇵🇰', '#PK'), '94': ('🇱🇰', '#LK'),
    '977': ('🇳🇵', '#NP'), '966': ('🇸🇦', '#SA'), '971': ('🇦🇪', '#AE'),
    '20': ('🇪🇬', '#EG'), '27': ('🇿🇦', '#ZA'), '90': ('🇹🇷', '#TR'),
}

# ========== BUILT-IN PLATFORM NAMES ==========
BUILTIN_PLATFORMS = {
    'telegram': ('🪁', 'Telegram'), 'whatsapp': ('💚', 'WhatsApp'),
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
        self.custom_platforms = self._load_custom_platforms()
        logger.info("🤖 Complete OTP Bot Initialized")
    
    def _load_custom_platforms(self):
        try:
            if os.path.exists(PLATFORM_CACHE_FILE):
                with open(PLATFORM_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_custom_platform(self, platform_name):
        try:
            if platform_name and platform_name not in self.custom_platforms:
                self.custom_platforms[platform_name] = True
                with open(PLATFORM_CACHE_FILE, 'w') as f:
                    json.dump(self.custom_platforms, f)
        except:
            pass
    
    def get_country_info(self, phone_number):
        try:
            clean_number = re.sub(r'\D', '', str(phone_number))
            if not clean_number:
                return "🇿🇼", "#ZW"
            
            # Check for Zimbabwe number
            if clean_number.startswith('263') or (len(clean_number) == 9 and clean_number.isdigit()):
                return "🇿🇼", "#ZW"
            
            for code, (flag, short) in COUNTRIES.items():
                if clean_number.startswith(code):
                    return flag, short
            return "🇿🇼", "#ZW"
        except:
            return "🇿🇼", "#ZW"
    
    def get_platform_info(self, cli, message):
        combined = f"{cli} {message}".lower()
        
        for key, (emoji, name) in BUILTIN_PLATFORMS.items():
            if key in combined:
                return emoji, name
        
        for platform_name in self.custom_platforms.keys():
            if platform_name.lower() in combined:
                return "📱", platform_name
        
        if cli and cli.strip() and len(cli.strip()) > 2:
            detected_name = cli.strip()
            self._save_custom_platform(detected_name)
            return "📱", detected_name
        
        return "📱", "Telegram"
    
    def hide_phone(self, phone):
        phone_str = re.sub(r'\D', '', str(phone))
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return "2637****0000"
    
    def handle_alert(self):
        try:
            alert = self.driver.switch_to.alert
            logger.warning(f"⚠️ Alert: {alert.text}")
            alert.accept()
            time.sleep(2)
            return True
        except:
            return False
    
    async def send_otp_to_telegram(self, country_flag, country_code, platform_emoji, platform_name, masked_phone, otp, is_new=True):
        try:
            if is_new:
                title = "🆕 NEW OTP!"
            else:
                title = "📜 Previous OTP"
            
            message = f"""{title}
{country_flag} {country_code} {platform_emoji} {platform_name} {masked_phone}

🔐 OTP: `{otp}`"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"📋 {otp} (Click to copy)", "copy_text": {"text": otp}}],
                    [
                        {"text": "🔢 Number Bot", "url": "https://t.me/Updateotpnew_bot"},
                        {"text": "📢 Main Channel", "url": "https://t.me/updaterange"}
                    ]
                ]
            }
            
            response = await asyncio.to_thread(
                requests.post,
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": GROUP_CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard,
                },
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ OTP sent: {otp}")
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
            for xpath in ["//div[contains(text(), 'What is')]", "//label[contains(text(), 'What is')]"]:
                try:
                    captcha_text = self.driver.find_element(By.XPATH, xpath).text
                    match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
                    if match:
                        result = int(match.group(1)) + int(match.group(2))
                        captcha_input = self.driver.find_element(By.NAME, "capt")
                        captcha_input.clear()
                        captcha_input.send_keys(str(result))
                        logger.info(f"✅ Captcha solved")
                        return True
                except:
                    continue
            return False
        except:
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
                time.sleep(10)
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
            r'Telegram code[:\s]*(\d{4,8})',
            r'code[:\s]*(\d{4,8})',
            r'OTP[:\s]*(\d{4,8})',
            r'#(\d{4,8})',
            r'\b(\d{5,8})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                otp = match.group(1)
                if len(otp) >= 4 and otp.isdigit():
                    return otp
        return None
    
    def get_all_sms(self):
        """Get all SMS - Auto detect columns"""
        try:
            self.handle_alert()
            time.sleep(2)
            
            # Find all rows
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                rows = self.driver.find_elements(By.XPATH, "//table//tr")
            
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 2:
                        continue
                    
                    # First, try to find phone number (12 digit number starting with 263)
                    phone = ""
                    cli = ""
                    sms_text = ""
                    
                    # Method 1: Look for number pattern in all columns
                    all_row_text = " ".join([col.text for col in cols])
                    
                    # Find Zimbabwe phone number (263XXXXXXXXX)
                    phone_match = re.search(r'\b(263\d{9})\b', all_row_text)
                    if phone_match:
                        phone = phone_match.group(1)
                        logger.info(f"📱 Phone found: {phone}")
                    
                    # Method 2: If not found, try to find any 10-12 digit number
                    if not phone:
                        phone_match = re.search(r'\b(\d{10,12})\b', all_row_text)
                        if phone_match:
                            phone = phone_match.group(1)
                            logger.info(f"📱 Phone found (10-12 digit): {phone}")
                    
                    # Find CLI (Telegram, WhatsApp, etc.)
                    for col in cols:
                        col_text = col.text.strip()
                        if col_text.lower() in ['telegram', 'whatsapp', 'facebook', 'instagram']:
                            cli = col_text
                            break
                    
                    # Find SMS/Message column (long text with code)
                    for col in cols:
                        col_text = col.text.strip()
                        if len(col_text) > 20 or ('code' in col_text.lower() and len(col_text) > 5):
                            sms_text = col_text
                            break
                    
                    # If still no SMS, use the longest column
                    if not sms_text:
                        for col in cols:
                            if len(col.text.strip()) > len(sms_text):
                                sms_text = col.text.strip()
                    
                    # Extract OTP
                    otp = self.extract_otp(sms_text)
                    
                    if otp:
                        # Get platform
                        platform_emoji, platform_name = self.get_platform_info(cli, sms_text)
                        
                        logger.info(f"📱 OTP: {otp} | Phone: {phone} | Platform: {platform_name}")
                        
                        sms_list.append({
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'phone': phone if phone else "2637****0000",
                            'client': platform_name,
                            'platform_emoji': platform_emoji,
                            'message': sms_text,
                            'otp': otp
                        })
                    else:
                        # Try to find OTP in row text
                        otp = self.extract_otp(all_row_text)
                        if otp:
                            platform_emoji, platform_name = self.get_platform_info(cli, all_row_text)
                            logger.info(f"📱 OTP from row: {otp}")
                            sms_list.append({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'phone': phone if phone else "2637****0000",
                                'client': platform_name,
                                'platform_emoji': platform_emoji,
                                'message': all_row_text,
                                'otp': otp
                            })
                            
                except Exception as e:
                    continue
            
            logger.info(f"📊 Total OTPs found: {len(sms_list)}")
            return sms_list
            
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def send_all_existing_otps(self):
        logger.info("📤 Sending all existing OTPs...")
        
        sms_list = self.get_all_sms()
        if not sms_list:
            logger.info("No existing OTPs found")
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = sms.get('otp')
            if otp:
                sms_id = f"{sms['phone']}_{otp}"
                if sms_id not in self.processed_otps:
                    country_flag, country_code = self.get_country_info(sms['phone'])
                    masked_phone = self.hide_phone(sms['phone'])
                    
                    logger.info(f"📜 Sending: {otp}")
                    
                    result = await self.send_otp_to_telegram(
                        country_flag, country_code, 
                        sms['platform_emoji'], sms['client'], 
                        masked_phone, otp, False
                    )
                    
                    if result:
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                    
                    await asyncio.sleep(1)
        
        logger.info(f"✅ Sent {otp_count} existing OTPs")
        
        startup_msg = f"""✅ **Bot Started Successfully!**
━━━━━━━━━━━━━━━━━━━━
📊 **Sent:** {otp_count} OTPs
⚡ **Check:** 0.5 sec | **Refresh:** 2 sec
⏰ **Started:** {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange"""
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "🔢 Number Bot", "url": "https://t.me/Updateotpnew_bot"},
                {"text": "📢 Main Channel", "url": "https://t.me/updaterange"}
            ]]
        }
        
        try:
            await asyncio.to_thread(
                requests.post,
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": GROUP_CHAT_ID,
                    "text": startup_msg,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard,
                },
                timeout=10
            )
        except:
            pass
    
    async def monitor(self):
        logger.info("🚀 Starting OTP monitor...")
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                sms_list = self.get_all_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = sms.get('otp')
                        if otp:
                            sms_id = f"{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                country_flag, country_code = self.get_country_info(sms['phone'])
                                masked_phone = self.hide_phone(sms['phone'])
                                
                                logger.info(f"🆕 NEW OTP: {otp}")
                                
                                result = await self.send_otp_to_telegram(
                                    country_flag, country_code,
                                    sms['platform_emoji'], sms['client'],
                                    masked_phone, otp, True
                                )
                                
                                if result:
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                
                                await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                await asyncio.sleep(max(0, 0.5 - elapsed))
                
                self.refresh_counter += 1
                if self.refresh_counter >= 4:
                    try:
                        self.driver.refresh()
                        self.refresh_counter = 0
                        await asyncio.sleep(2)
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
        print(f"⚡ Check: 0.5 sec | Refresh: 2 sec")
        print("="*60)
        
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        if not self.auto_login():
            print("❌ Login failed!")
            return
        
        print("\n✅ Login successful!")
        
        print("\n📤 Sending existing OTPs...")
        await self.send_all_existing_otps()
        
        print("\n🚀 Monitoring...")
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"📊 Total: {bot.total_otps_sent}")


if __name__ == "__main__":
    asyncio.run(main())