// pywebview 准备就绪后会广播一个事件。
// 必须等它，不然脚本跑的时候 pywebview 还没挂上来。
window.addEventListener("pywebviewready", async () => {
    setupTabs();
    setupSheet();
    setupAllPage();
    setupTargetPage();
    setupPlanPage();
    await refresh();
});


// 底部三个格子：点谁，就显示谁那一页
function setupTabs() {
    const tabs = document.querySelectorAll(".tab");
    const pages = document.querySelectorAll(".page");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => t.classList.remove("active"));
            pages.forEach((p) => p.classList.remove("show"));

            tab.classList.add("active");
            document.getElementById("page-" + tab.dataset.page).classList.add("show");
        });
    });
}


// 把界面重画一遍。数据全问 Python 要，网页自己不算账。
async function refresh() {
    const balance = await pywebview.api.get_balance();
    document.getElementById("balance").textContent = balance.toFixed(2);
    // 余额变负，整张卡翻红
    document.querySelector(".balance-card").classList.toggle("minus", balance < 0);

    const rows = await pywebview.api.get_records(null, 5);
    renderList("records", rows, rowCard, "还没有记录<br>点右下角那个「记」");

    const targets = await pywebview.api.get_targets();
    renderList("targets", targets, targetCard, "还没有目标<br>点右上角「创建新的」");

    const plans = await pywebview.api.get_plans();
    renderList("plans", plans, planCard, "还没有预算<br>记一笔的时候可以挂上去");
}


// 把一批东西画进某个容器。空了就说一句人话，别留一片白。
function renderList(boxId, items, cardFn, emptyText) {
    const box = document.getElementById(boxId);
    if (items.length === 0) {
        box.innerHTML = `<div class="empty">${emptyText}</div>`;
        return;
    }
    box.innerHTML = items.map(cardFn).join("");
}


// 一条记录 → 一张卡片
function rowCard(record) {
    const isIncome = record.operation_type === "收入";
    const side = isIncome ? "in" : "out";
    const sign = isIncome ? "+" : "−";

    return `
        <div class="row">
            <div class="row-top">
                <span class="type">${record.operation_type}</span>
                <span class="money ${side}">${sign}${record.operation_money.toFixed(2)}</span>
            </div>
            <div class="remark">${record.operation_remark ?? ""}</div>
        </div>
    `;
}


// 一条目标 → 一张卡片
function targetCard(target) {
    const pct = Math.min(target.progress, 100);   // 进度条最多画满
    const pic = target.picture_data
        ? `<img class="card-pic" src="${target.picture_data}" alt="">`
        : "";

    const cls = target.picture_data ? "tcard has-pic" : "tcard";

    return `
        <div class="${cls}">
            <div class="tcard-bg"></div>
            ${pic}
            <button class="tcard-del" data-key="${target.target_key}">×</button>
            <div class="tcard-body">
                <div class="tcard-name">${target.target_name}</div>
                <div class="tcard-sub">目标 ${target.target_money.toFixed(0)} 元 · 占比 ${(target.target_rate * 100).toFixed(0)}%</div>
                <div class="bar"><i style="width: ${pct}%"></i></div>
                <div class="tcard-pct">进度 ${target.progress.toFixed(2)}%</div>
            </div>
        </div>
    `;
}


// ---- 目标的 创建 / 删除 ----

// 表单里选好的图是哪一张（没选就是 null）
let pickedTargetPic = null;
let pickedPlanPic = null;

function setupTargetPage() {
    const mask = document.getElementById("target-sheet");

    document.getElementById("btn-new-target").addEventListener("click", () => {
        document.getElementById("t-name").value = "";
        document.getElementById("t-money").value = "";
        document.getElementById("t-rate").value = "";
        document.getElementById("t-err").textContent = "";
        pickedTargetPic = null;
        document.getElementById("t-picked").textContent = "";
        mask.classList.add("show");
        document.getElementById("t-name").focus();
    });

    document.getElementById("t-pick").addEventListener("click", async () => {
        const name = await pywebview.api.pick_image();
        if (!name) return;                       // 用户点了取消
        pickedTargetPic = name;
        document.getElementById("t-picked").textContent = name;
    });

    document.getElementById("btn-close-target").addEventListener("click", () => {
        mask.classList.remove("show");
    });

    mask.addEventListener("click", (e) => {
        if (e.target === mask) mask.classList.remove("show");
    });

    document.getElementById("btn-save-target").addEventListener("click", saveTarget);

    // 「删除一个」：点一下，卡片上浮出小叉；再点一下收回去
    document.getElementById("btn-del-target").addEventListener("click", () => {
        document.getElementById("targets").classList.toggle("deleting");
    });

    // 小叉是动态生成的，所以用"代理"接：点在容器上，看点是哪个
    document.getElementById("targets").addEventListener("click", async (e) => {
        const btn = e.target.closest(".tcard-del");
        if (!btn) return;
        await pywebview.api.delete_target(Number(btn.dataset.key));
        await refresh();
    });
}


async function saveTarget() {
    const name = document.getElementById("t-name").value;
    const money = document.getElementById("t-money").value;
    const rate = document.getElementById("t-rate").value;
    const errBox = document.getElementById("t-err");

    if (name === "") { errBox.textContent = "目标名字还没写"; return; }
    if (money === "") { errBox.textContent = "金额还没填"; return; }
    if (rate === "") { errBox.textContent = "占比还没填"; return; }

    try {
        await pywebview.api.create_target(name, money, rate, pickedTargetPic);
    } catch (e) {
        errBox.textContent = String(e);
        return;
    }

    document.getElementById("target-sheet").classList.remove("show");
    await refresh();
}


// 一条预算 → 一张卡片
function planCard(plan) {
    const height = Math.max(0, Math.min(plan.left_pct, 100));
    const over = plan.left < 0;        // 花超了
    const pic = plan.picture_data
        ? `<img class="card-pic" src="${plan.picture_data}" alt="">`
        : "";

    const cls = plan.picture_data ? "pcard has-pic" : "pcard";

    return `
        <div class="${cls}" data-key="${plan.plan_money_key}">
            <div class="pcard-bg"></div>
            ${pic}
            <button class="pcard-del" data-key="${plan.plan_money_key}">×</button>
            <div class="pcard-body">
                <div class="pcard-info">
                    <div class="pcard-name">${plan.plan_money_purpose}</div>
                    <div class="pcard-line">预算　　${plan.plan_money.toFixed(2)}</div>
                    <div class="pcard-line">已支出　${plan.used.toFixed(2)}</div>
                    <div class="pcard-line">剩余　　${plan.left.toFixed(2)}</div>
                </div>
                <div class="pcard-side">
                    <div class="vbar"><i style="height: ${height}%"></i></div>
                    <div class="pcard-pct">${over ? "超支" : plan.left_pct.toFixed(0) + "%"}</div>
                </div>
            </div>
        </div>
    `;
}


// ---- 预算的 创建 / 删除 ----

function setupPlanPage() {
    const mask = document.getElementById("plan-sheet");

    document.getElementById("btn-new-plan").addEventListener("click", () => {
        document.getElementById("p-purpose").value = "";
        document.getElementById("p-money").value = "";
        document.getElementById("p-err").textContent = "";
        pickedPlanPic = null;
        document.getElementById("p-picked").textContent = "";
        mask.classList.add("show");
        document.getElementById("p-purpose").focus();
    });

    document.getElementById("p-pick").addEventListener("click", async () => {
        const name = await pywebview.api.pick_image();
        if (!name) return;
        pickedPlanPic = name;
        document.getElementById("p-picked").textContent = name;
    });

    document.getElementById("btn-close-plan").addEventListener("click", () => {
        mask.classList.remove("show");
    });

    mask.addEventListener("click", (e) => {
        if (e.target === mask) mask.classList.remove("show");
    });

    document.getElementById("btn-save-plan").addEventListener("click", savePlan);

    document.getElementById("btn-del-plan").addEventListener("click", () => {
        document.getElementById("plans").classList.toggle("deleting");
    });

    document.getElementById("plans").addEventListener("click", async (e) => {
        const btn = e.target.closest(".pcard-del");
        if (btn) {
            await pywebview.api.delete_plan(Number(btn.dataset.key));
            await refresh();
            return;
        }

        // 点卡片本身 → 加预算
        const card = e.target.closest(".pcard");
        if (card) openPlanEdit(card);
    });

    const editMask = document.getElementById("plan-edit-sheet");
    document.getElementById("btn-close-pedit").addEventListener("click", () => {
        editMask.classList.remove("show");
    });
    editMask.addEventListener("click", (e) => {
        if (e.target === editMask) editMask.classList.remove("show");
    });
    document.getElementById("btn-save-pedit").addEventListener("click", savePlanEdit);
}


// 现在正在改哪一条预算
let editingPlanKey = null;

function openPlanEdit(card) {
    const key = Number(card.dataset.key);
    const name = card.querySelector(".pcard-name").textContent;
    const now = card.querySelectorAll(".pcard-line")[0].textContent.replace(/[^\d.]/g, "");

    editingPlanKey = key;
    document.getElementById("pe-title").textContent = `加预算 · ${name}`;
    document.getElementById("pe-money").value = now;
    document.getElementById("pe-err").textContent = "";
    document.getElementById("plan-edit-sheet").classList.add("show");
    document.getElementById("pe-money").focus();
}


async function savePlanEdit() {
    const money = document.getElementById("pe-money").value;
    const errBox = document.getElementById("pe-err");

    if (money === "") { errBox.textContent = "还没填金额"; return; }

    try {
        const changed = await pywebview.api.update_plan(editingPlanKey, money);
        if (changed === 0) {
            errBox.textContent = "没找到这条预算，可能已经被删了";
            return;
        }
    } catch (e) {
        errBox.textContent = String(e);
        return;
    }

    document.getElementById("plan-edit-sheet").classList.remove("show");
    await refresh();
}


async function savePlan() {
    const purpose = document.getElementById("p-purpose").value;
    const money = document.getElementById("p-money").value;
    const errBox = document.getElementById("p-err");

    if (purpose === "") { errBox.textContent = "预算目的还没写"; return; }
    if (money === "") { errBox.textContent = "预算金额还没填"; return; }

    try {
        await pywebview.api.create_plan(purpose, money, pickedPlanPic);
    } catch (e) {
        errBox.textContent = String(e);
        return;
    }

    document.getElementById("plan-sheet").classList.remove("show");
    await refresh();
}


// ---- 记一笔 ----

function setupSheet() {
    const mask = document.getElementById("sheet-mask");

    document.getElementById("btn-add").addEventListener("click", openSheet);
    document.getElementById("btn-close").addEventListener("click", closeSheet);
    document.getElementById("btn-save").addEventListener("click", saveRecord);

    // 点背景（弹窗外面的暗色）也能关掉
    mask.addEventListener("click", (e) => {
        if (e.target === mask) closeSheet();
    });

    // 类型那两个药丸：点谁谁亮
    document.querySelectorAll("#seg-type .seg-item").forEach((item) => {
        item.addEventListener("click", () => {
            document.querySelectorAll("#seg-type .seg-item")
                    .forEach((x) => x.classList.remove("active"));
            item.classList.add("active");
            pickPlanIfNeeded();
        });
    });
}


function openSheet() {
    document.getElementById("in-money").value = "";
    document.getElementById("in-remark").value = "";
    document.getElementById("err").textContent = "";
    document.getElementById("sheet-mask").classList.add("show");
    document.getElementById("in-money").focus();
    pickPlanIfNeeded();
}


// 选了「预算支出」才把预算下拉露出来，并且把选项装满
async function pickPlanIfNeeded() {
    const type = document.querySelector("#seg-type .seg-item.active").dataset.type;
    const box = document.getElementById("plan-pick");

    if (type !== "预算支出") {
        box.style.display = "none";
        return;
    }

    box.style.display = "block";
    const plans = await pywebview.api.get_plans();
    document.getElementById("in-plan").innerHTML = plans
        .map((p) => `<option value="${p.plan_money_key}">${p.plan_money_purpose}（剩 ${p.left.toFixed(0)}）</option>`)
        .join("");
}


function closeSheet() {
    document.getElementById("sheet-mask").classList.remove("show");
}


async function saveRecord() {
    const type = document.querySelector("#seg-type .seg-item.active").dataset.type;
    const money = document.getElementById("in-money").value;
    const remark = document.getElementById("in-remark").value;
    const errBox = document.getElementById("err");

    if (money === "") {
        errBox.textContent = "金额还没填";
        return;
    }

    let planKey = null;
    if (type === "预算支出") {
        planKey = Number(document.getElementById("in-plan").value);
        if (!planKey) {
            errBox.textContent = "还没有预算可以挂，先去预算页建一条";
            return;
        }
    }

    try {
        await pywebview.api.add_record(type, money, remark, planKey);
    } catch (e) {
        // 后端校验没过（比如金额不是数字），它会把原因抛回来
        errBox.textContent = String(e);
        return;
    }

    closeSheet();
    await refresh();
}


// ---- 总记录页 ----

let onlyFilter = "";        // "" = 全部，"收入" / "支出" = 只看那一类

function setupAllPage() {
    document.getElementById("btn-all").addEventListener("click", () => {
        showPage("all");
        refreshAll();
    });

    document.getElementById("btn-back").addEventListener("click", () => {
        showPage("home");
        markTab("home");
    });

    document.getElementById("btn-filter").addEventListener("click", () => {
        document.getElementById("filter-panel").classList.toggle("show");
    });

    document.querySelectorAll("#filter-panel .opt").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#filter-panel .opt")
                    .forEach((x) => x.classList.remove("active"));
            btn.classList.add("active");
            onlyFilter = btn.dataset.only;
            refreshAll();
        });
    });
}


function showPage(name) {
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("show"));
    document.getElementById("page-" + name).classList.add("show");
}


function markTab(name) {
    document.querySelectorAll(".tab").forEach((t) => {
        t.classList.toggle("active", t.dataset.page === name);
    });
}


async function refreshAll() {
    const only = onlyFilter || null;

    const s = await pywebview.api.get_summary(only);
    document.getElementById("all-count").textContent = s.count;
    document.getElementById("all-income").textContent = s.income.toFixed(0);
    document.getElementById("all-expense").textContent = s.expense.toFixed(0);

    const rows = await pywebview.api.get_records(only);
    document.getElementById("all-records").innerHTML = rows.map(rowCard).join("");
}
