# pictures Specification

## Purpose

Stores repair photos on the local filesystem with metadata in the
database and serves them through the API, for use by gas cylinders and
service parts.

## Requirements

### Requirement: Upload a picture
The system SHALL accept a multipart file upload, store the file under the
configured uploads directory in a `pictures` subfolder under a
system-generated unique name (preserving the original extension), and
record the relative path, uploader, and upload date in the picture
record.

#### Scenario: Successful upload
- **WHEN** a client POSTs a multipart form with a file field to /api/v1/pictures
- **THEN** the system responds with HTTP 201 with the picture metadata (id, path, uploader, date) and the file exists on the filesystem

#### Scenario: Missing file is rejected
- **WHEN** a client POSTs to /api/v1/pictures without a file
- **THEN** the system responds with HTTP 400 and no picture record is created

### Requirement: List and retrieve pictures
The system SHALL return a list of pictures and a single picture's
metadata by ID.

#### Scenario: Picture detail
- **WHEN** a client GETs /api/v1/pictures/<id> for an existing picture
- **THEN** the system responds with HTTP 200 with the metadata

#### Scenario: Unknown picture
- **WHEN** a client GETs /api/v1/pictures/<id> with a non-existent ID
- **THEN** the system responds with HTTP 404

### Requirement: Download a picture
The system SHALL serve the stored file of a picture with an appropriate
content type, resolving the file location only from the stored metadata
and never from client-supplied paths.

#### Scenario: Download a stored picture
- **WHEN** a client GETs /api/v1/pictures/<id>/file for a picture whose file exists
- **THEN** the system responds with HTTP 200 with the file's bytes and a content type matching the file extension

#### Scenario: Missing file on disk
- **WHEN** a picture record exists but its file is missing from the uploads directory
- **THEN** the system responds with HTTP 404

### Requirement: Delete a picture
The system SHALL allow deleting a picture, removing both the database
record and the stored file.

#### Scenario: Delete a picture removes the file
- **WHEN** a client DELETEs an unreferenced picture
- **THEN** the system responds with HTTP 204 and both the record and the file are gone

#### Scenario: Delete a referenced picture
- **WHEN** a client DELETEs a picture referenced by a gas cylinder or service part
- **THEN** the system responds with HTTP 409 and the picture is not deleted
