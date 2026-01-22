---
name: run_e2e_test
description: Execute an End-to-End test scenario in the browser to verify application functionality.
---

# Run E2E Test

Follow these steps to conduct an E2E test using the browser tool.

## 1. Prepare Environment
- **Check Server**: Ensure the application server is running (usually `uvicorn main:app` or similar).
  - Use `read_terminal` or `list_processes` (via shell) to verify.
  - If not running, ask the user or start it (if permitted).
- **Define URL**: Identify the target URL (e.g., `http://localhost:8000`).

## 2. Define Test Scenario
- Write down the specific steps the user would take.
- Example:
  1. Open Home Page.
  2. Click "Upload".
  3. Select file `test_video.mp4` (Use absolute path if uploading file).
  4. Verify "Processing" text appears.
  5. Verify "Complete" text appears.

## 3. Execute
- Call `browser_subagent`.
- **TaskName**: "E2E Test: [Scenario Name]"
- **Task**: Provide detailed instructions based on step 2. Be specific about selectors or text to look for.
- **RecordingName**: `e2e_test_[scenario_name]` (lowercase, underscores).

## 4. Analyze & Report
- Examine the tool output and artifacts (screenshots/recordings).
- Create a brief report (markdown) or update `walkthrough.md` with findings.
