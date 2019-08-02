import datetime

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)
def get_arrays(year):
    first_days = []
    last_days = []
    for month in range(1,13):
        last_days.append(last_day_of_month(datetime.date(year, month, 1)))
    for month in range(1,13):
        first_days.append(datetime.date(year, month, 1))
        
    return first_days,last_days