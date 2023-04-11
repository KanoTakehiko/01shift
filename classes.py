import datetime
import settings

class MicroBlock: #シフトの1コマ
    def __init__(self,start,end,text): #startとendはdatetimeオブジェクト。textはデータフレームでの列名
        self.start = start
        self.end = end
        self.text = text
        if start.date() != end.date():
            raise ValueError('startとendの日付が異なります。')
        else:
            self.date = start.date()

    @property
    def delta(self):
        return self.end - self.start

    @property
    def minutes(self):
        minutes = int(self.delta.total_seconds() / 60)
        if minutes < 1:
            raise ValueError('MicroBlockが小さすぎます')
        elif self.minutes % 1 != 0:
            raise ValueError('MicroBlockの分が整数になっていません。')

    def __str__(self):
        return f'{self.start}から{self.end}の間({self.minutes}分)'


class Answer:
    def __init__(self,person_id,series,blocks):
        self.person_id = person_id
        self.name = series['名前']
        self.in_lunch_group = series['ランチ班'] in (1,'所属している')
        self.in_desert_group = series['デザート班'] in (1,'所属している')
        self.is_senior = series['上級生'] in (1,'〇')
        self.answer = {}
        for block in blocks:
            self.answer[block] = series[block.text] in (1,'〇')

    def __str__(self):
        return f'{self.name}({self.id})の回答'


class DayShift:
    def __init__(self,person_id,name,day,day_shift):
        self.person_id = person_id
        self.name = name
        self.day = day
        self.day_shift = day_shift
        for x in day_shift:
            if not isinstance(x,MicroBlock):
                raise TypeError(f'DayShiftインスタンスのリストの中に{x}が入っています')
    
    @property
    def long(self):
        if len(self.day_shift) > 0:
            return self.day_shift[-1].end - self.day_shift[0].start
        else:
            return datetime.timedelta(minutes=0)

    @property
    def work(self):
        return self.long > datetime.timedelta(minutes=0)
    
    def __str__(self):
        return f'{self.name}({self.person_id})の{self.day}のシフトの候補'
    
    @property
    def is_ok(self):
        return settings.min_continue < self.long < settings.max_continue or self.long == datetime.timedelta(minutes=0)


class MonthShift:
    def __init__(self,person_id,name,month_shift):
        for day_shift in month_shift:
            if not isinstance(day_shift,DayShift):
                raise TypeError(f'month_shiftの中に{day_shift}が入っています。')
            elif day_shift.person_id != person_id or day_shift.name != name:
                raise Exception(f'違う人の1日のシフトが同じMonthShiftインスタンスに含まれています。')
        self.month_shift = month_shift
        self.name = name
        self.person_id = person_id
    
    @property
    def long(self):
        delta_list = []
        for day_shift in self.month_shift:
            if isinstance(day_shift,DayShift):
                delta_list.append(day_shift.long)
        return sum(delta_list)
    
    @property
    def is_ok(self):
        work_list = []
        for day_shift in self.month_shift:
            work_list.append(day_shift.work)
        return sum(work_list) < settings.max_work
    
    def __str__(self):
        return f'{self.name}({self.person_id})の1か月のシフトの候補'