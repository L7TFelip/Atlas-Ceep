(() => {
  "use strict";

  const { $, $$, api, currentUser, escapeHtml } = window.Atlas;

  let state = [];
  let editingId = null;
  let deletingId = null;
  let activeType = "all";

  function normalize(item) {
    return {
      id: item.id_evento,
      title: item.nome,
      description: item.descricao || "",
      type: item.tipo || "evento",
      audience: item.publico || "todos",
      date: item.data_evento || "",
      time: item.horario || "",
      location: item.local || ""
    };
  }

  function formatDate(value) {
    if (!value) return "Sem data";
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
  }

  function renderMonthFilter() {
    const select = $("#monthFilter");
    const current = select.value || "all";
    const months = [...new Set(state.map(e => e.date?.slice(0, 7)).filter(Boolean))].sort();
    select.innerHTML = '<option value="all">Todos os meses</option>' + months.map(month => {
      const [y, m] = month.split("-");
      const label = new Date(Number(y), Number(m) - 1, 1).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
      return `<option value="${month}">${label.charAt(0).toUpperCase() + label.slice(1)}</option>`;
    }).join("");
    select.value = months.includes(current) ? current : "all";
  }

  function getFiltered() {
    const audience = $("#audienceFilter").value;
    const month = $("#monthFilter").value;
    return state
      .filter(item => activeType === "all" || item.type === activeType)
      .filter(item => audience === "all" || item.audience === audience || item.audience === "todos")
      .filter(item => month === "all" || item.date.startsWith(month))
      .sort((a, b) => (a.date || "9999-12-31").localeCompare(b.date || "9999-12-31"));
  }

  function render() {
    renderMonthFilter();
    $$("#typeFilters [data-type]").forEach(btn => {
      const type = btn.dataset.type;
      const count = type === "all" ? state.length : state.filter(e => e.type === type).length;
      btn.querySelector(".filter-count").textContent = count;
    });

    const items = getFiltered();
    const list = $("#eventList");
    list.innerHTML = "";
    $("#eventEmpty").hidden = items.length > 0;

    items.forEach(item => {
      const article = document.createElement("article");
      article.className = "task";
      article.innerHTML = `
        <div class="task-content">
          <strong class="task-title">${escapeHtml(item.title)}</strong>
          <div class="task-subject-line">
            <span>${escapeHtml(item.type)}</span>
            <span>• ${formatDate(item.date)}${item.time ? ` às ${escapeHtml(item.time)}` : ""}</span>
          </div>
          <div class="task-subject-line">
            ${item.location ? `<span>${escapeHtml(item.location)}</span>` : ""}
            <span>• Público: ${escapeHtml(item.audience)}</span>
          </div>
        </div>
        <div class="task-side">
          <button type="button" class="ghost-btn edit-btn">Editar</button>
          <button type="button" class="danger-btn delete-btn">Excluir</button>
        </div>
      `;
      $(".edit-btn", article).addEventListener("click", () => openForm(item.id));
      $(".delete-btn", article).addEventListener("click", () => openDelete(item.id));
      list.appendChild(article);
    });

    const today = new Date().toISOString().slice(0, 10);
    $("#upcomingList").innerHTML = state
      .filter(e => e.date && e.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 5)
      .map(e => `<div class="recent-item"><strong>${escapeHtml(e.title)}</strong><span>${formatDate(e.date)}</span></div>`)
      .join("");

    const counts = {};
    state.forEach(e => { counts[e.type] = (counts[e.type] || 0) + 1; });
    $("#categoryList").innerHTML = Object.entries(counts)
      .map(([name, count]) => `<div class="class-item"><strong>${escapeHtml(name)}</strong><span>${count}</span></div>`)
      .join("");
  }

  function openForm(id = null) {
    editingId = id;
    const item = state.find(e => e.id === id);
    $("#formEyebrow").textContent = item ? "EDITAR EVENTO" : "NOVO EVENTO";
    $("#formTitle").textContent = item ? "Editar evento" : "Criar evento";
    $("#saveEventBtn").textContent = item ? "Salvar alterações" : "Publicar evento";
    $("#eventTitle").value = item?.title || "";
    $("#eventType").value = item?.type || "evento";
    $("#eventAudience").value = item?.audience || "todos";
    $("#eventDate").value = item?.date || new Date().toISOString().slice(0, 10);
    $("#eventTime").value = item?.time || "";
    $("#eventLocation").value = item?.location || "";
    $("#eventDescription").value = item?.description || "";
    $("#eventDialog").showModal();
  }

  function closeForm() {
    $("#eventDialog").close();
    editingId = null;
  }

  function openDelete(id) {
    deletingId = id;
    $("#deleteDialog").showModal();
  }

  function closeDelete() {
    deletingId = null;
    $("#deleteDialog").close();
  }

  async function loadData() {
    try {
      const user = await currentUser({ redirectOn401: true });
      if (!user) return;
      if (user.papel !== "adm") return window.location.href = "/login";
      const data = await api("/api/eventos");
      state = (data.eventos || []).map(normalize);
      render();
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  function bind() {
    $("#newEventBtn")?.addEventListener("click", () => openForm());
    $("#newEventBtn2")?.addEventListener("click", () => openForm());
    $("#emptyCreateBtn")?.addEventListener("click", () => openForm());
    $("#closeEventBtn")?.addEventListener("click", closeForm);
    $("#cancelEventBtn")?.addEventListener("click", closeForm);
    $("#closeDeleteBtn")?.addEventListener("click", closeDelete);
    $("#cancelDeleteBtn")?.addEventListener("click", closeDelete);
    $("#clearDataBtn")?.addEventListener("click", loadData);

    $("#confirmDeleteBtn")?.addEventListener("click", async () => {
      if (!deletingId) return closeDelete();
      try {
        await api(`/api/eventos/${deletingId}`, { method: "DELETE" });
        closeDelete();
        await loadData();
      } catch (error) {
        alert(error.message);
      }
    });

    $("#eventForm")?.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = {
        nome: $("#eventTitle").value.trim(),
        tipo: $("#eventType").value,
        publico: $("#eventAudience").value,
        data_evento: $("#eventDate").value,
        horario: $("#eventTime").value,
        local: $("#eventLocation").value.trim(),
        descricao: $("#eventDescription").value.trim()
      };

      try {
        await api(editingId ? `/api/eventos/${editingId}` : "/api/eventos", {
          method: editingId ? "PUT" : "POST",
          body: JSON.stringify(payload)
        });
        closeForm();
        await loadData();
      } catch (error) {
        alert(error.message);
      }
    });

    $$("#typeFilters [data-type]").forEach(btn => {
      btn.addEventListener("click", () => {
        activeType = btn.dataset.type;
        $$("#typeFilters [data-type]").forEach(item => item.classList.toggle("active", item === btn));
        render();
      });
    });

    $("#audienceFilter")?.addEventListener("change", render);
    $("#monthFilter")?.addEventListener("change", render);
  }

  function init() {
    if (!$("#eventList")) return;
    bind();
    loadData();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
