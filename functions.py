import pandas as pd
import re
import datetime
import classes
from tqdm import tqdm

def get_df():
    xlsx_path = input('アンケート結果のパスを入力してください\n').replace('\"','')
    df = pd.read_excel(xlsx_path)
    df.drop('タイムスタンプ',axis = 1,inplace = True)
    return df

def get_blocks(cols):
    cols = tuple(cols)
    blocks = []
    block_regex = re.compile('^\D*?(\d{1,2})月\D*?(\d{1,2})日\D*?(\d{1,2}):(\d{1,2})～(\d{1,2}):(\d{1,2})\D*?$')
    for col in cols:
        mo = block_regex.search(col)
        if mo != None:
            month = int(mo.group(1))
            day = int(mo.group(2))
            start_hour = int(mo.group(3))
            start_minute = int(mo.group(4))
            end_hour = int(mo.group(5))
            end_minute = int(mo.group(6))
            text = mo.group(0)
            start_datetime = datetime.datetime(year=2023,month=month,day=day,hour=start_hour,minute=start_minute)
            end_datetime = datetime.datetime(year=2023,month=month,day=day,hour=end_hour,minute=end_minute)
            block = classes.MicroBlock(start = start_datetime,end = end_datetime,text=text)
            blocks.append(block)
    return tuple(blocks)

def get_dates(blocks):
    dates = set()
    for block in blocks:
        dates.add(block.date)
    dates = sorted(dates)
    return tuple(dates)

def get_answers(df,blocks):
    answers = []
    n_rows = len(df.index)
    for n in range(n_rows):
        series = df.loc[n]
        ans = classes.Answer(person_id = n,series=series,blocks=blocks)
        answers.append(ans)
    return tuple(answers)

def get_dayshift_patterns(answer,day_blocks,day):
    person_id = answer.person_id
    name = answer.name
    patterns = [classes.DayShift(person_id = person_id, name = name, day=day, day_shift = [])]
    for n in range(len(day_blocks)):
        if not answer.answer[day_blocks[n]]:
            continue
        current = [day_blocks[n]]
        patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = tuple(current)))
        for m in range(n+1,len(day_blocks)):
            if answer.answer[day_blocks[m]]:
                current.append(day_blocks[m])
                patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = tuple(current)))
            else:
                break
    patterns = [pattern for pattern in patterns if pattern.is_ok]
    return tuple(patterns)

def get_dayshift_for_all(dates,blocks,answers):
    patterns = []
    for day in dates:
        day_blocks = [block for block in blocks if block.date == day]
        for answer in answers:
            patterns += get_dayshift_patterns(answer = answer, day_blocks = day_blocks, day = day)
    return tuple(patterns)

def get_monthshift_patterns(person_day_shift_list,dates):
    old = [()]
    for day in dates:
        the_day_shift_list = [day_shift for day_shift in person_day_shift_list if day_shift.day == day]
        new = []
        for old_month_shift in old:
            for day_shift in the_day_shift_list:
                new.append(old_month_shift+(day_shift,))
        old = new
    monthshift_patterns = []
    for month_shift in new:
        monthshift_patterns.append(classes.MonthShift(person_id = month_shift[0].person_id, name = month_shift[0].name, month_shift = tuple(month_shift)))
    monthshift_patterns = [pattern for pattern in monthshift_patterns if pattern.is_ok]
    return tuple(monthshift_patterns)

def get_monthshift_for_all(day_shift_patterns,person_id_tuple,dates):
    patterns = []
    for id,i in enumerate(person_id_tuple):
        person_day_shift_list = [day_shift for day_shift in day_shift_patterns if day_shift.person_id == id]
        month_shift_patterns = get_monthshift_patterns(person_day_shift_list=person_day_shift_list,dates=dates)
        patterns += month_shift_patterns
    return tuple(patterns)