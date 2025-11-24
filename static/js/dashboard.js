async function loadCards() {
  const res = await fetch("/api/dashboard_cards");
  const data = await res.json();
  document.getElementById("card-proximas").textContent = data.proximas_vencer;
  document.getElementById("card-proceso").textContent = data.en_proceso;
  document.getElementById("card-finalizadas").textContent = data.finalizadas_hoy;
  document.getElementById("card-auxiliares").textContent = data.auxiliares_activos;
}

async function loadPie() {
  const res = await fetch("/api/chart_tipologia");
  const data = await res.json();
  const ctx = document.getElementById("pieTipologia");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: data.labels,
      datasets: [{
        data: data.data,
        backgroundColor: ["#2563eb", "#3b82f6", "#93c5fd", "#cbd5e1"]
      }]
    },
    options: { plugins: { legend: { position: "bottom" } } }
  });
}

async function loadBar() {
  const res = await fetch("/api/chart_carga_auxiliar");
  const data = await res.json();
  const ctx = document.getElementById("barCarga");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [{
        label: "Cantidad ejecutada",
        data: data.data,
        backgroundColor: "#3b82f6"
      }]
    },
    options: { scales: { y: { beginAtZero: true } } }
  });
}

async function loadCriticas() {
  const res = await fetch("/api/tareas_criticas");
  const data = await res.json();
  const cont = document.getElementById("criticas");
  cont.innerHTML = "";

  data.forEach(t => {
    const color =
      t.estado === "vencida" ? "bg-red-600" :
      t.estado === "proxima" ? "bg-yellow-500" :
      "bg-green-500";

    const row = document.createElement("div");
    row.className = "flex items-center justify-between p-3 rounded-xl border hover:bg-slate-50";

    row.innerHTML = `
  <div class="w-16 text-slate-500">${t.id ?? "—"}</div>
  <div class="flex-1 font-medium">${t.actividad ? t.actividad : "—"}</div>
  <div class="w-20 text-slate-500">${t.fecha ? t.fecha : "—"}</div>

  <div class="w-48">
      <div class="h-2 bg-slate-200 rounded">
        <div class="h-2 rounded bg-blue-600" style="width:${t.porcentaje ?? 0}%"></div>
      </div>
  </div>

  <div class="w-12 text-right">
      ${(t.porcentaje ?? 0).toFixed(0)}%
  </div>

  <button class="ml-4 px-3 py-1 bg-blue-600 text-white rounded-xl">
      Abrir
  </button>
`;

    cont.appendChild(row);
  });
}

loadCards();
loadPie();
loadBar();
loadCriticas();

// Modal simple para mostrar los auxiliares activos
function createModal() {
  const modal = document.createElement("div");
  modal.id = "modalAuxiliares";
  modal.className = "fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center hidden z-50";
  modal.innerHTML = `
    <div class="bg-white rounded-2xl shadow-xl p-6 w-96 max-h-[80vh] overflow-y-auto relative">
      <h3 class="text-lg font-semibold text-blue-700 mb-4">Auxiliares activos (últimos 7 días)</h3>
      <div id="listaAuxiliares" class="space-y-2 text-slate-700"></div>
      <div class="text-right mt-4">
        <button id="cerrarModal" class="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700">Cerrar</button>
      </div>
    </div>

    <!-- Submodal para tareas -->
    <div id="modalTareas" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden z-50">
      <div class="bg-white rounded-2xl shadow-xl p-6 w-[600px] max-h-[80vh] overflow-y-auto">
        <h3 id="tituloTareas" class="text-lg font-semibold text-blue-700 mb-4">Tareas de auxiliar</h3>
        <div id="listaTareas" class="divide-y"></div>
        <div class="text-right mt-4">
          <button id="cerrarTareas" class="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700">Volver</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  document.getElementById("cerrarModal").onclick = () => modal.classList.add("hidden");
  document.getElementById("cerrarTareas").onclick = () => {
    document.getElementById("modalTareas").classList.add("hidden");
  };
}


async function showAuxiliaresActivos() {
  const modal = document.getElementById("modalAuxiliares");
  const lista = document.getElementById("listaAuxiliares");
  lista.innerHTML = `<p class="text-sm text-slate-400">Cargando...</p>`;
  modal.classList.remove("hidden");

  const res = await fetch("/api/auxiliares_activos");
  const data = await res.json();

  if (data.length === 0) {
    lista.innerHTML = `<p class="text-slate-500">No hay auxiliares activos en los últimos días.</p>`;
    return;
  }

  lista.innerHTML = "";
  data.forEach(a => {
    const row = document.createElement("div");
    row.className = "flex justify-between items-center p-2 border rounded-lg hover:bg-blue-50 cursor-pointer";
    row.innerHTML = `
      <span class="font-medium">${a.auxiliar}</span>
      <span class="text-blue-600 font-semibold">${a.total}</span>
    `;
    row.onclick = () => showTareasAuxiliar(a.auxiliar);
    lista.appendChild(row);
  });
}

// Mostrar las tareas del auxiliar seleccionado
async function showTareasAuxiliar(nombre) {
  const submodal = document.getElementById("modalTareas");
  const lista = document.getElementById("listaTareas");
  const titulo = document.getElementById("tituloTareas");

  titulo.textContent = `Tareas de ${nombre}`;
  lista.innerHTML = `<p class="text-sm text-slate-400">Cargando...</p>`;
  submodal.classList.remove("hidden");

  const res = await fetch(`/api/tareas_auxiliar/${encodeURIComponent(nombre)}`);
  const tareas = await res.json();

  if (tareas.length === 0) {
    lista.innerHTML = `<p class="text-slate-500">No hay tareas registradas recientemente.</p>`;
    return;
  }

  lista.innerHTML = "";
  tareas.forEach(t => {
    const row = document.createElement("div");
    row.className = "py-3 flex justify-between items-center";
    row.innerHTML = `
      <div class="w-24 text-slate-500 text-sm">${t.fecha}</div>
      <div class="flex-1">${t.actividad}</div>
      <div class="w-24 text-right">${t.cantidad.toFixed(2)}</div>
      <div class="w-24 text-right text-blue-600 font-medium">${t.porcentaje.toFixed(0)}%</div>
    `;
    lista.appendChild(row);
  });
}



async function loadTablaPendientes() {
  const res = await fetch("/api/tareas_pendientes");
  const data = await res.json();

  const table = document.getElementById("tablaPendientes");
  table.innerHTML = "";

  data.forEach(t => {
    const color =
      t.estado === "vencida" ? "bg-red-100 text-red-700 border-red-300" :
      t.estado === "proxima" ? "bg-yellow-100 text-yellow-700 border-yellow-300" :
      "bg-green-100 text-green-700 border-green-300";

    const row = document.createElement("div");
    row.className = `grid grid-cols-7 gap-2 p-2 rounded-xl border ${color}`;

    row.innerHTML = `
      <div class="font-semibold">${t.numero_tarea}</div>
      <div>${t.tipo}</div>
      <div>${t.tipologia || "—"}</div>
      <div>${t.finca || "—"}</div>
      <div>${t.fecha_publicacion}</div>
      <div class="font-bold">${t.dias_restantes} días</div>
      <button class="px-2 py-1 bg-blue-600 text-white rounded-xl hover:bg-blue-700">
        Abrir
      </button>
    `;

    table.appendChild(row);
  });
}

loadTablaPendientes();


// Crear el modal al cargar la página
createModal();

// Hacer clic sobre el número de auxiliares para ver la lista
document.getElementById("card-auxiliares").style.cursor = "pointer";
document.getElementById("card-auxiliares").onclick = showAuxiliaresActivos;
