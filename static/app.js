document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const providerSelect = document.getElementById("provider-select");
    const apiKeyGroup = document.getElementById("api-key-group");
    const apiKeyInput = document.getElementById("api-key-input");
    const jdTextarea = document.getElementById("jd-textarea");
    const saveJdBtn = document.getElementById("save-jd-btn");
    const runScreenBtn = document.getElementById("run-screen-btn");
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const uploadStatus = document.getElementById("upload-status");
    const downloadActions = document.getElementById("download-actions");
    const statsBar = document.getElementById("stats-bar");
    const loadingOverlay = document.getElementById("loading-overlay");
    const candidatesList = document.getElementById("candidates-list");
    const activeProviderBadge = document.getElementById("active-provider-badge");
    const activeProviderText = document.getElementById("active-provider-text");
    const toast = document.getElementById("toast");

    // Stats Elements
    const statTotal = document.getElementById("stat-total-resumes");
    const statAvg = document.getElementById("stat-avg-score");
    const statOutstanding = document.getElementById("stat-outstanding");

    // Init state
    let isUploading = false;

    // Load Job Description on startup
    fetchJd();
    
    // Load candidates on startup (if any exist)
    fetchCandidates();

    /* ==========================================================================
       Event Listeners
       ========================================================================== */

    // Provider select logic
    providerSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val === "mock") {
            apiKeyGroup.style.display = "none";
            updateProviderBadge("mock", "Mock Engine Active");
        } else if (val === "groq") {
            apiKeyGroup.style.display = "block";
            updateProviderBadge("groq", "Groq Llama-3 Active");
        }
    });

    // Save Job Description
    saveJdBtn.addEventListener("click", async () => {
        const text = jdTextarea.value.trim();
        if (!text) {
            showToast("Job description cannot be empty", "error");
            return;
        }

        saveJdBtn.disabled = true;
        saveJdBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;

        try {
            const res = await fetch("/api/job-description", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_description: text })
            });
            const data = await res.json();
            if (data.success) {
                showToast("Job Description saved successfully!", "success");
            } else {
                showToast(data.error || "Failed to save job description", "error");
            }
        } catch (e) {
            showToast("Network error saving job description", "error");
        } finally {
            saveJdBtn.disabled = false;
            saveJdBtn.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Save Job Description`;
        }
    });

    // Analyze Job Description with AI
    const analyzeJdBtn = document.getElementById("analyze-jd-btn");
    const jdAnalysisResult = document.getElementById("jd-analysis-result");
    
    analyzeJdBtn.addEventListener("click", async () => {
        const text = jdTextarea.value.trim();
        if (!text) {
            showToast("Job description cannot be empty", "error");
            return;
        }
        
        analyzeJdBtn.disabled = true;
        analyzeJdBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;
        jdAnalysisResult.style.display = "block";
        jdAnalysisResult.innerHTML = `<div style="padding: 15px; text-align: center; color: var(--text-muted); font-size: 0.85rem;"><i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing Job Description...</div>`;
        
        try {
            const res = await fetch("/api/analyze-jd", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_description: text })
            });
            const data = await res.json();
            
            if (data.success && data.analysis) {
                const ana = data.analysis;
                let html = `
                    <div class="jd-analysis-output mt-15" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 15px; font-size: 0.85rem; line-height: 1.4; text-align: left;">
                        <h4 style="color: var(--primary); margin-bottom: 8px;"><i class="fa-solid fa-address-card"></i> ${ana.job_title || "Job Title"}</h4>
                        
                        <div style="margin-bottom: 8px;">
                            <strong>Experience:</strong> ${ana.minimum_experience}+ years ${ana.maximum_experience ? `(up to ${ana.maximum_experience} years)` : ""}<br>
                            <strong>Education:</strong> ${ana.education_requirements.join(", ") || "None specified"}
                        </div>
                        
                        <div style="margin-bottom: 8px;">
                            <strong style="color: var(--success);">Required Skills:</strong>
                            <div class="badge-cloud mt-5" style="gap: 4px; display: flex; flex-wrap: wrap;">
                                ${ana.required_skills.map(x => `<span class="badge-item match" style="font-size: 0.7rem; padding: 2px 6px;">${x}</span>`).join("")}
                            </div>
                        </div>
                        
                        ${ana.preferred_skills && ana.preferred_skills.length > 0 ? `
                        <div style="margin-bottom: 8px;">
                            <strong style="color: var(--secondary);">Preferred Skills:</strong>
                            <div class="badge-cloud mt-5" style="gap: 4px; display: flex; flex-wrap: wrap;">
                                ${ana.preferred_skills.map(x => `<span class="badge-item" style="font-size: 0.7rem; padding: 2px 6px; background: rgba(255,255,255,0.05);">${x}</span>`).join("")}
                            </div>
                        </div>` : ""}
                        
                        ${ana.responsibilities && ana.responsibilities.length > 0 ? `
                        <div style="margin-bottom: 8px;">
                            <strong>Responsibilities:</strong>
                            <ul style="padding-left: 15px; color: var(--text-muted); margin-top: 4px; list-style-type: disc;">
                                ${ana.responsibilities.map(x => `<li style="margin-bottom: 2px;">${x}</li>`).join("")}
                            </ul>
                        </div>` : ""}
                        
                        ${ana.keywords && ana.keywords.length > 0 ? `
                        <div>
                            <strong>Keywords:</strong> ${ana.keywords.join(", ")}
                        </div>` : ""}
                    </div>
                `;
                jdAnalysisResult.innerHTML = html;
                showToast("Job description analyzed!", "success");
            } else {
                jdAnalysisResult.innerHTML = `<div style="padding: 15px; color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-triangle-exclamation"></i> ${data.error || "Failed to analyze Job Description"}</div>`;
                showToast("JD analysis failed", "error");
            }
        } catch (err) {
            jdAnalysisResult.innerHTML = `<div style="padding: 15px; color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-triangle-exclamation"></i> Network error</div>`;
            showToast("Network error during analysis", "error");
        } finally {
            analyzeJdBtn.disabled = false;
            analyzeJdBtn.innerHTML = `<i class="fa-solid fa-brain"></i> Analyze JD with AI`;
        }
    });

    // Run Screening Pipeline
    runScreenBtn.addEventListener("click", async () => {
        const provider = providerSelect.value;
        const apiKey = apiKeyInput.value.trim();

        if (provider !== "mock" && !apiKey) {
            // Let it fall back to environment variable, but log warning
            showToast("Proceeding using environment key if configured...", "warning");
        }

        showLoading(true);

        try {
            const res = await fetch("/api/screen", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ provider, api_key: apiKey })
            });
            const data = await res.json();
            
            if (data.success) {
                showToast("Screening run completed!", "success");
                renderCandidates(data.candidates);
                // Update header status text to match actual backend resolution
                if (data.provider === "mock") {
                    updateProviderBadge("mock", "Mock Engine Active");
                    providerSelect.value = "mock";
                    apiKeyGroup.style.display = "none";
                } else if (data.provider === "groq") {
                    updateProviderBadge("groq", "Groq Llama-3 Active");
                }
            } else {
                showToast(data.error || "Error running screening", "error");
            }
        } catch (e) {
            showToast("Failed to connect to backend screening API", "error");
        } finally {
            showLoading(false);
        }
    });

    // Drag and Drop Logic
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFilesUpload(files);
    });

    fileInput.addEventListener("change", (e) => {
        handleFilesUpload(e.target.files);
    });

    /* ==========================================================================
       API Interaction Helpers
       ========================================================================== */

    async function fetchJd() {
        try {
            const res = await fetch("/api/job-description");
            const data = await res.json();
            if (data.success) {
                jdTextarea.value = data.job_description;
            }
        } catch (e) {
            console.error("Error loading JD:", e);
        }
    }

    async function fetchCandidates() {
        showLoading(true);
        try {
            const res = await fetch("/api/candidates");
            const data = await res.json();
            if (data.success && data.candidates && data.candidates.length > 0) {
                renderCandidates(data.candidates);
            }
        } catch (e) {
            console.error("Error fetching candidates:", e);
        } finally {
            showLoading(false);
        }
    }

    async function handleFilesUpload(files) {
        if (files.length === 0 || isUploading) return;
        
        isUploading = true;
        uploadStatus.style.display = "block";
        uploadStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading ${files.length} file(s)...`;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("resumes", files[i]);
        }

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                let statusHtml = `<span style="color: var(--success); font-weight: bold;">${data.message}</span>`;
                if (data.errors && data.errors.length > 0) {
                    statusHtml += `<div style="margin-top: 6px; color: var(--danger); font-size: 0.8rem;">` + 
                        data.errors.join("<br>") + `</div>`;
                }
                uploadStatus.innerHTML = statusHtml;
                showToast("Resumes uploaded successfully!", "success");
            } else {
                uploadStatus.innerHTML = `<span style="color: var(--danger);">${data.error || "Upload failed"}</span>`;
                showToast(data.error || "Upload failed", "error");
            }
        } catch (e) {
            uploadStatus.innerHTML = `<span style="color: var(--danger);">Upload network error</span>`;
            showToast("Upload network error", "error");
        } finally {
            isUploading = false;
        }
    }

    /* ==========================================================================
       UI Renderer & Animation Helpers
       ========================================================================== */

    function showLoading(isLoading) {
        if (isLoading) {
            loadingOverlay.classList.add("active");
        } else {
            loadingOverlay.classList.remove("active");
        }
    }

    function updateProviderBadge(provider, text) {
        // Reset dots
        const dot = activeProviderBadge.querySelector(".status-dot");
        dot.className = "status-dot";
        dot.classList.add("dot-" + provider);
        activeProviderText.textContent = text;
    }

    function showToast(message, type = "success") {
        toast.textContent = message;
        toast.className = "toast active";
        if (type === "success") toast.classList.add("toast-success");
        if (type === "error") toast.classList.add("toast-error");
        if (type === "warning") toast.classList.add("toast-warning");

        setTimeout(() => {
            toast.classList.remove("active");
        }, 3000);
    }

    function renderCandidates(candidates) {
        candidatesList.innerHTML = "";
        
        if (!candidates || candidates.length === 0) {
            candidatesList.innerHTML = `
                <div style="padding: 40px; text-align: center; color: var(--text-dim);">
                    <i class="fa-solid fa-folder-open" style="font-size: 3rem; margin-bottom: 12px; display: block;"></i>
                    No candidates screened yet. Upload resumes and click Run Screening.
                </div>`;
            downloadActions.style.display = "none";
            statsBar.style.display = "none";
            return;
        }

        // Show exports and stats
        downloadActions.style.display = "flex";
        statsBar.style.display = "flex";

        // Calculate and render stats
        const total = candidates.length;
        const sumScores = candidates.reduce((acc, c) => acc + c.final_score, 0);
        const avgScore = (sumScores / total).toFixed(1);
        const outstandingCount = candidates.filter(c => c.tier === "Outstanding Match").length;

        statTotal.textContent = total;
        statAvg.textContent = avgScore + "%";
        statOutstanding.textContent = outstandingCount;

        // Render rows
        candidates.forEach((cand, idx) => {
            const rank = idx + 1;
            
            // Format tier class
            let tierClass = "tier-low";
            if (cand.tier === "Outstanding Match") tierClass = "tier-outstanding";
            else if (cand.tier === "Strong Match") tierClass = "tier-strong";
            else if (cand.tier === "Good Match") tierClass = "tier-good";

            const row = document.createElement("div");
            row.className = "candidate-row";
            
            row.innerHTML = `
                <!-- Candidate Header -->
                <div class="candidate-header-row">
                    <div class="rank-badge">${rank}</div>
                    <div class="candidate-meta">
                        <div class="candidate-name">${cand.name}</div>
                        <div class="candidate-subinfo">
                            <i class="fa-solid fa-file-lines"></i> ${cand.filename} | 
                            <i class="fa-solid fa-briefcase"></i> ${cand.years_of_experience} yrs exp | 
                            <i class="fa-solid fa-graduation-cap"></i> ${cand.education}
                        </div>
                    </div>
                    <div class="score-badge-box">
                        <div class="score-pct">${cand.final_score}%</div>
                        <div class="tier-badge ${tierClass}">${cand.tier}</div>
                    </div>
                    <i class="fa-solid fa-chevron-down expand-chevron"></i>
                </div>

                <!-- Candidate Details Drawer -->
                <div class="candidate-detail-drawer">
                    <div class="drawer-content">
                        <!-- Technical score progress bars -->
                        <div class="metrics-section">
                            <div class="metric-card">
                                <h4>Skills (40%)</h4>
                                <div class="metric-num" style="color: var(--primary);">${cand.skill_score}%</div>
                                <div class="metric-bar-container">
                                    <div class="metric-fill metric-fill-skills" data-width="${cand.skill_score}%"></div>
                                </div>
                            </div>
                            <div class="metric-card">
                                <h4>NLP Semantics (30%)</h4>
                                <div class="metric-num" style="color: var(--secondary);">${cand.nlp_score}%</div>
                                <div class="metric-bar-container">
                                    <div class="metric-fill metric-fill-nlp" data-width="${cand.nlp_score}%"></div>
                                </div>
                            </div>
                            <div class="metric-card">
                                <h4>Experience (20%)</h4>
                                <div class="metric-num" style="color: var(--success);">${cand.experience_score}%</div>
                                <div class="metric-bar-container">
                                    <div class="metric-fill metric-fill-exp" data-width="${cand.experience_score}%"></div>
                                </div>
                            </div>
                            <div class="metric-card">
                                <h4>Education (10%)</h4>
                                <div class="metric-num" style="color: var(--warning);">${cand.education_score}%</div>
                                <div class="metric-bar-container">
                                    <div class="metric-fill metric-fill-edu" data-width="${cand.education_score}%"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Technical Skill Pill Tags -->
                        <div class="details-section">
                            <div class="details-block">
                                <h4>Matching Required Skills</h4>
                                <div class="badge-cloud">
                                    ${cand.matching_skills.length > 0 
                                        ? cand.matching_skills.map(s => `<span class="badge-item match"><i class="fa-solid fa-circle-check"></i> ${s}</span>`).join("")
                                        : `<span style="color: var(--text-dim); font-size: 0.8rem; font-style: italic;">No direct skill matches</span>`}
                                </div>
                            </div>
                            <div class="details-block">
                                <h4>Missing Required Skills</h4>
                                <div class="badge-cloud">
                                    ${cand.missing_skills.length > 0 
                                        ? cand.missing_skills.map(s => `<span class="badge-item missing"><i class="fa-solid fa-circle-xmark"></i> ${s}</span>`).join("")
                                        : `<span style="color: var(--success); font-size: 0.8rem; font-weight: bold;"><i class="fa-solid fa-check-double"></i> All skills matching!</span>`}
                                </div>
                            </div>
                        </div>

                        <!-- Candidate Contact Info -->
                        <div style="margin-bottom: 20px; font-size: 0.85rem; color: var(--text-muted); display: flex; gap: 20px;">
                            <span><i class="fa-solid fa-envelope"></i> Email: <a href="mailto:${cand.email}" style="color: var(--primary); text-decoration: none;">${cand.email}</a></span>
                            <span><i class="fa-solid fa-phone"></i> Phone: ${cand.phone}</span>
                        </div>

                        <!-- AI Reasoning block -->
                        <div class="reasoning-block">
                            <h4>Agent Suitability Reasoning</h4>
                            <div style="margin-top: 8px;">
                                ${formatReasoning(cand.reasoning)}
                            </div>
                        </div>

                        <!-- AI Resume Improvement Block -->
                        <div class="improvement-block mt-20" style="border-top: 1px solid var(--border-color); padding-top: 15px; text-align: left;">
                            <button class="btn btn-outline btn-small improve-resume-btn">
                                <i class="fa-solid fa-graduation-cap"></i> Improve Resume with AI
                            </button>
                            <div class="resume-improvement-suggestions mt-10" style="display: none;"></div>
                        </div>
                    </div>
                </div>`;
            
            // Hook up Improve Resume with AI button click handler
            const improveBtn = row.querySelector(".improve-resume-btn");
            const suggestionsDiv = row.querySelector(".resume-improvement-suggestions");
            
            improveBtn.addEventListener("click", async (e) => {
                e.stopPropagation(); // prevent drawer toggle from clicking inside drawer
                
                improveBtn.disabled = true;
                improveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Improving...`;
                suggestionsDiv.style.display = "block";
                suggestionsDiv.innerHTML = `<div style="padding: 10px; color: var(--text-muted); font-size: 0.85rem;"><i class="fa-solid fa-circle-notch fa-spin"></i> Gaining insights from Groq...</div>`;
                
                try {
                    const res = await fetch("/api/improve-resume", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            resume_text: cand.resume_text || "",
                            job_description: jdTextarea.value.trim(),
                            candidate_result: cand
                        })
                    });
                    const data = await res.json();
                    
                    if (data.success && data.suggestions) {
                        const sug = data.suggestions;
                        let html = `
                            <div class="sug-container mt-10" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 15px; text-align: left;">
                                <h4 style="color: var(--primary); margin-bottom: 8px; font-size: 0.95rem;"><i class="fa-solid fa-gauge-high"></i> ATS Fit Summary</h4>
                                <p style="font-size: 0.85rem; line-height: 1.5; color: var(--text-main); margin-bottom: 12px;">${sug.current_match_summary}</p>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 12px;">
                                    <div>
                                        <h5 style="color: var(--success); margin-bottom: 6px; font-size: 0.85rem;"><i class="fa-solid fa-circle-check"></i> Strengths</h5>
                                        <ul style="padding-left: 15px; font-size: 0.8rem; color: var(--text-muted); list-style-type: disc;">
                                            ${sug.strengths.map(x => `<li style="margin-bottom: 4px;">${x}</li>`).join("")}
                                        </ul>
                                    </div>
                                    <div>
                                        <h5 style="color: var(--danger); margin-bottom: 6px; font-size: 0.85rem;"><i class="fa-solid fa-circle-xmark"></i> Missing/Weak Areas</h5>
                                        <ul style="padding-left: 15px; font-size: 0.8rem; color: var(--text-muted); list-style-type: disc;">
                                            ${sug.missing_or_weak_areas.map(x => `<li style="margin-bottom: 4px;">${x}</li>`).join("")}
                                        </ul>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <h5 style="color: var(--warning); margin-bottom: 6px; font-size: 0.85rem;"><i class="fa-solid fa-key"></i> Keywords to Highlight</h5>
                                    <div class="badge-cloud" style="gap: 6px; display: flex; flex-wrap: wrap;">
                                        ${sug.keywords_to_highlight.map(x => `<span class="badge-item match" style="font-size: 0.75rem; padding: 3px 8px;"><i class="fa-solid fa-tag"></i> ${x}</span>`).join("")}
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <h5 style="color: var(--secondary); margin-bottom: 6px; font-size: 0.85rem;"><i class="fa-solid fa-pen-to-square"></i> Experience/Project Improvements</h5>
                                    <ul style="padding-left: 15px; font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; list-style-type: disc;">
                                        ${sug.resume_improvements.map(x => `<li style="margin-bottom: 4px;">${x}</li>`).join("")}
                                        ${sug.project_suggestions.map(x => `<li style="margin-bottom: 4px; font-style: italic;">Project Idea: ${x}</li>`).join("")}
                                        ${sug.bullet_point_improvements.map(x => `<li style="margin-bottom: 4px;">${x}</li>`).join("")}
                                    </ul>
                                </div>
                                
                                <div>
                                    <h5 style="color: var(--primary); margin-bottom: 6px; font-size: 0.85rem;"><i class="fa-solid fa-circle-nodes"></i> Action Plan</h5>
                                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                                        <strong>🔥 High Priority:</strong> ${sug.priority_action_plan.high.join(", ") || "None"}<br>
                                        <strong>⚡ Medium Priority:</strong> ${sug.priority_action_plan.medium.join(", ") || "None"}<br>
                                        <strong>⭐ Low Priority:</strong> ${sug.priority_action_plan.low.join(", ") || "None"}
                                    </div>
                                </div>
                            </div>
                        `;
                        suggestionsDiv.innerHTML = html;
                        showToast("Resume suggestions loaded!", "success");
                    } else {
                        suggestionsDiv.innerHTML = `<div style="padding: 10px; color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-triangle-exclamation"></i> ${data.error || "Failed to analyze resume"}</div>`;
                        showToast("Resume improvement failed", "error");
                    }
                } catch (err) {
                    suggestionsDiv.innerHTML = `<div style="padding: 10px; color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-triangle-exclamation"></i> Network error</div>`;
                    showToast("Network error during analysis", "error");
                } finally {
                    improveBtn.disabled = false;
                    improveBtn.innerHTML = `<i class="fa-solid fa-graduation-cap"></i> Improve Resume with AI`;
                }
            });
            
            // Drawer Expand/Collapse Logic
            const header = row.querySelector(".candidate-header-row");
            header.addEventListener("click", () => {
                const isExpanded = row.classList.contains("expanded");
                
                // Collapse all first (accordion style)
                document.querySelectorAll(".candidate-row").forEach(r => {
                    r.classList.remove("expanded");
                    // Reset metric fills in other rows
                    r.querySelectorAll(".metric-fill").forEach(bar => {
                        bar.style.width = "0%";
                    });
                });

                if (!isExpanded) {
                    row.classList.add("expanded");
                    // Animate the progress bars of the expanded row
                    row.querySelectorAll(".metric-fill").forEach(bar => {
                        const targetWidth = bar.getAttribute("data-width");
                        setTimeout(() => {
                            bar.style.width = targetWidth;
                        }, 50); // slight delay for smooth render
                    });
                }
            });

            candidatesList.appendChild(row);
        });
    }

    // Convert markdown bullet points to HTML list
    function formatReasoning(reasoningText) {
        if (!reasoningText) return "";
        
        // Split by lines
        const lines = reasoningText.split("\n");
        let html = "<ul style='padding-left: 0; list-style-type: none;'>";
        
        lines.forEach(line => {
            const clean = line.trim();
            if (clean.startsWith("-") || clean.startsWith("*")) {
                // bullet point
                let inner = clean.substring(1).trim();
                
                // Replace bold markdown **text** with <strong>text</strong>
                inner = inner.replace(/\*\*(.*?)\*\*/g, "<strong style='color: var(--primary);'>$1</strong>");
                
                html += `<li style="margin-bottom: 8px; font-size: 0.9rem; line-height: 1.5; color: var(--text-main); display: flex; align-items: start; gap: 8px;">
                    <i class="fa-solid fa-angle-right" style="color: var(--secondary); margin-top: 4px; font-size: 0.8rem;"></i>
                    <div>${inner}</div>
                </li>`;
            } else if (clean) {
                // general text line
                let inner = clean;
                inner = inner.replace(/\*\*(.*?)\*\*/g, "<strong style='color: var(--primary);'>$1</strong>");
                html += `<p style="margin-bottom: 8px; font-size: 0.9rem; line-height: 1.5; color: var(--text-main);">${inner}</p>`;
            }
        });
        
        html += "</ul>";
        return html;
    }
});
