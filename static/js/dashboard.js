let currentPage = 1;

const limit = 10;

let totalPages = 1;

let taskToDelete = null;

function showLoading() {

    document
        .getElementById("loadingSpinner")
        .classList.remove("d-none");

}

function disableButton(button, text = "Loading...") {

    button.disabled = true;

    button.dataset.originalText = button.innerHTML;

    button.innerHTML = text;

}

function enableButton(button) {

    button.disabled = false;

    button.innerHTML = button.dataset.originalText;

}

function hideLoading() {

    document
        .getElementById("loadingSpinner")
        .classList.add("d-none");

}

async function loadCategories() {

    const response = await apiFetch("/api/categories");

    const categories = await response.json();

    if (!response.ok) {

        showToast(
            categories.error || categories.message,
            "danger"
        );

        return;

    }

    const select = document.getElementById("taskCategory");

    select.innerHTML = `
        <option value="">No Category</option>
    `;

    categories.forEach(category => {

        select.innerHTML += `
            <option value="${category.id}">
                ${category.name}
            </option>
        `;

    });

}

async function loadCategoryList() {

    const response =
        await apiFetch("/api/categories");

    const categories =
        await response.json();

    const container =
        document.getElementById("categoryList");

    if (!response.ok) {

        container.innerHTML = `
            <p class="text-danger">
                Unable to load categories.
            </p>
        `;

        return;
    }

    if (categories.length === 0) {

        container.innerHTML = `
            <p class="text-muted">
                No categories created yet.
            </p>
        `;

        return;
    }

    container.innerHTML = "";

    categories.forEach(category => {

        container.innerHTML += `
            <div class="d-flex justify-content-between
                        align-items-center
                        border-bottom
                        py-2">

                <span>
                    ${category.name}
                </span>

                <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    onclick="deleteCategory(${category.id})">

                    Delete

                </button>

            </div>
        `;

    });

}

document.addEventListener("DOMContentLoaded", () => {

    if (!requireLogin()) {
        return;
    }

    const toastMessage = localStorage.getItem("toast");

    if (toastMessage) {

        showToast(toastMessage, "success");

        localStorage.removeItem("toast");

    }

    loadTasks();
    loadCategories();
    loadCategoryList();

    document.getElementById("search")
        .addEventListener("input", () => {

            currentPage = 1;

            loadTasks();

        });

    document.getElementById("status")
        .addEventListener("change", () => {

            currentPage = 1;

            loadTasks();

        });

    document.getElementById("priority")
        .addEventListener("change", () => {

            currentPage = 1;

            loadTasks();

        });

    document.getElementById("sort_by")
        .addEventListener("change", () => {

            currentPage = 1;

            loadTasks();

        });

    document.getElementById("order")
        .addEventListener("change", () => {

            currentPage = 1;

            loadTasks();

        });

    document.getElementById("prevPage")
        .addEventListener("click", () => {

            if (currentPage > 1) {

                currentPage--;

                loadTasks();

            }

        });

    document.getElementById("nextPage")
        .addEventListener("click", () => {

            if (currentPage < totalPages) {

                currentPage++;

                loadTasks();

            }

        });

    document
    .getElementById("confirmDeleteBtn")
    .addEventListener("click", confirmDeleteTask);


        const createCategoryBtn =
    document.getElementById("createCategoryBtn");

    const newCategoryContainer =
        document.getElementById("newCategoryContainer");

    createCategoryBtn.addEventListener("click", () => {

        newCategoryContainer.classList.toggle("d-none");

    });

    document.getElementById("saveTaskBtn")
        .addEventListener("click", saveTask);


document
    .getElementById("saveCategoryBtn")
    .addEventListener("click", async () => {

        const newCategory =
            document.getElementById("newCategory").value.trim();

        if (!newCategory) {

            showToast(
                "Enter category name.",
                "warning"
            );

            return;
        }

        try {

            const response = await apiFetch(
                "/api/categories",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        name: newCategory
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {

                showToast(
                    result.error || result.message,
                    "danger"
                );

                return;
            }

            await loadCategories();

            const select =
                document.getElementById("taskCategory");

            const selectedCategory =
                newCategory.toLowerCase();

            for (const option of select.options) {

                if (
                    option.text.toLowerCase() ===
                    selectedCategory
                ) {

                    option.selected = true;

                    break;
                }
            }

            document
                .getElementById("newCategory")
                .value = "";

            newCategoryContainer.classList.add("d-none");

            showToast(
                "Category created successfully.",
                "success"
            );

        } catch (error) {

            console.error(error);

            showToast(
                "Unable to connect to server.",
                "danger"
            );

        }

    });


    document
    .querySelector('[data-bs-target="#taskModal"]')
    .addEventListener("click", () => {

        document.getElementById("taskForm").reset();

        document.getElementById("taskId").value = "";

        document.getElementById("taskModalTitle").innerText =
            "Create Task";

        document.getElementById("saveTaskBtn").innerText =
            "Save Task";

    });

});

async function saveTask() {

    const saveBtn =
        document.getElementById("saveTaskBtn");

    if (saveBtn.disabled) return;

    const taskId =
        document.getElementById("taskId").value;

    const title =
        document.getElementById("taskTitle").value.trim();

    const description =
        document.getElementById("taskDescription").value.trim();

    const categoryValue =
        document.getElementById("taskCategory").value;

    const category_id =
        categoryValue ? Number(categoryValue) : null;

    const priority =
        document.getElementById("taskPriority").value;

    const status =
        document.getElementById("taskStatus").value;

    const due_date =
        document.getElementById("taskDueDate").value || null;


    if (!title) {

        showToast(
            "Title is required.",
            "warning"
        );

        return;
    }


    saveBtn.disabled = true;
    saveBtn.innerHTML = taskId
        ? "Updating..."
        : "Saving...";


    try {

        const url = taskId
            ? `/api/tasks/${taskId}`
            : "/api/tasks";

        const method = taskId
            ? "PUT"
            : "POST";


        const response = await apiFetch(url, {

            method: method,

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                title,
                description,
                category_id,
                priority,
                status,
                due_date

            })

        });


        const result = await response.json();


        if (!response.ok) {

            showToast(
                result.error || result.message || "Failed to save task.",
                "danger"
            );

            return;
        }


        showToast(
            taskId
                ? "Task updated successfully."
                : "Task created successfully.",
            "success"
        );


        document
            .getElementById("taskForm")
            .reset();

        document
            .getElementById("taskId")
            .value = "";


        const modalElement =
            document.getElementById("taskModal");

        const modal =
            bootstrap.Modal.getOrCreateInstance(
                modalElement
            );

        modalElement.addEventListener(
            "hidden.bs.modal",
            () => {

                document
                    .querySelectorAll(".modal-backdrop")
                    .forEach(backdrop => {
                        backdrop.remove();
                    });

                document.body.classList.remove(
                    "modal-open"
                );

                document.body.style.removeProperty(
                    "overflow"
                );

                document.body.style.removeProperty(
                    "padding-right"
                );

            },
            { once: true }
        );

        modal.hide();

        await loadTasks();

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to connect to server.",
            "danger"
        );

    } finally {

        saveBtn.disabled = false;

        saveBtn.innerHTML = "Save Task";

    }

}


function getDueDateBadge(task) {

    if (!task.due_date) {
        return "-";
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const [year, month, day] = task.due_date.split("-").map(Number);

    const dueDate = new Date(year, month - 1, day);
        dueDate.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);


    if (task.status === "pending") {

        if (dueDate < today) {

            return `
                <span class="badge bg-danger">
                    Overdue
                </span>
            `;

        }

        if (dueDate.getTime() === today.getTime()) {

            return `
                <span class="badge bg-warning text-dark">
                    Due Today
                </span>
            `;

        }

        if (dueDate.getTime() === tomorrow.getTime()) {

            return `
                <span class="badge bg-success">
                    Tomorrow
                </span>
            `;

        }

    }

    return `
        <span class="badge bg-info text-dark">
            ${task.due_date}
        </span>
    `;

}

async function loadTasks() {

    const token = getAccessToken();
    showLoading();

    try {

        const search = document.getElementById("search").value.trim();

        const status = document.getElementById("status").value;

        const priority = document.getElementById("priority").value;

        const sort_by = document.getElementById("sort_by").value;

        const order = document.getElementById("order").value;

        const response = await apiFetch(

            `/api/tasks?page=${currentPage}&limit=${limit}&search=${encodeURIComponent(search)}&status=${status}&priority=${priority}&sort_by=${sort_by}&order=${order}`,

            {

                method: "GET",

                headers: {
                    "Authorization": `Bearer ${token}`
                }

            }

        );

        const result = await response.json();

        if (!response.ok) {

            hideLoading();

            showToast(result.error || result.message, "danger");
            
            return;

        }

        totalPages = result["total page"];

        document.getElementById("pageInfo").innerText =
            `Page ${currentPage} of ${totalPages}`;

        document.getElementById("prevPage").disabled =
            currentPage === 1;

        document.getElementById("nextPage").disabled =
            currentPage === totalPages;

        displayTasks(result.tasks);

        updateStats(result.tasks);

        drawStatusChart(result.tasks);

        hideLoading();
    }

    catch (error) {

        hideLoading();

        console.error(error);

        showToast("Unable to connect to server.", "danger");

    }

}

function displayTasks(tasks) {

    const table = document.getElementById("taskTable");

    table.innerHTML = "";

    if (tasks.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    No Tasks Found
                </td>
            </tr>
        `;

        return;

    }

    tasks.forEach(task => {

        const statusBadge =
            task.status === "completed"
                ? `<span class="badge bg-success">Completed</span>`
                : `<span class="badge bg-warning text-dark">Pending</span>`;

        const priorityBadge =
            task.priority === "high"
                ? `<span class="badge bg-danger">High</span>`
                : task.priority === "medium"
                ? `<span class="badge bg-primary">Medium</span>`
                : `<span class="badge bg-secondary">Low</span>`;

        table.innerHTML += `
            <tr>

                <td>${task.id}</td>

                <td>${task.title}</td>

                <td>${statusBadge}</td>

                <td>${priorityBadge}</td>

                <td>${task.category_name || "No Category"}</td>

                <td>${task.user_id}</td>

                <td>${getDueDateBadge(task)}</td>

                <td>

                    <button
                        class="btn btn-warning btn-sm"
                        onclick="editTask(${task.id})">

                        Edit

                    </button>

                    <button
                        class="btn btn-danger btn-sm"
                        onclick="deleteTask(${task.id})">

                        Delete

                    </button>

                </td>

            </tr>
        `;

    });

}
function updateStats(tasks) {

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const total = tasks.length;

    const pending = tasks.filter(task => task.status === "pending").length;

    const completed = tasks.filter(task => task.status === "completed").length;

    const high = tasks.filter(task => task.priority === "high").length;

    const overdue = tasks.filter(task => {

        if (
            task.status !== "pending" ||
            !task.due_date
        ) {
            return false;
        }

        const due = new Date(task.due_date);
        due.setHours(0, 0, 0, 0);

        return due < today;

    }).length;

    document.getElementById("totalTasks").innerText = total;

    document.getElementById("pendingTasks").innerText = pending;

    document.getElementById("completedTasks").innerText = completed;

    document.getElementById("highTasks").innerText = high;

    document.getElementById("overdueTasks").innerText = overdue;

    const percentage =
        total === 0
            ? 0
            : Math.round((completed / total) * 100);

    document.getElementById("progressBar").style.width =
        percentage + "%";

    document.getElementById("progressBar").innerText =
        percentage + "%";

    document.getElementById("progressText").innerText =
        `${completed} of ${total} Tasks Completed`;

}

function deleteTask(taskId) {

    taskToDelete = taskId;

    const modal = new bootstrap.Modal(
        document.getElementById("deleteModal")
    );

    modal.show();

}


async function editTask(taskId) {

    try {

        const response = await apiFetch(
            `/api/tasks/${taskId}`
        );

        const task = await response.json();

        if (!response.ok) {

            showToast(
                task.error || task.message,
                "danger"
            );

            return;
        }


        document.getElementById("taskId").value =
            task.id;

        document.getElementById("taskTitle").value =
            task.title || "";

        document.getElementById("taskDescription").value =
            task.description || "";

        document.getElementById("taskCategory").value =
            task.category_id || "";

        document.getElementById("taskPriority").value =
            task.priority;

        document.getElementById("taskStatus").value =
            task.status;

        document.getElementById("taskDueDate").value =
            task.due_date || "";


        document.getElementById("taskModalTitle").innerText =
            "Edit Task";

        document.getElementById("saveTaskBtn").innerText =
            "Update Task";


        const modalElement =
            document.getElementById("taskModal");

        const modal =
            bootstrap.Modal.getOrCreateInstance(
                modalElement
            );

        modal.show();


    } catch (error) {

        console.error(error);

        showToast(
            "Unable to load task.",
            "danger"
        );

    }

}


async function confirmDeleteTask() {

    if (taskToDelete === null) return;

    const token = getAccessToken();

    const deleteBtn = document.getElementById("confirmDeleteBtn");

    disableButton(deleteBtn, "Deleting...");

    try {

        const response = await apiFetch(`/api/tasks/${taskToDelete}`, {

            method: "DELETE",

            headers: {
                "Authorization": `Bearer ${token}`
            }

        });

        const result = await response.json();

        if (!response.ok) {

            enableButton(deleteBtn);

            showToast(result.error || result.message, "danger");

            return;

        }

        showToast(result.message, "success");

        const modal = bootstrap.Modal.getInstance(
            document.getElementById("deleteModal")
        );

        modal.hide();

        enableButton(deleteBtn);

        taskToDelete = null;

        loadTasks();

    }

    catch (err) {

        enableButton(deleteBtn);

        console.error(err);

        showToast("Unable to delete task.", "danger");

    }

}

let statusChart = null;

function drawStatusChart(tasks) {

    const pending =
        tasks.filter(task => task.status === "pending").length;

    const completed =
        tasks.filter(task => task.status === "completed").length;

    const ctx = document
        .getElementById("statusChart")
        .getContext("2d");

    if (statusChart) {
        statusChart.destroy();
    }

    statusChart = new Chart(ctx, {

        type: "pie",

        data: {

            labels: [
                "Pending",
                "Completed"
            ],

            datasets: [{

                data: [
                    pending,
                    completed
                ],

                backgroundColor: [
                    "#ffc107",
                    "#198754"
                ]

            }]

        },

        options: {

            responsive: true,
            maintainAspectRatio: false,
            plugins: {

                legend: {
                    position: "bottom"
                }

            }

        }

    });

}


async function deleteCategory(categoryId) {

    const confirmed = confirm(
        "Are you sure you want to delete this category?"
    );

    if (!confirmed) return;

    try {

        const response = await apiFetch(
            `/api/categories/${categoryId}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {

            showToast(
                result.error || result.message || "Failed to delete category.",
                "danger"
            );

            return;
        }

        showToast(
            result.message || "Category deleted successfully.",
            "success"
        );

        // Refresh category dropdown
        await loadCategories();

        // Refresh category management list
        await loadCategoryList();

        // Refresh tasks because a task may now have no category
        await loadTasks();

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to delete category.",
            "danger"
        );
    }
}