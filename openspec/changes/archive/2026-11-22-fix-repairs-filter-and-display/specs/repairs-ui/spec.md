# Spec Delta

## MODIFIED Requirements

### Requirement: Active repairs landing page
The application SHALL show, on the landing route, a table of active repairs (those with no end date) with the columns Customer, Total hours, and Delivery date, a per-row control to open that repair, and a control to start a new repair.

#### Scenario: Landing lists only active repairs
- **WHEN** a user opens the landing route
- **THEN** the table lists only repairs that have no end date

#### Scenario: Landing shows the requested delivery date
- **WHEN** a user opens the landing route
- **THEN** the Delivery date column shows each listed repair's requested delivery date

#### Scenario: Open a repair from its row
- **WHEN** the user activates a row's open control
- **THEN** the application navigates to that repair's detail page

#### Scenario: Start a new repair
- **WHEN** the user activates the create control
- **THEN** the application opens the repair page in new mode

### Requirement: Full repairs list
The application SHALL show a repairs list page listing all repairs, including completed ones, with the columns Customer, Total hours, Delivery date, and End date, and SHALL allow filtering the list.

#### Scenario: Completed repairs are listed
- **WHEN** a user opens the repairs list page
- **THEN** repairs with an end date appear alongside active ones

#### Scenario: List shows delivery and end dates
- **WHEN** a user opens the repairs list page
- **THEN** the table shows each repair's requested delivery date and its actual end date, the end date being blank while the repair is open

#### Scenario: Filtering narrows the list
- **WHEN** the user applies a filter
- **THEN** the table shows only repairs matching the filter

### Requirement: Create or edit a repair
The application SHALL provide a repair page for creating a new repair and editing an existing one, with an editable customer and vehicle chosen through a search modal, and editable start date, delivery date, and notes. The vehicle field SHALL show the selected vehicle's plate.

#### Scenario: Create a new repair
- **WHEN** the user completes the fields on the new-repair page and saves
- **THEN** the repair is created and the page shows the saved repair

#### Scenario: Pick a customer through search
- **WHEN** the user opens the customer field's search modal and selects a customer
- **THEN** the field shows the selected customer's name

#### Scenario: Loaded repair shows the vehicle plate
- **WHEN** the user opens an existing repair that has a vehicle
- **THEN** the Targa field shows that vehicle's plate, not its numeric id

#### Scenario: Edit an existing repair
- **WHEN** the user changes a field on an existing repair and saves
- **THEN** the change is persisted and reflected on the page
