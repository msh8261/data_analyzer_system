db_info = """### Database Structure:

### Database Structure:

    **Tables:**
    1. **employee**
    - `employee_id` (INT)
    - `full_name` (TEXT)
    - `department` (TEXT)

    **Sample Data**:
    | employee_id | full_name     | department   |
    |-------------|---------------|--------------|
    | 1           | John Doe      | Sales        |
    | 2           | Jane Smith    | Marketing    |
    | 3           | Alice Johnson | HR           |
    | 4           | Bob Brown     | Sales        |
    | 5           | Charlie Lee   | Engineering  |
    | 6           | David White   | Marketing    |
    | 7           | Eva Green     | HR           |
    | 8           | Frank Black   | Sales        |
    | 9           | Grace Clark   | Engineering  |
    | 10          | Henry Adams   | Marketing    |

    2. **sales**
    - `sale_id` (INT)
    - `employee_id` (INT, FK to `employee`)
    - `units_sold` (REAL)
    - `sale_date` (DATE)

    **Sample Data**:
    | sale_id | employee_id | units_sold | sale_date  |
    |---------|-------------|------------|------------|
    | 1       | 1           | 200        | 2021-01-01 |
    | 2       | 1           | 150        | 2021-02-01 |
    | 3       | 2           | 300        | 2021-01-01 |
    | 4       | 2           | 250        | 2021-02-01 |
    | 5       | 3           | 180        | 2021-01-01 |
    | 6       | 3           | 220        | 2021-02-01 |
    | 7       | 4           | 210        | 2021-01-01 |
    | 8       | 4           | 190        | 2021-02-01 |
    | 9       | 5           | 240        | 2021-01-01 |
    | 10      | 6           | 300        | 2021-01-01 |

    ### Key Points:
    - **Relationships**: One-to-many between `employee` and `product_sales` via `employee_id`.
    - **Indexes**: Likely primary keys on `employee_id` and `sale_id`.

    ### Example Query:
    - **Total units sold by each employee**:
    ```sql
    SELECT e.full_name, SUM(p.units_sold) AS total_sales_units
    FROM employee e
    JOIN product_sales p ON e.employee_id = p.employee_id
    GROUP BY e.employee_id;
    ```
   
   """
