let roleData = {};

document.addEventListener("DOMContentLoaded", async () => {

    if (!requireLogin()) return;

    if (localStorage.getItem("role") !== "admin") {
        window.location.replace("/dashboard");
        return;
    }

    await loadRolesAndPermissions();

});

async function loadRolesAndPermissions() {

    const response = await apiFetch("/api/admin/roles-permissions");

    const result = await response.json();

    if (!response.ok) {

        showToast(result.error || result.message, "danger");

        return;

    }

    roleData = result;

    populateRoles(roleData.roles);

}

function populateRoles(roles) {

    const select = document.getElementById("roleSelect");

    select.innerHTML = "";

    roles.forEach(role => {

        select.innerHTML += `
            <option value="${role.name}">
                ${role.name}
            </option>
        `;

    });

    // Automatically load first role permissions
    if (roles.length > 0) {

        loadRolePermissions(roles[0].name);

    }

}

document.getElementById("roleSelect").addEventListener("change", () => {

    const role = document.getElementById("roleSelect").value;

    loadRolePermissions(role);

});

async function loadRolePermissions(roleName) {

    const response = await apiFetch(
        `/api/admin/roles/${roleName}/permissions`
    );

    const permissions = await response.json();

    if (!response.ok) {

        showToast(permissions.error || permissions.message, "danger");

        return;

    }

    renderPermissions(permissions);

}

function renderPermissions(selectedPermissions) {

    const container = document.getElementById("permissionContainer");

    container.innerHTML = "";

    roleData.permissions.forEach(permission => {

        const checked = selectedPermissions.some(
            p => p.id === permission.id
        );

        container.innerHTML += `

            <div class="form-check mb-2">

                <input
                    class="form-check-input permission-checkbox"
                    type="checkbox"
                    id="permission-${permission.id}"
                    value="${permission.name}"
                    ${checked ? "checked" : ""}>

                <label
                    class="form-check-label"
                    for="permission-${permission.id}">

                    ${permission.name}

                </label>

            </div>

        `;

    });

}

document.getElementById("saveBtn").addEventListener("click", savePermissions);

async function savePermissions() {

    const roleName = document.getElementById("roleSelect").value;

    const saveBtn = document.getElementById("saveBtn");

    saveBtn.disabled = true;
    saveBtn.innerText = "Saving...";

    const permissions = [];

    document
        .querySelectorAll(".permission-checkbox:checked")
        .forEach(box => {

            permissions.push(box.value);

        });

    try {

        const response = await apiFetch(
            `/api/admin/roles/${roleName}/permissions`,
            {
                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    permissions: permissions
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {

            showToast(result.error || result.message, "danger");
            return;

        }

        showToast(result.message, "success");

    }
    catch (error) {

        console.error(error);

        showToast("Unable to connect to server.", "danger");

    }
    finally {

        saveBtn.disabled = false;
        saveBtn.innerText = "Save Changes";

    }

}