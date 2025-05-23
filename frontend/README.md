# OPMAS Frontend

This is the frontend application for the OPMAS (Operational Performance Monitoring and Alerting System) project. It provides a modern, responsive user interface for managing agents, viewing findings, and configuring the system.

## Features

- Dashboard with system overview and key metrics
- Agent management (create, update, delete)
- Agent rule configuration
- Finding management and filtering
- Real-time updates using React Query
- Responsive design with Material-UI
- TypeScript for type safety

## Prerequisites

- Node.js 16.x or later
- npm 7.x or later

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at http://localhost:3000.

## Development

- `npm start` - Start the development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Project Structure

```
src/
  ├── components/     # Reusable UI components
  ├── pages/         # Page components
  ├── services/      # API services
  ├── types/         # TypeScript type definitions
  ├── utils/         # Utility functions
  ├── App.tsx        # Main application component
  ├── index.tsx      # Application entry point
  └── theme.ts       # Material-UI theme configuration
```

## Technologies Used

- React 18
- TypeScript
- Material-UI
- React Query
- React Router
- Axios
- date-fns
- web-vitals

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

This project is licensed under the MIT License. 