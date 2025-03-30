# Tasks for Whisper Transcription Tool Refactor

This document outlines the tasks required to implement the refactor plan for the Whisper Transcription Tool, as detailed in `PLAN.md` and guided by the conventions in `CONVENTIONS.md`.

## Phase 1: Extract Shared Logic (High Priority)

*   **[ ] 1.1 Update `transcription_utils.py`:**
    *   **[ ]** Ensure all functions have complete type hints and docstrings, adhering to `CONVENTIONS.md`.
*   **[ ] 1.2 Modify `app.py`:**
    *   **[ ]** Import `load_whisper_model`, `transcribe_audio`, `format_transcription_output_combined`, and `save_transcription_to_file` from `transcription_utils.py`.
    *   **[ ]** Remove the duplicated implementations of these functions.
    *   **[ ]** Update calls to use the imported functions.
*   **[ ] 1.3 Modify `main.py`:**
    *   **[ ]** Import `load_whisper_model`, `transcribe_audio`, `format_transcription_output_combined`, and `save_transcription_to_file` from `transcription_utils.py`.
    *   **[ ]** Remove the duplicated implementations of these functions.
    *   **[ ]** Update calls to use the imported functions.

## Phase 2: Configuration and Error Handling (Medium Priority)

*   **[ ] 2.1 Verify `config.py`:**
    *   **[ ]** Ensure all constants are defined and documented.
*   **[ ] 2.2 Modify `app.py`:**
    *   **[ ]** Import configuration values from `config.py`.
    *   **[ ]** Replace hardcoded configuration values with imports from `config.py`.
    *   **[ ]** Implement `try...except` blocks for error handling.
    *   **[ ]** Provide informative error messages to the user.
    *   **[ ]** Consider logging errors to a file.
*   **[ ] 2.3 Modify `main.py`:**
    *   **[ ]** Import configuration values from `config.py`.
    *   **[ ]** Replace hardcoded configuration values with imports from `config.py`.
    *   **[ ]** Implement `try...except` blocks for error handling.
    *   **[ ]** Provide informative error messages to the user.
    *   **[ ]** Consider logging errors to a file.

## Phase 3: GUI Improvements (`app.py` - Medium Priority)

*   **[ ] 3.1 Refactor GUI Logic in `app.py`:**
    *   **[ ]** Create a class to encapsulate the GUI logic.
    *   **[ ]** Move GUI-related methods and attributes into this class.
*   **[ ] 3.2 Implement Progress Indication in `app.py`:**
    *   **[ ]** Add a progress bar or other visual indication to show the user that the transcription is in progress.
*   **[ ] 3.3 Implement Model Loading Indication in `app.py`:**
    *   **[ ]** Show a loading indicator while the Whisper model is being loaded.
*   **[ ] 3.4 Improve GUI Layout in `app.py`:**
    *   **[ ]** Review and improve the layout of the GUI for better usability.

## Phase 4: Command-Line Argument Parsing (`main.py` - Low Priority)

*   **[ ] 4.1 Implement `argparse` in `main.py`:**
    *   **[ ]** Replace manual input prompts with the `argparse` module.
    *   **[ ]** Implement arguments for the audio file path.
    *   **[ ]** Implement arguments for the Whisper model name.
    *   **[ ]** Consider adding arguments for other relevant options.
