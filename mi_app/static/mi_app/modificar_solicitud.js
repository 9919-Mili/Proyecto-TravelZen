document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("form-modificar");
    const resultado = document.getElementById("resultado");

    // Borra los errores del intento anterior
    function limpiarErrores() {
        formulario.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
        formulario.querySelectorAll(".invalid-feedback").forEach(el => el.textContent = "");
        resultado.className = "";
        resultado.innerHTML = "";
    }

    formulario.addEventListener("submit", async (event) => {
        event.preventDefault();
        limpiarErrores();

        try {
            // Envía el formulario por POST a la misma URL
            const respuesta = await fetch("", { method: "POST", body: new FormData(formulario) });
            const data = await respuesta.json();

            if (data.success) {
                resultado.className = "alert alert-success mt-3";
                resultado.innerText = data.message;

                // Vuelve al dashboard después de 1,5 segundos
                setTimeout(() => { window.location.href = "/dashboard/"; }, 1500);
            } else {
                // Muestra cada error debajo de su campo (en rojo)
                for (const campo in data.errors) {
                    const input = formulario.querySelector(`[name="${campo}"]`);
                    const error = document.getElementById(`error-${campo}`);
                    if (input && error) {
                        input.classList.add("is-invalid");
                        error.textContent = data.errors[campo].join(", ");
                    } else {
                        // Errores generales (que no son de un campo puntual)
                        resultado.className = "alert alert-danger mt-3";
                        resultado.innerHTML += `<p class="mb-1">${data.errors[campo].join(", ")}</p>`;
                    }
                }
            }
        } catch (error) {
            resultado.className = "alert alert-danger mt-3";
            resultado.innerText = "Error de conexión.";
            console.error("Error en la solicitud:", error);
        }
    });
});