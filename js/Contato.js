document.addEventListener("DOMContentLoaded", () => {

    /* =========================================
       LUCIDE
    ========================================= */

    if (window.lucide) {
        lucide.createIcons();
    }


    /* =========================================
       TEMA
    ========================================= */

    const html = document.documentElement;

    const themeButtons =
        document.querySelectorAll(
            "[data-theme-toggle]"
        );


    function updateThemeIcons() {

        if (!window.lucide) return;

        themeButtons.forEach(button => {

            const icon =
                button.querySelector(
                    "[data-lucide]"
                );

            if (!icon) return;

            icon.setAttribute(
                "data-lucide",
                html.getAttribute("data-theme") === "dark"
                    ? "sun"
                    : "moon"
            );

        });

        lucide.createIcons();
    }


    function toggleTheme() {

        const current =
            html.getAttribute("data-theme");

        const next =
            current === "dark"
                ? "light"
                : "dark";

        html.setAttribute(
            "data-theme",
            next
        );

        localStorage.setItem(
            "atlas-theme",
            next
        );

        updateThemeIcons();
    }


    themeButtons.forEach(button => {

        button.addEventListener(
            "click",
            toggleTheme
        );

    });


    const savedTheme =
        localStorage.getItem("atlas-theme");

    if (savedTheme) {

        html.setAttribute(
            "data-theme",
            savedTheme
        );

    }

    updateThemeIcons();


    /* =========================================
       LUZ DO MOUSE
    ========================================= */

    const contactPage =
        document.querySelector(
            ".contact-page"
        );


    if (contactPage) {

        contactPage.addEventListener(
            "mousemove",
            event => {

                const rect =
                    contactPage.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;

                contactPage.style.setProperty(
                    "--mouse-x",
                    `${x}px`
                );

                contactPage.style.setProperty(
                    "--mouse-y",
                    `${y}px`
                );

            }
        );

    }


    /* =========================================
       HEADER
    ========================================= */

    const header =
        document.getElementById(
            "site-header"
        );


    function updateHeader() {

        if (!header) return;

        if (window.scrollY > 30) {

            header.classList.add(
                "scrolled"
            );

        } else {

            header.classList.remove(
                "scrolled"
            );

        }

    }


    window.addEventListener(
        "scroll",
        updateHeader
    );

    updateHeader();


    /* =========================================
       MENU MOBILE
    ========================================= */

    const burger =
        document.querySelector(
            "[data-burger]"
        );

    const mobileMenu =
        document.querySelector(
            "[data-mobile-menu]"
        );

    const overlay =
        document.querySelector(
            "[data-overlay]"
        );

    const closeLinks =
        document.querySelectorAll(
            "[data-close]"
        );


    function openMenu() {

        mobileMenu?.classList.add("open");

        overlay?.classList.add("open");

        document.body.classList.add(
            "menu-open"
        );

    }


    function closeMenu() {

        mobileMenu?.classList.remove("open");

        overlay?.classList.remove("open");

        document.body.classList.remove(
            "menu-open"
        );

    }


    burger?.addEventListener(
        "click",
        openMenu
    );


    overlay?.addEventListener(
        "click",
        closeMenu
    );


    closeLinks.forEach(link => {

        link.addEventListener(
            "click",
            closeMenu
        );

    });


    /* =========================================
       FORMULÁRIO
    ========================================= */

    const form =
        document.getElementById(
            "contact-form"
        );

    if (form) {

        const nome =
            document.getElementById(
                "nome"
            );

        const email =
            document.getElementById(
                "email"
            );

        const telefone =
            document.getElementById(
                "telefone"
            );

        const curso =
            document.getElementById(
                "curso"
            );

        const mensagem =
            document.getElementById(
                "mensagem"
            );


        const nomeError =
            document.getElementById(
                "nomeError"
            );

        const emailError =
            document.getElementById(
                "emailError"
            );

        const telefoneError =
            document.getElementById(
                "telefoneError"
            );

        const mensagemError =
            document.getElementById(
                "mensagemError"
            );

        const success =
            document.getElementById(
                "formSuccess"
            );


        /* =====================================
           LIMPAR ERROS
        ===================================== */

        function clearErrors() {

            document
                .querySelectorAll(
                    ".form-group"
                )
                .forEach(group => {

                    group.classList.remove(
                        "has-error"
                    );

                });


            if (nomeError)
                nomeError.textContent = "";

            if (emailError)
                emailError.textContent = "";

            if (telefoneError)
                telefoneError.textContent = "";

            if (mensagemError)
                mensagemError.textContent = "";

        }


        /* =====================================
           EMAIL
        ===================================== */

        function validEmail(value) {

            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                .test(value);

        }


        /* =====================================
           TELEFONE
        ===================================== */

        telefone?.addEventListener(
            "input",
            () => {

                let value =
                    telefone.value
                        .replace(/\D/g, "")
                        .slice(0, 11);


                if (value.length > 10) {

                    value =
                        value.replace(
                            /^(\d{2})(\d{5})(\d{4})$/,
                            "($1) $2-$3"
                        );

                } else if (value.length > 6) {

                    value =
                        value.replace(
                            /^(\d{2})(\d{4})(\d{0,4})$/,
                            "($1) $2-$3"
                        );

                } else if (value.length > 2) {

                    value =
                        value.replace(
                            /^(\d{2})(\d{0,5})$/,
                            "($1) $2"
                        );

                }

                telefone.value = value;

            }
        );


        /* =====================================
           VALIDAÇÃO
        ===================================== */

        function validateForm() {

            clearErrors();

            let valid = true;


            /* NOME */

            if (!nome.value.trim()) {

                nomeError.textContent =
                    "Informe seu nome.";

                nome
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            } else if (
                nome.value.trim().length < 3
            ) {

                nomeError.textContent =
                    "Digite seu nome completo.";

                nome
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            }


            /* EMAIL */

            if (!email.value.trim()) {

                emailError.textContent =
                    "Informe seu e-mail.";

                email
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            } else if (
                !validEmail(
                    email.value.trim()
                )
            ) {

                emailError.textContent =
                    "Digite um e-mail válido.";

                email
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            }


            /* TELEFONE */

            if (
                telefone.value.trim() &&
                telefone.value.replace(
                    /\D/g,
                    ""
                ).length < 10
            ) {

                telefoneError.textContent =
                    "Digite um telefone válido.";

                telefone
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            }


            /* MENSAGEM */

            if (!mensagem.value.trim()) {

                mensagemError.textContent =
                    "Digite uma mensagem.";

                mensagem
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            } else if (
                mensagem.value.trim().length < 10
            ) {

                mensagemError.textContent =
                    "Sua mensagem precisa ter pelo menos 10 caracteres.";

                mensagem
                    .closest(".form-group")
                    .classList.add(
                        "has-error"
                    );

                valid = false;

            }


            return valid;

        }


        /* =====================================
           ENVIO
        ===================================== */

        form.addEventListener(
            "submit",
            event => {

                event.preventDefault();


                if (!validateForm()) {

                    const firstError =
                        form.querySelector(
                            ".has-error input, .has-error textarea, .has-error select"
                        );

                    firstError?.focus();

                    return;

                }


                /* Dados do formulário */

                const dados = {

                    nome:
                        nome.value.trim(),

                    email:
                        email.value.trim(),

                    telefone:
                        telefone.value.trim(),

                    curso:
                        curso.value,

                    mensagem:
                        mensagem.value.trim()

                };


                console.log(
                    "Dados do formulário:",
                    dados
                );


                /* Mostrar sucesso */

                success.classList.add(
                    "show"
                );


                form.reset();


                success.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest"
                });


                setTimeout(() => {

                    success.classList.remove(
                        "show"
                    );

                }, 6000);

            }
        );


        /* =====================================
           REMOVER ERROS AO DIGITAR
        ===================================== */

        [
            nome,
            email,
            telefone,
            mensagem
        ].forEach(field => {

            field?.addEventListener(
                "input",
                () => {

                    const group =
                        field.closest(
                            ".form-group"
                        );

                    group?.classList.remove(
                        "has-error"
                    );


                    const error =
                        document.getElementById(
                            `${field.id}Error`
                        );

                    if (error) {

                        error.textContent = "";

                    }

                }
            );

        });

    }


    /* =========================================
       ABAS DOS CURSOS
    ========================================= */

    const tabs =
        document.querySelectorAll(
            ".course-tab"
        );

    const courses =
        document.querySelectorAll(
            ".course-card"
        );


    tabs.forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                const category =
                    tab.dataset.category;


                tabs.forEach(item => {

                    item.classList.remove(
                        "active"
                    );

                });


                tab.classList.add(
                    "active"
                );


                courses.forEach(course => {

                    if (
                        course.dataset.category ===
                        category
                    ) {

                        course.classList.remove(
                            "hidden"
                        );

                    } else {

                        course.classList.add(
                            "hidden"
                        );

                    }

                });

            }
        );

    });

});
