# Spec Delta

## ADDED Requirements

### Requirement: Deep-linkable application routes

The application SHALL load the routed page when a user opens or refreshes any
application URL directly, including routes with two or more path segments. The
served entry document SHALL reference the entry script and stylesheet by a
location that does not depend on the current route, so the module executes and
the app mounts instead of leaving the page blank.

#### Scenario: Nested route opened directly renders inside the shell

- **WHEN** a user opens a nested route such as `/repairs/1`, `/repairs/new`, `/repairs/1/work-log/2`, or `/magazzino/bombole/1` directly
- **THEN** the app shell is visible and the content area shows that route's page, not a blank page

#### Scenario: Refreshing a nested route reloads the routed page

- **WHEN** a user is on a nested route and reloads the page
- **THEN** the app shell and the routed page are shown again

#### Scenario: Unknown deep link shows the not-found placeholder

- **WHEN** a user opens a URL that matches no defined route, including a nested one
- **THEN** the shell remains visible and the content area shows the not-found placeholder, without an unhandled error

#### Scenario: Built entry document loads its module regardless of route

- **WHEN** the production bundle's entry document is served for a nested route and the browser requests the script it references
- **THEN** the script is served as JavaScript from the application root, so the module executes
