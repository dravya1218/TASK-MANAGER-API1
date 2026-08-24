document.addEventListener("DOMContentLoaded", () => {

    const registerForm = document.getElementById("registerForm");
    const verifyForm = document.getElementById("verifyForm");
    const errorBox = document.getElementById("error");
    const successBox = document.getElementById("success");
    let registeredEmail = "";

    function showError(message) {
        showToast(message, "danger");
        errorBox.innerText = message;
        errorBox.classList.remove("d-none");
        successBox.classList.add("d-none");
    }

    function showSuccess(message) {
        showToast(message, "success");
        successBox.innerText = message;
        successBox.classList.remove("d-none");
        errorBox.classList.add("d-none");
    }

    registerForm.addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = registerForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.innerText = "Registering...";

        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        if (password !== confirmPassword) {
            showError("Passwords do not match");
            button.disabled = false;
            button.innerText = "Register";
            return;
        }

        registeredEmail = document.getElementById("email").value.trim().toLowerCase();

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: document.getElementById("username").value.trim(),
                    email: registeredEmail,
                    password: password,
                    confirm_password: confirmPassword
                })
            });

            const result = await response.json();

            if (!response.ok) {
                showError(result.error || "Unable to register");
                return;
            }

            showSuccess("Registration successful. Check your email for the OTP.");
            registerForm.classList.add("d-none");
            verifyForm.classList.remove("d-none");

        } catch (error) {
            showError("Unable to connect to server");
        } finally {
            button.disabled = false;
            button.innerText = "Register";
        }

    });

    verifyForm.addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = verifyForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.innerText = "Verifying...";

        try {
            const response = await fetch("/api/verify-email", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: registeredEmail,
                    otp: document.getElementById("otp").value.trim()
                })
            });

            const result = await response.json();

            if (!response.ok) {
                showError(result.error || "Unable to verify email");
                return;
            }

            showSuccess("Email verified. You can now log in.");
            verifyForm.classList.add("d-none");

        } catch (error) {
            showError("Unable to connect to server");
        } finally {
            button.disabled = false;
            button.innerText = "Verify Email";
        }

    });

});
