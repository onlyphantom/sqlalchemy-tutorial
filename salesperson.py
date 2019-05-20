from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
engine.execute('CREATE TABLE "salesperson" ('
               'id INTEGER NOT NULL,'
               'name VARCHAR,'
               'PRIMARY KEY (id));')

# print list of tables name
engine.table_names()

# use transactions (all commands must be successful, else rollback)
conn = engine.connect()
trans = conn.begin()
conn.execute('INSERT INTO "salesperson" (name)'
             'VALUES ("John Doe"), ("Margaret"), ("Anna")')
trans.commit()

# query single result
row = conn.execute('SELECT * FROM salesperson LIMIT 1').fetchone()
row[0] # returns 1
row[1] # returns 'John Doe'

resultproxy = conn.execute('SELECT * FROM salesperson')
# rows
# <sqlalchemy.engine.result.ResultProxy object at 0x102a2a9b0>
d, a = {}, []
for rowproxy in resultproxy:
    for column, value in rowproxy.items():
        print(d)
        d = {**d, **{column:value}}
    a.append(d)

[{column:value for column, value in rowproxy.items()} for rowproxy in resultproxy]
