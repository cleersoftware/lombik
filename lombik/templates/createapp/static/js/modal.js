function openModal(modalId, data) {
    data = data || {};
    var modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.addEventListener('click', closeOnBackdrop);

    Object.entries(data).forEach(function (pair) {
        var key = pair[0];
        var value = pair[1];

        var input = modal.querySelector('[name="' + key + '"]');
        if (input) input.value = value;

        var display = modal.querySelector('[data-field="' + key + '"]');
        if (display) display.textContent = value;
    });
}

function closeModal(modalId) {
    var modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.removeEventListener('click', closeOnBackdrop);
}

function closeOnBackdrop(e) {
    if (e.target === e.currentTarget) {
        e.currentTarget.classList.add('hidden');
        e.currentTarget.classList.remove('flex');
        e.currentTarget.removeEventListener('click', closeOnBackdrop);
    }
}
