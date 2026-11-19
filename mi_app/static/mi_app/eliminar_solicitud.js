let solicitudIdAEliminar = null;

document.addEventListener("DOMContentLoaded", () => {
    const eliminarBtns = document.querySelectorAll(".eliminar-btn");
    const modal = new bootstrap.Modal(document.getElementById("confirmarEliminarModal"));
    const confirmarBtn = document.getElementById("confirmarEliminarBtn");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    // 1. Al tocar "Eliminar" en una fila: guardar el id y abrir el modal
    eliminarBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            solicitudIdAEliminar = btn.getAttribute("data-id");
            modal.show();
        });
    });

    // 2. Al confirmar en el modal: pedirle al servidor que borre
    confirmarBtn.addEventListener("click", () => {
        if (!solicitudIdAEliminar) return;

        fetch(`/eliminarSolicitud/${solicitudIdAEliminar}/`, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 3. Sacar la fila de la tabla sin recargar la página
                const fila = document.getElementById(`solicitud-${solicitudIdAEliminar}`);
                if (fila) fila.remove();
            }
            modal.hide();
        })
        .catch(error => {
            console.error("Error al eliminar:", error);
            modal.hide();
        });
    });
});