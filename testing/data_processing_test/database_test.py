import sqlite3

import pytest
from unittest.mock import patch, MagicMock
from src.data_processing import database
from src.utility.settings_manager import Settings


def setup_database(cursor):
    # Create CRKN and local file name tables to store file names
    cursor.execute("""CREATE TABLE CRKN_file_names (file_name TEXT);""")
    cursor.execute("""CREATE TABLE local_file_names (file_name TEXT);""")

    # Define file names representing table names for CRKN and local data
    crkn_file_names = ['crkn_data_2021', 'crkn_data_2022']
    local_file_names = ['local_data_2021', 'local_data_2022']

    # Insert these file names into the corresponding tables
    for file_name in crkn_file_names:
        cursor.execute("INSERT INTO CRKN_file_names (file_name) VALUES (?);", (file_name,))
    for file_name in local_file_names:
        cursor.execute("INSERT INTO local_file_names (file_name) VALUES (?);", (file_name,))

    # Create tables based on the inserted file names and populate them with test data
    tables_to_create = crkn_file_names + local_file_names
    for table_name in tables_to_create:
        # Create a table for each file name
        cursor.execute(f"""CREATE TABLE {table_name} (
            Title TEXT,
            Platform_eISBN TEXT,
            OCN TEXT,
            Institution TEXT
        );""")

        # Insert test data into each table
        test_data = [
            ('Python Programming Basics', '123-4567890123', 'OCN123456', 'InstitutionA'),
            ('Advanced Python Programming', '123-4567890124', 'OCN123457', 'InstitutionB'),
            ('Data Science with Python', '123-4567890125', 'OCN123458', 'InstitutionA'),
            ('Machine Learning Fundamentals', '123-4567890126', 'OCN123459', 'InstitutionC')
        ]

        for record in test_data:
            cursor.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?, ?);", record)


@patch('src.data_processing.database.sqlite3')
def test_connect_to_database_mock(mock_sqlite3):
    # Set up the mock for sqlite3.connect
    mock_connection = MagicMock()
    mock_sqlite3.connect.return_value = mock_connection
    settings_manager = Settings()

    # Call the function
    connection = database.connect_to_database()

    # Check that sqlite3.connect was called with the correct database name
    mock_sqlite3.connect.assert_called_with(settings_manager.get_setting('database_name'))

    # Check that the return value is the mock connection
    assert connection == mock_connection


def test_close_database():
    # Create a mock object for the connection
    mock_connection = MagicMock()

    # Call the function with the mock connection
    database.close_database(mock_connection)

    # Assert that commit and close were called on the connection
    mock_connection.commit.assert_called_once()
    mock_connection.close.assert_called_once()


def test_create_file_name_tables_when_tables_exist():
    # Create a mock object for the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    # Simulate existing tables
    mock_cursor.execute.return_value.fetchall.return_value = [('CRKN_file_names',), ('local_file_names',)]

    # Call the function with the mock connection
    database.create_file_name_tables(mock_connection)

    # Assert that 'CREATE TABLE' command was not executed
    assert not any("CREATE TABLE" in call[0][0] for call in mock_cursor.execute.call_args_list)


def test_create_file_name_tables_when_tables_do_not_exist():
    # Create a mock object for the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    # Simulate no tables
    mock_cursor.execute.return_value.fetchall.return_value = []

    # Call the function with the mock connection
    database.create_file_name_tables(mock_connection)

    # Assert that 'CREATE TABLE' command was executed
    assert any("CREATE TABLE" in call[0][0] for call in mock_cursor.execute.call_args_list)


def test_get_tables():
    # temporary in-memory database
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE CRKN_file_names (file_name VARCHAR(255));""")
    cursor.execute("""CREATE TABLE local_file_names (file_name VARCHAR(255));""")

    # Insert mock data into tables
    crkn_files = ['CRKN_data1', 'CRKN_data2']
    local_files = ['local_data1', 'local_data2']
    for file in crkn_files:
        cursor.execute("INSERT INTO CRKN_file_names (file_name) VALUES (?);", (file,))
    for file in local_files:
        cursor.execute("INSERT INTO local_file_names (file_name) VALUES (?);", (file,))
    connection.commit()

    # Call get_tables and verify it returns correct table names
    expected_tables = sorted(crkn_files + local_files)
    actual_tables = sorted(database.get_tables(connection))

    assert actual_tables == expected_tables, "get_tables should return all file names from CRKN_file_names and local_file_names"

    connection.close()


def test_search_by_title():
    # temporary in-memory database
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    setup_database(cursor)
    connection.commit()

    # Search for a title containing "Python"
    search_title = "Python"
    results = database.search_by_title(connection, search_title)

    expected_titles = [
        'Python Programming Basics',
        'Advanced Python Programming',
        'Data Science with Python'
    ]
    actual_titles = [result[0] for result in results]

    # Verify that the number of results matches the expected number based on setup
    assert len(results) >= len(
        expected_titles), f"Expected at least {len(expected_titles)} results for 'Python' search, got {len(results)}."

    # Verify that all expected titles are present in the actual titles found by search
    for expected_title in expected_titles:
        assert expected_title in actual_titles, f"Expected title '{expected_title}' not found in search results."

    connection.close()


def test_search_by_ISBN():
    # Create an in-memory database
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    setup_database(cursor)
    connection.commit()

    # Validate get_tables function output
    tables = database.get_tables(connection)
    print("Tables returned by get_tables:", tables)

    # Search for the specific ISBN
    search_isbn = '123-4567890123'
    results = database.search_by_ISBN(connection, search_isbn)

    # Verify the results
    assert len(results) > 0, "Expected at least one result for the ISBN search."
    assert any(
        result[1] == search_isbn for result in results), f"Expected to find ISBN '{search_isbn}' in the search results."

    connection.close()


def test_search_by_OCN():
    # Create an in-memory database
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    setup_database(cursor)
    connection.commit()

    # Search for a specific OCN
    search_ocn = 'OCN123456'
    results = database.search_by_OCN(connection, search_ocn)

    # Verify the results contain the expected OCN and count the matches
    expected_ocn_count = sum(1 for _ in cursor.execute("SELECT * FROM crkn_data_2021 WHERE OCN=?", (search_ocn,))
                             ) + sum(
        1 for _ in cursor.execute("SELECT * FROM crkn_data_2022 WHERE OCN=?", (search_ocn,))
    ) + sum(1 for _ in cursor.execute("SELECT * FROM local_data_2021 WHERE OCN=?", (search_ocn,))
            ) + sum(1 for _ in cursor.execute("SELECT * FROM local_data_2022 WHERE OCN=?", (search_ocn,)))

    assert len(
        results) == expected_ocn_count, f"Expected {expected_ocn_count} results for OCN search, got {len(results)}."
    # Verify results
    for _, _, ocn, _ in results:
        assert ocn == search_ocn, f"Expected OCN '{search_ocn}' in the search results, got '{ocn}'"

    # Close the database connection
    connection.close()


def test_advanced_search_with_and_query():
    # Create an in-memory database
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    setup_database(cursor)
    connection.commit()

    # Prepare the base query with a placeholder for dynamic table names
    base_query = "SELECT * FROM {table_name} WHERE 1=1"  # Starting with a base condition that's always true for AND logic

    # Append condition for titles containing "Python"
    advanced_query = database.add_AND_query("Title", base_query, "%Python%")
    # Append condition for a specific ISBN number
    specific_isbn = "123-4567890124"  # Example ISBN number; adjust as needed based on test data
    advanced_query = database.add_AND_query("Platform_eISBN", advanced_query, specific_isbn)

    # Perform the advanced search
    # The advanced_search function is expected to iterate over each relevant table, replacing {table_name} dynamically
    results = database.advanced_search(connection, advanced_query)

    # Verify the results
    # Expecting results matching both criteria: titles containing "Python" AND the specific ISBN number
    assert len(
        results) > 0, "Expected at least one result matching both criteria for titles containing 'Python' and the specific ISBN number."
    assert all('Python' in result[0] and specific_isbn == result[1] for result in results), \
        "Expected all results to match 'Python' in Title and the specific ISBN number."

    connection.close()


def test_advanced_search_with_or_query():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    setup_database(cursor)  # This populates the database with diverse test data
    connection.commit()

    base_query = "SELECT * FROM {table_name} WHERE 1=0"  # base condition that's always false for OR logic

    # Append condition for titles containing "Python"
    advanced_query = database.add_OR_query("Title", base_query, "%Python%")
    # Append condition for a specific ISBN number
    specific_isbn = "123-4567890124"  # Example ISBN number; adjust as needed based on test data
    advanced_query = database.add_OR_query("Platform_eISBN", advanced_query, specific_isbn)

    # Perform the advanced search
    # The advanced_search function is expected to iterate over each relevant table, replacing {table_name} dynamically
    results = database.advanced_search(connection, advanced_query)

    # Verify the results
    # Expecting results matching any of the criteria: Titles containing "Python" OR specific ISBN number
    assert len(
        results) > 0, "Expected at least one result matching the criteria for titles containing 'Python' or the specific ISBN number."
    assert any('Python' in result[0] or specific_isbn in result[1] for result in results), \
        "Expected at least one result to match 'Python' in Title or the specific ISBN number."

    # Teardown: Close the database connection
    connection.close()
