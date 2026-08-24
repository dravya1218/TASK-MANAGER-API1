document.addEventListener("DOMContentLoaded", async () => {

    if (!getAccessToken()) {
        window.location.href = "/login";
        return;
    }

    const profileForm = document.getElementById("profileForm");
    const verifyEmailChangeForm = document.getElementById("verifyEmailChangeForm");
    const changePasswordForm = document.getElementById("changePasswordForm");

    async function loadProfile() {

        const response = await apiFetch("/api/profile");

        if (!response.ok) {
            showToast("Unable to load profile.", "danger");
            return;
        }

        const user = await response.json();
        document.getElementById("username").value = user.username;
        document.getElementById("email").value = user.email;
        document.getElementById("role").value = user.role;

    }

    await loadProfile();

    profileForm.addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = profileForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.innerText = "Saving...";

        try {
            const response = await apiFetch("/api/profile", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: document.getElementById("username").value.trim(),
                    email: document.getElementById("email").value.trim()
                })
            });

            const result = await response.json();

            if (!response.ok) {
                showToast(result.error || "Unable to update profile.", "danger");
                return;
            }

            showToast(result.message, "success");

            if (result.email_verification_required) {
                verifyEmailChangeForm.classList.remove("d-none");
            }

        } catch (error) {
            showToast("Unable to connect to server.", "danger");
        } finally {
            button.disabled = false;
            button.innerText = "Save Changes";
        }

    });

    verifyEmailChangeForm.addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = document.getElementById("verifyEmailChangeButton");
        button.disabled = true;
        button.innerText = "Verifying...";

        try {
            const response = await apiFetch("/api/verify-email-change", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    otp: document.getElementById("emailChangeOtp").value.trim()
                })
            });

            const result = await response.json();

            if (!response.ok) {
                showToast(result.error || "Unable to verify email.", "danger");
                return;
            }

            showToast(result.message, "success");
            verifyEmailChangeForm.reset();
            verifyEmailChangeForm.classList.add("d-none");
            await loadProfile();

        } catch (error) {
            showToast("Unable to connect to server.", "danger");
        } finally {
            button.disabled = false;
            button.innerText = "Verify New Email";
        }

    });

    changePasswordForm.addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = changePasswordForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.innerText = "Changing...";

        try {
            const response = await apiFetch("/api/change-password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    current_password: document.getElementById("currentPassword").value,
                    new_password: document.getElementById("newPassword").value,
                    confirm_password: document.getElementById("confirmPassword").value
                })
            });

            const result = await response.json();

            if (!response.ok) {
                showToast(result.error || "Unable to change password.", "danger");
                return;
            }

            showToast(result.message, "success");
            changePasswordForm.reset();

        } catch (error) {
            showToast("Unable to connect to server.", "danger");
        } finally {
            button.disabled = false;
            button.innerText = "Change Password";
        }

    });

});
