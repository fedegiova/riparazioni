# Spec Delta

## MODIFIED Requirements

### Requirement: Manage work-log entries from the repair page
The repair page SHALL show the repair's work-log entries and their descriptions in a table. On active repairs, it SHALL provide per-row controls to delete or edit an entry and a control to add a work log. On archived repairs, the work-log table SHALL remain visible without mutation controls.

#### Scenario: Cancel a work-log entry
- **WHEN** the user cancels a work-log entry on an active repair
- **THEN** the entry is deleted, and any gas-cylinder balance it recorded is restored

#### Scenario: Open a work-log entry for editing
- **WHEN** the user opens a work-log entry for editing on an active repair
- **THEN** the application navigates to that entry's work-log page

#### Scenario: Add a work log
- **WHEN** the user activates the add-work-log control on an active repair
- **THEN** the application opens the work-log page for a new entry on that repair

#### Scenario: View descriptions on an archived repair
- **WHEN** the user opens an archived repair
- **THEN** its work logs and descriptions are visible, but add, edit, stop, and delete controls are unavailable

### Requirement: Archive a repair
The repair page SHALL provide an archive control that closes the repair. If running timers block archiving, the application SHALL explain the blocker and let the user stop the timers explicitly before retrying.

#### Scenario: Archive closes the repair
- **WHEN** the user archives a repair with no running timers
- **THEN** the repair receives an end date and is no longer listed as active

#### Scenario: Manager must stop running timers
- **WHEN** the user attempts to archive a repair with running timers
- **THEN** the application identifies the blocking timers, the repair remains active, and the timers are not automatically stopped

### Requirement: Work-log editor page
The work-log page SHALL allow editing start time, end time, operator, and optional description on an active repair, and adding a gas recharge. The application SHALL require selection from the configured operator list before saving a new entry and SHALL NOT fall back to free-text operator input for creation.

#### Scenario: Edit times and operator
- **WHEN** the user changes a work-log entry's start time, end time, operator, or description and saves
- **THEN** the change is persisted to that entry

#### Scenario: New log requires operator selection
- **WHEN** the user opens a new work log and has not selected a configured operator
- **THEN** the application prevents submission and indicates that operator selection is required

#### Scenario: Configured operators are unavailable
- **WHEN** the configured operator list is empty or cannot be loaded for a new work log
- **THEN** the application explains why the log cannot be created instead of accepting an arbitrary operator

#### Scenario: Add a gas recharge
- **WHEN** the user records a gas recharge on the entry
- **THEN** the entry stores the gas data and any cylinder balance is updated accordingly

### Requirement: Stop a work-log entry
The repair page SHALL provide a control on each running work-log entry on an active repair that closes it by setting its end time.

#### Scenario: Stop closes the work-log entry
- **WHEN** the user stops a running work-log entry on an active repair
- **THEN** the entry receives an end time and no longer appears as running
