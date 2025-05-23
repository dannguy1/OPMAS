# OPMAS UI

The UI component provides a modern, responsive web interface for the OPMAS system, enabling efficient system monitoring, configuration management, and analysis result visualization.

## Documentation

### Design and Implementation
- [Design Specification](../docs/specifications/OPMAS-Frontend-DS.md) - Detailed design of the UI component
- [Implementation Plan](../docs/implementation_plans/frontend_ui.md) - Step-by-step implementation guide
- [UI Implementation Guidelines](../docs/guides/UI-Implementation-Guidelines.md) - UI/UX patterns and Tailwind CSS conventions

## Quick Start

### Prerequisites
- Node.js 16+
- npm 8+
- PostgreSQL 14+ (for development)
- Management API running locally

### Development Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

### Docker Setup
1. Build the image:
   ```bash
   docker build -t opmas-ui .
   ```

2. Run the container:
   ```bash
   docker run -p 3000:3000 --env-file .env opmas-ui
   ```

## Project Structure
```
ui/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── common/       # Shared components
│   │   ├── forms/        # Form components
│   │   ├── tables/       # Table components
│   │   └── modals/       # Modal components
│   ├── pages/            # Page components
│   │   ├── Dashboard/
│   │   ├── Agents/
│   │   ├── Findings/
│   │   └── ...
│   ├── services/         # API integration
│   │   ├── api.ts        # API client setup
│   │   └── endpoints/    # API endpoint definitions
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── types/            # TypeScript type definitions
│   └── context/          # React context providers
├── public/               # Static assets
└── tests/               # Test files
```

## Development Guidelines

### Code Organization
- Keep component files under 300 lines
- Keep components under 150 lines
- Keep hooks under 50 lines
- Use clear, descriptive names
- Follow TypeScript best practices
- Use proper type definitions

### UI/UX Guidelines
- Follow established Tailwind CSS patterns
- Maintain consistent component styling
- Ensure responsive design
- Implement proper loading states
- Provide clear error feedback
- Support keyboard navigation
- Maintain accessibility standards

### Testing
- Write unit tests for all components
- Maintain minimum 80% test coverage
- Use React Testing Library
- Mock API calls and external dependencies
- Test responsive behavior
- Test accessibility

### Performance
- Implement code splitting
- Use lazy loading for routes
- Optimize bundle size
- Implement proper caching
- Monitor performance metrics
- Use React.memo where appropriate

## Common Tasks

### Adding New Components
1. Create component in appropriate directory
2. Add TypeScript interfaces
3. Implement component logic
4. Add tests
5. Update documentation

### Adding New Pages
1. Create page component in `pages/`
2. Add route in `App.tsx`
3. Implement page logic
4. Add tests
5. Update navigation

### Running Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test -- src/components/Button.test.tsx

# Run with coverage
npm test -- --coverage
```

## Troubleshooting

### Common Issues
1. **API Connection**
   - Check Management API is running
   - Verify API URL in .env
   - Check network connectivity

2. **Build Issues**
   - Clear node_modules and reinstall
   - Check TypeScript errors
   - Verify dependency versions

3. **Styling Issues**
   - Check Tailwind configuration
   - Verify component classes
   - Check responsive breakpoints

### Development Tools
- Use React Developer Tools
- Monitor network requests
- Check console for errors
- Use performance profiler

## Contributing
1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Create pull request

## License
[Your License]
