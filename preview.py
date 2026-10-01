"""把界面渲染成一张图 —— 不用开窗口，也不碰屏幕。

用法：  python preview.py            → 主页
        python preview.py sheet      → 把「记一笔」弹窗也打开
出图：  preview.png / preview-sheet.png（就在这个文件夹里）

原理：临时造一个 _preview.html，把 Python 那边的接口 mock 成假数据，
      丢给「无头 Edge」截图，截完把临时文件删掉。
"""
import pathlib
import subprocess
import sys

BASE = pathlib.Path(__file__).parent
WEB = BASE / "web"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 假数据，只为了看界面长相
MOCK = """
<script>
window.pywebview = { api: {
    get_balance: async () => 4300.0,
    get_records: async () => [
        {main_key: 4, operation_type: "支出", operation_money: 200.0, operation_remark: "午饭", operation_date: "2026-10-01"},
        {main_key: 2, operation_type: "收入", operation_money: 500.0, operation_remark: "零花钱", operation_date: "2026-09-30"},
        {main_key: 1, operation_type: "支出", operation_money: 128.5, operation_remark: "话费充值", operation_date: "2026-09-28"},
    ],
    add_record: async () => null,
    get_summary: async (only) => {
        if (only === "收入") return {count: 1, income: 500.0, expense: 0};
        if (only === "支出") return {count: 2, income: 0, expense: 328.5};
        return {count: 3, income: 500.0, expense: 328.5};
    },
    get_targets: async () => [
        {target_key: 1, target_name: "买电脑", target_money: 30000.0, target_rate: 0.3, target_picture: null, need: 100000.0, progress: 4.3},
        {target_key: 2, target_name: "相机", target_money: 8000.0, target_rate: 0.5, target_picture: null, need: 16000.0, progress: 26.88},
    ],
    create_target: async () => null,
    delete_target: async () => null,
    get_plans: async () => [
        {plan_money_key: 1, plan_money_purpose: "伙食费", plan_money: 2000.0, plan_picture: null, used: 200.0, left: 1800.0, left_pct: 90.0},
        {plan_money_key: 2, plan_money_purpose: "话费", plan_money: 100.0, plan_picture: null, used: 0, left: 100.0, left_pct: 100.0},
        {plan_money_key: 3, plan_money_purpose: "买书", plan_money: 300.0, plan_picture: null, used: 380.0, left: -80.0, left_pct: -26.67},
    ],
    create_plan: async () => null,
    delete_plan: async () => null,
    update_plan: async () => 1,
}};
window.dispatchEvent(new Event("pywebviewready"));
setTimeout(() => {
    if (location.hash === "#sheet") document.getElementById("btn-add").click();
    if (location.hash === "#bs") {
        document.getElementById("btn-add").click();
        setTimeout(() => {
            document.querySelector("#seg-type [data-type=\\'\\u9884\\u7b97\\u652f\\u51fa\\']").click();
        }, 200);
    }
    if (location.hash === "#all") { markTab("home"); showPage("all"); refreshAll(); }
    if (location.hash === "#target") { markTab("target"); showPage("target"); }
    if (location.hash === "#tnew") {
        markTab("target"); showPage("target");
        document.getElementById("btn-new-target").click();
    }
    if (location.hash === "#tdel") {
        markTab("target"); showPage("target");
        document.getElementById("btn-del-target").click();
    }
    if (location.hash === "#plan") { markTab("plan"); showPage("plan"); }
    if (location.hash === "#pnew") {
        markTab("plan"); showPage("plan");
        document.getElementById("btn-new-plan").click();
    }
    if (location.hash === "#pdel") {
        markTab("plan"); showPage("plan");
        document.getElementById("btn-del-plan").click();
    }
    if (location.hash === "#pedit") {
        markTab("plan"); showPage("plan");
        document.querySelector("#plans .pcard").click();
    }
}, 150);
</script>
"""


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    html = (WEB / "index.html").read_text(encoding="utf-8")
    html = html.replace('<script src="app.js"></script>',
                        '<script src="app.js"></script>' + MOCK)

    preview = WEB / "_preview.html"
    preview.write_text(html, encoding="utf-8")

    out = BASE / (f"preview-{mode}.png" if mode else "preview.png")
    url = preview.as_uri() + (f"#{mode}" if mode else "")
    subprocess.run([
        EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={out}", "--window-size=520,820",
        "--virtual-time-budget=4000", url,
    ], check=True, capture_output=True)

    preview.unlink()
    print("出图:", out)


if __name__ == "__main__":
    main()
