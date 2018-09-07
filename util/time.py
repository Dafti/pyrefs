from datetime import datetime,timedelta

def bytes2time(dt):
    us = dt / 10
    try:
        td = timedelta(microseconds=us)
        time = datetime(1601,1,1) + td
    except:
        return '<bad time format>'
    if time.year < 2000 or time.year > datetime.today().year:
        return '<wrong date?> {}'.format(time)
    return time
