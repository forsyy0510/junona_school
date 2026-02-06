
import requests
from bs4 import BeautifulSoup
import re

URL = "https://junona-school-vdonsk.rostovschool.ru/sveden/common"
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

def probe():
    print(f"Fetching {URL}...")
    try:
        response = requests.get(URL, headers=HEADERS, verify=False) # Skip SSL verify if needed
        soup = BeautifulSoup(response.content, 'html.parser')
        
        keywords = [
            "Администрация города",
            "Контактный телефон",
            "Электронная",
            "Лицензия"
        ]
        
        print(f"Page Title: {soup.title.string if soup.title else 'No Title'}")
        
        for kw in keywords:
            print(f"\n--- Searching for: {kw} ---")
            elements = soup.find_all(string=re.compile(kw))
            for el in elements:
                parent = el.parent
                print(f"Found in tag: <{parent.name} class='{parent.get('class')}'>")
                print(f"Context: {parent.get_text(strip=True)[:100]}...")
                # checking grandparent to see structure
                grandparent = parent.parent
                if grandparent:
                     print(f"Grandparent: <{grandparent.name} class='{grandparent.get('class')}'>")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    probe()
