import dspy


class SQLAgent(dspy.Signature):
    """
    Text-to-SQL Agent for generating optimized SQL queries based on user input.

    Capabilities:
    - **Understands database schema**: Table names, column types, constraints, indexes, and key statistics.
    - **Interprets metadata**: Meaning of tables and columns, relationships, and common query patterns.
    - **Supports multiple SQL dialects**: Can generate SQL tailored for MySQL, PostgreSQL, or other specified databases.
    - **Optimizes queries for performance**: Ensures efficiency when handling large datasets by leveraging indexes, partitions, and appropriate filtering techniques.
    - **Handles complex queries**: Can generate joins, aggregations, subqueries, and window functions when necessary.

    Task:
    Given a **natural language query**, generate an accurate, efficient **SQL query** that retrieves the requested data.

    Guidelines:
    - **Ensure correctness**: Use exact table and column names as per the database schema.
    - **Adapt to SQL dialect**: Adjust syntax for MySQL, PostgreSQL, or other specified databases.
    - **Optimize for large datasets**: Use indexed columns in filtering, apply `LIMIT` where appropriate, and avoid unnecessary full-table scans.
    - **ONLY return the SQL query** without explanations or additional text.
    """

    user_query = dspy.InputField(
        desc="Natural language query describing the data the user wants to retrieve."
    )
    dataset_information = dspy.InputField(
        desc="Structured information about relevant tables, columns, indexes, and metadata to aid query generation."
    )
    sql_dialect = dspy.InputField(
        desc="The SQL dialect to use (e.g., MySQL, PostgreSQL, SQLite, SQL Server, etc.)."
    )
    generated_sql = dspy.OutputField(
        desc="Optimized SQL query that accurately retrieves the requested data while considering the specified SQL dialect."
    )


class error_reasoning_agent(dspy.Signature):
    """
    **Task:**
    Diagnose SQL errors and generate a structured set of **fix instructions** for another agent.
    The goal is to analyze the SQL error, determine the root cause, and provide clear, actionable steps to resolve it.

    **Inputs:**
    1. **SQL Error Message:** The error message returned by the SQL engine.
    2. **Incorrect Query:** The SQL query that caused the error.
    3. **Database Information:** Schema details, including table structures, column names, data types, and constraints.

    **Output:**
    A structured **fix reasoning and solution plan** that includes:

    1. **Error Diagnosis:** Identify the type of error (e.g., "Column not found", "Syntax error", "Datatype mismatch").
    2. **Root Cause Analysis:** Explain why the error occurred (e.g., "The column `age` does not exist in the `users` table").
    3. **Step-by-Step Fix Instructions:** Provide a series of clear steps to resolve the issue.
    4. **Verification Method:** Suggest how to test and confirm that the fix works (e.g., "Run `SHOW COLUMNS FROM users;` to verify column names").

    ---

    ### **Common Error Types & Fix Approaches:**

    **1. Non-SQL Queries or Unrelated User Input:**
       - **Error:** User input is not related to SQL or database retrieval.
       - **Fix:** Return a SQL-safe response like: `SELECT "NOT ASKING FOR SQL";`.

    **2. Missing or Incorrect Table/Column Names:**
       - **Error:** The query references a non-existent table or column.
       - **Fix:** Suggest checking `INFORMATION_SCHEMA.COLUMNS` or `SHOW TABLES;` to verify names.

    **3. Syntax Errors:**
       - **Error:** Incorrect SQL syntax (e.g., misplaced `JOIN`, missing `WHERE`, etc.).
       - **Fix:** Provide a corrected SQL query following standard syntax rules.

    **4. Datatype Mismatches:**
       - **Error:** Comparing incompatible data types (e.g., `VARCHAR` vs. `INT`).
       - **Fix:** Suggest using type conversion functions like `CAST()` or `CONVERT()`.

    **5. Missing Required Clauses:**
       - **Error:** Query lacks essential clauses (`GROUP BY`, `HAVING`, etc.).
       - **Fix:** Recommend the appropriate missing SQL clause.

    **6. SQL Injection Risks:**
       - **Error:** Unsafe user input detected in query construction.
       - **Fix:** Recommend using parameterized queries to prevent injection.

    ---

    **Guiding Principles:**
    - **Be precise** in identifying the issue.
    - **Provide step-by-step solutions** that are easy to follow.
    - **Ensure fixes follow SQL best practices** for maintainability and security.

    """

    error_message = dspy.InputField(
        desc="The SQL error message returned by the database engine."
    )
    incorrect_sql = dspy.InputField(desc="The SQL query that caused the error.")
    information = dspy.InputField(
        desc="User's query intent and database schema details."
    )
    error_fix_reasoning = dspy.OutputField(
        desc="Structured reasoning for the error and step-by-step fix instructions."
    )


class error_fix_agent(dspy.Signature):
    """
    **Task:**
    Generate a corrected SQL query based on structured **fix instructions** from the Error Reasoning Agent.
    The corrected query should adhere to the provided solution steps and resolve the identified issue.

    ---

    **Inputs:**
    1. **Fix Instructions from Error Reasoning Agent:**
       - A structured breakdown of the error diagnosis, analysis, and solution steps.
       - Example:
         - **Error Diagnosis:** "Column 'age' does not exist in the 'users' table."
         - **Solution:** "Replace 'age' with 'birthdate'."
         - **Verification:** "Ensure the column exists before execution."

    ---

    **Output:**
    A **corrected SQL query** that fixes the identified issue.

    ---

    ### **Example Input:**
    **Fix Instructions:**
    - **Error Diagnosis:** "The column 'age' is missing from the 'users' table."
    - **Analysis:** "Verify the schema for the correct column name."
    - **Solution:** "Replace 'age' with 'birthdate'."
    - **Verification:** "Confirm the change using `SHOW COLUMNS FROM users;`."

    ---

    ### **Example Output:**
    ```sql
    SELECT name, birthdate FROM users;
    ```

    ---

    ### **Guidelines for SQL Correction:**
    1. **Analyze the Fix Instructions:**
       - Identify the exact SQL elements to modify (column names, table names, syntax issues, etc.).

    2. **Apply the Solution:**
       - Make the necessary corrections to resolve the error.
       - Ensure compatibility with the SQL dialect being used (MySQL, PostgreSQL, etc.).

    3. **Validate Syntax & Structure:**
       - Ensure the corrected query follows proper SQL syntax.
       - Check for missing clauses (`GROUP BY`, `WHERE`, etc.).

    4. **Ensure Logical Accuracy:**
       - If replacing a column/table name, confirm it exists in the schema.
       - Ensure datatype consistency (e.g., avoid casting errors).

    ---

    **Best Practices:**
    - **Follow SQL best practices** to ensure maintainability and performance.
    - **Handle multiple SQL dialects** by adapting fixes to MySQL, PostgreSQL, etc.
    - **Optimize for clarity and efficiency**, ensuring no unnecessary complexity.
    """

    instruction = dspy.InputField(
        desc="Fix instructions from the Error Reasoning Agent detailing the error and solution."
    )
    generated_sql = dspy.OutputField(
        desc="The corrected SQL query with the issue resolved."
    )
