from langchain.tools import tool
import os
import requests

@tool
def get_notes() -> list:
    """Get all notes from Notion, including their title and current status (Pending or Done)."""
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_NOTES_DB_ID")

    if not api_key or not db_id:
        return ["Error: Notion API Key or DB id not set"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    try:
        res = requests.post(url, headers=headers, json={})   # No filter — fetch all notes
        res.raise_for_status()
        data = res.json()

        notes = []
        for page in data.get("results", []):
            props = page.get("properties", {})

            # Extract note title
            title_list = props.get("Note", {}).get("title", [])
            note_content = title_list[0].get("text", {}).get("content", "") if title_list else "Untitled Note"

            # Extract status
            status = props.get("Status", {}).get("select", {})
            status_name = status.get("name", "No Status") if status else "No Status"

            notes.append({"note": note_content, "status": status_name})

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


@tool
def update_note_status(note_title: str, status: str) -> str:
    """
    Update the status of an existing note in Notion.
    Searches for the note by its title/content and sets its Status to either 'Pending' or 'Done'.

    Args:
        note_title: The title/content of the note to find (partial match supported).
        status: The new status to set — must be either 'Pending' or 'Done'.
    """
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_NOTES_DB_ID")

    if not api_key or not db_id:
        return "Error: Notion API Key or DB id not set"

    # Validate status value
    valid_statuses = ["Pending", "Done"]
    if status not in valid_statuses:
        return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Step 1: Query the DB to find the page by note title
    query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    query_payload = {
        "filter": {
            "property": "Note",
            "rich_text": {
                "contains": note_title
            }
        }
    }

    try:
        res = requests.post(query_url, headers=headers, json=query_payload)
        res.raise_for_status()
        results = res.json().get("results", [])

        if not results:
            return f"Error: No note found matching '{note_title}'"

        # Use the first matching result
        page_id = results[0]["id"]
        matched_title = ""
        title_list = results[0].get("properties", {}).get("Note", {}).get("title", [])
        if title_list:
            matched_title = title_list[0].get("text", {}).get("content", note_title)

        # Step 2: PATCH the page to update its Status
        patch_url = f"https://api.notion.com/v1/pages/{page_id}"
        patch_payload = {
            "properties": {
                "Status": {
                    "select": {"name": status}
                }
            }
        }

        patch_res = requests.patch(patch_url, headers=headers, json=patch_payload)
        patch_res.raise_for_status()

        return f"Successfully updated note '{matched_title}' status to '{status}'"

    except Exception as e:
        return f"Error updating note status: {str(e)}"
