# Spec Delta

## MODIFIED Requirements

### Requirement: Application shell with Material theme

The web application SHALL present a Material Design app shell: a top app bar
with a control that returns to the landing route and a settings control that
opens the settings page, a breadcrumb bar, a content area, and a bottom
navigation with the destinations Repairs List, Magazzino, and Anagrafica,
rendered with a single application theme (consistent palette, typography, and
component styling) on every route. The shell SHALL host the active-repairs
landing at `/`, the settings page at `/settings`, and an unhandled route SHALL
render a not-found placeholder instead of crashing.

#### Scenario: Home route renders inside the shell

- **WHEN** a user opens the application root URL
- **THEN** the app shell (app bar, breadcrumb bar, content area, bottom navigation) is visible and the content area shows the active-repairs landing page

#### Scenario: Home control returns to the landing

- **WHEN** a user activates the app bar's home control from another page
- **THEN** the application navigates back to the landing route

#### Scenario: Settings control opens the settings page

- **WHEN** a user activates the app bar's settings control
- **THEN** the application navigates to the settings route and the content area shows the settings page

#### Scenario: Settings route renders inside the shell

- **WHEN** a user opens the settings route directly
- **THEN** the app shell is visible and the content area shows the settings page

#### Scenario: Bottom navigation switches sections

- **WHEN** a user selects a bottom-navigation destination
- **THEN** the application shows that section's page and marks the destination as selected

#### Scenario: Unhandled route shows not-found placeholder

- **WHEN** a user navigates to a URL that matches no defined route
- **THEN** the shell remains visible and the content area shows a not-found placeholder page, without an unhandled error
