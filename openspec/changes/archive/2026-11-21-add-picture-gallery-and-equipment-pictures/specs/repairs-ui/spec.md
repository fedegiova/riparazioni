# Spec Delta

## ADDED Requirements

### Requirement: View a repair's pictures full screen
The repair page SHALL let the user open one of the repair's pictures in the
full-screen picture gallery, and SHALL let the user scroll between that repair's
pictures while it is open.

#### Scenario: Open a repair picture full screen
- **WHEN** the user activates one of the repair's picture thumbnails
- **THEN** that picture is shown full screen

#### Scenario: Scroll between the repair's pictures
- **WHEN** the user requests the next or previous picture while a repair picture is shown full screen
- **THEN** the viewer shows the next or previous picture of that repair
