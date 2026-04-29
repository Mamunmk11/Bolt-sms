#!/usr/bin/env python3
"""
Bolt SMS - Complete OTP Monitor Bot (Final Version)
Features:
- Auto detects platform from CLI or message (any platform)
- Sends all existing OTPs on startup
- Monitors for new OTPs (0.5 sec check, 2 sec refresh)
- Country flags with short codes
- Clickable OTP button
- Auto-saves new platforms
- Handles alerts automatically
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

# ========== COUNTRY DATA (100+ countries) ==========
COUNTRIES = {
    # Africa
    '20': ('🇪🇬', '#EG'), '212': ('🇲🇦', '#MA'), '213': ('🇩🇿', '#DZ'), '216': ('🇹🇳', '#TN'),
    '218': ('🇱🇾', '#LY'), '221': ('🇸🇳', '#SN'), '222': ('🇲🇷', '#MR'), '223': ('🇲🇱', '#ML'),
    '224': ('🇬🇳', '#GN'), '225': ('🇨🇮', '#CI'), '226': ('🇧🇫', '#BF'), '227': ('🇳🇪', '#NE'),
    '228': ('🇹🇬', '#TG'), '229': ('🇧🇯', '#BJ'), '230': ('🇲🇺', '#MU'), '231': ('🇱🇷', '#LR'),
    '232': ('🇸🇱', '#SL'), '233': ('🇬🇭', '#GH'), '234': ('🇳🇬', '#NG'), '235': ('🇹🇩', '#TD'),
    '236': ('🇨🇫', '#CF'), '237': ('🇨🇲', '#CM'), '238': ('🇨🇻', '#CV'), '239': ('🇸🇹', '#ST'),
    '240': ('🇬🇶', '#GQ'), '241': ('🇬🇦', '#GA'), '242': ('🇨🇬', '#CG'), '243': ('🇨🇩', '#CD'),
    '244': ('🇦🇴', '#AO'), '245': ('🇬🇼', '#GW'), '248': ('🇸🇨', '#SC'), '249': ('🇸🇩', '#SD'),
    '250': ('🇷🇼', '#RW'), '251': ('🇪🇹', '#ET'), '252': ('🇸🇴', '#SO'), '253': ('🇩🇯', '#DJ'),
    '254': ('🇰🇪', '#KE'), '255': ('🇹🇿', '#TZ'), '256': ('🇺🇬', '#UG'), '257': ('🇧🇮', '#BI'),
    '258': ('🇲🇿', '#MZ'), '260': ('🇿🇲', '#ZM'), '261': ('🇲🇬', '#MG'), '262': ('🇷🇪', '#RE'),
    '263': ('🇿🇼', '#ZW'), '264': ('🇳🇦', '#NA'), '265': ('🇲🇼', '#MW'), '266': ('🇱🇸', '#LS'),
    '267': ('🇧🇼', '#BW'), '268': ('🇸🇿', '#SZ'), '269': ('🇰🇲', '#KM'), '27': ('🇿🇦', '#ZA'),
    '290': ('🇸🇭', '#SH'), '291': ('🇪🇷', '#ER'), '298': ('🇫🇴', '#FO'), '299': ('🇬🇱', '#GL'),
    
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
    '504': ('🇭🇴', '#HN'), '505': ('🇳🇮', '#NI'), '506': ('🇨🇷', '#CR'), '507': ('🇵🇦', '#PA'),
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

# ========== BUILT-IN PLATFORM NAMES (With Emojis) ==========
BUILTIN_PLATFORMS = {
    'telegram': ('🪁', 'Telegram'), 'whatsapp': ('💚', 'WhatsApp'),
    'facebook': ('📘', 'Facebook'), 'fb': ('📘', 'Facebook'),
    'instagram': ('📸', 'Instagram'), 'ig': ('📸', 'Instagram'),
    'gmail': ('📧', 'Gmail'), 'google': ('🔍', 'Google'),
    'apple': ('🍎', 'Apple'), 'icloud': ('🍎', 'Apple'),
    'binance': ('📊', 'Binance'), 'crypto': ('💰', 'Crypto'),
    'microsoft': ('💻', 'Microsoft'), 'outlook': ('📧', 'Outlook'),
    'amazon': ('📦', 'Amazon'), 'paypal': ('💰', 'PayPal'),
    'discord': ('🎮', 'Discord'), 'spotify': ('🎵', 'Spotify'),
    'netflix': ('🎬', 'Netflix'), 'tiktok': ('🎵', 'TikTok'),
    'signal': ('🔒', 'Signal'), 'twitter': ('🐦', 'Twitter'),
    'x.com': ('🐦', 'X'), 'linkedin': ('🔗', 'LinkedIn'),
    'snapchat': ('👻', 'Snapchat'), 'reddit': ('🤖', 'Reddit'),
    'twitch': ('🎮', 'Twitch'), 'uber': ('🚗', 'Uber'),
    'ola': ('🚗', 'Ola'), 'deliveroo': ('🍔', 'Deliveroo'),
    'zomato': ('🍕', 'Zomato'), 'swiggy': ('🍔', 'Swiggy'),
    'mama money': ('💰', 'Mama Money'), 'msaverify': ('✅', 'msaverify'),
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
        logger.info(f"📱 Built-in platforms: {len(BUILTIN_PLATFORMS)}")
        logger.info(f"📱 Custom platforms loaded: {len(self.custom_platforms)}")
    
    def _load_custom_platforms(self):
        """Load custom platforms from cache file"""
        try:
            if os.path.exists(PLATFORM_CACHE_FILE):
                with open(PLATFORM_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading custom platforms: {e}")
        return {}
    
    def _save_custom_platform(self, platform_name):
        """Save new platform to cache"""
        try:
            if platform_name and platform_name not in self.custom_platforms:
                self.custom_platforms[platform_name] = True
                with open(PLATFORM_CACHE_FILE, 'w') as f:
                    json.dump(self.custom_platforms, f)
                logger.info(f"📝 New platform saved: {platform_name}")
                return True
        except Exception as e:
            logger.error(f"Error saving custom platform: {e}")
        return False
    
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
    
    def get_platform_info(self, cli, message):
        """Detect platform from CLI column OR message content (Auto-detect any platform)"""
        combined = f"{cli} {message}".lower()
        
        # First check built-in platforms
        for key, (emoji, name) in BUILTIN_PLATFORMS.items():
            if key in combined:
                logger.info(f"✅ Platform detected (built-in): {name}")
                return emoji, name
        
        # Then check custom platforms
        for platform_name in self.custom_platforms.keys():
            if platform_name.lower() in combined:
                logger.info(f"✅ Platform detected (custom): {platform_name}")
                return "📱", platform_name
        
        # Try to detect new platform name
        detected_name = None
        
        # Check CLI column
        if cli and cli.strip() and len(cli.strip()) > 2:
            detected_name = cli.strip()
            logger.info(f"🔍 New platform detected from CLI: {detected_name}")
        
        # If not found in CLI, check message
        if not detected_name and message:
            words = message.split()
            for word in words:
                word_clean = re.sub(r'[^a-zA-Z]', '', word)
                if len(word_clean) > 3 and word_clean.lower() not in ['code', 'your', 'is', 'for', 'verification', 'please', 'account', 'login', 'click', 'link', 'https', 'http']:
                    detected_name = word_clean
                    logger.info(f"🔍 New platform detected from message: {detected_name}")
                    break
        
        # Save detected platform for future
        if detected_name:
            self._save_custom_platform(detected_name)
            return "📱", detected_name
        
        # Fallback
        if cli and cli.strip():
            return "📱", cli.strip()
        
        return "📱", "Other"
    
    def hide_phone(self, phone):
        """Hide phone number - show only first 4 and last 4 digits"""
        phone_str = re.sub(r'\D', '', str(phone))
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
    def handle_alert(self):
        """Handle any alert popups"""
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
    
    async def send_otp_to_telegram(self, country_flag, country_code, platform_emoji, platform_name, masked_phone, otp, is_new=True):
        """Send OTP to Telegram with click-to-copy feature"""
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
                    "disable_web_page_preview": True
                },
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ OTP sent: {otp} | Platform: {platform_name} | Phone: {masked_phone}")
                return True
            else:
                logger.error(f"❌ Failed to send: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def setup_browser(self):
        """Setup Chrome browser"""
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
                    logger.error(f"❌ ChromeDriver not found at: {chromedriver_path}")
                    return False
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Browser opened on Local PC")
            
            return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False
    
    def solve_captcha(self):
        """Solve captcha on login page"""
        try:
            for xpath in ["//div[contains(text(), 'What is')]", "//label[contains(text(), 'What is')]", "//span[contains(text(), '+')]"]:
                try:
                    captcha_text = self.driver.find_element(By.XPATH, xpath).text
                    if captcha_text:
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
        """Automatic login to SMS panel"""
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
            login_clicked = False
            for selector in ["//button[@type='submit']", "//input[@type='submit']"]:
                try:
                    self.driver.find_element(By.XPATH, selector).click()
                    login_clicked = True
                    logger.info("✅ Login button clicked")
                    break
                except:
                    continue
            
            if not login_clicked:
                try:
                    self.driver.find_element(By.TAG_NAME, "form").submit()
                    logger.info("✅ Form submitted")
                except:
                    logger.error("❌ Could not find login button")
                    return False
            
            time.sleep(8)
            current_url = self.driver.current_url
            logger.info(f"📍 URL after login: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url or 'SMS' in current_url:
                logger.info("✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
                self.logged_in = True
                self.driver.get(SMS_PAGE_URL)
                time.sleep(10)
                self.handle_alert()
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed!")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        """Extract OTP code from message - supports 4-10 digit codes"""
        if not isinstance(message, str):
            return None
        
        patterns = [
            r'Telegram code[:\s]*(\d{4,8})',
            r'WhatsApp code[:\s]*(\d{4,8})',
            r'code[:\s]*(\d{4,8})',
            r'OTP[:\s]*(\d{4,8})',
            r'verification code[:\s]*(\d{4,8})',
            r'#(\d{4,8})',
            r'is[:\s]*(\d{4,8})',
            r'\b(\d{5,8})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                otp = match.group(1)
                if len(otp) >= 4 and not otp.startswith(('263', '880', '1', '44', '91', '92', '234', '966', '971')):
                    return otp
        return None
    
    def get_all_sms(self):
        """Get all SMS from the page - Correct column mapping"""
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
                    
                    if len(cols) < 5:
                        continue
                    
                    # Column mapping based on your screenshot:
                    # Col 0: RANGE | Col 1: NUMBER | Col 2: CLI | Col 3: CLIENT | Col 4: SMS
                    phone = cols[1].text.strip() if len(cols) > 1 else ""
                    cli = cols[2].text.strip() if len(cols) > 2 else ""
                    sms_text = cols[4].text.strip() if len(cols) > 4 else ""
                    
                    # If SMS column empty but CLI has content, use CLI as message
                    if not sms_text and cli:
                        sms_text = cli
                        cli = ""
                    
                    if not sms_text:
                        continue
                    
                    # Try to get full message (might be truncated in display)
                    try:
                        sms_element = cols[4]
                        full_message = sms_element.get_attribute('title') or sms_element.get_attribute('data-fulltext') or sms_text
                    except:
                        full_message = sms_text
                    
                    # Extract OTP
                    otp = self.extract_otp(full_message)
                    
                    if otp:
                        # Detect platform from CLI OR message
                        platform_emoji, platform_name = self.get_platform_info(cli, full_message)
                        
                        logger.info(f"📱 Found OTP: {otp} | Phone: {phone} | Platform: {platform_name}")
                        
                        sms_list.append({
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'phone': phone,
                            'client': platform_name,
                            'platform_emoji': platform_emoji,
                            'message': full_message,
                            'otp': otp
                        })
                    else:
                        # Try to find OTP in row text
                        row_text = row.text
                        otp = self.extract_otp(row_text)
                        if otp:
                            platform_emoji, platform_name = self.get_platform_info(cli, row_text)
                            logger.info(f"📱 Found OTP (from row text): {otp} | Phone: {phone}")
                            sms_list.append({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'phone': phone,
                                'client': platform_name,
                                'platform_emoji': platform_emoji,
                                'message': row_text,
                                'otp': otp
                            })
                        
                except Exception as e:
                    logger.debug(f"Row parse error: {e}")
                    continue
            
            logger.info(f"📊 Total OTPs found: {len(sms_list)}")
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
            await self.send_otp_to_telegram("🌍", "#??", "📱", "Info", "No OTPs", "No OTPs found", False)
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = sms.get('otp') or self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['phone']}_{otp}"
                if sms_id not in self.processed_otps:
                    country_flag, country_code = self.get_country_info(sms['phone'])
                    platform_emoji = sms.get('platform_emoji', '📱')
                    platform_name = sms['client']
                    masked_phone = self.hide_phone(sms['phone'])
                    
                    logger.info(f"📜 Sending existing OTP: {otp} | Platform: {platform_name} | Phone: {sms['phone']}")
                    
                    result = await self.send_otp_to_telegram(
                        country_flag, country_code, platform_emoji, 
                        platform_name, masked_phone, otp, False
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
🌍 **Countries:** {len(COUNTRIES)}+ with flags
📱 **Platforms:** Auto-detect (any platform)
🔐 **OTP:** Click to copy
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
        except Exception as e:
            logger.error(f"Startup message error: {e}")
    
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
                                platform_emoji = sms.get('platform_emoji', '📱')
                                platform_name = sms['client']
                                masked_phone = self.hide_phone(sms['phone'])
                                
                                logger.info(f"🆕 NEW OTP FOUND! {otp} | Platform: {platform_name} | Phone: {sms['phone']}")
                                
                                result = await self.send_otp_to_telegram(
                                    country_flag, country_code, platform_emoji, 
                                    platform_name, masked_phone, otp, True
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
        """Main run method"""
        print("\n" + "="*60)
        print("🤖 BOLT SMS - COMPLETE OTP MONITOR BOT")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"📱 Telegram Chat: {GROUP_CHAT_ID}")
        print(f"⚡ Check Interval: 0.5 seconds")
        print(f"🔄 Browser Refresh: Every 2 seconds")
        print(f"🌍 Countries: {len(COUNTRIES)}+ with flags & short codes")
        print(f"📱 Platforms: Auto-detect (any platform)")
        print(f"✨ Feature: Click on OTP button to copy")
        print(f"🚀 Mode: {'Railway' if IS_RAILWAY else 'Local PC'}")
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
        
        print("\n" + "="*60)
        print("🚀 Starting OTP Monitor...")
        print("="*60)
        print("📱 Format: 🇿🇼 #ZW 🪁 Telegram 2637****8274")
        print("🔐 OTP Button: Click to copy the code")
        print("🔄 Browser refresh: 2 seconds")
        print("⚡ Check interval: 0.5 seconds")
        print("📝 New platforms will be auto-saved")
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