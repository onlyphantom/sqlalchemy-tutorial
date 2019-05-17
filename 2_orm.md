# Ground Up tutorial to SQLAlchemy: Course 2
In the first course we've seen how to create an instance of `Engine` and we learned that the `Engine` doesn't establish a real DBAPI connection to the database until a method like `Engine.execute()` or `Engine.connect()` is used to perform **a task against the database**. 

SQLAlchemy users however, do not usually interact with the `Engine` directly once created; Instead, we bind the `Engine` to `sessionmaker` which serve as a factory for new `Session` objects. This way of working with the database (using `Session`) is different from what we've been doing in the course thus far - it's presenting a high level and abstracted pattern of usage. This course aims to present a ground-up way of understanding this pattern, starting from the configuration.

## Object-relational configuration
> When using the ORM, the configurational process starts by describing the database tables we’ll be dealing with, and then by defining our own classes which will be mapped to those tables. In modern SQLAlchemy, these two tasks are usually performed together, using a system known as `Declarative`, which allows us to create classes that include directives to describe the actual database table they will be mapped to.

At the heart of the abstraction in the ORM pattern is the `Declarative` system, used by SQLAlchemy to define classes mapped to relational database tables. Classes mapped are defined in terms of a base class, which you can imagine as "a catalog of classes and tables relative to that base". We call this the **declarative base class**. Usually, an application will have just one instance of this base, created using the `declarative_base()` function:

### Declarative Base

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" id="base-1"}
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base() 
```

Once we have a base, we can define any number of mapped classes in terms of it. Let's start with a single table, `customers` and a class called `Customer` which we map to this table. Within the class, we define details about the table to which we'll be mapping:
- Table name  
- Name of columns
- Datatypes of columns

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="base-1"}
from sqlalchemy import Column, Integer, String
class Customer(base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)
    def __repr__(self):
        return f"<Customer(name={self.name}, country={self.country})>"

```

A class using Declarative at a minimum needs a `__tablename__` attribute and a `Column` that is part of a primary key. SQLAlchemy doesn't make any assumption about the table to which a class refers, and has no built-in conventions for names, datatypes, or constraints. 



## Mapping and `Mapper()`