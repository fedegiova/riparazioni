# Spec Delta

## MODIFIED Requirements

### Requirement: Settings page

The application SHALL provide a settings page that loads the current settings
when opened and saves the user's edits, presenting the backend error message
when a save is rejected.

#### Scenario: Load current settings

- **WHEN** a user opens the settings page
- **THEN** the page shows the stored operators, working hours, holidays, and gas types

#### Scenario: Save persists edits

- **WHEN** the user changes settings and activates save
- **THEN** the changes are persisted and remain after reopening the page

#### Scenario: Rejected save is shown

- **WHEN** a save is rejected by the backend
- **THEN** the page shows the returned error message and the stored settings are unchanged

## ADDED Requirements

### Requirement: Edit the gas type list

The settings page SHALL let the user add and remove gas types in a list editor.

#### Scenario: Add a gas type

- **WHEN** the user adds a gas type and saves
- **THEN** the gas type appears in the list and is persisted

#### Scenario: Remove a gas type

- **WHEN** the user removes a gas type and saves
- **THEN** the gas type no longer appears in the list and is removed from storage
