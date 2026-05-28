/* ============================
   TaskMaster — Main JavaScript
   (.complete-btn для страницы списка задач /tasks/)
   .task-checkbox обрабатывается в base.html
   ============================ */

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.complete-btn').forEach(btn => {
        btn.addEventListener('click', async function () {
            const taskId = this.dataset.taskId;
            if (!taskId) return;

            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" style="width:14px;height:14px;"></span>';

            const card = document.getElementById(`task-${taskId}`) || this.closest('.task-card');
            const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

            try {
                const resp = await fetch(`/tasks/${taskId}/complete/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await resp.json();

                if (data.status === 'ok') {
                    if (card) {
                        card.style.transition = 'opacity .4s';
                        card.style.opacity = '0';
                        setTimeout(() => card.remove(), 400);
                    }
                    // Навбар обновляется через base.html, но если хотим и здесь:
                    document.querySelectorAll('.nav-coins').forEach(el => el.textContent = data.new_coins);
                    document.querySelectorAll('.nav-streak').forEach(el => el.textContent = data.new_streak);
                    const xpFill = document.querySelector('.xp-bar-fill');
                    if (xpFill) xpFill.style.width = data.xp_percent + '%';
                } else {
                    this.disabled = false;
                    this.innerHTML = '<i class="bi bi-check2"></i>';
                }
            } catch (err) {
                console.error(err);
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-check2"></i>';
            }
        });
    });
});