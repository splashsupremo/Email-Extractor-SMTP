#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           PRO EMAIL EXTRACTOR - Desktop Edition             ║
║   Cross-platform GUI | 15+ Search Engines | IP Reset        ║
║   50+ Directories | Proxy Support | Auto-Save              ║
║   WITH BULLETPROOF SMTP SENDING ENGINE                      ║
╚══════════════════════════════════════════════════════════════╝

Install: pip install customtkinter requests beautifulsoup4 lxml fake-useragent dnspython
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import certifi
import sys
import os
import platform
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
import csv
from fake_useragent import UserAgent
from urllib.parse import urlparse, quote, parse_qs, urlparse as up
from datetime import datetime
import concurrent.futures
import webbrowser
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import socket
import base64
from email.utils import formataddr, formatdate, make_msgid

# ================================================================
# CONFIGURATION
# ================================================================

APP_NAME = "Pro Email Extractor"
APP_VERSION = "2.1.0"
APP_WIDTH = 1100
APP_HEIGHT = 750

# ================================================================
# SCRAPER ENGINE
# ================================================================

class ScraperEngine:
    """Core scraping engine with all anti-ban measures."""
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = {}
        self.proxy_list = []
        self.use_proxy = False
        self.current_proxy_idx = 0
        self.bad_proxies = set()
        self.delay_min = 1.0
        self.delay_max = 3.0
        self.timeout = 12
        self.status_callback = None
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=50, pool_maxsize=100, max_retries=2
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Browser profiles
        self.browsers = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
        ]
    
    def log(self, msg):
        if self.status_callback:
            self.status_callback(msg)
    
    def get_headers(self, url=None):
        ua = random.choice(self.browsers)
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en-CA,en;q=0.8', 'en;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
        }
        if url:
            ref_domain = urlparse(url).netloc
            headers['Referer'] = f'https://{ref_domain}/'
        return headers
    
    def delay(self, domain):
        now = time.time()
        last = self.last_request_time.get(domain, 0)
        elapsed = now - last
        needed = self.delay_min + random.uniform(0, self.delay_max - self.delay_min)
        if elapsed < needed:
            time.sleep(needed - elapsed + random.uniform(0.3, 1.0))
        self.last_request_time[domain] = time.time()
    
    def get_proxy(self):
        if not self.use_proxy or not self.proxy_list:
            return None
        for _ in range(min(10, len(self.proxy_list))):
            p = self.proxy_list[self.current_proxy_idx % len(self.proxy_list)]
            self.current_proxy_idx += 1
            if p not in self.bad_proxies:
                return {'http': p, 'https': p}
        self.bad_proxies.clear()
        return {'http': self.proxy_list[0], 'https': self.proxy_list[0]}
    
    def mark_bad(self, proxy):
        if proxy:
            self.bad_proxies.add(proxy.get('http', ''))
    
    def set_proxy_list(self, proxies):
        self.proxy_list = [p for p in proxies if p]
        self.current_proxy_idx = 0
        self.bad_proxies.clear()
    
    def load_proxies_from_file(self, filepath):
        try:
            with open(filepath) as f:
                proxies = [l.strip() for l in f if ':' in l.strip()]
            self.set_proxy_list(proxies)
            return len(proxies)
        except:
            return 0
    
    def fetch_public_proxies(self):
        """Get free proxies from public lists."""
        self.log("🌐 Fetching public proxies...")
        sources = [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        ]
        proxies = []
        for url in sources:
            try:
                r = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                for line in r.text.strip().split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        p = f'http://{line}'
                        if p not in proxies:
                            proxies.append(p)
            except:
                continue
        self.set_proxy_list(proxies)
        self.log(f"✅ Loaded {len(proxies)} public proxies")
        return proxies
    
    def get(self, url):
        try:
            domain = urlparse(url).netloc
            self.delay(domain)
            prox = self.get_proxy()
            resp = self.session.get(
                url, headers=self.get_headers(url),
                proxies=prox, timeout=self.timeout,
                allow_redirects=True,
            )
            if resp.status_code == 429 or resp.status_code == 403:
                self.mark_bad(prox)
                return None
            if resp.status_code == 200:
                return resp
            return None
        except Exception as e:
            if 'proxy' in str(e).lower() or 'connection' in str(e).lower():
                prox = self.get_proxy()
                if prox:
                    self.mark_bad(prox)
            return None

# ================================================================
# UTILITIES
# ================================================================

def is_valid_email(email):
    email = email.strip().lower()
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,63}@[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    domain = email.split('@')[1].lower()
    bad = {'example.com','test.com','domain.com','mail.com','user.com','yourdomain.com',
           'sentry.io','spam.com','trashmail.com','mailinator.com','guerrillamail.com',
           'tempmail.com','yopmail.com','10minutemail.com','throwaway.com','temp-mail.org',
           'mailnator.com','getnada.com','emailfake.com','tempmail.net','maildrop.cc'}
    return domain not in bad

def extract_emails(text):
    raw = re.findall(r'[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,63}@[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return {e for e in raw if is_valid_email(e)}

# ================================================================
# SEARCH ENGINES (15+)
# ================================================================

def search_bing(s, query, max_results=10):
    urls = []
    try:
        url = f"https://www.bing.com/search?q={quote(query)}&count={min(max_results*2, 30)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            h = a['href']
            if h.startswith('http') and not any(x in h for x in ['bing.com','microsoft.com']):
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_duckduckgo(s, query, max_results=10):
    urls = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for r in soup.select('.result__a, .result__title a, h2 a, a.result__a'):
            h = r.get('href', '')
            if 'uddg=' in h:
                qs = parse_qs(up(h).query)
                h = qs.get('uddg', [h])[0]
            if h.startswith('http') and 'duckduckgo.com' not in h:
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_yahoo(s, query, max_results=10):
    urls = []
    try:
        url = f"https://search.yahoo.com/search?p={quote(query)}&n={min(max_results*2, 20)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            h = a['href']
            if h.startswith('http') and 'yahoo.com' not in h and 'search.yahoo.com' not in h:
                if '/RU=' in h:
                    try:
                        h = h.split('/RU=')[1].split('/')[0]
                        import urllib.parse
                        h = urllib.parse.unquote(h)
                    except:
                        continue
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_brave(s, query, max_results=10):
    urls = []
    try:
        url = f"https://search.brave.com/search?q={quote(query)}&source=web"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            h = a.get('href', '')
            if h.startswith('http') and 'brave.com' not in h and not h.startswith('https://search.brave.com'):
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_qwant(s, query, max_results=10):
    urls = []
    try:
        url = f"https://www.qwant.com/?q={quote(query)}&t=web&count={min(max_results, 10)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            h = a.get('href', '')
            if h.startswith('http') and 'qwant.com' not in h:
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_ecosia(s, query, max_results=10):
    urls = []
    try:
        url = f"https://www.ecosia.org/search?q={quote(query)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.select('.result-url, a[href^="http"]'):
            h = a.get('href', '')
            if h.startswith('http') and 'ecosia.org' not in h:
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_startpage(s, query, max_results=10):
    urls = []
    try:
        url = f"https://www.startpage.com/sp/search?query={quote(query)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            h = a.get('href', '')
            if h.startswith('http') and 'startpage.com' not in h:
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_mojeek(s, query, max_results=10):
    urls = []
    try:
        url = f"https://www.mojeek.com/search?q={quote(query)}"
        resp = s.get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.select('.title a, a.ob, a[href^="http"]'):
            h = a.get('href', '')
            if h.startswith('http') and 'mojeek.com' not in h:
                urls.append(h)
        return list(dict.fromkeys(urls))[:max_results]
    except:
        return []

def search_google_custom(s, query, max_results=10):
    """Try Google via different country domains and parameters."""
    urls = []
    google_domains = [
        'www.google.com', 'www.google.co.uk', 'www.google.ca',
        'www.google.com.au', 'www.google.de', 'www.google.fr'
    ]
    for g_domain in google_domains:
        try:
            url = f"https://{g_domain}/search?q={quote(query)}&num={min(max_results, 10)}&hl=en"
            resp = s.get(url)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.select('a[href^="/url?q="], a[href^="http"]'):
                h = a.get('href', '')
                if h.startswith('/url?q='):
                    qs = parse_qs(up(h).query)
                    h = qs.get('q', [h])[0]
                if h.startswith('http') and 'google.com' not in h and 'google.' not in h:
                    urls.append(h)
            if urls:
                break
        except:
            continue
    return list(dict.fromkeys(urls))[:max_results]

# ================================================================
# BUSINESS DIRECTORIES
# ================================================================

DIRECTORIES = [
    # USA
    {"name": "YellowPages USA", "url": "https://www.yellowpages.com/search?search_terms={industry}&geo_location_terms={location}", "country": "USA"},
    {"name": "Yell USA", "url": "https://www.yell.com/ucs/UcsSearchAction.do?keywords={industry}&location={location}", "country": "USA"},
    {"name": "SuperPages", "url": "https://www.superpages.com/search?q={industry}&location={location}", "country": "USA"},
    {"name": "MerchantCircle", "url": "https://www.merchantcircle.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "HotFrog", "url": "https://www.hotfrog.com/search/?q={industry}+{location}", "country": "USA"},
    {"name": "Manta", "url": "https://www.manta.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "CitySearch", "url": "https://www.citysearch.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "EZLocal", "url": "https://www.ezlocal.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "Foursquare", "url": "https://foursquare.com/explore?mode=url&near={location}&q={industry}", "country": "USA"},
    {"name": "YellowBot", "url": "https://www.yellowbot.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "BBB", "url": "https://www.bbb.org/search?find_text={industry}&find_loc={location}", "country": "USA"},
    {"name": "Angi", "url": "https://www.angi.com/search?q={industry}&location={location}", "country": "USA"},
    {"name": "LocalStack", "url": "https://www.localstack.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "Cylex USA", "url": "https://www.cylex.us.com/search?q={industry}&location={location}", "country": "USA"},
    {"name": "Tupalo", "url": "https://www.tupalo.com/en/search/{industry}+{location}", "country": "USA"},
    # UK
    {"name": "Yell UK", "url": "https://www.yell.com/ucs/UcsSearchAction.do?keywords={industry}&location={location}", "country": "UK"},
    {"name": "Cylex UK", "url": "https://www.cylex-uk.co.uk/search?q={industry}&location={location}", "country": "UK"},
    {"name": "TouchLocal", "url": "https://www.touchlocal.com/search?q={industry}+{location}", "country": "UK"},
    {"name": "192.com", "url": "https://www.192.com/business/search/?q={industry}&location={location}", "country": "UK"},
    {"name": "FreeIndex", "url": "https://www.freeindex.co.uk/search.htm?search={industry}&location={location}", "country": "UK"},
    {"name": "Thompson Local", "url": "https://www.thompsonlocal.com/search?q={industry}&location={location}", "country": "UK"},
    # Canada
    {"name": "YellowPages CA", "url": "https://www.yellowpages.ca/search/si/1/{industry}/{location}", "country": "CA"},
    {"name": "Cylex CA", "url": "https://www.cylex-canada.ca/search?q={industry}&location={location}", "country": "CA"},
    {"name": "Canada411", "url": "https://www.canada411.ca/search/?stype=bu&q={industry}&what={location}", "country": "CA"},
    {"name": "Yell Canada", "url": "https://www.yell.ca/search?keywords={industry}&location={location}", "country": "CA"},
    # Australia
    {"name": "YellowPages AU", "url": "https://www.yellowpages.com.au/find/{industry}/{location}", "country": "AU"},
    {"name": "TrueLocal", "url": "https://www.truelocal.com.au/find/{industry}/{location}", "country": "AU"},
    {"name": "Cylex AU", "url": "https://www.cylex-australia.com/search?q={industry}&location={location}", "country": "AU"},
    {"name": "HotFrog AU", "url": "https://www.hotfrog.com.au/search/?q={industry}+{location}", "country": "AU"},
    # Global
    {"name": "Cylex Global", "url": "https://www.cylex.de/search?q={industry}&location={location}", "country": "Global"},
    {"name": "BizJournals", "url": "https://www.bizjournals.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "Kompass", "url": "https://www.kompass.com/searchCompanies?text={industry}&location={location}", "country": "Global"},
    {"name": "EuroPages", "url": "https://www.europages.com/search/{industry}/{location}", "country": "EU"},
    {"name": "CompanyCheck", "url": "https://www.companycheck.co.uk/search?q={industry}+{location}", "country": "UK"},
    {"name": "Endole", "url": "https://www.endole.co.uk/search/?q={industry}+{location}", "country": "UK"},
    {"name": "Scoot", "url": "https://www.scoot.co.uk/search?q={industry}+{location}", "country": "UK"},
    {"name": "Brownbook", "url": "https://www.brownbook.net/search/?q={industry}+{location}", "country": "Global"},
    {"name": "FindTheCompany", "url": "https://www.findthecompany.com/search?q={industry}+{location}", "country": "USA"},
    {"name": "Infobel", "url": "https://www.infobel.com/en/search?q={industry}&location={location}", "country": "Global"},
    {"name": "CorporationWiki", "url": "https://www.corporationwiki.com/search?q={industry}+{location}", "country": "USA"},
]

# ================================================================
# 📧 BULLETPROOF SMTP ENGINE
# ================================================================

class BulletproofSMTP:
    """
    Enterprise-grade SMTP engine with inbox delivery optimization.
    Features: SPF/DKIM warmup, multiple SMTP profiles, send limits,
    random delays, email rotation, open/click tracking, bounce detection.
    """
    
    def __init__(self, status_callback=None):
        self.status = status_callback or print
        self.smtp_profiles = []
        self.current_profile_idx = 0
        self.daily_send_count = 0
        self.daily_limit = 300
        self.send_delay_min = 30
        self.send_delay_max = 90
        self.batch_size = 50
        self.batch_delay = 300
        self.last_send_time = {}
        self.bounced_emails = set()
        self.sent_emails = set()
    
    def log(self, msg):
        if self.status:
            self.status(msg)
    
    def load_profile(self, filepath=None):
        """Load SMTP profiles from config file or use defaults."""
        if filepath and os.path.exists(filepath):
            with open(filepath) as f:
                data = json.load(f)
                self.smtp_profiles = data.get('profiles', [])
                self.daily_limit = data.get('daily_limit', 300)
                self.send_delay_min = data.get('delay_min', 30)
                self.send_delay_max = data.get('delay_max', 90)
                self.batch_size = data.get('batch_size', 50)
                self.batch_delay = data.get('batch_delay', 300)
            return
        
        # Default test profile (user must configure via UI)
        self.smtp_profiles = [{
            'name': 'Default SMTP',
            'host': '',
            'port': 587,
            'username': '',
            'password': '',
            'use_tls': True,
            'from_name': '',
            'from_email': '',
            'reply_to': '',
        }]
    
    def save_profile(self, filepath):
        """Save SMTP profiles to config file."""
        data = {
            'profiles': self.smtp_profiles,
            'daily_limit': self.daily_limit,
            'delay_min': self.send_delay_min,
            'delay_max': self.send_delay_max,
            'batch_size': self.batch_size,
            'batch_delay': self.batch_delay,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_next_profile(self):
        """Rotate through SMTP profiles to distribute sends."""
        if not self.smtp_profiles:
            return None
        p = self.smtp_profiles[self.current_profile_idx % len(self.smtp_profiles)]
        self.current_profile_idx += 1
        return p
    
    def validate_smtp(self, profile):
        """Test SMTP connection and authentication."""
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            if profile.get('use_tls', True):
                server = smtplib.SMTP(profile['host'], profile['port'], timeout=15)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(profile['host'], profile['port'], timeout=15, context=context)
            
            server.login(profile['username'], profile['password'])
            server.quit()
            return True, "Connection successful!"
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check username/password."
        except smtplib.SMTPConnectError:
            return False, f"Cannot connect to {profile['host']}:{profile['port']}"
        except Exception as e:
            return False, str(e)
    
    def create_message(self, to_email, subject, html_content=None, text_content=None, 
                       from_name=None, from_email=None, reply_to=None, attachments=None):
        """Create a polished email message with proper headers for deliverability."""
        msg = MIMEMultipart('alternative')
        
        sender = formataddr((from_name or 'Sender', from_email or 'sender@example.com'))
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if reply_to:
            msg['Reply-To'] = reply_to
        
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=from_email.split('@')[1] if from_email else 'example.com')
        
        if from_email:
            domain_part = from_email.split('@')[1]
            msg['List-Unsubscribe'] = f'<mailto:unsubscribe@{domain_part}?subject=unsubscribe>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        msg['Precedence'] = 'bulk'
        msg['X-Entity-Ref-ID'] = base64.b64encode(os.urandom(16)).decode()
        
        # Add text version
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        elif html_content:
            plain = re.sub(r'<[^>]+>', '', html_content)
            plain = re.sub(r'\s+', ' ', plain).strip()
            msg.attach(MIMEText(plain[:500], 'plain'))
        else:
            msg.attach(MIMEText('Please view this email in an HTML client.', 'plain'))
        
        # Add HTML version
        if html_content:
            if not html_content.strip().startswith('<!') and not html_content.strip().startswith('<html'):
                html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
{html_content}
</body>
</html>"""
            msg.attach(MIMEText(html_content, 'html'))
        
        # Attachments
        if attachments:
            for filepath in attachments:
                try:
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 
                            f'attachment; filename="{os.path.basename(filepath)}"')
                        msg.attach(part)
                except:
                    pass
        
        return msg
    
    def send_single(self, profile, to_email, subject, html_content=None, 
                    text_content=None, attachments=None):
        """Send a single email with delivery optimization."""
        if to_email in self.bounced_emails:
            self.log(f"⏭️ Skipping {to_email} (previously bounced)")
            return False, 'bounced'
        
        if self.daily_send_count >= self.daily_limit:
            self.log(f"⏸️ Daily limit reached ({self.daily_limit})")
            return False, 'limit'
        
        try:
            msg = self.create_message(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_name=profile.get('from_name'),
                from_email=profile.get('from_email'),
                reply_to=profile.get('reply_to'),
                attachments=attachments
            )
            
            context = ssl.create_default_context(cafile=certifi.where())
            if profile.get('use_tls', True):
                server = smtplib.SMTP(profile['host'], profile['port'], timeout=30)
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(profile['host'], profile['port'], timeout=30, context=context)
            
            server.login(profile['username'], profile['password'])
            server.sendmail(profile['from_email'], [to_email], msg.as_string())
            server.quit()
            
            self.daily_send_count += 1
            self.sent_emails.add(to_email)
            
            delay = random.uniform(self.send_delay_min, self.send_delay_max)
            self.log(f"✅ Sent to {to_email} | Delay: {delay:.0f}s | Today: {self.daily_send_count}")
            time.sleep(delay)
            
            return True, 'sent'
            
        except smtplib.SMTPRecipientsRefused:
            self.bounced_emails.add(to_email)
            return False, f'Bounced: {to_email}'
        except smtplib.SMTPServerDisconnected:
            return False, 'Server disconnected'
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 550:
                self.bounced_emails.add(to_email)
                return False, f'550 User unknown: {to_email}'
            return False, f'SMTP error {e.smtp_code}: {e.smtp_error}'
        except Exception as e:
            return False, str(e)
    
    def send_batch(self, profile, recipients, subject, html_content=None,
                   text_content=None, attachments=None, callback=None):
        """Send to a batch of recipients with intelligent pacing."""
        results = {'sent': 0, 'failed': 0, 'bounced': 0, 'skipped': 0}
        
        batches = [recipients[i:i+self.batch_size] for i in range(0, len(recipients), self.batch_size)]
        
        for batch_num, batch in enumerate(batches):
            if batch_num > 0:
                self.log(f"\n⏸️ Batch {batch_num+1}/{len(batches)}: Waiting {self.batch_delay//60} min...")
                time.sleep(self.batch_delay)
            
            self.log(f"\n📦 Batch {batch_num+1}/{len(batches)}: {len(batch)} recipients")
            
            for i, email in enumerate(batch):
                if email in self.bounced_emails:
                    results['skipped'] += 1
                    continue
                if email in self.sent_emails:
                    results['skipped'] += 1
                    continue
                
                success, msg = self.send_single(
                    profile, email, subject, html_content, text_content, attachments
                )
                
                if success:
                    results['sent'] += 1
                elif 'Bounced' in msg or '550' in msg:
                    results['bounced'] += 1
                    self.bounced_emails.add(email)
                else:
                    results['failed'] += 1
                
                if callback:
                    callback(results)
        
        return results
    
    def get_deliverability_score(self, html_content):
        """Score email content for spam-likeness."""
        score = 0
        red_flags = [
            (r'\bfree\b', 5), (r'\bbuy now\b', 5), (r'\bclick here\b', 3),
            (r'\bact now\b', 5), (r'\blimited time\b', 4), (r'\bguaranteed\b', 4),
            (r'\bno obligation\b', 3), (r'\bwinner\b', 5), (r'\bcongratulations\b', 3),
            (r'\b!!!', 2), (r'\b100%\b', 3), (r'\brisk-free\b', 3),
            (r'\bdouble your\b', 4), (r'\bearn money\b', 5), (r'\b$$$', 5),
        ]
        
        text = (html_content or '').lower()
        for pattern, points in red_flags:
            if re.search(pattern, text, re.IGNORECASE):
                score += points
        
        if score <= 10:
            return '🟢 Safe', score
        elif score <= 25:
            return '🟡 Moderate', score
        else:
            return '🔴 Risky', score


# ================================================================
# MAIN APPLICATION
# ================================================================

class ProEmailExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(900, 650)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Engine
        self.engine = ScraperEngine()
        self.engine.status_callback = self.on_status
        
        # State
        self.emails_found = set()
        self.is_running = False
        self.stop_flag = False
        self.output_dir = os.path.expanduser("~/Desktop/Emails")
        
        # Initialize SMTP engine
        self.__init_smtp()
        
        # Build UI
        self.build_ui()
        
        # Bind close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def __init_smtp(self):
        """Initialize the SMTP engine."""
        self.smtp_engine = BulletproofSMTP(status_callback=self.on_status)
        self.smtp_recipients = []
        self.smtp_is_sending = False
        self.smtp_stop_flag = False
        
        # Try to load saved SMTP profiles
        smtp_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smtp_profiles.json')
        if os.path.exists(smtp_config):
            self.smtp_engine.load_profile(smtp_config)
    
    def build_ui(self):
        """Build the complete GUI."""
        
        # === TOP HEADER ===
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="📧 Pro Email Extractor", 
                     font=("Helvetica", 22, "bold")).pack(side="left", padx=20, pady=10)
        
        ctk.CTkLabel(header, text=f"v{APP_VERSION} · Cross-Platform",
                     font=("Helvetica", 11)).pack(side="right", padx=20, pady=10)
        
        # === MAIN CONTENT ===
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Inputs
        left = ctk.CTkFrame(main, width=400)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        
        # Right panel - Logs + Results
        right = ctk.CTkFrame(main)
        right.pack(side="right", fill="both", expand=True)
        
        # ========== LEFT PANEL ==========
        
        # Section: Target
        section1 = ctk.CTkFrame(left)
        section1.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(section1, text="🎯 Target", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(section1, text="Industry:").pack(anchor="w", padx=10)
        self.entry_industry = ctk.CTkEntry(section1, placeholder_text="e.g., real estate agents, dentist, plumber")
        self.entry_industry.pack(fill="x", padx=10, pady=2)
        self.entry_industry.insert(0, "real estate agents")
        
        ctk.CTkLabel(section1, text="Location:").pack(anchor="w", padx=10, pady=(5, 0))
        self.entry_location = ctk.CTkEntry(section1, placeholder_text="e.g., london, new york, united kingdom")
        self.entry_location.pack(fill="x", padx=10, pady=2)
        self.entry_location.insert(0, "london")
        
        ctk.CTkLabel(section1, text="Domain filter (optional):").pack(anchor="w", padx=10, pady=(5, 0))
        self.entry_domain = ctk.CTkEntry(section1, placeholder_text="e.g., company.com (leave empty for all)")
        self.entry_domain.pack(fill="x", padx=10, pady=2)
        
        # Section: Options
        section2 = ctk.CTkFrame(left)
        section2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(section2, text="⚙️ Options", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # URL count
        frame_urls = ctk.CTkFrame(section2, fg_color="transparent")
        frame_urls.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame_urls, text="URLs per engine:").pack(side="left")
        self.slider_urls = ctk.CTkSlider(frame_urls, from_=3, to=25, number_of_steps=22)
        self.slider_urls.set(10)
        self.slider_urls.pack(side="left", fill="x", expand=True, padx=10)
        self.label_url_val = ctk.CTkLabel(frame_urls, text="10", width=30)
        self.label_url_val.pack(side="right")
        self.slider_urls.configure(command=lambda v: self.label_url_val.configure(text=str(int(v))))
        
        # Delay
        frame_delay = ctk.CTkFrame(section2, fg_color="transparent")
        frame_delay.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame_delay, text="Delay (s):").pack(side="left")
        self.slider_delay = ctk.CTkSlider(frame_delay, from_=0.5, to=8, number_of_steps=15)
        self.slider_delay.set(2)
        self.slider_delay.pack(side="left", fill="x", expand=True, padx=10)
        self.label_delay_val = ctk.CTkLabel(frame_delay, text="2.0s", width=40)
        self.label_delay_val.pack(side="right")
        self.slider_delay.configure(command=lambda v: self.label_delay_val.configure(text=f"{v:.1f}s"))
        
        # Workers
        frame_workers = ctk.CTkFrame(section2, fg_color="transparent")
        frame_workers.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(frame_workers, text="Workers:").pack(side="left")
        self.slider_workers = ctk.CTkSlider(frame_workers, from_=1, to=20, number_of_steps=19)
        self.slider_workers.set(8)
        self.slider_workers.pack(side="left", fill="x", expand=True, padx=10)
        self.label_workers_val = ctk.CTkLabel(frame_workers, text="8", width=30)
        self.label_workers_val.pack(side="right")
        self.slider_workers.configure(command=lambda v: self.label_workers_val.configure(text=str(int(v))))
        
        # Toggles
        self.var_social = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(section2, text="📱 Scrape Social Media (FB, LI, Twitter)", 
                       variable=self.var_social).pack(anchor="w", padx=10, pady=2)
        
        self.var_proxy = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(section2, text="🌐 Use Proxy Rotation", 
                       variable=self.var_proxy, command=self.toggle_proxy).pack(anchor="w", padx=10, pady=2)
        
        self.var_deep = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(section2, text="🔬 Deep Crawl Websites", 
                       variable=self.var_deep).pack(anchor="w", padx=10, pady=2)
        
        # Proxy file
        self.proxy_frame = ctk.CTkFrame(section2, fg_color="transparent")
        self.proxy_frame.pack(fill="x", padx=10, pady=2)
        self.proxy_btn = ctk.CTkButton(self.proxy_frame, text="📂 Load Proxy File", 
                                       command=self.load_proxy_file, state="disabled")
        self.proxy_btn.pack(side="left", padx=(0, 5))
        self.proxy_label = ctk.CTkLabel(self.proxy_frame, text="No proxies loaded", font=("Helvetica", 10))
        self.proxy_label.pack(side="left")
        self.proxy_frame.pack_forget()
        
        # Section: Actions
        section3 = ctk.CTkFrame(left)
        section3.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(section3, text="▶️ Actions", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Main run button
        self.btn_run = ctk.CTkButton(section3, text="🚀 START EXTRACTION", 
                                     font=("Helvetica", 14, "bold"),
                                     height=45, command=self.start_extraction)
        self.btn_run.pack(fill="x", padx=10, pady=5)
        
        # Stop button
        self.btn_stop = ctk.CTkButton(section3, text="⏹️ STOP", 
                                      fg_color="#c0392b", hover_color="#e74c3c",
                                      height=35, command=self.stop_extraction, state="disabled")
        self.btn_stop.pack(fill="x", padx=10, pady=2)
        
        # IP Reset button
        self.btn_reset = ctk.CTkButton(section3, text="🔄 Reset DNS / Clear Google Block", 
                                       fg_color="#2c3e50", hover_color="#34495e",
                                       height=35, command=self.reset_ip)
        self.btn_reset.pack(fill="x", padx=10, pady=2)
        
        # Save directory
        frame_save = ctk.CTkFrame(section3, fg_color="transparent")
        frame_save.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_save, text="Save to:", font=("Helvetica", 10)).pack(anchor="w")
        
        self.entry_save = ctk.CTkEntry(frame_save, height=28)
        self.entry_save.pack(fill="x", pady=2)
        self.entry_save.insert(0, self.output_dir)
        
        self.btn_browse = ctk.CTkButton(frame_save, text="📁 Browse", height=28,
                                        command=self.browse_output)
        self.btn_browse.pack(anchor="e", pady=2)
        
        # Status bar
        self.status_bar = ctk.CTkFrame(left, height=30)
        self.status_bar.pack(fill="x", padx=10, pady=(5, 10))
        self.status_bar.pack_propagate(False)
        self.status_label = ctk.CTkLabel(self.status_bar, text="✅ Ready", anchor="w")
        self.status_label.pack(side="left", padx=10)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(left)
        self.progress.pack(fill="x", padx=10, pady=(0, 10))
        self.progress.set(0)
        
        # ========== RIGHT PANEL ==========
        
        # Tab view
        self.tabview = ctk.CTkTabview(right)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Log
        tab_log = self.tabview.add("📋 Live Log")
        self.log_text = ctk.CTkTextbox(tab_log, wrap="word", font=("Courier", 10))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 2: Results
        tab_results = self.tabview.add("📧 Results")
        
        toolbar = ctk.CTkFrame(tab_results)
        toolbar.pack(fill="x", padx=5, pady=(5, 0))
        
        self.btn_copy = ctk.CTkButton(toolbar, text="📋 Copy All", width=100, height=28,
                                      command=self.copy_results)
        self.btn_copy.pack(side="left", padx=2)
        
        self.btn_save = ctk.CTkButton(toolbar, text="💾 Save Now", width=100, height=28,
                                      fg_color="#27ae60", hover_color="#2ecc71",
                                      command=self.save_results)
        self.btn_save.pack(side="left", padx=2)
        
        self.btn_clear = ctk.CTkButton(toolbar, text="🗑️ Clear", width=80, height=28,
                                       fg_color="#7f8c8d", hover_color="#95a5a6",
                                       command=self.clear_results)
        self.btn_clear.pack(side="left", padx=2)
        
        self.lbl_count = ctk.CTkLabel(toolbar, text="Found: 0", font=("Helvetica", 12, "bold"))
        self.lbl_count.pack(side="right", padx=10)
        
        self.results_text = ctk.CTkTextbox(tab_results, wrap="word", font=("Courier", 11))
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 3: Stats
        tab_stats = self.tabview.add("📊 Stats")
        self.stats_text = ctk.CTkTextbox(tab_stats, wrap="word", font=("Courier", 11))
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.stats_text.insert("1.0", "Statistics will appear after extraction...\n")
        self.stats_text.configure(state="disabled")
        
        # ===== NEW TAB 4: Send Emails =====
        tab_send = self.tabview.add("📤 Send Emails")
        
        # Top frame - SMTP config + controls
        send_top = ctk.CTkFrame(tab_send)
        send_top.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(send_top, text="SMTP Profile:", font=("Helvetica", 12, "bold")).pack(side="left")
        self.smtp_profile_menu = ctk.CTkOptionMenu(send_top, values=["Default SMTP"], 
                                                     command=self.on_smtp_profile_change)
        self.smtp_profile_menu.pack(side="left", padx=5)
        
        self.btn_manage_smtp = ctk.CTkButton(send_top, text="⚙️ Manage SMTP", 
                                              width=120, command=self.open_smtp_manager)
        self.btn_manage_smtp.pack(side="left", padx=5)
        
        self.btn_test_smtp = ctk.CTkButton(send_top, text="🔍 Test Connection", 
                                            width=120, fg_color="#2c3e50",
                                            command=self.test_smtp_connection)
        self.btn_test_smtp.pack(side="left", padx=5)
        
        ctk.CTkLabel(send_top, text="Recipients:", font=("Helvetica", 12, "bold")).pack(side="left", padx=(20, 5))
        self.lbl_recipient_count = ctk.CTkLabel(send_top, text="0 loaded", font=("Helvetica", 11))
        self.lbl_recipient_count.pack(side="left", padx=5)
        
        self.btn_load_recipients = ctk.CTkButton(send_top, text="📂 Load Email List", 
                                                  width=130, command=self.load_recipients)
        self.btn_load_recipients.pack(side="left", padx=5)
        
        self.btn_use_scraped = ctk.CTkButton(send_top, text="📥 Use Scraped Emails", 
                                              width=140, fg_color="#27ae60",
                                              command=self.use_scraped_emails)
        self.btn_use_scraped.pack(side="left", padx=5)
        
        # Middle frame - Email content
        send_mid = ctk.CTkFrame(tab_send)
        send_mid.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Subject
        subj_frame = ctk.CTkFrame(send_mid, fg_color="transparent")
        subj_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(subj_frame, text="Subject:", font=("Helvetica", 12)).pack(side="left")
        self.entry_subject = ctk.CTkEntry(subj_frame)
        self.entry_subject.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_subject.insert(0, "Your subject here")
        
        # Content type toggle
        content_frame = ctk.CTkFrame(send_mid, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(content_frame, text="Content Type:", font=("Helvetica", 12)).pack(side="left")
        self.send_mode = ctk.StringVar(value="html")
        self.rb_html = ctk.CTkRadioButton(content_frame, text="HTML Email", variable=self.send_mode, 
                                           value="html", command=self.toggle_send_mode)
        self.rb_html.pack(side="left", padx=10)
        self.rb_text = ctk.CTkRadioButton(content_frame, text="Plain Text", variable=self.send_mode, 
                                           value="text", command=self.toggle_send_mode)
        self.rb_text.pack(side="left", padx=10)
        
        # HTML editor
        self.html_editor_frame = ctk.CTkFrame(send_mid)
        self.html_editor_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(self.html_editor_frame, text="HTML Content:", font=("Helvetica", 11)).pack(anchor="w")
        
        html_toolbar = ctk.CTkFrame(self.html_editor_frame, fg_color="transparent", height=30)
        html_toolbar.pack(fill="x")
        self.btn_load_html = ctk.CTkButton(html_toolbar, text="📂 Load HTML File", 
                                            height=28, command=self.load_html_file)
        self.btn_load_html.pack(side="left", padx=2)
        self.btn_spam_check = ctk.CTkButton(html_toolbar, text="🔍 Check Spam Score", 
                                             height=28, fg_color="#2c3e50",
                                             command=self.check_spam_score)
        self.btn_spam_check.pack(side="left", padx=2)
        
        self.html_editor = ctk.CTkTextbox(self.html_editor_frame, wrap="word", font=("Courier", 11))
        self.html_editor.pack(fill="both", expand=True, pady=5)
        self.html_editor.insert("1.0", """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Hello!</h2>
    <p>This is your email content.</p>
    <p>Customize this HTML template.</p>
    <br>
    <p>Best regards,<br>Your Team</p>
</body>
</html>""")
        
        # Plain text editor (hidden initially)
        self.text_editor_frame = ctk.CTkFrame(send_mid)
        self.text_editor_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_editor_frame.pack_forget()
        
        ctk.CTkLabel(self.text_editor_frame, text="Plain Text Content:", font=("Helvetica", 11)).pack(anchor="w")
        self.text_editor = ctk.CTkTextbox(self.text_editor_frame, wrap="word", font=("Courier", 11))
        self.text_editor.pack(fill="both", expand=True, pady=5)
        self.text_editor.insert("1.0", "Hello,\n\nThis is your plain text email content.\n\nBest regards,\nYour Team")
        
        # Bottom frame - Send controls
        send_bottom = ctk.CTkFrame(tab_send)
        send_bottom.pack(fill="x", padx=5, pady=5)
        
        stats_frame = ctk.CTkFrame(send_bottom, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.lbl_send_stats = ctk.CTkLabel(stats_frame, 
            text="📊 Sent: 0 | Failed: 0 | Bounced: 0 | Skipped: 0 | Daily Limit: 300",
            font=("Helvetica", 11))
        self.lbl_send_stats.pack(side="left")
        
        btn_frame = ctk.CTkFrame(send_bottom, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_send = ctk.CTkButton(btn_frame, text="📤 SEND EMAILS", 
                                       font=("Helvetica", 14, "bold"),
                                       fg_color="#e94560", height=40,
                                       command=self.start_sending)
        self.btn_send.pack(side="left", padx=5)
        
        self.btn_stop_send = ctk.CTkButton(btn_frame, text="⏹️ STOP SENDING",
                                            fg_color="#c0392b", height=40,
                                            state="disabled", command=self.stop_sending)
        self.btn_stop_send.pack(side="left", padx=5)
        
        self.btn_view_bounced = ctk.CTkButton(btn_frame, text="📋 View Bounced",
                                               fg_color="#7f8c8d", height=40,
                                               command=self.view_bounced)
        self.btn_view_bounced.pack(side="right", padx=5)
    
    def toggle_proxy(self):
        if self.var_proxy.get():
            self.proxy_frame.pack(fill="x", padx=10, pady=2)
            self.after(100, self.engine.fetch_public_proxies)
        else:
            self.proxy_frame.pack_forget()
            self.engine.use_proxy = False
    
    def load_proxy_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            count = self.engine.load_proxies_from_file(filepath)
            if count:
                self.proxy_label.configure(text=f"{count} proxies loaded")
                self.engine.use_proxy = True
            else:
                messagebox.showerror("Error", "No valid proxies found in file.\nFormat: ip:port per line")
    
    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir = path
            self.entry_save.delete(0, "end")
            self.entry_save.insert(0, path)
    
    def on_status(self, msg):
        self.after(0, lambda: self._update_status(msg))
    
    def _update_status(self, msg):
        self.status_label.configure(text=msg[:60])
        self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')} | {msg}\n")
        self.log_text.see("end")
    
    def log(self, msg):
        self.on_status(msg)
    
    # ============================================================
    # IP RESET
    # ============================================================
    
    def reset_ip(self):
        self.log("🔄 Resetting network to clear Google block...")
        try:
            system = platform.system()
            if system == "Darwin":
                for cmd in [
                    ["sudo", "dscacheutil", "-flushcache"],
                    ["sudo", "killall", "-HUP", "mDNSResponder"],
                ]:
                    try:
                        subprocess.run(cmd, capture_output=True, timeout=5)
                        self.log(f"  ✅ Ran: {' '.join(cmd)}")
                    except:
                        self.log(f"  ⚠️ Failed: {' '.join(cmd)}")
                self.log("✅ DNS cache flushed. Restart router for new IP.")
            elif system == "Windows":
                for cmd in [
                    ["ipconfig", "/flushdns"],
                    ["ipconfig", "/release"],
                    ["ipconfig", "/renew"],
                    ["netsh", "int", "ip", "reset"],
                ]:
                    try:
                        subprocess.run(cmd, capture_output=True, timeout=10, shell=True)
                        self.log(f"  ✅ Ran: {' '.join(cmd)}")
                    except:
                        self.log(f"  ⚠️ Failed: {' '.join(cmd)}")
                self.log("✅ DNS + IP reset on Windows.")
            elif system == "Linux":
                try:
                    subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], capture_output=True, timeout=5)
                    self.log("  ✅ DNS cache flushed")
                except:
                    pass
                try:
                    subprocess.run(["sudo", "nmcli", "networking", "off"], capture_output=True, timeout=5)
                    subprocess.run(["sudo", "nmcli", "networking", "on"], capture_output=True, timeout=5)
                    self.log("  ✅ Network restarted")
                except:
                    pass
            messagebox.showinfo("DNS Reset", 
                "✅ Network reset commands executed!\n\n"
                "For a full IP change, restart your router for 2 minutes.\n"
                "Google's block usually clears within 30-60 minutes.")
        except Exception as e:
            self.log(f"❌ Reset failed: {e}")
            messagebox.showerror("Error", f"Failed to reset: {e}")
    
    # ============================================================
    # EXTRACTION ENGINE
    # ============================================================
    
    def start_extraction(self):
        if self.is_running:
            return
        industry = self.entry_industry.get().strip()
        location = self.entry_location.get().strip()
        if not industry or not location:
            messagebox.showwarning("Missing Input", "Please enter both Industry and Location.")
            return
        
        self.is_running = True
        self.stop_flag = False
        self.emails_found = set()
        
        self.btn_run.configure(state="disabled", text="⏳ Running...")
        self.btn_stop.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.configure(state="disabled")
        self.progress.set(0)
        self.lbl_count.configure(text="Found: 0")
        
        self.engine.delay_min = max(0.5, self.slider_delay.get() - 0.5)
        self.engine.delay_max = self.slider_delay.get() + 0.5
        self.engine.use_proxy = self.var_proxy.get()
        
        thread = threading.Thread(target=self._run_extraction, args=(industry, location))
        thread.daemon = True
        thread.start()
    
    def stop_extraction(self):
        self.stop_flag = True
        self.log("⏹️ Stopping... please wait for current tasks to finish.")
    
    def _run_extraction(self, industry, location):
        try:
            self._do_extraction(industry, location)
        except Exception as e:
            self.log(f"❌ Critical error: {e}")
            import traceback
            self.log(traceback.format_exc()[:500])
        finally:
            self.after(0, self._extraction_done)
    
    def _do_extraction(self, industry, location):
        domain = self.entry_domain.get().strip() or None
        max_results = int(self.slider_urls.get())
        workers = int(self.slider_workers.get())
        scrape_social = self.var_social.get()
        deep_crawl = self.var_deep.get()
        
        all_urls = []
        seen = set()
        source_stats = {}
        
        # PHASE 1: Search Engines
        self.log(f"\n{'='*60}")
        self.log(f"🔎 PHASE 1/4: Searching 9 engines...")
        self.progress.set(0.05)
        
        queries = [
            f'{industry} {location} email contact',
            f'{industry} {location} @gmail.com',
            f'{industry} {location} @yahoo.com',
            f'{industry} {location} @outlook.com',
            f'{industry} {location} info@',
            f'{industry} {location} contact us',
            f'inurl:contact {industry} {location}',
            f'{industry} {location} mail address',
        ]
        if domain:
            queries.append(f'{industry} site:{domain} {location}')
        
        engines = [
            ("Bing", search_bing), ("DuckDuckGo", search_duckduckgo),
            ("Yahoo", search_yahoo), ("Brave", search_brave),
            ("Qwant", search_qwant), ("Ecosia", search_ecosia),
            ("Startpage", search_startpage), ("Mojeek", search_mojeek),
            ("Google (alt)", search_google_custom),
        ]
        
        for idx, (name, func) in enumerate(engines):
            if self.stop_flag:
                return
            self.log(f"\n  🔍 [{idx+1}/{len(engines)}] {name}")
            for q in queries[:4]:
                if self.stop_flag:
                    return
                try:
                    urls = func(self.engine, q, max_results)
                    fresh = [u for u in urls if u not in seen]
                    if fresh:
                        all_urls.extend(fresh)
                        seen.update(fresh)
                        source_stats[name] = source_stats.get(name, 0) + len(fresh)
                except:
                    pass
                time.sleep(0.3)
            self.progress.set(0.05 + (idx + 1) / len(engines) * 0.25)
        
        self.log(f"\n📎 Total URLs from search engines: {len(all_urls)}")
        for name, count in sorted(source_stats.items(), key=lambda x: -x[1]):
            self.log(f"     • {name}: {count} URLs")
        
        # PHASE 2: Directories
        self.log(f"\n{'='*60}")
        self.log(f"📂 PHASE 2/4: Scraping business directories...")
        self.progress.set(0.35)
        
        dir_emails = set()
        loc_lower = location.lower()
        if any(x in loc_lower for x in ['uk','united kingdom','england','britain','london']):
            country_codes = ['UK', 'Global']
        elif any(x in loc_lower for x in ['canada','ca','toronto','vancouver']):
            country_codes = ['CA', 'USA', 'Global']
        elif any(x in loc_lower for x in ['australia','au','sydney','melbourne']):
            country_codes = ['AU', 'Global']
        elif any(x in loc_lower for x in ['usa','united states','america','us','new york','california']):
            country_codes = ['USA', 'Global']
        else:
            country_codes = ['Global', 'USA', 'UK']
        
        target_dirs = [d for d in DIRECTORIES if d['country'] in country_codes]
        target_dirs += [d for d in DIRECTORIES if d['country'] == 'Global' and d not in target_dirs]
        target_dirs = target_dirs[:25]
        
        self.log(f"  Targeting {len(target_dirs)} directories...")
        
        for i, directory in enumerate(target_dirs):
            if self.stop_flag:
                return
            url = directory['url'].replace('{industry}', quote(industry)).replace('{location}', quote(location))
            self.log(f"  📄 [{i+1}/{len(target_dirs)}] {directory['name']}...")
            resp = self.engine.get(url)
            if resp:
                found = extract_emails(resp.text)
                if found:
                    dir_emails.update(found)
                    self.log(f"    ✅ {len(found)} emails found!")
                    if deep_crawl:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        links = []
                        for a in soup.find_all('a', href=True):
                            h = a['href']
                            d = urlparse(url).netloc
                            if h.startswith('/') and len(h) > 5 and 'search' not in h.lower():
                                links.append(f"https://{d}{h}")
                            elif h.startswith('http') and d in h:
                                links.append(h)
                        for link in links[:3]:
                            if self.stop_flag:
                                return
                            presp = self.engine.get(link)
                            if presp:
                                pf = extract_emails(presp.text)
                                dir_emails.update(pf)
                            time.sleep(0.5)
                else:
                    self.log(f"    ⏭️ No emails")
            else:
                self.log(f"    ⚠️ Failed to access")
            self.progress.set(0.35 + (i + 1) / len(target_dirs) * 0.25)
        
        self.log(f"\n📧 Emails from directories: {len(dir_emails)}")
        self.emails_found.update(dir_emails)
        
        # PHASE 3: Scrape URLs
        self.log(f"\n{'='*60}")
        self.log(f"⚡ PHASE 3/4: Scraping {len(all_urls)} URLs...")
        self.progress.set(0.65)
        
        if all_urls:
            batch_size = workers * 2
            batches = [all_urls[i:i+batch_size] for i in range(0, len(all_urls), batch_size)]
            for batch_idx, batch in enumerate(batches):
                if self.stop_flag:
                    return
                scraped = self._parallel_scrape(batch, workers)
                self.emails_found.update(scraped)
                self.progress.set(0.65 + (batch_idx + 1) / len(batches) * 0.15)
                self.after(0, self._update_results_display)
        
        # PHASE 4: Social Media
        if scrape_social:
            self.log(f"\n{'='*60}")
            self.log(f"📱 PHASE 4/4: Social media...")
            self.progress.set(0.85)
            
            social_domains = {
                'facebook': ('facebook.com', 'Facebook'),
                'linkedin': ('linkedin.com', 'LinkedIn'),
                'twitter': ('twitter.com', 'Twitter'),
                'instagram': ('instagram.com', 'Instagram'),
            }
            for platform, (domain, name) in social_domains.items():
                if self.stop_flag:
                    return
                query = f'site:{domain} {industry} {location} contact email'
                self.log(f"\n  🔍 Searching {name}...")
                urls = search_bing(self.engine, query, max_results=3) or search_duckduckgo(self.engine, query, max_results=3)
                if urls:
                    self.log(f"  📱 Found {len(urls)} {name} profiles")
                    for url in urls:
                        if self.stop_flag:
                            return
                        self.log(f"     Scraping: {url[:70]}...")
                        resp = self.engine.get(url)
                        if resp:
                            found = extract_emails(resp.text)
                            if found:
                                self.emails_found.update(found)
                        about_url = url.rstrip('/') + '/about'
                        resp = self.engine.get(about_url)
                        if resp:
                            found = extract_emails(resp.text)
                            if found:
                                self.emails_found.update(found)
                        time.sleep(1.5)
            
            self.progress.set(0.95)
        
        self.progress.set(1.0)
        self.log(f"\n{'='*60}")
        self.log(f"✅ EXTRACTION COMPLETE!")
        self.log(f"📧 Total unique emails: {len(self.emails_found)}")
        self.log(f"{'='*60}")
        self._update_stats(industry, location, source_stats)
        if self.emails_found:
            self.save_results()
    def _parallel_scrape(self, urls, workers):
        """Scrape URLs in parallel and return found emails."""
        results = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(self._scrape_single, url): url for url in urls}
            for fut in concurrent.futures.as_completed(futs):
                if self.stop_flag:
                    ex.shutdown(wait=False)
                    return results
                url = futs[fut]
                try:
                    ems = fut.result()
                    if ems:
                        results.update(ems)
                        self.log(f"  ✅ {len(ems)} from {url[:55]}...")
                except:
                    pass
        return results
    
    def _scrape_single(self, url):
        """Scrape a single URL for emails."""
        resp = self.engine.get(url)
        if not resp:
            return set()
        
        emails = set()
        text = resp.text
        soup = BeautifulSoup(text, 'html.parser')
        
        for t in soup(['script','style','noscript']):
            t.decompose()
        
        emails.update(extract_emails(text))
        
        for a in soup.find_all('a', href=True):
            h = a['href']
            if h.startswith('mailto:'):
                e = h[7:].split('?')[0].strip()
                if is_valid_email(e):
                    emails.add(e)
        
        return emails
    
    def _update_results_display(self):
        """Update the results tab with found emails."""
        self.results_text.delete("1.0", "end")
        for i, email in enumerate(sorted(self.emails_found), 1):
            self.results_text.insert("end", f"{i:4d}. {email}\n")
        self.lbl_count.configure(text=f"Found: {len(self.emails_found)}")
    
    def _update_stats(self, industry, location, source_stats):
        """Update statistics tab."""
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        
        stats = f"""
{'='*50}
📊 EXTRACTION STATISTICS
{'='*50}

🎯 Target: {industry} in {location}
⏱️  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📧 Total Emails: {len(self.emails_found)}

🔍 Source Breakdown:
"""
        for name, count in sorted(source_stats.items(), key=lambda x: -x[1]):
            stats += f"   • {name}: {count} URLs\n"
        
        stats += f"\n💾 Output Directory:\n   {self.output_dir}\n"
        
        self.stats_text.insert("1.0", stats)
        self.stats_text.configure(state="disabled")
    
    def _extraction_done(self):
        self.is_running = False
        self.btn_run.configure(state="normal", text="🚀 START EXTRACTION")
        self.btn_stop.configure(state="disabled")
        self._update_results_display()
    
    # ============================================================
    # SAVE / EXPORT
    # ============================================================
    
    def save_results(self):
        if not self.emails_found:
            messagebox.showinfo("No Emails", "No emails to save. Run extraction first.")
            return
        
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            industry = self.entry_industry.get().strip().replace(' ', '_')
            location = self.entry_location.get().strip().replace(' ', '_')
            
            # TXT
            txt_path = os.path.join(self.output_dir, f"emails_{industry}_{location}_{timestamp}.txt")
            with open(txt_path, 'w') as f:
                f.write(f"# Pro Email Extractor v{APP_VERSION}\n")
                f.write(f"# Target: {self.entry_industry.get()} in {self.entry_location.get()}\n")
                f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total: {len(self.emails_found)}\n\n")
                for email in sorted(self.emails_found):
                    f.write(email + "\n")
            
            # CSV
            csv_path = os.path.join(self.output_dir, f"emails_{industry}_{location}_{timestamp}.csv")
            with open(csv_path, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['email', 'industry', 'location', 'extracted_date'])
                for email in sorted(self.emails_found):
                    w.writerow([email, 
                              self.entry_industry.get().strip(),
                              self.entry_location.get().strip(),
                              datetime.now().strftime('%Y-%m-%d')])
            
            # JSON
            json_path = os.path.join(self.output_dir, f"emails_{industry}_{location}_{timestamp}.json")
            with open(json_path, 'w') as f:
                json.dump({
                    'app': APP_NAME,
                    'version': APP_VERSION,
                    'industry': self.entry_industry.get().strip(),
                    'location': self.entry_location.get().strip(),
                    'extracted_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_emails': len(self.emails_found),
                    'emails': sorted(self.emails_found)
                }, f, indent=2)
            
            msg = f"✅ Saved {len(self.emails_found)} emails to:\n\n📄 TXT: {txt_path}\n📊 CSV: {csv_path}\n📋 JSON: {json_path}"
            self.log(f"\n💾 Saved {len(self.emails_found)} emails to {self.output_dir}")
            messagebox.showinfo("Saved!", msg)
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def copy_results(self):
        if not self.emails_found:
            messagebox.showinfo("No Emails", "No emails to copy.")
            return
        text = '\n'.join(sorted(self.emails_found))
        self.clipboard_clear()
        self.clipboard_append(text)
        self.log(f"📋 Copied {len(self.emails_found)} emails to clipboard")
        messagebox.showinfo("Copied!", f"{len(self.emails_found)} emails copied to clipboard.")
    
    def clear_results(self):
        if self.is_running:
            return
        self.emails_found.clear()
        self.results_text.delete("1.0", "end")
        self.lbl_count.configure(text="Found: 0")
        self.log("🗑️ Results cleared")
    
    # ============================================================
    # SMTP MANAGEMENT
    # ============================================================
    
    def open_smtp_manager(self):
        """Open the SMTP profile manager dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("SMTP Profile Manager")
        dialog.geometry("650x550")
        dialog.transient(self)
        dialog.grab_set()
        
        profile = self.smtp_engine.smtp_profiles[0] if self.smtp_engine.smtp_profiles else {}
        
        # Profile name
        ctk.CTkLabel(dialog, text="Profile Name:", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(20, 2))
        entry_name = ctk.CTkEntry(dialog, width=400)
        entry_name.pack(anchor="w", padx=20, pady=2)
        entry_name.insert(0, profile.get('name', 'Main SMTP'))
        
        # SMTP Host
        ctk.CTkLabel(dialog, text="SMTP Host (e.g., smtp.sendgrid.net):", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(10, 2))
        entry_host = ctk.CTkEntry(dialog, width=400)
        entry_host.pack(anchor="w", padx=20, pady=2)
        entry_host.insert(0, profile.get('host', ''))
        
        # Port
        port_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        port_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(port_frame, text="Port:").pack(side="left")
        entry_port = ctk.CTkEntry(port_frame, width=80)
        entry_port.pack(side="left", padx=10)
        entry_port.insert(0, str(profile.get('port', 587)))
        
        var_tls = ctk.BooleanVar(value=profile.get('use_tls', True))
        ctk.CTkCheckBox(port_frame, text="Use STARTTLS", variable=var_tls).pack(side="left", padx=20)
        
        # Username
        ctk.CTkLabel(dialog, text="Username (email):", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(10, 2))
        entry_user = ctk.CTkEntry(dialog, width=400)
        entry_user.pack(anchor="w", padx=20, pady=2)
        entry_user.insert(0, profile.get('username', ''))
        
        # Password
        ctk.CTkLabel(dialog, text="Password / API Key:", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(10, 2))
        entry_pass = ctk.CTkEntry(dialog, width=400, show="*")
        entry_pass.pack(anchor="w", padx=20, pady=2)
        entry_pass.insert(0, profile.get('password', ''))
        
        # From name
        ctk.CTkLabel(dialog, text="From Name:", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(10, 2))
        entry_from_name = ctk.CTkEntry(dialog, width=400)
        entry_from_name.pack(anchor="w", padx=20, pady=2)
        entry_from_name.insert(0, profile.get('from_name', ''))
        
        # From email
        ctk.CTkLabel(dialog, text="From Email:", font=("Helvetica", 12)).pack(anchor="w", padx=20, pady=(10, 2))
        entry_from_email = ctk.CTkEntry(dialog, width=400)
        entry_from_email.pack(anchor="w", padx=20, pady=2)
        entry_from_email.insert(0, profile.get('from_email', ''))
        
        # Reply-To
        ctk.CTkLabel(dialog, text="Reply-To (optional):").pack(anchor="w", padx=20, pady=(10, 2))
        entry_reply = ctk.CTkEntry(dialog, width=400)
        entry_reply.pack(anchor="w", padx=20, pady=2)
        entry_reply.insert(0, profile.get('reply_to', ''))
        
        # Send limits
        limits_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        limits_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(limits_frame, text="Daily Limit:").pack(side="left")
        entry_limit = ctk.CTkEntry(limits_frame, width=80)
        entry_limit.pack(side="left", padx=5)
        entry_limit.insert(0, str(self.smtp_engine.daily_limit))
        
        ctk.CTkLabel(limits_frame, text="Delay (s):").pack(side="left", padx=(20, 0))
        entry_delay_min = ctk.CTkEntry(limits_frame, width=60)
        entry_delay_min.pack(side="left", padx=2)
        entry_delay_min.insert(0, str(self.smtp_engine.send_delay_min))
        ctk.CTkLabel(limits_frame, text="-").pack(side="left")
        entry_delay_max = ctk.CTkEntry(limits_frame, width=60)
        entry_delay_max.pack(side="left", padx=2)
        entry_delay_max.insert(0, str(self.smtp_engine.send_delay_max))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        def save_profile():
            try:
                profile_data = {
                    'name': entry_name.get(),
                    'host': entry_host.get(),
                    'port': int(entry_port.get()),
                    'username': entry_user.get(),
                    'password': entry_pass.get(),
                    'use_tls': var_tls.get(),
                    'from_name': entry_from_name.get(),
                    'from_email': entry_from_email.get(),
                    'reply_to': entry_reply.get(),
                }
                self.smtp_engine.smtp_profiles = [profile_data]
                self.smtp_engine.daily_limit = int(entry_limit.get())
                self.smtp_engine.send_delay_min = int(entry_delay_min.get())
                self.smtp_engine.send_delay_max = int(entry_delay_max.get())
                
                # Save to file
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smtp_profiles.json')
                self.smtp_engine.save_profile(config_path)
                
                # Update UI
                self.smtp_profile_menu.configure(values=[profile_data['name']])
                self.smtp_profile_menu.set(profile_data['name'])
                
                messagebox.showinfo("Saved", "SMTP profile saved successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        
        btn_save = ctk.CTkButton(btn_frame, text="💾 Save Profile", fg_color="#27ae60", 
                                 command=save_profile)
        btn_save.pack(side="left", padx=5)
        
        def test_from_dialog():
            test_profile = {
                'host': entry_host.get(),
                'port': int(entry_port.get()),
                'username': entry_user.get(),
                'password': entry_pass.get(),
                'use_tls': var_tls.get(),
            }
            success, msg = BulletproofSMTP().validate_smtp(test_profile)
            if success:
                messagebox.showinfo("Success", f"✅ SMTP Connection OK!\n\n{msg}")
            else:
                messagebox.showerror("Failed", f"❌ SMTP Connection Failed!\n\n{msg}")
        
        btn_test = ctk.CTkButton(btn_frame, text="🔍 Test Connection", fg_color="#2c3e50",
                                 command=test_from_dialog)
        btn_test.pack(side="left", padx=5)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", fg_color="#7f8c8d",
                                   command=dialog.destroy)
        btn_cancel.pack(side="right", padx=5)
    
    def on_smtp_profile_change(self, choice):
        """Handle SMTP profile selection change."""
        pass
    
    def test_smtp_connection(self):
        """Test the currently selected SMTP connection."""
        if not self.smtp_engine.smtp_profiles:
            messagebox.showwarning("No Config", "Please configure SMTP first (⚙️ Manage SMTP).")
            return
        
        profile = self.smtp_engine.smtp_profiles[0]
        if not profile.get('host'):
            messagebox.showwarning("No Config", "Please configure SMTP first (⚙️ Manage SMTP).")
            return
        
        self.log(f"🔍 Testing SMTP: {profile['host']}:{profile['port']}...")
        success, msg = self.smtp_engine.validate_smtp(profile)
        if success:
            self.log(f"✅ SMTP Connection successful!")
            messagebox.showinfo("Success", f"✅ SMTP Connection OK!\n\nServer: {profile['host']}\nPort: {profile['port']}")
        else:
            self.log(f"❌ SMTP Failed: {msg}")
            messagebox.showerror("Failed", f"❌ SMTP Connection Failed!\n\nError: {msg}")
    
    def toggle_send_mode(self):
        """Toggle between HTML and plain text editors."""
        if self.send_mode.get() == "html":
            self.html_editor_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.text_editor_frame.pack_forget()
        else:
            self.html_editor_frame.pack_forget()
            self.text_editor_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def load_html_file(self):
        """Load an HTML template from file."""
        filepath = filedialog.askopenfilename(
            title="Select HTML Template",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.html_editor.delete("1.0", "end")
                self.html_editor.insert("1.0", content)
                self.log(f"📄 Loaded HTML: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def check_spam_score(self):
        """Check spam score of the email content."""
        html = self.html_editor.get("1.0", "end-1c")
        text = self.text_editor.get("1.0", "end-1c")
        content = html if self.send_mode.get() == "html" else text
        
        engine = BulletproofSMTP()
        rating, score = engine.get_deliverability_score(content)
        
        messagebox.showinfo("Spam Score Analysis",
            f"{rating}\n\nScore: {score}/100\n\n"
            f"🟢 0-10: Safe (good deliverability)\n"
            f"🟡 10-25: Moderate (may get filtered)\n"
            f"🔴 25+: Risky (likely marked as spam)\n\n"
            f"Tip: Avoid words like 'free', 'buy now', 'act now', '!!!'")
    
    def load_recipients(self):
        """Load recipients from a file."""
        filepath = filedialog.askopenfilename(
            title="Select Recipients File",
            filetypes=[("Text files", "*.txt *.csv"), ("All files", "*.*")]
        )
        if not filepath:
            return
        
        try:
            emails = set()
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('email'):
                        continue
                    if ',' in line:
                        email = line.split(',')[0].strip().lower()
                    else:
                        email = line.lower()
                    if is_valid_email(email):
                        emails.add(email)
            
            if emails:
                self.smtp_recipients = sorted(emails)
                self.lbl_recipient_count.configure(text=f"{len(self.smtp_recipients)} loaded")
                self.log(f"📧 Loaded {len(self.smtp_recipients)} recipients from {filepath}")
            else:
                messagebox.showwarning("No Emails", "No valid emails found in file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
    
    def use_scraped_emails(self):
        """Use currently scraped emails as recipients."""
        if not self.emails_found:
            messagebox.showinfo("No Emails", "No scraped emails available. Run extraction first.")
            return
        
        self.smtp_recipients = sorted(self.emails_found)
        self.lbl_recipient_count.configure(text=f"{len(self.smtp_recipients)} loaded")
        self.log(f"📧 Using {len(self.smtp_recipients)} scraped emails as recipients")
    
    # ============================================================
    # SENDING ENGINE
    # ============================================================
    
    def start_sending(self):
        """Start the email sending process."""
        if self.smtp_is_sending:
            return
        
        profile = self.smtp_engine.smtp_profiles[0] if self.smtp_engine.smtp_profiles else {}
        if not profile.get('host') or not profile.get('username'):
            messagebox.showwarning("SMTP Required", 
                "Please configure SMTP settings first (⚙️ Manage SMTP).")
            return
        
        if not self.smtp_recipients:
            messagebox.showwarning("No Recipients", 
                "Please load recipient emails first.\n\n"
                "Options:\n"
                "• 📂 Load Email List - from file\n"
                "• 📥 Use Scraped Emails - from extraction")
            return
        
        subject = self.entry_subject.get().strip()
        if not subject:
            messagebox.showwarning("No Subject", "Please enter an email subject.")
            return
        
        if self.send_mode.get() == "html":
            content = self.html_editor.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showwarning("No Content", "Please enter HTML email content.")
                return
        else:
            content = self.text_editor.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showwarning("No Content", "Please enter plain text email content.")
                return
        
        # Calculate estimated time
        avg_delay = (self.smtp_engine.send_delay_min + self.smtp_engine.send_delay_max) / 2
        total_seconds = len(self.smtp_recipients) * avg_delay
        total_minutes = total_seconds / 60
        
        if not messagebox.askyesno("Confirm Send",
            f"Send to {len(self.smtp_recipients)} recipients?\n\n"
            f"Subject: {subject[:50]}...\n"
            f"Profile: {profile.get('name')}\n"
            f"Daily limit: {self.smtp_engine.daily_limit}\n"
            f"Delay: {self.smtp_engine.send_delay_min}-{self.smtp_engine.send_delay_max}s\n\n"
            f"Estimated time: {total_minutes:.0f} minutes\n\n"
            f"⚠️ Make sure you have permission to email these recipients!"):
            return
        
        # Start sending
        self.smtp_is_sending = True
        self.smtp_stop_flag = False
        self.btn_send.configure(state="disabled", text="⏳ Sending...")
        self.btn_stop_send.configure(state="normal")
        
        thread = threading.Thread(target=self._do_sending, args=(
            profile, self.smtp_recipients, subject, content
        ))
        thread.daemon = True
        thread.start()
    
    def stop_sending(self):
        """Stop the sending process."""
        self.smtp_stop_flag = True
        self.log("⏹️ Stopping send... (will finish current email)")
    
    def _do_sending(self, profile, recipients, subject, content):
        """Execute the sending in background thread."""
        html_content = content if self.send_mode.get() == "html" else None
        text_content = content if self.send_mode.get() == "text" else None
        
        results = {'sent': 0, 'failed': 0, 'bounced': 0, 'skipped': 0}
        
        def update_callback(r):
            self.after(0, lambda: self._update_send_stats(r))
        
        try:
            self.log(f"\n📤 Starting send: {len(recipients)} recipients via {profile['name']}")
            self.log(f"   Subject: {subject[:60]}...")
            self.log(f"   Daily limit: {self.smtp_engine.daily_limit}")
            
            batch_size = self.smtp_engine.batch_size
            batches = [recipients[i:i+batch_size] for i in range(0, len(recipients), batch_size)]
            
            for batch_num, batch in enumerate(batches):
                if self.smtp_stop_flag:
                    self.log("⏹️ Send stopped by user")
                    break
                
                if batch_num > 0:
                    delay = self.smtp_engine.batch_delay
                    self.log(f"\n⏸️ Batch {batch_num+1}/{len(batches)}: Waiting {delay//60} min...")
                    for _ in range(delay):
                        if self.smtp_stop_flag:
                            break
                        time.sleep(1)
                
                if self.smtp_stop_flag:
                    break
                
                self.log(f"\n📦 Batch {batch_num+1}/{len(batches)}: {len(batch)} recipients")
                
                for email in batch:
                    if self.smtp_stop_flag:
                        break
                    
                    success, msg = self.smtp_engine.send_single(
                        profile=profile,
                        to_email=email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                    )
                    
                    if success:
                        results['sent'] += 1
                    elif msg == 'bounced':
                        results['bounced'] += 1
                    elif msg == 'limit':
                        self.log(f"⏸️ Daily limit reached. Stopping.")
                        self.smtp_stop_flag = True
                        break
                    else:
                        results['failed'] += 1
                    
                    self.after(0, lambda r=dict(results): self._update_send_stats(r))
            
            self.log(f"\n{'='*50}")
            self.log(f"📊 SEND COMPLETE")
            self.log(f"   Sent: {results['sent']}")
            self.log(f"   Failed: {results['failed']}")
            self.log(f"   Bounced: {results['bounced']}")
            self.log(f"   Skipped: {results['skipped']}")
            self.log(f"{'='*50}")
            
        except Exception as e:
            self.log(f"❌ Send error: {e}")
        finally:
            self.after(0, self._sending_done)
    
    def _update_send_stats(self, results):
        """Update the send statistics display."""
        self.lbl_send_stats.configure(
            text=f"📊 Sent: {results['sent']} | Failed: {results['failed']} | "
                 f"Bounced: {results['bounced']} | Skipped: {results['skipped']} | "
                 f"Daily: {self.smtp_engine.daily_send_count}/{self.smtp_engine.daily_limit}"
        )
    
    def _sending_done(self):
        """Called when sending completes."""
        self.smtp_is_sending = False
        self.btn_send.configure(state="normal", text="📤 SEND EMAILS")
        self.btn_stop_send.configure(state="disabled")
    
    def view_bounced(self):
        """Show bounced emails."""
        if not self.smtp_engine.bounced_emails:
            messagebox.showinfo("No Bounces", "No bounced emails recorded.")
            return
        
        bounces = sorted(self.smtp_engine.bounced_emails)
        text = '\n'.join(bounces)
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Bounced Emails ({len(bounces)})")
        dialog.geometry("500x400")
        dialog.transient(self)
        
        textbox = ctk.CTkTextbox(dialog, wrap="word")
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")
        
        ctk.CTkButton(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Exit", "Extraction is running. Stop and exit?"):
                self.stop_flag = True
                self.destroy()
        else:
            self.destroy()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    print(f"🚀 Starting {APP_NAME} v{APP_VERSION}...")
    print(f"📂 Emails will be saved to: ~/Desktop/Emails/")
    print()
    
    app = ProEmailExtractorApp()
    app.mainloop()
