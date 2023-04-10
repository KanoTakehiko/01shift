import pandas as pd
import re
import datetime
import classes

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
    blocks = tuple(blocks)
    return blocks

def get_dates(blocks):
    dates = set()
    for block in blocks:
        dates.add(block.date)
    dates = sorted(dates)
    dates = tuple(dates)
    return dates

def get_answers(df,blocks):
    answers = []
    n_rows = len(df.index)
    for n in range(n_rows):
        series = df.loc[n]
        ans = classes.Answer(person_id = n,series=series,blocks=blocks)
        answers.append(ans)
    answers = tuple(answers)
    return answers

def get_dayshift_patterns(answer,day_blocks,day):
    person_id = answer.person_id
    name = answer.name
    patterns = [classes.DayShift(person_id = person_id, name = name, day=day, day_shift = [])]
    for n in range(len(day_blocks)):
        if not answer.answer[day_blocks[n]]:
            continue
        current = [day_blocks[n]]
        patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = current.copy()))
        for m in range(n+1,len(day_blocks)):
            if answer.answer[day_blocks[m]]:
                current.append(day_blocks[m])
                patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = current.copy()))
            else:
                break
    return patterns

def get_dayshift_for_all(dates,blocks,answers):
    patterns = []
    for day in dates:
        day_blocks = [block for block in blocks if block.date == day]
        for answer in answers:
            patterns += get_dayshift_patterns(answer = answer, day_blocks = day_blocks, day = day)
    return patterns