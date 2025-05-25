# OPMAS UI Implementation Guidelines

This document outlines the established UI/UX patterns and Tailwind CSS conventions used in the OPMAS frontend application. Adhering to these guidelines ensures visual consistency and a predictable user experience across different pages.

## 1. Design Principles

* **Consistency:** Maintain consistent patterns across all pages and components
* **Clarity:** Clear visual hierarchy and intuitive navigation
* **Efficiency:** Minimize user actions required for common tasks
* **Feedback:** Provide clear feedback for all user actions
* **Accessibility:** Ensure the interface is usable by everyone
* **Responsiveness:** Optimize for all screen sizes
* **Performance:** Maintain smooth interactions and quick load times

## 2. Page Layout

- **Main Content Area:** Most pages should wrap their primary content within a card container.
  - **Classes:** `bg-white p-6 rounded-lg shadow-md`
  - **Purpose:** Provides a visually distinct and consistent container for page elements.
  - **Responsive Behavior:** Add `mx-4 md:mx-6 lg:mx-8` for responsive margins

## 3. Headers

- **Page Title & Actions:** Each page card should start with a header section.
  - **Container Classes:** `border-b border-gray-200 pb-4 mb-4 flex justify-between items-center`
  - **Title (`h1`) Classes:** `text-xl font-semibold text-gray-800`
  - **Primary Action Button:** Typically placed on the right side of the header (See Buttons section).
  - **Breadcrumb Navigation:** Add above the header when needed
    - **Classes:** `text-sm text-gray-500 mb-2`
    - **Separator:** `mx-2 text-gray-400`
- **Sub-Headers (within page):** For sections like "Steps" within a page.
  - **Title (`h2`) Classes:** `text-lg font-medium text-gray-700`
  - **Description:** Optional subtitle with `text-sm text-gray-500 mt-1`

## 4. Tables

- **General Structure:** Use standard HTML table elements (`table`, `thead`, `tbody`, `tr`, `th`, `td`).
- **Container:** Wrap the table in a `div` with `overflow-x-auto` for responsiveness.
- **Table Classes:** `min-w-full divide-y divide-gray-200 border border-gray-200`
- **Thead Classes:** `bg-gray-50`
- **Th Classes:** `px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200` (Omit `border-r` for the last header cell).
- **Tbody Classes:** `bg-white divide-y divide-gray-200`
- **Tr Classes (Hover):** Consider adding `hover:bg-gray-50` for visual feedback, although not strictly enforced yet.
- **Td Classes:** `px-4 py-3 whitespace-nowrap text-sm` (adjust `whitespace-nowrap` as needed). Add `border-r border-gray-200`. Use `align-top` for cells containing multi-line content or buttons.
  - **Text Color:** Default `text-gray-900` or `text-gray-600`. Use `text-blue-600 hover:underline` for links within table cells.
- **Empty Table State:** Use a single row with `td` spanning all columns (`colSpan={numberOfColumns}`).
  - **Classes:** `px-4 py-6 text-center text-sm text-gray-500`
- **Preformatted Text (e.g., JSON):** Use `<pre>` tags within table cells.
  - **Classes:** `text-xs whitespace-pre-wrap font-mono bg-gray-100 p-2 rounded border border-gray-200`
- **Pagination:**
  - **Container Classes:** `flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6`
  - **Page Info Classes:** `text-sm text-gray-700`
  - **Navigation Classes:** `flex justify-between flex-1 sm:hidden`
  - **Button Classes:** `relative inline-flex items-center px-4 py-2 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50`

## 5. Buttons

- **Primary Action (e.g., Add, Submit):** Solid background, typically blue.
  - **Classes:** `px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 transition duration-150 shadow disabled:opacity-50`
  - **Small Variant (`btn-sm`):** Use `px-3 py-1 text-sm` (e.g., for "Add Step").
  - **Icon Button:** Add `inline-flex items-center` and include icon with `mr-2` or `ml-2`
- **Secondary/Cancel Action:** White background, gray border.
  - **Classes:** `px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-400 transition duration-150 text-sm disabled:opacity-50`
- **Destructive Action (e.g., Delete):** White background, red border/text.
  - **Classes:** `px-2 py-1 text-xs border border-red-500 bg-white text-red-600 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150` (This is the small variant `btn-outline-danger btn-sm`).
- **Edit Action (Table):** White background, gray border (small variant).
  - **Classes:** `px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150` (`btn-outline-secondary btn-sm`).
- **General:** Include `disabled:opacity-50` for disabled states. Include `transition duration-150` for smooth hover effects.
- **Loading State:** Add spinner when button is in loading state
  - **Classes:** `animate-spin -ml-1 mr-2 h-4 w-4 text-white`

## 6. Modals

- **Backdrop:** Fixed position overlay.
  - **Classes:** `fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm`
  - **Behavior:** Close modal on backdrop click (`onClick={onClose}`).
- **Modal Content:** Centered container.
  - **Classes:** `bg-white rounded-lg shadow-xl p-6 w-full max-w-md` (or `max-w-lg` for wider content like JSON editors).
  - **Behavior:** Prevent closing when clicking inside (`onClick={(e) => e.stopPropagation()}`).
- **Modal Header:** Title with bottom border.
  - **Classes:** `text-xl font-semibold mb-4 text-gray-800 border-b pb-2`
- **Modal Footer:** Container for action buttons.
  - **Classes:** `flex justify-end space-x-3 border-t pt-4`
- **Buttons:** Typically "Cancel" (Secondary Outline) and "Submit/Save" (Primary Blue).
- **Error Display:** Place error messages (`p` tag, `text-red-600 text-sm mb-3`) near the top of the form.
- **State Management:** Parent page controls modal `isOpen` state. Modals manage their own internal form state and submission state (`isSubmitting`). `onSubmit` prop should be an async function; modals handle calling it, managing `isSubmitting`, and displaying errors thrown by `onSubmit`.
- **Loading State:** Show loading spinner in submit button when `isSubmitting` is true
- **Success State:** Show success message and auto-close after successful submission

## 7. Forms (within Modals/Pages)

- **Labels:** `block text-sm font-medium text-gray-700 mb-1`
- **Required Indicator:** `<span className="text-red-500">*</span>` after the label text.
- **Input/Textarea:** Common styling for text inputs and textareas.
  - **Classes:** `w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm`
  - **Textarea:** Add `rows={n}` as needed. Use `font-mono` for code/JSON inputs.
- **Helper Text:** Small text below inputs.
  - **Classes:** `text-xs text-gray-500 mt-1`
- **Error States:**
  - **Input Classes:** Add `border-red-300` and `focus:ring-red-500 focus:border-red-500`
  - **Error Message:** `text-sm text-red-600 mt-1`
- **Select/Dropdown:**
  - **Container Classes:** `relative`
  - **Select Classes:** Same as input, add `appearance-none`
  - **Dropdown Icon:** `absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none`
- **Checkbox/Radio:**
  - **Container Classes:** `flex items-center`
  - **Input Classes:** `h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded`
  - **Label Classes:** `ml-2 block text-sm text-gray-900`

## 8. Notifications

- **Library:** `react-hot-toast` is used for success/error notifications.
- **Usage:** Call `toast.success('Message')` or `toast.error('Message')` after API operations complete in the parent page components (often within modal `onSubmit` handlers or delete handlers).
- **Position:** Top-right corner by default
- **Duration:** 3 seconds for success, 5 seconds for errors
- **Customization:**
  - **Success:** Green background with checkmark icon
  - **Error:** Red background with X icon
  - **Loading:** Blue background with spinner
- **Dismissible:** All notifications can be manually dismissed

## 9. Links

- **Back Links:** Placed near the top of the page card, before the main header.
  - **Classes:** `text-sm text-blue-600 hover:underline mb-4 inline-block`
  - **Content:** `&larr; Back to [Previous Page]`
- **Table Links:** Links within table cells.
  - **Classes:** `text-blue-600 hover:underline`
- **Navigation Links:** Links in the sidebar or header
  - **Classes:** `text-gray-600 hover:text-gray-900`
  - **Active State:** `text-blue-600 font-medium`

## 10. Loading & Error States (Page Level)

- **Placement:** Display within the main card body, typically centered, replacing the main content (e.g., table) while loading or if a fatal error occurs.
- **Loading Classes:** `text-gray-600 py-4 text-center`
- **Error Classes:** `text-red-600 font-semibold py-4 text-center`
- **Conditional Rendering:** Use boolean state variables (`loading`, `error`) to conditionally render these messages or the main content.
- **Skeleton Loading:**
  - **Container Classes:** `animate-pulse`
  - **Text Classes:** `h-4 bg-gray-200 rounded w-3/4`
  - **Image Classes:** `h-32 bg-gray-200 rounded`
- **Error Recovery:**
  - **Retry Button:** Add retry button below error message
  - **Classes:** `mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700`

## 11. Responsive Design

- **Breakpoints:**
  - **sm:** 640px
  - **md:** 768px
  - **lg:** 1024px
  - **xl:** 1280px
  - **2xl:** 1536px
- **Mobile First:** Design for mobile first, then enhance for larger screens
- **Common Patterns:**
  - **Stack to Grid:** `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
  - **Full to Contained:** `w-full md:w-auto`
  - **Hidden to Visible:** `hidden md:block`
  - **Stack to Side-by-Side:** `flex flex-col md:flex-row`

## 12. Accessibility

- **Color Contrast:** Ensure sufficient contrast between text and background
- **Focus States:** Visible focus rings on interactive elements
- **ARIA Labels:** Add appropriate ARIA labels to interactive elements
- **Keyboard Navigation:** Support full keyboard navigation
- **Screen Readers:** Test with screen readers
- **Skip Links:** Add skip links for keyboard users
- **Error Messages:** Associate error messages with form controls

## 13. Performance Optimization

- **Image Optimization:**
  - Use appropriate image formats (WebP with fallback)
  - Implement lazy loading
  - Use responsive images
- **Code Splitting:**
  - Lazy load routes
  - Split large components
- **Memoization:**
  - Use `React.memo` for pure components
  - Use `useMemo` and `useCallback` for expensive computations
- **Virtualization:**
  - Use virtual lists for long lists
  - Implement infinite scrolling where appropriate

## 14. Dark Mode Support

- **Toggle:**
  - Add dark mode toggle in header
  - Use `dark:` variant for dark mode styles
- **Common Dark Mode Classes:**
  - **Background:** `dark:bg-gray-900`
  - **Text:** `dark:text-gray-100`
  - **Borders:** `dark:border-gray-700`
  - **Hover States:** `dark:hover:bg-gray-800`

## 15. Component Library Integration

- **Headless UI:**
  - Use for accessible components
  - Style with Tailwind CSS
- **React Icons:**
  - Use consistent icon set
  - Maintain consistent sizing
- **Date/Time:**
  - Use `date-fns` for date formatting
  - Implement timezone support
- **Form Validation:**
  - Use `react-hook-form` for form handling
  - Implement `zod` for schema validation

## 16. Testing Guidelines

- **Component Testing:**
  - Test rendering
  - Test user interactions
  - Test accessibility
- **Integration Testing:**
  - Test form submissions
  - Test API interactions
  - Test navigation
- **E2E Testing:**
  - Test critical user flows
  - Test error scenarios
  - Test responsive behavior

## 17. Code Organization

- **Component Structure:**
  - One component per file
  - Co-locate related components
  - Use index files for exports
- **Hooks:**
  - Custom hooks in separate files
  - Reusable logic in hooks
- **Utils:**
  - Helper functions in utils
  - Constants in separate files
- **Types:**
  - TypeScript interfaces/types
  - Shared type definitions

## 18. Version Control

- **Branching Strategy:**
  - Feature branches
  - Pull request reviews
  - Semantic versioning
- **Commit Messages:**
  - Conventional commits
  - Clear descriptions
  - Reference issues
- **Code Review:**
  - UI/UX consistency
  - Accessibility
  - Performance
  - Testing coverage

## Related Documents

- [OPMAS-DS.md](../specifications/OPMAS-DS.md): Main design specification
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md): System architecture overview
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md): Development environment setup
- [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md): API reference
