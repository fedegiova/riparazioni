# warehouse-ui Specification

## Purpose

The warehouse page where the workshop manages its spare parts and gas
cylinders — listing, creating, editing, refilling, and retiring them — reached
from the application shell.

## Requirements

### Requirement: Warehouse page with tabs
The application SHALL provide a warehouse page at /magazzino presenting tabs
for the regular spare parts, the refrigerator spare parts, and the gas
cylinders, and SHALL show the data belonging to the selected tab.

#### Scenario: Open the warehouse page
- **WHEN** a user opens /magazzino
- **THEN** the page shows the Ricambi, Ricambi Frigo, and Bombole tabs with the Ricambi tab selected

#### Scenario: Switch to the cylinders tab
- **WHEN** the user selects the Bombole tab
- **THEN** the page shows the gas-cylinder overview and list

### Requirement: Manage spare parts
The page SHALL let the user create, edit, and delete spare parts, and SHALL
present refrigerator parts and regular parts through the same management
screen, differing only in the refrigerator-part flag.

#### Scenario: Create a spare
- **WHEN** the user creates a spare with its fields and saves
- **THEN** the spare appears in the list and is persisted

#### Scenario: Edit a spare
- **WHEN** the user changes a spare's fields and saves
- **THEN** the change is persisted

#### Scenario: Delete a spare
- **WHEN** the user deletes an unreferenced spare
- **THEN** the spare is removed from the list

#### Scenario: Refrigerator parts share the screen
- **WHEN** the user opens the Ricambi Frigo tab
- **THEN** the same part management screen is shown listing only refrigerator parts

### Requirement: Manage gas cylinders
The page SHALL let the user create, edit, and delete gas cylinders, and SHALL
provide a per-cylinder overview of the current state.

#### Scenario: Create a cylinder
- **WHEN** the user creates a cylinder with its fields and saves
- **THEN** the cylinder appears in the list and is persisted

#### Scenario: Edit a cylinder
- **WHEN** the user changes a cylinder's fields and saves
- **THEN** the change is persisted

#### Scenario: Overview of cylinder state
- **WHEN** the user views the Bombole tab
- **THEN** the page shows each cylinder's remaining and full weight and a summary of cylinder states

#### Scenario: Refill a cylinder
- **WHEN** the user records a refill for a cylinder
- **THEN** the cylinder's remaining weight is shown as full

#### Scenario: Archive and restore a cylinder
- **WHEN** the user archives a cylinder below a quarter and then restores it
- **THEN** the cylinder is archived and then shown as active again with its balance unchanged

#### Scenario: Deletion is blocked for a referenced cylinder
- **WHEN** the user attempts to delete a cylinder referenced by a work log
- **THEN** the page reports the backend error and the cylinder remains

### Requirement: Choose gas types from settings
The cylinder editor SHALL offer the gas types from the gas_types setting as the
available choices for a cylinder's gas kind.

#### Scenario: Gas types populate the picker
- **WHEN** the user opens the cylinder editor and gas types are configured
- **THEN** the editor offers those gas types as choices
