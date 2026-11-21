# picture-gallery Specification

## Purpose

A reusable full-screen viewer for pictures so a user can inspect one photo at a
readable size and move between the photos of the current record.

## Requirements

### Requirement: Display a picture full screen
The application SHALL display a picture at full screen size, over the current
screen, when the user activates it from a collection of pictures, and SHALL
provide a control that closes the viewer and returns to the collection.

#### Scenario: Open a picture full screen
- **WHEN** the user activates a picture in a collection
- **THEN** the picture is shown full screen and the underlying collection is covered

#### Scenario: Close the viewer
- **WHEN** the user activates the close control while a picture is shown full screen
- **THEN** the viewer closes and the collection is shown again

#### Scenario: Full-size picture is shown
- **WHEN** a picture is shown full screen
- **THEN** the viewer loads the picture's full stored image, not its minified view

### Requirement: Zoom and pan a picture
While a picture is displayed full screen, the application SHALL let the user
zoom it in and out and pan it while zoomed, on both touch and pointer devices.

#### Scenario: Zoom with a pinch
- **WHEN** the user pinches out on the full-screen picture
- **THEN** the picture zooms in, and pinching in zooms it back out

#### Scenario: Zoom with a double tap or double click
- **WHEN** the user double-taps or double-clicks the full-screen picture
- **THEN** the picture zooms in, and repeating it zooms further up to a maximum

#### Scenario: Zoom past native resolution
- **WHEN** the user zooms in on a picture displayed smaller than its stored size
- **THEN** the picture can be magnified up to three times its native resolution

#### Scenario: Pan a zoomed picture
- **WHEN** the picture is zoomed in and the user drags it
- **THEN** the visible area moves with the drag

### Requirement: Scroll between pictures
While a picture is displayed full screen, the application SHALL let the user
move to the previous and next picture within the same collection, and SHALL NOT
wrap around at either end.

#### Scenario: Show the next picture
- **WHEN** the user requests the next picture and a later picture exists
- **THEN** the later picture is shown full screen

#### Scenario: Show the previous picture
- **WHEN** the user requests the previous picture and an earlier picture exists
- **THEN** the earlier picture is shown full screen

#### Scenario: Navigate with the keyboard
- **WHEN** the user presses the left or right arrow key while the viewer is open
- **THEN** the viewer shows the previous or next picture respectively

#### Scenario: Navigate with a swipe
- **WHEN** the user swipes horizontally on the full-screen picture
- **THEN** the viewer moves to the adjacent picture in the swipe direction

#### Scenario: No wrap at the ends
- **WHEN** the first or last picture of the collection is shown
- **THEN** the control toward the outside of the collection is disabled and no wrap occurs
