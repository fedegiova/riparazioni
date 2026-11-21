# settings-ui Specification

## Purpose

The Settings page where the workshop maintains application settings — the
operator list, factory working hours, and the yearly holiday calendar — reached
from the app shell.

## Requirements

### Requirement: Settings page

The application SHALL provide a settings page that loads the current settings
when opened and saves the user's edits, presenting the backend error message
when a save is rejected.

#### Scenario: Load current settings

- **WHEN** a user opens the settings page
- **THEN** the page shows the stored operators, working hours, and holidays

#### Scenario: Save persists edits

- **WHEN** the user changes settings and activates save
- **THEN** the changes are persisted and remain after reopening the page

#### Scenario: Rejected save is shown

- **WHEN** a save is rejected by the backend
- **THEN** the page shows the returned error message and the stored settings are unchanged

### Requirement: Edit the operator list

The settings page SHALL let the user add and remove operators in a list editor.

#### Scenario: Add an operator

- **WHEN** the user adds an operator and saves
- **THEN** the operator appears in the list and is persisted

#### Scenario: Remove an operator

- **WHEN** the user removes an operator and saves
- **THEN** the operator no longer appears in the list and is removed from storage

### Requirement: Edit factory working hours

The settings page SHALL let the user edit each weekday's working intervals,
adding and removing intervals per day, where a day with no intervals is shown as
closed.

#### Scenario: Set a day's intervals

- **WHEN** the user sets a weekday's intervals and saves
- **THEN** that weekday's intervals are persisted

#### Scenario: Clear a day

- **WHEN** the user removes all intervals for a weekday and saves
- **THEN** that weekday is stored as closed

### Requirement: Edit holidays by year

The settings page SHALL provide a year selector and let the user add, edit, and
remove named holiday ranges for the selected year.

#### Scenario: Selecting a year shows that year's ranges

- **WHEN** the user selects a year in the holidays selector
- **THEN** the page shows the holiday ranges stored for that year

#### Scenario: Add a holiday range

- **WHEN** the user adds a named range with a start and end date for the selected year and saves
- **THEN** the range is persisted for that year

#### Scenario: Remove a holiday range

- **WHEN** the user removes a holiday range and saves
- **THEN** the range is no longer stored for that year
