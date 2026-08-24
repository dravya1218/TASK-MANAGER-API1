document.addEventListener("DOMContentLoaded", () => {

    // --------------------------------
    // Elements
    // --------------------------------

    const emailStep =
        document.getElementById("emailStep");

    const otpStep =
        document.getElementById("otpStep");

    const passwordStep =
        document.getElementById("passwordStep");

    const pageTitle =
        document.getElementById("pageTitle");

    const errorBox =
        document.getElementById("error");

    const successBox =
        document.getElementById("success");

    const emailForm =
        document.getElementById("emailForm");

    const otpForm =
        document.getElementById("otpForm");

    const passwordForm =
        document.getElementById("passwordForm");

    const resendOtpBtn =
        document.getElementById("resendOtpBtn");

    const resendTimer =
        document.getElementById("resendTimer");


    // --------------------------------
    // State
    // --------------------------------

    let email = "";

    let resetToken = "";

    let resendInterval = null;


    // --------------------------------
    // Helpers
    // --------------------------------

    function showError(message) {

        errorBox.innerText = message;

        errorBox.classList.remove("d-none");

        successBox.classList.add("d-none");
    }


    function showSuccess(message) {

        successBox.innerText = message;

        successBox.classList.remove("d-none");

        errorBox.classList.add("d-none");
    }


    function clearMessages() {

        errorBox.classList.add("d-none");

        successBox.classList.add("d-none");
    }


    function showStep(step) {

        emailStep.classList.add("d-none");

        otpStep.classList.add("d-none");

        passwordStep.classList.add("d-none");


        if (step === "email") {

            emailStep.classList.remove("d-none");

            pageTitle.innerText =
                "Forgot Password";

        }


        if (step === "otp") {

            otpStep.classList.remove("d-none");

            pageTitle.innerText =
                "Verify OTP";

        }


        if (step === "password") {

            passwordStep.classList.remove("d-none");

            pageTitle.innerText =
                "Create New Password";

        }

    }


    // --------------------------------
    // Resend cooldown
    // --------------------------------

    function startResendCooldown(seconds = 60) {

        resendOtpBtn.disabled = true;

        let remaining = seconds;

        resendTimer.innerText =
            `You can request another OTP in ${remaining} seconds`;


        resendInterval = setInterval(() => {

            remaining--;

            if (remaining <= 0) {

                clearInterval(resendInterval);

                resendOtpBtn.disabled = false;

                resendTimer.innerText = "";

                return;

            }

            resendTimer.innerText =
                `You can request another OTP in ${remaining} seconds`;

        }, 1000);

    }


    // --------------------------------
    // STEP 1
    // Request OTP
    // --------------------------------

    emailForm.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            clearMessages();


            email = document
                .getElementById("email")
                .value
                .trim()
                .toLowerCase();


            try {

                const response = await fetch(
                    "/api/forgot-password",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: email
                        })
                    }
                );


                const result =
                    await response.json();


                if (!response.ok) {

                    showError(
                        result.error ||
                        "Unable to send OTP"
                    );

                    return;
                }


                showSuccess(
                    "OTP sent successfully"
                );

                showStep("otp");

                startResendCooldown();

            } catch (error) {

                console.error(
                    "FORGOT PASSWORD ERROR:",
                    error
                );

                showError(
                    "Unable to connect to server"
                );

            }

        }
    );


    // --------------------------------
    // STEP 2
    // Verify OTP
    // --------------------------------

    otpForm.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            clearMessages();


            const otp =
                document
                    .getElementById("otp")
                    .value
                    .trim();


            try {

                const response =
                    await fetch(
                        "/api/verify-password-reset",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                email: email,
                                otp: otp
                            })
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    showError(
                        result.error ||
                        "Invalid OTP"
                    );

                    return;
                }


                resetToken =
                    result.reset_token;


                showSuccess(
                    "OTP verified successfully"
                );

                showStep("password");

            } catch (error) {

                console.error(
                    "OTP VERIFICATION ERROR:",
                    error
                );

                showError(
                    "Unable to connect to server"
                );

            }

        }
    );


    // --------------------------------
    // Resend OTP
    // --------------------------------

    resendOtpBtn.addEventListener(
        "click",
        async () => {

            clearMessages();


            if (resendOtpBtn.disabled) {
                return;
            }


            try {

                const response =
                    await fetch(
                        "/api/forgot-password",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                email: email
                            })
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    showError(
                        result.error ||
                        "Unable to resend OTP"
                    );

                    return;
                }


                showSuccess(
                    "New OTP sent successfully"
                );

                startResendCooldown();

            } catch (error) {

                console.error(
                    "RESEND OTP ERROR:",
                    error
                );

                showError(
                    "Unable to connect to server"
                );

            }

        }
    );


    // --------------------------------
    // STEP 3
    // Reset Password
    // --------------------------------

    passwordForm.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();

            clearMessages();


            const newPassword =
                document
                    .getElementById("newPassword")
                    .value;

            const confirmPassword =
                document
                    .getElementById("confirmPassword")
                    .value;


            if (newPassword !== confirmPassword) {

                showError(
                    "Passwords do not match"
                );

                return;
            }


            if (newPassword.length < 6) {

                showError(
                    "Password must be at least 6 characters"
                );

                return;
            }


            try {

                const response =
                    await fetch(
                        "/api/reset-password",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Authorization":
                                    `Bearer ${resetToken}`
                            },

                            body: JSON.stringify({
                                new_password:
                                    newPassword,

                                confirm_password:
                                    confirmPassword
                            })
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    showError(
                        result.error ||
                        "Unable to reset password"
                    );

                    return;
                }


                showSuccess(
                    "Password reset successfully. Redirecting to login..."
                );


                setTimeout(() => {

                    window.location.replace(
                        "/login"
                    );

                }, 1500);


            } catch (error) {

                console.error(
                    "PASSWORD RESET ERROR:",
                    error
                );

                showError(
                    "Unable to connect to server"
                );

            }

        }
    );

});