"""记账本 · 桌面壳

这个文件只干一件事：把窗口，和 main.py 里的函数，接起来。
界面显示什么、长什么样，全在 web/ 里面。
"""
import os
import time

import webview

import main


BASE = os.path.dirname(os.path.abspath(__file__))


class Api:
    """网页能调到的全部东西，都写在类里面。

    网页那边写 pywebview.api.get_balance()，
    实际执行的就是下面这个 get_balance()。
    """

    def get_balance(self):
        return main.get_balance()

    def get_records(self, only=None, limit=None):
        return main.get_records(only, limit)

    def add_record(self, operation_type, money, remark):
        today = time.strftime("%Y-%m-%d", time.localtime())
        main.a_record(operation_type, money, remark, today)

    def get_summary(self, only=None):
        return main.get_summary(only)

    def get_targets(self):
        return main.get_targets()

    def create_target(self, name, money, rate):
        main.create_target(name, money, rate, None)

    def delete_target(self, target_key):
        main.delete_target(target_key)


if __name__ == "__main__":
    webview.create_window(
        "记账本",
        os.path.join(BASE, "web", "index.html"),
        js_api=Api(),
        width=420,
        height=760,
    )
    webview.start()
