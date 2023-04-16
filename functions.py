import pandas as pd
import re
import datetime
import classes
from tqdm import tqdm
import mip
import settings
import pandas as pd

#アンケート結果のデータフレームを取得
def get_df() ->pd.DataFrame:
    xlsx_path = input('アンケート結果のパスを入力してください\n').replace('\"','')
    df = pd.read_excel(xlsx_path)
    df.drop('タイムスタンプ',axis = 1,inplace = True)
    return df

#列名のリストかタプル->Microblockのタプル
def get_blocks(cols:list) ->tuple:
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

#Microblockのリストかタプル->日付一覧のタプル
def get_dates(blocks:list) ->tuple:
    dates = set()
    for block in blocks:
        dates.add(block.date)
    dates = sorted(dates)
    return tuple(dates)

#各メンバーごとにAnswerオブジェクトを作成し、タプルにまとめる。アンケート結果のデータフレームとMicroblockの一覧を引数として利用する
def get_answers(df:pd.DataFrame,blocks:list) ->tuple:
    answers = []
    n_rows = len(df.index)
    for n in range(n_rows):
        series = df.loc[n]
        ans = classes.Answer(person_id = n,series=series,blocks=blocks)
        answers.append(ans)
    return tuple(answers)

#day_shiftのリストにシフトの種類を追加したものをリストとして返す
def set_roles_to_dayshift(day_shift:list,answer:classes.Answer,current=[[]],n=0) ->list:
    if n < len(day_shift):
        block = day_shift[n]
        if answer.in_lunch_group and block.in_lunch_time:
            if_lunch = set_roles_to_dayshift(day_shift=day_shift,answer=answer,current=[pattern + [classes.Microblock_with_roletype(block=block,role='lunch')] for pattern in current],n=n+1)
        else:
            if_lunch = []
        if answer.in_desert_group and block.in_desert_time:
            if_desert = set_roles_to_dayshift(day_shift=day_shift,answer=answer,current=[pattern + [classes.Microblock_with_roletype(block=block,role='desert')] for pattern in current],n=n+1)
        else:
            if_desert = []
        if block.in_help_time:
            if_help = set_roles_to_dayshift(day_shift=day_shift,answer=answer,current=[pattern + [classes.Microblock_with_roletype(block=block,role='help')] for pattern in current],n=n+1)
        else:
            if_help = []
        if block.in_normal_shift_time:
            if_normal = set_roles_to_dayshift(day_shift=day_shift,answer=answer,current=[pattern + [classes.Microblock_with_roletype(block=block,role='normal')] for pattern in current],n=n+1)
        else:
            if_normal = []
        return if_lunch+if_desert+if_help+if_normal
    else:
        return current

#Answerオブジェクト1つ、1日のMicroblockの一覧、その日の日付->その日のシフトの候補一覧
def get_dayshift_patterns(answer:classes.Answer,day_blocks:list,day:datetime.date) ->tuple:
    person_id = answer.person_id
    name = answer.name
    patterns = [classes.DayShift(person_id = person_id, name = name, day=day, day_shift = [],answer=answer)]#全くシフトに入らないパターンだけ先に作っておく
    for n in range(len(day_blocks)):
        if not answer.answer[day_blocks[n]]:
            continue
        current = [day_blocks[n]]
        patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = tuple(current),answer=answer))
        for m in range(n+1,len(day_blocks)):
            if answer.answer[day_blocks[m]]:
                current.append(day_blocks[m])
                for pattern in set_roles_to_dayshift(day_shift=current,answer=answer):
                    patterns.append(classes.DayShift(person_id = person_id, name = name, day=day, day_shift = tuple(pattern),answer = answer))
            else:
                break
    patterns = [pattern for pattern in patterns if pattern.is_ok]#連続してシフトに入る時間を調べて、条件に合うものだけ残す
    return tuple(patterns)

#日付一覧、Microblock一覧、Answerオブジェクトの一覧->全てのメンバーの全ての日の1日のシフトの候補一覧
def get_dayshift_for_all(dates:list,blocks:list,answers:list):
    patterns = []
    for day in dates:
        day_blocks = [block for block in blocks if block.date == day]
        for answer in answers:
            patterns += get_dayshift_patterns(answer = answer, day_blocks = day_blocks, day = day)
    return tuple(patterns)

#1人の全ての日のシフトの候補の一覧、日付一覧->その人の1か月のシフトの候補の一覧
def get_monthshift_patterns(person_day_shift_list:list,dates:list):
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
        monthshift_patterns.append(classes.MonthShift(person_id = month_shift[0].person_id, name = month_shift[0].name, month_shift = tuple(month_shift),answer = month_shift[0].answer))
    monthshift_patterns = [pattern for pattern in monthshift_patterns if pattern.is_ok]
    return tuple(monthshift_patterns)

#全てのメンバーの各日のシフトの候補、メンバーのidの一覧、日付の一覧->全てのメンバーの1か月のシフトの候補一覧
def get_monthshift_for_all(day_shift_patterns:list,person_id_tuple:tuple,dates:list):
    patterns = []
    for id,i in enumerate(person_id_tuple):
        person_day_shift_list = [day_shift for day_shift in day_shift_patterns if day_shift.person_id == id]
        month_shift_patterns = get_monthshift_patterns(person_day_shift_list=person_day_shift_list,dates=dates)
        patterns += month_shift_patterns
    return tuple(patterns)

#最適化モデルを作成し、1か月のシフトの候補それぞれに変数を割り当てる。モデルを返す
def register(month_shift_patterns:list):
    model = mip.Model()
    for pattern in month_shift_patterns:
        pattern.var = model.add_var('x',var_type = 'B')
    return model

#1人1つシフトパターンを割りあてる
def one2one(month_shift_patterns:list,person_id_tuple:tuple,model:mip.Model):
    for id in person_id_tuple:
        person_monthshift_var_list = [month_shift.var for month_shift in month_shift_patterns if month_shift.person_id == id]
        model += sum(person_monthshift_var_list) == 1
    return model

#必要な人員の確保
def set_requirements(blocks:list,month_shift_patterns:list,model:mip.Model) ->mip.Model:#blocksの中にはMicroblockオブジェクト
    for block in blocks:
        for min,max,role,included in ((settings.min_shift,settings.max_shift,'normal',block.in_normal_shift_time),
                            (settings.min_help,settings.max_help,'help',block.in_help_time),
                            (settings.min_desert,settings.max_desert,'desert',block.in_desert_time),
                            (settings.min_lunch,settings.max_lunch,'lunch',block.in_lunch_time)):
            if included:
                target_blocks = []
                for month_shift in month_shift_patterns:
                    for day_shift in month_shift.month_shift:
                        if classes.Microblock_with_roletype(block,role) in day_shift.day_shift and month_shift not in target_blocks:
                            target_blocks.append(month_shift)
                if len(target_blocks) > 0:
                    model += min <= sum([block.var for block in target_blocks])
                    model += max >= sum([block.var for block in target_blocks])
    return model