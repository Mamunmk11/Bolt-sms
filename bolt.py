#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Monitor Bot (2 sec refresh)
- Country flags with short codes (100+ countries)
- Full platform names with emojis (💚 WhatsApp, 📘 Facebook, 🍎 Apple, etc.)
- Clickable OTP button (copy_text feature)
- 2 sec browser refresh, 0.5 sec check interval
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
from selenium.common.exceptions import WebDriverException

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

# ========== COUNTRY DATA (100+ countries with flags and short codes) ==========
COUNTRIES = {
    # Africa
    '20': ('🇪🇬', '#EG'), '212': ('🇲🇦', '#MA'), '213': ('🇩🇿', '#DZ'), '216': ('🇹🇳', '#TN'),
    '218': ('🇱🇾', '#LY'), '221': ('🇸🇳', '#SN'), '222': ('🇲🇷', '#MR'), '223': ('🇲🇱', '#ML'),
    '224': ('🇬🇳', '#GN'), '225': ('🇨🇮', '#CI'), '226': ('🇧🇫', '#BF'), '227': ('🇳🇪', '#NE'),
    '228': ('🇹🇬', '#TG'), '229': ('🇧🇯', '#BJ'), '230': ('🇲🇺', '#MU'), '231': ('🇱🇷', '#LR'),
    '232': ('🇸🇱', '#SL'), '233': ('🇬🇭', '#GH'), '234': ('🇳🇬', '#NG'), '235': ('🇹🇩', '#TD'),
    '236': ('🇨🇫', '#CF'), '237': ('🇨🇲', '#CM'), '238': ('🇨🇻', '#CV'), '239': ('🇸🇹', '#ST'),
    '240': ('🇬🇶', '#GQ'), '241': ('🇬🇦', '#GA'), '242': ('🇨🇬', '#CG'), '243': ('🇨🇩', '#CD'),
    '244': ('🇦🇴', '#AO'), '245': ('🇬🇼', '#GW'), '246': ('🇮🇴', '#IO'), '247': ('🇦🇨', '#AC'),
    '248': ('🇸🇨', '#SC'), '249': ('🇸🇩', '#SD'), '250': ('🇷🇼', '#RW'), '251': ('🇪🇹', '#ET'),
    '252': ('🇸🇴', '#SO'), '253': ('🇩🇯', '#DJ'), '254': ('🇰🇪', '#KE'), '255': ('🇹🇿', '#TZ'),
    '256': ('🇺🇬', '#UG'), '257': ('🇧🇮', '#BI'), '258': ('🇲🇿', '#MZ'), '259': ('🇿🇼', '#ZW'),
    '260': ('🇿🇲', '#ZM'), '261': ('🇲🇬', '#MG'), '262': ('🇷🇪', '#RE'), '263': ('🇿🇼', '#ZW'),
    '264': ('🇳🇦', '#NA'), '265': ('🇲🇼', '#MW'), '266': ('🇱🇸', '#LS'), '267': ('🇧🇼', '#BW'),
    '268': ('🇸🇿', '#SZ'), '269': ('🇰🇲', '#KM'), '27': ('🇿🇦', '#ZA'), '290': ('🇸🇭', '#SH'),
    '291': ('🇪🇷', '#ER'), '298': ('🇫🇴', '#FO'), '299': ('🇬🇱', '#GL'),
    
    # Asia
    '81': ('🇯🇵', '#JP'), '82': ('🇰🇷', '#KR'), '84': ('🇻🇳', '#VN'), '850': ('🇰🇵', '#KP'),
    '852': ('🇭🇰', '#HK'), '853': ('🇲🇴', '#MO'), '855': ('🇰🇭', '#KH'), '856': ('🇱🇦', '#LA'),
    '86': ('🇨🇳', '#CN'), '880': ('🇧🇩', '#BD'), '886': ('🇹🇼', '#TW'), '90': ('🇹🇷', '#TR'),
    '91': ('🇮🇳', '#IN'), '92': ('🇵🇰', '#PK'), '93': ('🇦🇫', '#AF'), '94': ('🇱🇰', '#LK'),
    '95': ('🇲🇲', '#MM'), '960': ('🇲🇻', '#MV'), '961': ('🇱🇧', '#LB'), '962': ('🇯🇴', '#JO'),
    '963': ('🇸🇾', '#SY'), '964': ('🇮🇶', '#IQ'), '965': ('🇰🇼', '#KW'), '966': ('🇸🇦', '#SA'),
    '967': ('🇾🇪', '#YE'), '968': ('🇴🇲', '#OM'), '970': ('🇵🇸', '#PS'), '971': ('🇦🇪', '#AE'),
    '972': ('🇮🇱', '#IL'), '973': ('🇧🇭', '#BH'), '974': ('🇶🇦', '#QA'), '975': ('🇧🇹', '#BT'),
    '976': ('🇲🇳', '#MN'), '977': ('🇳🇵', '#NP'), '98': ('🇮🇷', '#IR'), '992': ('🇹🇯', '#TJ'),
    '993': ('🇹🇲', '#TM'), '994': ('🇦🇿', '#AZ'), '995': ('🇬🇪', '#GE'), '996': ('🇰🇬', '#KG'),
    '998': ('🇺🇿', '#UZ'),
    
    # Europe
    '30': ('🇬🇷', '#GR'), '31': ('🇳🇱', '#NL'), '32': ('🇧🇪', '#BE'), '33': ('🇫🇷', '#FR'),
    '34': ('🇪🇸', '#ES'), '350': ('🇬🇮', '#GI'), '351': ('🇵🇹', '#PT'), '352': ('🇱🇺', '#LU'),
    '353': ('🇮🇪', '#IE'), '354': ('🇮🇸', '#IS'), '355': ('🇦🇱', '#AL'), '356': ('🇲🇹', '#MT'),
    '357': ('🇨🇾', '#CY'), '358': ('🇫🇮', '#FI'), '359': ('🇧🇬', '#BG'), '36': ('🇭🇺', '#HU'),
    '370': ('🇱🇹', '#LT'), '371': ('🇱🇻', '#LV'), '372': ('🇪🇪', '#EE'), '373': ('🇲🇩', '#MD'),
    '374': ('🇦🇲', '#AM'), '375': ('🇧🇾', '#BY'), '376': ('🇦🇩', '#AD'), '377': ('🇲🇨', '#MC'),
    '378': ('🇸🇲', '#SM'), '379': ('🇻🇦', '#VA'), '380': ('🇺🇦', '#UA'), '381': ('🇷🇸', '#RS'),
    '382': ('🇲🇪', '#ME'), '383': ('🇽🇰', '#XK'), '385': ('🇭🇷', '#HR'), '386': ('🇸🇮', '#SI'),
    '387': ('🇧🇦', '#BA'), '389': ('🇲🇰', '#MK'), '39': ('🇮🇹', '#IT'), '40': ('🇷🇴', '#RO'),
    '41': ('🇨🇭', '#CH'), '420': ('🇨🇿', '#CZ'), '421': ('🇸🇰', '#SK'), '423': ('🇱🇮', '#LI'),
    '43': ('🇦🇹', '#AT'), '44': ('🇬🇧', '#UK'), '45': ('🇩🇰', '#DK'), '46': ('🇸🇪', '#SE'),
    '47': ('🇳🇴', '#NO'), '48': ('🇵🇱', '#PL'), '49': ('🇩🇪', '#DE'),
    
    # North America
    '1': ('🇺🇸', '#US'), '1242': ('🇧🇸', '#BS'), '1246': ('🇧🇧', '#BB'), '1264': ('🇦🇮', '#AI'),
    '1268': ('🇦🇬', '#AG'), '1284': ('🇻🇬', '#VG'), '1340': ('🇻🇮', '#VI'), '1345': ('🇰🇾', '#KY'),
    '1441': ('🇧🇲', '#BM'), '1473': ('🇬🇩', '#GD'), '1649': ('🇹🇨', '#TC'), '1664': ('🇲🇸', '#MS'),
    '1670': ('🇲🇵', '#MP'), '1671': ('🇬🇺', '#GU'), '1684': ('🇦🇸', '#AS'), '1721': ('🇸🇽', '#SX'),
    '1758': ('🇱🇨', '#LC'), '1767': ('🇩🇲', '#DM'), '1784': ('🇻🇨', '#VC'), '1809': ('🇩🇴', '#DO'),
    '1829': ('🇩🇴', '#DO'), '1849': ('🇩🇴', '#DO'), '1868': ('🇹🇹', '#TT'), '1869': ('🇰🇳', '#KN'),
    '1876': ('🇯🇲', '#JM'), '1939': ('🇵🇷', '#PR'),
    
    # South America
    '500': ('🇫🇰', '#FK'), '501': ('🇧🇿', '#BZ'), '502': ('🇬🇹', '#GT'), '503': ('🇸🇻', '#SV'),
    '504': ('🇭🇳', '#HN'), '505': ('🇳🇮', '#NI'), '506': ('🇨🇷', '#CR'), '507': ('🇵🇦', '#PA'),
    '508': ('🇵🇲', '#PM'), '509': ('🇭🇹', '#HT'), '51': ('🇵🇪', '#PE'), '52': ('🇲🇽', '#MX'),
    '53': ('🇨🇺', '#CU'), '54': ('🇦🇷', '#AR'), '55': ('🇧🇷', '#BR'), '56': ('🇨🇱', '#CL'),
    '57': ('🇨🇴', '#CO'), '58': ('🇻🇪', '#VE'), '591': ('🇧🇴', '#BO'), '592': ('🇬🇾', '#GY'),
    '593': ('🇪🇨', '#EC'), '594': ('🇬🇫', '#GF'), '595': ('🇵🇾', '#PY'), '596': ('🇲🇶', '#MQ'),
    '597': ('🇸🇷', '#SR'), '598': ('🇺🇾', '#UY'), '599': ('🇧🇶', '#BQ'),
    
    # Oceania
    '61': ('🇦🇺', '#AU'), '64': ('🇳🇿', '#NZ'), '674': ('🇳🇷', '#NR'), '675': ('🇵🇬', '#PG'),
    '676': ('🇹🇴', '#TO'), '677': ('🇸🇧', '#SB'), '678': ('🇻🇺', '#VU'), '679': ('🇫🇯', '#FJ'),
    '680': ('🇵🇼', '#PW'), '681': ('🇼🇫', '#WF'), '682': ('🇨🇰', '#CK'), '683': ('🇳🇺', '#NU'),
    '685': ('🇼🇸', '#WS'), '686': ('🇰🇮', '#KI'), '687': ('🇳🇨', '#NC'), '688': ('🇹🇻', '#TV'),
    '689': ('🇵🇫', '#PF'), '690': ('🇹🇰', '#TK'), '691': ('🇫🇲', '#FM'), '692': ('🇲🇭', '#MH'),
}

# ========== PLATFORM EMOJI MAPPING (Full Names) ==========
PLATFORM_NAMES = {
    'whatsapp': ('💚', 'WhatsApp'), 'telegram': ('🪁', 'Telegram'), 'facebook': ('📘', 'Facebook'),
    'fb': ('📘', 'Facebook'), 'instagram': ('📸', 'Instagram'), 'ig': ('📸', 'Instagram'),
    'gmail': ('📧', 'Gmail'), 'google': ('🔍', 'Google'), 'apple': ('🍎', 'Apple'),
    'icloud': ('🍎', 'Apple'), 'binance': ('📊', 'Binance'), 'crypto': ('💰', 'Crypto'),
    'microsoft': ('💻', 'Microsoft'), 'outlook': ('📧', 'Outlook'), 'amazon': ('📦', 'Amazon'),
    'paypal': ('💰', 'PayPal'), 'discord': ('🎮', 'Discord'), 'spotify': ('🎵', 'Spotify'),
    'netflix': ('🎬', 'Netflix'), 'tiktok': ('🎵', 'TikTok'), 'signal': ('🔒', 'Signal'),
    'twitter': ('🐦', 'Twitter'), 'x.com': ('🐦', 'X'), 'linkedin': ('🔗', 'LinkedIn'),
    'snapchat': ('👻', 'Snapchat'), 'reddit': ('🤖', 'Reddit'), 'twitch': ('🎮', 'Twitch'),
    'uber': ('🚗', 'Uber'), 'ola': ('🚗', 'Ola'), 'deliveroo': ('🍔', 'Deliveroo'),
    'zomato': ('🍕', 'Zomato'), 'swiggy': ('🍔', 'Swiggy'), 'mama money': ('💰', 'Mama Money'),
    'msaverify': ('✅', 'msaverify'), 'psa verify': ('✅', 'PSA Verify'),
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
        """Get country flag and short code from phone number"""
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
        """Get platform emoji and full name"""
        combined = f"{client_name} {message}".lower()
        
        for key, (emoji, name) in PLATFORM_NAMES.items():
            if key in combined:
                return emoji, name
        
        if client_name and client_name.strip():
            return "📱", client_name.strip()
        
        return "📱", "Other"
    
    def hide_phone(self, phone):
        """Hide phone number - show only first 4 and last 4 digits"""
        phone_str = re.sub(r'\D', '', str(phone))
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
    def send_otp_to_telegram(self, country_flag, country_code, platform_emoji, platform_name, masked_number, otp):
        """Send OTP to Telegram with click-to-copy feature"""
        try:
            # Format: 🇿🇼 #ZW 💚 WhatsApp 2637****8341
            message = f"{country_flag} {country_code} {platform_emoji} {platform_name} {masked_number}"
            
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": f"{otp}",
                            "copy_text": {"text": otp}
                        }
                    ],
                    [
                        {
                            "text": "🔢 Number Bot",
                            "url": "https://t.me/Updateotpnew_bot"
                        },
                        {
                            "text": "📢 Main Channel",
                            "url": "https://t.me/updaterange"
                        }
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
            else:
                logger.error(f"Failed to send: {response.status_code}")
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
                logger.info("✅ Browser opened on Railway")
            else:
                chromedriver_path = r"C:\Users\mamun\Desktop\chromedriver.exe"
                if not os.path.exists(chromedriver_path):
                    logger.error(f"ChromeDriver not found at: {chromedriver_path}")
                    return False
                chrome_options.add_argument('--start-maximized')
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
            for xpath in ["//div[contains(text(), 'What is')]", "//label[contains(text(), 'What is')]", "//span[contains(text(), '+')]"]:
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
            
            login_clicked = False
            for selector in ["//button[@type='submit']", "//input[@type='submit']"]:
                try:
                    self.driver.find_element(By.XPATH, selector).click()
                    login_clicked = True
                    break
                except:
                    continue
            
            if not login_clicked:
                try:
                    self.driver.find_element(By.TAG_NAME, "form").submit()
                except:
                    logger.error("Could not find login button")
                    return False
            
            time.sleep(8)
            current_url = self.driver.current_url
            
            if 'agent' in current_url or 'Dashboard' in current_url or 'SMS' in current_url:
                logger.info("✅ LOGIN SUCCESSFUL!")
                self.logged_in = True
                self.driver.get(SMS_PAGE_URL)
                time.sleep(8)
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        """Extract OTP code - supports 4-10 digit codes"""
        if not isinstance(message, str):
            return None
        
        patterns = [
            r'#(\d{4,10})',
            r'(?:code|CODE|OTP|otp)[:\s]*(\d{4,10})',
            r'is[:\s]*(\d{4,10})',
            r'verification code[:\s]*(\d{4,10})',
            r'(\d{4,10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                otp = match.group(1)
                if not otp.startswith(('263', '880', '1', '44', '91', '92', '234', '966', '971')):
                    return otp
        
        return None
    
    def get_sms(self):
        """Get SMS messages from the page"""
        try:
            time.sleep(0.5)
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
        """Main monitoring loop - 0.5 sec check, 2 sec refresh"""
        logger.info("🚀 Starting OTP monitor (0.5 sec interval)...")
        logger.info("🔄 Browser will refresh every 2 seconds")
        
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
                                country_flag, country_code = self.get_country_info(sms['phone'])
                                platform_emoji, platform_name = self.get_platform_info(sms['client'], sms['message'])
                                masked_number = self.hide_phone(sms['phone'])
                                
                                logger.info(f"🆕 NEW OTP! {otp} - {platform_name} - {sms['phone']}")
                                
                                result = self.send_otp_to_telegram(
                                    country_flag, country_code, platform_emoji, 
                                    platform_name, masked_number, otp
                                )
                                
                                if result:
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    logger.info(f"📊 Total OTPs sent: {self.total_otps_sent}")
                                
                                await asyncio.sleep(0.5)
                
                # Check interval (0.5 seconds)
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                # Refresh browser every 2 seconds (4 checks = 2 sec)
                self.refresh_counter += 1
                if self.refresh_counter >= 4:  # 4 * 0.5 = 2 seconds
                    self.driver.refresh()
                    logger.debug("🔄 Browser refreshed (2 seconds)")
                    self.refresh_counter = 0
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
        print("🤖 BOLT SMS - COMPLETE OTP MONITOR BOT")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"📱 Telegram Chat: {GROUP_CHAT_ID}")
        print(f"⚡ Check Interval: 0.5 seconds")
        print(f"🔄 Browser Refresh: Every 2 seconds")
        print(f"🌍 Countries: {len(COUNTRIES)}+ with flags & short codes")
        print(f"🎨 Platforms: Full names with emojis")
        print(f"✨ Feature: Click on OTP button to copy")
        if IS_RAILWAY:
            print("🚀 Running on Railway (Headless Mode)")
        else:
            print("💻 Running on Local PC")
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
        
        print("\n" + "="*60)
        print("🚀 Starting OTP Monitor...")
        print("="*60)
        print("📱 Format: 🇿🇼 #ZW 💚 WhatsApp 2637****8341")
        print("🔐 OTP Button: Click to copy the code")
        print("🔄 Browser refresh: 2 seconds")
        print("⚡ Check interval: 0.5 seconds")
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
        print(f"📊 Total OTPs sent: {bot.total_otps_sent}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())