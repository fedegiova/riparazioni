# Repairs UI delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Show the repair's gas-work lock
The repair page SHALL identify the refrigerator locked to the repair and SHALL prevent changing the associated vehicle after the gas-work lock is set.

#### Scenario: A locked repair shows its recorded unit
- **WHEN** the user opens a repair locked to a refrigerator that has since been replaced on the allestimento
- **THEN** the repair shows the recorded refrigerator, not the replacement, and the vehicle selector cannot reassign the repair
