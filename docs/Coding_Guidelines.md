# Shepherd: Coding Guidelines

This document outlines the development standards, architecture principles, and workflow protocols for the Shepherd project. Adherence to these guidelines is mandatory to ensure code quality, consistency, and maintainability.

---

### **The Blueprint and Build Protocol**

This protocol governs the entire lifecycle of creating any non-trivial feature.

*   **Phase 1: The Blueprint (Planning & Documentation):** Before writing code, a plan MUST be created in a new file at `docs/features/FeatureName.md`. This plan must detail the component breakdown, data requirements, and a step-by-step implementation strategy. This plan requires human approval before proceeding.
*   **Phase 2: The Build (Iterative Implementation):** The approved plan is executed one step at a time. Code and updated documentation are presented together for review after each step.

---

### **Technology-Specific Guidelines**

These rules are specific to the Shepherd project's tech stack (Next.js, Electron, FastAPI, Python).

#### **1. General Principles**
*   **Version Control:** All work must be done on feature branches (`feature/FR-XXX-description`). Commits should be atomic and have clear, descriptive messages.
*   **Local First:** The application must function entirely offline. No core feature should rely on an external internet connection.
*   **Error Handling:** All API calls, file operations, and AI model interactions must be wrapped in robust error-handling blocks.

#### **2. Frontend (Electron + Next.js)**
*   **Framework:** Use Next.js with TypeScript.
*   **Component Model:** Default to React Server Components (RSCs) for anything that doesn't require client-side interactivity to maximize performance. Use Client Components (`'use client'`) only when necessary (e.g., for hooks like `useState`, `useEffect`).
*   **Styling:** Use **Tailwind CSS** for all styling. Do not write custom CSS files or use CSS-in-JS libraries. Create reusable UI components for common elements like buttons and panels.
*   **State Management:** For simple, local state, use React Hooks (`useState`, `useContext`). For complex, global state, use a lightweight library like Zustand.
*   **API Communication:** Use a typed client (e.g., generated from the OpenAPI spec of the backend) for communicating between the Next.js frontend and the FastAPI backend to ensure type safety.
*   **Directory Structure:**
    ```
    /src
    ├── /app          # Next.js App Router
    ├── /components
    │   ├── /ui       # Reusable, unstyled primitives (Button, Card, etc.)
    │   └── /features # Complex components related to a specific feature
    ├── /lib          # Utility functions, API clients
    └── /hooks        # Custom React hooks
    ```

#### **3. Backend (FastAPI)**
*   **Language:** Python 3.10+ with full type hinting.
*   **Validation:** Use **Pydantic** for all data modeling and validation, both for API request/response bodies and for internal data structures.
*   **API Design:** Follow RESTful principles. Endpoints should be logical and well-documented using FastAPI's automatic OpenAPI/Swagger documentation generation.
*   **Dependency Injection:** Leverage FastAPI's dependency injection system for managing resources like database connections and AI model instances.
*   **Asynchronous Operations:** Use `async` and `await` for all I/O-bound operations (file access, network requests) to keep the server non-blocking. CPU-bound tasks (like AI inference) should be run in a separate threadpool to avoid blocking the event loop.
*   **Directory Structure:**
    ```
    /backend
    ├── /app
    │   ├── /api        # API router definitions
    │   ├── /core       # Configuration, settings
    │   ├── /models     # Pydantic models
    │   ├── /services   # Business logic (e.g., transcription, export)
    │   └── main.py     # FastAPI app instantiation
    ├── requirements.txt
    ```