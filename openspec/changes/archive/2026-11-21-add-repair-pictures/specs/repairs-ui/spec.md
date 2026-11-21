# Spec Delta

## ADDED Requirements

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
