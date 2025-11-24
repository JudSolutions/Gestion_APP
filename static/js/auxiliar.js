let AUX_SESSION = {
  idRegistroActual: null,
  tipologiaActual: null,
  tareaActual: null,
};

async function api(url, data=null, method="GET") {
  const opts = { method, headers: { "Content-Type":"application/json" } };
  if (data) opts.body = JSON.stringify(data);
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ---- LOGIN ----
async function login() {
  const usuario = document.getElementById("user").value;
  const password = document.getElementById("pass").value;
  try {
    const r = await api("/api/login", {usuario, password}, "POST");
    document.getElementById("loginBox").classList.add("hidden");
    document.getElementById("panelTrabajo").classList.remove("hidden");
    document.getElementById("nombreAux").textContent = r.nombre;
    loadTareas();
  } catch (e) {
    alert("Error de login");
  }
}

// ---- TAREAS ----
async function loadTareas() {
  const tipo = document.getElementById("filtroTipo").value; // ALTA / BAJA / INSERCION
  AUX_SESSION.tipologiaActual = tipo;
  const tareas = await api("/api/tareas_disponibles?tipologia=" + encodeURIComponent(tipo));
  const sel = document.getElementById("selectTarea");
  sel.innerHTML = "";
  tareas.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = `${t.numero_tarea_wm} - ${t.finca} (${t.tipologia_finca})`;
    sel.appendChild(opt);
  });
}

// ---- ACTIVIDADES ----
async function loadActividades() {
  const acts = await api("/api/actividades?tipologia=" + AUX_SESSION.tipologiaActual);
  const sel = document.getElementById("selectActividad");
  sel.innerHTML = "";
  acts.forEach(a => {
    const opt = document.createElement("option");
    opt.value = a.id;
    opt.textContent = `${a.codigo} - ${a.alias_corto} (${a.rendimiento_hora}/h)`;
    sel.appendChild(opt);
  });
}

// ---- INICIAR ACTIVIDAD ----
async function iniciarActividad() {
  const idTarea = document.getElementById("selectTarea").value;
  const idAct = document.getElementById("selectActividad").value;
  if (!idTarea || !idAct) {
    alert("Selecciona tarea y actividad");
    return;
  }
  const r = await api("/api/actividad/inicio", {
    id_tarea_cuadro: parseInt(idTarea),
    id_actividad: parseInt(idAct),
  }, "POST");
  AUX_SESSION.idRegistroActual = r.id_registro;
  alert("Actividad iniciada. Registro #" + r.id_registro);
}

// ---- CERRAR ACTIVIDAD ----
async function cerrarActividad() {
  const cant = parseFloat(prompt("Cantidad ejecutada:"));
  if (isNaN(cant)) return;
  const r = await api("/api/actividad/fin", {
    id_registro: AUX_SESSION.idRegistroActual,
    cantidad: cant
  }, "POST");
  alert("Actividad cerrada. Cumplimiento: " + r.porcentaje.toFixed(1) + "%");
  AUX_SESSION.idRegistroActual = null;
}
