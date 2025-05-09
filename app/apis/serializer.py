from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_restx import fields



class TimeAgo(fields.Raw):
    def format(self, value):
        now = datetime.now()
        if now - value <= timedelta(seconds=3):
            return '刚刚'
        diff = relativedelta(now, value)
        if diff.years > 0:
            return f'{diff.years}年前'
        if diff.months > 0:
            return f'{diff.months}个月前'
        if diff.days > 0:
            return f'{diff.days}天前'
        if diff.hours > 0:
            return f'{diff.hours}小时前'
        if diff.minutes > 0:
            return f'{diff.minutes}分钟前'
        return f'{diff.seconds}秒前'
