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


const examples = [

    {
        code: `numbers = [1, 2, 3, 4, 5]

result = []

for number in numbers:
    square = number * number
    result.append(square)

print(result)`,

        tests: ""
    },


    {
        code: `def find_pairs(nums, target):
    result = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                result.append((nums[i], nums[j]))
    return result

nums = list(range(1, 1501))
print(len(find_pairs(nums, 1500)))`,

        tests: `find_pairs([1, 2, 3, 4, 5], 6)
find_pairs([], 3)
find_pairs([3, 3, 3], 6)
find_pairs([-1, 1, 0], 0)`
    },


    {
        code: `def total_cost(prices, tax, discount):
    total = 0
    for price in prices:
        total += price * (1 + tax) * (1 - discount)
    return total

prices = list(range(1, 200001))
print(total_cost(prices, 0.18, 0.1))`,

        tests: `total_cost([1, 2, 3], 0.1, 0.2)
total_cost([], 0.1, 0.2)
total_cost([100], 0, 0)`
    }

];


let exampleIndex = 0;



function loadExampleCode() {

    const example =
        examples[exampleIndex % examples.length];

    exampleIndex++;


    document.getElementById("codeInput").value =
        example.code;

    document.getElementById("testInput").value =
        example.tests;


    updateCodeInfo();

    showNotification(
        "Example " +
        (((exampleIndex - 1) % examples.length) + 1) +
        " of " + examples.length + " loaded. Click Example again for the next one."
    );

}



/* =====================================================
   CLEAR CODE
===================================================== */


function clearEditor() {

    document.getElementById("codeInput").value = "";

    document.getElementById("testInput").value = "";

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


let lastResult = null;

let currentScale = 1000000;



function getModules() {

    return {

        static: document.getElementById("staticCheck").checked,

        complexity: document.getElementById("complexityCheck").checked,

        optimization: document.getElementById("optimizationCheck").checked,

        benchmark: document.getElementById("benchmarkCheck").checked,

        energy: document.getElementById("energyCheck").checked,

        carbon: document.getElementById("carbonCheck").checked

    };

}



function getTests() {

    return document.getElementById("testInput").value
        .split("\n")
        .map(function (line) { return line.trim(); })
        .filter(function (line) { return line !== ""; });

}



async function runAnalysis() {

    const code =
        document.getElementById("codeInput").value.trim();

    const language =
        document.getElementById("languageSelect").value;

    const button =
        document.querySelector(".analyze-button");


    if (!code) {

        showNotification(
            "Please enter or upload source code first."
        );

        return;

    }


    if (language !== "python") {

        showNotification(
            "This version analyzes Python only. C++ and JavaScript are planned for a later phase."
        );

        return;

    }


    showNotification(
        "Running and analyzing your code..."
    );

    button.disabled = true;


    try {

        const response = await fetch("/api/analyze", {

            method: "POST",

            headers: { "Content-Type": "application/json" },

            body: JSON.stringify({

                code: document.getElementById("codeInput").value,

                language: language,

                tests: getTests(),

                modules: getModules(),

                hardware: document.getElementById("hardwareSelect").value,

                region: document.getElementById("regionSelect").value

            })

        });


        const data = await response.json();


        if (!response.ok) {

            showNotification(data.error);

        }
        else {

            showResult(data);

            showPageByName("results");

            showNotification(
                data.status === "Rejected"
                    ? "A rewrite was found but rejected by validation."
                    : "Analysis completed successfully."
            );

            loadStats();

            loadHistory();

        }

    }
    catch (error) {

        showNotification(
            "Could not reach the GreenTrace backend. Start it with: python app.py"
        );

    }


    button.disabled = false;

}



/* =====================================================
   OPTIMIZATION DATA
===================================================== */


function setText(id, text) {

    document.getElementById(id).textContent = text;

}



function orDash(value, formatter) {

    if (value === null || value === undefined) {

        return "—";

    }

    return formatter(value);

}



function formatTime(seconds) {

    if (seconds >= 1) {

        return seconds.toFixed(2) + " s";

    }

    if (seconds >= 0.001) {

        return (seconds * 1000).toFixed(2) + " ms";

    }

    return (seconds * 1000000).toFixed(1) + " µs";

}



function formatChange(percent) {

    if (percent === null || percent === undefined) {

        return "—";

    }

    if (Math.abs(percent) < 0.05) {

        return "No measurable change";

    }

    if (percent > 0) {

        return percent.toFixed(1) + "% reduction";

    }

    return (-percent).toFixed(1) + "% increase";

}



/* ---------- show one finished analysis on every page ---------- */

function showResult(data) {

    lastResult = data;

    const o = data.original;

    const n = data.optimized;

    const c = data.comparison;


    /* Results page */

    setText("runtimeResult", orDash(o.runtime_s, formatTime));

    setText("cpuResult", orDash(o.cpu_s, formatTime));

    setText("energyResult", orDash(o.energy_wh, formatEnergy));

    setText("carbonResult", orDash(o.co2_g, formatCarbon));

    setText("scoreValue", o.score);

    renderIssues(o.findings);


    if (o.complexity) {

        setText(
            "scoreNote",
            "Time " + o.complexity.time +
            " • Space " + o.complexity.space +
            " • Grade " + o.complexity.grade
        );

    }
    else {

        setText("scoreNote", "Complexity analysis was switched off.");

    }


    /* Optimization page */

    document.getElementById("originalCode").textContent = o.code;

    document.getElementById("optimizedCode").textContent = n.code;

    createLineNumbers("originalNumbers", o.code);

    createLineNumbers("optimizedNumbers", n.code);

    setText("originalLineCount", o.code.split("\n").length);

    setText("optimizationLanguage", "Python");

    renderOptimization(data);


    /* Validation page */

    renderValidation(data);


    /* Comparison page */

    setText("cmpRuntimeOld", orDash(o.runtime_s, formatTime));
    setText("cmpRuntimeNew", orDash(n.runtime_s, formatTime));
    setText("cmpRuntimeNote", formatChange(c.runtime_pct));

    setText("cmpCpuOld", orDash(o.cpu_s, formatTime));
    setText("cmpCpuNew", orDash(n.cpu_s, formatTime));
    setText("cmpCpuNote", formatChange(c.cpu_pct));

    setText("cmpEnergyOld", orDash(o.energy_wh, formatEnergy));
    setText("cmpEnergyNew", orDash(n.energy_wh, formatEnergy));
    setText("cmpEnergyNote", formatChange(c.energy_pct));

    setText("cmpCarbonOld", orDash(o.co2_g, formatCarbon));
    setText("cmpCarbonNew", orDash(n.co2_g, formatCarbon));
    setText("cmpCarbonNote", formatChange(c.co2_pct));


    updateScale(currentScale);

}



function renderIssues(findings) {

    const list = document.getElementById("issueList");

    list.innerHTML = "";


    let highest = "none";

    const rank = { none: 0, low: 1, medium: 2, high: 3 };


    if (!findings || findings.length === 0) {

        const empty = document.createElement("p");

        empty.className = "empty-note";

        empty.textContent = "No inefficient patterns were detected.";

        list.appendChild(empty);

    }


    (findings || []).forEach(function (f) {

        if (rank[f.severity] > rank[highest]) {

            highest = f.severity;

        }


        const item = document.createElement("div");

        item.className = "issue-item";


        const tag = document.createElement("span");

        tag.className = "severity " + f.severity;

        tag.textContent = f.severity.toUpperCase() + " • line " + f.line;


        const title = document.createElement("h4");

        title.textContent = f.title;


        const message = document.createElement("p");

        message.textContent = f.message;


        const box = document.createElement("div");

        box.className = "explanation";


        const label = document.createElement("strong");

        label.textContent = "Why is this inefficient?";


        const why = document.createElement("p");

        why.textContent = f.why;


        box.appendChild(label);

        box.appendChild(why);

        item.appendChild(tag);

        item.appendChild(title);

        item.appendChild(message);

        item.appendChild(box);

        list.appendChild(item);

    });


    const severityTag = document.getElementById("severityTag");

    severityTag.className = "severity " + highest;

    severityTag.textContent = highest === "none" ? "CLEAN" : highest.toUpperCase();

}



function renderOptimization(data) {

    const applied = data.applied;

    const valid = data.validation.status === "VALID";


    if (applied.length > 0) {

        setText("optBadge", "✓ Validated Optimization");

        setText("optName", applied.length === 1 ? "1 rewrite" : applied.length + " rewrites");

        setText("optConfidence", valid ? "High" : "Low");

        setText("optTitle", applied.map(function (a) { return a.title; }).join(" • "));

        setText(
            "optText",
            applied.map(function (a) { return a.why; }).join(" ") +
            " The optimized code is regenerated from the syntax tree, so comments and blank lines are not kept."
        );

    }
    else {

        setText(
            "optBadge",
            data.status === "Rejected" ? "✗ Rewrite rejected" : "No optimization applied"
        );

        setText("optName", "None");

        setText("optConfidence", "—");

        setText(
            "optTitle",
            data.status === "Rejected" ? "Rewrite rejected by validation" : "Nothing to optimize automatically"
        );

        setText("optText", data.message);

    }


    setText("chkSyntax", "✓ Syntax");

    setText("chkPattern", (applied.length > 0 ? "✓" : "–") + " Pattern Match");

    setText("chkTests", (data.validation.status === "VALID" ? "✓" : data.validation.status === "INVALID" ? "✗" : "–") + " Test Output");

    setText("chkEquiv", (valid ? "✓" : data.validation.status === "INVALID" ? "✗" : "–") + " Functional Equivalence");

}



function renderValidation(data) {

    const v = data.validation;

    const step = document.getElementById("valMatchStep");

    step.classList.remove("success-step", "failed-step");


    setText("valTotal", v.executed);

    setText("valPassed", v.passed);

    setText("valFailed", v.failed);

    setText("valStatus", v.status);

    document.getElementById("valFailed").className = v.failed > 0 ? "bad-text" : "";

    document.getElementById("valStatus").className =
        v.status === "VALID" ? "green-text" : v.status === "INVALID" ? "bad-text" : "";


    if (v.status === "VALID") {

        step.classList.add("success-step");

        setText("valMatchIcon", "✓");

        setText("valMatchText", "All outputs matched");

        setText("valBadge", "✓ Output Equivalence Confirmed");

    }
    else if (v.status === "INVALID") {

        step.classList.add("failed-step");

        setText("valMatchIcon", "✗");

        setText("valMatchText", "Outputs differ");

        setText("valBadge", "✗ Output mismatch – rewrite discarded");

    }
    else {

        setText("valMatchIcon", "–");

        setText("valMatchText", "Nothing to compare");

        setText("valBadge", "No optimization to validate");

    }


    setText(
        "valTestsText",
        v.rows.length === 0
            ? "No tests were needed"
            : v.executed + " test case(s) executed" + (v.skipped ? ", " + v.skipped + " skipped" : "")
    );


    const body = document.getElementById("valRows");

    body.innerHTML = "";


    if (v.rows.length === 0) {

        const row = document.createElement("tr");

        const cell = document.createElement("td");

        cell.colSpan = 4;

        cell.textContent = "No optimization was applied, so there was nothing to validate.";

        row.appendChild(cell);

        body.appendChild(row);

    }


    v.rows.forEach(function (t) {

        const row = document.createElement("tr");

        [t.name, t.original, t.optimized].forEach(function (text) {

            const cell = document.createElement("td");

            cell.textContent = text;

            row.appendChild(cell);

        });


        const result = document.createElement("td");

        result.textContent = t.status.toUpperCase();

        result.className = "status-" + t.status;

        row.appendChild(result);

        body.appendChild(row);

    });

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

    currentScale = executions;


    document.querySelectorAll(".scale-options button").forEach(function (button) {

        const value = Number(button.textContent.replace(/[^0-9]/g, ""));

        const isBillion = button.textContent.trim() === "1 Billion";

        button.classList.toggle(
            "active",
            (isBillion ? 1000000000 : value) === executions
        );

    });


    if (!lastResult) {

        setText("scaleEnergy", "—");

        setText("scaleCarbon", "—");

        return;

    }


    const energyPerRun = lastResult.comparison.energy_saved_wh;

    const carbonPerRun = lastResult.comparison.co2_saved_g;


    setText("scaleEnergy", orDash(energyPerRun === null ? null : energyPerRun * executions, formatEnergy));

    setText("scaleCarbon", orDash(carbonPerRun === null ? null : carbonPerRun * executions, formatCarbon));

}



function formatEnergy(wh) {

    if (wh === 0) {

        return "0 Wh";

    }

    if (Math.abs(wh) >= 1000) {

        return (wh / 1000).toFixed(2) + " kWh";

    }

    if (Math.abs(wh) >= 1) {

        return wh.toFixed(2) + " Wh";

    }

    if (Math.abs(wh) >= 0.001) {

        return (wh * 1000).toFixed(2) + " mWh";

    }

    return (wh * 1000000).toFixed(2) + " µWh";

}



function formatCarbon(grams) {

    if (grams === 0) {

        return "0 g";

    }

    if (Math.abs(grams) >= 1000) {

        return (grams / 1000).toFixed(2) + " kg";

    }

    if (Math.abs(grams) >= 1) {

        return grams.toFixed(2) + " g";

    }

    if (Math.abs(grams) >= 0.001) {

        return (grams * 1000).toFixed(2) + " mg";

    }

    return (grams * 1000000).toFixed(2) + " µg";

}



/* =====================================================
   REPORT
===================================================== */


function generateReport() {

    if (!lastResult) {

        showNotification(
            "Run an analysis first (or open one from History)."
        );

        return;

    }

    window.open("/report/" + lastResult.id, "_blank");

    showNotification(
        "Report opened. Use Print / Save as PDF inside it."
    );

}



/* =====================================================
   DASHBOARD STATISTICS (from SQLite)
===================================================== */

async function loadStats() {

    try {

        const response = await fetch("/api/stats");

        const s = await response.json();


        setText("statAnalyses", s.analyses);

        setText("statAnalysesNote", "+" + s.this_week + " this week");

        setText("statOptimizations", s.optimizations);

        setText(
            "statOptNote",
            s.success_rate === null ? "No rewrites attempted yet" : s.success_rate + "% success rate"
        );

        setText("statEnergy", formatEnergy(s.energy_saved_wh));

        setText("statCarbon", formatCarbon(s.co2_saved_g));

    }
    catch (error) {

        /* backend not running: keep the default values */

    }

}



/* =====================================================
   HISTORY (from SQLite)
===================================================== */

function formatDate(isoText) {

    return new Date(isoText).toLocaleDateString("en-GB", {

        day: "2-digit",

        month: "short",

        year: "numeric"

    });

}



async function loadHistory() {

    const body = document.getElementById("historyBody");


    try {

        const response = await fetch("/api/history");

        const rows = await response.json();


        body.innerHTML = "";


        if (rows.length === 0) {

            body.innerHTML =
                '<tr><td colspan="5">No analyses yet. Run one from "Analyze Code".</td></tr>';

            return;

        }


        rows.forEach(function (item) {

            const row = document.createElement("tr");


            [formatDate(item.created_at), "Python", item.title].forEach(function (text) {

                const cell = document.createElement("td");

                cell.textContent = text;

                row.appendChild(cell);

            });


            const statusCell = document.createElement("td");

            const status = document.createElement("span");

            status.className = "table-status" + (item.status === "Rejected" ? " rejected" : "");

            status.textContent = item.status;

            statusCell.appendChild(status);

            row.appendChild(statusCell);


            const actionCell = document.createElement("td");

            const view = document.createElement("button");

            view.textContent = "View";

            view.onclick = function () { openHistory(item.id); };

            const report = document.createElement("button");

            report.textContent = "Report";

            report.onclick = function () { window.open("/report/" + item.id, "_blank"); };

            actionCell.appendChild(view);

            actionCell.appendChild(report);

            row.appendChild(actionCell);


            body.appendChild(row);

        });

    }
    catch (error) {

        /* backend not running: keep the default row */

    }

}



async function openHistory(id) {

    try {

        const response = await fetch("/api/history/" + id);

        const data = await response.json();

        showResult(data);

        showPageByName("comparison");

    }
    catch (error) {

        showNotification("Could not load that analysis.");

    }

}



/* =====================================================
   SETTINGS: hardware profile and grid region
===================================================== */

function savePreferences() {

    localStorage.setItem(
        "greentrace-hardware",
        document.getElementById("hardwareSelect").value
    );

    localStorage.setItem(
        "greentrace-region",
        document.getElementById("regionSelect").value
    );

    showNotification("Settings saved. They apply to your next analysis.");

}



function loadPreferences() {

    const hardware = localStorage.getItem("greentrace-hardware");

    const region = localStorage.getItem("greentrace-region");

    if (hardware) {

        document.getElementById("hardwareSelect").value = hardware;

    }

    if (region) {

        document.getElementById("regionSelect").value = region;

    }

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

        loadPreferences();

        updateCodeInfo();

        updateScale(currentScale);

        loadStats();

        loadHistory();

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
