document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const textInput = document.getElementById('text-input');
    const urlInput = document.getElementById('url-input');
    const fileInput = document.getElementById('file-input');
    
    const dropzone = document.getElementById('dropzone');
    const dropzoneEmpty = document.getElementById('dropzone-empty');
    const dropzonePreview = document.getElementById('dropzone-preview');
    const previewImage = document.getElementById('preview-image');
    const clearImageBtn = document.getElementById('clear-image-btn');
    
    const analyzeBtn = document.getElementById('analyze-btn');
    const analyzeBtnText = document.getElementById('analyze-btn-text');
    
    const loadingOverlay = document.getElementById('loading-overlay');
    const commandCenterCard = document.getElementById('command-center-card');
    
    const resultsContainer = document.getElementById('results-container');
    
    let currentImageBase64 = null;
    
    // --- Validation ---
    const isValidUrl = (string) => {
        try { const url = new URL(string); return url.protocol === 'https:'; }
        catch (_) { return false; }
    };

    const validateInputs = () => {
        const hasText = textInput.value.trim().length > 10;
        const hasUrl = isValidUrl(urlInput.value);
        const hasImg = currentImageBase64 !== null;
        
        if (hasText || hasUrl || hasImg) {
            analyzeBtn.removeAttribute('disabled');
        } else {
            analyzeBtn.setAttribute('disabled', 'true');
        }
    };

    // --- Input Handlers ---
    textInput.addEventListener('input', () => {
        if (textInput.value) {
            urlInput.value = '';
            clearImage();
        }
        validateInputs();
    });

    urlInput.addEventListener('input', () => {
        if (urlInput.value) {
            textInput.value = '';
            clearImage();
        }
        validateInputs();
    });

    // --- Image Upload Handlers ---
    const handleImageFile = (file) => {
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            currentImageBase64 = e.target.result;
            previewImage.src = currentImageBase64;
            dropzoneEmpty.classList.add('hidden');
            dropzonePreview.classList.remove('hidden');
            dropzonePreview.classList.add('flex');
            dropzone.classList.add('border-none', 'p-1', 'bg-surface-900');
            fileInput.classList.add('hidden');
            
            textInput.value = '';
            urlInput.value = '';
            validateInputs();
        };
        reader.readAsDataURL(file);
    };

    const clearImage = () => {
        currentImageBase64 = null;
        previewImage.src = '';
        dropzoneEmpty.classList.remove('hidden');
        dropzonePreview.classList.add('hidden');
        dropzonePreview.classList.remove('flex');
        dropzone.classList.remove('border-none', 'p-1', 'bg-surface-900');
        fileInput.classList.remove('hidden');
        validateInputs();
    };

    clearImageBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        clearImage();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageFile(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('border-primary', 'bg-primary/5'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('border-primary', 'bg-primary/5'), false);
    });

    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleImageFile(e.dataTransfer.files[0]);
        }
    });

    // --- Analyze Submission ---
    analyzeBtn.addEventListener('click', () => {
        // Show Loading
        loadingOverlay.classList.remove('hidden');
        commandCenterCard.classList.add('opacity-50', 'pointer-events-none');
        analyzeBtnText.textContent = "Analyzing...";
        resultsContainer.innerHTML = '';
        resultsContainer.classList.add('hidden');
        
        // Mock Delay
        setTimeout(() => {
            renderResults();
            lucide.createIcons();
            
            // Hide Loading
            loadingOverlay.classList.add('hidden');
            commandCenterCard.classList.remove('opacity-50', 'pointer-events-none');
            analyzeBtnText.textContent = "Analyze Context";
            
            resultsContainer.classList.remove('hidden');
            resultsContainer.classList.add('flex');
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 2500);
    });

    // --- UI Renderers ---
    const getRadialGaugeHtml = (value, label, type) => {
        let colorClass = 'text-primary';
        let iconName = '';
        
        if (type === 'risk') {
            if (value > 0.7) { colorClass = 'text-alert'; iconName = 'shield-alert'; }
            else if (value > 0.4) { colorClass = 'text-warning'; iconName = 'alert-triangle'; }
            else { colorClass = 'text-success'; iconName = 'shield-check'; }
        } else {
            if (value > 0.7) { colorClass = 'text-success'; iconName = 'shield-check'; }
            else if (value > 0.4) { colorClass = 'text-warning'; iconName = 'alert-triangle'; }
            else { colorClass = 'text-alert'; iconName = 'shield-alert'; }
        }

        const radius = 40;
        const circumference = radius * Math.PI;
        const offset = circumference - (value * circumference);
        const pct = Math.round(value * 100);

        return `
            <div class="flex flex-col items-center justify-center p-4 bg-surface-800 rounded-xl border border-white/5 relative group hover:border-white/10 transition-colors">
                <div class="relative w-32 h-20 overflow-hidden flex justify-center items-end pb-2">
                    <svg class="absolute top-0 w-32 h-32 transform -rotate-180" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="${radius}" fill="transparent" stroke="rgba(255,255,255,0.05)" stroke-width="10" stroke-dasharray="${circumference} ${circumference}" stroke-linecap="round"></circle>
                        <circle cx="50" cy="50" r="${radius}" fill="transparent" stroke="currentColor" stroke-width="10" stroke-dasharray="${circumference} ${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round" class="transition-all duration-1000 ease-out drop-shadow-md ${colorClass}"></circle>
                    </svg>
                    <div class="flex flex-col items-center leading-none z-10 translate-y-3">
                        <span class="text-2xl font-bold text-white tracking-tight">${pct}%</span>
                    </div>
                </div>
                <div class="flex items-center gap-1.5 mt-4">
                    <i data-lucide="${iconName}" class="w-3.5 h-3.5 ${colorClass}"></i>
                    <span class="metric-label !mt-0 !w-auto">${label}</span>
                </div>
            </div>
        `;
    };

    const parseMarkdownToHtml = (text) => {
        if (!text) return '';
        let parsed = text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
        parsed = parsed.replace(/\[(\d+)\]([^\.,\s]*\s[\w\s]+?(?=[,\.]|\s|$))/g, (match, id, name) => {
            return `<a href="#source-${id}" class="inline-flex items-center gap-1 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 px-2 py-0.5 rounded-md text-xs font-medium transition-colors cursor-pointer mx-1 no-underline"><span class="opacity-70">[${id}]</span>${name}</a>`;
        });
        return parsed;
    };

    const renderResults = () => {
        // Only rendering text analysis for now to match structure
        
        const scores = { confidence_score: 0.85, credibility_avg: 0.92, recency_score: 0.98, conflict_score: 0.15, ai_risk_score: 0.05, sensitivity_score: 0.3 };
        
        const summary = "The claims presented indicate a **strong alignment** with verified news sources. According to [1] Reuters, the events occurred exactly as described. However, [2] BBC News notes some minor discrepancies in the timeline.";
        
        const sources = [
            { url: "#", domain: "reuters.com", title: "Global Event Confirmed By Authorities", credibility_score: 0.95, content: "Full verified text from Reuters detailing the timeline of events. The authorities have confirmed that the incident took place at exactly 1:00 PM.", fact_check_status: "VERIFIED" },
            { url: "#", domain: "bbc.com", title: "Timeline Discrepancies in Recent Event", credibility_score: 0.88, content: "BBC analysis shows that while the main event happened, the time was actually reported as 2:00 PM by some local witnesses." },
            { url: "#", domain: "sketchy-news.net", title: "The Truth They Are Hiding", credibility_score: 0.20, content: "They want you to believe it happened at 1 PM, but it never happened at all!", fact_check_status: "DEBUNKED" }
        ];

        let sourcesHtml = sources.map((s, idx) => {
            const credClass = s.credibility_score > 0.7 ? "bg-success" : s.credibility_score > 0.4 ? "bg-warning" : "bg-alert";
            const isRecent = idx < 2; 
            
            let badges = isRecent ? `<span class="text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 px-1.5 py-0.5 rounded uppercase tracking-wider">New</span>` : '';
            if (s.fact_check_status === 'DEBUNKED') badges += `<span class="flex items-center gap-1 text-[10px] font-bold bg-alert/10 text-alert border border-alert/20 px-1.5 py-0.5 rounded uppercase tracking-wider"><i data-lucide="x-circle" class="w-3 h-3"></i> Debunked</span>`;
            if (s.fact_check_status === 'VERIFIED') badges += `<span class="flex items-center gap-1 text-[10px] font-bold bg-success/10 text-success border border-success/20 px-1.5 py-0.5 rounded uppercase tracking-wider"><i data-lucide="check-circle" class="w-3 h-3"></i> Verified</span>`;

            return `
                <div id="source-${idx + 1}" class="bg-surface-800 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors flex flex-col gap-3">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex items-center gap-2 overflow-hidden">
                            <img src="https://www.google.com/s2/favicons?domain=${s.domain}&sz=32" alt="" class="w-5 h-5 rounded-sm bg-white" />
                            <span class="text-sm font-medium text-text-muted truncate">${s.domain}</span>
                        </div>
                        <div class="flex items-center gap-2 flex-shrink-0">${badges}</div>
                    </div>
                    <a href="${s.url}" target="_blank" class="text-white font-medium hover:text-primary transition-colors line-clamp-2">[${idx+1}] ${s.title}</a>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-text-muted w-16">Credibility</span>
                        <div class="flex-1 h-1.5 bg-surface-950 rounded-full overflow-hidden">
                            <div class="h-full rounded-full ${credClass}" style="width: ${Math.max(5, s.credibility_score * 100)}%"></div>
                        </div>
                        <span class="text-xs font-semibold text-white">${Math.round(s.credibility_score * 100)}%</span>
                    </div>
                    <div class="mt-2 pt-3 border-t border-white/5 relative">
                        <p class="text-sm text-text-muted leading-relaxed">${s.content}</p>
                    </div>
                </div>
            `;
        }).join('');

        resultsContainer.innerHTML = `
            <!-- Reliability Matrix -->
            <div class="glass-card p-6 md:p-8">
                <h2 class="text-xl font-semibold mb-6 flex items-center gap-2 text-white">
                    Reliability Matrix
                    <span class="text-xs font-normal text-text-muted bg-surface-800 px-2 py-1 rounded-md border border-white/10">Multivector Analysis</span>
                </h2>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    ${getRadialGaugeHtml(scores.confidence_score, 'Confidence', 'confidence')}
                    ${getRadialGaugeHtml(scores.credibility_avg, 'Credibility', 'confidence')}
                    ${getRadialGaugeHtml(scores.recency_score, 'Recency', 'confidence')}
                    ${getRadialGaugeHtml(scores.conflict_score, 'Conflict', 'risk')}
                    ${getRadialGaugeHtml(scores.ai_risk_score, 'AI Risk', 'risk')}
                    ${getRadialGaugeHtml(scores.sensitivity_score, 'Sensitivity', 'risk')}
                </div>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                <!-- Context Synthesis -->
                <div class="lg:col-span-2 glass-card p-6 md:p-8 h-full flex flex-col">
                    <div class="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
                        <i data-lucide="file-text" class="w-5 h-5 text-primary"></i>
                        <h2 class="text-xl font-semibold text-white">Context Synthesis</h2>
                    </div>
                    <div class="prose prose-invert max-w-none text-text leading-relaxed text-sm md:text-base">
                        <p class="whitespace-pre-wrap">${parseMarkdownToHtml(summary)}</p>
                    </div>
                </div>
                
                <!-- Source Feed -->
                <div class="lg:col-span-1 glass-card p-6 h-full flex flex-col">
                    <div class="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
                        <div class="flex items-center gap-3">
                            <i data-lucide="database" class="w-5 h-5 text-primary"></i>
                            <h2 class="text-lg font-semibold text-white">Source Verification</h2>
                        </div>
                        <span class="text-xs text-text-muted">3 Retrieved</span>
                    </div>
                    <div class="flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar" style="max-height: 600px;">
                        ${sourcesHtml}
                    </div>
                </div>
            </div>
        `;
    };

});
