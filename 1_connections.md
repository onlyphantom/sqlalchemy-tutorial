# Ground Up tutorial to SQLAlchemy

## Understanding the `Engine` object
The `Engine` is the starting point for any SQLAlchemy application. The official documentation calls it the **home base** for the actual database and its DBAPI, and a `Dialect` which describes how to talk to a specific kind of database/DBAPI combination.
![](assets/sqla_engine_arch.png)

The code below creates an `engine`, which rereferences a **Dialect** object tailored for SQLite and a **Pool** object which will establish a DBAPI connection when a connection request is first received.

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
print(engine)
```

Notice that the `Engine` and its underlying `Pool` doesn't establish the first actual DBAPI until the `Engine.connect()` method is called, or until an operation dependent on this method (such as `Engine.execute()`) is invoked. In this way, `Engine` and `Pool`is said to have a _lazy initialization_ behavior.

> The typical usage of `create_engine()` is once per particular database URL, held globally for the lifetime of a single application process... it is most efficient when created just once at the module level of an application, not per-object or per-function call.

The Engine can be used in one of two ways:
- Interact with the db directly by through SQL commands  
- Passed to a `Session` object to work with the ORM 

## Working with Engines directly

A common use-case is to procure a connection resource via the `Engine.connect()` method:

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT * FROM response ORDER BY workshop_id desc LIMIT 10")
print([col for col in result.keys()])
```

The `connection` we created above is an instance of `Connection`, which is a **proxy** object for an actual DBAPI connection.

### `ResultProxy.close()`

What about `result`? Well, `result` is an instance of `ResultProxy`, a **proxy** object that references a DBAPI cursor and provides a largely compatible inferface with that of the DBAPI cursor. The DBAPI cursor will be closed by the `ResultProxy` when all of its result rows are exhausted. A `ResultProxy` that returns no rows, such as that of an `UPDATE` statement, releases cursor resources immediately upon construction. Let's see an example of that:

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT * FROM response ORDER BY workshop_id LIMIT 5")
print([row['comments'] for row in result])
print([row['comments'] for row in result])
print([row['comments'] for row in result])
```

Notice that after the first time, the result rows are exhausted so subsequent call to `print()` return an empty list. Similarly, when we use one of `fetchall()`, `fetchmany()` and `fetchone()` to fetch result rows, once all rows have been exhausted any subsequent rows will return an empty list.

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT satisfaction_score, comments FROM response ORDER BY workshop_id LIMIT 5")
print(result.fetchall())
print(result.fetchall())
print(result.fetchall())
```

Why is it important to learn about the `ResultProxy.close()` method so early on in the Ground Up tutorial? Because it is very fundamental to how `ResultProxy` and how return sets in general will behave. It's a concept that seasoned developers familiar to SQL or those working with ORM will often take for granted; Inexperienced developers new to SQLAlchemy however often find confusing. 

To add to said beginner's confusion, some of the operations don't seem all that obvious that the `ResultProxy.close()` would have been called. One common example is the `.first()` method. 

The `first()` method fetches the first row and then close the result set unconditionally: 

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
from sqlalchemy.exc import ResourceClosedError
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT satisfaction_score, comments FROM response ORDER BY workshop_id LIMIT 5")
print(result.first())
try: 
    print(result.fetchall())
except ResourceClosedError as e:
    print("Resource Closed:", e)
```

A quick recap:
```py
engine = create_engine('sqlite:///rcsample.db')
print(engine) 
# returns: Engine(sqlite:///rcsample.db)

connection = engine.connect()
print(connection)
# returns: <sqlalchemy.engine.base.Connection object at 0x1069b7b00>

result = connection.execute("SELECT * FROM response ORDER BY workshop_id LIMIT 5")
print(result)
# returns: <sqlalchemy.engine.result.ResultProxy object at 0x1069b7b00>
```


#### The Soft Close

_New in version 1.0.0_
The method releases all DBAPI cursor resources but leaves the `ResultProxy` "open" from a semantic perspective, meaning the `fetchXXX()` methods will continue to return empty results instead of raising a `ResourceClosedError` exception :
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
from sqlalchemy.exc import ResourceClosedError
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT satisfaction_score, comments FROM response ORDER BY workshop_id LIMIT 5")
print(result.fetchall())
try: 
    result._soft_close()
    print(result.fetchone())
except ResourceClosedError as e:
    print("Resource Closed:", e)
```


###  Queue Pool

Whenever the `connect()` or `execute()` methods are called, the `Engine` will ask the connection pool for a connection. The default connection pool, `QueuePool` will open connections to the database on an as-needed basis; As concurrent statements are executed, `QueuePool` will grow its pool of connections to a defaulot size of five, and allow a default "overflow" of ten.
> Tip:
> `QueuePool` is not used by default for SQLite engines

We can overwrite the above using the Engine Creation API.
```py
engine = create_engine(
    "mysql://scott:tiger@hostname/dbname",
    case_sensitive=True,
    encoding='latin1', 
    pool_size=5,
    max_overflow=10)
```

The several parameters in our engine creation call above:
- **case_sensitive=True**: if False, result columns names will match in a case-insensitive fashion
- **encoding**: defaults to `utf-8`; The string encoding used by SQLAlchemy for string encode/decode operations which occur within SQLAlchemy, **outside of the DBAPI**
- **pool_size**: number of connections to keep open. To disable pooling, set `poolclass` to `NullPool`, a `pool_size` setting of 0 indicates no limit
- **max_overflow**: number of connections to allow in connection pool "overflow", that is connections that can be opened above and beyond the `pool_size` setting

---
Knowledge Check:
1. Use the `engine.table_names()` to print the table names from `rcsample.db`. How many tables were there? 

2. Create an engine just like you did in (1) and execute a SQL query to count the number of rows within the `employee` table. How many rows are there?

<details>
<summary>Hint:</summary>
<p>

Hint for question (1):
```py
# import engine...
print(engine.table_names())
```

Hint for question (2):
```py
# import engine and wrap sql command
conn.execute('SELECT COUNT(*) FROM employee').scalar()
```

</p>
</details>

------

### Transactions

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT workshop_category, class_size FROM workshop LIMIT 10")
print([row['class_size'] for row in result])
print([col for col in result.keys()])
```



Using the Engine to execute our database commands:
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
engine.execute('CREATE TABLE "salesperson" ('
               'id INTEGER NOT NULL,'
               'name VARCHAR,'
               'PRIMARY KEY (id));')
# print list of tables name
print(engine.table_names())
```


```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
conn = create_engine('sqlite:///rcsample.db').connect()
result = conn.execute('SELECT * FROM workshop LIMIT 10')
print(result)
```

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
allresults = []
result = connection.execute("SELECT satisfaction_score FROM response ORDER BY workshop_id LIMIT 5")
allresults += result.fetchone()
result.close()
print(allresults)
allresults += result.fetchmany(2)
print(allresults)
```


```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
conn = engine.connect()
trans = conn.begin()
conn.execute('CREATE TABLE "salesperson" ('
               'id INTEGER NOT NULL,'
               'name VARCHAR,'
               'PRIMARY KEY (id));')
conn.execute('INSERT INTO "salesperson" (name)'
             'VALUES ("John Doe"), ("Margaret"), ("Anna")')
conn.execute('SELECT age FROM salesperson')
trans.commit()

results = conn.execute('SELECT * FROM salesperson')
print([{column:value for column, value in result.items()} for result in results])
```
