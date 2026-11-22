# Repairs delta

## MODIFIED Requirements

### Requirement: Update a repair
The system SHALL allow updating a repair's customer, vehicle, refrigerator, notes, delivery date, and end datetime, subject to the gas-work refrigerator lock. Setting the end datetime on an active repair SHALL archive it and save the adjusted total in the same transaction, unless a running timer blocks archiving. Clearing the end datetime SHALL reopen the repair and restore live calculation. Updating an already-archived repair without reopening it SHALL NOT recalculate the frozen total.

#### Scenario: Complete a repair
- **WHEN** a client updates an active repair with an end datetime and no timers are running on it
- **THEN** the system responds with HTTP 200, saves the end datetime and adjusted total, and returns the saved total in `total_hours`

#### Scenario: Running timers prevent archiving
- **WHEN** a client sets an end datetime on an active repair with a work log that has a start time and no end time
- **THEN** the system responds with HTTP 409, identifies the blocking timers and their operators where known, and leaves the repair and its logs unchanged

#### Scenario: Reopen a completed repair
- **WHEN** a client updates a completed repair with a null end datetime
- **THEN** the end datetime is cleared and `total_hours` is once again calculated from the current calendar and work logs

#### Scenario: Re-archive a reopened repair
- **WHEN** a client archives a reopened repair after its running timers have been stopped
- **THEN** the system freezes a new total using the calendar and logs in effect at that archive

#### Scenario: Change the requested delivery date
- **WHEN** a client updates a repair's delivery date
- **THEN** the change is stored and the system responds with HTTP 200

#### Scenario: Locked equipment cannot be reassigned
- **WHEN** a client tries to change or clear the vehicle or refrigerator on a repair locked by gas work
- **THEN** the system responds with HTTP 409 and leaves the repair unchanged

## ADDED Requirements

### Requirement: Record gas operations on work logs
Gas work SHALL use `none`, `fill`, `recovery`, or `recovery_recharge`. A missing operation SHALL record or display ordinary work when no gas data is supplied. Gas movement SHALL require one cylinder with a gas type matching the refrigerator and one finite measured amount in kg. The work log, repair lock, and cylinder movement SHALL be saved atomically; a resulting balance outside zero through cylinder capacity SHALL be rejected.

#### Scenario: None is ordinary work
- **WHEN** a client creates a work log with no gas data or explicitly selects `none` without any cylinder or weights
- **THEN** it is saved without a gas movement and without requiring an allestimento or refrigerator

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a client records `fill` using a matching cylinder with enough stock and a positive amount at or below nameplate capacity
- **THEN** the entered weight is saved, reported as recharged weight, and subtracted from the cylinder

#### Scenario: Recovered weight is stored
- **WHEN** a client records `recovery` with a matching cylinder and a non-negative measured recovered weight that fits in the cylinder
- **THEN** the measured weight is stored and added to the cylinder balance

#### Scenario: Combined work uses one net measurement
- **WHEN** a client records `recovery_recharge` with a 3.0 kg nameplate and a measured net addition of 0.4 kg from a matching cylinder with 10.0 kg remaining
- **THEN** the system saves the 3.0 kg capacity used and the 0.4 kg measured net addition, reports 3.0 kg recharged and 2.6 kg calculated recovered, and leaves 9.6 kg in the cylinder

#### Scenario: Combined amount can be zero or equal to capacity
- **WHEN** a client explicitly records zero or the full nameplate capacity as net added, and the cylinder balance permits the movement
- **THEN** zero is accepted as no fresh gas used, and the full nameplate amount is accepted as zero calculated recovery

#### Scenario: Reject invalid gas inputs
- **WHEN** a gas write has an unknown or missing operation, incompatible fields, a missing cylinder or required measurement, a missing or mismatched gas type, a fill above nameplate capacity, a combined net addition outside zero through capacity, or a movement outside cylinder balance bounds
- **THEN** the write fails without changing the work log, repair lock, cylinder balance, or any running timer

#### Scenario: Gas data without an operation is rejected
- **WHEN** a client supplies gas movement data without `gas_operation`
- **THEN** the system responds with HTTP 400 and does not save a movement

#### Scenario: Overdraw is rejected
- **WHEN** a fill or combined operation needs more gas than the cylinder has available
- **THEN** the system responds with HTTP 400 without changing the cylinder or saving the movement

#### Scenario: Overfill is rejected
- **WHEN** a recovery would take the cylinder balance above its full weight
- **THEN** the system responds with HTTP 400 without changing the cylinder or saving the movement

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a fill or combined operation has no cylinder reference
- **THEN** the system responds with HTTP 400 without saving the movement

#### Scenario: Edit or clear gas on an active work log
- **WHEN** a client successfully replaces the gas dataset or explicitly changes the operation to `none`
- **THEN** the system reverses the old stored movement and applies the replacement, if any, in the same transaction; omitting gas fields on update leaves them unchanged

#### Scenario: Existing ordinary work needs no conversion
- **WHEN** a work log without a recorded operation is read or edited without adding gas work
- **THEN** it is treated as ordinary work without requiring a refrigerator or generating a cylinder movement

### Requirement: Bind gas work to the installed refrigerator
New or changed gas work SHALL require an existing repair allestimento with a valid installed refrigerator. The first successful gas operation SHALL lock that unit to the repair. Later gas work on the repair SHALL use the locked unit only while it is still installed on that allestimento. Replacing the unit SHALL NOT alter the repair's recorded refrigerator or existing gas movements.

#### Scenario: First gas operation binds the installed unit
- **WHEN** a repair that is not yet locked records its first valid gas operation
- **THEN** the system resolves and locks the refrigerator installed at save time and returns its identity with the repair

#### Scenario: No installed unit blocks only gas work
- **WHEN** a client attempts a gas operation for a repair with no allestimento or no installed unit
- **THEN** the system rejects the gas write with an explanation, and an ordinary work log remains allowed

#### Scenario: Replacement after gas work requires a separate repair
- **WHEN** a different refrigerator is installed after the repair was locked and a client attempts to record further gas work on that repair
- **THEN** the system rejects the gas work and points to a separate repair for the replacement unit; the prior logs and lock are unchanged

#### Scenario: Historical calculation does not follow nameplate edits
- **WHEN** the nameplate capacity is edited after a combined operation was saved
- **THEN** reading, editing unrelated work-log fields, or reversing that operation uses the original recorded values, not the new capacity

## REMOVED Requirements

### Requirement: Gas recharge operations
**Reason**: Explicit gas operations replace the old gas-state and dual-measurement model.
**Migration**: Use `gas_operation` for gas work. No legacy gas entries or state values are converted.
