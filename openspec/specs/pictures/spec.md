# pictures Specification

## Purpose

Stores repair photos on the local filesystem with metadata in the
database and serves them through the API, for use by gas cylinders and
service parts.

## Requirements

### Requirement: Upload a picture
The system SHALL accept a multipart upload carrying an owner type (`repair`,
`spare`, or `cylinder`) and an owner id, decode it as an image, and store a copy
resized so its longest edge is at most 2880 px (aspect ratio and orientation
preserved) as `<owner_type>/YYYY-MM-DD-SEQ.<ext>` under the uploads directory,
with a per-type, per-day sequence and the extension from the decoded format,
recording the path, owner, uploader, and upload date.

#### Scenario: Successful upload
- **WHEN** a client POSTs a multipart form with a file field, `owner_type=repair`, and the id of an existing repair to /api/v1/pictures
- **THEN** the system responds with HTTP 201 with the picture metadata (id, path, owner, uploader, date) and stores the file under the uploads directory in the `repair` folder named `YYYY-MM-DD-SEQ` with the decoded image's extension

#### Scenario: Large image is downscaled
- **WHEN** a client uploads an image whose longest edge exceeds 2880 px
- **THEN** the stored file's longest edge is at most 2880 px and its aspect ratio is preserved

#### Scenario: Small image is not enlarged
- **WHEN** a client uploads an image whose longest edge is at most 2880 px
- **THEN** the stored file keeps the upload's original dimensions

#### Scenario: Sequence increments per type and day
- **WHEN** two pictures of the same owner type are uploaded on the same day
- **THEN** the two stored names carry consecutive sequence numbers, and a picture of a different owner type gets its own sequence

#### Scenario: Missing file is rejected
- **WHEN** a client POSTs to /api/v1/pictures without a file
- **THEN** the system responds with HTTP 400 and no picture record is created

#### Scenario: Camera upload without a filename
- **WHEN** a client POSTs a multipart form whose file part has an empty filename (some device cameras send this)
- **THEN** the system responds with HTTP 201 and stores the file with an extension derived from the decoded image's format

#### Scenario: Missing or invalid owner is rejected
- **WHEN** a client POSTs a file without `owner_type`/`owner_id`, or with an unknown owner type
- **THEN** the system responds with HTTP 400 and no picture record is created

#### Scenario: Unknown owner id is rejected
- **WHEN** a client POSTs a file with an owner type and an id that does not exist for that type
- **THEN** the system responds with HTTP 409 and no picture record is created

### Requirement: Reject a non-image upload
The system SHALL reject an upload whose file the server cannot decode as an image
with HTTP 400, creating no picture record and storing no file.

#### Scenario: Non-image upload is rejected
- **WHEN** a client POSTs a multipart form whose file is not a decodable image
- **THEN** the system responds with HTTP 400 and creates neither a picture record nor a stored file

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

### Requirement: Serve a minified view
The system SHALL store, alongside each picture, a minified derivative whose
longest edge is at most 320 px, and SHALL serve it at
`GET /api/v1/pictures/<id>/thumbnail` for fast display in picture grids.

#### Scenario: Minified view is created on upload
- **WHEN** a client uploads an image
- **THEN** a minified derivative with a longest edge of at most 320 px exists for the new picture and its location is recorded on the picture

#### Scenario: Download the minified view
- **WHEN** a client GETs /api/v1/pictures/<id>/thumbnail for a picture that has a minified derivative
- **THEN** the system responds with HTTP 200 with the derivative's bytes and an image content type

#### Scenario: Legacy picture gets its minified view lazily
- **WHEN** a client GETs /api/v1/pictures/<id>/thumbnail for a picture stored before this change and no derivative exists yet
- **THEN** the system derives the minified view from the stored file, records it, and responds with HTTP 200

#### Scenario: Unknown picture has no minified view
- **WHEN** a client GETs /api/v1/pictures/<id>/thumbnail with a non-existent ID
- **THEN** the system responds with HTTP 404

### Requirement: Delete a picture
The system SHALL allow deleting a picture, removing both the database record
and the stored file. A picture belongs to exactly one owner, so deleting it is
never blocked by a reference.

#### Scenario: Delete a picture removes the file
- **WHEN** a client DELETEs an unreferenced picture
- **THEN** the system responds with HTTP 204 and both the record and the file are gone

#### Scenario: Delete a referenced picture
- **WHEN** a client DELETEs a picture attached to a gas cylinder or service part
- **THEN** the system responds with HTTP 204 and both the record and the file are gone

### Requirement: List pictures by owner
The system SHALL support listing pictures filtered by owner type and owner id.

#### Scenario: Filter by owner
- **WHEN** a client GETs /api/v1/pictures?owner_type=repair&owner_id=<id>
- **THEN** the response contains only the pictures owned by that repair

#### Scenario: Incomplete owner filter is rejected
- **WHEN** a client GETs /api/v1/pictures with only one of `owner_type` or `owner_id`
- **THEN** the system responds with HTTP 400
