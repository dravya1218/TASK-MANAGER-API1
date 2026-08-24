document.addEventListener("DOMContentLoaded", () => {

    const logoutBtn = document.getElementById("logoutBtn");

    if (!logoutBtn) {
        return;
    }

    logoutBtn.addEventListener("click", logout);

});

async function logout() {

    const token = getAccessToken();

    try {

        await apiFetch("/api/logout", {

            method: "POST",

            headers: {
                "Authorization": `Bearer ${token}`
            }

        });

    }

    catch (error) {

        console.error(error);

    }

    localStorage.removeItem("access_token");

    localStorage.removeItem("refresh_token");

    localStorage.removeItem("role");

    window.location.replace("/login");

}