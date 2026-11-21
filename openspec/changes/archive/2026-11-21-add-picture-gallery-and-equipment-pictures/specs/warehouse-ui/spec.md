# Spec Delta

## ADDED Requirements

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
