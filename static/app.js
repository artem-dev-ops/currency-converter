(function() {
    const stored = localStorage.getItem('theme');
    if (stored) document.documentElement.setAttribute('data-theme', stored);
})();

document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    function currentTheme() {
        const attr = document.documentElement.getAttribute('data-theme');
        if (attr) return attr;
        return prefersDark ? 'dark' : 'light';
    }

    function updateToggleIcon() {
        themeToggle.textContent = currentTheme() === 'dark' ? '☀️' : '🌙';
    }
    updateToggleIcon();

    themeToggle.addEventListener('click', function() {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateToggleIcon();
    });

    const arrow = document.querySelector('.arrow-icon');
    const fromSelect = document.querySelector('select[name="from_currency"]');
    const toSelect = document.querySelector('select[name="to_currency"]');
    const form = document.getElementById('convertForm');
    const resultArea = document.getElementById('resultArea');
    const submitBtn = document.getElementById('submitBtn');
    const submitIcon = document.getElementById('submitIcon');
    const submitLabel = document.getElementById('submitLabel');

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function renderResult(payload) {
        resultArea.innerHTML = `
            <div class="result-card">
                <div class="result-label">✅ Текущий результат</div>
                <div class="result-value">
                    <span>${escapeHtml(payload.amount)}</span>
                    <span class="currency-code">${escapeHtml(payload.from_currency)}</span>
                    <span>=</span>
                    <span class="converted-number" id="convertedNumber" title="Нажмите, чтобы скопировать">${escapeHtml(payload.converted)}</span>
                    <span class="currency-code">${escapeHtml(payload.to_currency)}</span>
                </div>
                <div class="rate-line">
                    1 ${escapeHtml(payload.from_currency)} ≈ ${escapeHtml(payload.rate)} ${escapeHtml(payload.to_currency)}
                </div>
                <div class="copy-hint" id="copyHint">Нажмите на сумму, чтобы скопировать</div>
            </div>`;
        attachCopyHandler();
    }

    function renderError(message) {
        resultArea.innerHTML = `<div class="error-message"><span>⚠️</span> ${escapeHtml(message)}</div>`;
    }

    function attachCopyHandler() {
        const el = document.getElementById('convertedNumber');
        const hint = document.getElementById('copyHint');
        if (!el) return;
        el.addEventListener('click', function() {
            navigator.clipboard.writeText(el.textContent.trim()).then(function() {
                if (hint) {
                    const original = hint.textContent;
                    hint.textContent = 'Скопировано ✓';
                    setTimeout(() => { hint.textContent = original; }, 1500);
                }
            }).catch(function() {});
        });
    }
    attachCopyHandler();

    if (form) {
        form.addEventListener('submit', function(e) {
            if (!window.fetch) return; // no-JS/old-browser fallback: real form submit
            e.preventDefault();

            submitBtn.disabled = true;
            submitIcon.classList.add('spin');
            submitLabel.textContent = 'Считаем...';

            const formData = new FormData(form);

            fetch('/api/convert', { method: 'POST', body: formData })
                .then(async function(response) {
                    const data = await response.json();
                    if (!response.ok) {
                        renderError(data.error || 'Не удалось выполнить конвертацию.');
                        return;
                    }
                    renderResult(data);
                })
                .catch(function() {
                    renderError('Ошибка соединения с сервисом курсов валют. Попробуйте позже.');
                })
                .finally(function() {
                    submitBtn.disabled = false;
                    submitIcon.classList.remove('spin');
                    submitLabel.textContent = 'Конвертировать';
                });
        });
    }

    if (arrow && fromSelect && toSelect && form) {
        let isProcessing = false;

        arrow.addEventListener('click', function(e) {
            e.preventDefault();

            if (isProcessing) return;
            isProcessing = true;

            const fromVal = fromSelect.value;
            const toVal = toSelect.value;
            fromSelect.value = toVal;
            toSelect.value = fromVal;

            arrow.style.transition = 'transform 0.2s ease';
            arrow.style.transform = 'rotate(180deg)';

            setTimeout(() => {
                arrow.style.transform = 'rotate(0deg)';
                const amountInput = document.querySelector('input[name="amount"]');
                isProcessing = false;
                if (amountInput && amountInput.value && parseFloat(amountInput.value) > 0) {
                    form.requestSubmit ? form.requestSubmit() : form.submit();
                }
            }, 200);
        });
    }
});
