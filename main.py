import sqlite3
import time


DB = "记账.db"


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


#记录
def a_record(operation_type, operation_money, operation_remark, operation_date, plan_money_key=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO 记录 (operation_type, operation_money, operation_remark, operation_date, plan_money_key)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_type, operation_money, operation_remark, operation_date, plan_money_key))
    conn.commit()
    conn.close()

def all_show(only=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    sql = """SELECT main_key, operation_type, operation_money, operation_remark, operation_date FROM 记录"""
    args = ()
    where = ""
    if only:
        where += " WHERE operation_type = ?"
        args = (only,)
    count = c.execute("SELECT COUNT(*) FROM 记录" + where, args).fetchone()[0]
    income, expense = get_income_expense()
    if only == '支出':
        income = 0
    elif only == '收入':
        expense = 0
    print(f"总记录（共{count}条）    总收入：{income}     总支出：{expense}")
    sql += where + " ORDER BY operation_date DESC, main_key DESC"
    for a,a1,a2,a3,a4 in c.execute(sql,args):
        print(f'==========记录{a:04d}==========\n[类型]:{a1}\n[金额]:{a2}\n[备注]:{a3}\n[日期]:{a4}\n===========================')
    conn.close()

def show_balance(balance):
    print(f"当前余额：{balance}")


#预算
def create_plan(plan_money_purpose,plan_money,plan_picture):
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


#目标
def create_target(target_name, target_money, target_rate, target_picture):
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
            print(f"已添加一条记录。\n[类型]:{operation_type}\n[金额]:{operation_money}\n[备注]:{operation_remark}\n[日期]:{operation_date}")
            if operation_type == '预算支出':
                all_show_plan()
                plan_money_key = input("挂在哪个预算上（输编号）：")
                operation_type = '支出'  # ⭐ 这一行是关键
            a_record(operation_type, operation_money, operation_remark, operation_date, plan_money_key)
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
                print("\n1.创建新的预算计划    \n2.查看所有的预算    \n3.删除一个预算    \n0.退出")
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
                    plan_money_key = input("请输入要删除预算的对应编号：")
                    delete_plan(plan_money_key)
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
                    create_target(target_name,target_money,target_rate,target_picture)
                elif choice2 == '2':
                    all_show_target()
                elif choice2 == '3':
                    all_show_target()
                    target_key = input("请输入要删除目标的对应编号：")
                    delete_target(target_key)
                elif choice2 == '0':
                    break
        elif choice == '7':
            all_show()
            main_key = input("请输入要删除记录的对应编号：")
            delete_record(main_key)
        elif choice == '0':
            break
if __name__ == "__main__":
    main()
