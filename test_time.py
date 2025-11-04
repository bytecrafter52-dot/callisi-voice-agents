from datetime import datetime
from zoneinfo import ZoneInfo

# Test Pakistan time
pk_time = datetime.now(ZoneInfo('Asia/Karachi'))
print(f"Current Pakistan time: {pk_time.strftime('%I:%M %p')}")
print(f"Full ISO: {pk_time.isoformat()}")

# Test UTC time
utc_time = datetime.utcnow()
print(f"UTC time: {utc_time.strftime('%I:%M %p')}")
