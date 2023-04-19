import datetime
import settings
import pandas as pd

class MicroBlock: #シフトの1コマ
    def __init__(self,start:datetime.datetime,end:datetime.datetime,text:str): #startとendはdatetimeオブジェクト。textはデータフレームでの列名
        self.start = start
        self.end = end
        self.text = text
        self.in_lunch_time = settings.lunch_start <= self.start.time() and self.end.time() <= settings.lunch_end
        self.in_desert_time = settings.desert_start <= self.start.time() and self.end.time() <= settings.desert_end
        self.in_help_time = settings.help_start <= self.start.time() and self.end.time() <= settings.help_end
        self.in_normal_shift_time = settings.normal_shift_start <= self.start.time() and self.end.time() <= settings.normal_shift_end
        if start.date() != end.date():
            raise ValueError('startとendの日付が異なります。')
        else:
            self.date = start.date()

    @property
    def delta(self):
        return self.end-self.start
    
    @property
    def minutes(self):
        minutes = int(self.delta.total_seconds() / 60)
        if minutes < 1:
            raise ValueError('MicroBlockが小さすぎます')
        elif minutes % 1 != 0:
            raise ValueError('MicroBlockの分が整数になっていません。')
        else:
            return minutes

    def __str__(self):
        return f'{self.start}から{self.end}の間({self.minutes}分)'
    
    def __eq__(self, other) -> bool:
        if type(self) == type(other) and (self.start, self.end) == (other.start, other.end):
            return True
        else:
            return False
        
    def __hash__(self) -> int:
        return hash(str(self))


class Microblock_with_roletype(MicroBlock):
    def __init__(self,block:MicroBlock,role:str):
        assert isinstance(block,MicroBlock)
        assert not isinstance(block,Microblock_with_roletype)
        super().__init__(start=block.start,end=block.end,text=block.text)
        self.role = role
        self.base = block
    def __str__(self):
        return str(self.base)+self.role
    def __eq__(self,other):
        if super().__eq__(other) and self.role == other.role:
            return True
        else:
            return False
            


#MicroblockからMicroblock_with_roletypeを生成
def set_role(self:MicroBlock,role:str):
    return Microblock_with_roletype(block=self,role=role)

MicroBlock.set_role = set_role

class Answer:
    def __init__(self,person_id:int,series:pd.Series,blocks:list):
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
    def __init__(self,person_id:int,name:str,day:datetime.date,day_shift:list,answer:Answer):#day_shiftの中にはMicroblock_with_roletype
        self.person_id = person_id
        self.name = name
        self.day = day
        self.day_shift = day_shift
        self.answer = answer
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
        return settings.min_continue <= self.long <= settings.max_continue or self.long == datetime.timedelta(minutes=0)

    @property
    def minutes(self):
        return sum([block.minutes for block in self.day_shift])
    @property
    def minutes(self):
        return sum([block.minutes for block in self.day_shift])

class MonthShift:
    def __init__(self,person_id:int,name:str,month_shift:list,answer:Answer):#month_shiftの中にはDayShiftオブジェクト
        for day_shift in month_shift:
            if not isinstance(day_shift,DayShift):
                raise TypeError(f'month_shiftの中に{day_shift}が入っています。')
            elif day_shift.person_id != person_id or day_shift.name != name:
                raise Exception(f'違う人の1日のシフトが同じMonthShiftインスタンスに含まれています。')
        self.month_shift = month_shift
        self.name = name
        self.person_id = person_id
        self.answer = answer
        self.var = 'undefined'
    
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
        return sum(work_list) <= settings.max_work_days
    
    def __str__(self):
        return f'{self.name}({self.person_id})の1か月のシフトの候補'
    
    @property
    def flat(self):
        flat_list = []
        for day_shift in self.month_shift:
            for block in day_shift.day_shift:
                flat_list.append(block)
        return flat_list
    
    @property
    def minutes(self):
        return sum([day_shift.minutes for day_shift in self.month_shift])