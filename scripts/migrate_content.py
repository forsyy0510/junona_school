
import os
import sys
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from info.models import InfoSection
from file_manager import file_manager

OLD_SITE_URL = "https://junona-school-vdonsk.rostovschool.ru/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def download_file(url, section):
    """Downloads a file and returns the path relative to static/uploads/info"""
    if not url:
        return None
        
    try:
        # Resolve relative URLs
        if not url.startswith('http'):
            url = urljoin(OLD_SITE_URL, url)
            
        response = requests.get(url, headers=HEADERS, stream=True)
        if response.status_code == 200:
            filename = url.split('/')[-1].split('?')[0]  # Remove query params
            
            # Use file_manager logic or manual save
            # For simplicity in this script, we'll manually save to ensure control
            upload_folder = os.path.join(os.getcwd(), 'static', 'uploads', 'info', 'migration', section)
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Return relative path/url format expected by field
            # In site_junona, file fields usually expect a URL like '/download_file/...'
            # But the file manager saves them and returns a URL.
            # We will try to simulate what file_manager does or just put the file and valid URL
            
            # Modern file manager uses DB. We need to register the file in DB if we want full compatibility.
            # But for now let's just return the local path for debug
            return file_path, filename
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None, None


def migrate_main_section(app):
    print("Migrating Main Section (Common)...")
    url = urljoin(OLD_SITE_URL, "sveden/common")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        response.encoding = 'utf-8' # Ensure correct encoding
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 1. Full Name & Short Name (Usually at the top or in title)
    # Based on probe, we might need to find specific headers. 
    # Let's use the layout: usually "Основные сведения" page has text blocks.
    
    data = {}
    
    # Extracting standard fields by keyword search
    def find_text_after_keyword(keyword):
        element = soup.find(string=re.compile(keyword))
        if element:
            # Try to get text from parent or next sibling
            full_text = element.parent.get_text(strip=True)
            # Remove keyword from text
            clean = re.sub(re.escape(keyword) + r'[:\-\s]*', '', full_text, flags=re.IGNORECASE)
            return clean.strip()
        return None

    data['founder'] = find_text_after_keyword("Администрация города Волгодонска")
    data['address'] = find_text_after_keyword("3473") # Searching by index start might be risky, but let's try finding address block
    
    # Founder detailed search
    founder_el = soup.find(string=re.compile("Администрация города Волгодонска"))
    if founder_el:
        data['founder'] = "Администрация города Волгодонска в лице Управления образования г. Волгодонска" # Hardcoded based on reading
    
    # Address detailed search (looking for postal code pattern)
    address_match = soup.find(string=re.compile(r"3473\d{2}"))
    if address_match:
        data['address'] = address_match.strip()
    
    # Phones
    phones = []
    phone_el = soup.find(string=re.compile("Контактный телефон"))
    if phone_el:
        # Check parent text
        text = phone_el.parent.get_text(strip=True)
        # Extract digits format
        found_phones = re.findall(r'[\d\(\)\-\s]{7,}', text)
        for p in found_phones:
             if len(re.sub(r'\D', '', p)) > 5: # Filter short noise
                 phones.append(p.strip())
    data['telephone'] = ", ".join(phones)
    
    # Email
    email_el = soup.find('a', href=re.compile(r'mailto:'))
    if email_el:
        data['email'] = email_el.get_text(strip=True)
    
    # Work time
    work_time_parts = []
    work_keywords = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    for kw in work_keywords:
        el = soup.find(string=re.compile(kw))
        if el:
            work_time_parts.append(el.strip())
    data['work_time'] = "; ".join(list(set(work_time_parts))) # Dedup and join
    
    # Full Name and Short Name
    # Often in meta tags or h1/h2
    # Hardcoding based on known site for now as fallback, but trying to scrape
    # <div class="block-title"> often contains site name in header
    
    data['full_name'] = 'МБОУ "ИТ Гимназия "Юнона" при ВИТИ НИЯУ МИФИ г. Волгодонска"'
    data['short_name'] = 'МБОУ "ИТ Гимназия "Юнона"'
    data['reg_date'] = "01.09.1990" # Placeholder if not found
    
    reg_date_el = soup.find(string=re.compile("Дата создания"))
    if reg_date_el:
         data['reg_date'] = reg_date_el.parent.get_text(strip=True).replace("Дата создания:", "").strip()

    # Files (License, Accreditation)
    # These map to specific fields in the new site
    # New site fields (based on section.html logic): 
    # - licenseDocLink -> Лицензия
    # - accreditationDocLink -> Аккредитация
    
    # Finding License
    license_link = soup.find('a', href=re.compile(r'license|li[sz]enz|^/file/download\?id=58')) # Specific ID from probe check
    license_url = None
    if license_link:
         license_url = urljoin(OLD_SITE_URL, license_link['href'])
    
    # Download license if found
    license_path = None
    if license_url:
        print(f"Downloading license from {license_url}")
        l_path, l_name = download_file(license_url, 'main')
        if l_path:
             # Construct URL for DB
             license_path = f"/info/download_file/main/{l_name}|Лицензия"

    print(f"Extracted Data: {data}")

    # Prepare form_data
    form_data = {
        'full_name': data.get('full_name'),
        'short_name': data.get('short_name'),
        'founding_date': data.get('reg_date'),
        'location_address': data.get('address'),
        'contact_phone': data.get('telephone'),
        'contact_email': data.get('email'),
        'working_hours': data.get('work_time'), # Tentative, checking template next
        'founder_info': data.get('founder'),
        # 'licenseDocLink': license_path if license_path else '' 
    }

    # Save to DB
    with app.app_context():
        # Mapping 'common' from old site to 'main' in new site
        section = InfoSection.query.filter_by(endpoint='main').first()
        if not section:
            print("Main section not found in DB!")
            return

        current_data = json.loads(section.text) if section.text else {'form_data': {}}
        
        # Merge carefully
        for k, v in form_data.items():
            if v:
                current_data['form_data'][k] = v
        
        section.text = json.dumps(current_data, ensure_ascii=False)
        db.session.commit()
        print("Main section updated in DB.")

if __name__ == "__main__":
    app = create_app()
    migrate_main_section(app)
