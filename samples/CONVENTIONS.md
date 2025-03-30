# Conventions for Aider AI - Pure Python, Native Libraries & Whisper

This document outlines the conventions to follow when contributing to or working with the Aider AI project, specifically focusing on pure Python code, the use of native libraries (where necessary and justified), and integration with Whisper for audio processing. It also includes a section for tracking tasks related to the Whisper Transcription Tools refactor plan.

## 1. Pure Python Code

* **Emphasis on Readability:** Write code that is easy to understand. Use descriptive variable names, clear function and class names, and keep functions and methods concise.
    * **Example (Good):** `user_query = input("Enter your query: ")`
    * **Example (Bad):** `q = input("Enter query: ")`
* **PEP 8 Compliance:** Adhere to the PEP 8 style guide for Python code. This includes naming conventions, indentation (4 spaces), line length (generally 79 characters, 99 for comments/docstrings), and whitespace. Use a linter (like `flake8` or `pylint`) and a formatter (like `black`) to ensure consistency.
* **Explicit is Better than Implicit:** Be explicit in your code. Avoid relying on implicit behavior that might be unclear to others.
* **Keep it Simple:** Favor straightforward solutions over complex or overly clever ones, unless complexity is genuinely required for performance or functionality.
* **Docstrings:** Write comprehensive docstrings for all modules, classes, functions, and methods. Follow the NumPy/SciPy docstring convention for clarity and consistency.
    * Include a brief summary line.
    * Elaborate on parameters, their types, and what they represent.
    * Describe what the function/method returns, including the type.
    * Include examples where appropriate.
* **Type Hinting:** Use type hints (as defined in PEP 484) to improve code readability and help with static analysis.
    * **Example:** `def greet(name: str) -> str:`
* **Avoid Magic Numbers:** Use named constants for literal values that have a specific meaning.
    * **Example (Good):** `MAX_RETRIES = 3`
    * **Example (Bad):** `for i in range(3): ...`
* **String Formatting:** Use f-strings (formatted string literals) for cleaner and more readable string formatting.
    * **Example:** `print(f"The user's name is {name}.")`

## 2. Native Libraries

* **Justification:** Native (C/C++) libraries should only be used when there is a clear and significant performance bottleneck that cannot be adequately addressed with pure Python, or when access to specific system-level functionalities is required.
* **Minimal Usage:** Keep the usage of native libraries to a minimum. The core logic of Aider AI should ideally remain in pure Python for portability and maintainability.
* **Clear Interfaces:** When using native libraries, ensure that the Python interface is well-defined, easy to use, and thoroughly documented. Consider using tools like `ctypes`, `Cython`, or `PyBind11` to create these interfaces.
* **Build Instructions:** Provide clear and concise instructions on how to build and install any required native library dependencies. This should include platform-specific considerations.
* **Testing:** Thoroughly test the Python wrappers around native libraries to ensure they function correctly and handle potential errors gracefully.

## 3. Whisper Integration

* **Clear Separation:** Maintain a clear separation between the core Aider AI logic and the Whisper-specific code. Create dedicated modules or classes for handling audio transcription using Whisper.
* **Abstraction:** Abstract the Whisper API calls behind well-defined functions or methods. This will make it easier to switch to a different speech-to-text engine in the future if needed.
* **Configuration:** Allow for configuration of Whisper parameters (e.g., model size, language) through Aider AI's settings or command-line arguments.
* **Input Handling:** Implement robust handling of various audio input formats and sources. Clearly document the supported formats.
* **Error Handling:** Implement proper error handling for Whisper API calls and potential issues with audio processing. Provide informative error messages to the user.
* **Performance Considerations:** Be mindful of the computational resources required by Whisper, especially larger models. Provide guidance to users on choosing appropriate model sizes based on their hardware.
* **Optional Dependency:** Consider making Whisper an optional dependency. If Aider AI can function without audio transcription capabilities, clearly document how to install the necessary Whisper components.

## 4. General Conventions

* **Version Control (Git):** Follow standard Git practices for committing code, writing commit messages, and creating pull requests.
* **Testing:** Write comprehensive unit tests and integration tests for all new features and bug fixes. Aim for high test coverage. Use a testing framework like `pytest`.
* **Logging:** Use a consistent logging mechanism to track the execution of Aider AI and aid in debugging.
* **Configuration:** Externalize configuration parameters (e.g., API keys, file paths) into configuration files or environment variables.
* **Error Handling:** Implement robust error handling throughout the codebase. Catch exceptions appropriately and provide informative error messages to the user.
* **Code Reviews:** All code contributions should undergo thorough code reviews by other contributors.
* **Documentation:** Keep the project documentation up-to-date with any changes to the codebase, features, or dependencies.

## 5. Whisper Transcription Tools Refactor Tasks

This section tracks the tasks outlined in the "Refactor Plan for Whisper Transcription Tools".

### Phase 1: Extract Shared Logic (High Priority)

* **[ ] 1. Create `whisper_utils.py` file:**
    * **[ ]** Move `load_whisper_model` to `whisper_utils.py`.
    * **[ ]** Move `transcribe_audio` to `whisper_utils.py`.
    * **[ ]** Move `format_transcription_output_combined` to `whisper_utils.py`.
    * **[ ]** Move `save_transcription_to_file` to `whisper_utils.py`.
    * **[ ]** Add type hints to all function signatures and return values in `whisper_utils.py` as per the plan.
* **[ ] 2. Update `app.py`:**
    * **[ ]** Import functions from `whisper_utils.py`.
    * **[ ]** Remove the duplicated Whisper-related functions.
    * **[ ]** Update calls to use the imported functions.
* **[ ] 3. Update `main.py`:**
    * **[ ]** Import functions from `whisper_utils.py`.
    * **[ ]** Remove the duplicated Whisper-related functions.
    * **[ ]** Update calls to use the imported functions.

### Phase 2: Configuration and Error Handling (Medium Priority)

* **[ ] 1. Create `config.py` file:**
    * **[ ]** Define `PAUSE_THRESHOLD` constant.
    * **[ ]** Define `SPEAKER_KEYWORDS` constant.
    * **[ ]** Define `VALID_MODELS` constant.
    * **[ ]** Define `DEFAULT_MODEL` constant.
* **[ ] 2. Update `app.py`:**
    * **[ ]** Import configuration values from `config.py`.
    * **[ ]** Replace hardcoded configuration values with imports from `config.py`.
* **[ ] 3. Update `main.py`:**
    * **[ ]** Import configuration values from `config.py`.
    * **[ ]** Replace hardcoded configuration values with imports from `config.py`.
* **[ ] 4. Improve Error Handling:**
    * **[ ]** Review `app.py` and implement more consistent `try...except` blocks.
    * **[ ]** Provide more informative error messages in `app.py`.
    * **[ ]** Consider logging errors to a file from `app.py`.
    * **[ ]** Review `main.py` and implement more consistent `try...except` blocks.
    * **[ ]** Provide more informative error messages in `main.py`.
    * **[ ]** Consider logging errors to a file from `main.py`.

### Phase 3: GUI Improvements (`app.py` - Medium Priority)

* **[ ] 1. Separate GUI Logic:**
    * **[ ]** Create a class to encapsulate the main GUI logic in `app.py`.
    * **[ ]** Move GUI-related methods and attributes into this class.
* **[ ] 2. Progress Indication:**
    * **[ ]** Implement a progress bar or other visual indicator during transcription in `app.py`.
* **[ ] 3. Model Loading Indication:**
    * **[ ]** Display a loading indicator while the Whisper model is being loaded in `app.py`.
* **[ ] 4. Clearer Layout:**
    * **[ ]** Review and improve the layout of the Tkinter GUI in `app.py` for better usability.

### Phase 4: Command-Line Argument Parsing (`main.py` - Low Priority)

* **[ ] 1. Use `argparse`:**
    * **[ ]** Replace manual input prompts in `main.py` with the `argparse` module.
    * **[ ]** Implement arguments for the audio file path.
    * **[ ]** Implement arguments for the Whisper model name.
    * **[ ]** Consider adding arguments for other relevant options.

By adhering to these conventions and systematically addressing the refactor tasks, we can build a more robust, maintainable, and user-friendly Aider AI project.