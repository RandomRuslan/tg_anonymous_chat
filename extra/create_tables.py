import sqlalchemy as sa

from constants import DB_URL

db = sa.create_engine(DB_URL)

db.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        gender VARCHAR(2) NOT NULL, 
        preference VARCHAR(2),
        prev_partners TEXT,
        partner INTEGER 
    );
''')


# db.execute('''
#     CREATE TABLE IF NOT EXISTS chats (
#         id SERIAL,
#         userid1 INTEGER NOT NULL,
#         userid2 INTEGER NOT NULL,
#         startts TIMESTAMP,
#         finishts TIMESTAMP
#     );
# ''')

# try:
#     db.execute("INSERT INTO users VALUES ('12345', 'my_first_user_in_table', 'm', 'b');")
# except sa.exc.IntegrityError as e:
#     pass

