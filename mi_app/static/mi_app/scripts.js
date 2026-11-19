const form = document.getElementById("form-paquete");
const pasos = document.querySelectorAll(".paso");
const numeros = document.querySelectorAll(".paso-num");
let pasoActual = 1;

// ===== Navegación entre pasos =====
function mostrarPaso(n, hacerScroll = true) {
  pasoActual = n;
  pasos.forEach(p => {
    p.hidden = Number(p.dataset.paso) !== n;
  });
  numeros.forEach(num => {
    const n2 = Number(num.dataset.pasoNum);
    num.classList.toggle("activo", n2 === n);
    num.classList.toggle("completo", n2 < n);
  });
  if (hacerScroll) {
    document.querySelector(".stepper").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// ===== Errores de validación =====
function limpiarErrores() {
  document.querySelectorAll(".error").forEach(p => p.textContent = "");
  document.querySelectorAll(".con-error").forEach(el => el.classList.remove("con-error"));
}

function mostrarErrores(errores) {
  limpiarErrores();
  for (const campo in errores) {
    const p = document.querySelector(`[data-error="${campo}"]`);
    if (p) p.textContent = errores[campo].join(" ");
    document.querySelectorAll(`[name="${campo}"]`).forEach(el => el.classList.add("con-error"));
  }
  // Llevar la pantalla al primer error visible, para que el usuario no tenga que buscarlo
  const primerError = [...document.querySelectorAll(".paso:not([hidden]) .error")]
    .find(p => p.textContent);
  if (primerError) primerError.scrollIntoView({ behavior: "smooth", block: "center" });
}

document.querySelectorAll("[data-anterior]").forEach(btn => {
  btn.addEventListener("click", () => mostrarPaso(pasoActual - 1));
});

// ===== Formato de importes =====
function money(n) {
  return "$" + Number(n).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function usd(n) {
  return "US$ " + Number(n).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fila(etiqueta, valor, clase = "") {
  return `<div class="fila-resumen ${clase}"><span>${etiqueta}</span><span>${valor}</span></div>`;
}

// Calcula qué porcentaje del subtotal, representa un descuento
function porcentaje(parte, total) {
  return Math.round((parte / total) * 100);
}

// ===== Resumen del paquete (ARS y USD) =====
function renderResumen(r) {
  const c = r.costos;

  function renderResumen(r, dolar) {
    const c = r.costos;

    // Muestra el importe en pesos y, debajo, en dólares
    function conUsd(n) {
      if (!dolar) return money(n);
      return `${money(n)}<small class="valor-usd">${usd(n / dolar.venta)}</small>`;
    }

    let descuentos = "";
    if (c.descuento_noches > 0)
      descuentos += fila(`Descuento por noches (${porcentaje(c.descuento_noches, c.subtotal)}%)`, "- " + conUsd(c.descuento_noches), "descuento");
    if (c.descuento_viajeros > 0)
      descuentos += fila(`Descuento por viajeros (${porcentaje(c.descuento_viajeros, c.subtotal)}%)`, "- " + conUsd(c.descuento_viajeros), "descuento");
    if (c.descuento_anticipacion > 0)
      descuentos += fila(`Descuento por anticipación (${porcentaje(c.descuento_anticipacion, c.subtotal)}%)`, "- " + conUsd(c.descuento_anticipacion), "descuento");

    document.getElementById("resumen").innerHTML = `
    <div class="resumen-grid">

      <div class="card-resumen card-paquete">
        <h3>Tu paquete</h3>
        ${fila("Responsable", r.nombre)}
        ${fila("Email", r.email)}
        ${fila("Destino", r.destino)}
        ${fila("Fechas", `${r.fecha_inicio} - ${r.fecha_fin}`)}
        ${fila("Viajeros", `${r.adultos} adulto(s), ${r.ninios} niño(s)`)}
        ${fila("Vuelo", r.tipo_vuelo)}
        ${fila("Alojamiento", r.alojamiento)}
        ${fila("Régimen de comidas", r.regimen)}
        ${fila("Equipaje", r.equipaje)}
        ${fila("Anticipación de la reserva", `${r.dias_anticipacion} días`)}
      </div>

      <div class="card-resumen card-costos">
        <h3>Detalle de costos</h3>
        ${fila("Vuelo", conUsd(c.costo_vuelo))}
        ${fila(`Alojamiento (${c.noches} noches)`, conUsd(c.costo_alojamiento))}
        ${fila("Comidas", conUsd(c.costo_comidas))}
        ${fila("Equipaje", conUsd(c.costo_equipaje))}
        <hr>
        ${fila("Subtotal", conUsd(c.subtotal), "subtotal")}
        ${descuentos}
        ${fila("Total", conUsd(c.total), "total")}
        ${dolar
        ? `<p class="nota-dolar">Dólar oficial (venta): ${money(dolar.venta)} · Actualizado: ${new Date(dolar.fecha).toLocaleString("es-AR")}</p>`
        : `<p class="nota-dolar">No pudimos obtener la cotización del dólar. Los valores se muestran solo en pesos.</p>`}
      </div>

    </div>`;
  }


// ===== Cotización del dólar (vista DRF /api/dolar/) =====
  async function obtenerDolar() {
    try {
      const resp = await fetch("/api/dolar/");
      if (!resp.ok) return null;      // la API respondió con error (ej.: 503)
      return await resp.json();       // { compra, venta, fecha }
    } catch (error) {
      return null;                    // sin conexión con el servidor
    }
  }

// ===== Comunicación con el servidor (Django) =====
  async function llamarBackend(url, extra = {}) {
    const datos = new FormData(form);
    for (const clave in extra) datos.append(clave, extra[clave]);
    const resp = await fetch(url, {method: "POST", body: datos});
    return await resp.json();
  }

  async function validarPaso(n) {
    const data = await llamarBackend("/validar-paso/", {paso: n});
    if (!data.ok) {
      mostrarErrores(data.errores);
      return false;
    }
    limpiarErrores();
    return true;
  }

  document.querySelectorAll("[data-siguiente]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (await validarPaso(pasoActual)) mostrarPaso(pasoActual + 1);
    });
  });

  document.getElementById("btn-ver-resumen").addEventListener("click", async () => {
    if (!(await validarPaso(4))) return;
    const data = await llamarBackend("/calcular/");
    if (!data.ok) {
      mostrarErrores(data.errores);
      return;
    }
    limpiarErrores();
    const dolar = await obtenerDolar();
    renderResumen(data.resumen, dolar);
    mostrarPaso(5);
  });

  document.getElementById("btn-editar").addEventListener("click", () => mostrarPaso(1));

// ===== Cartel de confirmación de envío =====
  const modalEnvio = document.getElementById("modal-envio");

  function mostrarModalEnvio(titulo, texto, esAviso = false) {
    if (!modalEnvio) return;
    const icono = document.getElementById("modal-envio-icono");
    icono.textContent = esAviso ? "!" : "✓";
    icono.classList.toggle("aviso", esAviso);   // naranja si es aviso
    document.getElementById("modal-envio-titulo").textContent = titulo;
    document.getElementById("modal-envio-texto").textContent = texto;
    modalEnvio.hidden = false;                    // muestra el cartel
    document.getElementById("modal-envio-cerrar").focus();
  }

  function cerrarModalEnvio() {
    modalEnvio.hidden = true;
  }

// Se cierra con el botón ACEPTAR, tocando afuera del cartel o con la tecla ESC.
// El "if" evita que se rompa el resto del script si el cartel no está en el HTML.
  if (modalEnvio) {
    document.getElementById("modal-envio-cerrar").addEventListener("click", cerrarModalEnvio);
    modalEnvio.addEventListener("click", (e) => {
      if (e.target === modalEnvio) cerrarModalEnvio();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modalEnvio.hidden) cerrarModalEnvio();
    });
  }

// ===== Botón ENVIAR =====
  document.getElementById("btn-enviar").addEventListener("click", async () => {
    const btn = document.getElementById("btn-enviar");
    btn.disabled = true;
    btn.textContent = "Enviando...";
    limpiarErrores();  // borra mensajes de intentos anteriores

    // Devuelve el botón a su estado normal para poder reintentar
    function restaurarBoton() {
      btn.disabled = false;
      btn.textContent = "ENVIAR";
    }

    let data;
    try {
      data = await llamarBackend("/enviar/");
    } catch (error) {
      // Sin conexión, servidor apagado o respuesta inválida (por ejemplo, error 500)
      console.error("Error al enviar la solicitud:", error);
      mostrarErrores({
        __all__: ["No pudimos conectarnos con el servidor. Revisá tu conexión e intentá nuevamente"],
      });
      restaurarBoton();
      return;
    }

    // El servidor respondió, pero con errores de validación
    if (!data.ok) {
      mostrarErrores(data.errores);
      restaurarBoton();
      return;
    }

    // Éxito. Si el mail falló, el servidor manda un aviso
    limpiarErrores();
    const mensaje = data.aviso || "¡Listo! Te enviamos la reserva por email.";
    const color = data.aviso ? "#b26a00" : "green";
    document.getElementById("resumen").innerHTML =
        `<p style="color:${color}; font-weight:600;">${mensaje}</p>`;
    btn.hidden = true;
    document.getElementById("btn-editar").hidden = true;
    mostrarModalEnvio(data.aviso ? "REGISTRADO" : "ENVIADO", mensaje, Boolean(data.aviso));
  });

// ===== Botones + y −  =====
  document.querySelectorAll("[data-sumar]").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.sumar);
      input.value = (parseInt(input.value) || 0) + 1;
    });
  });

  document.querySelectorAll("[data-restar]").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.restar);
      const min = parseInt(input.min) || 0;
      input.value = Math.max(min, (parseInt(input.value) || 0) - 1);
    });
  });

  mostrarPaso(1, false);
}