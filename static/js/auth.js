function getAccessToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function saveAccessToken(token) {
    localStorage.setItem("access_token", token);
}

function logoutUser() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");

    window.location.replace("/login");
}

async function refreshAccessToken() {

    const refreshToken = getRefreshToken();

    if (!refreshToken) {

        logoutUser();

        return null;

    }

    const response = await fetch("/api/refresh", {

        method: "POST",

        headers: {
            "Authorization": `Bearer ${refreshToken}`
        }

    });

    if (!response.ok) {

        logoutUser();

        return null;

    }

    const result = await response.json();

    saveAccessToken(result.access_token);

    return result.access_token;

}

async function apiFetch(url, options = {}) {

    let token = getAccessToken();

    options.headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${token}`
    };

    let response = await fetch(url, options);

    if (response.status !== 401) {

        return response;

    }

    token = await refreshAccessToken();

    if (!token) {

        return response;

    }

    options.headers["Authorization"] = `Bearer ${token}`;

    return await fetch(url, options);

}

function requireLogin() {

    if (!getAccessToken()) {

        window.location.replace("/login");

        return false;

    }

    return true;

}

document.addEventListener("DOMContentLoaded", () => {

    updateNavbar();

    const logoutBtn = document.getElementById("logoutBtn");

    if (logoutBtn) {

        logoutBtn.addEventListener("click", () => {

            logoutUser();

        });

    }

});


function updateNavbar() {

    const dashboardLink = document.getElementById("dashboardLink");
    const profileLink = document.getElementById("profileLink");
    const logoutBtn = document.getElementById("logoutBtn");
    const loginLink = document.getElementById("loginLink");
    const registerLink = document.getElementById("registerLink");

    const loggedIn = !!getAccessToken();

    if (dashboardLink) {
        dashboardLink.style.display =
            loggedIn ? "inline-block" : "none";
    }

    if (profileLink) {
        profileLink.style.display =
            loggedIn ? "inline-block" : "none";
    }

    if (logoutBtn) {
        logoutBtn.style.display =
            loggedIn ? "inline-block" : "none";
    }

    if (loginLink) {
        loginLink.style.display =
            loggedIn ? "none" : "inline-block";
    }

    if (registerLink) {
        registerLink.style.display =
            loggedIn ? "none" : "inline-block";
    }
}