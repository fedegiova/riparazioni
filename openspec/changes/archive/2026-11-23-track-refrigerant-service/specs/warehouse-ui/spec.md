# Warehouse UI delta

## ADDED Requirements

### Requirement: Distinguish calculated recovery in cylinder history
The cylinder operation-log page SHALL distinguish the measured net addition, total recharge, and calculated recovery for combined operations.

#### Scenario: A new combined operation shows measurement origin
- **WHEN** a user opens the cylinder history for a single-measurement combined operation
- **THEN** the row displays the net added amount, the total recharged amount, and the recovered amount labeled as calculated, alongside the resulting balance
