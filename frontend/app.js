document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatMessages = document.getElementById("chatMessages");
    const historyList = document.getElementById("historyList");
    const rawJsonCode = document.getElementById("rawJsonCode");
    const cotStepsList = document.getElementById("cotStepsList");
    const reactThought = document.getElementById("reactThought");
    const reactAction = document.getElementById("reactAction");
    const reactObservation = document.getElementById("reactObservation");
    const copyJsonBtn = document.getElementById("copyJsonBtn");
    
    const footerIntent = document.getElementById("footerIntent");
    const footerRisk = document.getElementById("footerRisk");
    
    let activeJsonData = null;

    // --- TAB SWITCHING SYSTEM ---
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const tabId = `tab-${btn.dataset.tab}`;
            document.getElementById(tabId).classList.add("active");
        });
    });

    // --- COPY JSON BUTTON ---
    copyJsonBtn.addEventListener("click", () => {
        if (activeJsonData) {
            navigator.clipboard.writeText(JSON.stringify(activeJsonData, null, 2))
                .then(() => {
                    const originalText = copyJsonBtn.textContent;
                    copyJsonBtn.textContent = "COPIED!";
                    copyJsonBtn.style.backgroundColor = "var(--neon-teal)";
                    setTimeout(() => {
                        copyJsonBtn.textContent = originalText;
                        copyJsonBtn.style.backgroundColor = "#FFF";
                    }, 1500);
                })
                .catch(err => console.error("Could not copy text: ", err));
        }
    });

    // --- FETCH SESSION HISTORY ---
    async function loadHistory() {
        try {
            const res = await fetch("/api/history");
            if (!res.ok) throw new Error("History request failed");
            const history = await res.ok ? await res.json() : [];
            
            renderHistoryList(history);
        } catch (err) {
            console.error("Error loading history:", err);
        }
    }

    function renderHistoryList(history) {
        historyList.innerHTML = "";
        
        if (history.length === 0) {
            historyList.innerHTML = `<div class="no-history-msg">No logs stored yet. Start chatting!</div>`;
            return;
        }

        // Display newest first
        const sortedHistory = [...history].reverse();

        sortedHistory.forEach((item, index) => {
            const historyItem = document.createElement("div");
            historyItem.className = `history-item`;
            
            // Assign color badge based on risk level
            const riskClass = getRiskBadgeClass(item.risk_level);
            
            historyItem.innerHTML = `
                <div class="history-item-header">
                    <span class="history-time">${formatTime(item.timestamp)}</span>
                    <span class="risk-badge ${riskClass}" style="font-size: 0.65rem; padding: 1px 5px;">${item.risk_level}</span>
                </div>
                <div class="history-item-body">
                    <strong>Q:</strong> ${escapeHtml(item.query)}
                </div>
            `;
            
            // Load this specific historical session's data in the inspector on click
            historyItem.addEventListener("click", () => {
                // Remove active class from all
                document.querySelectorAll(".history-item").forEach(el => el.classList.remove("active"));
                historyItem.classList.add("active");
                
                // Load into Inspector
                inspectData(item.full_data || item);
                
                // Also display the historical exchange in the chat message field if wanted,
                // or just load the JSON data into the inspector.
            });
            
            historyList.appendChild(historyItem);
        });
    }

    // --- LOAD JSON INTO INSPECTOR ---
    function inspectData(data) {
        activeJsonData = data;
        
        // Populate RAW_JSON tab
        rawJsonCode.textContent = JSON.stringify(data, null, 2);
        
        // Populate Reasoning CoT tab
        cotStepsList.innerHTML = "";
        const steps = data.reasoning_steps || [];
        if (steps.length === 0) {
            cotStepsList.innerHTML = `<li class="cot-placeholder">No reasoning steps available.</li>`;
        } else {
            steps.forEach(step => {
                const li = document.createElement("li");
                li.textContent = step;
                cotStepsList.appendChild(li);
            });
        }

        // Populate ReAct steps
        reactThought.textContent = data.react_thought || "N/A";
        reactAction.textContent = data.react_action || "N/A";
        reactObservation.textContent = data.react_observation || "N/A";

        // Update footer info
        footerIntent.textContent = data.intent || "unknown";
        footerRisk.className = `risk-badge ${getRiskBadgeClass(data.risk_level)}`;
        footerRisk.textContent = data.risk_level || "-";
    }

    // --- CHAT MESSAGE SYSTEM ---
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // Clear input field
        userInput.value = "";

        // Append user query to chat window
        appendMessage("USER", messageText, "user-msg");

        // Show typing indicator
        const typingIndicator = showTypingIndicator();

        try {
            // Post to backend
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: messageText })
            });

            // Remove typing indicator
            typingIndicator.remove();

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Server error occurred");
            }

            const data = await res.json();
            
            // Append assistant response
            const metaInfo = `risk_level: ${data.risk_level} | intent: ${data.intent}`;
            appendMessage("ViperAI", data.response, "assistant-msg", metaInfo);
            
            // Inspect the response JSON immediately
            inspectData(data);
            
            // Reload history panel
            loadHistory();
            
        } catch (err) {
            typingIndicator.remove();
            appendMessage("ViperAI // System", `Error: ${err.message}`, "assistant-msg", "error");
            console.error("Chat Error:", err);
        }
    });

    function appendMessage(sender, text, className, meta = null) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;
        
        let contentHtml = `
            <div class="msg-sender">${sender}</div>
            <div class="msg-content">${escapeHtml(text)}</div>
        `;
        
        if (meta) {
            contentHtml += `<div class="msg-meta">${meta}</div>`;
        }
        
        msgDiv.innerHTML = contentHtml;
        chatMessages.appendChild(msgDiv);
        
        // Auto scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const indicatorDiv = document.createElement("div");
        indicatorDiv.className = "message assistant-msg";
        indicatorDiv.innerHTML = `
            <div class="msg-sender">ViperAI // Thinking</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatMessages.appendChild(indicatorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicatorDiv;
    }

    // --- HELPER UTILITIES ---
    function getRiskBadgeClass(riskLevel) {
        switch (riskLevel?.toLowerCase()) {
            case "safe": return "badge-safe";
            case "low": return "badge-low";
            case "medium": return "badge-medium";
            case "high": return "badge-high";
            default: return "badge-neutral";
        }
    }

    function formatTime(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return "";
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- INITIAL LOADING ---
    loadHistory();
});
