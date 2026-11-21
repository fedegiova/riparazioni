# Tasks

## 1. Implement the Anagrafica page

- [x] 1.1 Replace the placeholder in `frontend/src/pages/AnagraficaPage.tsx` with a tabbed page using MUI `Tabs`/`Tab` (Clienti and Allestimenti, Clienti selected by default), following the `MagazzinoPage` pattern; verify with a new `frontend/src/pages/AnagraficaPage.test.tsx` that both tabs render and Clienti is selected.
- [x] 1.2 Build the Clienti tab: load `listCustomers()` through `useApi` and render a read-only table (columns `cliente`, `via`, `cap`, `citta`, `prov`, `tel`, `cell`, `email`) with loading, error, and empty states; verify the test shows a customer's name and shows the error message when the load rejects (mock `../api/reference`).
- [x] 1.3 Build the Allestimenti tab: load `listVehicles()` through `useApi` and render a read-only table (columns `targa`, `autocarro`, `carrozzeria`, `modello`, `classe`, `commessa`) with loading, error, and empty states; verify the test shows a vehicle's `targa` after switching tabs and shows the error message when the load rejects.
- [x] 1.4 Add a single search box to each tab that filters the displayed rows to those whose visible fields contain the query (case-insensitive) and shows all rows when the query is empty; verify the test narrows the list on a matching query, restores all rows when cleared, and shows no rows when nothing matches.
- [x] 1.5 Ensure the page is read-only: import no write helpers and render no create/edit/delete controls; verify the test asserts no such controls are present on either tab.
- [x] 1.6 Run `npm test` for `AnagraficaPage.test.tsx` and verify every scenario in `specs/anagrafica-ui/spec.md` (tabs, both lists, both error states, per-tab search, read-only) is covered and passing.

## 2. Integration checks

- [x] 2.1 Run the frontend `lint`, `build` (type check), and full `test` scripts; verify all pass with the new page.
- [x] 2.2 Manually verify `/anagrafica` against a running backend: the Clienti and Allestimenti lists load, switching tabs works, the per-tab search box filters the rows, and no write controls are shown.
