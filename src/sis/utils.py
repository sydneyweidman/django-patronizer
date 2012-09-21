import datetime

def calc_checkdigit(barcode_stub):
    """Calculate the check digit for the given barcode."""
    odd = [int(i) for (idx, i) in enumerate(barcode_stub) if not idx % 2]
    even = [int(i) for (idx, i) in enumerate(barcode_stub) if idx % 2]
    step_1 = sum([i*2 for i in odd if i*2 < 10])
    step_2 = sum([i*2 - 9 for i in odd if i*2 >= 10])
    total = sum(even + [step_1, step_2])
    # find next highest multiple of 10, and subtract total from that
    return str((10 - total % 10) % 10)

DATE_FMT = '%d-%m-%y'
CUTOFF = (6,30)

def get_next_date(month, day, format=DATE_FMT, today=datetime.date.today(), cutoff=CUTOFF):
    """
    Return the next occurrence of month/day as a datetime.date object
    formatted according to format. Parameter format should be a string
    matching datetime.date.strftime format codes. Parameters month and
    day should be integers. Raise ValueError if day is invalid for
    month. Optional parameter today should be a date object. This
    parameter is provided to allow testing of arbitrary dates.

    If (today.month, today.day) is greater than cutoff, then set the
    expiry date to a next plus one year, e.g. if this is July 1, 2008,
    set expiry date to Aug 31 of 2009 rather than 2008.
    """
    # Just do this in case the day is invalid for the month
    # so that a ValueError is raised. Check for current and next year
    # in case of leap year.
    y = today.year
    t = d = today
    datetime.date(y,month,day)
    datetime.date(y+1,month,day)
    while True:
        if d.day == day and d.month == month:
            break
        d += datetime.date.resolution
    if t > datetime.date(t.year, cutoff[0], cutoff[1]):
        d = datetime.date(y + 1, d.month, d.day)
    return d.strftime(format)
