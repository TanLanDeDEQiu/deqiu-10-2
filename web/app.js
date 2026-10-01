// pywebview 准备就绪后会广播一个事件。
// 必须等它，不然这个脚本跑的时候，pywebview 还没挂上来。
window.addEventListener("pywebviewready", async () => {
    const balance = await pywebview.api.get_balance();

    document.getElementById("balance").textContent = balance.toFixed(2);
});
