function showToast(message, type = "primary") {

    const toastElement = document.getElementById("appToast");

    const toastMessage = document.getElementById("toastMessage");

    toastElement.className =
        `toast align-items-center text-bg-${type} border-0`;

    toastMessage.innerText = message;

    const toast = new bootstrap.Toast(toastElement);

    toast.show();

}