# Anagrafica UI delta

## MODIFIED Requirements

### Requirement: Anagrafica data is read-only
The Anagrafica page SHALL present legacy customer and allestimento fields without controls to create, edit, or delete the legacy records. Controls that manage the app-owned refrigerator on an Allestimenti row SHALL NOT modify legacy fields.

#### Scenario: No write controls are offered
- **WHEN** the user views either the Clienti or the Allestimenti tab
- **THEN** the page shows no control to create, edit, or delete the underlying customer or allestimento records

## ADDED Requirements

### Requirement: Manage installed refrigerators in Anagrafica
The Allestimenti tab SHALL identify each vehicle's installed refrigerator or indicate that none is installed. It SHALL offer controls to create, edit, and explicitly replace a refrigerator, with fields for serial number, manufacturer, model, gas type from Settings, and nameplate capacity in kg.

#### Scenario: Register a refrigerator from the vehicle row
- **WHEN** the user opens Add refrigerator for an allestimento with no installed unit and saves valid details
- **THEN** the row shows the newly installed unit and the legacy vehicle fields stay unchanged

#### Scenario: Edit or replace an installed refrigerator
- **WHEN** the user edits the refrigerator details or explicitly installs a replacement
- **THEN** the row shows the saved details or replacement, and replacing the unit does not rewrite the old refrigerator record

#### Scenario: Installation save is rejected
- **WHEN** the server rejects a refrigerator save
- **THEN** Anagrafica reports the error and does not display an unsaved installation as current
