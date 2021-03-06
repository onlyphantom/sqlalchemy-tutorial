# Ground Up tutorial to SQLAlchemy

## Project Description
A ground-up introduction to SQLAlchemy, which will cover everything from `Engine`, to `Pools` and its ORM implementation through `Session`.

Update on an almost-daily basis since 12 May 2019.

## Preview (Sample Chapter)
The `Engine` is the starting point for any SQLAlchemy application. The official documentation calls it the **home base** for the actual database and its DBAPI, and a `Dialect` which describes how to talk to a specific kind of database/DBAPI combination.
![](assets/sqla_engine_arch.png)
The code below creates an `engine`, which rereferences a **Dialect** object tailored for SQLite and a **Pool** object which will establish a DBAPI connection when a connection request is first received.

```py
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
print(engine)
```
<pre class="language-text">Engine(sqlite:///:memory:)
</pre>

Notice that the `Engine` and its underlying `Pool` doesn't establish the first actual DBAPI until the `Engine.connect()` method is called, or until an operation dependent on this method (such as `Engine.execute()`) is invoked. In this way, `Engine` and `Pool`is said to have a _lazy initialization_ behavior.

> The typical usage of `create_engine()` is once per particular database URL, held globally for the lifetime of a single application process... it is most efficient when created just once at the module level of an application, not per-object or per-function call.

The Engine can be used in one of two ways:
- Interact with the db directly by through SQL commands  
- Passed to a `Session` object to work with the ORM 

## Working with Engines directly

A common use-case is to procure a connection resource via the `Engine.connect()` method:

```py
from sqlalchemy import create_engine
connection = create_engine('sqlite:///../data/rcsample.db').connect()
result = connection.execute("select * from response order by workshop_id desc limit 10")
print([row['comments'] for row in result])
print([col for col in result.keys()])
```
<pre class="language-text">['', '', '', '', '', '', '', '', 'yang robustness kok belum ya bang', 'Thank you,  you can teach and explain all the statistics "things" very clearly and make it fun. ']
['id', 'workshop_id', 'difficulty', 'assistants_score', 'knowledge', 'objectives', 'timeliness', 'venue_score', 'satisfaction_score', 'comments']
</pre>

The `connection` we created above is an instance of `Connection`, which is a **proxy** object for an actual DBAPI connection.

####  Queue Pool
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

Using the Engine to execute our database commands:
```py
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
engine.execute('CREATE TABLE "salesperson" ('
               'id INTEGER NOT NULL,'
               'name VARCHAR,'
               'PRIMARY KEY (id));')
# print list of tables name
print(engine.table_names())
```
<pre class="language-text">['salesperson']
</pre>