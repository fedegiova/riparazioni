# repairs-ui Specification

## Purpose

The workshop-facing repairs screens: the active-repairs landing, the searchable
full repairs list with Excel export, the repair detail/edit page with its parts
and work-log tables, and the work-log editor.

## Requirements

### Requirement: Active repairs landing page
The application SHALL show, on the landing route, a table of active repairs
(those with no end date) with the columns Customer, Total hours, and End date, a
per-row control to open that repair, and a control to start a new repair.

#### Scenario: Landing lists only active repairs
- **WHEN** a user opens the landing route
- **THEN** the table lists only repairs that have no end date

#### Scenario: Open a repair from its row
- **WHEN** the user activates a row's open control
- **THEN** the application navigates to that repair's detail page

#### Scenario: Start a new repair
- **WHEN** the user activates the create control
- **THEN** the application opens the repair page in new mode

### Requirement: Full repairs list
The application SHALL show a repairs list page listing all repairs, including
completed ones, and SHALL allow filtering the list.

#### Scenario: Completed repairs are listed
- **WHEN** a user opens the repairs list page
- **THEN** repairs with an end date appear alongside active ones

#### Scenario: Filtering narrows the list
- **WHEN** the user applies a filter
- **THEN** the table shows only repairs matching the filter

### Requirement: Delete a repair from the list
The repairs list SHALL allow deleting a repair only after a confirmation step.

#### Scenario: Confirm delete
- **WHEN** the user requests deletion of a repair and confirms
- **THEN** the repair is deleted and disappears from the list

#### Scenario: Cancel delete
- **WHEN** the user requests deletion and dismisses the confirmation
- **THEN** the repair is unchanged

### Requirement: Export repairs to Excel
The repairs list SHALL allow exporting repairs as an Excel workbook using the
currently applied filter.

#### Scenario: Export downloads a workbook
- **WHEN** the user activates the export control
- **THEN** the application downloads an Excel workbook of the filtered repairs

### Requirement: Create or edit a repair
The application SHALL provide a repair page for creating a new repair and
editing an existing one, with an editable customer and vehicle chosen through a
search modal, and editable start date, delivery date, and notes.

#### Scenario: Create a new repair
- **WHEN** the user completes the fields on the new-repair page and saves
- **THEN** the repair is created and the page shows the saved repair

#### Scenario: Pick a customer through search
- **WHEN** the user opens the customer field's search modal and selects a customer
- **THEN** the field shows the selected customer's name

#### Scenario: Edit an existing repair
- **WHEN** the user changes a field on an existing repair and saves
- **THEN** the change is persisted and reflected on the page

### Requirement: Manage a repair's parts
The repair page SHALL show the repair's parts in a table and SHALL allow adding
and deleting a part.

#### Scenario: Add a part
- **WHEN** the user adds a part with a quantity
- **THEN** the part appears in the parts table and is saved with the repair

#### Scenario: Delete a part
- **WHEN** the user deletes a part from the table
- **THEN** the part is removed and no longer saved with the repair

### Requirement: Manage work-log entries from the repair page
The repair page SHALL show the repair's work-log entries in a table with a
per-row control to cancel (delete) an entry or to open it for editing, and a
control to add a work log.

#### Scenario: Cancel a work-log entry
- **WHEN** the user cancels a work-log entry
- **THEN** the entry is deleted, and any gas-cylinder balance it recorded is restored

#### Scenario: Open a work-log entry for editing
- **WHEN** the user opens a work-log entry
- **THEN** the application navigates to that entry's work-log page

#### Scenario: Add a work log
- **WHEN** the user activates the add-work-log control
- **THEN** the application opens the work-log page for a new entry on that repair

### Requirement: Archive a repair
The repair page SHALL provide an archive control that closes the repair.

#### Scenario: Archive closes the repair
- **WHEN** the user archives a repair
- **THEN** the repair receives an end date and is no longer listed as active

### Requirement: Work-log editor page
The work-log page SHALL allow editing an entry's start time, end time, and
operator, and adding a gas recharge.

#### Scenario: Edit times and operator
- **WHEN** the user changes a work-log entry's start time, end time, or operator and saves
- **THEN** the change is persisted to that entry

#### Scenario: Add a gas recharge
- **WHEN** the user records a gas recharge on the entry
- **THEN** the entry stores the gas data and any cylinder balance is updated accordingly

### Requirement: Prefill the start time when creating
The application SHALL prefill the start date of a new repair and the start time
of a new work-log entry with the current date and time.

#### Scenario: New repair is prefilled with the current time
- **WHEN** the user opens the new-repair page
- **THEN** the start date field already holds the current date and time

#### Scenario: New work log is prefilled with the current time
- **WHEN** the user opens the new-work-log page
- **THEN** the start time field already holds the current date and time

### Requirement: Stop a work-log entry
The repair page SHALL provide a control on each open work-log entry that closes
it by setting its end time.

#### Scenario: Stop closes the work-log entry
- **WHEN** the user stops an open work-log entry
- **THEN** the entry receives an end time and no longer appears as open

### Requirement: Start a work log from the landing page
The active-repairs landing SHALL provide a per-row control that opens a new
work-log entry for that repair.

#### Scenario: Start a work log from a repair row
- **WHEN** the user activates a row's start-work-log control
- **THEN** the application opens the new-work-log page for that repair

### Requirement: Manage a repair's pictures
The repair page SHALL show the repair's pictures and SHALL allow capturing a
new picture from the device camera and deleting an existing one, without
asking the user for a file name.

#### Scenario: Capture a picture from the repair page
- **WHEN** the user activates the capture control and takes or chooses a photo
- **THEN** the photo is uploaded for that repair and appears in the pictures list

#### Scenario: No file name is requested
- **WHEN** the user activates the capture control
- **THEN** the device camera is opened directly and the user is not asked to name the file

#### Scenario: Pictures are shown as thumbnails
- **WHEN** the user opens a repair that has pictures
- **THEN** the repair page shows the pictures as thumbnails

#### Scenario: Delete a picture
- **WHEN** the user deletes a picture from the repair page
- **THEN** it is removed from the list and no longer stored for that repair

### Requirement: View a repair's pictures full screen
The repair page SHALL let the user open one of the repair's pictures in the
full-screen picture gallery, and SHALL let the user scroll between that repair's
pictures while it is open.

#### Scenario: Open a repair picture full screen
- **WHEN** the user activates one of the repair's picture thumbnails
- **THEN** that picture is shown full screen

#### Scenario: Scroll between the repair's pictures
- **WHEN** the user requests the next or previous picture while a repair picture is shown full screen
- **THEN** the viewer shows the next or previous picture of that repair
