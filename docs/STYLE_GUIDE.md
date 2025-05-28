# Documentation Style Guide

## General Guidelines

### File Organization
- Use lowercase with hyphens for filenames (e.g., `setup-guide.md`)
- Place files in appropriate directories based on their purpose
- Keep related documentation together
- Use clear, descriptive filenames

### Document Structure
1. **Title** (H1)
2. **Introduction** - Brief overview of the document's purpose
3. **Table of Contents** (for longer documents)
4. **Main Content** - Organized with clear headings
5. **Examples** - Where applicable
6. **References** - Links to related documentation
7. **Version Information** - At the bottom of each document

### Markdown Formatting

#### Headers
```markdown
# Main Title (H1)
## Section (H2)
### Subsection (H3)
#### Minor Section (H4)
```

#### Code Blocks
- Use triple backticks with language specification
- Include comments for clarity
```python
# Example Python code
def example_function():
    """Documentation string."""
    return True
```

#### Lists
- Use ordered lists for sequential steps
- Use unordered lists for related items
- Indent nested lists with 2 spaces

#### Links
- Use relative paths for internal links
- Include descriptive text in link
```markdown
[Link Text](relative/path/to/file.md)
```

### Writing Style

#### Language
- Use clear, concise language
- Write in present tense
- Use active voice
- Avoid jargon unless necessary

#### Technical Content
- Include code examples where relevant
- Explain complex concepts
- Use diagrams for visual explanation
- Include error handling examples

#### Version Information
Add at the bottom of each document:
```markdown
---
Version: 1.0.0
Last Updated: YYYY-MM-DD
```

## Specific Guidelines

### Code Documentation
- Include purpose and usage examples
- Document parameters and return values
- Include error handling
- Add comments for complex logic

### API Documentation
- Document all endpoints
- Include request/response examples
- Document error codes
- Include authentication requirements

### Configuration Documentation
- Document all configuration options
- Include default values
- Explain impact of changes
- Provide examples

### Tutorial Documentation
- Start with prerequisites
- Break into clear steps
- Include verification steps
- Provide troubleshooting tips

### API Endpoint Naming Conventions
- Use plural forms for all endpoint names (e.g., `agents`, `users`, `devices`).
- Ensure all endpoint files and related documentation follow this convention.
- Avoid mixing singular and plural forms in endpoint definitions.
- Update any existing code to adhere to this standard to prevent confusion and maintain consistency.

## Best Practices

### Documentation Maintenance
- Keep documentation up to date
- Review regularly
- Update version numbers
- Remove outdated information

### Cross-Referencing
- Link to related documentation
- Avoid circular references
- Use relative paths
- Keep links current

### Examples
- Use realistic examples
- Include edge cases
- Show error handling
- Provide complete solutions

### Diagrams
- Use Mermaid for flowcharts
- Include alt text
- Keep diagrams simple
- Update with code changes

## Tools and Resources

### Recommended Tools
- Markdown editor with preview
- Diagram creation tools
- Code syntax highlighting
- Version control system

### Templates
- Use provided templates for consistency
- Customize as needed
- Maintain version information
- Include required sections

## Review Process

### Documentation Review
1. Technical accuracy
2. Completeness
3. Clarity
4. Formatting
5. Links
6. Examples
7. Version information

### Update Process
1. Create branch
2. Make changes
3. Update version
4. Review
5. Merge
6. Update changelog
