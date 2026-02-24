from langchain.tools import tool
import os
import datetime
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
def add_calendar_event(date: str, time: str, event: str) -> str:
    """
    Add a calendar event to Notion.
    Provide date (YYYY-MM-DD), time (HH:MM), and event description.
    Status is automatically set to 'Upcoming' if the date is today or in the future,
    or 'Done' if the date has already passed.
    Valid statuses are: 'Upcoming', 'Done', 'Cancelled'.
    """

    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return {"error": "Keys not set"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = "https://api.notion.com/v1/pages"

    start_datetime = f"{date}T{time}:00" if time else date

    # Auto-determine status: 'Upcoming' for future/today, 'Done' for past dates
    try:
        event_date = datetime.date.fromisoformat(date)
        status = "Upcoming" if event_date >= datetime.date.today() else "Done"
    except ValueError:
        status = "Upcoming"  # Default to Upcoming if date can't be parsed

    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Event": {
                "title": [{"text": {"content": event}}]
            },
            "Date": {
                "date": {"start": start_datetime}
            },
            "Status": {
                "select": {"name": status}
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return f"Added Event: '{event}' at {time} on {date} with status '{status}'"

    except Exception as e:
        return f"Error : {str(e)}"


@tool
def get_all_calendar_events() -> list:
    """
    Fetch all events from the Notion calendar database with no date filter.
    Returns every event with its name, date, and time, sorted by date (earliest first).
    Use this when the user wants to see the full calendar or all upcoming events.
    """
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return [{"error": "Notion API Key or Calendar DB ID not set"}]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/databases/{db_id}/query"

    # Sort all events by Date ascending (earliest first)
    payload = {
        "sorts": [
            {
                "property": "Date",
                "direction": "ascending"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        events = []
        for page in data.get("results", []):
            props = page.get("properties", {})

            # Extract event name
            event_title_list = props.get("Event", {}).get("title", [])
            event_name = event_title_list[0].get("text", {}).get("content", "") if event_title_list else "Untitled Event"

            # Extract date
            date_prop = props.get("Date", {}).get("date", {})
            event_date = date_prop.get("start", "No Date") if date_prop else "No Date"

            # Extract time (rich_text field)
            time_list = props.get("Time", {}).get("rich_text", [])
            event_time = time_list[0].get("text", {}).get("content", "") if time_list else "All day"

            events.append({
                "event": event_name,
                "date": event_date,
                "time": event_time
            })

        if not events:
            return [{"message": "No events found in the calendar"}]

        return events

    except Exception as e:
        return [{"error": f"Error fetching calendar events: {str(e)}"}]


@tool
def update_calendar_event(
    event_name: str,
    new_name: str = None,
    new_date: str = None,
    new_time: str = None,
    new_status: str = None
) -> str:
    """
    Update one or more fields of an existing calendar event in Notion.
    Searches for the event by name (partial match) and updates only the fields you provide.

    Args:
        event_name: The current name of the event to search for (partial match supported).
        new_name:   Optional. New name/title for the event.
        new_date:   Optional. New date in YYYY-MM-DD format.
        new_time:   Optional. New time in HH:MM format.
        new_status: Optional. New status — must be 'Upcoming', 'Done', or 'Cancelled'.
                    If new_date is provided but new_status is not, status is auto-set:
                    future/today → 'Upcoming', past → 'Done'.
    """
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return "Error: Notion API Key or Calendar DB ID not set"

    if not any([new_name, new_date, new_time, new_status]):
        return "Error: Provide at least one field to update (new_name, new_date, new_time, or new_status)"

    valid_statuses = ["Upcoming", "Done", "Cancelled"]
    if new_status and new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Step 1: Find the event by name
    query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    query_payload = {
        "filter": {
            "property": "Event",
            "rich_text": {
                "contains": event_name
            }
        }
    }

    try:
        res = requests.post(query_url, headers=headers, json=query_payload)
        res.raise_for_status()
        results = res.json().get("results", [])

        if not results:
            return f"Error: No event found matching '{event_name}'"

        page = results[0]
        page_id = page["id"]

        # Get the current matched title for the confirmation message
        title_list = page.get("properties", {}).get("Event", {}).get("title", [])
        matched_name = title_list[0].get("text", {}).get("content", event_name) if title_list else event_name

        # Step 2: Build the properties patch — only include what was provided
        updated_properties = {}
        changes = []

        if new_name:
            updated_properties["Event"] = {
                "title": [{"text": {"content": new_name}}]
            }
            changes.append(f"name → '{new_name}'")

        if new_date or new_time:
            # Resolve final date and time values (use existing if not provided)
            current_date_prop = page.get("properties", {}).get("Date", {}).get("date", {})
            current_start = current_date_prop.get("start", "") if current_date_prop else ""

            # Parse existing start to get date/time parts
            if "T" in current_start:
                current_date_part, current_time_part = current_start.split("T")[0], current_start.split("T")[1][:5]
            else:
                current_date_part, current_time_part = current_start, ""

            final_date = new_date if new_date else current_date_part
            final_time = new_time if new_time else current_time_part
            final_start = f"{final_date}T{final_time}:00" if final_time else final_date

            updated_properties["Date"] = {"date": {"start": final_start}}

            if new_date:
                changes.append(f"date → '{new_date}'")
            if new_time:
                changes.append(f"time → '{new_time}'")

            # Auto-set status from new date if no explicit status given
            if new_date and not new_status:
                try:
                    event_date_obj = datetime.date.fromisoformat(new_date)
                    auto_status = "Upcoming" if event_date_obj >= datetime.date.today() else "Done"
                    updated_properties["Status"] = {"select": {"name": auto_status}}
                    changes.append(f"status → '{auto_status}' (auto)")
                except ValueError:
                    pass

        if new_status:
            updated_properties["Status"] = {"select": {"name": new_status}}
            changes.append(f"status → '{new_status}'")

        # Step 3: PATCH the page
        patch_url = f"https://api.notion.com/v1/pages/{page_id}"
        patch_res = requests.patch(patch_url, headers=headers, json={"properties": updated_properties})
        patch_res.raise_for_status()

        return f"Updated event '{matched_name}': {', '.join(changes)}"

    except Exception as e:
        return f"Error updating calendar event: {str(e)}"


@tool
def delete_calendar_event(event_name: str) -> str:
    """
    Delete a calendar event from Notion by name.
    Searches for the event by name (partial match) and permanently deletes it.

    Args:
        event_name: The name of the event to delete (partial match supported).
    """
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_CALENDAR_DB_ID")

    if not api_key or not db_id:
        return "Error: Notion API Key or Calendar DB ID not set"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }

    # Step 1: Find the event by name
    query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
    query_payload = {
        "filter": {
            "property": "Event",
            "rich_text": {
                "contains": event_name
            }
        }
    }

    try:
        res = requests.post(query_url, headers=headers, json=query_payload)
        res.raise_for_status()
        results = res.json().get("results", [])

        if not results:
            return f"Error: No event found matching '{event_name}'"

        page = results[0]
        page_id = page["id"]

        # Get the matched title for the confirmation message
        title_list = page.get("properties", {}).get("Event", {}).get("title", [])
        matched_name = title_list[0].get("text", {}).get("content", event_name) if title_list else event_name

        # Step 2: Delete the page
        delete_url = f"https://api.notion.com/v1/pages/{page_id}"
        delete_res = requests.delete(delete_url, headers=headers)
        delete_res.raise_for_status()

        return f"Deleted event: '{matched_name}'"

    except Exception as e:
        return f"Error deleting calendar event: {str(e)}"