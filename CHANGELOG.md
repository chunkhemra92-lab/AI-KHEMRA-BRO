# Changelog

## v6.5 — Stability release

This release standardizes the application version at **6.5** and adds a reproducible development dependency set for release validation. Runtime dependency pins remain unchanged from the previously verified baseline; no unvalidated production behavior or deployment target is changed by this scoped release.

### Validation scope

- Source-level safeguards and application stability assertions.
- Audio, subtitle timing, language, voice, theme, and deployment package checks already present in the repository.
- Python compilation and version consistency checks.

### Deployment note

This GitHub release is a versioned source release, not an automatic production deployment. Before deploying, create a backup of the production license database, build from the tagged commit, verify the Streamlit health endpoint, and run one complete video-to-Khmer-SRT-to-MP3 workflow.
