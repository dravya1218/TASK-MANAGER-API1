document.addEventListener("DOMContentLoaded", () => {

    // --------------------------------
    // Already logged in?
    // --------------------------------

    if (getAccessToken()) {

        const role = localStorage.getItem("role");

        if (role === "admin") {
            window.location.replace("/admin");
        } else {
            window.location.replace("/dashboard");
        }

        return;
    }


    // --------------------------------
    // Login form
    // --------------------------------

    const form = document.getElementById("loginForm");
    const errorBox = document.getElementById("error");

    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        errorBox.classList.add("d-none");

        const submitButton = form.querySelector("button[type='submit']");
        submitButton.disabled = true;
        submitButton.innerText = "Logging in...";

        const email = document.getElementById("email").value
            .trim()
            .toLowerCase();

        const password = document.getElementById("password").value;

        try {

            const response = await fetch("/api/login", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })

            });

            const result = await response.json();


            // ----------------------------
            // Login successful
            // ----------------------------

            if (response.ok) {

                saveAccessToken(
                    result.token.access_token
                );

                localStorage.setItem(
                    "refresh_token",
                    result.token.refresh_token
                );

                localStorage.setItem(
                    "role",
                    result.token.role
                );


                if (result.token.role === "admin") {

                    window.location.replace("/admin");

                } else {

                    window.location.replace("/dashboard");

                }

                return;
            }


            // ----------------------------
            // Login failed
            // ----------------------------

            errorBox.innerText =
                result.error || "Login failed";

            errorBox.classList.remove("d-none");
            showToast(result.error || "Login failed", "danger");
            submitButton.disabled = false;
            submitButton.innerText = "Login";

        } catch (error) {

            console.error("LOGIN ERROR:", error);

            errorBox.innerText =
                "Unable to connect to server";

            errorBox.classList.remove("d-none");
            showToast("Unable to connect to server", "danger");
            submitButton.disabled = false;
            submitButton.innerText = "Login";

        }

    });


    // --------------------------------
    // Password visibility
    // --------------------------------

    const togglePassword =
        document.getElementById("togglePassword");

    const passwordInput =
        document.getElementById("password");

    togglePassword.addEventListener("click", () => {

        if (passwordInput.type === "password") {

            passwordInput.type = "text";

            togglePassword.innerHTML =
                '<i class="bi bi-eye-slash"></i>';

        } else {

            passwordInput.type = "password";

            togglePassword.innerHTML =
                '<i class="bi bi-eye"></i>';

        }

    });

});
