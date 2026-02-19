# Contributing to Chicago Data Analysis

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check the [Issues](../../issues) page to see if it's already been reported
2. If not, [create a new issue](../../issues/new) with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (Python version, OS, etc.)

### Making Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/chicago-data-analysis.git
   cd chicago-data-analysis
   ```

2. **Set up development environment**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   source venv/bin/activate
   ```

3. **Make your changes**
   - Keep code clean and well-documented
   - Follow PEP 8 style guidelines
   - Add comments for complex logic
   - Test thoroughly before submitting

4. **Test your changes**
   ```bash
   python chicago_data_analysis.py
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   git push origin feature-branch
   ```

6. **Submit a Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Ensure all tests pass

## Code Standards

- **Python Version**: 3.7+
- **Style Guide**: PEP 8
- **Documentation**: Clear docstrings for all functions and classes
- **Comments**: Explain the "why" not the "what"

## Project Areas for Contribution

- **Performance**: Optimize queries or data loading
- **Features**: Add new analysis queries or visualizations
- **Documentation**: Improve README, docstrings, or examples
- **Bug Fixes**: Address reported issues
- **Testing**: Add or improve test coverage
- **Visualization**: Create charts/graphs from results

## Questions?

Feel free to open an issue with the `question` label or contact the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Happy Contributing! 🚀
