months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
months_abv = {m[:3].lower():m for m in months}

import cgi

def valid_day(day):
    try:
        d = int(day)
    except ValueError:
        return None
    return d if 1 <= d <= 31 else None
    
def valid_year(year):
    try:
        y = int(year)
    except ValueError:
        return None
    return y if 1900 <= y <= 2020 else None
    
def valid_month(month):
    short_month = month[:3].lower()
    return months_abv.get(short_month)
    
def escape_html(s):
    return cgi.escape(s, quote = True)
