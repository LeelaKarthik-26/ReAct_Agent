from langchain.tools import tool
import os
import requests


@tool
def get_calendar_events(date: str) -> dict:
    """
    This Tool will get calender events for a specific date (YYYY-MM-DD) from Notion
    """
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return {"error":"Keys not set"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json",
        "Notion-Version":"2022-06-28"
    }

    url=f"https://api.notion.com/v1/databases/{db_id}/query"

    payload={
        "filter":{
            "property":"Date",
            "date":{
                "equals":date
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        events = []

        for page in data.get("results",[]):
            props = page.get("properties",[])

            # Extracting the Event name (Title)
            event_title_list = props.get("Event",{}).get("title", [])
            event_name = event_title_list[0].get("text",{}).get("content","") if event_title_list else "Untitled event"

            # Extract the Time
            time_list = props.get("Time",{}).get("rich_text",[])
            event_time = time_list[0].get("text",{}).get("content","") if time_list else "All day"

            events.append({
                "event":event_name,
                "time":event_time
            })
        return {"events":events, "date":date}
    except Exception as e:
        return {"error": str(e)}

@tool
def add_calendar_event(date:str, time:str, event:str)-> str:
    """
    this tool will be used to add calender events in notion.
    You have to provide date (YYY-MM-DD), time(HH:MM), event(description)
    """

    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return {"error":"Keys not set"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json",
        "Notion-Version":"2022-06-28"
    }

    url="https://api.notion.com/v1/pages"

    start_datetime = f"{date}T{time}:00" if time else date

    payload = {
        "parent" : {"database_id":db_id},
        "properties":{
            "Event":{
                "title":[{"text":{"content":event}}]
            },
            "Date":{
                "date":{"start":start_datetime}
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return f"Added Event:{event} at {time} on {date}"
    
    except Exception as e:
        return f"Error : {str(e)}"