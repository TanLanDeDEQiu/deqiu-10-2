import time
print(time.strftime("%Y-%m-%d", time.localtime(time.time())))
a = 1234
a = f"{a:04d}"
print(a)
import main
print(main.get_records())