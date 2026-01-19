/**
 * 引継ぎくん - フロントエンドアプリケーション
 * htmx + Vanilla JS
 */

// ==========================================================================
// State Management
// ==========================================================================
const state = {
    sessionId: null,
    currentPhase: 'upload',
    eventSource: null,
};

// ==========================================================================
// DOM Elements
// ==========================================================================
const elements = {
    // Phases
    uploadPhase: document.getElementById('upload-phase'),
    processingPhase: document.getElementById('processing-phase'),
    policyPhase: document.getElementById('policy-phase'),
    analyzingPhase: document.getElementById('analyzing-phase'),
    completePhase: document.getElementById('complete-phase'),

    // Upload
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    businessTitle: document.getElementById('business-title'),
    authorName: document.getElementById('author-name'),
    additionalNotes: document.getElementById('additional-notes'),

    // Processing
    statusText: document.getElementById('status-text'),
    stepUpload: document.getElementById('step-upload'),
    stepProcess: document.getElementById('step-process'),
    stepAnalyze: document.getElementById('step-analyze'),

    // Question
    questionCard: document.getElementById('question-card'),
    questionText: document.getElementById('question-text'),
    questionInput: document.getElementById('question-input'),
    skipBtn: document.getElementById('skip-btn'),
    answerBtn: document.getElementById('answer-btn'),

    // Policy
    policyTextarea: document.getElementById('policy-textarea'),
    startAnalysisBtn: document.getElementById('start-analysis-btn'),

    // Analyzing
    encouragingMessage: document.getElementById('encouraging-message'),

    // Complete
    analysisResult: document.getElementById('analysis-result'),
    documentPreview: document.getElementById('document-preview'),
    generateDocBtn: document.getElementById('generate-doc-btn'),
    copyBtn: document.getElementById('copy-btn'),

    // Hidden
    sessionIdInput: document.getElementById('session-id'),
};

// ==========================================================================
// Phase Management
// ==========================================================================
function showPhase(phaseName) {
    // Hide all phases
    document.querySelectorAll('.phase').forEach(phase => {
        phase.classList.remove('active');
    });

    // Show target phase
    const targetPhase = document.getElementById(`${phaseName}-phase`);
    if (targetPhase) {
        targetPhase.classList.add('active');
        state.currentPhase = phaseName;
    }
}

function updateProgressSteps(currentStep) {
    const steps = ['upload', 'process', 'analyze'];
    const currentIndex = steps.indexOf(currentStep);

    steps.forEach((step, index) => {
        const stepElement = document.getElementById(`step-${step}`);
        if (!stepElement) return;

        stepElement.classList.remove('active', 'completed');

        if (index < currentIndex) {
            stepElement.classList.add('completed');
        } else if (index === currentIndex) {
            stepElement.classList.add('active');
        }
    });
}

// ==========================================================================
// File Upload
// ==========================================================================
function setupDropZone() {
    const dropZone = elements.dropZone;
    const fileInput = elements.fileInput;
    const selectFileBtn = document.getElementById('select-file-btn');

    // Drag & Drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // Click button to select file
    selectFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

async function handleFileUpload(file) {
    // Validate file size (2GB)
    const maxSize = 2 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('ファイルが大きすぎます。2GB以下のファイルを選択してください。');
        return;
    }

    // Show processing phase
    showPhase('processing');
    updateProgressSteps('upload');
    elements.statusText.textContent = 'ファイルをアップロード中...';

    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', state.sessionId);
    formData.append('business_title', elements.businessTitle.value || '');
    formData.append('author_name', elements.authorName.value || '');
    formData.append('additional_notes', elements.additionalNotes.value || '');

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'アップロードに失敗しました');
        }

        const data = await response.json();

        if (data.status === 'processing') {
            // Start SSE for status updates
            updateProgressSteps('process');
            elements.statusText.textContent = '動画を処理中...';
            startEventStream();
        } else {
            // Non-video file, go directly to complete
            showPhase('complete');
        }
    } catch (error) {
        alert(`エラー: ${error.message}`);
        showPhase('upload');
    }
}

// ==========================================================================
// Server-Sent Events
// ==========================================================================
function startEventStream() {
    if (state.eventSource) {
        state.eventSource.close();
    }

    state.eventSource = new EventSource(`/api/events/${state.sessionId}`);

    state.eventSource.addEventListener('phase', (e) => {
        const data = JSON.parse(e.data);
        handlePhaseChange(data.phase);
    });

    state.eventSource.addEventListener('scoping', (e) => {
        const data = JSON.parse(e.data);
        handleScopingResult(data.result);
    });

    state.eventSource.addEventListener('done', (e) => {
        state.eventSource.close();
        state.eventSource = null;
    });

    state.eventSource.addEventListener('error', (e) => {
        console.error('SSE Error:', e);
        // Try to reconnect after 5 seconds
        setTimeout(() => {
            if (state.currentPhase === 'processing') {
                startEventStream();
            }
        }, 5000);
    });
}

function handlePhaseChange(phase) {
    switch (phase) {
        case 'uploading':
            updateProgressSteps('upload');
            elements.statusText.textContent = 'ファイルをアップロード中...';
            break;
        case 'processing':
            updateProgressSteps('process');
            elements.statusText.textContent = '動画を処理中...';
            break;
        case 'questioning':
            updateProgressSteps('analyze');
            elements.statusText.textContent = 'AI分析中...';
            break;
        case 'analyzing':
            showPhase('analyzing');
            startEncouragingMessages();
            break;
        case 'complete':
            fetchAnalysisResult();
            break;
        case 'error':
            alert('処理中にエラーが発生しました。');
            showPhase('upload');
            break;
    }
}

function handleScopingResult(result) {
    // Move to policy phase
    showPhase('policy');
    elements.policyTextarea.value = result;
}

// ==========================================================================
// Policy Phase
// ==========================================================================
function setupPolicyPhase() {
    elements.startAnalysisBtn.addEventListener('click', async () => {
        const policy = elements.policyTextarea.value;

        // Update policy on server
        try {
            await fetch('/api/policy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    policy: policy,
                }),
            });

            // Start analysis
            showPhase('analyzing');
            startEncouragingMessages();

            const response = await fetch(`/api/analyze/${state.sessionId}`, {
                method: 'POST',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '解析に失敗しました');
            }

            const data = await response.json();
            showAnalysisResult(data.analysis);

        } catch (error) {
            alert(`エラー: ${error.message}`);
            showPhase('policy');
        }
    });
}

// ==========================================================================
// Analyzing Phase
// ==========================================================================
const encouragingMessages = [
    'もうすぐ完成です！',
    '動画を詳しく分析しています...',
    '重要なポイントを抽出中...',
    'チェックリストを確認しています...',
    'あと少しで完了します！',
];

let messageIndex = 0;
let messageInterval = null;

function startEncouragingMessages() {
    messageIndex = 0;
    updateEncouragingMessage();

    messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % encouragingMessages.length;
        updateEncouragingMessage();
    }, 5000);
}

function updateEncouragingMessage() {
    if (elements.encouragingMessage) {
        elements.encouragingMessage.textContent = encouragingMessages[messageIndex];
    }
}

function stopEncouragingMessages() {
    if (messageInterval) {
        clearInterval(messageInterval);
        messageInterval = null;
    }
}

// ==========================================================================
// Complete Phase
// ==========================================================================
async function fetchAnalysisResult() {
    try {
        const response = await fetch(`/api/analysis/${state.sessionId}`);
        if (!response.ok) {
            throw new Error('結果の取得に失敗しました');
        }
        const data = await response.json();
        showAnalysisResult(data.video_analysis);
    } catch (error) {
        console.error('Error fetching analysis:', error);
    }
}

function showAnalysisResult(analysis) {
    stopEncouragingMessages();
    showPhase('complete');

    // Show raw analysis in editor
    elements.analysisResult.textContent = analysis;
}

function setupCompletePhase() {
    // Generate document button
    elements.generateDocBtn.addEventListener('click', async () => {
        elements.generateDocBtn.disabled = true;
        elements.generateDocBtn.textContent = '生成中...';

        try {
            const response = await fetch('/api/generate-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'ドキュメント生成に失敗しました');
            }

            const data = await response.json();

            // Render markdown preview
            elements.documentPreview.innerHTML = marked.parse(data.document);

        } catch (error) {
            alert(`エラー: ${error.message}`);
        } finally {
            elements.generateDocBtn.disabled = false;
            elements.generateDocBtn.textContent = 'ドキュメント生成';
        }
    });

    // Copy button
    elements.copyBtn.addEventListener('click', async () => {
        const content = elements.documentPreview.innerText;
        try {
            await navigator.clipboard.writeText(content);
            elements.copyBtn.textContent = 'コピーしました！';
            setTimeout(() => {
                elements.copyBtn.textContent = 'コピー';
            }, 2000);
        } catch (error) {
            console.error('Copy failed:', error);
        }
    });
}

// ==========================================================================
// Initialization
// ==========================================================================
function init() {
    // Get session ID from hidden input
    state.sessionId = elements.sessionIdInput.value;

    // Setup event listeners
    setupDropZone();
    setupPolicyPhase();
    setupCompletePhase();

    // Show initial phase
    showPhase('upload');
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
