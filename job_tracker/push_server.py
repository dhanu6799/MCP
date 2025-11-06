from mcp.server.fastmcp import FastMCP
from database import write_log
from datetime import datetime

mcp = FastMCP("push_notification_server")


@mcp.tool()
async def send_push_notification(tracker_name: str, message: str) -> str:
    """
    Send a push notification with job tracking updates.
    
    Args:
        tracker_name: Name of the job tracker sending the notification
        message: The notification message
    
    Returns:
        Confirmation message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notification = f"[{timestamp}] {tracker_name}: {message}"
    
    # Log to database
    write_log(tracker_name, "notification", message)
    
    # In a real app, this would send to a notification service
    print(f"📱 PUSH: {notification}")
    
    return f"Notification sent successfully at {timestamp}"


if __name__ == "__main__":
    mcp.run(transport='stdio')