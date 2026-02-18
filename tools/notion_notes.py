from langchain.tools import tool
import os
import requests

@tool
def get_notes() -> list:
    """Get all pending notes from Notion"""
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_NOTES_DB_ID")

    if not api_key or not db_id:
        return ["Error: Notion API Key or DB id not set"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json",
        "Notion-Version":"2022-06-28"
    }

    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    payload = {
        "filter":{
            "property":"Status",
            "select":{
                "equals":"Pending"
            }
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()

        notes = []
        for page in data.get("results",[]):
            props = page.get("properties", {})
            title_list = props.get("Note", {}).get("title", {})
            note_content = title_list[0].get("text",{}).get("content", "") if title_list else "Untitled Note"
            notes.append(note_content)

        return notes
    
    except Exception as e:
        return [f"Error Fetching Notes: {str(e)}"]

@tool
def add_note(note:str) -> str:
    """Add a new note to Notion"""
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_NOTES_DB_ID")

    if not api_key or not db_id:
        return ("Error: Notion API Key or DB id not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json",
        "Notion-Version":"2022-06-28"
    }

    url="https://api.notion.com/v1/pages"


    payload = {
        "parent" : {"database_id":db_id},
        "properties":{
            "Note":{
                "title" : [{"text":{"content":note}}]
            },
            "Status": {
                "select":{"name": "Pending"}
            }
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return f"Note added successfully: {note}"
    except Exception as e:
        return f"Error adding note: {str(e)}"