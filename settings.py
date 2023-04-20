from datetime import timedelta,time

min_continue = timedelta(hours=2)
max_continue = timedelta(hours=4)

max_work_days = 2

min_senior = 0
max_senior = 2

min_junior = 0
max_junior = 1

min_shift = 0
max_shift = 2
normal_shift_start = time(hour=12)
normal_shift_end = time(hour=19)

min_help = 0
max_help = 1
help_start = time(hour=11)
help_end = time(hour=12)

min_desert = 0
max_desert = 1
desert_start = time(hour=11)
desert_end = time(hour=12)

min_lunch = 0
max_lunch = 0
lunch_start = time(hour=11)
lunch_end = time(hour=12)