document.body.addEventListener('htmx:configRequest', function (event) {
    event.detail.headers['X-CSRFToken'] =
        document.querySelector('meta[name="csrf-token"]').content;
});