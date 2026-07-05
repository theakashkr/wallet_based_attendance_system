/**
 * ═══════════════════════════════════════════════════════════════════════════
 * WalletGuard — Dashboard JavaScript
 *
 * Handles all AJAX interactions:
 *   • QR Code scanning via html5-qrcode library
 *   • Check-In / Check-Out via POST with QR token
 *   • Wallet Recharge via POST to /recharge/
 *   • Dynamic UI updates (button states, balance, status indicator)
 *   • Toast notifications for success/error feedback
 *   • Recharge modal open/close
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ─── Global State ───
let qrScanner = null;       // Html5Qrcode instance
let pendingAction = null;   // "checkin" or "checkout"


// ─── Utility: Extract CSRF Token from cookies (Django requirement) ───
function getCSRFToken() {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith("csrftoken=")) {
            return cookie.substring("csrftoken=".length);
        }
    }
    return "";
}


// ─── Toast Notification System ───
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    const icon = type === "success" ? "✅" : "❌";
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Auto-remove after 4 seconds with exit animation
    setTimeout(() => {
        toast.classList.add("toast-exit");
        toast.addEventListener("animationend", () => toast.remove());
    }, 4000);
}


// ─── Update Dashboard UI Without Page Reload ───
function updateDashboardUI(data, action) {
    // Update wallet balance
    const balanceEl = document.getElementById("wallet-balance");
    if (data.wallet_balance !== undefined) {
        balanceEl.innerHTML = `<span class="currency">₹</span>${data.wallet_balance}`;
    }

    const statusIndicator = document.getElementById("status-indicator");
    const statusDetail = document.getElementById("status-detail");
    const checkinBtn = document.getElementById("checkin-btn");
    const checkoutBtn = document.getElementById("checkout-btn");

    if (action === "checkin") {
        // User just checked in
        statusIndicator.innerHTML = `
            <div class="status-dot status-inside"></div>
            <span class="status-text status-text-inside">Inside Office</span>
        `;
        statusDetail.innerHTML = `<span>Checked in at: ${formatTime(data.entry_time)}</span>`;
        checkinBtn.disabled = true;
        checkoutBtn.disabled = false;
    } else if (action === "checkout") {
        // User just checked out
        statusIndicator.innerHTML = `
            <div class="status-dot status-outside"></div>
            <span class="status-text status-text-outside">Outside</span>
        `;
        statusDetail.innerHTML = "";
        checkinBtn.disabled = false;
        checkoutBtn.disabled = true;
    }
}


// ─── Format datetime string to 12-hour time ───
function formatTime(datetimeStr) {
    if (!datetimeStr) return "—";
    const date = new Date(datetimeStr.replace(" ", "T"));
    return date.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    });
}


// ─── Format datetime string to readable date ───
function formatDate(datetimeStr) {
    if (!datetimeStr) return "—";
    const date = new Date(datetimeStr.replace(" ", "T"));
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}


// ─── Set Button Loading State ───
function setButtonLoading(btn, loading) {
    if (loading) {
        btn.classList.add("btn-loading");
        btn.disabled = true;
    } else {
        btn.classList.remove("btn-loading");
        // Don't re-enable here — let the UI update logic handle it
    }
}


// ═══════════════════════════════════════════════════════════════════════════
// QR Code Scanner
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Open the QR scanner modal and start the camera.
 * @param {string} action - "checkin" or "checkout"
 */
function openQRScanner(action) {
    pendingAction = action;

    const modal = document.getElementById("qr-scanner-modal");
    const title = document.getElementById("qr-scanner-title");
    const statusEl = document.getElementById("qr-scan-status");

    title.textContent = action === "checkin"
        ? "📷 Scan QR to Check In"
        : "📷 Scan QR to Check Out";
    statusEl.innerHTML = '<span class="scan-waiting">Waiting for QR code...</span>';

    modal.classList.add("active");

    // Start the scanner after a small delay for the modal animation
    setTimeout(() => startQRScanner(), 350);
}

/**
 * Initialize and start the html5-qrcode scanner.
 */
function startQRScanner() {
    const readerEl = document.getElementById("qr-reader");

    // Clear any previous scanner content
    readerEl.innerHTML = "";

    qrScanner = new Html5Qrcode("qr-reader");

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
    };

    qrScanner.start(
        { facingMode: "environment" },  // Prefer back camera
        config,
        onQRCodeScanned,                // Success callback
        () => {}                        // Ignore per-frame errors
    ).catch((err) => {
        console.error("Camera error:", err);
        const statusEl = document.getElementById("qr-scan-status");
        statusEl.innerHTML = `
            <span class="scan-error">
                ⚠️ Camera access denied or unavailable.<br>
                Please allow camera permission and try again.
            </span>
        `;
    });
}

/**
 * Called when a QR code is successfully scanned.
 * Stops the scanner and submits the token.
 */
async function onQRCodeScanned(decodedText) {
    // Stop the scanner immediately to prevent duplicate scans
    if (qrScanner) {
        try {
            await qrScanner.stop();
        } catch (e) {
            // Scanner may already be stopped
        }
    }

    const statusEl = document.getElementById("qr-scan-status");
    statusEl.innerHTML = '<span class="scan-processing">✨ QR code scanned! Processing...</span>';

    // Send the scanned token to the appropriate endpoint
    if (pendingAction === "checkin") {
        await submitCheckIn(decodedText);
    } else if (pendingAction === "checkout") {
        await submitCheckOut(decodedText);
    }

    // Close the scanner modal
    closeQRScanner();
}

/**
 * Close the QR scanner modal and stop the camera.
 */
function closeQRScanner() {
    const modal = document.getElementById("qr-scanner-modal");
    modal.classList.remove("active");
    pendingAction = null;

    // Stop the camera
    if (qrScanner) {
        qrScanner.stop().catch(() => {});
        qrScanner = null;
    }

    // Clear the reader container
    const readerEl = document.getElementById("qr-reader");
    if (readerEl) readerEl.innerHTML = "";
}


// ═══════════════════════════════════════════════════════════════════════════
// Check-In / Check-Out Handlers (with QR token)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Submit check-in with the scanned QR token.
 */
async function submitCheckIn(qrToken) {
    const btn = document.getElementById("checkin-btn");
    setButtonLoading(btn, true);

    try {
        const response = await fetch("/check-in/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({ qr_token: qrToken }),
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, "success");
            updateDashboardUI(data, "checkin");

            // Add new row to attendance table
            addAttendanceRow({
                date: formatDate(data.entry_time),
                entry: formatTime(data.entry_time),
                exit: null,
                duration: null,
                credits: null,
                active: true,
            });
        } else {
            showToast(data.message, "error");
            btn.disabled = false;
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
        btn.disabled = false;
    }

    setButtonLoading(btn, false);
}

/**
 * Submit check-out with the scanned QR token.
 */
async function submitCheckOut(qrToken) {
    const btn = document.getElementById("checkout-btn");
    setButtonLoading(btn, true);

    try {
        const response = await fetch("/check-out/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({ qr_token: qrToken }),
        });

        const data = await response.json();

        if (data.success) {
            showToast(
                `${data.message} Duration: ${data.duration_minutes} min | ₹${data.credits_deducted} deducted.`,
                "success"
            );
            updateDashboardUI(data, "checkout");

            // Update the first "active" row in the attendance table
            updateActiveAttendanceRow({
                exit: formatTime(data.exit_time),
                duration: data.duration_minutes,
                credits: data.credits_deducted,
            });
        } else {
            showToast(data.message, "error");
            btn.disabled = false;
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
        btn.disabled = false;
    }

    setButtonLoading(btn, false);
}


// ═══════════════════════════════════════════════════════════════════════════
// Recharge Handler (unchanged — no QR required)
// ═══════════════════════════════════════════════════════════════════════════

async function handleRecharge() {
    const amountInput = document.getElementById("recharge-amount");
    const amount = parseFloat(amountInput.value);

    if (!amount || amount <= 0) {
        showToast("Please enter a valid amount greater than 0.", "error");
        return;
    }

    const btn = document.getElementById("recharge-submit-btn");
    setButtonLoading(btn, true);

    try {
        const response = await fetch("/recharge/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify({ amount: amount }),
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, "success");

            // Update wallet balance display
            const balanceEl = document.getElementById("wallet-balance");
            balanceEl.innerHTML = `<span class="currency">₹</span>${data.wallet_balance}`;

            // Add transaction row
            addTransactionRow(amount);

            // Close modal and reset input
            closeRechargeModal();
            amountInput.value = "";
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
    }

    setButtonLoading(btn, false);
    btn.disabled = false;
}


// ─── Recharge Modal Controls ───
function openRechargeModal() {
    const modal = document.getElementById("recharge-modal");
    modal.classList.add("active");
    // Focus the amount input after transition
    setTimeout(() => {
        document.getElementById("recharge-amount").focus();
    }, 300);
}

function closeRechargeModal() {
    const modal = document.getElementById("recharge-modal");
    modal.classList.remove("active");
}

function setRechargeAmount(amount) {
    document.getElementById("recharge-amount").value = amount;
}


// ─── Table Row Helpers ───

/**
 * Add a new row to the top of the attendance table.
 */
function addAttendanceRow({ date, entry, exit, duration, credits, active }) {
    const tbody = document.getElementById("attendance-tbody");

    // Remove empty state row if present
    const emptyRow = tbody.querySelector(".empty-state");
    if (emptyRow) {
        emptyRow.closest("tr").remove();
    }

    const row = document.createElement("tr");
    row.setAttribute("data-active", "true");
    row.innerHTML = `
        <td>${date}</td>
        <td>${entry}</td>
        <td>${exit ? exit : '<span class="badge badge-active">—</span>'}</td>
        <td>${duration !== null ? duration + " min" : '<span class="badge badge-active">Ongoing</span>'}</td>
        <td>${credits !== null ? "₹" + credits : "—"}</td>
        <td><span class="badge ${active ? "badge-active" : "badge-completed"}">${active ? "Inside" : "Completed"}</span></td>
    `;

    // Insert at the top
    tbody.insertBefore(row, tbody.firstChild);
}

/**
 * Update the currently active attendance row (the first row with data-active="true").
 */
function updateActiveAttendanceRow({ exit, duration, credits }) {
    const tbody = document.getElementById("attendance-tbody");
    const activeRow = tbody.querySelector('tr[data-active="true"]');

    if (activeRow) {
        const cells = activeRow.querySelectorAll("td");
        cells[2].innerHTML = exit;
        cells[3].innerHTML = duration + " min";
        cells[4].innerHTML = "₹" + credits;
        cells[5].innerHTML = '<span class="badge badge-completed">Completed</span>';
        activeRow.removeAttribute("data-active");
    }
}

/**
 * Add a new row to the top of the transaction table.
 */
function addTransactionRow(amount) {
    const tbody = document.getElementById("transaction-tbody");

    // Remove empty state row if present
    const emptyRow = tbody.querySelector(".empty-state");
    if (emptyRow) {
        emptyRow.closest("tr").remove();
    }

    const now = new Date();
    const dateStr = now.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
    const timeStr = now.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    });

    const row = document.createElement("tr");
    row.innerHTML = `
        <td>${dateStr} — ${timeStr}</td>
        <td>Wallet Recharge — +${amount} credits</td>
        <td class="amount-positive">+₹${parseFloat(amount).toFixed(2)}</td>
    `;

    tbody.insertBefore(row, tbody.firstChild);
}


// ─── Event Listeners ───
document.addEventListener("DOMContentLoaded", () => {
    // Close modals on backdrop click
    const rechargeOverlay = document.getElementById("recharge-modal");
    if (rechargeOverlay) {
        rechargeOverlay.addEventListener("click", (e) => {
            if (e.target === rechargeOverlay) {
                closeRechargeModal();
            }
        });
    }

    const qrOverlay = document.getElementById("qr-scanner-modal");
    if (qrOverlay) {
        qrOverlay.addEventListener("click", (e) => {
            if (e.target === qrOverlay) {
                closeQRScanner();
            }
        });
    }

    // Close modals on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeRechargeModal();
            closeQRScanner();
        }
    });

    // Submit recharge on Enter key inside the amount input
    const amountInput = document.getElementById("recharge-amount");
    if (amountInput) {
        amountInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                handleRecharge();
            }
        });
    }
});
