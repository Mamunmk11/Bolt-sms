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
                1: "🇺🇸",   # USA/Canada
                7: "🇷🇺",   # Russia
                20: "🇪🇬",  # Egypt
                27: "🇿🇦",  # South Africa
                30: "🇬🇷",  # Greece
                31: "🇳🇱",  # Netherlands
                32: "🇧🇪",  # Belgium
                33: "🇫🇷",  # France
                34: "🇪🇸",  # Spain
                36: "🇭🇺",  # Hungary
                39: "🇮🇹",  # Italy
                40: "🇷🇴",  # Romania
                41: "🇨🇭",  # Switzerland
                43: "🇦🇹",  # Austria
                44: "🇬🇧",  # UK
                45: "🇩🇰",  # Denmark
                46: "🇸🇪",  # Sweden
                47: "🇳🇴",  # Norway
                48: "🇵🇱",  # Poland
                49: "🇩🇪",  # Germany
                51: "🇵🇪",  # Peru
                52: "🇲🇽",  # Mexico
                53: "🇨🇺",  # Cuba
                54: "🇦🇷",  # Argentina
                55: "🇧🇷",  # Brazil
                56: "🇨🇱",  # Chile
                57: "🇨🇴",  # Colombia
                58: "🇻🇪",  # Venezuela
                60: "🇲🇾",  # Malaysia
                61: "🇦🇺",  # Australia
                62: "🇮🇩",  # Indonesia
                63: "🇵🇭",  # Philippines
                64: "🇳🇿",  # New Zealand
                65: "🇸🇬",  # Singapore
                66: "🇹🇭",  # Thailand
                81: "🇯🇵",  # Japan
                82: "🇰🇷",  # South Korea
                84: "🇻🇳",  # Vietnam
                86: "🇨🇳",  # China
                90: "🇹🇷",  # Turkey
                91: "🇮🇳",  # India
                92: "🇵🇰",  # Pakistan
                93: "🇦🇫",  # Afghanistan
                94: "🇱🇰",  # Sri Lanka
                95: "🇲🇲",  # Myanmar
                98: "🇮🇷",  # Iran
                212: "🇲🇦", # Morocco
                213: "🇩🇿", # Algeria
                216: "🇹🇳", # Tunisia
                218: "🇱🇾", # Libya
                220: "🇬🇲", # Gambia
                221: "🇸🇳", # Senegal
                222: "🇲🇷", # Mauritania
                223: "🇲🇱", # Mali
                224: "🇬🇳", # Guinea
                225: "🇨🇮", # Ivory Coast
                226: "🇧🇫", # Burkina Faso
                227: "🇳🇪", # Niger
                228: "🇹🇬", # Togo
                229: "🇧🇯", # Benin
                230: "🇲🇺", # Mauritius
                231: "🇱🇷", # Liberia
                232: "🇸🇱", # Sierra Leone
                233: "🇬🇭", # Ghana
                234: "🇳🇬", # Nigeria
                235: "🇹🇩", # Chad
                236: "🇨🇫", # Central African Republic
                237: "🇨🇲", # Cameroon
                238: "🇨🇻", # Cape Verde
                239: "🇸🇹", # Sao Tome
                240: "🇬🇶", # Equatorial Guinea
                241: "🇬🇦", # Gabon
                242: "🇨🇬", # Congo
                243: "🇨🇩", # DR Congo
                244: "🇦🇴", # Angola
                245: "🇬🇼", # Guinea-Bissau
                246: "🇮🇴", # Diego Garcia
                247: "🇦🇨", # Ascension Island
                248: "🇸🇨", # Seychelles
                249: "🇸🇩", # Sudan
                250: "🇷🇼", # Rwanda
                251: "🇪🇹", # Ethiopia
                252: "🇸🇴", # Somalia
                253: "🇩🇯", # Djibouti
                254: "🇰🇪", # Kenya
                255: "🇹🇿", # Tanzania
                256: "🇺🇬", # Uganda
                257: "🇧🇮", # Burundi
                258: "🇲🇿", # Mozambique
                260: "🇿🇲", # Zambia
                261: "🇲🇬", # Madagascar
                262: "🇷🇪", # Reunion
                263: "🇿🇼", # Zimbabwe
                264: "🇳🇦", # Namibia
                265: "🇲🇼", # Malawi
                266: "🇱🇸", # Lesotho
                267: "🇧🇼", # Botswana
                268: "🇸🇿", # Eswatini
                269: "🇰🇲", # Comoros
                290: "🇸🇭", # St Helena
                291: "🇪🇷", # Eritrea
                297: "🇦🇼", # Aruba
                298: "🇫🇴", # Faroe Islands
                299: "🇬🇱", # Greenland
                350: "🇬🇮", # Gibraltar
                351: "🇵🇹", # Portugal
                352: "🇱🇺", # Luxembourg
                353: "🇮🇪", # Ireland
                354: "🇮🇸", # Iceland
                355: "🇦🇱", # Albania
                356: "🇲🇹", # Malta
                357: "🇨🇾", # Cyprus
                358: "🇫🇮", # Finland
                359: "🇧🇬", # Bulgaria
                370: "🇱🇹", # Lithuania
                371: "🇱🇻", # Latvia
                372: "🇪🇪", # Estonia
                373: "🇲🇩", # Moldova
                374: "🇦🇲", # Armenia
                375: "🇧🇾", # Belarus
                376: "🇦🇩", # Andorra
                377: "🇲🇨", # Monaco
                378: "🇸🇲", # San Marino
                379: "🇻🇦", # Vatican
                380: "🇺🇦", # Ukraine
                381: "🇷🇸", # Serbia
                382: "🇲🇪", # Montenegro
                383: "🇽🇰", # Kosovo
                385: "🇭🇷", # Croatia
                386: "🇸🇮", # Slovenia
                387: "🇧🇦", # Bosnia
                389: "🇲🇰", # North Macedonia
                420: "🇨🇿", # Czech Republic
                421: "🇸🇰", # Slovakia
                423: "🇱🇮", # Liechtenstein
                500: "🇫🇰", # Falkland Islands
                501: "🇧🇿", # Belize
                502: "🇬🇹", # Guatemala
                503: "🇸🇻", # El Salvador
                504: "🇭🇳", # Honduras
                505: "🇳🇮", # Nicaragua
                506: "🇨🇷", # Costa Rica
                507: "🇵🇦", # Panama
                508: "🇵🇲", # St Pierre
                509: "🇭🇹", # Haiti
                590: "🇬🇵", # Guadeloupe
                591: "🇧🇴", # Bolivia
                592: "🇬🇾", # Guyana
                593: "🇪🇨", # Ecuador
                594: "🇬🇫", # French Guiana
                595: "🇵🇾", # Paraguay
                596: "🇲🇶", # Martinique
                597: "🇸🇷", # Suriname
                598: "🇺🇾", # Uruguay
                599: "🇨🇼", # Curacao
                670: "🇹🇱", # Timor-Leste
                672: "🇦🇶", # Antarctica
                673: "🇧🇳", # Brunei
                674: "🇳🇷", # Nauru
                675: "🇵🇬", # Papua New Guinea
                676: "🇹🇴", # Tonga
                677: "🇸🇧", # Solomon Islands
                678: "🇻🇺", # Vanuatu
                679: "🇫🇯", # Fiji
                680: "🇵🇼", # Palau
                681: "🇼🇫", # Wallis and Futuna
                682: "🇨🇰", # Cook Islands
                683: "🇳🇺", # Niue
                685: "🇼🇸", # Samoa
                686: "🇰🇮", # Kiribati
                687: "🇳🇨", # New Caledonia
                688: "🇹🇻", # Tuvalu
                689: "🇵🇫", # French Polynesia
                690: "🇹🇰", # Tokelau
                691: "🇫🇲", # Micronesia
                692: "🇲🇭", # Marshall Islands
                850: "🇰🇵", # North Korea
                852: "🇭🇰", # Hong Kong
                853: "🇲🇴", # Macau
                855: "🇰🇭", # Cambodia
                856: "🇱🇦", # Laos
                880: "🇧🇩", # Bangladesh
                886: "🇹🇼", # Taiwan
                960: "🇲🇻", # Maldives
                961: "🇱🇧", # Lebanon
                962: "🇯🇴", # Jordan
                963: "🇸🇾", # Syria
                964: "🇮🇶", # Iraq
                965: "🇰🇼", # Kuwait
                966: "🇸🇦", # Saudi Arabia
                967: "🇾🇪", # Yemen
                968: "🇴🇲", # Oman
                970: "🇵🇸", # Palestine
                971: "🇦🇪", # UAE
                972: "🇮🇱", # Israel
                973: "🇧🇭", # Bahrain
                974: "🇶🇦", # Qatar
                975: "🇧🇹", # Bhutan
                976: "🇲🇳", # Mongolia
                977: "🇳🇵", # Nepal
                992: "🇹🇯", # Tajikistan
                993: "🇹🇲", # Turkmenistan
                994: "🇦🇿", # Azerbaijan
                995: "🇬🇪", # Georgia
                996: "🇰🇬", # Kyrgyzstan
                998: "🇺🇿", # Uzbekistan
            }
            
            flag = country_flags.get(country_code, "🌍")
            return flag, f"+{country_code}"
        except:
            return "🌍", ""
    
    def format_phone_display(self, phone_number):
        """Format phone number with country flag in the requested style"""
        flag, country_code = self.get_country_flag_and_code(phone_number)
        # Mask the phone number (show first 4 and last 4 digits)
        phone_str = str(phone_number)
        if len(phone_str) >= 8:
            masked = phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            masked = phone_str[:2] + "***" + phone_str[-2:]
        else:
            masked = phone_str
        
        return f"╭────────────────────╮\n│ {flag} #{country_code} 📱 <code>{masked}</code> │\n╰────────────────────╯"
    
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
            return "Telegram"
        elif 'whatsapp' in message_lower or 'whatsapp' in client_lower:
            return "WhatsApp"
        elif 'instagram' in message_lower:
            return "Instagram"
        elif 'facebook' in message_lower or 'fb' in message_lower:
            return "Facebook"
        elif 'gmail' in message_lower or 'google' in message_lower:
            return "Gmail"
        elif 'twitter' in message_lower or 'x.com' in message_lower:
            return "Twitter/X"
        elif 'apple' in message_lower or 'icloud' in message_lower:
            return "Apple"
        elif 'microsoft' in message_lower or 'outlook' in message_lower:
            return "Microsoft"
        elif 'amazon' in message_lower:
            return "Amazon"
        elif 'paypal' in message_lower:
            return "PayPal"
        elif 'binance' in message_lower or 'crypto' in message_lower:
            return "Binance/Crypto"
        elif 'discord' in message_lower:
            return "Discord"
        elif 'spotify' in message_lower:
            return "Spotify"
        elif 'netflix' in message_lower:
            return "Netflix"
        elif 'tiktok' in message_lower:
            return "TikTok"
        elif 'signal' in message_lower:
            return "Signal"
        else:
            return "Other"
    
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
    
    async def send_telegram(self, msg):
        try:
            keyboard = [[
                InlineKeyboardButton("Main Channel", url="https://t.me/updaterange"),
                InlineKeyboardButton("Number Bot", url="https://t.me/Updateotpnew_bot"),
                InlineKeyboardButton("Developer", url="https://t.me/rana1132")
            ]]
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=msg,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def send_all_today_otps(self):
        logger.info("Sending today's OTPs...")
        
        sms_list = self.get_sms()
        if not sms_list:
            await self.send_telegram("No OTPs found for today")
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                if sms_id not in self.processed_otps:
                    phone_display = self.format_phone_display(sms['phone'])
                    platform = self.extract_platform(sms['message'], sms['client'])
                    
                    msg = f"""
<b>Previous OTP</b>
────────────────────

<b>Time:</b> <code>{sms['time']}</code>
{phone_display}
<b>Platform:</b> {platform}

<b>OTP Code:</b> <code>{otp}</code>

────────────────────
@updaterange
"""
                    if await self.send_telegram(msg):
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                        await asyncio.sleep(1)
        
        logger.info(f"Sent {otp_count} OTPs")
        self._save_processed_otps()
        
        await self.send_telegram(
            f"<b>Startup Complete!</b>\n"
            f"────────────────────\n"
            f"Today's OTPs: {otp_count}\n"
            f"Check Interval: 0.5 seconds\n"
            f"Browser Refresh: Every 1.5 seconds\n"
            f"Status: Monitoring\n"
            f"Started: {datetime.now().strftime('%H:%M:%S')}\n"
            f"────────────────────"
        )
    
    async def monitor(self):
        logger.info("Starting OTP monitor (0.5 sec interval)...")
        logger.info("Browser will refresh every 1.5 seconds")
        
        await self.send_telegram(f"Bot Started!\nUser: {USERNAME}")
        
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
                                phone_display = self.format_phone_display(sms['phone'])
                                
                                logger.info(f"NEW OTP! {sms['time']} - {sms['phone']} - {platform}")
                                
                                msg = f"""
<b>NEW OTP!</b>
────────────────────

<b>Time:</b> <code>{sms['time']}</code>
{phone_display}
<b>Platform:</b> {platform}

<b>OTP Code:</b> <code>{otp}</code>

<b>Message:</b>
<code>{sms['message'][:300]}</code>

────────────────────
@updaterange
"""
                                if await self.send_telegram(msg):
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
        print(f"Telegram: {GROUP_CHAT_ID}")
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
            await self.send_telegram("<b>Login Failed!</b>")
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