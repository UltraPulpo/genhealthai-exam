# Frontend Agent Guide

## Tech Stack

- **Framework:** React 19.x with TypeScript 5.7.x
- **Build tool:** Vite 6.x
- **Test runner:** Vitest 3.x with @testing-library/react
- **Linter:** ESLint 9.x with @typescript-eslint (strict + stylistic)
- **Formatter:** Prettier 3.x
- **Pre-commit hooks:** Husky 9.x + lint-staged 15.x

## Quick Reference

| Action | Command |
|--------|---------|
| Start dev server | `npm run dev` |
| Build for production | `npm run build` |
| Run linter | `npm run lint` |
| Run linter with auto-fix | `npm run lint:fix` |
| Auto-format code | `npm run format` |
| Check formatting | `npm run format:check` |
| Run tests | `npm run test` |
| Run tests in watch mode | `npm run test:watch` |
| Run tests with coverage | `npm run test:coverage` |
| Run dependency audit | `npm audit` |

## Coverage Requirements

- **Line coverage:** 70%
- **Branch coverage:** 70%
- **Function coverage:** 70%
- **Statement coverage:** 70%

Coverage is enforced by vitest config. Tests that reduce coverage below the threshold will fail `npm run test:coverage`.

## Pre-Commit Hooks

The following checks run automatically on `git commit` via husky + lint-staged:
1. **Prettier** — auto-formats staged `.ts`, `.tsx`, `.css`, `.json`, `.md` files
2. **ESLint** — lints and auto-fixes staged `.ts`, `.tsx` files

To install hooks after a fresh clone: `npm install` (runs the `prepare` script automatically).

To bypass hooks (emergency only): `git commit --no-verify`

## Project Structure

```
frontend/
├── src/                   # Application source code
│   ├── main.tsx           # Entry point
│   ├── test/
│   │   └── setup.ts       # Vitest setup (jest-dom matchers)
│   └── ...
├── build/                 # Production build output
├── eslint.config.js       # ESLint flat config
├── vitest.config.ts       # Vitest config (extends vite.config.ts)
├── vite.config.ts         # Vite config
├── tsconfig.json          # TypeScript config (strict mode)
├── .prettierrc            # Prettier config
├── .husky/pre-commit      # Pre-commit hook
└── package.json           # Dependencies, scripts, lint-staged config
```

## Testing Conventions

- Test files live next to the source files they test: `Component.test.tsx`
- Use `@testing-library/react` for component tests
- Use `@testing-library/user-event` for simulating user interactions
- `@testing-library/jest-dom` matchers are globally available via setup file
- Vitest globals are enabled (`describe`, `it`, `expect` — no imports needed)

## Linting Rules

ESLint is configured with:
- `@typescript-eslint/strict-type-checked` — strictest TypeScript rules
- `@typescript-eslint/stylistic-type-checked` — consistent code style
- `eslint-plugin-react-hooks` — enforces Rules of Hooks
- `eslint-plugin-react-refresh` — validates Fast Refresh compatibility
- `eslint-config-prettier` — disables rules that conflict with Prettier

## Before Submitting Code

1. Run `npm run format` to auto-format
2. Run `npm run lint:fix` to fix lint issues
3. Run `npm run test:coverage` to verify tests pass and coverage meets thresholds
4. Run `npm audit` to check for dependency vulnerabilities
