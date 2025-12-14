# Contributing to Primary Assistant

Thank you for your interest in contributing to this project!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nbowman189/primary-assistant.git
   cd primary-assistant
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

## Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Production hotfixes

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation

3. **Test your changes**
   ```bash
   docker-compose exec web pytest
   docker-compose exec web pytest --cov
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add description of your feature"
   ```

5. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub targeting 'develop' branch
   ```

## Commit Message Convention

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: Add workout logging API endpoint
fix: Resolve authentication session timeout issue
docs: Update API documentation for health metrics
```

## Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ features
- **CSS**: Use CSS variables for theming
- **SQL**: Use descriptive table/column names

## Testing Requirements

All new features must include:
- Unit tests
- Integration tests (where applicable)
- Minimum 80% code coverage

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add description of changes
4. Link related issues
5. Request review from maintainers

## Questions?

Contact: nbowman189@gmail.com
