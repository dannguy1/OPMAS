# UI Development Guide

## Overview
The OPMAS UI is a React-based single-page application built with TypeScript and Material UI. This guide provides information for developers working on the frontend.

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+

### Installation
```bash
cd ui
npm install
```

### Development
```bash
npm run dev
```

### Building
```bash
npm run build
```

## Project Structure
```
ui/
├── src/
│   ├── api/          # API integration
│   ├── assets/       # Static assets
│   ├── components/   # Reusable components
│   ├── context/      # React context providers
│   ├── hooks/        # Custom React hooks
│   ├── pages/        # Page components
│   ├── services/     # Business logic
│   ├── types/        # TypeScript types
│   └── utils/        # Utility functions
├── tests/            # Unit and integration tests
├── docs/            # UI-specific documentation
├── config/          # Configuration files
└── scripts/         # Build and deployment scripts
```

## Component Guidelines

### Component Structure
```typescript
import React from 'react';
import { styled } from '@mui/material/styles';

interface Props {
  // Props interface
}

const StyledComponent = styled('div')({
  // Styles
});

export const Component: React.FC<Props> = ({ prop1, prop2 }) => {
  // Component logic
  return (
    <StyledComponent>
      {/* Component JSX */}
    </StyledComponent>
  );
};
```

### State Management
- Use React Context for global state
- Use local state for component-specific state
- Use custom hooks for reusable state logic

### Styling
- Use Material UI components when possible
- Use styled-components for custom styling
- Follow the theme configuration in `src/theme.ts`

### Testing
- Write unit tests for all components
- Use React Testing Library
- Test user interactions and state changes

## API Integration
- Use the `apiService` from `src/services/api.ts`
- Handle loading and error states
- Implement proper error handling
- Use TypeScript interfaces for API responses

## Best Practices
1. **Code Organization**
   - Keep components small and focused
   - Use proper file naming conventions
   - Follow the project structure

2. **TypeScript**
   - Use proper type definitions
   - Avoid using `any`
   - Use interfaces for props

3. **Performance**
   - Use React.memo for expensive components
   - Implement proper code splitting
   - Optimize bundle size

4. **Accessibility**
   - Use semantic HTML
   - Implement proper ARIA attributes
   - Ensure keyboard navigation

## Common Issues and Solutions
1. **Material UI Theme**
   - Customize theme in `src/theme.ts`
   - Use theme provider at the root

2. **API Integration**
   - Handle CORS issues
   - Implement proper error handling
   - Use proper authentication

3. **Build Issues**
   - Clear node_modules and reinstall
   - Check TypeScript configuration
   - Verify environment variables
