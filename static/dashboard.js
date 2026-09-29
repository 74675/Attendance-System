// ======================================================
// CURRENT DATE
// ======================================================

function updateDate() {

    const dateElement =
        document.getElementById("currentDate");

    if (!dateElement) {
        return;
    }

    const now = new Date();

    const options = {
        weekday: "short",
        day: "2-digit",
        month: "short",
        year: "numeric"
    };

    dateElement.textContent =
        now.toLocaleDateString(
            "en-IN",
            options
        );
}


updateDate();


// ======================================================
// SIDEBAR TOGGLE
// ======================================================

function toggleSidebar() {

    const sidebar =
        document.querySelector(".sidebar");

    if (!sidebar) {
        return;
    }

    sidebar.classList.toggle("mobile-open");
}


// ======================================================
// PASSWORD TOGGLE
// ======================================================

function togglePassword(
    inputId,
    button
) {

    const input =
        document.getElementById(inputId);

    if (!input) {
        return;
    }

    if (input.type === "password") {

        input.type = "text";

        button.innerHTML =
            '<i class="fa-solid fa-eye-slash"></i>';

    } else {

        input.type = "password";

        button.innerHTML =
            '<i class="fa-solid fa-eye"></i>';

    }
}


// ======================================================
// FILE NAME
// ======================================================

function showFileName(input) {

    const fileName =
        document.getElementById("file-name");

    if (!fileName) {
        return;
    }

    if (input.files.length > 0) {

        fileName.textContent =
            input.files[0].name;

    } else {

        fileName.textContent =
            "Choose face image";

    }
}


// ======================================================
// TABLE SEARCH
// ======================================================

function filterTable(
    searchInputId,
    tableId
) {

    const input =
        document.getElementById(
            searchInputId
        );

    const table =
        document.getElementById(
            tableId
        );

    if (!input || !table) {
        return;
    }

    const filter =
        input.value.toLowerCase();

    const rows =
        table
        .getElementsByTagName("tbody")[0]
        .getElementsByTagName("tr");

    for (let i = 0; i < rows.length; i++) {

        const text =
            rows[i].textContent
            .toLowerCase();

        if (text.includes(filter)) {

            rows[i].style.display = "";

        } else {

            rows[i].style.display = "none";

        }

    }
}


// ======================================================
// ATTENDANCE PAGE DATE
// ======================================================

const attendanceDate =
    document.getElementById(
        "attendanceDate"
    );

if (attendanceDate) {

    const now = new Date();

    attendanceDate.textContent =
        now.toLocaleDateString(
            "en-IN",
            {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );
}


// ======================================================
// AUTO REMOVE FLASH MESSAGE
// ======================================================

setTimeout(function () {

    const messages =
        document.querySelectorAll(
            ".flash-message"
        );

    messages.forEach(function (message) {

        message.style.opacity = "0";

        message.style.transform =
            "translateY(-10px)";

        setTimeout(function () {
            message.remove();
        }, 300);

    });

}, 5000);


// ======================================================
// CLOSE SIDEBAR ON MOBILE
// ======================================================

document.addEventListener(
    "click",
    function (event) {

        const sidebar =
            document.querySelector(".sidebar");

        const mobileButton =
            document.querySelector(".mobile-menu");

        if (!sidebar || !mobileButton) {
            return;
        }

        if (
            window.innerWidth <= 900 &&
            sidebar.classList.contains("mobile-open") &&
            !sidebar.contains(event.target) &&
            !mobileButton.contains(event.target)
        ) {

            sidebar.classList.remove(
                "mobile-open"
            );

        }

    }
);