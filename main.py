#インポート
import classes
import functions

#データフレームを取得
df = functions.get_df()

#コマのタプルを取得
blocks = functions.get_blocks(df.columns)

#日付のタプルを取得
dates = functions.get_dates(blocks)

#それぞれの回答をオブジェクト化
answers = functions.get_answers(df=df,blocks=blocks)

#1日のシフトの候補を作成
day_shift_patterns = functions.get_dayshift_for_all(dates=dates,blocks=blocks,answers=answers)

#1か月のシフトのパターンのタプルを作成
person_id_tuple = tuple(range(len(df.index)))
month_shift_patterns = functions.get_monthshift_for_all(day_shift_patterns = day_shift_patterns, person_id_tuple=person_id_tuple, dates=dates)

#それぞれのパターンに変数を登録
model = functions.register(month_shift_patterns)

#1人1つシフト表
model = functions.one2one(month_shift_patterns=month_shift_patterns,person_id_tuple = person_id_tuple,model = model)

model = functions.set_requirements(blocks = blocks,month_shift_patterns=month_shift_patterns,model=model)