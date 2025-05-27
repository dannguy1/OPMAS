# OPMAS UI Development Guide

## Table of Contents
1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Project Structure](#3-project-structure)
4. [Development Guidelines](#4-development-guidelines)
5. [UI Implementation Patterns](#5-ui-implementation-patterns)
6. [Testing & Quality Assurance](#6-testing--quality-assurance)
7. [Deployment & CI/CD](#7-deployment--cicd)
8. [AI Coding Assistance Guidelines](#8-ai-coding-assistance-guidelines)

## 1. Overview

The OPMAS UI is a React-based single-page application built with TypeScript and Tailwind CSS. This guide provides comprehensive information for developers working on the frontend, covering both implementation patterns and development workflows.

### Technology Stack
- React 18+
- TypeScript
- Tailwind CSS
- React Query
- React Hook Form
- React Router

### Key Features
- Authentication and protected routes
- Real-time updates via WebSocket
- Advanced search and filtering
- Responsive design
- Type-safe API integration

## 2. Getting Started

### Prerequisites
- Node.js 18+
- npm 9+
- Python 3.10+ (for monorepo tools)

### Installation
```bash
# Create virtual environment (if needed for monorepo tools)
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install UI dependencies
cd ui
npm install
```

### Development
```bash
# Start development server
npm run dev

# Run tests
npm test

# Run linting
npm run lint
```

## 3. Project Structure
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

## 4. Development Guidelines

### Code Organization
- Keep components under 400 lines
- Split large components into smaller ones
- Use composition over inheritance
- Follow monorepo component structure

### Type Safety
- Define strict TypeScript interfaces
- Use zod for runtime validation
- Add proper error types
- Document public APIs

### State Management
- Use React Context for global state
- Use local state for component-specific state
- Use custom hooks for reusable state logic
- Implement proper error boundaries

### API Integration
- Use React Query for data fetching
- Handle loading and error states
- Implement proper error handling
- Use TypeScript interfaces for API responses
- Implement rate limiting handling
- Add request validation

## 5. UI Implementation Patterns

### Page Layout
- **Main Content Area:** Wrap primary content in a card container
  - **Classes:** `bg-white p-6 rounded-lg shadow-md`
  - **Responsive Behavior:** Add `mx-4 md:mx-6 lg:mx-8` for responsive margins

### Headers
- **Page Title & Actions:**
  - **Container Classes:** `border-b border-gray-200 pb-4 mb-4 flex justify-between items-center`
  - **Title Classes:** `text-xl font-semibold text-gray-800`
  - **Search and Filter Section:**
    - **Container Classes:** `flex items-center space-x-4 mb-4`
    - **Search Input Classes:** `w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm`
    - **Sort Select Classes:** `px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm`
    - **Direction Toggle Classes:** `p-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500`

### Tables
- **General Structure:** Use standard HTML table elements
- **Container:** Wrap in `div` with `overflow-x-auto`
- **Table Classes:** `min-w-full divide-y divide-gray-200 border border-gray-200`
- **Thead Classes:** `bg-gray-50`
- **Th Classes:**
  - **Base:** `px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200`
  - **Sortable:** Add `cursor-pointer hover:bg-gray-100` and sort indicator icon
  - **Active Sort:** Add `text-blue-600` and appropriate sort direction icon
- **Tbody Classes:** `bg-white divide-y divide-gray-200`
- **Tr Classes (Hover):** `hover:bg-gray-50`
- **Td Classes:** `px-4 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200`

### List View Features
- **Search Implementation:**
  - **Debounce:** Use 300ms debounce for search input
  - **Placeholder:** "Search by name or description..."
  - **Clear Button:** Show when search has value
  - **Loading State:** Show spinner while searching

- **Sort Implementation:**
  - **Column Headers:** Show sort indicators (↑↓)
  - **Active Sort:** Highlight active column
  - **Direction Toggle:** Allow switching between asc/desc
  - **Default Sort:** Usually by name ascending

- **Pagination Implementation:**
  - **Page Size:** Default to 10 items per page
  - **Page Navigation:** Show current page and total pages
  - **Page Size Selector:** Allow changing items per page
  - **Total Count:** Show total number of items

### Forms
- **Labels:** `block text-sm font-medium text-gray-700 mb-1`
- **Required Indicator:** `<span className="text-red-500">*</span>`
- **Input/Textarea:**
  - **Classes:** `w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm`
  - **Error State:** Add `border-red-300` and `focus:ring-red-500 focus:border-red-500`

### Modals
- **Backdrop:** `fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm`
- **Content:** `bg-white rounded-lg shadow-xl p-6 w-full max-w-md`
- **Header:** `text-xl font-semibold mb-4 text-gray-800 border-b pb-2`
- **Footer:** `flex justify-end space-x-3 border-t pt-4`

## 6. Testing & Quality Assurance

### Testing Strategy
1. **Unit Tests**
   - Test individual components
   - Test utility functions
   - Test hooks
   - Maintain 80% coverage

2. **Integration Tests**
   - Test page flows
   - Test API integration
   - Test state management
   - Test component interactions

3. **E2E Tests**
   - Test critical user flows
   - Test error scenarios
   - Test responsive behavior
   - Test security features

### Code Quality
- Use ESLint and Prettier
- Follow TypeScript best practices
- Maintain consistent code style
- Use pre-commit hooks

### Accessibility
- Follow WCAG guidelines
- Test with screen readers
- Ensure keyboard navigation
- Regular accessibility audits

## 7. Deployment & CI/CD

### Build Process
```bash
# Build for production
npm run build

# Build Docker image
docker build -t opmas-ui .
```

### CI/CD Integration
- Run tests on every pull request
- Enforce code quality checks
- Generate and publish documentation
- Build and test Docker images

### Monitoring
- Implement structured logging
- Use centralized logging solution
- Monitor application metrics
- Set up alerting for critical issues

## 8. AI Coding Assistance Guidelines

### Common Pitfalls to Avoid

1. **Component Structure**
   - Always check if a component exceeds 400 lines before adding new code
   - Split large components into smaller, focused ones
   - Keep state management close to where it's used
   - Avoid prop drilling - use Context or composition instead

2. **Type Safety**
   - Never use `any` type - always define proper interfaces
   - Use `zod` for runtime validation of API responses
   - Add proper error types for all async operations
   - Document complex type relationships

3. **State Management**
   - Use React Query for server state
   - Keep UI state local when possible
   - Use Context only for truly global state
   - Implement proper loading and error states

4. **API Integration**
   - Always handle loading states
   - Implement proper error boundaries
   - Use React Query's built-in caching
   - Add proper TypeScript interfaces for API responses

5. **UI Implementation**
   - Follow the exact Tailwind classes specified in this guide
   - Maintain consistent spacing and layout
   - Implement proper responsive design
   - Add loading states for all async operations

### Code Review Checklist

1. **Before Making Changes**
   - Check if the component is already too large
   - Verify if the change fits the existing patterns
   - Consider if the change requires new dependencies
   - Review similar implementations in the codebase

2. **During Implementation**
   - Follow the exact class names from the style guide
   - Implement proper loading states
   - Add error handling
   - Maintain type safety
   - Keep components focused and small

3. **After Implementation**
   - Verify responsive behavior
   - Check accessibility
   - Test error scenarios
   - Verify loading states
   - Ensure proper TypeScript types

### Common Patterns

1. **List Views**
   ```typescript
   // Always include these features
   const [search, setSearch] = useState('');
   const [sortBy, setSortBy] = useState('name');
   const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
   const [page, setPage] = useState(1);
   const [limit, setLimit] = useState(10);

   // Use React Query for data fetching
   const { data, isLoading, error } = useQuery({
     queryKey: ['items', search, sortBy, sortDirection, page, limit],
     queryFn: () => fetchItems({ search, sortBy, sortDirection, page, limit })
   });
   ```

2. **Form Handling**
   ```typescript
   // Always use React Hook Form
   const form = useForm<FormData>({
     resolver: zodResolver(formSchema),
     defaultValues: {
       // Always provide default values
     }
   });

   // Always handle loading and error states
   const { mutate, isLoading } = useMutation({
     mutationFn: submitForm,
     onSuccess: () => {
       toast.success('Success');
       form.reset();
     },
     onError: (error) => {
       toast.error(error.message);
     }
   });
   ```

3. **Modal Implementation**
   ```typescript
   // Always include these props
   interface ModalProps {
     isOpen: boolean;
     onClose: () => void;
     onSubmit: (data: FormData) => Promise<void>;
     title: string;
     children: React.ReactNode;
   }

   // Always handle loading state
   const [isSubmitting, setIsSubmitting] = useState(false);
   ```

### Error Prevention

1. **Type Safety**
   - Always define proper interfaces
   - Use strict TypeScript configuration
   - Validate API responses
   - Handle all possible error states

2. **State Management**
   - Avoid unnecessary re-renders
   - Use proper dependency arrays
   - Implement proper cleanup
   - Handle race conditions

3. **UI Consistency**
   - Follow the exact class names
   - Maintain consistent spacing
   - Use the correct color scheme
   - Follow the responsive patterns

4. **Performance**
   - Implement proper memoization
   - Use proper code splitting
   - Optimize bundle size
   - Monitor resource usage

### Testing Requirements

1. **Component Tests**
   - Test all user interactions
   - Verify loading states
   - Test error scenarios
   - Check accessibility

2. **Integration Tests**
   - Test form submissions
   - Verify API integration
   - Test state management
   - Check error handling

3. **E2E Tests**
   - Test critical user flows
   - Verify responsive behavior
   - Test error scenarios
   - Check accessibility

### Documentation Requirements

1. **Code Documentation**
   - Document complex logic
   - Add JSDoc comments
   - Document props
   - Explain state management

2. **Type Documentation**
   - Document complex types
   - Explain type relationships
   - Document API types
   - Add examples

3. **Component Documentation**
   - Document usage examples
   - Explain props
   - Document state
   - Add accessibility notes

## Related Documents

- [OPMAS-DS.md](../specifications/OPMAS-DS.md): Main design specification
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md): System architecture overview
- [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md): API reference
