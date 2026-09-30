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


def a_record(operation_type, operation_money, operation_remark, operation_date, plan_money_key=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """INSERT INTO 记录 (operation_type, operation_money, operation_remark, operation_date, plan_money_key)
                VALUES (?, ?, ?, ?, ?)
            """, (operation_type, operation_money, operation_remark, operation_date, plan_money_key))
    conn.commit()
    conn.close()

def all_show():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for a1,a2,a3,a4 in c.execute("""SELECT 
                                    operation_type, operation_money, operation_remark, operation_date FROM 记录 
                                    ORDER BY operation_date DESC"""):
        print(f'==========记录==========\n[类型]:{a1}\n[金额]:{a2}\n[备注]:{a3}\n[日期]:{a4}\n=======================')



def main():
    pre_load()
    while True:
        print('打印菜单：   \n1. 记一笔    \n2. 看全部    \n0. 退出')
        choice = input("请选择：")
        if choice == '1':
            operation_type = input("请输入类型：")
            operation_money = input("请输入金额：")
            operation_remark = input("请输入备注：")
            operation_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            print(f"已添加一条记录。\n[类型]:{operation_type}\n[金额]:{operation_money}\n[备注]:{operation_remark}\n[日期]:{operation_date}")
            a_record(operation_type, operation_money, operation_remark, operation_date)
        elif choice == '2':
            all_show()
        elif choice == '0':
            break
if __name__ == "__main__":
    main()
