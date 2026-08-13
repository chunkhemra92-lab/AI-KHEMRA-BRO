# AI KHEMRA BRO v6.3 — Mobile Ready

This release improves the Streamlit interface for **Android phones, iPhones, small-screen devices, and landscape mobile use** while preserving the existing video-to-SRT, translation, SRT-to-speech, and text-to-speech workflow.

## Mobile improvements

| Area | Improvement |
|---|---|
| Small phones | The layout prevents horizontal page overflow and adapts down to 320 px-wide displays. |
| iPhone and Android browsers | Text inputs and text areas use a minimum 16 px font size to avoid focus zoom in mobile browsers. |
| Touch controls | Primary buttons have larger, comfortable tap targets and allow long text labels to wrap. |
| Workflow navigation | The four main tabs are arranged in a two-by-two grid on phone screens, so they remain visible without horizontal clipping. |
| Notched devices | Main content respects safe-area insets, preventing controls from being blocked by device cut-outs or home indicators. |
| Settings menu | The popover menu is constrained to the current screen width. |
| Media and uploads | Audio, video, upload areas, and long utility content remain within the visible screen width. |
| Landscape mode | Compact spacing and controls are applied when phones are held horizontally. |

## Deployment

Replace the deployed `app.py` with this release's `app.py`. Keep `requirements.txt` and `packages.txt` unchanged, then redeploy the Streamlit service.

For best results, test the deployed service in current versions of Chrome on Android and Safari on iPhone. Users should open the app directly in a browser; no app-store installation is required.

## Included files

| File | Purpose |
|---|---|
| `app.py` | Full application with responsive mobile interface improvements. |
| `requirements.txt` | Python dependencies. |
| `packages.txt` | System package requirement (`ffmpeg`). |

> This update is focused on responsive presentation and touch usability. It does not change the AI translation, speech-generation, account, or licensing workflows.
