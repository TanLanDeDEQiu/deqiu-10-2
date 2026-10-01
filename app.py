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

    def add_record(self, operation_type, money, remark, plan_key=None):
        today = time.strftime("%Y-%m-%d", time.localtime())
        main.a_record(operation_type, money, remark, today, plan_key)

    def get_summary(self, only=None):
        return main.get_summary(only)

    def get_targets(self):
        targets = main.get_targets()
        for t in targets:
            t["picture_data"] = main.read_image(t["target_picture"])
        return targets

    def create_target(self, name, money, rate, picture=None):
        main.create_target(name, money, rate, picture)

    def delete_target(self, target_key):
        main.delete_target(target_key)

    def get_plans(self):
        plans = main.get_plans()
        for p in plans:
            p["picture_data"] = main.read_image(p["plan_picture"])
        return plans

    def create_plan(self, purpose, money, picture=None):
        main.create_plan(purpose, money, picture)

    def delete_plan(self, plan_money_key):
        main.delete_plan(plan_money_key)

    def update_plan(self, plan_money_key, new_money):
        return main.update_plan(plan_money_key, new_money)

    def pick_image(self):
        """弹系统对话框让用户选图；选完复制进 images\\，返回文件名。"""
        paths = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=("图片 (*.png;*.jpg;*.jpeg;*.webp;*.bmp)",),
        )
        if not paths:
            return None              # 用户点了取消
        return main.save_image(paths[0])


if __name__ == "__main__":
    webview.create_window(
        "记账本",
        os.path.join(BASE, "web", "index.html"),
        js_api=Api(),
        width=420,
        height=760,
    )
    webview.start()
