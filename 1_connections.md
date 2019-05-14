# Ground Up tutorial to SQLAlchemy
To truly appreciate the inner workings of SQLAlchemy, we need to fully grasp **four main objects** that are foundational to the SQLAlchemy module:
- `Engine`
- `Connection`
- `Transaction`
- `Session`

## Understanding `Engine` and `Connection`
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

### Understanding `ResultProxy.close()`

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
Instead of the exception, the try/except block returns a `None`.

### `RowProxy`: Like Tuples, but not really

Most of what you do with SQLAlchemy involves fetching some rows from a database. At first sight, it seems like SQLAlchemy returns a tuple. Look at the following code block and pay attention to the returned value of:
- `fetched`
- `fetched[:2]` 
- `len(fetched)`

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" id="row-proxy-1"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///rcsample.db')
conn = engine.connect()
d = {}

executed = conn.execute('SELECT timeliness, satisfaction_score, comments FROM response ORDER BY workshop_id  LIMIT 1 OFFSET 8')
fetched = executed.fetchone()
d['timeliness'], d['satisfaction'], d['comments'] = fetched
```

The returned value from one of the `fetchXXX()` method looks and _behaves_ almost like a tuple in the way we perform indexing and slicing. `len()` also correctly prints the number of elements in the "tuple":

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="row-proxy-1"}
print(fetched)
print(fetched[:2])
print(len(fetched))
```

However, it is not an instance of the `tuple` class. If it were a tuple, we wouldn't expect `fetched['comments']` to work:

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="row-proxy-1"}
print(fetched['comments'])
print(d)
print(isinstance(fetched, tuple))
print(isinstance(d, dict))
```

If it is not a `tuple`, what then could it be?

Well, turns out it is a proxy, namely a `RowProxy`. This `RowProxy` allows for the values of the individual columns to be accessed in addition to the tuple-like slicing behavior. The documentation on `ResultProxy` reads:
> Individual columns may be accessed by their integer position, case-insensitive column name, or by schema.Column object

This allows us to build our dictionary `d` through accessing the value specified by column names.

Let's break down the concepts from `ResultProxy` to `RowProxy` a little more:

- `executed` is a `ResultProxy`. A `session.execute()` or `connection.execute()` method uses the `ResultProxy` to return its values
- The `ResultProxy` instance is comprised of `RowProxy` instances  
- The `RowProxy` object has two useful methods:
    - `.items()`: This returns the key, value tuples of all the items in the row as a list
    - `.values()`: Returns all values as a list

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="row-proxy-1"}
print(fetched.values())
print(isinstance(fetched.values(), list))
print(fetched.items())
print(isinstance(fetched.items()[0], tuple))
```

This allows us to unpack each value in the tuple in a `for` operation:
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///rcsample.db')
conn = engine.connect()
fetched = conn.execute('SELECT timeliness, satisfaction_score FROM response ORDER BY workshop_id  LIMIT 3 OFFSET 8').fetchall()

print(fetched)
print(fetched[1].keys())
print(fetched[1].values())
print(fetched[0].has_key('timeliness'))
reviews = [{col:val for col, val in eachset.items()} for eachset in fetched]
print(reviews)
```

As we've seen, `RowProxy` is really just a proxy for values from a single cursor row. The methods found on the documentation of `RowProxy` are:
- `has_key()`: Return True if this `RowProxy` contains the given key
- `items()`: Return a list of types, each tuple containing a key/value pair
- `keys()`: Return the list of keys as strings

Curiously, `values()` is not a documented method, even though as we've seen above it return the values of a single cursor row as a list.







Another example:
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
conn = engine.connect()
results = []

conn.execute('CREATE TABLE "salesperson" ('
           'id INTEGER NOT NULL,'
           'name VARCHAR,'
           'PRIMARY KEY (id));')
conn.execute('INSERT INTO "salesperson" (name)'
         'VALUES ("John Doe"), ("Margaret"), ("Anna")')
results += conn.execute('SELECT * FROM salesperson').fetchmany(3)

print(results)
print(results[0])
print(results[0][1])
print(results[0]['name'])
print(isinstance(results, list))
print(isinstance(results[0], tuple))
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

## Transactions
In database lingo, **transaction** is a logical, atomic unit of work that contains one or more SQL statements. Database users use transaction to group SQL statements so that they are either all committed (which means applied to the database), or all rolled back. 

We use `Transactions` directly when working with `Engine` and `Connection` objects, but rarely so when we work with SQLAlchemy ORM (we'll get to what ORM means in the next chapter). 

The `Connection` object provides a `begin()` method which returns an instance of `Transaction` - this instance represents the "scope" of the transaction so that it's guaranteed to invoke one, and **only one**, of two methods:
- `Transaction.rollback()`
- `Transaction.commit()`

The transaction "scope" completes when one of the two method above is called. The `Transaction` object is usually used within a try/except clause but it also implements a context manager interface so Python's `with` statement can be used in the following way:

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
import os
from sqlalchemy import create_engine
engine = create_engine('sqlite:///salesperson.db')
results = engine.execute('SELECT * FROM salesperson')
print("Before transaction:", results.fetchall())
with engine.begin() as conn:
    conn.execute('INSERT INTO "salesperson" (name)'
             'VALUES ("Marshall")')
    conn.execute('INSERT INTO "salesperson" (name)'
             'VALUES ("John Doe"), ("Margaret"), ("Anna")')

results = engine.execute('SELECT * FROM salesperson')
print("After transaction:",results.fetchall())
os.remove('salesperson.db')
```
Now, have we tried a simple experiment by changing the last `INSERT` clause to say `INSERT INTO "salespeople" (name)` instead of `INSERT INTO "salesperson (name)"`, what do you think would happen?

To verify this, you can open `salesperson.db` using any of your favorite sqlite browser, and hopefully, you will see that Marshall is not included in the table. Yes - the earlier `INSERT` clause did not take effect as the Transaction wasn't completed. 

This follows the "A" in "ACID", which is short for **Atomicity**. All tasks of a transaction are performed or none of them are. There are no partial transactions. If a transaction starts updating 10 rows but fails after 7 rows, the database rolls back the changes to these 7 rows.

### Not everything can be "rolled back"
For an SQLAlchemy user not particularly familiar with SQL, sometimes its not obvious when an unexpected behavior is due to SQLAlchemy's design decisions or characteristics of the underlying database. One such example is the `rollback()` method.

Consider the following example of `Transction`. The code is similar to the context-manager one above, with one change: we're using a try/except clause instead of a context manager. This allow me to exclude a `raise()`, with the except clause is executed. 

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
tbl_names = engine.table_names
print(tbl_names())
conn = engine.connect()
trans = conn.begin()
results = []
try:
    conn.execute('CREATE TABLE "salesperson" ('
               'id INTEGER NOT NULL,'
               'name VARCHAR,'
               'PRIMARY KEY (id));')
    conn.execute('INSERT INTO "salesperson" (name)'
             'VALUES ("John Doe"), ("Margaret"), ("Anna")')
    results += conn.execute('SELECT * FROM salesperson').fetchmany(3)
    trans.commit()
except:
    trans.rollback()
    # raise()

print(results)
print(tbl_names())
```
Let's inspect the three `print` statements in the order of execution:
1. `print(tbl_names)` in line 4 returns an empty list. At this point, no tables were created yet in our in-memory database.
2. `print(results)` returns a list of `RowProxy`. Notice that while it prints like a  

Supposed we repeat our experiment by changing the last `INSERT` clause to say `INSERT INTO "salespeople" (name)` instead of `INSERT INTO "salesperson (name)"`, what do you think would happen to the two `print` statements at the bottom?

You may have guessed that we got two empty lists (`[]`). Except that's not what happened. As it turns out, we got an empty list (`[]`) from printing `results` but our `tbl_names()` return `['salesperson']`. 







```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python"}
from sqlalchemy import create_engine
connection = create_engine('sqlite:///rcsample.db').connect()
result = connection.execute("SELECT workshop_category, class_size FROM workshop LIMIT 10")
print([row['class_size'] for row in result])
print([col for col in result.keys()])
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
