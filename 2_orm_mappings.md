---
toc:
  depth_from: 1
  depth_to: 4
  ordered: true
---
# Ground Up tutorial to SQLAlchemy: Course 2

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

* [Ground Up tutorial to SQLAlchemy: Course 2](#ground-up-tutorial-to-sqlalchemy-course-2)
	* [Object-relational configuration](#object-relational-configuration)
		* [Declarative Base](#declarative-base)
		* [Two types of Mappings](#two-types-of-mappings)
			* [Classical Mappings](#classical-mappings)
			* [Declarative Mappings](#declarative-mappings)
		* [Runtime Introspection](#runtime-introspection)
					* [Knowledge Check](#knowledge-check)
	* [Summary](#summary)

<!-- /code_chunk_output -->



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

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="base-1" id="base-2"}
from sqlalchemy import Column, Integer, String
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)
    def __repr__(self):
        return f"<Customer(name={self.name}, country={self.country})>"
```

A class using Declarative at a minimum needs a `__tablename__` attribute and a `Column` that is part of a primary key. SQLAlchemy doesn't make any assumption about the table to which a class refers, and has no built-in conventions for names, datatypes, or constraints. 

When our class is constructed, Declarative replaces all `Column` objects with special Python accessor known as **descriptors** in a process known as instrumentation. Through instrumentation, our `Customer` class will be provided with the means to refer to our table in a SQL context, as well as to persist and load the values of columns from the database. 

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="base-2"}
cust = Customer()
cust.id = 3
cust.name = "Mary Anne"

class Representative():
    id = 3
    name = "Andy"

rep1 = Representative()
rep1.name = "McKinsey"

print(cust.__tablename__)
print(rep1.name)
```

From the code above, we are reminded that outside of what the mapping does to our class, the class remains otherwise mostly a normal Python class to which we can define any number of ordinary attributes and methods. `cust`'s distinctive difference from that of a regular Python class instance is that it includes the mapper attribute (`cust.__mapper__`) informing its mapping configuration onto the `customers` table.

### Two types of Mappings

One source of confusion for developers is how there seems to be more than one way to perform a mapper configuration. To understand this, it's helpful to recognize that SQLAlchemy apps can feature two distinct styles of mapper configuration:
- The "Classical" style is SQLAlchemy's original mapping API  
- The "Declarative" style is the richer and more succinct system we see above  
They may be used interchangably as the end result is exactly the same: a user-defined class mapped by the `mapper()` function onto a selectable unit, typically a `Table`.

#### Classical Mappings
A _Classical Mapping_ refers to the configuration style that uses the `mapper()` function directly without the Declarative system. In this classical form, the table metadata is created separately with the `Table` construct, then associated with the `Customer` class via `mapper()`:

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" id="classical-1"}
from sqlalchemy import Table, MetaData, Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapper

metadata= MetaData()
customer = Table('customer', metadata, 
                Column('id', Integer, primary_key=True),
                Column('name', String(50)),
                Column('country', String(12))
            )

class Customer(object):
    def __init__(self, name, country):
        self.name = name
        self.country = country
```

To associate the `Class` with the `Table`, we use `mapper()`:
```py
mapper(Customer, customer)
```

Just for illustration purposes, let's see the print output of this `mapper()` method:
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="classical-1"}
print(f'{mapper(Customer, customer)}')
```

Information about mapped attributes such as relationships to other classes are provided via the `properties` dictionary:
```py
receipt = Table('receipt', metadata,
                Column('id', Integer),
                Column('customer_id', Integer, ForeignKey('customer.id')),
                Column('amount', Integer)
            )

mapper(Customer, customer, properties={
    'receipts': relationship(Receipt, backref='customer', order_by=receipt.c.id)
})

mapper(Receipt, receipt)
```

When using classical mappings, classes must be provided directly without the benefit of the "string lookup" system provided by Declarative. SQL expressions are specified in terms of the `Table` objects, i.e. `receipt.c.id` and not `Receipt.id` (Class attribute) as the `Receipt` class may not yet be linked to table metadata. 

#### Declarative Mappings 
We said that the two Classical and Declarative approaches are fully interchangable because ultimately, they create the same configuration:
- `Table`
- User-defined class
- Linking the two above with a `mapper()`

```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" id="declarative-1"}
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base() 
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)
    def __repr__(self):
        return f"<Customer(name={self.name}, country={self.country})>"

```

When we inherit from a base class, created through `declarative_base()`, instance of this class has a `.__mapper__` attribute even though we did not explicit call `mapper()` as per the Classical approach: 
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="declarative-1"}
print(f'{Customer().__mapper__}')
```

### Runtime Introspection
Having learned that the `Mapper` object is available from any mapped class, regardless of approaches, we shall see how to "acquire" the `Mapper` from a mapped class through `inspect()`: 
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="declarative-1"}
from sqlalchemy import inspect
insp = inspect(Customer)
print(list(insp.columns)) # equivalent: [i for i in insp.columns]
```

`Mapper.columns` is an ordered collection that we can view in a list, like we did above, or accessed via column names. To see an example, we can try printing `insp.columns.country` and see the following returned:
```py
Column('country', String(), table=<customers>)
```

Another useful namespace is the `Mapper.all_orm_descriptors`, which includes all mapped attributes as well as hybrids, association proxies: 
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" continue="declarative-1"}
from sqlalchemy import inspect
insp = inspect(Customer)
print(insp.all_orm_descriptors.keys())
```

###### Knowledge Check
```py {cmd="/Users/samuel/.virtualenvs/revconnexion/bin/python" id="knowledge-1"}
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Date, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

if os.path.exists('blog.db'):
    os.remove('blog.db')

engine = create_engine('sqlite:///blog.db')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    blogs = relationship("Blogpost", backref="written")

class Blogpost(Base):
     __tablename__ = 'blogpost'
     id = Column(Integer, primary_key=True)
     created = Column(Date, default=datetime.now)
     writtenby = Column(ForeignKey("author.id"))

Base.metadata.create_all(engine)

sherlock = Author(username="sherlock")
blogpost1 = Blogpost(writtenby=1)
session.add_all([sherlock, blogpost1])
session.commit()
```

1. In the code above, the `Author` and `Blogpost` models are mapped using which approach? Choose from the following:
    Choice (1): Classical Mappings
    Choice (2): Declarative Mappings

2. Applying what you've learned in coursebook (1), execute the following query and return a scalar using `.scalar()`:
`SELECT COUNT(*) FROM author`
    What is the integer value that is returned from that SQL statement?

------

## Summary

In coursebook (2), we learn about a crucial component of the SQLAlchemy ORM pattern: the object-relational mapping. 
 
In particular, we've learned:

- Object-relational configuration
- the Declarative Base
- two types of mappings and their differences
- the `mapper()` object
- performing runtime introspection
