from datetime import datetime
# 2003-04-12 23:05:06 +01:00

date_time_str = '31/03/22 21:30'
date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M')
print(date_time_obj)
print(datetime.now())
