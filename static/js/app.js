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

    // AI理解（スコーピング結果から動的に更新）
    aiUnderstanding: {
        taskType: '',
        estimatedSteps: 0,
        tools: [],
        duration: ''
    },

    // 生成されたステップ
    generatedSteps: [],

    // Phase2の状態
    phase2Stage: 'overview',
    phase2Progress: 0,

    // Phase 5: 詳細解析結果とドキュメント
    videoAnalysis: '',        // 詳細動画分析結果（Markdown）
    generatedDocument: ''     // 生成済みドキュメント（Markdown）
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
// Phase 1: 軽量解析（SSEベース - 実際の進捗）
// ==========================================================================
function initPhase1Display() {
    // Phase1画面の初期表示
    elements.phase1Progress.textContent = '0%';
    elements.phase1ProgressBar.style.width = '0%';
    elements.currentTimestamp.textContent = '00:00';
    elements.currentRecognition.textContent = '準備中...';
}

function updatePhase1Progress(step, progress) {
    // SSEから受信した進捗で更新
    elements.phase1Progress.textContent = `${progress}%`;
    elements.phase1ProgressBar.style.width = `${progress}%`;

    // 50-70%の区間で追加メッセージ表示
    if (progress >= 50 && progress < 70) {
        elements.currentRecognition.innerHTML = `
            ${step}
            <span class="text-muted" style="font-size: 0.9em;">（しばらくお待ちください...）</span>
        `;
    } else {
        elements.currentRecognition.textContent = step;
    }
}

// ==========================================================================
// Questions Step
// ==========================================================================
function parseScopingResult(scopingText) {
    // スコーピング結果のテキストを解析してAI理解度を更新
    console.log('Parsing scoping result:', scopingText);

    // 【業務テーマ】セクションから抽出
    const taskTypeMatch = scopingText.match(/【業務テーマ】\s*\n([^\n【]+)/);
    if (taskTypeMatch) {
        state.aiUnderstanding.taskType = taskTypeMatch[1].trim();
    }

    // 【解析方針案】セクションから項目を抽出（箇条書き）
    const policyMatch = scopingText.match(/【解析方針案】\s*\n((?:[-•]\s*[^\n]+\n?)+)/);
    if (policyMatch) {
        const policyItems = policyMatch[1]
            .split('\n')
            .filter(line => line.trim().match(/^[-•]\s*/))
            .map(line => line.replace(/^[-•]\s*/, '').trim())
            .filter(item => item.length > 0);

        // 推定ステップ数: 方針案の項目数を基準にする
        if (policyItems.length > 0) {
            state.aiUnderstanding.estimatedSteps = Math.max(3, policyItems.length * 2);
        }
    }

    // ツール情報を抽出（キーワード検索）
    const toolKeywords = ['Chrome', 'Excel', 'システム', 'ブラウザ', 'アプリ', 'ソフト'];
    const foundTools = toolKeywords.filter(tool => scopingText.includes(tool));
    if (foundTools.length > 0) {
        state.aiUnderstanding.tools = foundTools.slice(0, 3); // 最大3つ
    }

    // 所要時間の推定（仮: 固定値）
    state.aiUnderstanding.duration = '約15分';

    console.log('Updated AI understanding:', state.aiUnderstanding);
}

function setupQuestionsUI() {
    // Reset question state
    state.currentQuestionIndex = 0;
    state.answers = [];

    // Update AI understanding display（空の場合はフォールバック）
    elements.aiTaskType.textContent = state.aiUnderstanding.taskType || '解析中...';
    elements.aiEstimatedSteps.textContent = state.aiUnderstanding.estimatedSteps > 0
        ? `約${state.aiUnderstanding.estimatedSteps}個`
        : '解析中...';
    elements.aiTools.textContent = state.aiUnderstanding.tools.length > 0
        ? state.aiUnderstanding.tools.join('、')
        : '解析中...';
    elements.aiDuration.textContent = state.aiUnderstanding.duration || '解析中...';

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

    // Next question or detailed analysis
    if (state.currentQuestionIndex < state.questions.length - 1) {
        state.currentQuestionIndex++;
        setTimeout(() => showCurrentQuestion(), 300);
    } else {
        setTimeout(() => startDetailedAnalysis(), 500);
    }
}

function formatAnswersAsPolicy(answers) {
    // 回答配列をMarkdown形式のテキストに変換
    const labels = {
        'handoverTo': '【引き継ぎ先】',
        'projectName': '【プロジェクト名】',
        'skillLevel': '【ITスキル】',
        'purpose': '【目的】'
    };

    let policy = '';
    answers.forEach(answer => {
        const label = labels[answer.questionId] || `【${answer.questionId}】`;
        policy += `${label}\n${answer.answer}\n\n`;
    });

    return policy.trim();
}

async function startDetailedAnalysis() {
    console.log('Starting detailed analysis...');

    try {
        // 回答をuser_policyフォーマットに変換
        const policy = formatAnswersAsPolicy(state.answers);
        console.log('Formatted policy:', policy);

        // POST /api/policy でuser_policyを更新
        const policyResponse = await fetch('/api/policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                policy: policy
            })
        });

        if (!policyResponse.ok) {
            throw new Error(`Policy update failed: ${policyResponse.status}`);
        }

        console.log('User policy updated successfully');

        // POST /api/analyze/{session_id} で詳細解析開始
        const analyzeResponse = await fetch(`/api/analyze/${state.sessionId}`, {
            method: 'POST'
        });

        if (!analyzeResponse.ok) {
            throw new Error(`Detailed analysis start failed: ${analyzeResponse.status}`);
        }

        console.log('Detailed analysis started successfully');

        // Phase2画面への遷移はSSEのphaseイベントで自動的に行われる

    } catch (error) {
        console.error('Failed to start detailed analysis:', error);
        showErrorMessage('解析の開始に失敗しました。もう一度お試しください。');
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

    // 解析中UIを表示
    updatePhase2AnalyzingUI();

    // SSEのphaseイベントでANALYZINGフェーズを監視
    // フェーズがCOMPLETEになったら解析完了処理を呼び出す
}

function updatePhase2AnalyzingUI() {
    elements.phase2Task.textContent = '動画の内容を解析しています...';
    updatePhase2Stages('overview');
    // 進捗バーは表示するが、パーセンテージは更新しない（待機状態）
}

async function handleAnalysisComplete() {
    console.log('Analysis complete, fetching results...');

    try {
        // 1. GET /api/analysis/{session_id} で解析結果を取得
        const analysisResponse = await fetch(`/api/analysis/${state.sessionId}`);
        if (!analysisResponse.ok) {
            throw new Error(`Failed to fetch analysis: ${analysisResponse.status}`);
        }

        const analysisData = await analysisResponse.json();

        // 2. video_analysisをstateに保存
        state.videoAnalysis = analysisData.video_analysis;
        console.log('Video analysis saved:', state.videoAnalysis);

        // 3. UI更新（解析完了 → ドキュメント生成開始）
        elements.phase2Task.textContent = 'ドキュメントを生成中...';
        updatePhase2Stages('generation');
        // 進捗バーは引き続き待機状態（一括処理のため）

        // 4. POST /api/generate-document でドキュメント生成開始
        await generateDocument();

    } catch (error) {
        console.error('Failed to complete analysis:', error);
        showErrorMessage('解析結果の取得に失敗しました');
    }
}

async function generateDocument() {
    console.log('Generating document...');

    try {
        // POST /api/generate-document でドキュメント生成
        const response = await fetch('/api/generate-document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`Document generation failed: ${response.status}`);
        }

        const data = await response.json();

        // 生成されたドキュメントをstateに保存
        state.generatedDocument = data.document;
        console.log('Document generated successfully');

        // UI更新（完了）
        state.phase2Progress = 100;
        elements.phase2ProgressBar.style.width = '100%';
        elements.phase2ProgressText.textContent = '100%';
        updatePhase2Stages('generation');
        elements.phase2Task.textContent = 'ドキュメント生成完了';

        // Complete画面へ自動遷移（1秒後）
        setTimeout(() => {
            showStep('complete');
            setupCompleteUI();
        }, 1000);

    } catch (error) {
        console.error('Failed to generate document:', error);
        showErrorMessage('ドキュメント生成に失敗しました');
    }
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

    state.eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log('Progress event received:', data);

        // Phase1画面の進捗を更新
        if (state.currentStep === 'phase1') {
            updatePhase1Progress(data.step, data.progress);
        }

        // Reset retry count on successful event
        sseRetryCount = 0;
    });

    state.eventSource.addEventListener('scoping', (e) => {
        const data = JSON.parse(e.data);
        // Update AI understanding from server
        if (data.result) {
            parseScopingResult(data.result);
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
            // Initialize Phase1 display
            initPhase1Display();
            break;
        case 'questioning':
            showStep('questions');
            setupQuestionsUI();
            break;
        case 'analyzing':
            startPhase2();
            break;
        case 'complete':
            // Phase2画面にいる場合は解析完了処理を実行
            if (state.currentStep === 'phase2') {
                handleAnalysisComplete();
            } else {
                // それ以外の場合は既存の動作（Complete画面へ直接遷移）
                showStep('complete');
                setupCompleteUI();
            }
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
