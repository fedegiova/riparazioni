-- Prebaked dev seed data for the DATIDBSTORICO external tables.
--
-- Derived from the legacy sample in clienti.sql (MSSQL dialect), adapted to
-- SQLite: 3-part names reduced to DATIDBSTORICO.<table>, GO separators and
-- {d '...'} date literals removed, trailing CHAR padding stripped,
-- whitespace-only values written as NULL.
--
-- This file is INSERT-only: `flask dev-init` creates the tables from the
-- models (app/models/external.py). To use your own reference data, edit
-- this file or point DEV_SEED_SQL at your own SQL file with the same
-- statement shape, then run `flask dev-init --reset`.
--
-- Prebaked rows (ids kept from the sample so seeded repairs reference
-- recognizable values):
--   customer: id 9  ("PP.", Sassuolo)
--   vehicle:  id 12363 (IVECO 130E18, targa 417023)
--   user:     id 21  ("LORENZA")

INSERT INTO DATIDBSTORICO.VICLIENTI
    (ID, N_NOMINATIVO, CLIENTE, NCLIENTE, VIA, CAP, CITTA, PROV, TEL, FAX, CELL, EMAIL, NOTE)
VALUES
    (9, 9, 'PP.', '000000000000009', 'Via Montanara', '41049', 'SASSUOLO', 'MO',
     '0536', '0536 PIZZER', NULL, NULL, NULL);

INSERT INTO DATIDBSTORICO.TBALLESTIMENTI
    (ID_INT, ID, NOMINATIVO_ID, TARGA, AUTOCARRO, CARROZZERIA, MODELLO, CLASSE,
     COMMESSA, PROD, ATP, PROGRESSIVO, DATA_RILASCIO, OL, NOTE, CPCCCHK)
VALUES
    (12363, '000000000000009', '000000000008404', '417023', 'IVECO 130E18', 'GIO',
     '79B001', 'FRC', '10-2003', '2003-09-01', NULL, NULL, NULL,
     'LG/D 3186', 'FATTO NEL 2003', '.');

INSERT INTO DATIDBSTORICO.TBUSERS
    (ID_INT, ID, NAME, PASSWORD, LAST_LOGIN)
VALUES
    (21, '000000000000021', 'LORENZA',
     '80c352d256044230901b96077ec8e68aec731cde', NULL);
