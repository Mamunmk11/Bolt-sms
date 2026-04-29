#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Monitor Bot (Fixed for 2-column table)
Table structure: CLI | SMS (OTP code is in SMS column)
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
from selenium.common.exceptions import WebDriverException, NoAlertPresentException

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
    '263': ('🇿🇼', '#ZW'), '880': ('🇧🇩', '#BD'), '91': ('🇮🇳', '#IN'),
    '1': ('🇺🇸', '#US'), '44': ('🇬🇧', '#UK'), '61': ('🇦🇺', '#AU'),
    '86': ('🇨🇳', '#CN'), '81': ('🇯🇵', '#JP'), '49': ('🇩🇪', '#DE'),
}

PLATFORM_NAMES = {
    'telegram': ('🪁', 'Telegram'), 'whatsapp': ('💚', 'WhatsApp'),
    'facebook': ('📘', 'Facebook'), 'instagram': ('📸', 'Instagram'),
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
            for code, (flag, short) in COUNTRIES.items():
                if clean_number.startswith(code):
                    return flag, short
            return "🌍", "#??"
        except:
            return "🌍", "#??"
    
    def get_platform_info(self, client_name, message):
        combined = f"{client_name} {message}".lower()
        if 'telegram' in combined:
            return "🪁", "Telegram"
        elif 'whatsapp' in combined:
            return "💚", "WhatsApp"
        elif 'facebook' in combined:
            return "📘", "Facebook"
        return "📱", client_name if client_name else "Unknown"
    
    def hide_phone(self, phone):
        phone_str = re.sub(r'\D', '', str(phone))
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
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
    
    async def send_otp_to_telegram(self, country_flag, country_code, platform_emoji, platform_name, masked_number, otp, is_new=True):
        """Send OTP to Telegram"""
        try:
            if is_new:
                title = "🆕 NEW OTP!"
            else:
                title = "📜 Previous OTP"
            
            message = f"""{title}
{country_flag} {country_code} {platform_emoji} {platform_name} {masked_number}

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
                timeout=10
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
                        logger.info(f"✅ Captcha solved: {match.group(1)} + {match.group(2)} = {result}")
                        return True
                except:
                    continue
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
                time.sleep(10)  # বেশি সময় দিন পেজ লোডের জন্য
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
        """Extract OTP from message"""
        if not isinstance(message, str):
            return None
        
        patterns = [
            r'Telegram code[:\s]*(\d{4,8})',
            r'WhatsApp code[:\s]*(\d{4,8})',
            r'code[:\s]*(\d{4,8})',
            r'verification code[:\s]*(\d{4,8})',
            r'(\d{5,8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                otp = match.group(1)
                if len(otp) >= 4:
                    return otp
        return None
    
    def get_all_sms(self):
        """Get all SMS from the page - Your table has 2 columns: CLI | SMS"""
        try:
            self.handle_alert()
            time.sleep(2)
            
            # Find all table rows
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                rows = self.driver.find_elements(By.XPATH, "//table//tr")
            
            if not rows:
                logger.warning("❌ No rows found")
                return []
            
            sms_list = []
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    # Skip if less than 2 columns
                    if len(cols) < 2:
                        continue
                    
                    # Your table structure:
                    # Col 0: CLI (Telegram, WhatsApp, etc.)
                    # Col 1: SMS (Full message with OTP code)
                    
                    cli = cols[0].text.strip()
                    sms_text = cols[1].text.strip()
                    
                    # If SMS column is empty but CLI has text, use CLI as message
                    if not sms_text and cli:
                        sms_text = cli
                        cli = "Unknown"
                    
                    if not sms_text:
                        continue
                    
                    # Check if this row has OTP code
                    otp = self.extract_otp(sms_text)
                    
                    if otp:
                        logger.info(f"📱 Found OTP: {otp} from CLI: {cli}")
                        
                        sms_list.append({
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'phone': "2637****0000",
                            'client': cli if cli else "Telegram",
                            'message': sms_text,
                            'otp': otp
                        })
                    else:
                        logger.debug(f"⏭️ Skipping row (no OTP): {sms_text[:50]}")
                        
                except Exception as e:
                    logger.debug(f"Row parse error: {e}")
                    continue
            
            logger.info(f"📊 Total OTPs found: {len(sms_list)}")
            
            # If no OTPs found in table, search page text directly
            if not sms_list:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                direct_otps = re.findall(r'Telegram code[:\s]*(\d{4,8})', page_text, re.IGNORECASE)
                for otp in direct_otps:
                    logger.info(f"🔍 Found OTP directly in page: {otp}")
                    sms_list.append({
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'phone': "2637****0000",
                        'client': "Telegram",
                        'message': f"Telegram code {otp}",
                        'otp': otp
                    })
            
            return sms_list
            
        except Exception as e:
            logger.error(f"Get SMS error: {e}")
            return []
    
    async def send_all_existing_otps(self):
        """Send all existing OTPs on startup"""
        logger.info("📤 Sending all existing OTPs...")
        
        sms_list = self.get_all_sms()
        if not sms_list:
            logger.info("No existing OTPs found")
            await self.send_otp_to_telegram("🌍", "#??", "📱", "Info", "", "No OTPs found", False)
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = sms.get('otp') or self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['phone']}_{otp}"
                if sms_id not in self.processed_otps:
                    country_flag, country_code = self.get_country_info(sms['phone'])
                    platform_emoji, platform_name = self.get_platform_info(sms['client'], sms['message'])
                    masked_number = self.hide_phone(sms['phone'])
                    
                    logger.info(f"📜 Sending existing OTP: {otp}")
                    
                    result = await self.send_otp_to_telegram(
                        country_flag, country_code, platform_emoji, 
                        platform_name, masked_number, otp, False
                    )
                    
                    if result:
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                    
                    await asyncio.sleep(1)
        
        logger.info(f"✅ Sent {otp_count} existing OTPs")
        
        # Send startup complete message
        startup_msg = f"""✅ **Bot Started Successfully!**
━━━━━━━━━━━━━━━━━━━━
📊 **Existing OTPs Sent:** {otp_count}
⚡ **Check Interval:** 0.5 seconds
🔄 **Browser Refresh:** Every 2 seconds
⏰ **Started:** {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange"""
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔢 Number Bot", "url": "https://t.me/Updateotpnew_bot"},
                    {"text": "📢 Main Channel", "url": "https://t.me/updaterange"}
                ]
            ]
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
        """Monitor for new OTPs"""
        logger.info("🚀 Starting OTP monitor (0.5 sec interval)...")
        logger.info("🔄 Browser will refresh every 2 seconds")
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                sms_list = self.get_all_sms()
                
                if sms_list:
                    for sms in sms_list:
                        otp = sms.get('otp') or self.extract_otp(sms['message'])
                        if otp:
                            sms_id = f"{sms['phone']}_{otp}"
                            
                            if sms_id not in self.processed_otps:
                                country_flag, country_code = self.get_country_info(sms['phone'])
                                platform_emoji, platform_name = self.get_platform_info(sms['client'], sms['message'])
                                masked_number = self.hide_phone(sms['phone'])
                                
                                logger.info(f"🆕 NEW OTP FOUND: {otp}")
                                
                                result = await self.send_otp_to_telegram(
                                    country_flag, country_code, platform_emoji, 
                                    platform_name, masked_number, otp, True
                                )
                                
                                if result:
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    logger.info(f"📊 Total new OTPs sent: {self.total_otps_sent}")
                                
                                await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                await asyncio.sleep(max(0, 0.5 - elapsed))
                
                # Refresh every 2 seconds
                self.refresh_counter += 1
                if self.refresh_counter >= 4:
                    try:
                        self.driver.refresh()
                        logger.debug("🔄 Browser refreshed")
                        await asyncio.sleep(2)
                    except:
                        pass
                    self.refresh_counter = 0
                    
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
        
        print("\n🔧 Setting up browser...")
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        print("\n🔐 Logging in...")
        if not self.auto_login():
            print("❌ Login failed!")
            return
        
        print("\n✅ Login successful!")
        
        print("\n📤 Sending existing OTPs...")
        await self.send_all_existing_otps()
        
        print("\n🚀 Starting OTP monitor...")
        print("📱 Waiting for new OTPs...")
        print("💾 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"📊 Total new OTPs sent: {bot.total_otps_sent}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())