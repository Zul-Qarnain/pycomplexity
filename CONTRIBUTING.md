# Contributing to bigopy

Thank you for your interest in contributing!

## How to contribute

1. Fork the repository on GitHub
2. Clone your fork locally:
   git clone https://github.com/Zul-Qarnain/pycomplexity.git
   cd pycomplexity
   git clone https://github.com/Zul-Qarnain/bigopy.git
   cd bigopy

3. Create a feature branch:
   git checkout -b feature/your-feature-name

4. Make your changes

5. Test your changes:
   python3 -m pytest tests/ -v
   OR
   python3 tests/unit/test_estimator.py

6. Commit and push:
   git add .
   git commit -m "feat: describe your change"
   git push origin feature/your-feature-name

7. Open a Pull Request on GitHub

## Adding a new algorithm test

1. Add the function to tests/fixtures/algorithms.py
2. Add a test case to tests/unit/test_estimator.py
3. Run tests to confirm it passes

## Code style

- Follow PEP 8
- Add docstrings to all public functions
- Keep functions small and focused

## Reporting bugs

Open an issue on GitHub with:
- Your Python version (python3 --version)
- The code that gave wrong results
- What you expected vs what you got
