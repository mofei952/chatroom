from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask_restx import fields


class TimeAgo(fields.Raw):
    def format(self, dt):
        now = datetime.now()
        if now - dt <= timedelta(seconds=3):
            return '刚刚'
        diff = relativedelta(now, dt)
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


class ShortTime(fields.Raw):
    def format(self, dt):
        today = date.today()
        if dt.date() == today:
            return dt.strftime('%H:%M')
        if dt.date() == today - timedelta(days=1):
            return f'昨天 {dt.strftime("%H:%M")}'
        elif dt.year == today.year:
            return dt.strftime('%m-%d %H:%M')
        return dt.strftime('%Y-%m-%d %H:%M')
