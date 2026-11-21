# Spec Delta

## MODIFIED Requirements

### Requirement: Upload a picture
The system SHALL accept a multipart file upload that carries an owner type
(`repair`, `spare`, or `cylinder`) and an owner id, store the file under the
configured uploads directory in a folder named for the owner type as
`YYYY-MM-DD-SEQ` (a sequence per owner type and day, preserving the original
extension), and record the relative path, owner, uploader, and upload date in
the picture record.

#### Scenario: Successful upload
- **WHEN** a client POSTs a multipart form with a file field, `owner_type=repair`, and the id of an existing repair to /api/v1/pictures
- **THEN** the system responds with HTTP 201 with the picture metadata (id, path, owner, uploader, date) and the file exists under the uploads directory in the `repair` folder named `YYYY-MM-DD-SEQ` with the original extension

#### Scenario: Sequence increments per type and day
- **WHEN** two pictures of the same owner type are uploaded on the same day
- **THEN** the two stored names carry consecutive sequence numbers, and a picture of a different owner type gets its own sequence

#### Scenario: Missing file is rejected
- **WHEN** a client POSTs to /api/v1/pictures without a file
- **THEN** the system responds with HTTP 400 and no picture record is created

#### Scenario: Camera upload without a filename
- **WHEN** a client POSTs a multipart form whose file part has an empty filename (some device cameras send this)
- **THEN** the system responds with HTTP 201 and stores the file with an extension derived from the part's content type

#### Scenario: Missing or invalid owner is rejected
- **WHEN** a client POSTs a file without `owner_type`/`owner_id`, or with an unknown owner type
- **THEN** the system responds with HTTP 400 and no picture record is created

#### Scenario: Unknown owner id is rejected
- **WHEN** a client POSTs a file with an owner type and an id that does not exist for that type
- **THEN** the system responds with HTTP 409 and no picture record is created

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

## ADDED Requirements

### Requirement: List pictures by owner
The system SHALL support listing pictures filtered by owner type and owner id.

#### Scenario: Filter by owner
- **WHEN** a client GETs /api/v1/pictures?owner_type=repair&owner_id=<id>
- **THEN** the response contains only the pictures owned by that repair

#### Scenario: Incomplete owner filter is rejected
- **WHEN** a client GETs /api/v1/pictures with only one of `owner_type` or `owner_id`
- **THEN** the system responds with HTTP 400
