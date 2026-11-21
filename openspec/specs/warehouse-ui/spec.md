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

### Requirement: Manage spare-part pictures
The warehouse page SHALL let the user capture, list, and delete the pictures of a
spare part, both from a per-row Pictures dialog on the parts list and from the
part's New/Edit dialog. Capturing SHALL open the device camera directly without
asking the user for a file name, and the pictures SHALL be loaded on demand for
the part being viewed.

#### Scenario: Capture a spare-part picture from the row dialog
- **WHEN** the user opens a part's Pictures dialog, activates the capture control, and takes or chooses a photo
- **THEN** the photo is uploaded for that part and appears in the dialog's pictures list

#### Scenario: No file name is requested
- **WHEN** the user activates the capture control for a spare part
- **THEN** the device camera is opened directly and the user is not asked to name the file

#### Scenario: Spare-part pictures are shown as thumbnails
- **WHEN** the user opens the Pictures dialog of a part that has pictures
- **THEN** the dialog shows the part's pictures as thumbnails

#### Scenario: Delete a spare-part picture
- **WHEN** the user deletes a picture from a part's pictures
- **THEN** it is removed from the list and no longer stored for that part

#### Scenario: Manage pictures from the edit dialog
- **WHEN** the user opens an existing part for editing
- **THEN** the edit dialog shows a Pictures area that lists, adds, and deletes that part's pictures

#### Scenario: A new part has no pictures until saved
- **WHEN** the user is creating a new part that has not been saved yet
- **THEN** no picture controls are offered until the part exists

### Requirement: Manage gas-cylinder pictures
The warehouse page SHALL let the user capture, list, and delete the pictures of a
gas cylinder, both from a per-row Pictures dialog on the cylinder list and from
the cylinder's New/Edit dialog. Capturing SHALL open the device camera directly
without asking the user for a file name, and the pictures SHALL be loaded on
demand for the cylinder being viewed.

#### Scenario: Capture a cylinder picture from the row dialog
- **WHEN** the user opens a cylinder's Pictures dialog, activates the capture control, and takes or chooses a photo
- **THEN** the photo is uploaded for that cylinder and appears in the dialog's pictures list

#### Scenario: Cylinder pictures are shown as thumbnails
- **WHEN** the user opens the Pictures dialog of a cylinder that has pictures
- **THEN** the dialog shows the cylinder's pictures as thumbnails

#### Scenario: Delete a cylinder picture
- **WHEN** the user deletes a picture from a cylinder's pictures
- **THEN** it is removed from the list and no longer stored for that cylinder

#### Scenario: Manage pictures from the edit dialog
- **WHEN** the user opens an existing cylinder for editing
- **THEN** the edit dialog shows a Pictures area that lists, adds, and deletes that cylinder's pictures

#### Scenario: A new cylinder has no pictures until saved
- **WHEN** the user is creating a new cylinder that has not been saved yet
- **THEN** no picture controls are offered until the cylinder exists

### Requirement: View equipment pictures full screen
The warehouse page SHALL let the user open a spare part's or gas cylinder's
picture in the full-screen picture gallery, and SHALL let the user scroll between
that record's pictures while it is open.

#### Scenario: Open an equipment picture full screen
- **WHEN** the user activates a spare-part or cylinder picture thumbnail
- **THEN** that picture is shown full screen

#### Scenario: Scroll between a record's pictures
- **WHEN** the user requests the next or previous picture while a spare-part or cylinder picture is shown full screen
- **THEN** the viewer shows the next or previous picture of that record

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
