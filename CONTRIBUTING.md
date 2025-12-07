# Contributing to UAE Legal Documents ETL Pipeline

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs
1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Error messages or logs

### Suggesting Features
1. Check if the feature has been suggested in Issues
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach

### Code Contributions

#### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git
cd uae-legal-etl-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py
```

#### Making Changes
1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests
5. Run tests: `python run_tests.py`
6. Commit with clear message: `git commit -m "Add: feature description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

#### Commit Message Guidelines
- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Prefix with type:
  - `Add:` new feature
  - `Fix:` bug fix
  - `Update:` update existing feature
  - `Refactor:` code refactoring
  - `Docs:` documentation changes
  - `Test:` adding or updating tests

#### Code Style
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

#### Testing
- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Test with different PDF formats

### Pull Request Process
1. Update README.md if needed
2. Update documentation
3. Add tests for new features
4. Ensure all tests pass
5. Update CHANGELOG.md (if exists)
6. Request review from maintainers

### Code Review
- Be respectful and constructive
- Explain your suggestions
- Be open to feedback
- Focus on code quality and maintainability

## Development Guidelines

### Project Structure
```
├── main.py                 # Entry point
├── etl_orchestrator.py     # Pipeline coordinator
├── deterministic_extractor.py  # Core extraction
├── result_merger.py        # Deduplication
├── output_schema_exporter.py   # JSON export
├── tests/                  # Unit tests
├── Data/                   # Input PDFs
└── reference/              # Reference documents
```

### Adding New Extractors
1. Create new file: `your_extractor.py`
2. Implement extraction logic
3. Add to `etl_orchestrator.py`
4. Write tests in `tests/test_your_extractor.py`
5. Update documentation

### Adding New Output Formats
1. Create new exporter in `output_schema_exporter.py`
2. Add configuration option in `config.json`
3. Update documentation
4. Add examples

## Questions?

- Open an issue for questions
- Check existing issues and documentation
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
