# Quizzes
> Answer the following questions by referencing the Knowledge Check sections in `1_connections`.

1. Use the `engine.table_names()` to print the table names from `rcsample.db` located in the `/data` folder. How many tables were there? 
- [ ] None
- [ ] 3
- [ ] 4
- [ ] 5

2. Create an engine just like you did in (1) and execute a SQL query to count the number of rows within the `employee` table. How many rows are there?
- [ ] 18
- [ ] 28
- [ ] 38
- [ ] 48

3. What is the output of `len(fetched.values())`?
- [ ] Empty list
- [ ] 2
- [ ] 3
- [ ] 4

4. What is the output of `len(results)`?
- [ ] Empty list
- [ ] 2
- [ ] 3
- [ ] 4

5. Is `results` an instance of `list`?
- [ ] Yes, it is a list
- [ ] No

> Answer the following questions by referencing the Knowledge Check sections in `2_orm_mappings`.

6. From the code you find in the Knowledge Check section, the `Author` and `Blogpost` models are mapped using which approach? 
- [ ] Classical Mappings
- [ ] Declarative Mappings

7. Applying what you've learned in coursebook (1), execute the following query and return a scalar using `.scalar()`:
`SELECT COUNT(*) FROM author`

What is the integer value that is returned from that SQL statement?
- [ ] No integer returned. Just a `Resultroxy` object.
- [ ] 0
- [ ] 1

> If you have participated in an instructor-led workshop and given credit, pick a participation code. Otherwise leave this blank empty or on its default value. 

# Instructor-led participation

8. [Classroom] Participation code:
- [x] Alpha
- [ ] Beta
- [ ] Delta
- [ ] Mu 