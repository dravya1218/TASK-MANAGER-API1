let allUsers = [];

document.addEventListener("DOMContentLoaded", () => {

        if (!requireLogin()) return;

        if (localStorage.getItem("role") !== "admin") {
            window.location.replace("/dashboard");
            return;
        }

    loadUsers();

});

async function loadUsers() {

    try {

        const response = await apiFetch("/api/users");

        const users = await response.json();
        
        allUsers = users;

        if (!response.ok) {

    showToast(users.error || users.message, "danger");

    return;

}

        document.getElementById("totalUsers").innerText = users.length;

        const table = document.getElementById("userTable");

        table.innerHTML = "";

       renderUsers(users);

    }

    catch (error) {

        console.error(error);

        showToast("Unable to connect to server.", "danger");

    }

}

function renderUsers(users) {

    const table = document.getElementById("userTable");

    table.innerHTML = "";

    if (users.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    No users found
                </td>
            </tr>
        `;

        return;

    }

    users.forEach(user => {

        table.innerHTML += `

            <tr>

                <td>${user.id}</td>

                <td>${user.username}</td>

                <td>${user.email}</td>

                <td>${user.role}</td>

                <td>

                    <select
                        class="form-select form-select-sm roleSelect"
                        data-id="${user.id}">

                        <option
                            value="user"
                            ${user.role === "user" ? "selected" : ""}>

                            User

                        </option>

                        <option
                            value="admin"
                            ${user.role === "admin" ? "selected" : ""}>

                            Admin

                        </option>

                    </select>

                </td>

                <td>

                    <button

                        class="btn btn-danger btn-sm deleteUserBtn"

                        data-id="${user.id}"
                        
                        data-username="${user.username}">

                        Delete
                    </button>

                </td>

            </tr>

        `;

    });

    document.querySelectorAll(".roleSelect").forEach(select => {

        select.addEventListener("change", () => {

            const userId = select.dataset.id;

            const role = select.value;

            const confirmed = confirm(
                `Are you sure you want to change this user's role to "${role}"?`
            );

            if (!confirmed) {

                loadUsers();

                return;

            }

            updateRole(userId, role);

        });

    });

    document.querySelectorAll(".deleteUserBtn").forEach(button => {

        button.addEventListener("click", () => {

            const userId = button.dataset.id;

            const username = button.dataset.username;

            deleteUser(userId, username);

        });

    });

}

async function updateRole(userId, role) {

    const select = document.querySelector(
        `.roleSelect[data-id="${userId}"]`
    );

    select.disabled = true;

    try {

        const response = await apiFetch(

            `/api/users/${userId}/role`,

            {

                method: "PUT",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    role: role

                })

            }

        );

        const result = await response.json();

        if (!response.ok) {

            showToast(result.error || result.message, "danger");

            loadUsers();

            return;

        }

        showToast(result.message, "success");

        loadUsers();

    }

    catch (error) {

        console.error(error);

        showToast("Unable to connect to server.", "danger");

    }
    finally {

        select.disabled = false;

    }

}

async function deleteUser(userId,username) {

    const confirmed = confirm(
    `Delete "${username}" permanently?\n\nThis action cannot be undone.`
    );

    if (!confirmed) return;

        const button = document.querySelector(
            `.deleteUserBtn[data-id="${userId}"]`
        );

        button.disabled = true;
        button.innerText = "Deleting...";

    try {

        const response = await apiFetch(
            `/api/users/${userId}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {

            showToast(result.error || result.message, "danger");

            return;

        }

        showToast(result.message, "success");

        loadUsers();

    }

    catch (error) {

            console.error(error);

            showToast("Unable to connect to server.", "danger");

        }
        finally {

            button.disabled = false;
            button.innerText = "Delete";

        }

}

document
    .getElementById("searchUser")
    .addEventListener("input", function () {

        const search = this.value.toLowerCase().trim();

        const filtered = allUsers.filter(user =>

            user.username.toLowerCase().includes(search) ||
            user.email.toLowerCase().includes(search)

        );

        renderUsers(filtered);

    });