// Spend Tracker Frontend JavaScript

// Dynamically determine backend API base URL
// If running on Django server (port 8000), use relative paths ("").
// If running on Live Server (port 5500, etc.) or file://, direct to Django backend on port 8000.
const API_BASE_URL = (window.location.protocol.startsWith("http") && window.location.port === "8000") ? "" : "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    // Set default date input to today
    const dateInput = document.getElementById("date");
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split("T")[0];
        dateInput.value = today;
    }

    // Initial Data Load
    loadSummary();
    loadExpenses();

    // Event Listeners
    const form = document.getElementById("expense-form");
    if (form) {
        form.addEventListener("submit", handleFormSubmit);
    }

    const applyFiltersBtn = document.getElementById("apply-filters-btn");
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener("click", () => loadExpenses());
    }

    const clearFiltersBtn = document.getElementById("clear-filters-btn");
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener("click", clearFilters);
    }

    const toggleFiltersBtn = document.getElementById("toggle-filters-btn");
    const filterControls = document.getElementById("filter-controls");
    if (toggleFiltersBtn && filterControls) {
        toggleFiltersBtn.addEventListener("click", () => {
            filterControls.classList.toggle("hidden");
        });
    }
});

// Format Currency Utility
function formatCurrency(amount) {
    const num = parseFloat(amount) || 0;
    return "₹" + num.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Fetch & Display Financial Summary Metrics
async function loadSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/summary/`);
        if (!response.ok) {
            throw new Error(`Failed to load summary (HTTP ${response.status})`);
        }
        const data = await response.json();

        // Update Total Spend
        const totalSpendEl = document.getElementById("total-spend");
        if (totalSpendEl) totalSpendEl.textContent = formatCurrency(data.total_spend);

        // Update Current Month
        const currMonthSpendEl = document.getElementById("current-month-spend");
        const currMonthPeriodEl = document.getElementById("current-month-period");
        if (currMonthSpendEl) currMonthSpendEl.textContent = formatCurrency(data.current_month.total_spend);
        if (currMonthPeriodEl) currMonthPeriodEl.textContent = `${getMonthName(data.current_month.month)} ${data.current_month.year}`;

        // Update Previous Month
        const prevMonthSpendEl = document.getElementById("previous-month-spend");
        const prevMonthPeriodEl = document.getElementById("previous-month-period");
        if (prevMonthSpendEl) prevMonthSpendEl.textContent = formatCurrency(data.previous_month.total_spend);
        if (prevMonthPeriodEl) prevMonthPeriodEl.textContent = `${getMonthName(data.previous_month.month)} ${data.previous_month.year}`;

        // Update Month-over-Month Change
        const momPercentageEl = document.getElementById("mom-percentage");
        const momDiffEl = document.getElementById("mom-difference");
        if (momPercentageEl && momDiffEl) {
            const pct = data.mom_change.percentage;
            const diff = data.mom_change.difference;
            const sign = diff >= 0 ? "+" : "";
            momPercentageEl.textContent = `${sign}${pct}%`;
            momPercentageEl.style.color = pct > 0 ? "var(--error-text)" : (pct < 0 ? "var(--success-text)" : "var(--text-primary)");
            momDiffEl.textContent = `${sign}${formatCurrency(diff)}`;
        }

        // Spend by Category
        renderCategorySpend(data.spend_by_category);

        // Spending Insights
        renderInsights(data.insights);

    } catch (err) {
        console.error("Error loading summary:", err);
    }
}

// Helper to get month name
function getMonthName(monthNumber) {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[monthNumber - 1] || `Month ${monthNumber}`;
}

// Render Spend by Category
function renderCategorySpend(spendByCategory) {
    const container = document.getElementById("category-list");
    if (!container) return;

    container.textContent = ""; // Clear existing

    const categories = Object.keys(spendByCategory || {});
    if (categories.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No category spending data yet.";
        container.appendChild(empty);
        return;
    }

    categories.forEach(cat => {
        const item = document.createElement("div");
        item.className = "category-item";

        const nameSpan = document.createElement("span");
        nameSpan.textContent = cat;

        const amountSpan = document.createElement("span");
        amountSpan.style.fontWeight = "600";
        amountSpan.textContent = formatCurrency(spendByCategory[cat]);

        item.appendChild(nameSpan);
        item.appendChild(amountSpan);
        container.appendChild(item);
    });
}

// Render Insights
function renderInsights(insights) {
    const container = document.getElementById("insights-list");
    if (!container) return;

    container.textContent = "";

    if (!insights || insights.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No high spending increases (>20%) detected.";
        container.appendChild(empty);
        return;
    }

    insights.forEach(insight => {
        const card = document.createElement("div");
        card.className = "insight-card";
        card.textContent = insight.message;
        container.appendChild(card);
    });
}

// Fetch & Display Filtered Expense List
async function loadExpenses() {
    const container = document.getElementById("expense-list-container");
    if (!container) return;

    container.textContent = "";
    const loading = document.createElement("p");
    loading.className = "empty-state";
    loading.textContent = "Loading expenses...";
    container.appendChild(loading);

    // Build query params
    const category = document.getElementById("filter-category")?.value.trim();
    const startDate = document.getElementById("filter-start-date")?.value;
    const endDate = document.getElementById("filter-end-date")?.value;

    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    const queryString = params.toString() ? `?${params.toString()}` : "";

    try {
        const response = await fetch(`${API_BASE_URL}/api/expenses/${queryString}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch expenses (HTTP ${response.status})`);
        }
        const expenses = await response.json();

        container.textContent = "";

        if (expenses.length === 0) {
            const empty = document.createElement("p");
            empty.className = "empty-state";
            empty.textContent = "No expenses found matching the criteria.";
            container.appendChild(empty);
            return;
        }

        expenses.forEach(exp => {
            const item = document.createElement("div");
            item.className = "expense-item";

            const details = document.createElement("div");
            details.className = "expense-details";

            const catEl = document.createElement("div");
            catEl.className = "expense-category";
            catEl.textContent = exp.category;

            const noteEl = document.createElement("div");
            noteEl.className = "expense-note";
            noteEl.textContent = exp.note || "(No note)";

            const dateEl = document.createElement("div");
            dateEl.className = "expense-date";
            dateEl.textContent = exp.date;

            details.appendChild(catEl);
            details.appendChild(noteEl);
            details.appendChild(dateEl);

            const amountEl = document.createElement("div");
            amountEl.className = "expense-amount";
            amountEl.textContent = formatCurrency(exp.amount);

            item.appendChild(details);
            item.appendChild(amountEl);
            container.appendChild(item);
        });

    } catch (err) {
        console.error("Error loading expenses:", err);
        container.textContent = "";
        const errEl = document.createElement("p");
        errEl.className = "empty-state";
        errEl.style.color = "var(--error-text)";
        errEl.textContent = "Failed to load expenses. Please make sure the Django server is running at http://127.0.0.1:8000/";
        container.appendChild(errEl);
    }
}

// Clear Filters
function clearFilters() {
    const catInput = document.getElementById("filter-category");
    const startInput = document.getElementById("filter-start-date");
    const endInput = document.getElementById("filter-end-date");
    if (catInput) catInput.value = "";
    if (startInput) startInput.value = "";
    if (endInput) endInput.value = "";
    loadExpenses();
}

// Handle Expense Form Submit
async function handleFormSubmit(e) {
    e.preventDefault();
    clearErrors();

    const amount = document.getElementById("amount").value;
    const category = document.getElementById("category").value;
    const date = document.getElementById("date").value;
    const note = document.getElementById("note").value;

    const payload = { amount, category, date, note };

    const submitBtn = document.getElementById("submit-btn");
    if (submitBtn) submitBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/expenses/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            showAlert("Expense added successfully!", "success");
            // Reset form fields except keep date to today
            document.getElementById("amount").value = "";
            document.getElementById("category").value = "";
            document.getElementById("note").value = "";
            const today = new Date().toISOString().split("T")[0];
            document.getElementById("date").value = today;

            // Reload data
            loadExpenses();
            loadSummary();
        } else {
            // Handle validation errors
            showAlert("Please fix the errors in the form.", "error");
            displayErrors(data);
        }

    } catch (err) {
        console.error("Error submitting expense:", err);
        showAlert("Failed to communicate with backend server.", "error");
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// Clear Validation Errors and Alert Box
function clearErrors() {
    const alertBox = document.getElementById("alert-box");
    if (alertBox) {
        alertBox.className = "alert-box hidden";
        alertBox.textContent = "";
    }
    document.querySelectorAll(".field-error").forEach(el => {
        el.textContent = "";
    });
}

// Show Alert Box Message
function showAlert(message, type) {
    const alertBox = document.getElementById("alert-box");
    if (alertBox) {
        alertBox.textContent = message;
        alertBox.className = `alert-box ${type}`;
    }
}

// Display DRF Field Validation Errors
function displayErrors(errors) {
    if (typeof errors !== "object" || !errors) return;

    Object.keys(errors).forEach(field => {
        const errorEl = document.getElementById(`error-${field}`);
        if (errorEl) {
            const messages = Array.isArray(errors[field]) ? errors[field].join(" ") : errors[field];
            errorEl.textContent = messages;
        }
    });
}
