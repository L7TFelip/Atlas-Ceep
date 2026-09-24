const STORAGE = {

    tasks: "atlas_tasks_v1",

    notices: "atlas_notices_v1",

    grades: "atlas_grades_v1",

    theme: "atlas_theme_v1",

    events: "atlas_events_v1"

};


/* DADOS INICIAIS */

const defaultTasks = [

    {
        id: 1,
        title: "Redação",
        subject: "Língua Portuguesa",
        done: true
    },

    {
        id: 2,
        title: "Lista de exercícios",
        subject: "Física",
        done: true
    },

    {
        id: 3,
        title: "Projeto final",
        subject: "Desenvolvimento de Sistemas",
        done: false
    },

    {
        id: 4,
        title: "Revisão",
        subject: "Matemática",
        done: false
    }

];


const defaultNotices = [

    {
        id: 1,
        text: "Aula extra de Redação",
        date: "Sexta-feira"
    },

    {
        id: 2,
        text: "Simulado ENEM",
        date: "Sábado"
    }

];


const defaultGrades = [

    ["Português", 7.8],

    ["Matemática", 8.7],

    ["Física", 7.2],

    ["Química", 8.9],

    ["Biologia", 7.7],

    ["DS", 8.3]

];


function getStorage(key, fallback) {

    try {

        const data =
            localStorage.getItem(key);

        return data
            ? JSON.parse(data)
            : fallback;

    } catch {

        return fallback;

    }

}


function saveStorage(key, value) {

    localStorage.setItem(
        key,
        JSON.stringify(value)
    );

}


/* ESTADO */

let tasks =
    getStorage(
        STORAGE.tasks,
        defaultTasks
    );


let notices =
    getStorage(
        STORAGE.notices,
        defaultNotices
    );


let grades =
    getStorage(
        STORAGE.grades,
        defaultGrades
    );


let events =
    getStorage(
        STORAGE.events,
        {}
    );


/* ELEMENTOS */

const taskList =
    document.querySelector("#taskList");

const taskEmpty =
    document.querySelector("#taskEmpty");


/* TAREFAS */

function renderTasks() {

    taskList.innerHTML = "";

    taskEmpty.hidden =
        tasks.length > 0;


    tasks.forEach(task => {

        const row =
            document.createElement("div");


        row.className =
            `task ${task.done ? "done" : ""}`;


        row.innerHTML = `

            <button
                class="check"
                title="Marcar como concluída">

                ${task.done ? "✓" : ""}

            </button>


            <div class="task-content">

                <span class="task-title"></span>

                <span class="task-subject"></span>

            </div>


            <button
                class="delete-btn"
                title="Excluir tarefa">

                ×

            </button>

        `;


        row.querySelector(
            ".task-title"
        ).textContent =
            task.title;


        row.querySelector(
            ".task-subject"
        ).textContent =
            task.subject;


        row.querySelector(
            ".check"
        ).onclick = () => {

            task.done =
                !task.done;

            saveStorage(
                STORAGE.tasks,
                tasks
            );

            renderAll();

        };


        row.querySelector(
            ".delete-btn"
        ).onclick = () => {

            tasks =
                tasks.filter(
                    t => t.id !== task.id
                );

            saveStorage(
                STORAGE.tasks,
                tasks
            );

            renderAll();

        };


        taskList.appendChild(row);

    });


    updateStats();

}


/* ESTATÍSTICAS */

function updateStats() {

    const done =
        tasks.filter(
            task => task.done
        ).length;


    const pending =
        tasks.length - done;


    const progress =
        tasks.length
            ? Math.round(
                done /
                tasks.length *
                100
            )
            : 0;


    const average =
        grades.length
            ? grades.reduce(
                (total, grade) =>
                    total +
                    Number(grade[1]),
                0
            ) / grades.length
            : 0;


    document.querySelector(
        "#doneCount"
    ).textContent =
        done;


    document.querySelector(
        "#pendingCount"
    ).textContent =
        pending;


    document.querySelector(
        "#progressCount"
    ).textContent =
        progress + "%";


    document.querySelector(
        "#averageCount"
    ).textContent =
        average
            .toFixed(1)
            .replace(".", ",");

}


/* GRÁFICO */

function renderGrades() {

    const bars =
        document.querySelector("#bars");

    bars.innerHTML = "";


    grades.forEach(
        ([name, value]) => {

            const wrap =
                document.createElement("div");


            wrap.className =
                "bar-wrap";


            const height =
                Math.max(
                    8,
                    Math.min(
                        100,
                        Number(value) * 10
                    )
                );


            wrap.innerHTML = `

                <span class="bar-value">
                    ${Number(value).toFixed(1)}
                </span>

                <div
                    class="bar"
                    style="height:${height}%">
                </div>

                <span class="bar-label">
                    ${name}
                </span>

            `;


            bars.appendChild(wrap);

        }
    );

}


/* AVISOS */

function renderNotices() {

    const list =
        document.querySelector(
            "#noticeList"
        );


    list.innerHTML = "";


    notices.forEach(notice => {

        const item =
            document.createElement("div");


        item.className =
            "notice";


        item.innerHTML = `

            <span class="pin">
                ⌖
            </span>

            <div class="notice-text">

                <div class="notice-message">
                </div>

                <div class="notice-date">
                </div>

            </div>

            <button
                class="notice-remove"
                title="Excluir aviso">

                ×

            </button>

        `;


        item.querySelector(
            ".notice-message"
        ).textContent =
            notice.text;


        item.querySelector(
            ".notice-date"
        ).textContent =
            notice.date || "";


        item.querySelector(
            ".notice-remove"
        ).onclick = () => {

            notices =
                notices.filter(
                    item =>
                        item.id !== notice.id
                );


            saveStorage(
                STORAGE.notices,
                notices
            );


            renderNotices();

        };


        list.appendChild(item);

    });

}


/* CALENDÁRIO */

let viewDate =
    new Date();


let selectedDate =
    new Date();


function dateKey(date) {

    return `${date.getFullYear()}-${String(
        date.getMonth() + 1
    ).padStart(2, "0")}-${String(
        date.getDate()
    ).padStart(2, "0")}`;

}


function renderCalendar() {

    const calendar =
        document.querySelector(
            "#calendar"
        );


    const monthLabel =
        document.querySelector(
            "#monthLabel"
        );


    calendar.innerHTML = "";


    const year =
        viewDate.getFullYear();


    const month =
        viewDate.getMonth();


    monthLabel.textContent =
        viewDate.toLocaleDateString(
            "pt-BR",
            {
                month: "long",
                year: "numeric"
            }
        );


    const firstDay =
        new Date(
            year,
            month,
            1
        ).getDay();


    const days =
        new Date(
            year,
            month + 1,
            0
        ).getDate();


    for (
        let i = 0;
        i < firstDay;
        i++
    ) {

        const blank =
            document.createElement("div");

        blank.className =
            "day empty";

        calendar.appendChild(blank);

    }


    const today =
        dateKey(new Date());


    for (
        let day = 1;
        day <= days;
        day++
    ) {

        const date =
            new Date(
                year,
                month,
                day
            );


        const key =
            dateKey(date);


        const element =
            document.createElement("button");


        element.className =
            "day";


        if (key === today) {

            element.classList.add(
                "today"
            );

        }


        if (
            key ===
            dateKey(selectedDate)
        ) {

            element.classList.add(
                "selected"
            );

        }


        if (
            events[key] &&
            events[key].length
        ) {

            element.classList.add(
                "has-event"
            );

        }


        element.textContent =
            day;


        element.onclick = () => {

            selectedDate =
                date;

            renderCalendar();

            renderSelectedEvents();

        };


        calendar.appendChild(
            element
        );

    }


    renderSelectedEvents();

}


function renderSelectedEvents() {

    const key =
        dateKey(selectedDate);


    const box =
        document.querySelector(
            "#selectedEvents"
        );


    const eventList =
        events[key] || [];


    if (eventList.length) {

        box.innerHTML =
            `<strong>
                ${selectedDate.toLocaleDateString("pt-BR")}
            </strong>: ${eventList.join(" • ")}`;

    } else {

        box.textContent =
            `Nenhum evento em ${
                selectedDate.toLocaleDateString("pt-BR")
            }.`;

    }

}


/* MODAIS */

function openDialog(id) {

    document
        .querySelector("#" + id)
        .showModal();

}


function closeDialog(id) {

    document
        .querySelector("#" + id)
        .close();

}


/* ABRIR TAREFA */

document.querySelector(
    "#addTaskBtn"
).onclick = () => {

    openDialog(
        "taskDialog"
    );

};


document.querySelector(
    "#emptyAddBtn"
).onclick = () => {

    openDialog(
        "taskDialog"
    );

};


/* ADICIONAR TAREFA */

document.querySelector(
    "#taskForm"
).onsubmit = event => {

    event.preventDefault();


    const title =
        document.querySelector(
            "#taskTitle"
        ).value.trim();


    const subject =
        document.querySelector(
            "#taskSubject"
        ).value;


    tasks.push({

        id: Date.now(),

        title,

        subject,

        done: false

    });


    saveStorage(
        STORAGE.tasks,
        tasks
    );


    event.target.reset();


    closeDialog(
        "taskDialog"
    );


    renderAll();

};


/* LIMPAR CONCLUÍDAS */

document.querySelector(
    "#clearDoneBtn"
).onclick = () => {

    tasks =
        tasks.filter(
            task => !task.done
        );


    saveStorage(
        STORAGE.tasks,
        tasks
    );


    renderAll();

};


/* AVISOS */

document.querySelector(
    "#addNoticeBtn"
).onclick = () => {

    openDialog(
        "noticeDialog"
    );

};


document.querySelector(
    "#noticeForm"
).onsubmit = event => {

    event.preventDefault();


    const title =
        document.querySelector(
            "#noticeTitle"
        ).value.trim();


    const date =
        document.querySelector(
            "#noticeDate"
        ).value;


    notices.unshift({

        id: Date.now(),

        text: title,

        date: date
            ? new Date(
                date + "T12:00:00"
              ).toLocaleDateString(
                "pt-BR"
              )
            : "Sem data"

    });


    saveStorage(
        STORAGE.notices,
        notices
    );


    event.target.reset();


    closeDialog(
        "noticeDialog"
    );


    renderNotices();

};


/* EDITAR NOTAS */

document.querySelector(
    "#editGradesBtn"
).onclick = () => {

    const box =
        document.querySelector(
            "#gradeInputs"
        );


    box.innerHTML = "";


    grades.forEach(
        ([name, value], index) => {

            const label =
                document.createElement(
                    "span"
                );


            label.textContent =
                name;


            const input =
                document.createElement(
                    "input"
                );


            input.type =
                "number";


            input.min = 0;

            input.max = 10;

            input.step = 0.1;

            input.value = value;

            input.dataset.index =
                index;


            box.append(
                label,
                input
            );

        }
    );


    openDialog(
        "gradesDialog"
    );

};


/* SALVAR NOTAS */

document.querySelector(
    "#gradesForm"
).onsubmit = event => {

    event.preventDefault();


    document.querySelectorAll(
        "#gradeInputs input"
    ).forEach(input => {

        const index =
            Number(
                input.dataset.index
            );


        grades[index][1] =
            Math.max(
                0,
                Math.min(
                    10,
                    Number(input.value) || 0
                )
            );

    });


    saveStorage(
        STORAGE.grades,
        grades
    );


    closeDialog(
        "gradesDialog"
    );


    renderGrades();

    updateStats();

};


/* FECHAR MODAIS */

document
    .querySelectorAll(
        "[data-close]"
    )
    .forEach(button => {

        button.onclick = () => {

            closeDialog(
                button.dataset.close
            );

        };

    });


/* CALENDÁRIO */

document.querySelector(
    "#prevMonth"
).onclick = () => {

    viewDate.setMonth(
        viewDate.getMonth() - 1
    );

    renderCalendar();

};


document.querySelector(
    "#nextMonth"
).onclick = () => {

    viewDate.setMonth(
        viewDate.getMonth() + 1
    );

    renderCalendar();

};


/* TEMA */

document.querySelector(
    "#themeBtn"
).onclick = () => {

    const root =
        document.documentElement;


    const nextTheme =
        root.dataset.theme === "dark"
            ? "light"
            : "dark";


    root.dataset.theme =
        nextTheme;


    localStorage.setItem(
        STORAGE.theme,
        nextTheme
    );


    document.querySelector(
        "#themeBtn"
    ).textContent =
        nextTheme === "dark"
            ? "☼"
            : "☾";

};


/* PERFIL */

document.querySelector(
    "#profileBtn"
).onclick = () => {

    alert(
        "Perfil do aluno\n\n" +
        "Felipe Neves\n" +
        "3º ano • Desenvolvimento de Sistemas"
    );

};


/* TEMA SALVO */

const savedTheme =
    localStorage.getItem(
        STORAGE.theme
    ) || "dark";


document.documentElement.dataset.theme =
    savedTheme;


document.querySelector(
    "#themeBtn"
).textContent =
    savedTheme === "dark"
        ? "☼"
        : "☾";


/* RENDERIZAÇÃO */

function renderAll() {

    renderTasks();

    renderGrades();

    renderNotices();

    renderCalendar();

}


renderAll();