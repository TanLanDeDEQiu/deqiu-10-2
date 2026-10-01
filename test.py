import time
print(time.strftime("%Y-%m-%d", time.localtime(time.time())))
a = "abc"
a = f"{a:04d}"
print(a)