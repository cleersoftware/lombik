function openModal(modalId, data = {}) {
    const modal = document.getElementById(modalId);

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    modal.addEventListener('click', closeOnBackdrop);

    Object.entries(data).forEach(([key, val]) => {

        // fill inputs
        const input = modal.querySelector(`[name="${key}"]`);
        if (input) input.value = val;

        // fill display fields
        const display = modal.querySelector(`[data-field="${key}"]`);
        if (display) display.textContent = val;
    });
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);

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