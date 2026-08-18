import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime


# ============================================================
# DATABASE PATH
# ============================================================

DB_PATH = os.path.join(
    "database",
    "collateral.db",
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _connect():
    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE CONTEXT MANAGER
# ============================================================

@contextmanager
def db():

    conn = _connect()

    try:

        yield conn

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# INITIALIZE INPUT DATABASE
# ============================================================

def initialize_input_database():
    """
    Create the master/input tables.

    Existing tables are NOT deleted.

    The securities table uses:
        nse_symbol
        isin

    Historical collateral tables are not modified.
    """

    with db() as conn:

        conn.executescript(
            """

            CREATE TABLE IF NOT EXISTS loans (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                borrower TEXT NOT NULL,

                loan_id TEXT NOT NULL UNIQUE,

                loan_start_date TEXT NOT NULL,

                expected_closure_date TEXT,

                sanctioned_amount_cr REAL NOT NULL,

                initial_disbursement_cr REAL DEFAULT 0,

                outstanding_at_onboarding_cr REAL DEFAULT 0,

                required_security_cover REAL NOT NULL,

                loan_status TEXT NOT NULL DEFAULT 'Active'

                    CHECK (
                        loan_status IN (
                            'Active',
                            'Closed'
                        )
                    ),

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS securities (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                loan_id INTEGER NOT NULL,

                listed_company_name TEXT NOT NULL,

                nse_symbol TEXT NOT NULL,

                isin TEXT NOT NULL,

                initial_pledged_shares INTEGER NOT NULL,

                initial_pledge_date TEXT NOT NULL,

                collateralwise_security_cover REAL NOT NULL,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    loan_id
                )
                REFERENCES loans(id)
                ON DELETE CASCADE,

                UNIQUE (
                    loan_id,
                    isin
                )
            );


            CREATE TABLE IF NOT EXISTS additional_collateral (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                loan_id INTEGER NOT NULL,

                collateral_type TEXT NOT NULL

                    CHECK (
                        collateral_type IN (
                            'FD',
                            'MF'
                        )
                    ),

                collateral_amount_cr REAL NOT NULL,

                collateral_date TEXT NOT NULL,

                maturity_release_date TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    loan_id
                )
                REFERENCES loans(id)
                ON DELETE CASCADE
            );


            CREATE TABLE IF NOT EXISTS repayment_schedule (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                loan_id INTEGER NOT NULL,

                repayment_date TEXT NOT NULL,

                repayment_amount_cr REAL NOT NULL,

                remarks TEXT,

                source_file TEXT,

                uploaded_at TEXT NOT NULL,

                FOREIGN KEY (
                    loan_id
                )
                REFERENCES loans(id)
                ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS prepayments (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                loan_id INTEGER NOT NULL,

                prepayment_date TEXT NOT NULL,

                amount_cr REAL NOT NULL,

                remarks TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    loan_id
                )
                REFERENCES loans(id)
                ON DELETE CASCADE
            );


            CREATE TABLE IF NOT EXISTS share_movements_master (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                security_id INTEGER NOT NULL,

                movement_date TEXT NOT NULL,

                movement_type TEXT NOT NULL

                    CHECK (
                        movement_type IN (
                            'Addition',
                            'Release'
                        )
                    ),

                number_of_shares INTEGER NOT NULL

                    CHECK (
                        number_of_shares > 0
                    ),

                remarks TEXT,

                resulting_shares INTEGER NOT NULL,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    security_id
                )
                REFERENCES securities(id)
                ON DELETE CASCADE
            );


            CREATE INDEX IF NOT EXISTS
            idx_loans_borrower
            ON loans(borrower);


            CREATE INDEX IF NOT EXISTS
            idx_securities_loan
            ON securities(loan_id);


            CREATE INDEX IF NOT EXISTS
            idx_collateral_loan
            ON additional_collateral(loan_id);


            CREATE INDEX IF NOT EXISTS
            idx_repayment_loan
            ON repayment_schedule(loan_id);


            CREATE INDEX IF NOT EXISTS
            idx_prepayment_loan
            ON prepayments(loan_id);


            CREATE INDEX IF NOT EXISTS
            idx_share_movement_security
            ON share_movements_master(security_id);

            """
        )


# ============================================================
# LOANS
# ============================================================

def list_loans(
    active_only=False,
):

    initialize_input_database()

    sql = """
        SELECT *
        FROM loans
    """

    if active_only:

        sql += """
            WHERE loan_status = 'Active'
        """

    sql += """
        ORDER BY borrower, loan_id
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql
            ).fetchall()
        ]


def get_loan(
    loan_db_id,
):

    initialize_input_database()

    with db() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM loans
            WHERE id = ?
            """,
            (
                loan_db_id,
            ),
        ).fetchone()

        return (
            dict(row)
            if row
            else None
        )


        # --------------------------------------------------------
        # REPAYMENT SCHEDULE MIGRATION
        # --------------------------------------------------------

        repayment_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(repayment_schedule)"
            ).fetchall()
        }

        if "opening_outstanding_cr" not in repayment_columns:

            conn.execute(
                """
                ALTER TABLE repayment_schedule
                ADD COLUMN opening_outstanding_cr REAL
                """
            )

        if "closing_outstanding_cr" not in repayment_columns:

            conn.execute(
                """
                ALTER TABLE repayment_schedule
                ADD COLUMN closing_outstanding_cr REAL
                """
            )

def create_loan(
    borrower,
    loan_id,
    loan_start_date,
    expected_closure_date,
    sanctioned_amount_cr,
    initial_disbursement_cr,
    outstanding_at_onboarding_cr,
    required_security_cover,
    loan_status,
):

    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        cur = conn.execute(
            """
            INSERT INTO loans (
                borrower,
                loan_id,
                loan_start_date,
                expected_closure_date,
                sanctioned_amount_cr,
                initial_disbursement_cr,
                outstanding_at_onboarding_cr,
                required_security_cover,
                loan_status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                borrower.strip(),
                loan_id.strip(),
                str(loan_start_date),
                (
                    str(expected_closure_date)
                    if expected_closure_date
                    else None
                ),
                float(sanctioned_amount_cr),
                float(initial_disbursement_cr),
                float(
                    outstanding_at_onboarding_cr
                ),
                float(
                    required_security_cover
                ),
                loan_status,
                now,
                now,
            ),
        )

        return cur.lastrowid


# ============================================================
# SECURITIES
# ============================================================

def list_securities(
    loan_db_id=None,
    active_only=True,
):

    initialize_input_database()

    sql = """
        SELECT
            s.*,
            l.borrower,
            l.loan_id AS loan_number
        FROM securities s
        JOIN loans l
            ON l.id = s.loan_id
        WHERE 1=1
    """

    params = []

    if loan_db_id is not None:

        sql += """
            AND s.loan_id = ?
        """

        params.append(
            loan_db_id
        )

    if active_only:

        sql += """
            AND s.active = 1
        """

    sql += """
        ORDER BY
            l.borrower,
            s.listed_company_name
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql,
                params,
            ).fetchall()
        ]


def add_security(
    loan_db_id,
    listed_company_name,
    nse_symbol,
    isin,
    initial_pledged_shares,
    initial_pledge_date,
    collateralwise_security_cover,
):

    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        cur = conn.execute(
            """
            INSERT INTO securities (
                loan_id,
                listed_company_name,
                nse_symbol,
                isin,
                initial_pledged_shares,
                initial_pledge_date,
                collateralwise_security_cover,
                active,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, 1, ?
            )
            """,
            (
                loan_db_id,
                listed_company_name.strip(),
                nse_symbol.strip().upper(),
                isin.strip().upper(),
                int(initial_pledged_shares),
                str(initial_pledge_date),
                float(
                    collateralwise_security_cover
                ),
                now,
            ),
        )

        return cur.lastrowid


# ============================================================
# ADDITIONAL COLLATERAL
# ============================================================

def add_additional_collateral(
    loan_db_id,
    collateral_type,
    collateral_amount_cr,
    collateral_date,
    maturity_release_date,
):

    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        cur = conn.execute(
            """
            INSERT INTO additional_collateral (
                loan_id,
                collateral_type,
                collateral_amount_cr,
                collateral_date,
                maturity_release_date,
                active,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, 1, ?
            )
            """,
            (
                loan_db_id,
                collateral_type,
                float(
                    collateral_amount_cr
                ),
                str(collateral_date),
                (
                    str(maturity_release_date)
                    if maturity_release_date
                    else None
                ),
                now,
            ),
        )

        return cur.lastrowid


def list_additional_collateral(
    loan_db_id=None,
):

    initialize_input_database()

    sql = """
        SELECT
            c.*,
            l.borrower,
            l.loan_id AS loan_number
        FROM additional_collateral c
        JOIN loans l
            ON l.id = c.loan_id
        WHERE c.active = 1
    """

    params = []

    if loan_db_id is not None:

        sql += """
            AND c.loan_id = ?
        """

        params.append(
            loan_db_id
        )

    sql += """
        ORDER BY
            c.collateral_date DESC,
            c.id DESC
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql,
                params,
            ).fetchall()
        ]


# ============================================================
# PREPAYMENTS
# ============================================================

def add_prepayment(
    loan_db_id,
    prepayment_date,
    amount_cr,
    remarks,
):

    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        cur = conn.execute(
            """
            INSERT INTO prepayments (
                loan_id,
                prepayment_date,
                amount_cr,
                remarks,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?
            )
            """,
            (
                loan_db_id,
                str(prepayment_date),
                float(amount_cr),
                remarks.strip(),
                now,
            ),
        )

        return cur.lastrowid


def list_prepayments(
    loan_db_id=None,
):

    initialize_input_database()

    sql = """
        SELECT
            p.*,
            l.borrower,
            l.loan_id AS loan_number
        FROM prepayments p
        JOIN loans l
            ON l.id = p.loan_id
        WHERE 1=1
    """

    params = []

    if loan_db_id is not None:

        sql += """
            AND p.loan_id = ?
        """

        params.append(
            loan_db_id
        )

    sql += """
        ORDER BY
            p.prepayment_date DESC,
            p.id DESC
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql,
                params,
            ).fetchall()
        ]


# ============================================================
# REPAYMENT SCHEDULE
# ============================================================

def add_repayment_rows(
    loan_db_id,
    rows,
    source_file=None,
):
    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    inserted = 0

    with db() as conn:

        # =====================================================
        # REPLACE EXISTING REPAYMENT SCHEDULE
        # =====================================================
        conn.execute(
            """
            DELETE FROM repayment_schedule
            WHERE loan_id = ?
            """,
            (
                loan_db_id,
            ),
        )

        # =====================================================
        # INSERT NEW REPAYMENT SCHEDULE
        # =====================================================
        for row in rows:

            conn.execute(
                """
                INSERT INTO repayment_schedule (
                    loan_id,
                    repayment_date,
                    repayment_amount_cr,
                    remarks,
                    source_file,
                    uploaded_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    loan_db_id,
                    str(
                        row["repayment_date"]
                    ),
                    float(
                        row["repayment_amount_cr"]
                    ),
                    str(
                        row.get(
                            "remarks",
                            "",
                        )
                    ),
                    source_file,
                    now,
                ),
            )

            inserted += 1

    return inserted

def list_repayments(
    loan_db_id=None,
):

    initialize_input_database()

    sql = """
        SELECT
            r.*,
            l.borrower,
            l.loan_id AS loan_number
        FROM repayment_schedule r
        JOIN loans l
            ON l.id = r.loan_id
        WHERE 1=1
    """

    params = []

    if loan_db_id is not None:

        sql += """
            AND r.loan_id = ?
        """

        params.append(
            loan_db_id
        )

    sql += """
        ORDER BY
            r.repayment_date,
            r.id
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql,
                params,
            ).fetchall()
        ]


# ============================================================
# CURRENT SHARE BALANCE
# ============================================================

def get_current_share_balance(
    security_id,
):

    initialize_input_database()

    with db() as conn:

        security = conn.execute(
            """
            SELECT
                initial_pledged_shares
            FROM securities
            WHERE id = ?
            """,
            (
                security_id,
            ),
        ).fetchone()

        if not security:

            raise ValueError(
                "Security not found"
            )

        movement_rows = conn.execute(
            """
            SELECT
                movement_type,
                number_of_shares
            FROM share_movements_master
            WHERE security_id = ?
            ORDER BY
                movement_date,
                id
            """,
            (
                security_id,
            ),
        ).fetchall()

        balance = int(
            security[
                "initial_pledged_shares"
            ]
        )

        for row in movement_rows:

            if row[
                "movement_type"
            ] == "Addition":

                balance += int(
                    row[
                        "number_of_shares"
                    ]
                )

            else:

                balance -= int(
                    row[
                        "number_of_shares"
                    ]
                )

        return balance


# ============================================================
# SHARE MOVEMENT
# ============================================================

def add_share_movement(
    security_id,
    movement_date,
    movement_type,
    number_of_shares,
    remarks,
):

    initialize_input_database()

    number_of_shares = int(
        number_of_shares
    )

    if number_of_shares <= 0:

        raise ValueError(
            "Number of shares must be greater than zero"
        )

    current = get_current_share_balance(
        security_id
    )

    if movement_type == "Addition":

        resulting = (
            current
            + number_of_shares
        )

    elif movement_type == "Release":

        resulting = (
            current
            - number_of_shares
        )

        if resulting < 0:

            raise ValueError(
                "Release cannot exceed current pledged shares"
            )

    else:

        raise ValueError(
            "Movement type must be Addition or Release"
        )

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        cur = conn.execute(
            """
            INSERT INTO share_movements_master (
                security_id,
                movement_date,
                movement_type,
                number_of_shares,
                remarks,
                resulting_shares,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                security_id,
                str(movement_date),
                movement_type,
                number_of_shares,
                remarks.strip(),
                resulting,
                now,
            ),
        )

        return (
            cur.lastrowid,
            resulting,
        )


def list_share_movements(
    security_id=None,
):

    initialize_input_database()

    sql = """
        SELECT
            m.*,
            s.listed_company_name,
            s.nse_symbol,
            s.isin,
            l.borrower,
            l.loan_id AS loan_number
        FROM share_movements_master m
        JOIN securities s
            ON s.id = m.security_id
        JOIN loans l
            ON l.id = s.loan_id
        WHERE 1=1
    """

    params = []

    if security_id is not None:

        sql += """
            AND m.security_id = ?
        """

        params.append(
            security_id
        )

    sql += """
        ORDER BY
            m.movement_date DESC,
            m.id DESC
    """

    with db() as conn:

        return [
            dict(row)
            for row in conn.execute(
                sql,
                params,
            ).fetchall()
        ]


# ============================================================
# EDIT EXISTING LOAN
# ============================================================

def update_loan(
    loan_db_id,
    borrower,
    loan_id,
    loan_start_date,
    expected_closure_date,
    sanctioned_amount_cr,
    initial_disbursement_cr,
    outstanding_at_onboarding_cr,
    required_security_cover,
    loan_status,
):

    initialize_input_database()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    with db() as conn:

        conn.execute(
            """
            UPDATE loans

            SET
                borrower = ?,
                loan_id = ?,
                loan_start_date = ?,
                expected_closure_date = ?,
                sanctioned_amount_cr = ?,
                initial_disbursement_cr = ?,
                outstanding_at_onboarding_cr = ?,
                required_security_cover = ?,
                loan_status = ?,
                updated_at = ?

            WHERE id = ?
            """,
            (
                borrower.strip(),
                loan_id.strip(),
                str(loan_start_date),
                (
                    str(expected_closure_date)
                    if expected_closure_date
                    else None
                ),
                float(
                    sanctioned_amount_cr
                ),
                float(
                    initial_disbursement_cr
                ),
                float(
                    outstanding_at_onboarding_cr
                ),
                float(
                    required_security_cover
                ),
                loan_status,
                now,
                loan_db_id,
            ),
        )


# ============================================================
# EDIT EXISTING SECURITY
# ============================================================

def update_security(
    security_id,
    listed_company_name,
    nse_symbol,
    isin,
    initial_pledged_shares,
    initial_pledge_date,
    collateralwise_security_cover,
    active=1,
):

    initialize_input_database()

    with db() as conn:

        conn.execute(
            """
            UPDATE securities

            SET
                listed_company_name = ?,
                nse_symbol = ?,
                isin = ?,
                initial_pledged_shares = ?,
                initial_pledge_date = ?,
                collateralwise_security_cover = ?,
                avtive = ?

            WHERE id = ?
            """,
            (
                listed_company_name.strip(),
                nse_symbol.strip().upper(),
                isin.strip().upper(),
                int(
                    initial_pledged_shares
                ),
                str(
                    initial_pledge_date
                ),
                float(
                    collateralwise_security_cover
                ),
                security_id,
            ),
        )