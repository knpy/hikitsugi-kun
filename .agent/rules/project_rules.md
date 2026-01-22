---
trigger: always_on
---

# Project Rules

This document defines the "School Rules" for the **Podcast Generator** project. All agents and developers should adhere to these guidelines.

## 1. Technology Stack & Environment
- **Platform**: Google Apps Script (GAS)
- **Language**: JavaScript (ES6+ supported via V8 runtime)
- **Deployment**: `clasp` (CLI for Apps Script)
- **Package Manager**: npm (for local dev dev-dependencies if needed), but primarily GAS libraries.

## 2. Git & Version Control
### Branching Strategy
- **`main`**: Production-ready code.
- **Feature Branches**: `feat/description`, `fix/issue-id`, `refactor/scope`.

### Commit Convention
Follow **Conventional Commits**:
- `feat: ...` for new features
- `fix: ...` for bug fixes
- `docs: ...` for documentation
- `style: ...` for formatting (no logic change)
- `refactor: ...` for code restructuring
- `test: ...` for adding tests
- `chore: ...` for maintenance (build, config)

**Example**: `feat: add whisper transcription support`

## 3. Deployment Workflow
- **Do not edit directly in the GAS browser editor.** Always edit locally and push.
- Use the **`deploy_gas` skill** to push and deploy code.
- `clasp push`: Uploads local files to script.google.com.

## 4. Task Management
- **Active Task**: Track detailed progress in `.gemini/antigravity/brain/.../task.md`.
- **Experiments**: All prompt engineering and model capability tests must be conducted in `experiments/` directory with a dedicated report.

## 5. Agent Interaction
- **"School Rules" First**: Agents must check this file (`.agent/rules/project_rules.md`) to understand project constraints.
- **Artifacts**: Maintain `implementation_plan.md` and `task.md` for complex tasks.
