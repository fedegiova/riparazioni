# Proposal

## Why

The frontend is currently only an application shell with placeholder pages.
Workshop operators, working on a tablet in the shop, need real screens to see
the repair queue, open and edit a repair with its work log and parts, and
search or export the full repair history.

## What Changes

- **Shell navigation**: add a home icon to the top app bar, a breadcrumb bar,
  and a bottom navigation with three destinations — **Repairs List**,
  **Magazzino**, and **Anagrafica**. The landing route becomes the active
  repairs overview.
- **Landing page** (default route): a breadcrumb bar, a table of **active**
  repairs (`end_data` empty) with columns **Cliente**, **Total hours**, and
  **End date**; each row links to its Repair page; a `+` button opens a new
  repair.
- **Repairs List page**: a table of **all** repairs (including completed) with
  search/filter, per-row **load** (open for editing) and **delete** (with
  confirmation) actions, and an **Export XLSX** button.
- **Repair page** (new / edit): editable customer and vehicle chosen via
  **search modals**, start date, delivery date, and notes; a **Parts table**
  (add / delete a repair part); a **work-log table** whose rows can be
  cancelled (deleted) or opened for editing, with a button to add a work log;
  and an **Archive** button to close the repair.
- **Work-log page**: start time, end time, operator, and adding a gas recharge.
- A shared **search-modal** component for picking referenced records.

Out of scope for this change: the Magazzino, Anagrafica, and Ricambi screens
(not yet specified); they keep the shell/navigation placeholders only.

## Capabilities

### New Capabilities
- `repairs-ui`: the repairs feature screens — landing (active repairs), repairs
  list with search and export, the repair detail/edit page with its work-log
  and parts tables, and the work-log editor page.

### Modified Capabilities
- `frontend-app`: the application shell gains a home icon, a breadcrumb bar,
  and bottom navigation; the landing route hosts the active-repairs overview
  instead of a placeholder.

## Impact

- Code: `frontend/src/App.tsx` (shell, routes), new pages under
  `frontend/src/pages/`, shared components (breadcrumb, bottom nav, search
  modal), and use of the shared API client.
- Contract dependency: requires the `repairs-api-delivery-and-export` change
  (`delivery_date`, `total_hours`, customer name, XLSX export) to land first,
  then `docs/openapi.yaml` is regenerated into the committed frontend client.
- Out of scope: Magazzino, Anagrafica, and Ricambi screens.
