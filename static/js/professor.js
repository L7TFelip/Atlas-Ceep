(() => {
  "use strict";

  const { $, $$, api, currentUser, escapeHtml } = window.Atlas;

  let state = [];
  let turmas = [];
  let materias = [];
  let editingId = null;
  let deletingId = null;
  let activeType = "all";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  let selectedDate = isoDate(today);

  function isoDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function formatDate(value) {
    if (!value) return "Sem data";
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
  }

  function formatLongDate(value) {
    if (!value) return "Sem data";
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR", {
      weekday: "long", day: "2-digit", month: "long"
    });
  }

  function publicationsForDate(date) {
    const items = [];
    state.forEach(publication => {
      const context = [publication.className, publication.subject].filter(Boolean).join(" · ");
      if (publication.date === date) {
        items.push({ ...publication, calendarLabel: "Publicação", calendarContext: context });
      }
      if (publication.type === "atividade" && publication.deadline === date && publication.deadline !== publication.date) {
        items.push({ ...publication, calendarLabel: "Prazo", calendarContext: context });
      }
    });
    return items;
  }

  function calendarItemMarkup(item) {
    return `<button type="button" class="calendar-event" data-publication-id="${item.id}">
      <span class="event-bullet" aria-hidden="true"></span>
      <span class="calendar-event-text"><strong>${escapeHtml(item.title)}</strong>
      <span>${escapeHtml(item.calendarLabel)}${item.calendarContext ? ` · ${escapeHtml(item.calendarContext)}` : ""}</span></span>
    </button>`;
  }

  function bindCalendarItems(container) {
    container.querySelectorAll("[data-publication-id]").forEach(button => {
      button.addEventListener("click", () => openForm(Number(button.dataset.publicationId)));
    });
  }

  function renderSelectedPublications() {
    const items = publicationsForDate(selectedDate);
    const isToday = selectedDate === isoDate(today);
    $("#todaySection").hidden = !isToday;
    $("#todayTitle").textContent = formatLongDate(selectedDate);
    $("#todayCount").textContent = `${items.length} ${items.length === 1 ? "item" : "itens"}`;
    const todayList = $("#todayList");
    todayList.innerHTML = items.map(calendarItemMarkup).join("");
    bindCalendarItems(todayList);
    $("#todayEmpty").hidden = items.length !== 0;

    const selected = $("#selectedEvents");
    if (isToday) {
      selected.hidden = true;
      selected.innerHTML = "";
      return;
    }

    selected.hidden = false;
    selected.innerHTML = `<div class="selected-date-title">${escapeHtml(formatLongDate(selectedDate))}</div>
      ${items.length ? items.map(calendarItemMarkup).join("") : '<p class="muted">Nenhum item nesta data.</p>'}`;
    bindCalendarItems(selected);
  }

  function renderCalendar() {
    const label = currentMonth.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
    $("#monthLabel").textContent = label.charAt(0).toUpperCase() + label.slice(1);
    const calendar = $("#calendar");
    calendar.innerHTML = "";
    const first = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
    const totalDays = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();

    for (let index = 0; index < first.getDay(); index++) {
      const blank = document.createElement("span");
      blank.className = "day blank";
      calendar.appendChild(blank);
    }

    for (let day = 1; day <= totalDays; day++) {
      const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
      const dateIso = isoDate(date);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "day";
      button.textContent = day;
      if (dateIso === isoDate(today)) button.classList.add("today");
      if (dateIso === selectedDate) button.classList.add("selected");
      if (publicationsForDate(dateIso).length) button.classList.add("has-event");
      button.setAttribute("aria-label", formatLongDate(dateIso));
      button.setAttribute("aria-pressed", String(dateIso === selectedDate));
      button.addEventListener("click", () => {
        selectedDate = dateIso;
        renderCalendar();
      });
      calendar.appendChild(button);
    }
    renderSelectedPublications();
  }

  function normalize(item) {
    return {
      id: item.id_publicacao,
      title: item.titulo,
      description: item.descricao || "",
      type: item.tipo,
      date: item.data_publicacao,
      deadline: item.prazo_entrega || "",
      classId: item.id_turma,
      className: item.turma,
      subjectId: item.id_materia,
      subject: item.materia
    };
  }

  function populateFormOptions() {
    const subject = $("#contentSubject");
    const classSelect = $("#contentClass");

    subject.innerHTML = '<option value="">Selecione</option>' + materias
      .map(item => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`)
      .join("");

    classSelect.innerHTML = '<option value="">Selecione</option>' + turmas
      .map(item => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`)
      .join("");
  }

  function renderFilters() {
    const classFilter = $("#classFilter");
    const subjectFilter = $("#subjectFilter");
    const currentClass = classFilter.value || "all";
    const currentSubject = subjectFilter.value || "all";

    classFilter.innerHTML = '<option value="all">Todas as turmas</option>' + turmas
      .map(item => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`)
      .join("");
    subjectFilter.innerHTML = '<option value="all">Todas as disciplinas</option>' + materias
      .map(item => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`)
      .join("");

    classFilter.value = turmas.some(i => String(i.id) === currentClass) ? currentClass : "all";
    subjectFilter.value = materias.some(i => String(i.id) === currentSubject) ? currentSubject : "all";

    $$("#typeFilters [data-type]").forEach(btn => {
      const type = btn.dataset.type;
      const count = type === "all" ? state.length : state.filter(i => i.type === type).length;
      const target = btn.querySelector(".filter-count");
      if (target) target.textContent = count;
    });
  }

  function getFiltered() {
    const classValue = $("#classFilter").value;
    const subjectValue = $("#subjectFilter").value;
    return state
      .filter(item => activeType === "all" || item.type === activeType)
      .filter(item => classValue === "all" || String(item.classId) === classValue)
      .filter(item => subjectValue === "all" || String(item.subjectId) === subjectValue)
      .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  }

  function render() {
    renderFilters();
    const list = $("#contentList");
    const items = getFiltered();
    list.innerHTML = "";
    $("#contentEmpty").hidden = items.length > 0;

    items.forEach(item => {
      const article = document.createElement("article");
      article.className = "task";
      article.innerHTML = `
        <div class="task-content">
          <strong class="task-title">${escapeHtml(item.title)}</strong>
          <div class="task-subject-line">
            <span>${escapeHtml(item.subject)}</span>
            <span>• ${escapeHtml(item.className)}</span>
          </div>
          <div class="task-subject-line">
            <span>${escapeHtml(item.type)}</span>
            <span>• ${formatDate(item.date)}</span>
            ${item.deadline ? `<span>• Prazo: ${formatDate(item.deadline)}</span>` : ""}
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

    renderCalendar();
  }

  function updateDeadlineVisibility() {
    const isActivity = $("#contentType").value === "atividade";
    $("#deadlineField").hidden = !isActivity;
    if (!isActivity) $("#contentDeadline").value = "";
  }

  function openForm(id = null) {
    editingId = id;
    const item = state.find(i => i.id === id);

    $("#formEyebrow").textContent = item ? "EDITAR PUBLICAÇÃO" : "NOVA PUBLICAÇÃO";
    $("#formTitle").textContent = item ? "Editar conteúdo" : "Publicar conteúdo";
    $("#saveContentBtn").textContent = item ? "Salvar alterações" : "Publicar conteúdo";

    $("#contentTitle").value = item?.title || "";
    $("#contentSubject").value = item ? String(item.subjectId) : "";
    $("#contentType").value = item?.type || "";
    $("#contentClass").value = item ? String(item.classId) : "";
    $("#contentDate").value = item?.date || new Date().toISOString().slice(0, 10);
    $("#contentDeadline").value = item?.deadline || "";
    $("#contentDescription").value = item?.description || "";
    updateDeadlineVisibility();
    $("#contentDialog").showModal();
  }

  function closeForm() {
    $("#contentDialog").close();
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
      if (user.papel !== "professor") {
        window.location.href = "/login";
        return;
      }

      const [optionsData, publicationsData] = await Promise.all([
        api("/api/professor/opcoes"),
        api("/api/professor/publicacoes")
      ]);

      turmas = optionsData.turmas || [];
      materias = optionsData.materias || [];
      state = (publicationsData.publicacoes || []).map(normalize);
      populateFormOptions();
      render();
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  function bind() {
    $("#newContentBtn2")?.addEventListener("click", () => openForm());
    $("#emptyCreateBtn")?.addEventListener("click", () => openForm());
    $("#closeContentBtn")?.addEventListener("click", closeForm);
    $("#cancelContentBtn")?.addEventListener("click", closeForm);
    $("#contentType")?.addEventListener("change", updateDeadlineVisibility);
    $("#closeDeleteBtn")?.addEventListener("click", closeDelete);
    $("#cancelDeleteBtn")?.addEventListener("click", closeDelete);

    $("#prevMonth")?.addEventListener("click", () => {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
      renderCalendar();
    });
    $("#nextMonth")?.addEventListener("click", () => {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
      renderCalendar();
    });

    $("#confirmDeleteBtn")?.addEventListener("click", async () => {
      if (!deletingId) return closeDelete();
      try {
        await api(`/api/professor/publicacoes/${deletingId}`, { method: "DELETE" });
        closeDelete();
        await loadData();
      } catch (error) {
        alert(error.message);
      }
    });

    $("#contentForm")?.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = {
        titulo: $("#contentTitle").value.trim(),
        id_materia: Number($("#contentSubject").value),
        tipo: $("#contentType").value,
        id_turma: Number($("#contentClass").value),
        data_publicacao: $("#contentDate").value,
        prazo_entrega: $("#contentType").value === "atividade" ? $("#contentDeadline").value : null,
        descricao: $("#contentDescription").value.trim()
      };

      try {
        await api(editingId ? `/api/professor/publicacoes/${editingId}` : "/api/professor/publicacoes", {
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

    $("#classFilter")?.addEventListener("change", render);
    $("#subjectFilter")?.addEventListener("change", render);
  }

  function init() {
    if (!$("#contentList")) return;
    bind();
    loadData();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
