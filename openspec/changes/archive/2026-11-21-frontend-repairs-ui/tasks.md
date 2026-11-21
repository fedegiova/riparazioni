# Tasks

## 1. Prerequisite and shell

- [x] 1.1 After the backend change lands, regenerate the committed API client and verify `npm run build` type-checks against `delivery_date`, `total_hours`, `customer_name`, and the export endpoint
- [x] 1.2 Add the route map and page scaffolding (landing, repairs list, repair new/edit, work-log editor, Magazzino/Anagrafica placeholders) and verify each route renders
- [x] 1.3 Add the breadcrumb bar, the app-bar home control, and the bottom navigation, and verify a test covers section switching and returning to the landing
- [x] 1.4 Update `frontend/README.md` (layout / pages) to match the new screens and verify the documented commands still run

## 2. Shared components

- [x] 2.1 Add the reusable search-modal component and verify a test filters its list and returns a selection
- [x] 2.2 Add the small data-loading hook over the shared client and verify a test covers the success and `ApiError` states

## 3. Landing page

- [x] 3.1 Build the active-repairs table (Customer, Total hours, End date) with a per-row open control and a create control, and verify a test shows only repairs without an end date and navigates on open

## 4. Repairs list page

- [x] 4.1 Build the full repairs list with filters and verify a test includes completed repairs and narrows the list when a filter is applied
- [x] 4.2 Add per-row delete behind a confirmation and verify tests cover both confirming and cancelling
- [x] 4.3 Add the Export XLSX control and verify a test requests the export endpoint with the currently applied filter

## 5. Repair page

- [x] 5.1 Build the field form with customer and vehicle search modals plus start date, delivery date, and notes, and verify tests for creating and editing a repair
- [x] 5.2 Build the Parts table with add and delete, and verify tests that save the full parts array
- [x] 5.3 Build the work-log table with cancel, open-for-edit, and add controls, and verify tests for each
- [x] 5.4 Add the archive control and verify a test that archiving sets the repair's end date

## 6. Work-log editor page

- [x] 6.1 Build the start time, end time, and operator editing plus gas-recharge capture, and verify tests for both

## 7. Integration

- [x] 7.1 Run `npm run lint`, `npm run build`, and `npm test` and verify they pass against the regenerated client

## 8. Follow-up UI refinements

- [x] 8.1 Prefill the current date/time on the new-repair and new-work-log pages and verify tests cover both prefills
- [x] 8.2 Add a stop action to the repair page's work-log rows that sets the entry's end time, and verify a test covers it
- [x] 8.3 Add a start-work-log shortcut to the landing page's active-repair rows and verify a test covers the navigation
- [x] 8.4 Run `npm run lint`, `npm run build`, and `npm test` and verify they pass
