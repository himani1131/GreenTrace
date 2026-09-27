/* =====================================================
   GREENTRACE JAVASCRIPT
===================================================== */


/* =====================================================
   SPLASH SCREEN
===================================================== */

window.addEventListener("load", function () {

    const splash = document.getElementById("splashScreen");

    setTimeout(function () {

        splash.classList.add("hide");

    }, 2500);

});



/* =====================================================
   PAGE NAVIGATION
===================================================== */

const pageTitles = {

    dashboard: [
        "Dashboard",
        "Monitor your software's energy impact."
    ],

    analyze: [
        "Analyze Code",
        "Analyze source code and detect inefficient patterns."
    ],

    results: [
        "Analysis Results",
        "View detected issues and performance indicators."
    ],

    optimization: [
        "Optimization",
        "Compare original and optimized source code."
    ],

    validation: [
        "Functional Validation",
        "Verify that optimization preserves expected output."
    ],

    comparison: [
        "Impact Comparison",
        "Compare performance, energy and estimated carbon."
    ],

    history: [
        "Analysis History",
        "Review previous GreenTrace analyses."
    ],

    reports: [
        "Reports",
        "Generate GreenTrace analysis reports."
    ],

    settings: [
        "Settings",
        "Customize your GreenTrace experience."
    ]

};



function showPage(pageId, clickedButton) {

    const pages =
        document.querySelectorAll(".page");

    pages.forEach(function (page) {

        page.classList.remove("active-page");

    });


    const selectedPage =
        document.getElementById(pageId);

    if (selectedPage) {

        selectedPage.classList.add("active-page");

    }


    const navItems =
        document.querySelectorAll(".nav-item");

    navItems.forEach(function (item) {

        item.classList.remove("active");

    });


    if (clickedButton) {

        clickedButton.classList.add("active");

    }
    else {

        const matchingButton =
            document.querySelector(
                `.nav-item[onclick*="'${pageId}'"]`
            );

        if (matchingButton) {

            matchingButton.classList.add("active");

        }

    }


    if (pageTitles[pageId]) {

        document.getElementById("pageTitle").textContent =
            pageTitles[pageId][0];

        document.getElementById("pageSubtitle").textContent =
            pageTitles[pageId][1];

    }


    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}



function showPageByName(pageId) {

    showPage(pageId);

}



/* =====================================================
   EXAMPLE CODE
===================================================== */

const exampleCode = `numbers = [1, 2, 3, 4, 5]

result = []

for number in numbers:
    square = number * number
    result.append(square)

print(result)`;


const optimizedExampleCode = `numbers = [1, 2, 3, 4, 5]

result = [number * number for number in numbers]

print(result)`;



function loadExampleCode() {

    const editor =
        document.getElementById("codeInput");

    editor.value = exampleCode;

    updateCodeInfo();

    showNotification(
        "Example Python code loaded."
    );

}



/* =====================================================
   CLEAR CODE
===================================================== */

function clearEditor() {

    const editor =
        document.getElementById("codeInput");

    editor.value = "";

    updateCodeInfo();

    showNotification(
        "Code editor cleared."
    );

}



/* =====================================================
   CODE INFORMATION
===================================================== */

function updateCodeInfo() {

    const editor =
        document.getElementById("codeInput");

    const language =
        document.getElementById("languageSelect").value;

    const lines =
        editor.value === ""
            ? 0
            : editor.value.split("\n").length;


    const languageName = {

        python: "Python",

        cpp: "C++",

        javascript: "JavaScript"

    };


    document.getElementById("codeInfo").textContent =
        `${languageName[language]} • ${lines} lines`;

}



document.addEventListener(
    "DOMContentLoaded",
    function () {

        const editor =
            document.getElementById("codeInput");

        if (editor) {

            editor.addEventListener(
                "input",
                updateCodeInfo
            );

        }

    }
);



/* =====================================================
   LANGUAGE
===================================================== */

function changeLanguage() {

    updateCodeInfo();

    const language =
        document.getElementById("languageSelect").value;


    document.getElementById(
        "optimizationLanguage"
    ).textContent =
        language === "python"
            ? "Python"
            : language === "cpp"
                ? "C++"
                : "JavaScript";


    showNotification(
        "Language changed."
    );

}



/* =====================================================
   FILE UPLOAD
===================================================== */

function uploadCode() {

    document.getElementById(
        "codeFile"
    ).click();

}



function handleFileUpload(event) {

    const file =
        event.target.files[0];

    if (!file) {

        return;

    }


    const reader =
        new FileReader();


    reader.onload = function (e) {

        document.getElementById(
            "codeInput"
        ).value = e.target.result;

        updateCodeInfo();

        showNotification(
            file.name + " loaded successfully."
        );

    };


    reader.readAsText(file);

}



/* =====================================================
   RUN ANALYSIS
===================================================== */

function runAnalysis() {

    const code =
        document.getElementById(
            "codeInput"
        ).value.trim();


    if (!code) {

        showNotification(
            "Please enter or upload source code first."
        );

        return;

    }


    showNotification(
        "Analyzing source code..."
    );


    setTimeout(function () {

        populateOptimization();

        showPageByName("results");

        showNotification(
            "Analysis completed successfully."
        );

    }, 800);

}



/* =====================================================
   OPTIMIZATION DATA
===================================================== */

function populateOptimization() {

    const original =
        document.getElementById(
            "originalCode"
        );

    const optimized =
        document.getElementById(
            "optimizedCode"
        );


    original.textContent =
        exampleCode;

    optimized.textContent =
        optimizedExampleCode;


    createLineNumbers(
        "originalNumbers",
        exampleCode
    );


    createLineNumbers(
        "optimizedNumbers",
        optimizedExampleCode
    );


    document.getElementById(
        "originalLineCount"
    ).textContent =
        exampleCode.split("\n").length;


    document.getElementById(
        "optimizationLanguage"
    ).textContent =
        "Python";

}



/* =====================================================
   CORRECT LINE NUMBERS
===================================================== */

function createLineNumbers(
    containerId,
    code
) {

    const container =
        document.getElementById(
            containerId
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    const lines =
        code.split("\n");


    lines.forEach(function (
        line,
        index
    ) {

        const number =
            document.createElement("span");


        number.textContent =
            index + 1;


        container.appendChild(
            number
        );

    });

}



/* =====================================================
   SCALE IMPACT SIMULATOR
===================================================== */

function updateScale(executions) {

    const energySavedPerRun =
        0.007;


    const carbonSavedPerRun =
        0.000003;


    const energy =
        energySavedPerRun *
        executions;


    const carbon =
        carbonSavedPerRun *
        executions;


    document.getElementById(
        "scaleEnergy"
    ).textContent =
        formatEnergy(energy);


    document.getElementById(
        "scaleCarbon"
    ).textContent =
        formatCarbon(carbon);

}



function formatEnergy(value) {

    if (value < 1) {

        return value.toFixed(3) + " Wh";

    }


    if (value < 1000) {

        return value.toFixed(1) + " Wh";

    }


    return (
        value / 1000
    ).toFixed(2) + " kWh";

}



function formatCarbon(value) {

    if (value < 1) {

        return value.toFixed(3) + " g";

    }


    if (value < 1000) {

        return value.toFixed(1) + " g";

    }


    return (
        value / 1000
    ).toFixed(2) + " kg";

}



/* =====================================================
   REPORT
===================================================== */

function generateReport() {

    showNotification(
        "GreenTrace report prepared successfully."
    );

}



/* =====================================================
   DARK / LIGHT MODE
===================================================== */

function setTheme(theme) {

    const body =
        document.body;

    if (theme === "light") {

        body.classList.add(
            "light-mode"
        );

        localStorage.setItem(
            "greentrace-theme",
            "light"
        );

    }
    else {

        body.classList.remove(
            "light-mode"
        );

        localStorage.setItem(
            "greentrace-theme",
            "dark"
        );

    }


    updateThemeButton();

    updateThemeSelector();

}



/* =====================================================
   TOGGLE THEME
===================================================== */

function toggleTheme() {

    const isLight =
        document.body.classList.contains(
            "light-mode"
        );


    setTheme(
        isLight
            ? "dark"
            : "light"
    );

}



/* =====================================================
   UPDATE THEME BUTTON
===================================================== */

function updateThemeButton() {

    const button =
        document.getElementById(
            "themeButton"
        );


    if (!button) {

        return;

    }


    const isLight =
        document.body.classList.contains(
            "light-mode"
        );


    if (isLight) {

        button.textContent =
            "☀ Light";

    }
    else {

        button.textContent =
            "🌙 Dark";

    }

}



/* =====================================================
   SETTINGS THEME BUTTONS
===================================================== */

function updateThemeSelector() {

    const darkButton =
        document.getElementById(
            "darkModeButton"
        );

    const lightButton =
        document.getElementById(
            "lightModeButton"
        );


    if (!darkButton || !lightButton) {

        return;

    }


    const isLight =
        document.body.classList.contains(
            "light-mode"
        );


    darkButton.classList.toggle(
        "active",
        !isLight
    );


    lightButton.classList.toggle(
        "active",
        isLight
    );

}



/* =====================================================
   LOAD SAVED THEME
===================================================== */

function loadTheme() {

    const savedTheme =
        localStorage.getItem(
            "greentrace-theme"
        );


    if (savedTheme === "light") {

        setTheme("light");

    }
    else {

        setTheme("dark");

    }

}



/* =====================================================
   NOTIFICATION
===================================================== */

function showNotification(message) {

    let notification =
        document.getElementById(
            "greenNotification"
        );


    if (!notification) {

        notification =
            document.createElement(
                "div"
            );


        notification.id =
            "greenNotification";


        notification.style.position =
            "fixed";

        notification.style.right =
            "25px";

        notification.style.bottom =
            "25px";

        notification.style.padding =
            "12px 18px";

        notification.style.borderRadius =
            "9px";

        notification.style.background =
            "#55d98b";

        notification.style.color =
            "#042512";

        notification.style.fontSize =
            "12px";

        notification.style.fontWeight =
            "700";

        notification.style.zIndex =
            "10000";

        notification.style.boxShadow =
            "0 10px 30px rgba(0,0,0,0.25)";


        document.body.appendChild(
            notification
        );

    }


    notification.textContent =
        message;


    notification.style.opacity =
        "1";


    clearTimeout(
        window.greenNotificationTimer
    );


    window.greenNotificationTimer =
        setTimeout(function () {

            notification.style.opacity =
                "0";

        }, 2500);

}



/* =====================================================
   INITIALIZE
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadTheme();

        populateOptimization();

        updateCodeInfo();

    }
);


/* =====================================================
   KEYBOARD SHORTCUT
   Ctrl + Enter = Analyze
===================================================== */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {

            event.preventDefault();

            runAnalysis();

        }

    }
);