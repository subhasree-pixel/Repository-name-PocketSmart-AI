const $ = (selector) =>
    document.querySelector(selector);


const money = (value) =>
    new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 0
        }
    ).format(value);


async function api(
    url,
    options = {}
) {

    const response = await fetch(
        url,
        {
            credentials: "include",
            ...options
        }
    );

    const data =
        await response
            .json()
            .catch(
                () => ({
                    detail:
                        "Unexpected server response"
                })
            );

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Request failed"
        );

    }

    return data;
}


function setMessage(
    text,
    ok = false
) {

    const element =
        $("#formMessage");

    if (!element) {
        return;
    }

    element.textContent = text;

    element.className =
        "message " +
        (ok ? "ok" : "error");
}


async function bindRegister() {

    const form =
        $("#registerForm");

    if (!form) {
        return;
    }

    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            const formData =
                new FormData(form);

            const data =
                Object.fromEntries(
                    formData
                );

            try {

                await api(
                    "/register",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body:
                            JSON.stringify(data)
                    }
                );

                setMessage(
                    "Account created. Redirecting…",
                    true
                );

                setTimeout(
                    () => {
                        window.location.href =
                            "/login";
                    },
                    700
                );

            } catch (error) {

                setMessage(
                    error.message
                );

            }
        }
    );
}


async function bindLogin() {

    const form =
        $("#loginForm");

    if (!form) {
        return;
    }

    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            const formData =
                new URLSearchParams(
                    new FormData(form)
                );

            try {

                await api(
                    "/login",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/x-www-form-urlencoded"
                        },
                        body:
                            formData
                    }
                );

                window.location.href =
                    "/dashboard";

            } catch (error) {

                setMessage(
                    error.message
                );

            }
        }
    );
}


async function logout() {

    await api(
        "/logout",
        {
            method: "POST"
        }
    ).catch(
        () => {}
    );

    window.location.href = "/";
}


function parseCsv(value) {

    if (!value) {
        return [];
    }

    return value
        .split(",")
        .map(
            item => item.trim()
        )
        .filter(Boolean);
}


async function bindPlanner(
    type
) {

    const form =
        $("#" + type + "Form");

    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            setMessage(
                "Generating your plan…",
                true
            );


            let options = {
                method: "POST"
            };


            if (type === "jewelry") {

                options.body =
                    new FormData(form);

            } else {

                const formData =
                    new FormData(form);

                const data =
                    Object.fromEntries(
                        formData
                    );


                data.budget =
                    Number(data.budget);


                if (type === "home") {

                    data.rooms =
                        parseCsv(
                            data.rooms
                        );

                    data.priorities =
                        parseCsv(
                            data.priorities
                        );


                    try {

                        data.items =
                            JSON.parse(
                                data.items || "{}"
                            );

                    } catch {

                        setMessage(
                            'Items must be valid JSON, e.g. {"lights": 4}'
                        );

                        return;
                    }

                } else {

                    data.guests =
                        Number(data.guests);

                    data.priorities =
                        parseCsv(
                            data.priorities
                        );

                }


                options.headers = {
                    "Content-Type":
                        "application/json"
                };

                options.body =
                    JSON.stringify(data);
            }


            try {

                const result =
                    await api(
                        "/generate-" + type,
                        options
                    );

                renderResults(
                    result
                );

            } catch (error) {

                setMessage(
                    error.message
                );

            }

        }
    );
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function renderResults(result) {

    setMessage(
        result.ai_used
            ? "Gemini-powered plan generated."
            : "Plan generated with the reliable local fallback catalog.",
        true
    );


    const element =
        $("#results");

    if (!element) {
        return;
    }


    const allocations =
        Object.entries(
            result.allocations
        )
        .map(
            ([key, value]) => `
                <div>
                    <span>
                        ${escapeHtml(key)}
                    </span>

                    <b>
                        ${money(value)}
                    </b>
                </div>
            `
        )
        .join("");


    const recommendations =
        result.recommendations
        .map(
            item => `
                <article class="rec">

                    <div>

                        <span class="pill">
                            ${escapeHtml(item.platform)}
                        </span>

                        <h3>
                            ${escapeHtml(item.name)}
                        </h3>

                        <p>
                            ${escapeHtml(item.reason)}
                        </p>

                    </div>

                    <div class="price">

                        ${money(item.price)}

                        <a
                            target="_blank"
                            rel="noopener"
                            href="${item.url}"
                        >
                            Find product ↗
                        </a>

                    </div>

                </article>
            `
        )
        .join("");


    const tips =
        result.tips
        .map(
            tip =>
                `<li>${escapeHtml(tip)}</li>`
        )
        .join("");


    element.innerHTML = `

        <div class="result-head">

            <div>

                <span class="pill">
                    ${
                        result.ai_used
                            ? "AI"
                            : "FALLBACK"
                    }
                </span>

                <h2>
                    ${escapeHtml(result.summary)}
                </h2>

            </div>

            <strong>
                ${money(result.allocated_total)}
            </strong>

        </div>


        <div class="allocations">
            ${allocations}
        </div>


        <h3>
            Recommendations
        </h3>


        <div class="recommendations">
            ${recommendations}
        </div>


        <h3>
            Tips
        </h3>


        <ul>
            ${tips}
        </ul>

    `;
}


async function loadDashboard() {

    try {

        const session =
            await api(
                "/session-info"
            );

        const welcome =
            $("#welcome");

        if (welcome) {

            welcome.textContent =
                `Welcome, ${session.full_name}. You have a saved workspace for your next plan.`;

        }


        const history =
            await api(
                "/history"
            );


        const recent =
            $("#recent");

        if (!recent) {
            return;
        }


        recent.innerHTML =
            history.length
                ? history
                    .slice(0, 5)
                    .map(
                        item =>
                            historyRow(item)
                    )
                    .join("")
                : "No plans yet.";

    } catch {

        window.location.href =
            "/login";
    }
}


function historyRow(item) {

    return `

        <a
            class="history-row"
            href="/recommendations-details/${item.id}"
        >

            <span>
                ${escapeHtml(
                    item.planner_type
                )}
            </span>

            <b>
                ${money(item.budget)}
            </b>

            <time>
                ${new Date(
                    item.created_at
                ).toLocaleString()}
            </time>

        </a>
    `;
}


async function loadHistory() {

    try {

        const history =
            await api(
                "/history"
            );


        const element =
            $("#history");

        if (!element) {
            return;
        }


        element.innerHTML =
            history.length
                ? history
                    .map(
                        item =>
                            historyRow(item)
                    )
                    .join("")
                : "No saved recommendations yet.";

    } catch {

        window.location.href =
            "/login";
    }
}