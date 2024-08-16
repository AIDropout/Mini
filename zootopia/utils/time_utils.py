from datetime import datetime
import pytz


def get_current_time_cst_iso8601() -> str:
    central_tz = pytz.timezone("America/Chicago")
    current_time = datetime.now(central_tz)
    return current_time.strftime("%Y-%m-%d %H:%M:%S%z")


def get_current_time_readable() -> str:
    current_time = datetime.now()
    return current_time.strftime("%-I:%M%p %A, %b %-d, %Y")
