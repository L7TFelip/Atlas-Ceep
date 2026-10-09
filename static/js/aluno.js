(() => {
  "use strict";

  const { $, $$, api, currentUser, escapeHtml } = window.Atlas;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let state = { subjects: [], tasks: [], notices: [], events: [] };
  let currentFilter = "all";
  let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  let selectedDate = isoDate(today);
  let selectedDetailId = null;
  let editingTaskId = null;

  function isoDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function addDays(date, days) {
    const copy = new Date(date);
    copy.setDate(copy.getDate() + days);
    return copy;
  }

  function daysBetween(a, b) {
    if (!a || !b) return 9999;
    return Math.round((new Date(`${a}T00:00:00`) - new Date(`${b}T00:00:00`)) / 86400000);
  }

  function formatDate(value) {
    if (!value) return "Sem data";
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  }

  function formatLongDate(value) {
    if (!value) return "Sem data";
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR", {
      weekday: "long", day: "2-digit", month: "long"
    });
  }

  function statusInfo(task) {
    if (task.status === "done") return { key: "done", label: "Concluída", className: "status-done" };
    const diff = daysBetween(task.due, isoDate(today));
    if (diff < 0) return { key: "overdue", label: "Atrasada", className: "status-overdue" };
    if (diff <= 2) return {
      key: "soon",
      label: diff === 0 ? "Entrega hoje" : `Vence em ${diff}d`,
      className: "status-soon"
    };
    if (task.status === "progress") return { key: "progress", label: "Em andamento", className: "status-progress" };
    return { key: "pending", label: "Pendente", className: "status-pending" };
  }

  function taskMatchesFilter(task, filter = currentFilter) {
    const status = statusInfo(task).key;
    if (filter === "all") return true;
    if (filter === "pending") return status === "pending";
    if (filter === "progress") return task.status === "progress";
    if (filter === "overdue") return status === "overdue";
    if (filter === "soon") return status === "soon";
    if (filter === "done") return status === "done";
    return true;
  }

  function renderSubjects() {
    const select = $("#subjectFilter");
    const current = select.value;
    const activityCounts = new Map();
    state.tasks
      .filter(task => task.source === "professor" && task.subject)
      .forEach(task => activityCounts.set(task.subject, (activityCounts.get(task.subject) || 0) + 1));
    const subjects = [...new Map(state.subjects
      .filter(subject => subject?.nome)
      .map(subject => [subject.nome, subject.nome])).values()]
      .sort((a, b) => a.localeCompare(b));
    select.innerHTML = '<option value="all">Todas as disciplinas</option>' + subjects
      .map(subject => {
        const count = activityCounts.get(subject) || 0;
        const label = count === 0
          ? `${subject} (sem atividades)`
          : `${subject} (${count} ${count === 1 ? "atividade" : "atividades"})`;
        return `<option value="${escapeHtml(subject)}">${escapeHtml(label)}</option>`;
      })
      .join("");
    select.value = subjects.includes(current) ? current : "all";
  }

  function getFilteredTasks() {
    const subject = $("#subjectFilter").value;
    return state.tasks
      .filter(task => taskMatchesFilter(task))
      .filter(task => subject === "all" || task.subject === subject)
      .sort((a, b) => {
        if (a.status === "done" && b.status !== "done") return 1;
        if (a.status !== "done" && b.status === "done") return -1;
        return (a.due || "9999-12-31").localeCompare(b.due || "9999-12-31");
      });
  }

  function taskElement(task) {
    const status = statusInfo(task);
    const article = document.createElement("article");
    article.className = `task ${task.status === "done" ? "done" : ""}`;
    article.dataset.id = task.id;
    article.innerHTML = `
      <button class="check" type="button">${task.status === "done" ? "✓" : ""}</button>
      <div class="task-content">
        <span class="task-title">${escapeHtml(task.title)}</span>
        <div class="task-subject-line">
          ${task.submittedAt ? "<span>Entrega registrada</span>" : ""}
          ${task.teacher ? `<span>${escapeHtml(task.teacher)}</span>` : ""}
          ${task.source === "professor" ? '<span class="change-badge">Professor</span>' : ""}
        </div>
      </div>
      <div class="task-side">
        <span class="status-pill ${status.className}">${escapeHtml(status.label)}</span>
        <span class="task-due">${task.status === "done" ? "Concluída" : formatDate(task.due)}</span>
      </div>
      ${task.editable ? '<button class="delete-btn" type="button">×</button>' : ""}
    `;

    $(".check", article).addEventListener("click", event => {
      event.stopPropagation();
      toggleTask(task);
    });

    $(".delete-btn", article)?.addEventListener("click", event => {
      event.stopPropagation();
      removeTask(task);
    });

    article.addEventListener("click", () => openDetail(task.id));
    return article;
  }

  function renderTasks() {
    const tasks = getFilteredTasks();
    const list = $("#taskList");
    list.innerHTML = "";
    list.hidden = tasks.length === 0;
    $("#taskEmpty").hidden = tasks.length !== 0;
    if (!tasks.length) return;

    const groups = {};
    tasks.forEach(task => {
      if (!groups[task.subject]) groups[task.subject] = [];
      groups[task.subject].push(task);
    });

    Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0])).forEach(([subject, items]) => {
      const group = document.createElement("section");
      group.className = "subject-group";
      group.innerHTML = `
        <div class="subject-group-title">
          <span>${escapeHtml(subject)}</span>
          <small>${items.length} ${items.length === 1 ? "atividade" : "atividades"}</small>
        </div>
      `;
      items.forEach(task => group.appendChild(taskElement(task)));
      list.appendChild(group);
    });
  }

  function renderStats() {
    const subject = $("#subjectFilter").value;
    const tasks = state.tasks.filter(task => subject === "all" || task.subject === subject);
    $$("#statusFilters .filter-chip").forEach(button => {
      const count = tasks.filter(task => taskMatchesFilter(task, button.dataset.filter)).length;
      button.querySelector(".filter-count").textContent = count;
    });
  }

  function renderToday() {
    const todayIso = isoDate(today);
    const tasks = state.tasks
      .filter(task => task.due === todayIso)
      .sort((a, b) => a.title.localeCompare(b.title));
    const notices = state.notices.filter(notice => notice.date === todayIso);
    const events = state.events.filter(event => event.data_evento === todayIso);
    const itemCount = tasks.length + notices.length + events.length;

    $("#todayTitle").textContent = new Date(`${todayIso}T00:00:00`).toLocaleDateString("pt-BR", {
      weekday: "long", day: "numeric", month: "long"
    });
    $("#todayCount").textContent = `${itemCount} ${itemCount === 1 ? "item" : "itens"}`;

    const list = $("#todayList");
    list.innerHTML = [
      ...tasks.map(task => `
      <button type="button" class="calendar-event" data-task-id="${escapeHtml(task.id)}">
        <span class="event-bullet" aria-hidden="true"></span>
        <span class="calendar-event-text"><strong>${escapeHtml(task.subject)}</strong>
        <span>${escapeHtml(task.title)}</span></span>
      </button>
      `),
      ...notices.map(notice => `
        <div class="calendar-event"><span class="event-bullet notice-bullet" aria-hidden="true"></span><span class="calendar-event-text"><strong>Aviso</strong><span>${escapeHtml(notice.title)}</span></span></div>
      `),
      ...events.map(event => `
        <div class="calendar-event"><span class="event-bullet" aria-hidden="true"></span><span class="calendar-event-text"><strong>${escapeHtml(event.tipo || "Evento")}</strong><span>${escapeHtml(event.nome)}${event.horario ? ` · ${escapeHtml(event.horario)}` : ""}</span></span></div>
      `)
    ].join("");
    $("#todayEmpty").hidden = itemCount !== 0;
    list.hidden = itemCount === 0;
    $$('[data-task-id]', list).forEach(button => {
      button.addEventListener("click", () => openDetail(button.dataset.taskId));
    });
  }

  function dateHasEvent(dateIso) {
    return state.tasks.some(task => task.due === dateIso) ||
      state.notices.some(notice => notice.date === dateIso) ||
      state.events.some(event => event.data_evento === dateIso);
  }

  function renderCalendar() {
    const label = currentMonth.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
    $("#monthLabel").textContent = label.charAt(0).toUpperCase() + label.slice(1);

    const calendar = $("#calendar");
    calendar.innerHTML = "";
    const first = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
    const totalDays = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();

    for (let i = 0; i < first.getDay(); i++) {
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
      if (dateHasEvent(dateIso)) button.classList.add("has-event");
      button.setAttribute("aria-label", formatLongDate(dateIso));
      button.setAttribute("aria-pressed", String(dateIso === selectedDate));
      button.addEventListener("click", () => {
        selectedDate = dateIso;
        renderCalendar();
      });
      calendar.appendChild(button);
    }

    renderSelectedEvents();
  }

  function renderSelectedEvents() {
    const container = $("#selectedEvents");
    const isToday = selectedDate === isoDate(today);
    $("#todaySection").hidden = !isToday;

    if (isToday) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }

    const tasks = state.tasks.filter(task => task.due === selectedDate);
    const notices = state.notices.filter(notice => notice.date === selectedDate);
    const events = state.events.filter(event => event.data_evento === selectedDate);

    if (!tasks.length && !notices.length && !events.length) {
      container.hidden = false;
      container.innerHTML = `
        <div class="selected-date-title">${escapeHtml(formatLongDate(selectedDate))}</div>
        <p class="muted">Nenhum item nesta data.</p>
      `;
      return;
    }

    container.hidden = false;
    container.innerHTML = `
      <div class="selected-date-title">${escapeHtml(formatLongDate(selectedDate))}</div>
      ${tasks.map(task => `
        <button type="button" class="calendar-event" data-task-id="${escapeHtml(task.id)}">
          <span class="event-bullet" aria-hidden="true"></span>
          <span class="calendar-event-text"><strong>${escapeHtml(task.subject)}</strong><span>${escapeHtml(task.title)}</span></span>
        </button>
      `).join("")}
      ${notices.map(notice => `
        <div class="calendar-event"><span class="event-bullet notice-bullet" aria-hidden="true"></span><span class="calendar-event-text"><strong>Aviso</strong><span>${escapeHtml(notice.title)}</span></span></div>
      `).join("")}
      ${events.map(event => `
        <div class="calendar-event">
          <span class="event-bullet" aria-hidden="true"></span>
          <span class="calendar-event-text"><strong>${escapeHtml(event.tipo || "Evento")}</strong><span>${escapeHtml(event.nome)}${event.horario ? ` · ${escapeHtml(event.horario)}` : ""}</span></span>
        </div>
      `).join("")}
    `;

    $$('[data-task-id]', container).forEach(button => {
      button.addEventListener("click", () => openDetail(button.dataset.taskId));
    });
  }

  function renderNotices() {
    const list = $("#noticeList");
    const upcomingEvents = state.events
      .filter(event => !event.data_evento || event.data_evento >= isoDate(today))
      .slice(0, 5);

    list.innerHTML = [
      ...state.notices.map(notice => `
        <article class="notice-item">
          <div>
            <strong>${escapeHtml(notice.title)}</strong>
            <span>${formatDate(notice.date)}</span>
          </div>
          ${notice.editable ? `<button type="button" class="delete-btn" data-notice-id="${notice.sourceId}">×</button>` : ""}
        </article>
      `),
      ...upcomingEvents.map(event => `
        <article class="notice-item">
          <div>
            <strong>${escapeHtml(event.nome)}</strong>
            <span>${formatDate(event.data_evento)}${event.local ? ` · ${escapeHtml(event.local)}` : ""}</span>
          </div>
        </article>
      `)
    ].join("");

    $$('[data-notice-id]', list).forEach(button => {
      button.addEventListener("click", () => removeNotice(Number(button.dataset.noticeId)));
    });
  }

  function openDialog(id) {
    const dialog = $(`#${id}`);
    if (dialog && !dialog.open) dialog.showModal();
  }

  function closeDialog(id) {
    const dialog = $(`#${id}`);
    if (dialog?.open) dialog.close();
  }

  function openDetail(id) {
    const task = state.tasks.find(item => item.id === id);
    if (!task) return;
    selectedDetailId = id;
    updateDetail(task);
    openDialog("detailDialog");
  }

  function updateDetail(task) {
    const status = statusInfo(task);
    $("#detailSubject").textContent = task.subject || "ATIVIDADE";
    $("#detailTitle").textContent = task.title;
    $("#detailMeta").innerHTML = `
      <span class="status-pill ${status.className}">${escapeHtml(status.label)}</span>
      <span>Prazo: ${escapeHtml(formatLongDate(task.due))}</span>
      ${task.teacher ? `<span>Professor: ${escapeHtml(task.teacher)}</span>` : ""}
      ${task.inClass ? `<span>Passada em sala em ${escapeHtml(formatDate(task.assignedOn || task.created))}</span>` : ""}
    `;
    $("#detailDescription").textContent = task.description || "Nenhuma observação cadastrada.";
    $("#detailToggleBtn").textContent = task.status === "done" ? "Marcar como pendente" : "Marcar como concluída";
    $("#detailDeliveryStatus").textContent = task.submittedAt
      ? `Entrega registrada em ${formatDate(task.submittedAt)}`
      : "Entrega não registrada";
    $("#detailDeliveryBtn").textContent = task.submittedAt ? "Desfazer registro" : "Registrar entrega";
    $("#detailEditBtn").hidden = !task.editable;
    $("#detailChanges").hidden = true;
  }

  function setAssignedDateVisibility() {
    const active = $("#taskIsToday").checked;
    $("#taskAssignedWrap").hidden = !active;
    $("#taskAssignedOn").required = active;
  }

  function openTaskForm(task = null) {
    if (!task?.editable) return;
    editingTaskId = task.id;
    $("#taskDialogTitle").textContent = "Editar atividade";
    $("#taskSubmitBtn").textContent = "Salvar alterações";
    $("#taskForm").reset();
    $("#taskTitle").value = task?.title || "";
    $("#taskSubject").value = task?.subject || "Língua Portuguesa";
    $("#taskTeacher").value = task?.teacher || "";
    $("#taskDue").value = task?.due || isoDate(addDays(today, 1));
    $("#taskDescription").value = task?.description || "";
    $("#taskIsToday").checked = Boolean(task.inClass);
    $("#taskAssignedOn").value = task?.assignedOn || task?.created || isoDate(today);
    setAssignedDateVisibility();
    openDialog("taskDialog");
  }

  async function loadData() {
    try {
      const user = await currentUser({ redirectOn401: true });
      if (!user) return;
      if (user.papel !== "aluno") return window.location.href = "/login";
      const data = await api("/api/aluno/agenda");
      state = {
        subjects: data.subjects || [],
        tasks: data.tasks || [],
        notices: data.notices || [],
        events: data.events || []
      };
      renderAll();
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  async function toggleTask(task) {
    const nextStatus = task.status === "done" ? "pending" : "done";
    try {
      await api(`/api/aluno/tarefas/${task.source}/${task.sourceId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus, entregue_em: task.submittedAt || null })
      });
      await loadData();
      const updated = state.tasks.find(item => item.id === task.id);
      if (updated && $("#detailDialog").open) updateDetail(updated);
    } catch (error) {
      alert(error.message);
    }
  }

  async function toggleDelivery(task) {
    const delivered = task.submittedAt ? null : isoDate(today);
    try {
      await api(`/api/aluno/tarefas/${task.source}/${task.sourceId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: task.status, entregue_em: delivered })
      });
      await loadData();
      const updated = state.tasks.find(item => item.id === task.id);
      if (updated) updateDetail(updated);
    } catch (error) {
      alert(error.message);
    }
  }

  async function removeTask(task) {
    if (!task.editable) return;
    try {
      await api(`/api/aluno/atividades/${task.sourceId}`, { method: "DELETE" });
      await loadData();
    } catch (error) {
      alert(error.message);
    }
  }

  async function removeNotice(id) {
    try {
      await api(`/api/aluno/avisos/${id}`, { method: "DELETE" });
      await loadData();
    } catch (error) {
      alert(error.message);
    }
  }

  function renderAll() {
    renderSubjects();
    renderTasks();
    renderStats();
    renderToday();
    renderCalendar();
    renderNotices();
  }

  function bindUI() {
    $("#prevMonth")?.addEventListener("click", () => {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
      selectedDate = isoDate(currentMonth);
      renderCalendar();
    });

    $("#nextMonth")?.addEventListener("click", () => {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
      selectedDate = isoDate(currentMonth);
      renderCalendar();
    });

    $("#subjectFilter")?.addEventListener("change", () => {
      renderTasks();
      renderStats();
    });

    $$("#statusFilters .filter-chip").forEach(button => {
      button.addEventListener("click", () => {
        $$("#statusFilters .filter-chip").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        currentFilter = button.dataset.filter;
        renderTasks();
      });
    });

    $$("[data-close]").forEach(button => button.addEventListener("click", () => closeDialog(button.dataset.close)));
    $("#taskIsToday")?.addEventListener("change", setAssignedDateVisibility);

    $("#taskForm")?.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = {
        titulo: $("#taskTitle").value.trim(),
        disciplina: $("#taskSubject").value,
        professor: $("#taskTeacher").value.trim(),
        prazo: $("#taskDue").value,
        descricao: $("#taskDescription").value.trim(),
        foi_passada_em_sala: $("#taskIsToday").checked,
        data_passada: $("#taskIsToday").checked ? $("#taskAssignedOn").value : null
      };
      if (!payload.titulo || !payload.disciplina || !payload.prazo) return;

      try {
        const editing = state.tasks.find(task => task.id === editingTaskId);
        if (!editing?.editable) return;
        await api(`/api/aluno/atividades/${editing.sourceId}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
        editingTaskId = null;
        closeDialog("taskDialog");
        await loadData();
      } catch (error) {
        alert(error.message);
      }
    });

    $("#detailEditBtn")?.addEventListener("click", () => {
      const task = state.tasks.find(item => item.id === selectedDetailId);
      if (!task?.editable) return;
      closeDialog("detailDialog");
      openTaskForm(task);
    });

    $("#detailDeliveryBtn")?.addEventListener("click", () => {
      const task = state.tasks.find(item => item.id === selectedDetailId);
      if (task) toggleDelivery(task);
    });

    $("#detailToggleBtn")?.addEventListener("click", () => {
      const task = state.tasks.find(item => item.id === selectedDetailId);
      if (task) toggleTask(task);
    });

    $("#taskAssignedOn").value = isoDate(today);
    $("#taskDue").value = isoDate(addDays(today, 1));
    setAssignedDateVisibility();
  }

  function init() {
    if (!$("#taskList")) return;
    bindUI();
    loadData();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
