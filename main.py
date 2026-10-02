import sqlite3
import time
import os
import base64
import shutil
from PIL import Image
import sys

def pick_app_dir():
    if getattr(sys, 'frozen', False):
        here = os.path.dirname(sys.executable)
    else:
        here = os.path.dirname(os.path.abspath(__file__))

    portable = os.path.join(here,"data")
    if os.path.exists(portable):
        return portable

    return os.path.join(os.environ["APPDATA"],"记账本")

APP_DIR = pick_app_dir()
os.makedirs(os.path.join(APP_DIR, "images"), exist_ok=True)
DB = os.path.join(APP_DIR, "记账.db")


def pre_load():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS 设置 
        ( start_money REAL DEFAULT 0 )
    """)


    c.execute("""CREATE TABLE IF NOT EXISTS 预算 
    ( 
            plan_money_key INTEGER PRIMARY KEY,
            plan_money_purpose TEXT,
            plan_money REAL,
            plan_picture TEXT,
            plan_created_at TEXT
    )
    """)

    c.execute("""CREATE TABLE IF NOT EXISTS 目标
    ( 
            target_key INTEGER PRIMARY KEY,
            target_name TEXT,
            target_money REAL,
            target_rate REAL,
            target_picture TEXT,
            target_created_at TEXT
    )
    """)

    c.execute("""CREATE TABLE IF NOT EXISTS 记录
    (
            main_key INTEGER PRIMARY KEY,
            operation_type TEXT,
            operation_money REAL,
            operation_remark TEXT,
            operation_date TEXT,
            plan_money_key INTEGER
    )
    """)

    if not c.execute("SELECT start_money FROM 设置").fetchone():
        c.execute("INSERT INTO 设置 (start_money) VALUES (?)", (0,))
    conn.commit()


# ⭐ 只要 import 这个模块，就保证表存在。
#    桌面版 app.py 走的是 import，不会执行 main()，
#    所以这个调用必须放在模块层 —— 只放在 main() 里的话，
#    别人拿到的是空库，一保存就报 no such table。
pre_load()




#设置
def set_start_money():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    set_money = input("请设置初始余额：")
    c.execute("UPDATE 设置 SET start_money = ?", (set_money,))
    print(f"改了{c.rowcount}行")
    conn.commit()
    conn.close()

def get_balance():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    start = c.execute("""SELECT start_money FROM 设置""").fetchone()[0] or 0
    income,expense = get_income_expense()
    balance = start + income - expense
    conn.close()
    return balance

def get_income_expense():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    income = c.execute("""SELECT SUM(operation_money) FROM 记录 WHERE operation_type = ?""",('收入',)).fetchone()[0] or 0
    expense = c.execute("""SELECT SUM(operation_money) FROM 记录 WHERE operation_type = ?""",('支出',)).fetchone()[0] or 0
    conn.close()
    return income, expense

def delete_record(main_key):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM 记录 WHERE main_key = ?",(main_key,))
    print(f"删除了{c.rowcount}行")
    conn.commit()
    conn.close()

def ask_key(prompt):
    while True:
        raw = input(prompt)
        if raw.isdigit():
            return int(raw)
        print("编号得是数字")


#记录
def a_record(operation_type, operation_money, operation_remark, operation_date, plan_money_key=None):
    if operation_type == '预算支出':
        operation_type = "支出"
    if operation_type not in ("支出","收入"):
        raise ValueError(f"类型不对：{operation_type}")
    try:
        operation_money = float(operation_money)
    except (TypeError,ValueError):
        raise ValueError(f"金额不是数字：{operation_money}")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO 记录 (operation_type, operation_money, operation_remark, operation_date, plan_money_key)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_type, operation_money, operation_remark, operation_date, plan_money_key))
    conn.commit()
    conn.close()

def all_show(only=None):
    rows = get_records(only)
    s = get_summary(only)
    print(f"总记录（共{s['count']}条）    总收入：{s['income']}     总支出：{s['expense']}")
    for r in rows:
        print(f'==========记录{r["main_key"]:04d}==========\n'
              f'[类型]:{r["operation_type"]}\n[金额]:{r["operation_money"]}\n'
              f'[备注]:{r["operation_remark"]}\n[日期]:{r["operation_date"]}\n'
              f'===========================')

def show_balance(balance):
    print(f"当前余额：{balance}")


#预算
def create_plan(plan_money_purpose,plan_money,plan_picture):
    plan_money = check_money(plan_money,"预算")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO 预算 (plan_money_purpose, plan_money, plan_picture, plan_created_at)
    Values (?, ?, ?, ?)
    """,(plan_money_purpose,plan_money,plan_picture,time.strftime("%Y-%m-%d", time.localtime(time.time()))))
    conn.commit()
    conn.close()

def all_show_plan():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c1 = conn.cursor()
    for a,a1,a2,a3,a4 in c.execute("""SELECT plan_money_key, plan_money_purpose, plan_money, plan_picture, plan_created_at FROM 预算"""):
        used = c1.execute("""SELECT  SUM(operation_money) FROM 记录 WHERE plan_money_key = ?""",(a,)).fetchone()[0] or 0
        left = a2 - used
        percent = ( used / a2 ) * 100
        print(f"========预算{a:04d}========\n[预算目的]:{a1}\n[预算金额]:{a2}\n[已花费预算]:{used:.2f}\n[剩余余额]:{left:.2f}\n[已花费]:{percent:.2f}\n[创建日期]:{a4}\n=======================")
    conn.close()

def delete_plan(plan_money_key):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""DELETE FROM 预算 WHERE plan_money_key = ?""", (plan_money_key,))
    print(f"删除了{c.rowcount}行")
    conn.commit()
    conn.close()

def update_plan(plan_money_key, new_money):
    new_money = check_money(new_money,"预算")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE 预算 SET plan_money = ? WHERE plan_money_key = ?""", (new_money,plan_money_key,))
    changed = c.rowcount
    conn.commit()
    conn.close()
    return changed

def check_money(raw, what="金额"):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{what}不是数字:{raw}")
    if value <= 0:
        raise ValueError(f"{what}必须大于0:{raw}")
    return value


def get_plans():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    plans = c.execute("""SELECT plan_money_key, plan_money_purpose, plan_money, plan_picture, plan_created_at FROM 预算""").fetchall()
    result = []
    for p in plans:
        item = dict(p)
        item['used'] = c.execute("SELECT SUM(operation_money) FROM 记录 WHERE plan_money_key = ?",(p['plan_money_key'],)).fetchone()[0] or 0
        item['left'] = p['plan_money'] - item['used']
        item['left_pct'] = item['left'] / p['plan_money'] * 100
        result.append(item)
    conn.close()
    return result



#目标
def create_target(target_name, target_money, target_rate, target_picture):
    target_money = check_money(target_money,"目标金额")
    try:
        target_rate = float(target_rate)
    except (TypeError, ValueError):
        raise ValueError(f"占比不是数字：{target_rate}")
    if target_rate <= 0:
        raise ValueError(f"占比必须大于 0：{target_rate}")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO 目标 (target_name, target_money, target_rate, target_picture, target_created_at) 
    Values (?, ?, ?, ?, ?)""",(target_name,target_money,target_rate,target_picture,time.strftime("%Y-%m-%d", time.localtime(time.time()))))
    conn.commit()
    conn.close()

def all_show_target():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    balance = get_balance()
    for a,a1,a2,a3,a4,a5 in c.execute("""SELECT target_key, target_name, target_money, target_rate, target_picture, target_created_at FROM 目标"""):
        need = a2 / a3
        progress = (balance / need) * 100
        print(f"========目标{a:04d}========\n[目标内容]:{a1}\n[目标金额]:{a2}\n[目标占比]:{a3}\n[需要的余额]:{need:.2f}\n[目标进度]:{progress:.2f}%\n[创建日期]:{a5}\n======================")
    conn.close()

def delete_target(target_key):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM 目标 WHERE target_key = ?",(target_key,))
    print(f"删除了{c.rowcount}行")
    conn.commit()
    conn.close()


######

def get_targets():
    balance = get_balance()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    rows = c.execute("""SELECT target_key, target_name, target_money, target_rate, target_picture, target_created_at FROM 目标""").fetchall()
    conn.close()
    results = []
    for r in rows:
        item = dict(r)
        item['need'] = r['target_money'] / r['target_rate']
        item['progress'] = balance / item['need'] * 100
        results.append(item)
    return results


def get_records(only=None, limit=None):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    where = ""
    args = ()
    if only:
        where = " WHERE operation_type = ? "
        args = (only,)
    sql = """ SELECT main_key, operation_type, operation_money, operation_remark, operation_date 
            FROM 记录 """ + where + " ORDER BY operation_date DESC, main_key DESC "
    if limit:
        sql += "LIMIT ? "
        args = args + (limit,)
    rows = c.execute(sql,args).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_summary(only=None):
    where =''
    args = ()
    if only:
        where = " WHERE operation_type = ? "
        args = (only,)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM 记录 " + where, args).fetchone()[0]
    conn.close()
    income,expense = get_income_expense()
    if only == '支出':
        income = 0
    elif only == '收入':
        expense = 0
    return {"count":count,"income":income,"expense":expense}


def save_image(src_path):
    name = os.path.basename(src_path)
    target = os.path.join(APP_DIR, "images", name)
    if os.path.exists(target):
        name = f"{int(time.time())}_{name}"
        target = os.path.join(APP_DIR, "images", name)
    shutil.copy2(src_path, target)
    return name

def read_image(filename):
    if not filename:
        return None
    path = os.path.join(APP_DIR, "images", filename)
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        raw = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(filename)[1].lstrip('.').lower()
    if ext == 'jpg':
        ext = 'jpeg'
    return f"data:image/{ext};base64,{raw}"

#废函数
def trim_white(path,tolerance=10):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img,mask=img.convert("RGBA").split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    w,h = img.size
    px = img.load()
    step = max(1, w//200)

    def row_white(y):
        return all(all(ch >= 255 - tolerance for ch in px[x, y]) for x in range(0, w, step))

    def col_white(x):
        return all(all(ch >= 255 - tolerance for ch in px[x, y]) for y in range(0, h, step))

    top = 0
    while top < h - 1 and row_white(top):
        top += 1
    bottom = h - 1
    while bottom > top and row_white(bottom):
        bottom -= 1
    left = 0
    while left < w - 1 and col_white(left):
        left += 1
    right = w - 1
    while right > left and col_white(right):
        right -= 1
    top,left = max(0, top - 2),max(0, left - 2)
    bottom,right = min(h - 1, bottom + 2),min(w - 1, right + 2)
    new_w, new_h = right - left + 1, bottom - top + 1
    if new_w == w and new_h == h:
        return False
    if new_w < w * 0.2 or new_h < h * 0.2:
        return False

    img.crop((left, top, right + 1, bottom + 1)).save(path)
    return True




def main():
    pre_load()
    while True:
        print('打印菜单：   \n1.记一笔    \n2.看全部    \n3.看余额    \n4.重置余额    \n5.预算    \n6.目标    \n7.删除一条记录    \n0.退出     ')
        choice = input("请选择：")
        if choice == '1':
            plan_money_key = None
            operation_type = input("请输入类型：")
            operation_money = input("请输入金额：")
            operation_remark = input("请输入备注：")
            operation_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            try:
                a_record(operation_type, operation_money, operation_remark, operation_date, plan_money_key)
                print(f"已添加一条记录。\n[类型]:{operation_type}\n[金额]:{operation_money}\n[备注]:{operation_remark}\n[日期]:{operation_date}")
            except ValueError as e:
                print(f"没记上：{e}")
        elif choice == '2':
            while True:
                print("==========查看类型==========\n1.看全部\n2.看所有目标\n3.看所有预算\n4.只看收入\n5.只看支出\n0.退出")
                choice3 = input("请选择：")
                if choice3 == '1':
                    all_show()
                elif choice3 == '2':
                    all_show_target()
                elif choice3 == '3':
                    all_show_plan()
                elif choice3 == '4':
                    all_show('收入')
                elif choice3 == '5':
                    all_show('支出')
                elif choice3 == '0':
                    break
        elif choice == '3':
            show_balance(get_balance())
        elif choice == '4':
            set_start_money()
        elif choice == '5':
            while True:
                print("\n1.创建新的预算计划    \n2.查看所有的预算    \n3.删除一个预算    \n4追加预算    \n0.退出")
                choice1 = input("请选择：")
                if choice1 == '1':
                    plan_money_purpose = input("请输入预算目的：")
                    plan_money = input("请输入预算金额：")
                    plan_picture = None
                    create_plan(plan_money_purpose,plan_money,plan_picture)
                elif choice1 == '2':
                    all_show_plan()
                elif choice1 == '3':
                    all_show_plan()
                    plan_money_key = ask_key("请输入要删除预算的对应编号：")
                    delete_plan(plan_money_key)
                elif choice1 == '4':
                    all_show_plan()
                    plan_money_key = ask_key("改哪条（输编号）：")
                    new_money = input("新的预算金额：")
                    update_plan(plan_money_key, new_money)
                elif choice1 == '0':
                    break
        elif choice == '6':
            while True:
                print("\n1.创建新的目标计划    \n2.查看所有的目标    \n3.删除一个目标    \n0.退出")
                choice2 = input("请选择：")
                if choice2 == '1':
                    target_name = input("请输入目标内容：")
                    target_money = input("请输入目标金额：")
                    target_rate = input("请输入占比：")
                    target_picture = None
                    try:
                        create_target(target_name, target_money, target_rate, target_picture)
                        print("目标创建好了")
                    except ValueError as e:
                        print(f"没建成：{e}")
                elif choice2 == '2':
                    all_show_target()
                elif choice2 == '3':
                    all_show_target()
                    target_key = ask_key("请输入要删除目标的对应编号：")
                    delete_target(target_key)
                elif choice2 == '0':
                    break
        elif choice == '7':
            all_show()
            main_key = ask_key("请输入要删除记录的对应编号：")
            delete_record(main_key)
        elif choice == '0':
            break
if __name__ == "__main__":
    main()
