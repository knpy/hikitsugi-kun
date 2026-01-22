#!/bin/bash

# 引継ぎくん - GitHub Issues作成スクリプト
# 使用方法: ./create_issues.sh

set -e

# 色の定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}引継ぎくん - GitHub Issues作成${NC}"
echo ""

# リポジトリ情報を確認
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo -e "リポジトリ: ${GREEN}${REPO}${NC}"
echo ""

# ラベルを作成（存在しない場合）
echo -e "${YELLOW}ラベルを作成中...${NC}"
gh label create "priority:high" --color "d73a4a" --description "高優先度" --force || true
gh label create "priority:medium" --color "fbca04" --description "中優先度" --force || true
gh label create "priority:low" --color "0e8a16" --description "低優先度" --force || true
gh label create "type:feature" --color "a2eeef" --description "新機能" --force || true
gh label create "type:bug" --color "d73a4a" --description "バグ修正" --force || true
gh label create "type:refactor" --color "c5def5" --description "リファクタリング" --force || true
gh label create "phase:1" --color "bfdadc" --description "Phase 1" --force || true
gh label create "phase:2" --color "bfdadc" --description "Phase 2" --force || true
gh label create "phase:3" --color "bfdadc" --description "Phase 3" --force || true
gh label create "phase:4" --color "bfdadc" --description "Phase 4" --force || true
gh label create "phase:5" --color "bfdadc" --description "Phase 5" --force || true
gh label create "phase:6" --color "bfdadc" --description "Phase 6" --force || true
gh label create "phase:7" --color "bfdadc" --description "Phase 7" --force || true

echo ""
echo -e "${YELLOW}Issueを作成中...${NC}"
echo ""

# Phase 1
echo -e "${BLUE}Phase 1: SSEイベントストリームの接続${NC}"

ISSUE_1_1=$(gh issue create \
  --title "Phase 1.1: SSEイベントストリームの有効化" \
  --body "## 概要
動画アップロード後にSSE（Server-Sent Events）接続を開始し、バックエンドの処理進捗をリアルタイムで監視できるようにする。

## タスク
- [ ] \`init()\`関数でセッションIDを取得
- [ ] \`handleFileUpload()\`でアップロード成功後にSSE接続開始
- [ ] ブラウザ開発者ツールでSSE接続を確認

## 検証
- [ ] ネットワークタブに\`/api/events/{session_id}\`が表示される
- [ ] タイプが\`EventStream\`になっている
- [ ] コンソールに接続ログが表示される

## 関連ファイル
- \`static/js/app.js\`

## 実装プラン
Implementation Planを参照: \`phase1_implementation_plan.md\`

## 推定時間
1時間" \
  --label "priority:high,type:feature,phase:1" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_1_1}${NC}"

ISSUE_1_2=$(gh issue create \
  --title "Phase 1.2: フェーズ変更イベントのハンドリング" \
  --body "## 概要
SSEで受信したフェーズ変更イベントに応じて、適切な画面遷移を実装する。

## タスク
- [ ] \`handlePhaseChange()\`関数を拡張
- [ ] 各フェーズ（UPLOADING, PROCESSING, QUESTIONING, ANALYZING, COMPLETE）に対応
- [ ] タイマーベースの画面遷移を削除

## 検証
- [ ] 各フェーズに応じて正しい画面に遷移する
- [ ] コンソールに\`[Phase] Changed to: XXX\`のログが表示される

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_1_1#*/}

## 推定時間
1時間" \
  --label "priority:high,type:feature,phase:1" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_1_2}${NC}"

ISSUE_1_3=$(gh issue create \
  --title "Phase 1.3: SSE接続のエラーハンドリング" \
  --body "## 概要
SSE接続エラー時のリトライロジックとエラー表示UIを実装する。

## タスク
- [ ] エラーモーダルをHTMLに追加
- [ ] SSE接続エラー時のリトライロジック（最大3回、Exponential Backoff）
- [ ] エラー表示関数\`showError()\`を実装

## 検証
- [ ] サーバー停止時にエラーモーダルが表示される
- [ ] リトライロジックが動作する（コンソールで確認）
- [ ] 最大リトライ後にエラーメッセージが表示される

## 関連ファイル
- \`static/js/app.js\`
- \`templates/index.html\`

## 依存関係
- #${ISSUE_1_1#*/}

## 推定時間
1時間" \
  --label "priority:high,type:feature,phase:1" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_1_3}${NC}"
echo ""

# Phase 2
echo -e "${BLUE}Phase 2: Phase1（初期解析）の実装${NC}"

ISSUE_2_1=$(gh issue create \
  --title "Phase 2.1: Phase1画面のモックコード削除" \
  --body "## 概要
\`startPhase1()\`関数からタイマーベースの進捗アニメーションを削除する。

## タスク
- [ ] \`startPhase1()\`のタイマー処理を削除
- [ ] 固定のタイムスタンプ・認識テキスト配列を削除

## 関連ファイル
- \`static/js/app.js\` (L322-358)

## 依存関係
- #${ISSUE_1_2#*/}

## 推定時間
30分" \
  --label "priority:high,type:refactor,phase:2" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_2_1}${NC}"

ISSUE_2_2=$(gh issue create \
  --title "Phase 2.2: SSEイベントでのPhase1進捗表示" \
  --body "## 概要
SSEで\`scoping\`イベントを受信したら進捗バーを更新し、\`QUESTIONING\`フェーズで自動的にQuestions画面へ遷移する。

## タスク
- [ ] \`scoping\`イベント受信時に進捗バー更新
- [ ] スコーピング解析中は「解析中...」表示を維持
- [ ] フェーズが\`QUESTIONING\`になったら自動遷移

## 検証
- [ ] スコーピング解析中に進捗が表示される
- [ ] 解析完了後、自動的にQuestions画面に遷移する

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_2_1#*/}

## 推定時間
1時間" \
  --label "priority:high,type:feature,phase:2" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_2_2}${NC}"
echo ""

# Phase 3
echo -e "${BLUE}Phase 3: Questions画面の実装${NC}"

ISSUE_3_1=$(gh issue create \
  --title "Phase 3.1: スコーピング結果の表示" \
  --body "## 概要
SSEで受信した\`scoping_result\`を解析して「AI理解度」セクションに表示する。

## タスク
- [ ] \`state.aiUnderstanding\`の固定値を削除
- [ ] スコーピング結果から業務テーマ、推定ステップ、使用ツール、所要時間を抽出
- [ ] UI要素に動的に表示

## 検証
- [ ] Questions画面で実際のAI分析結果が表示される
- [ ] 固定値ではなく動的データが表示される

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_2_2#*/}

## 推定時間
1.5時間" \
  --label "priority:high,type:feature,phase:3" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_3_1}${NC}"

ISSUE_3_2=$(gh issue create \
  --title "Phase 3.2: ユーザー回答の送信と詳細解析開始" \
  --body "## 概要
すべての質問に回答後、\`POST /api/policy\`でユーザー方針を更新し、\`POST /api/analyze/{session_id}\`で詳細解析を開始する。

## タスク
- [ ] すべての質問回答後に\`POST /api/policy\`を呼び出し
- [ ] \`POST /api/analyze/{session_id}\`で詳細解析を開始
- [ ] Phase2画面への遷移はSSEイベントで自動的に行う

## 検証
- [ ] 質問回答後、バックエンドで詳細解析が開始される
- [ ] SSEで\`ANALYZING\`フェーズが通知される
- [ ] Phase2画面に自動遷移する

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_3_1#*/}

## 推定時間
1.5時間" \
  --label "priority:high,type:feature,phase:3" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_3_2}${NC}"
echo ""

# Phase 4
echo -e "${BLUE}Phase 4: Phase2（ドキュメント生成）の実装${NC}"

ISSUE_4_1=$(gh issue create \
  --title "Phase 4.1: Phase2画面のモックコード削除" \
  --body "## 概要
\`startPhase2()\`からタイマーベースの進捗アニメーションを削除する。

## タスク
- [ ] \`startPhase2()\`のタイマー処理を削除
- [ ] 固定タスク配列を削除

## 関連ファイル
- \`static/js/app.js\` (L510-584)

## 依存関係
- #${ISSUE_3_2#*/}

## 推定時間
30分" \
  --label "priority:high,type:refactor,phase:4" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_4_1}${NC}"

ISSUE_4_2=$(gh issue create \
  --title "Phase 4.2: 詳細解析結果の取得とドキュメント生成" \
  --body "## 概要
フェーズが\`COMPLETE\`になったら解析結果を取得し、ドキュメント生成APIを呼び出す。

## タスク
- [ ] \`COMPLETE\`フェーズで\`GET /api/analysis/{session_id}\`を呼び出し
- [ ] 解析結果（\`video_analysis\`）を保存
- [ ] \`POST /api/generate-document\`でドキュメント生成を開始
- [ ] Complete画面へ自動遷移

## 検証
- [ ] 詳細解析完了後、ドキュメントが生成される
- [ ] Complete画面に自動遷移する

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_4_1#*/}

## 推定時間
2時間" \
  --label "priority:high,type:feature,phase:4" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_4_2}${NC}"
echo ""

# Phase 5
echo -e "${BLUE}Phase 5: Complete画面の実装${NC}"

ISSUE_5_1=$(gh issue create \
  --title "Phase 5.1: 生成ドキュメントの表示" \
  --body "## 概要
\`POST /api/generate-document\`のレスポンスから生成ドキュメントを取得し、Markdownをパースして表示する。

## タスク
- [ ] 生成ドキュメントを取得
- [ ] \`marked.js\`でMarkdownをHTMLに変換
- [ ] \`#document-steps\`に表示
- [ ] タイトルと所要時間を動的に設定

## 検証
- [ ] 生成されたドキュメントが表示される
- [ ] Markdownが正しくレンダリングされる

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_4_2#*/}

## 推定時間
1.5時間" \
  --label "priority:medium,type:feature,phase:5" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_5_1}${NC}"

ISSUE_5_2=$(gh issue create \
  --title "Phase 5.2: ダウンロード機能の実装" \
  --body "## 概要
「ドキュメントをダウンロード」ボタンにMarkdownファイルのダウンロード機能を追加する。

## タスク
- [ ] ダウンロードボタンのクリックイベント実装
- [ ] Markdownファイルを生成してダウンロード
- [ ] ファイル名を動的に生成（例: \`引継ぎ資料_顧客管理システム_20260120.md\`）

## 検証
- [ ] ボタンクリックでファイルがダウンロードされる
- [ ] ファイル名が適切に生成される

## 関連ファイル
- \`static/js/app.js\`

## 依存関係
- #${ISSUE_5_1#*/}

## 推定時間
30分" \
  --label "priority:medium,type:feature,phase:5" \
  --assignee "@me")

echo -e "✅ Created: ${GREEN}${ISSUE_5_2}${NC}"
echo ""

# Phase 6 & 7 は省略（必要に応じて作成）

echo ""
echo -e "${GREEN}✅ すべてのIssueを作成しました！${NC}"
echo ""
echo -e "${YELLOW}作成されたIssue一覧:${NC}"
echo "Phase 1.1: $ISSUE_1_1"
echo "Phase 1.2: $ISSUE_1_2"
echo "Phase 1.3: $ISSUE_1_3"
echo "Phase 2.1: $ISSUE_2_1"
echo "Phase 2.2: $ISSUE_2_2"
echo "Phase 3.1: $ISSUE_3_1"
echo "Phase 3.2: $ISSUE_3_2"
echo "Phase 4.1: $ISSUE_4_1"
echo "Phase 4.2: $ISSUE_4_2"
echo "Phase 5.1: $ISSUE_5_1"
echo "Phase 5.2: $ISSUE_5_2"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "1. task.mdを更新してIssue番号を紐付ける"
echo "2. 各PhaseのImplementation Planを完成させる"
echo "3. Phase 1から実装を開始する"
