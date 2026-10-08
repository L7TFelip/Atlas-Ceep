(() => {
  "use strict";

  const { $, $$, api, currentUser, escapeHtml } = window.Atlas;
  const students = [];
  const teachers = [];
  let classes = [];
  let currentAdminId = null;
  let editing = null;
  let deleting = null;
  let editingClassId = null;
  let academicDeleteAction = null;

  function personItem(person, kind) {
    const student = kind === "student";
    const id = student ? person.id_aluno : person.id_professor;
    const detail = student
      ? [person.cgm ? `CGM: ${person.cgm}` : "CGM não informado", person.turma || "Sem turma", person.email].filter(Boolean).join(" · ")
      : [person.atributo, person.telefone].filter(Boolean).join(" · ");
    const article = document.createElement("article");
    article.className = "task";
    article.innerHTML = `<div class="task-content">
      <strong class="task-title">${escapeHtml(person.nome)}</strong>
      <div class="task-subject-line"><span>${escapeHtml(detail || "Sem informações adicionais")}</span></div>
      </div><div class="task-side">
      <button type="button" class="ghost-btn edit-person-btn">Editar</button>
      <button type="button" class="danger-btn delete-person-btn">Excluir</button>
      </div>`;
    $(".edit-person-btn", article).addEventListener("click", () => openForm(kind, id));
    $(".delete-person-btn", article).addEventListener("click", () => openDelete(kind, id, person.nome));
    return article;
  }

  function renderList(kind, items) {
    const list = $(`#${kind}List`);
    list.replaceChildren(...items.map(item => personItem(item, kind)));
    list.hidden = items.length === 0;
    $(`#${kind}Empty`).hidden = items.length !== 0;
  }

  async function loadPeople() {
    const [studentData, teacherData, classData] = await Promise.all([
      api("/api/alunos"), api("/api/professores"), api("/api/turmas")
    ]);
    students.splice(0, students.length, ...(studentData.alunos || []));
    teachers.splice(0, teachers.length, ...(teacherData.professores || []));
    classes = classData.turmas || [];
    renderList("student", students);
    renderList("teacher", teachers);
    renderClasses();
    const classSelect = $("#studentClass");
    const selected = classSelect.value;
    classSelect.innerHTML = '<option value="">Sem turma</option>' + classes.map(item =>
      `<option value="${item.id_turma}">${escapeHtml(item.nome)}</option>`
    ).join("");
    if (classes.some(item => String(item.id_turma) === selected)) classSelect.value = selected;
  }

  function renderClasses() {
    const list = $("#classList");
    list.replaceChildren(...classes.map(item => {
      const details = [item.sala ? `Sala ${item.sala}` : "", item.ano || "", item.materias || ""]
        .filter(Boolean).join(" · ");
      const article = document.createElement("article");
      article.className = "task";
      article.innerHTML = `<div class="task-content">
        <strong class="task-title">${escapeHtml(item.nome)}</strong>
        <div class="task-subject-line"><span>${escapeHtml(details || "Sem detalhes")}</span></div>
        </div><div class="task-side">
        <button type="button" class="ghost-btn edit-class-btn">Editar</button>
        <button type="button" class="danger-btn delete-class-btn">Excluir</button>
        </div>`;
      $(".edit-class-btn", article).addEventListener("click", () => openClassForm(item.id_turma));
      $(".delete-class-btn", article).addEventListener("click", () => deleteClass(item));
      return article;
    }));
    list.hidden = classes.length === 0;
    $("#classEmpty").hidden = classes.length !== 0;
  }

  function openClassForm(id = null) {
    editingClassId = id;
    const item = classes.find(entry => entry.id_turma === id);
    $("#classFormEyebrow").textContent = item ? "EDITAR TURMA" : "NOVA TURMA";
    $("#classFormTitle").textContent = item ? "Editar turma" : "Criar turma";
    $("#saveClassBtn").textContent = item ? "Salvar alterações" : "Criar turma";
    $("#className").value = item?.nome || "";
    $("#classRoom").value = item?.sala || "";
    $("#classYear").value = item?.ano || "";
    const subjectsFields = $("#classSubjectsFieldsWrap");
    const fieldsList = $("#classSubjectsFields");
    subjectsFields.hidden = Boolean(item);
    fieldsList.replaceChildren();
    if (!item) addClassSubjectField();
    updateClassSubjectButtons();
    $("#classDialog").showModal();
  }

  function addClassSubjectField() {
    const field = document.createElement("div");
    field.innerHTML = '<label data-new-subject-row>Matéria<input type="text" data-new-subject-name maxlength="150"></label>';
    $("#classSubjectsFields").appendChild(field);
    updateClassSubjectButtons();
  }

  function removeClassSubjectField() {
    const fields = $("#classSubjectsFields");
    if (fields.children.length > 1) fields.lastElementChild.remove();
    updateClassSubjectButtons();
  }

  function updateClassSubjectButtons() {
    $("#removeClassSubjectBtn").disabled = $("#classSubjectsFields").children.length <= 1;
  }

  async function saveClass(event) {
    event.preventDefault();
    const currentClass = classes.find(item => item.id_turma === editingClassId);
    const materias = editingClassId ? [] : $$('[data-new-subject-row]', $("#classSubjectsFields")).map(row => ({
      nome: $("[data-new-subject-name]", row).value.trim()
    })).filter(item => item.nome);
    if (!editingClassId && !materias.length) {
      alert("Adicione ao menos uma matéria para criar a turma.");
      return;
    }
    const payload = {
      nome: $("#className").value.trim(),
      sala: $("#classRoom").value.trim() || null,
      ano: $("#classYear").value ? Number($("#classYear").value) : null,
      id_administrado: currentClass?.id_administrado ?? currentAdminId,
      materias
    };
    try {
      await api(editingClassId ? `/api/turmas/${editingClassId}` : "/api/turmas", {
        method: editingClassId ? "PUT" : "POST", body: JSON.stringify(payload)
      });
      $("#classDialog").close();
      editingClassId = null;
      await loadPeople();
    } catch (error) {
      alert(error.message);
    }
  }

  async function deleteClass(item) {
    askAcademicDelete(`A turma ${item.nome}, suas publicações e vínculos serão excluídos. Os alunos permanecerão cadastrados, sem vínculo com esta turma.`, async () => {
      await api(`/api/turmas/${item.id_turma}`, { method: "DELETE" });
      await loadPeople();
    }, "EXCLUIR TURMA");
  }

  function askAcademicDelete(message, action, eyebrow = "DESVINCULAR MATÉRIA") {
    academicDeleteAction = action;
    $("#academicDeleteMessage").textContent = message;
    $("#academicDeleteEyebrow").textContent = eyebrow;
    $("#academicDeleteDialog").showModal();
  }

  function closeAcademicDelete() {
    academicDeleteAction = null;
    $("#academicDeleteDialog").close();
  }

  async function confirmAcademicDelete() {
    if (!academicDeleteAction) return closeAcademicDelete();
    const action = academicDeleteAction;
    try {
      await action();
      closeAcademicDelete();
    } catch (error) {
      alert(error.message);
    }
  }

  function setKind(kind, createOnly) {
    $("#personForm").dataset.kind = kind;
    $$("[data-person-field]").forEach(group => {
      group.hidden = group.dataset.personField !== kind;
    });
    $$("[data-create-only]").forEach(group => { group.hidden = !createOnly; });
    $("#teacherLogin").required = kind === "teacher" && createOnly;
    $("#teacherPassword").required = kind === "teacher" && createOnly;
  }

  function openForm(kind, id = null) {
    editing = id === null ? null : { kind, id };
    const student = kind === "student";
    const item = id === null ? null : (student ? students : teachers).find(person =>
      (student ? person.id_aluno : person.id_professor) === id
    );
    setKind(kind, !item);
    $("#personFormEyebrow").textContent = item ? "EDITAR CADASTRO" : "NOVO CADASTRO";
    $("#personFormTitle").textContent = `${item ? "Editar" : "Novo"} ${student ? "aluno" : "professor"}`;
    $("#savePersonBtn").textContent = item ? "Salvar alterações" : "Criar cadastro";
    $("#personName").value = item?.nome || "";
    $("#personPhone").value = item?.telefone || "";
    $("#studentEmail").value = item?.email || "";
    $("#studentBirth").value = item?.data_nascimento || "";
    $("#studentClass").value = item?.id_turma || "";
    $("#studentCgm").value = "";
    $("#studentPassword").value = "";
    $("#teacherHireDate").value = item?.data_contratacao || "";
    $("#teacherAttribute").value = item?.atributo || "";
    $("#teacherLogin").value = "";
    $("#teacherPassword").value = "";
    $("#personDialog").showModal();
  }

  function closeForm() {
    $("#personDialog").close();
    editing = null;
  }

  function openDelete(kind, id, name) {
    deleting = { kind, id };
    $("#personDeleteMessage").textContent = `O cadastro de ${name} e o acesso vinculado serão removidos.`;
    $("#personDeleteDialog").showModal();
  }

  function closeDelete() {
    deleting = null;
    $("#personDeleteDialog").close();
  }

  async function submitForm(event) {
    event.preventDefault();
    const kind = $("#personForm").dataset.kind;
    const student = kind === "student";
    const payload = student ? {
      nome: $("#personName").value.trim(),
      email: $("#studentEmail").value.trim(),
      telefone: $("#personPhone").value.trim(),
      data_nascimento: $("#studentBirth").value || null,
      id_turma: $("#studentClass").value || null
    } : {
      nome: $("#personName").value.trim(),
      telefone: $("#personPhone").value.trim(),
      data_contratacao: $("#teacherHireDate").value || null,
      atributo: $("#teacherAttribute").value.trim()
    };
    if (!editing) {
      if (student) {
        payload.cgm = $("#studentCgm").value.trim();
        if ($("#studentPassword").value) payload.senha = $("#studentPassword").value;
      } else {
        payload.login = $("#teacherLogin").value.trim();
        payload.senha = $("#teacherPassword").value;
      }
    }
    const base = student ? "/api/alunos" : "/api/professores";
    try {
      await api(editing ? `${base}/${editing.id}` : base, {
        method: editing ? "PUT" : "POST",
        body: JSON.stringify(payload)
      });
      closeForm();
      await loadPeople();
    } catch (error) {
      alert(error.message);
    }
  }

  async function confirmDelete() {
    if (!deleting) return closeDelete();
    const base = deleting.kind === "student" ? "/api/alunos" : "/api/professores";
    try {
      await api(`${base}/${deleting.id}`, { method: "DELETE" });
      closeDelete();
      await loadPeople();
    } catch (error) {
      alert(error.message);
    }
  }

  function showManagement(show) {
    $("#managementSection").hidden = !show;
    $("#eventsView").hidden = show;
    if (show) loadPeople().catch(error => alert(error.message));
  }

  async function init() {
    if (!$("#managementSection")) return;
    const user = await currentUser({ redirectOn401: true });
    if (!user) return;
    if (user.papel !== "adm") return window.location.href = "/login";
    currentAdminId = user.id;

    $("#managementNavLink").addEventListener("click", event => {
      event.preventDefault();
      showManagement(true);
    });
    $("#eventsNavLink").addEventListener("click", event => {
      event.preventDefault();
      showManagement(false);
    });
    if (window.location.hash === "#managementSection") showManagement(true);
    $("#newStudentBtn").addEventListener("click", () => openForm("student"));
    $("#newTeacherBtn").addEventListener("click", () => openForm("teacher"));
    $("#personForm").addEventListener("submit", submitForm);
    $("#closePersonBtn").addEventListener("click", closeForm);
    $("#cancelPersonBtn").addEventListener("click", closeForm);
    $("#closePersonDeleteBtn").addEventListener("click", closeDelete);
    $("#cancelPersonDeleteBtn").addEventListener("click", closeDelete);
    $("#confirmPersonDeleteBtn").addEventListener("click", confirmDelete);
    $("#newClassBtn").addEventListener("click", () => openClassForm());
    $("#classForm").addEventListener("submit", saveClass);
    $("#closeClassBtn").addEventListener("click", () => $("#classDialog").close());
    $("#cancelClassBtn").addEventListener("click", () => $("#classDialog").close());
    $("#addClassSubjectBtn").addEventListener("click", addClassSubjectField);
    $("#removeClassSubjectBtn").addEventListener("click", removeClassSubjectField);
    $("#closeAcademicDeleteBtn").addEventListener("click", closeAcademicDelete);
    $("#cancelAcademicDeleteBtn").addEventListener("click", closeAcademicDelete);
    $("#confirmAcademicDeleteBtn").addEventListener("click", confirmAcademicDelete);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
