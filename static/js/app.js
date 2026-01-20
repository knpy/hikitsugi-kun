/**
 * 引継ぎくん - フロントエンドアプリケーション
 * htmx + Vanilla JS (v0デザイン移植版)
 */

// ==========================================================================
// State Management
// ==========================================================================
const state = {
    sessionId: null,
    currentStep: 'welcome',
    eventSource: null,

    // ファイル情報
    fileName: '',
    fileSize: 0,

    // 質問関連
    questions: [
        {
            id: 'handoverTo',
            question: '誰に引き継ぎますか?',
            type: 'text'
        },
        {
            id: 'projectName',
            question: 'プロジェクト名・業務名を教えてください',
            type: 'text'
        },
        {
            id: 'skillLevel',
            question: '引き継ぐ相手のITスキルはどれくらいですか?',
            type: 'choice',
            options: [
                { value: 'beginner', label: '初心者' },
                { value: 'intermediate', label: '中級者' },
                { value: 'advanced', label: '上級者' }
            ]
        },
        {
            id: 'purpose',
            question: 'この作業の目的は何ですか?',
            type: 'choice',
            options: [
                { value: 'new_data', label: '新規データの登録' },
                { value: 'update_data', label: '既存データの更新' },
                { value: 'report', label: 'レポート作成' },
                { value: 'other', label: 'その他' }
            ]
        }
    ],
    currentQuestionIndex: 0,
    answers: [],

    // AI理解
    aiUnderstanding: {
        taskType: '顧客管理システムへのデータ入力',
        estimatedSteps: 7,
        tools: ['Chrome', 'Excel', '社内システム'],
        duration: '約15分'
    },

    // 生成されたステップ
    generatedSteps: [],

    // Phase2の状態
    phase2Stage: 'overview',
    phase2Progress: 0,
};

// ==========================================================================
// DOM Elements
// ==========================================================================
const getElements = () => ({
    // Steps
    stepWelcome: document.getElementById('step-welcome'),
    stepUpload: document.getElementById('step-upload'),
    stepUploading: document.getElementById('step-uploading'),
    stepPhase1: document.getElementById('step-phase1'),
    stepQuestions: document.getElementById('step-questions'),
    stepPhase2: document.getElementById('step-phase2'),
    stepComplete: document.getElementById('step-complete'),

    // Step indicator
    stepIndicator: document.getElementById('step-indicator'),

    // Welcome
    startUploadBtn: document.getElementById('start-upload-btn'),

    // Upload
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    uploadIcon: document.getElementById('upload-icon'),
    uploadText: document.getElementById('upload-text'),
    backToWelcome: document.getElementById('back-to-welcome'),

    // Uploading
    fileNameEl: document.getElementById('file-name'),
    fileSizeEl: document.getElementById('file-size'),
    uploadProgress: document.getElementById('upload-progress'),
    progressText: document.getElementById('progress-text'),

    // Phase1
    phase1Progress: document.getElementById('phase1-progress'),
    phase1ProgressBar: document.getElementById('phase1-progress-bar'),
    currentTimestamp: document.getElementById('current-timestamp'),
    currentRecognition: document.getElementById('current-recognition'),

    // Questions
    questionsHeader: document.getElementById('questions-header'),
    aiUnderstanding: document.getElementById('ai-understanding'),
    aiTaskType: document.getElementById('ai-task-type'),
    aiEstimatedSteps: document.getElementById('ai-estimated-steps'),
    aiTools: document.getElementById('ai-tools'),
    aiDuration: document.getElementById('ai-duration'),
    chatMessages: document.getElementById('chat-messages'),
    currentQuestion: document.getElementById('current-question'),
    questionText: document.getElementById('question-text'),
    textInputArea: document.getElementById('text-input-area'),
    questionInput: document.getElementById('question-input'),
    sendBtn: document.getElementById('send-btn'),
    choiceOptions: document.getElementById('choice-options'),
    questionProgress: document.getElementById('question-progress'),

    // Phase2
    stageOverview: document.getElementById('stage-overview'),
    stageConfirmation: document.getElementById('stage-confirmation'),
    stageGeneration: document.getElementById('stage-generation'),
    phase2ProgressBar: document.getElementById('phase2-progress-bar'),
    phase2Task: document.getElementById('phase2-task'),
    phase2ProgressText: document.getElementById('phase2-progress'),
    generatedSteps: document.getElementById('generated-steps'),
    stepsList: document.getElementById('steps-list'),

    // Complete
    documentTitle: document.getElementById('document-title'),
    documentDuration: document.getElementById('document-duration'),
    documentSteps: document.getElementById('document-steps'),
    downloadBtn: document.getElementById('download-btn'),
    restartBtn: document.getElementById('restart-btn'),

    // Hidden
    sessionIdInput: document.getElementById('session-id'),
});

let elements = {};

// ==========================================================================
// Step Management
// ==========================================================================
const STEPS = ['welcome', 'upload', 'uploading', 'phase1', 'questions', 'phase2', 'complete'];

function showStep(stepName) {
    // Hide all steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    const targetStep = document.getElementById(`step-${stepName}`);
    if (targetStep) {
        targetStep.classList.add('active');
        state.currentStep = stepName;
    }

    // Update step indicator
    updateStepIndicator(stepName);
}

function updateStepIndicator(currentStep) {
    const currentIndex = STEPS.indexOf(currentStep);

    document.querySelectorAll('.step-dot').forEach((dot, index) => {
        dot.classList.remove('active', 'past');

        if (index === currentIndex) {
            dot.classList.add('active');
        } else if (index < currentIndex) {
            dot.classList.add('past');
        }
    });
}

// ==========================================================================
// Welcome Step
// ==========================================================================
function setupWelcomeStep() {
    elements.startUploadBtn.addEventListener('click', () => {
        showStep('upload');
    });
}

// ==========================================================================
// Upload Step
// ==========================================================================
function setupUploadStep() {
    const dropZone = elements.dropZone;
    const fileInput = elements.fileInput;

    // Drag & Drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragging');
            elements.uploadText.textContent = 'ここにドロップ';
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragging');
            elements.uploadText.textContent = 'ファイルをドロップ、またはクリック';
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // Click to select file
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Back button
    elements.backToWelcome.addEventListener('click', () => {
        showStep('welcome');
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleFileSelect(file) {
    // Validate file size (500MB for v0 design)
    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('ファイルが大きすぎます。500MB以下のファイルを選択してください。');
        return;
    }

    state.fileName = file.name;
    state.fileSize = file.size;

    // Show uploading step
    showStep('uploading');

    // Update file info
    elements.fileNameEl.textContent = file.name;
    elements.fileSizeEl.textContent = (file.size / (1024 * 1024)).toFixed(1) + ' MB';

    // Start upload
    handleFileUpload(file);
}

// ==========================================================================
// File Upload
// ==========================================================================
async function handleFileUpload(file) {
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', state.sessionId);

    // Simulate upload progress (TODO: Replace with actual upload progress tracking)
    let currentProgress = 0;
    const uploadInterval = setInterval(() => {
        currentProgress += Math.random() * 12;
        if (currentProgress >= 100) {
            currentProgress = 100;
            clearInterval(uploadInterval);
        }
        updateUploadProgress(currentProgress);
    }, 200);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            clearInterval(uploadInterval);
            const error = await response.json();
            throw new Error(error.detail || 'アップロードに失敗しました');
        }

        const data = await response.json();
        console.log('Upload response:', data);

        // Clear the mock upload progress interval
        clearInterval(uploadInterval);

        // Ensure progress shows 100%
        updateUploadProgress(100);

        // Start SSE connection after successful upload
        setTimeout(() => {
            startEventStream();
        }, 500);

    } catch (error) {
        clearInterval(uploadInterval);
        alert(`エラー: ${error.message}`);
        showStep('upload');
    }
}

function updateUploadProgress(progress) {
    elements.uploadProgress.style.width = `${progress}%`;
    elements.progressText.textContent = `${Math.round(progress)}%`;
}

// ==========================================================================
// Phase 1: 軽量解析
// ==========================================================================
function startPhase1() {
    showStep('phase1');

    const recognitions = [
        { time: '00:12', text: 'ブラウザを起動' },
        { time: '00:32', text: 'ログイン画面を発見' },
        { time: '01:05', text: '認証情報を入力中' },
        { time: '01:45', text: 'メニュー画面を操作' },
        { time: '02:20', text: 'データ入力フォームにアクセス' },
        { time: '03:10', text: 'Excel ファイルを開く' },
        { time: '04:15', text: 'データをコピー&ペースト' },
        { time: '04:50', text: '保存ボタンをクリック' }
    ];

    let index = 0;
    const phase1Interval = setInterval(() => {
        if (index < recognitions.length) {
            elements.currentTimestamp.textContent = recognitions[index].time;
            elements.currentRecognition.textContent = recognitions[index].text;

            const progress = ((index + 1) / recognitions.length) * 100;
            elements.phase1Progress.textContent = `${Math.round(progress)}%`;
            elements.phase1ProgressBar.style.width = `${progress}%`;

            index++;
        } else {
            clearInterval(phase1Interval);
            setTimeout(() => {
                showStep('questions');
                setupQuestionsUI();
            }, 1000);
        }
    }, 600);
}

// ==========================================================================
// Questions Step
// ==========================================================================
function setupQuestionsUI() {
    // Reset question state
    state.currentQuestionIndex = 0;
    state.answers = [];

    // Update AI understanding display
    elements.aiTaskType.textContent = state.aiUnderstanding.taskType;
    elements.aiEstimatedSteps.textContent = `約${state.aiUnderstanding.estimatedSteps}個`;
    elements.aiTools.textContent = state.aiUnderstanding.tools.join('、');
    elements.aiDuration.textContent = state.aiUnderstanding.duration;

    // Clear chat messages
    elements.chatMessages.innerHTML = '';

    // Show header and AI understanding (first question only)
    elements.questionsHeader.style.display = 'block';
    elements.aiUnderstanding.style.display = 'block';

    // Setup question progress dots
    setupQuestionProgress();

    // Show first question
    showCurrentQuestion();
}

function setupQuestionProgress() {
    elements.questionProgress.innerHTML = '';
    state.questions.forEach((_, idx) => {
        const dot = document.createElement('div');
        dot.className = 'progress-dot';
        if (idx === 0) dot.classList.add('current');
        elements.questionProgress.appendChild(dot);
    });
}

function updateQuestionProgress() {
    const dots = elements.questionProgress.querySelectorAll('.progress-dot');
    dots.forEach((dot, idx) => {
        dot.classList.remove('current', 'completed');
        if (idx < state.currentQuestionIndex) {
            dot.classList.add('completed');
        } else if (idx === state.currentQuestionIndex) {
            dot.classList.add('current');
        }
    });
}

function showCurrentQuestion() {
    const question = state.questions[state.currentQuestionIndex];

    // Hide header and AI understanding after first question
    if (state.currentQuestionIndex > 0) {
        elements.questionsHeader.style.display = 'none';
        elements.aiUnderstanding.style.display = 'none';
    }

    // Update question text
    elements.questionText.textContent = question.question;

    // Show appropriate input type
    if (question.type === 'text') {
        elements.textInputArea.style.display = 'flex';
        elements.choiceOptions.style.display = 'none';
        elements.questionInput.value = '';
        elements.questionInput.focus();
    } else {
        elements.textInputArea.style.display = 'none';
        elements.choiceOptions.style.display = 'grid';
        renderChoiceOptions(question.options);
    }

    updateQuestionProgress();
}

function renderChoiceOptions(options) {
    elements.choiceOptions.innerHTML = '';
    options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'choice-button';
        btn.textContent = option.label;
        btn.addEventListener('click', () => handleAnswerSubmit(option.label));
        elements.choiceOptions.appendChild(btn);
    });
}

function setupQuestionsStep() {
    // Text input submit
    elements.sendBtn.addEventListener('click', () => {
        const value = elements.questionInput.value.trim();
        if (value) {
            handleAnswerSubmit(value);
        }
    });

    elements.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const value = elements.questionInput.value.trim();
            if (value) {
                handleAnswerSubmit(value);
            }
        }
    });
}

function handleAnswerSubmit(answer) {
    const currentQuestion = state.questions[state.currentQuestionIndex];

    // Add to answers
    state.answers.push({
        questionId: currentQuestion.id,
        answer: answer
    });

    // Add to chat history
    addToChatHistory(currentQuestion.question, answer);

    // Clear input
    elements.questionInput.value = '';

    // Next question or phase2
    if (state.currentQuestionIndex < state.questions.length - 1) {
        state.currentQuestionIndex++;
        setTimeout(() => showCurrentQuestion(), 300);
    } else {
        setTimeout(() => startPhase2(), 500);
    }
}

function addToChatHistory(question, answer) {
    const messageHtml = `
        <div class="chat-message">
            <div class="ai-message">
                <div class="ai-avatar">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 3l1.45 2.9L17 6.5l-2.18 2.18L15.36 13 12 11.18 8.64 13l.54-4.32L7 6.5l3.55-.6L12 3z"/>
                    </svg>
                </div>
                <p class="ai-question-text">${question}</p>
            </div>
            <div class="user-answer">
                <div class="answer-bubble">${answer}</div>
            </div>
        </div>
    `;
    elements.chatMessages.insertAdjacentHTML('beforeend', messageHtml);
}

// ==========================================================================
// Phase 2: 本格解析
// ==========================================================================
function startPhase2() {
    showStep('phase2');
    state.phase2Stage = 'overview';
    state.phase2Progress = 0;
    state.generatedSteps = [];

    const phase2Tasks = [
        { stage: 'overview', task: '動画全体を分析中...', duration: 2000 },
        { stage: 'confirmation', task: '内容を確認中...', duration: 2000 },
        { stage: 'generation', task: 'ステップ1の説明を生成中...', duration: 1800 },
        { stage: 'generation', task: 'スクリーンショットを抽出中...', duration: 1800 },
        { stage: 'generation', task: '注意点を洗い出し中...', duration: 1800 },
        { stage: 'generation', task: '用語集を作成中...', duration: 1800 },
        { stage: 'generation', task: '初心者向けの補足を追加中...', duration: 1800 }
    ];

    const steps = [
        'ブラウザを開き、社内システムにアクセスする',
        'ログイン画面でメールアドレスとパスワードを入力する',
        'メニューから「顧客管理」を選択する',
        'データ入力フォームを開く',
        'Excelファイルから必要なデータをコピーする',
        'フォームに貼り付けて内容を確認する',
        '保存ボタンをクリックして完了する'
    ];

    let taskIndex = 0;
    let stepIndex = 0;

    function executeNextTask() {
        if (taskIndex >= phase2Tasks.length) {
            setTimeout(() => showStep('complete'), 1500);
            setupCompleteUI();
            return;
        }

        const currentTask = phase2Tasks[taskIndex];
        state.phase2Stage = currentTask.stage;
        elements.phase2Task.textContent = currentTask.task;

        // Update stage indicators
        updatePhase2Stages(currentTask.stage);

        // Update progress
        if (currentTask.stage === 'overview') {
            state.phase2Progress = 15;
        } else if (currentTask.stage === 'confirmation') {
            state.phase2Progress = 35;
        } else if (currentTask.stage === 'generation') {
            // Add generated step
            if (stepIndex < steps.length) {
                state.generatedSteps.push(steps[stepIndex]);
                addGeneratedStep(steps[stepIndex], stepIndex);
                stepIndex++;
            }
            state.phase2Progress = 35 + (stepIndex / steps.length) * 65;

            // Show generated steps container
            if (state.generatedSteps.length > 0) {
                elements.generatedSteps.style.display = 'block';
            }
        }

        elements.phase2ProgressBar.style.width = `${state.phase2Progress}%`;
        elements.phase2ProgressText.textContent = `${Math.round(state.phase2Progress)}%`;

        taskIndex++;
        setTimeout(executeNextTask, currentTask.duration);
    }

    executeNextTask();
}

function updatePhase2Stages(currentStage) {
    const stages = ['overview', 'confirmation', 'generation'];
    const currentIndex = stages.indexOf(currentStage);

    stages.forEach((stage, idx) => {
        const el = document.getElementById(`stage-${stage}`);
        if (!el) return;

        el.classList.remove('active', 'completed');

        if (idx < currentIndex) {
            el.classList.add('completed');
        } else if (idx === currentIndex) {
            el.classList.add('active');
        }
    });
}

function addGeneratedStep(stepText, index) {
    const stepHtml = `
        <div class="step-item">
            <div class="step-number">${index + 1}</div>
            <p class="step-text">${stepText}</p>
        </div>
    `;
    elements.stepsList.insertAdjacentHTML('beforeend', stepHtml);
}

// ==========================================================================
// Complete Step
// ==========================================================================
function setupCompleteUI() {
    // Update document preview
    elements.documentTitle.textContent = state.aiUnderstanding.taskType;
    elements.documentDuration.textContent = `推定所要時間: ${state.aiUnderstanding.duration}`;

    // Clear and add steps
    elements.documentSteps.innerHTML = '';
    state.generatedSteps.forEach((step, idx) => {
        const stepHtml = `
            <div class="document-step">
                <div class="step-number">${idx + 1}</div>
                <p class="step-text">${step}</p>
            </div>
        `;
        elements.documentSteps.insertAdjacentHTML('beforeend', stepHtml);
    });
}

function setupCompleteStep() {
    elements.downloadBtn.addEventListener('click', async () => {
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
                throw new Error('ドキュメント生成に失敗しました');
            }

            const data = await response.json();

            // Download as markdown file
            const blob = new Blob([data.document], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `引継ぎドキュメント_${new Date().toISOString().slice(0, 10)}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            alert(`エラー: ${error.message}`);
        }
    });

    elements.restartBtn.addEventListener('click', () => {
        // Reset state
        state.currentQuestionIndex = 0;
        state.answers = [];
        state.generatedSteps = [];
        state.phase2Progress = 0;

        // Clear generated steps list
        elements.stepsList.innerHTML = '';
        elements.generatedSteps.style.display = 'none';

        // Go back to welcome
        showStep('welcome');
    });
}

// ==========================================================================
// Server-Sent Events (for real API integration)
// ==========================================================================

// SSE retry configuration
const SSE_CONFIG = {
    maxRetries: 5,
    initialRetryDelay: 1000, // 1 second
    maxRetryDelay: 30000, // 30 seconds
};

let sseRetryCount = 0;
let sseRetryTimeout = null;

function startEventStream(isRetry = false) {
    if (state.eventSource) {
        state.eventSource.close();
    }

    if (!isRetry) {
        sseRetryCount = 0;
    }

    console.log(`Starting SSE connection (attempt ${sseRetryCount + 1}/${SSE_CONFIG.maxRetries})...`);

    state.eventSource = new EventSource(`/api/events/${state.sessionId}`);

    state.eventSource.addEventListener('phase', (e) => {
        const data = JSON.parse(e.data);
        handlePhaseChange(data.phase);
        // Reset retry count on successful event
        sseRetryCount = 0;
    });

    state.eventSource.addEventListener('scoping', (e) => {
        const data = JSON.parse(e.data);
        // Update AI understanding from server
        if (data.result) {
            state.aiUnderstanding.taskType = data.result;
        }
        // Reset retry count on successful event
        sseRetryCount = 0;
    });

    state.eventSource.addEventListener('done', (e) => {
        console.log('SSE connection closed (done event)');
        state.eventSource.close();
        state.eventSource = null;
        sseRetryCount = 0;
    });

    state.eventSource.addEventListener('error', (e) => {
        console.error('SSE Error:', e);

        // Close the current connection
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }

        // Clear any existing retry timeout
        if (sseRetryTimeout) {
            clearTimeout(sseRetryTimeout);
            sseRetryTimeout = null;
        }

        // Check if we should retry
        if (sseRetryCount < SSE_CONFIG.maxRetries) {
            // Calculate exponential backoff delay
            const retryDelay = Math.min(
                SSE_CONFIG.initialRetryDelay * Math.pow(2, sseRetryCount),
                SSE_CONFIG.maxRetryDelay
            );

            console.log(`Retrying SSE connection in ${retryDelay}ms...`);

            sseRetryCount++;
            sseRetryTimeout = setTimeout(() => {
                startEventStream(true);
            }, retryDelay);
        } else {
            // Max retries reached
            console.error('Max SSE retries reached. Giving up.');
            showErrorMessage('サーバーとの接続に失敗しました。ページをリロードしてください。');
        }
    });

    state.eventSource.addEventListener('open', () => {
        console.log('SSE connection established');
    });
}

function showErrorMessage(message) {
    // Create error message UI if it doesn't exist
    let errorContainer = document.getElementById('error-message');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-message';
        errorContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            max-width: 400px;
            font-size: 14px;
            line-height: 1.5;
        `;
        document.body.appendChild(errorContainer);
    }
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
}

function handlePhaseChange(phase) {
    console.log('Phase changed to:', phase);

    switch (phase.toLowerCase()) {
        case 'uploading':
            // Show uploading screen with progress
            showStep('uploading');
            break;
        case 'processing':
            // Show Phase1 analysis screen
            showStep('phase1');
            // The actual progress will come from SSE 'scoping' events
            break;
        case 'questioning':
            showStep('questions');
            setupQuestionsUI();
            break;
        case 'analyzing':
            startPhase2();
            break;
        case 'complete':
            showStep('complete');
            setupCompleteUI();
            break;
        case 'error':
            alert('処理中にエラーが発生しました。');
            showStep('welcome');
            break;
        default:
            console.warn('Unknown phase:', phase);
    }
}

// ==========================================================================
// Initialization
// ==========================================================================
function init() {
    // Get DOM elements
    elements = getElements();

    // Get session ID from hidden input
    state.sessionId = elements.sessionIdInput.value;

    // Setup event listeners
    setupWelcomeStep();
    setupUploadStep();
    setupQuestionsStep();
    setupCompleteStep();

    // Show initial step
    showStep('welcome');
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
