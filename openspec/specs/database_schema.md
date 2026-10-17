# Database tables owned by the application


## Repair work log

```sql
CREATE TABLE REPAIR_WORK_LOG(
ID          INT IDENTITY(1,1),
ID_REPAIRS  INT NOT NULL,
START_TIME  DATETIME,
END_TIME    DATETIME,
OPERATOR    CHAR(32),
GAS_RECHARGE INT,
GAS_RECHARGE_WEIGHT FLOAT,
CONSTRAIN  FK_WORKLOG_REPAIRS foreign key ("ID_REPAIRS") references REPAIRS("ID"),
CONSTRAIN  FK_WORKLOG_RECHARGE foreign key ("GAS_RECHARGE") references GAS_CYLINDER("ID"),
)

```

## Repair common data

```sql
CREATE TABLE REPAIRS(
ID          INT IDENTITY(1,1),
CUSTOMER    INT,
VEHICLE     INT,
START_DATA  DATETIME,
NOTES       VARCHAR,
REFRIGERATOR INT,
CONSTRAIN  FK_REPAIRS_CUSTOMER foreign key ("CUSTOMER") references VICLIENTI("ID"),
CONSTRAIN  FK_REPAIRS_VEHICLE foreign key ("VEHICLE") references TBALLESTIMENTI("INT_ID"),
CONSTRAIN  FK_REPAIRS_REFRIGERATOR foreign key ("REFRIGERATOR") references REFRIGERATORS("ID"),
)

```


## Refrigerator data

```sql
CREATE TABLE REFRIGERATORS(
ID          INT IDENTITY(1,1),
SERIAL_NR   CHAR(32), 
MODEL       CHAR(32), 
BRAND       CHAR(32), 
GAS_KG      FLOAT,
NOTES       VARCHAR,
)

```

## Gas cylinder data

```sql
CREATE TABLE GAS_CYLINDERS(
ID          INT IDENTITY(1,1),
GAS_KIND    CHAR(32), 
SERIAL_NR   CHAR(32), 
MODEL       CHAR(32), 
FULL_WEIGHT      FLOAT,
REMAINING_WEIGHT      FLOAT,
PICTURE_REF    INT,
NOTES       VARCHAR,
CONSTRAIN  FK_GAS_PICTURE foreign key ("PICTURE_REF") references PICTURES("ID"),
)

```
## Service Part data

```sql
CREATE TABLE SERVICE_PARTS(
ID          INT IDENTITY(1,1),
NAME    CHAR(64), 
SUPPLIER   CHAR(64), 
KIND      CHAR(64), 
PRICE     INT,
IS_REFRIGERATOR_PART BOOL,
PICTURE_REF    INT,
NOTES       VARCHAR,
CONSTRAIN  FK_SERVICE_PART_PICTURE foreign key ("PICTURE_REF") references PICTURES("ID"),
)

```

## Pictures ref data

```sql
CREATE TABLE PICTURES(
ID          INT IDENTITY(1,1),
PATH        CHAR(1024), 
UPLOADED_BY CHAR(64), 
UPLOADED_DATE DATETIME,
)

```


------------------------------------RIPA FRIGO 
1 numero 
2 ora e data inizio ( quando si crea la riparazioni )
3 ora e data fine ( quando si termina la riparazione )
4 cliente -> ( dalla tabella clienti )
5 targa veicolo -> ( dalla tabella veicoli)
6 frigo ->(dalla tabella frigo)

6 check toggle box -> (impianto vuoto , pieno , ricarica) ;
    impanto vuoto -> compare un casella con il kg di gas ricaricato
    impianto pieno -> niente 
    recupero e Ricarica  -> compaiono 2 casella con il kg di gas recuperato e ricaricato 
    NOTA: quando si carica del gas bisogna selezionare la bombola che si sta usando e aggiornare il suo saldo

7 ricambi frigo  -> (dalla tabella ricambi frigo )
8 note->
9 cartella ->( link alla cartella RIPA)

------------------------------------RIPA 
1 numero 
2 ora e data inizio ( quando si crea la riparazioni )
3 ora e data fine ( quando si termina la riparazione )
4 cliente -> ( dalla tabella clienti )
5 targa veicolo -> ( dalla tabella veicoli)
6 frigo ->(dalla tabella frigo)
7 ricambi   -> (dalla tabella ricambi  )
8 note->
9 cartella ->( link alla cartella RIPA per le foto )

