# Spec Delta

## MODIFIED Requirements

### Requirement: Gas recharge operations
When a work-log entry carries gas data, the system SHALL require a gas system
state (VUOTO, PIENO, RECUPERO, or RICUPERO_RICARICA). The system SHALL apply
each gas movement to the cylinder referenced by the entry in the same
transaction, storing recharged and recovered weights as independent values: a
recharged weight SHALL decrease the cylinder's remaining weight and a recovered
weight SHALL increase it. A recharge SHALL require a cylinder and a positive
recharged weight; a recovery SHALL require a cylinder and a non-negative
recovered weight; PIENO SHALL carry no cylinder or weights. A movement taking
the balance below zero or above the cylinder's full weight SHALL be rejected.

#### Scenario: Recharge decreases cylinder balance
- **WHEN** a work-log entry is created with state VUOTO, recharged weight 2.5, and a cylinder whose remaining weight is 10.0
- **THEN** the entry stores the cylinder reference and weight, and the cylinder's remaining weight becomes 7.5

#### Scenario: Full system stores no gas data
- **WHEN** a work-log entry is created with state PIENO
- **THEN** the entry is stored without cylinder reference or weights

#### Scenario: Recovered weight is stored
- **WHEN** a work-log entry is created with state RECUPERO and recovered weight 1.0 against a cylinder whose remaining weight is 4.0
- **THEN** the entry stores the recovered weight and the cylinder's remaining weight becomes 5.0

#### Scenario: Recover and recharge apply independently
- **WHEN** a work-log entry is created with state RICUPERO_RICARICA, recovered weight 1.0 and recharged weight 2.5 against a cylinder whose remaining weight is 10.0
- **THEN** the entry stores both weights and the cylinder's remaining weight becomes 8.5

#### Scenario: Gas data without a state is rejected
- **WHEN** a work-log entry is created with a gas recharge but no gas system state
- **THEN** the system responds with HTTP 400 and no entry is created

#### Scenario: Overdraw is rejected
- **WHEN** a recharge of 12.0 is recorded against a cylinder whose remaining weight is 10.0
- **THEN** the system responds with HTTP 400, no entry is created, and the cylinder balance is unchanged

#### Scenario: Overfill is rejected
- **WHEN** a recovery would raise the cylinder's remaining weight above its full weight
- **THEN** the system responds with HTTP 400, no entry is created, and the cylinder balance is unchanged

#### Scenario: Recharge without cylinder is rejected
- **WHEN** a gas recharge is recorded without a cylinder reference
- **THEN** the system responds with HTTP 400

### Requirement: Deleting a recharge entry restores the balance
Deleting a work-log entry that recorded gas movements SHALL reverse them in the
same transaction: the cylinder's remaining weight SHALL increase by the
recharged weight and decrease by the recovered weight.

#### Scenario: Balance is restored on delete
- **WHEN** a work-log entry that recharged 2.5 and recovered 1.0 from a cylinder is deleted
- **THEN** the cylinder's remaining weight has increased by 1.5

## ADDED Requirements

### Requirement: Report gas used per repair
The system SHALL report, for a repair, the total recharged gas weight as the
sum of the recharged weights recorded on its work-log entries.

#### Scenario: Gas total sums recharges
- **WHEN** a repair has work-log entries recharging 2.5 and 1.0
- **THEN** the repair's reported gas used is 3.5

#### Scenario: No gas records
- **WHEN** a repair has no work-log entry carrying a recharged weight
- **THEN** the repair's reported gas used is 0
