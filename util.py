import holidays


def is_holiday(date):
    us_holidays = holidays.US()
    return date in us_holidays

    