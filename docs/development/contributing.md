# Contributing Guide

## Getting Started

### Prerequisites
- Follow the [Setup Guide](setup.md) to set up your development environment
- Read the [Development Workflow](workflow.md) to understand our processes
- Review the [Troubleshooting Guide](troubleshooting.md) for common issues

### Code of Conduct
- Be respectful and professional
- Help others learn and grow
- Focus on the best solution, not just your solution
- Give and receive constructive feedback

## Development Process

### 1. Branch Management
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/your-bug-fix

# Create hotfix branch
git checkout -b hotfix/your-hotfix
```

### 2. Commit Guidelines
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests liberally
- Consider starting commit message with applicable emoji:
  - 🎨 `:art:` when improving the format/structure of the code
  - 🐎 `:racehorse:` when improving performance
  - 🚱 `:non-potable_water:` when plugging memory leaks
  - 📝 `:memo:` when writing docs
  - 🐛 `:bug:` when fixing a bug
  - 🔥 `:fire:` when removing code or files
  - 💚 `:green_heart:` when fixing the CI build
  - ✅ `:white_check_mark:` when adding tests
  - 🔒 `:lock:` when dealing with security
  - ⬆️ `:arrow_up:` when upgrading dependencies
  - ⬇️ `:arrow_down:` when downgrading dependencies

### 3. Pull Request Process
1. Update documentation
2. Add tests for new functionality
3. Ensure all tests pass
4. Update the changelog
5. Request review from at least one maintainer

## Code Standards

### Python
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
from typing import List, Optional

def process_items(items: List[str], limit: Optional[int] = None) -> List[str]:
    """
    Process a list of items with an optional limit.

    Args:
        items: List of items to process
        limit: Optional maximum number of items to process

    Returns:
        List of processed items
    """
    if limit is not None:
        items = items[:limit]
    return [item.strip() for item in items]
```

### TypeScript/JavaScript
- Follow ESLint configuration
- Use TypeScript for type safety
- Write JSDoc comments
- Use meaningful variable names
- Keep components focused

Example:
```typescript
interface User {
  id: string;
  name: string;
  email: string;
}

/**
 * Fetches user data from the API
 * @param userId - The ID of the user to fetch
 * @returns Promise resolving to user data
 */
async function fetchUser(userId: string): Promise<User> {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  return response.json();
}
```

### SQL
- Use meaningful table and column names
- Include comments for complex queries
- Use consistent formatting
- Follow naming conventions

Example:
```sql
-- Get active users with their latest login
SELECT
    u.id,
    u.username,
    u.email,
    MAX(l.login_time) as last_login
FROM users u
LEFT JOIN login_history l ON u.id = l.user_id
WHERE u.is_active = true
GROUP BY u.id, u.username, u.email
ORDER BY last_login DESC;
```

## Testing

### Backend Tests
```python
# Test structure
def test_function_name():
    # Arrange
    input_data = {...}

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_output
```

### Frontend Tests
```typescript
// Component test
describe('ComponentName', () => {
  it('should render correctly', () => {
    // Arrange
    const props = {...};

    // Act
    render(<Component {...props} />);

    // Assert
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

## Documentation

### Code Documentation
- Write clear docstrings/comments
- Document complex algorithms
- Explain non-obvious code
- Keep documentation up to date

### API Documentation
- Document all endpoints
- Include request/response examples
- Document error cases
- Keep OpenAPI spec updated

## Review Process

### Code Review Checklist
- [ ] Code follows style guide
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No security issues
- [ ] Performance considered
- [ ] Error handling included
- [ ] Logging appropriate
- [ ] No unnecessary dependencies

### Review Guidelines
- Be constructive and specific
- Focus on the code, not the person
- Explain the "why" of suggestions
- Be timely with reviews
- Consider the bigger picture

## Deployment

### Staging
1. Create release branch
2. Run all tests
3. Update version numbers
4. Create pull request
5. Get approval
6. Merge to staging

### Production
1. Create release candidate
2. Run integration tests
3. Perform security scan
4. Get final approval
5. Deploy to production
6. Monitor for issues

## Support

### Getting Help
- Check documentation first
- Search existing issues
- Ask in team chat
- Create new issue if needed

### Providing Help
- Be patient and clear
- Provide examples
- Link to documentation
- Follow up if needed

## License
- All contributions are subject to the project's license
- Ensure you have the right to contribute
- Include license headers in new files
