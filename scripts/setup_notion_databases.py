import os
import requests
import json
from dotenv import load_dotenv

def create_databases():
    load_dotenv()
    
    api_key = os.getenv("NOTION_API_KEY")
    
    print("--- Setup Notion Databases ---")
    
    if not api_key:
        print("NOTION_API_KEY not found in .env")
        print("Please set it in your .env file first.")
        return

    print(f"Using API Key: {api_key[:4]}...{api_key[-4:]}")
    
    print("\nTo create databases, we need a Parent Page ID.")
    print("1. Create a new Page in Notion (e.g., 'Smart Task Planner').")
    print("2. Share this page with your Integration (Add connections).")
    print("3. Copy the Page ID from the URL (the long string at the end).")
    print("   Example URL: https://www.notion.so/My-Page-1234567890abcdef1234567890abcdef")
    print("   The ID is: 1234567890abcdef1234567890abcdef")
    user_input = input("\nEnter Parent Page ID or URL: ").strip()
    
    def extract_page_id(input_str):
        if "?" in input_str:
            input_str = input_str.split("?")[0]
        
        if "notion.so" in input_str:
            parts = input_str.split("/")
            last_part = parts[-1]
            import re
            match = re.search(r'([a-fA-F0-9]{32})', last_part)
            if match:
                return match.group(1)
            return last_part
        
        return input_str.replace("-", "")

    parent_page_id = extract_page_id(user_input)
    
    if len(parent_page_id) != 32:
        print(f"Warning: The ID '{parent_page_id}' doesn't look like a standard 32-char UUID.")
        print("Attempting to use it anyway...")


    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    print("\nCreating 'Smart Task Planner Calendar'...")
    calendar_payload = {
        "parent": { "type": "page_id", "page_id": parent_page_id },
        "title": [ { "type": "text", "text": { "content": "ReAct Agent Calendar" } } ],
        "properties": {
            "Event": { "title": {} },
            "Date": { "date": {} },
            "Time": { "rich_text": {} },
            "Status": {
                "select": {
                    "options": [
                        { "name": "Upcoming", "color": "blue" },
                        { "name": "Done", "color": "green" },
                        { "name": "Cancelled", "color": "red" }
                    ]
                }
            }
        }
    }
    
    try:
        response = requests.post("https://api.notion.com/v1/databases", headers=headers, json=calendar_payload)
        if response.status_code == 200:
            cal_db_id = response.json()["id"]
            print(f"Created Calendar DB! ID: {cal_db_id}")
        else:
            print(f"Failed to create Calendar DB: {response.text}")
            cal_db_id = None
    except Exception as e:
        print(f"Exception: {e}")
        cal_db_id = None

    print("\nCreating 'Smart Task Planner Notes'...")
    notes_payload = {
        "parent": { "type": "page_id", "page_id": parent_page_id },
        "title": [ { "type": "text", "text": { "content": "ReAct Agent Notes" } } ],
        "properties": {
            "Note": { "title": {} },
            "Status": {
                "select": {
                    "options": [
                        { "name": "Pending", "color": "yellow" },
                        { "name": "Done", "color": "green" }
                    ]
                }
            }
        }
    }
    
    try:
        response = requests.post("https://api.notion.com/v1/databases", headers=headers, json=notes_payload)
        if response.status_code == 200:
            notes_db_id = response.json()["id"]
            print(f"Created Notes DB! ID: {notes_db_id}")
        else:
            print(f"Failed to create Notes DB: {response.text}")
            notes_db_id = None
    except Exception as e:
        print(f"Exception: {e}")
        notes_db_id = None

    print("\n--- Setup Complete ---")
    if cal_db_id and notes_db_id:
        print("Please update your .env file with these IDs:")
        print(f"NOTION_CALENDAR_DB_ID={cal_db_id}")
        print(f"NOTION_NOTES_DB_ID={notes_db_id}")
        print("\nThen restart the application.")

if __name__ == "__main__":
    create_databases()