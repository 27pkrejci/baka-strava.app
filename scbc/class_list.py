"""
Module for discovering and fetching the list of all classes from the school website.

Fetches the HTML from https://www.dgkralupy.cz/studium/rozvrhy-hodin/ and extracts
all class links from the "ROZVRHY TŘÍD" section.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def fetch_classes_from_school() -> List[Dict[str, str]]:
    """
    Fetch all class schedules from the school website.
    
    Returns:
        List of dicts with keys:
        - 'name': class name (e.g., '7.G', '3.P')
        - 'code': schedule code (e.g., 'truk' from truk.htm)
        - 'url': full URL to the schedule
    """
    url = "https://www.dgkralupy.cz/studium/rozvrhy-hodin/"
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            raise Exception(f"Failed to fetch page: {response.status_code}")
    except Exception as e:
        raise Exception(f"Could not fetch class list from {url}: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    classes = []
    
    h3_tags = soup.find_all("h3")
    class_section_found = False
    
    for h3 in h3_tags:
        text = h3.get_text(strip=True).lower()
        if "tříd" in text:
            class_section_found = True
            ul = h3.find_next("ul", class_="clss")
            if ul:
                links = ul.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    class_name = link.get_text(strip=True)
                    
                    match = re.search(r'/rozvrh/([a-z0-9]+)\.htm', href)
                    if match and class_name:
                        code = match.group(1)
                        classes.append({
                            'name': class_name,
                            'code': code,
                            'url': f"https://www.dgkralupy.cz/BakaFiles/rozvrh/{code}.htm"
                        })
            break
    
    if not class_section_found:
        raise Exception("Could not find 'ROZVRHY TŘÍD' section on the page")
    
    if not classes:
        raise Exception("No classes found in the class list")
    
    return classes


def fetch_teachers_from_school() -> List[Dict[str, str]]:
    """
    Fetch all teacher schedules from the school website.
    
    Returns:
        List of dicts with keys:
        - 'name': teacher name
        - 'code': schedule code
        - 'url': full URL to the schedule
    """
    url = "https://www.dgkralupy.cz/studium/rozvrhy-hodin/"
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            raise Exception(f"Failed to fetch page: {response.status_code}")
    except Exception as e:
        raise Exception(f"Could not fetch teacher list from {url}: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    teachers = []
    
    h3_tags = soup.find_all("h3")
    
    for h3 in h3_tags:
        text = h3.get_text(strip=True).lower()
        if "učitel" in text:
            ul = h3.find_next("ul", class_="clss")
            if ul:
                links = ul.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    teacher_name = link.get_text(strip=True)

                    match = re.search(r'/rozvrh/([a-z0-9]+)\.htm', href)
                    if match and teacher_name:
                        code = match.group(1)
                        teachers.append({
                            'name': teacher_name,
                            'code': code,
                            'url': f"https://www.dgkralupy.cz/BakaFiles/rozvrh/{code}.htm"
                        })
    
    return teachers


def fetch_rooms_from_school() -> List[Dict[str, str]]:
    """
    Fetch all room schedules from the school website.
    
    Returns:
        List of dicts with keys:
        - 'name': room number/identifier
        - 'code': schedule code
        - 'url': full URL to the schedule
    """
    url = "https://www.dgkralupy.cz/studium/rozvrhy-hodin/"
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            raise Exception(f"Failed to fetch page: {response.status_code}")
    except Exception as e:
        raise Exception(f"Could not fetch room list from {url}: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    rooms = []

    h3_tags = soup.find_all("h3")
    
    for h3 in h3_tags:
        text = h3.get_text(strip=True).lower()
        if "učeb" in text:
            ul = h3.find_next("ul", class_="clss")
            if ul:
                links = ul.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    room_name = link.get_text(strip=True)
                    
                    match = re.search(r'/rozvrh/([a-z0-9]+)\.htm', href)
                    if match and room_name:
                        code = match.group(1)
                        rooms.append({
                            'name': room_name,
                            'code': code,
                            'url': f"https://www.dgkralupy.cz/BakaFiles/rozvrh/{code}.htm"
                        })
    
    return rooms


if __name__ == "__main__":
    print("Fetching classes...")
    classes = fetch_classes_from_school()
    print(f"Found {len(classes)} classes:")
    for cls in classes:
        print(f"  {cls['name']}: {cls['code']}")
    
    print("\nFetching teachers...")
    teachers = fetch_teachers_from_school()
    print(f"Found {len(teachers)} teachers (showing first 5):")
    for teacher in teachers[:5]:
        print(f"  {teacher['name']}: {teacher['code']}")
    
    print("\nFetching rooms...")
    rooms = fetch_rooms_from_school()
    print(f"Found {len(rooms)} rooms:")
    for room in rooms:
        print(f"  {room['name']}: {room['code']}")
