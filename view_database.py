import sqlite3


DATABASE_PATH = "database/collateral.db"


connection = sqlite3.connect(
    DATABASE_PATH
)


cursor = connection.cursor()


cursor.execute(
    """
    SELECT
        date,
        borrower,
        security,
        price,
        collateral_value,
        cover,
        status

    FROM collateral_history
    """
)


records = cursor.fetchall()


print("=" * 80)
print("COLLATERAL HISTORY")
print("=" * 80)


for row in records:

    print(
        f"""
Date       : {row[0]}
Borrower   : {row[1]}
Security   : {row[2]}
Price      : ₹{row[3]}
Collateral : ₹{row[4]:,.2f}
Cover      : {row[5]}x
Status     : {row[6]}
----------------------------------------
"""
    )


connection.close()