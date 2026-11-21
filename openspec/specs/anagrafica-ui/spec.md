# anagrafica-ui Specification

## Purpose

The read-only Anagrafica section where workshop staff look up the legacy
customer and allestimenti master data that repair records reference.

## Requirements

### Requirement: Anagrafica page with tabs

The application SHALL provide an Anagrafica page at `/anagrafica` presenting a
Clienti tab and an Allestimenti tab, and SHALL show the data belonging to the
selected tab.

#### Scenario: Open the Anagrafica page

- **WHEN** a user opens `/anagrafica`
- **THEN** the page shows the Clienti and Allestimenti tabs with the Clienti tab selected

#### Scenario: Switch to the allestimenti tab

- **WHEN** the user selects the Allestimenti tab
- **THEN** the page shows the allestimenti list

### Requirement: Read-only customer list

The Clienti tab SHALL list the customers from the legacy customers reference
data, showing each customer's name together with its address and contact
fields, and SHALL load them when the tab is opened.

#### Scenario: Customers are listed

- **WHEN** the user opens the Clienti tab
- **THEN** the page shows the customers returned by the reference data, including each customer's name

#### Scenario: Customer load failure is reported

- **WHEN** the customers cannot be loaded
- **THEN** the page shows an error instead of an empty list

### Requirement: Read-only allestimenti list

The Allestimenti tab SHALL list the vehicles from the legacy allestimenti
reference data, showing each vehicle's license plate and its vehicle, body, and
model fields, and SHALL load them when the tab is opened.

#### Scenario: Allestimenti are listed

- **WHEN** the user opens the Allestimenti tab
- **THEN** the page shows the vehicles returned by the reference data, including each vehicle's license plate

#### Scenario: Allestimenti load failure is reported

- **WHEN** the allestimenti cannot be loaded
- **THEN** the page shows an error instead of an empty list

### Requirement: Search within a tab

Each tab SHALL provide a single search box that filters the displayed rows to
those whose visible fields contain the query, matching case-insensitively, and
SHALL show all rows when the query is empty.

#### Scenario: Matching rows are kept

- **WHEN** the user enters a query that matches some rows
- **THEN** the list shows only the rows matching the query

#### Scenario: Clearing the search restores all rows

- **WHEN** the user clears the search query
- **THEN** the list shows all rows again

#### Scenario: No matches shows an empty result

- **WHEN** the user enters a query that matches no rows
- **THEN** the list shows no rows

### Requirement: Anagrafica data is read-only

The Anagrafica page SHALL present the customer and allestimenti data without
any control to create, edit, or delete records.

#### Scenario: No write controls are offered

- **WHEN** the user views either the Clienti or the Allestimenti tab
- **THEN** the page shows no control to create, edit, or delete records
