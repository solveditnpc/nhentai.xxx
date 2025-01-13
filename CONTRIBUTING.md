# Contributing to nhentai.xxx

Thank you for your interest in contributing to nhentai.xxx! We welcome contributions from the community and are pleased to have you join us.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How to Contribute

There are several ways you can contribute to this project:

1. **Reporting Bugs**
   - Use the GitHub Issues section to report bugs
   - Describe the bug in detail
   - Include steps to reproduce the issue
   - Add screenshots if applicable
   - Mention your operating system and Python version

2. **Suggesting Enhancements**
   - Use GitHub Issues to suggest new features
   - Explain your use case clearly
   - Provide examples if possible

3. **Code Contributions**
   - Fork the repository
   - Create a new branch for your feature/fix
   - Write clear, commented code
   - Follow the existing code style
   - Include tests for new features
   - Update documentation as needed

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure your code follows the project's coding standards
4. Update the documentation
5. Squash your commits into a single meaningful commit:
   ```bash
   git rebase -i HEAD~n  # where n is the number of commits to squash
   ```
   - Write a clear and descriptive commit message
   - The commit message should explain both what and why
6. Issue the pull request

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Coding Standards

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Comment complex logic
- Keep functions focused and concise

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Run tests using:
  ```bash
  python -m pytest
  ```

## Documentation

- Update README.md if you change functionality
- Document new features
- Keep documentation clear and concise

## Questions?

Feel free to open an issue if you have any questions about contributing.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---
Last updated: 2025-01-13
