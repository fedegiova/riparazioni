# Spec Delta

## ADDED Requirements

### Requirement: Cylinder operation-log page
The application SHALL provide a per-cylinder page at
/magazzino/bombole/:id showing the cylinder's identity and current state
(full and remaining weight, archived flag) and its operation log. The page
SHALL be reached from the Bombole tab of the warehouse page.

#### Scenario: Open the page from the cylinders list
- **WHEN** the user activates a cylinder's log control in the Bombole tab
- **THEN** the application navigates to that cylinder's page

#### Scenario: Page shows the cylinder's current state
- **WHEN** the user opens a cylinder's page
- **THEN** the page shows the cylinder's identity, its remaining and full weight, and whether it is archived

#### Scenario: Page lists the operations
- **WHEN** the user opens a cylinder's page
- **THEN** the page lists the cylinder's refills and gas movements, newest first, each showing its date, operation kind, weights, and resulting remaining weight

### Requirement: Initial balance on create, read-only on edit
The cylinder editor SHALL offer a remaining-weight (initial balance) control
when creating a cylinder, so a non-empty cylinder can be registered, and SHALL
NOT allow the remaining weight to be changed when editing an existing cylinder.

#### Scenario: New cylinder can set an initial balance
- **WHEN** the user creates a cylinder and enters a remaining weight
- **THEN** the cylinder is saved with that balance

#### Scenario: Omitted balance defaults to full
- **WHEN** the user creates a cylinder and leaves the remaining weight empty
- **THEN** the cylinder is saved full

#### Scenario: Editing cannot change the balance
- **WHEN** the user opens an existing cylinder in the editor
- **THEN** the balance is shown read-only and cannot be edited

### Requirement: New cylinder balance cannot exceed full weight
When creating a cylinder, the editor SHALL reject a remaining weight greater
than the full weight, validating in the client before calling the API.

#### Scenario: Over-full initial balance is rejected
- **WHEN** the user creates a cylinder with a remaining weight above the full weight
- **THEN** the editor reports the error and the cylinder is not saved

#### Scenario: Balance equal to full is allowed
- **WHEN** the user creates a cylinder with a remaining weight equal to the full weight
- **THEN** the cylinder is saved

### Requirement: Operation entries link to their source record
The cylinder page SHALL show each operation's reference and SHALL let the user
open the source record: a gas-movement entry SHALL link to its repair (and work
log), and a refill entry SHALL show its recorded reference text.

#### Scenario: Gas movement links to its repair
- **WHEN** the user activates a gas-movement entry's reference
- **THEN** the application opens the source repair's page

#### Scenario: Refill shows its reference
- **WHEN** a refill entry with a recorded reference appears on the page
- **THEN** the page shows that reference text for the entry

#### Scenario: Failed log load is reported
- **WHEN** the log cannot be loaded for the cylinder
- **THEN** the page shows an error instead of an empty list
