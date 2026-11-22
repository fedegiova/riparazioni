# repairs-ui Specification

## Purpose

The workshop-facing repairs screens: the active-repairs landing, the searchable
full repairs list with Excel export, the repair detail/edit page with its parts
and work-log tables, and the work-log editor.

## Requirements

### Requirement: Active repairs landing page
The application SHALL show, on the landing route, a table of active repairs
(those with no end date) with the columns Customer, Total hours, and Delivery
date, a per-row control to open that repair, and a control to start a new repair.

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
The application SHALL show a repairs list page listing all repairs, including
completed ones, with the columns Customer, Total hours, Delivery date, and End
date, and SHALL allow filtering the list.

#### Scenario: Completed repairs are listed
- **WHEN** a user opens the repairs list page
- **THEN** repairs with an end date appear alongside active ones

#### Scenario: List shows delivery and end dates
- **WHEN** a user opens the repairs list page
- **THEN** the table shows each repair's requested delivery date and its actual end date, the end date being blank while the repair is open

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
search modal, and editable start date, delivery date, and notes. The vehicle
field SHALL show the selected vehicle's plate.

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
On an active repair, the work-log editor SHALL support start time, end time, operator, and optional description. It SHALL require a configured operator for a new entry, with no free-text fallback. It SHALL offer a gas operation selector with None, Fill, Recovery, and Recovery + recharge, defaulting to None for new work logs.

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
- **WHEN** the user saves a valid Fill or Recovery + recharge operation
- **THEN** the work log displays the saved gas data and the cylinder balance reflects the movement

#### Scenario: None leaves the gas fields hidden
- **WHEN** the user selects None
- **THEN** the gas inputs are hidden and no gas movement is submitted; explicitly switching a saved gas operation to None requests reversal

#### Scenario: Gas operation shows equipment and matching cylinders
- **WHEN** the user selects a gas operation on a repair with valid installed equipment
- **THEN** the editor identifies the refrigerator, shows its nameplate capacity and gas type, and offers cylinders of that gas type only

#### Scenario: Only the applicable measurement is editable
- **WHEN** the user selects Fill, Recovery, or Recovery + recharge
- **THEN** the editor respectively requires only the added amount, recovered amount, or measured net added amount as the weight input; for combined work it previews the recovered amount as calculated, not editable

#### Scenario: Equipment blockers are actionable
- **WHEN** the user selects a gas operation on a repair missing an allestimento or configured refrigerator, or whose locked refrigerator has been replaced
- **THEN** the editor blocks that gas save and directs the user respectively to the repair's vehicle selector, Anagrafica, or a separate repair for the new unit

#### Scenario: Metadata edits leave the gas operation unchanged
- **WHEN** the user edits only the time, operator, or description of a saved gas work log
- **THEN** the editor saves those fields without submitting a replacement gas operation

### Requirement: Show the repair's gas-work lock
The repair page SHALL identify the refrigerator locked to the repair and SHALL prevent changing the associated vehicle after the gas-work lock is set.

#### Scenario: A locked repair shows its recorded unit
- **WHEN** the user opens a repair locked to a refrigerator that has since been replaced on the allestimento
- **THEN** the repair shows the recorded refrigerator, not the replacement, and the vehicle selector cannot reassign the repair

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
The repair page SHALL provide a control on each running work-log entry on an active repair that closes it by setting its end time.

#### Scenario: Stop closes the work-log entry
- **WHEN** the user stops a running work-log entry on an active repair
- **THEN** the entry receives an end time and no longer appears as running

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

### Requirement: Repair and work-log times are entered and shown as local wall-clock time
The application SHALL send a repair start date and work-log start/end times as the local wall-clock value entered in the field, without converting it to UTC, and SHALL show the stored value back unchanged. The "now" actions that bypass the field — archiving a repair and stopping a work-log entry — SHALL record the local current wall-clock time.

#### Scenario: An entered repair start is shown unchanged after saving
- **WHEN** the user saves a repair whose Start date is `2026-11-22T00:07` and reopens it
- **THEN** the Start date field shows `2026-11-22T00:07`

#### Scenario: Entered work-log times are shown unchanged after saving
- **WHEN** the user saves a work-log entry with start `2026-11-22T00:13` and end `2026-11-22T01:43` and reopens it
- **THEN** the start and end fields show `2026-11-22T00:13` and `2026-11-22T01:43`

#### Scenario: Archiving records the local current time
- **WHEN** the user archives a repair
- **THEN** the end datetime sent to the API is the local current wall-clock time, not the UTC time

#### Scenario: Stopping a work-log entry records the local current time
- **WHEN** the user stops an open work-log entry
- **THEN** the end time sent to the API is the local current wall-clock time, not the UTC time
