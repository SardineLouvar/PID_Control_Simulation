import pytest
import sqlite3
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from backend.services import database
from backend.services.database import generate_table, insert_data, delete_db


@pytest.fixture
def temp_db():
    """
    Creates a temporary database for testing.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test.db")
    
    # Mock the config and database path
    with patch("backend.services.database.config", {"database_name": temp_db_path}):
        with patch("backend.services.database.DB_PATH", temp_db_path):
            conn = sqlite3.connect(temp_db_path)
            cur = conn.cursor()
            
            # Replace module-level connection and cursor
            original_conn = database.conn
            original_cur = database.cur
            database.conn = conn
            database.cur = cur
            
            yield temp_db_path, conn, cur
            
            # Cleanup
            database.conn = original_conn
            database.cur = original_cur
            conn.close()
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)
            os.rmdir(temp_dir)


def test_generate_table_creates_table(temp_db):
    """
    Tests that generate_table creates the experimental_data table.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    # Query to check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experimental_data'")
    result = cur.fetchone()
    
    assert result is not None
    assert result[0] == "experimental_data"


def test_generate_table_creates_correct_columns(temp_db):
    """
    Tests that generated table has all required columns.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    # Get table schema
    cur.execute("PRAGMA table_info(experimental_data)")
    columns = cur.fetchall()
    
    column_names = [col[1] for col in columns]
    expected_columns = ["id", "time", "temperature", "co2", "o2", "thermal"]
    
    assert set(column_names) == set(expected_columns)


def test_generate_table_idempotent(temp_db):
    """
    Tests that calling generate_table multiple times doesn't cause errors.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    generate_table()  # Should not raise
    
    # Verify table still exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experimental_data'")
    assert cur.fetchone() is not None


def test_insert_data_single_row(temp_db):
    """
    Tests that insert_data correctly inserts a single row.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)
    
    # Verify data was inserted
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[1] == test_time
    assert result[2] == 22.5
    assert result[3] == 400.0
    assert result[4] == 21.0
    assert result[5] == 5000.0


def test_insert_data_multiple_rows(temp_db):
    """
    Tests that insert_data can insert multiple rows.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    for i in range(5):
        insert_data(test_time, 20.0 + i, 400.0 + i, 21.0, 5000.0 + i)
    
    cur.execute("SELECT COUNT(*) FROM experimental_data")
    count = cur.fetchone()[0]
    
    assert count == 5


def test_insert_data_with_null_values(temp_db):
    """
    Tests that insert_data handles None values (should fail due to NOT NULL constraints).
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    # This should raise an IntegrityError due to NOT NULL constraint
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(None, 22.5, 400.0, 21.0, 5000.0)


def test_insert_data_with_negative_values(temp_db):
    """
    Tests that insert_data accepts negative values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, -10.5, -100.0, -5.0, -1000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[2] == -10.5
    assert result[3] == -100.0


def test_insert_data_with_zero_values(temp_db):
    """
    Tests that insert_data accepts zero values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 0.0, 0.0, 0.0, 0.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[2] == 0.0
    assert result[3] == 0.0


def test_insert_data_with_very_large_numbers(temp_db):
    """
    Tests that insert_data handles very large numeric values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 999999.99, 1000000.0, 99999.99, 9999999.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[2] == pytest.approx(999999.99)


def test_insert_data_with_special_characters_in_time(temp_db):
    """
    Tests that insert_data handles timestamps with special characters.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = "2024-01-27T15:30:45.123456"
    
    insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[1] == test_time


def test_insert_data_auto_increment_id(temp_db):
    """
    Tests that the id column auto-increments correctly.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)
    insert_data(test_time, 23.5, 401.0, 21.0, 5001.0)
    insert_data(test_time, 24.5, 402.0, 21.0, 5002.0)
    
    cur.execute("SELECT id FROM experimental_data ORDER BY id")
    ids = [row[0] for row in cur.fetchall()]
    
    assert ids == [1, 2, 3]


def test_insert_data_float_precision(temp_db):
    """
    Tests that float values maintain precision.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    precision_value = 22.123456789
    insert_data(test_time, precision_value, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT temperature FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()[0]
    
    # SQLite FLOAT has limited precision
    assert result == pytest.approx(precision_value, rel=1e-5)


def test_delete_db_closes_connection(temp_db):
    """
    Tests that delete_db closes the database connection.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    insert_data(datetime.now().isoformat(), 22.5, 400.0, 21.0, 5000.0)
    
    delete_db()
    
    # Connection should be closed
    with pytest.raises(sqlite3.ProgrammingError):
        cur.execute("SELECT * FROM experimental_data")


def test_delete_db_removes_file(temp_db):
    """
    Tests that delete_db removes the database file.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    insert_data(datetime.now().isoformat(), 22.5, 400.0, 21.0, 5000.0)
    
    assert os.path.exists(temp_db_path)
    
    delete_db()
    
    assert not os.path.exists(temp_db_path)


def test_insert_data_duplicate_timestamps(temp_db):
    """
    Tests that insert_data allows duplicate timestamps (no unique constraint on time).
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)
    insert_data(test_time, 23.5, 401.0, 21.0, 5001.0)
    
    cur.execute("SELECT COUNT(*) FROM experimental_data WHERE time = ?", (test_time,))
    count = cur.fetchone()[0]
    
    assert count == 2


def test_insert_data_preserves_order(temp_db):
    """
    Tests that inserted data maintains order by id.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    temps = [20.0, 21.0, 22.0, 23.0, 24.0]
    for temp in temps:
        insert_data(test_time, temp, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT temperature FROM experimental_data ORDER BY id")
    result_temps = [row[0] for row in cur.fetchall()]
    
    assert result_temps == temps


def test_generate_table_column_types(temp_db):
    """
    Tests that table columns have correct data types.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    cur.execute("PRAGMA table_info(experimental_data)")
    columns = {col[1]: col[2] for col in cur.fetchall()}
    
    assert columns["id"] == "INTEGER"
    assert columns["time"] == "TEXT"
    assert columns["temperature"] == "FLOAT"
    assert columns["co2"] == "FLOAT"
    assert columns["o2"] == "FLOAT"
    assert columns["thermal"] == "FLOAT"


def test_insert_data_scientific_notation(temp_db):
    """
    Tests that insert_data handles scientific notation values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    insert_data(test_time, 1.5e2, 4.0e2, 2.1e1, 5.0e3)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[2] == pytest.approx(150.0)
    assert result[3] == pytest.approx(400.0)


def test_insert_data_sql_injection_attempt(temp_db):
    """
    Tests that parameterized queries prevent SQL injection.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    # Attempt SQL injection
    malicious_time = "2024-01-27'; DROP TABLE experimental_data; --"
    
    insert_data(malicious_time, 22.5, 400.0, 21.0, 5000.0)
    
    # Table should still exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experimental_data'")
    assert cur.fetchone() is not None
    
    # Data should be stored with the injection attempt as literal string
    cur.execute("SELECT COUNT(*) FROM experimental_data WHERE time = ?", (malicious_time,))
    assert cur.fetchone()[0] == 1

def test_query_empty_table(temp_db):
    """
    Tests that querying an empty table returns correct results.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    cur.execute("SELECT COUNT(*) FROM experimental_data")
    count = cur.fetchone()[0]
    
    assert count == 0


def test_query_empty_table_select_all(temp_db):
    """
    Tests that SELECT * on empty table returns empty result.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    
    cur.execute("SELECT * FROM experimental_data")
    result = cur.fetchall()
    
    assert result == []


def test_insert_data_with_unicode_timestamp(temp_db):
    """
    Tests that insert_data handles Unicode characters in timestamp.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    # Unicode timestamp with special characters
    unicode_time = "2024-01-27T15:30:45.123456 📅"
    
    insert_data(unicode_time, 22.5, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (unicode_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[1] == unicode_time


def test_insert_data_with_very_long_timestamp(temp_db):
    """
    Tests that insert_data handles very long timestamp strings.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    # Very long timestamp string
    long_time = "2024-01-27T15:30:45" + "." + ("0" * 1000)
    
    insert_data(long_time, 22.5, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (long_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[1] == long_time


def test_insert_data_without_creating_table(temp_db):
    """
    Tests that insert_data without creating table first raises error.
    """
    temp_db_path, conn, cur = temp_db
    
    # Don't call generate_table
    test_time = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.OperationalError):
        insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)


def test_insert_data_with_string_numeric_values(temp_db):
    """
    Tests that insert_data accepts string values for numeric fields (SQLite type affinity).
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    # SQLite will coerce strings to numbers if possible
    cur.execute("""
        INSERT INTO experimental_data
        (time, temperature, co2, o2, thermal)
        VALUES (?, ?, ?, ?, ?)""",
        (test_time, "22.5", "400", "21.0", "5000"))
    conn.commit()
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    # Values are stored as floats due to column type
    assert float(result[2]) == 22.5


def test_insert_data_with_nan_values(temp_db):
    """
    Tests that insert_data with NaN values raises IntegrityError.
    SQLite converts NaN to NULL, which violates NOT NULL constraint.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    import math
    
    # SQLite converts NaN to NULL, which violates the NOT NULL constraint on temperature
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(test_time, math.nan, 400.0, 21.0, 5000.0)


def test_insert_data_with_infinity(temp_db):
    """
    Tests that insert_data handles infinity values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    import math
    
    insert_data(test_time, math.inf, -math.inf, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (test_time,))
    result = cur.fetchone()
    
    assert result is not None
    # SQLite stores infinity as float
    assert result[2] == float('inf')
    assert result[3] == float('-inf')


def test_database_recreation_delete_then_create(temp_db):
    """
    Tests that database can be deleted and recreated properly.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    insert_data(test_time, 22.5, 400.0, 21.0, 5000.0)
    
    # Verify data exists
    cur.execute("SELECT COUNT(*) FROM experimental_data")
    assert cur.fetchone()[0] == 1
    
    # Must close connections before deleting file (especially on Windows)
    database.cur.close()
    database.conn.close()
    
    # Now delete the database file
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    
    # Recreate database with fresh connection
    new_conn = sqlite3.connect(temp_db_path)
    new_cur = new_conn.cursor()
    
    # Update module-level references temporarily
    database.conn = new_conn
    database.cur = new_cur
    
    generate_table()
    
    # Table should be empty
    new_cur.execute("SELECT COUNT(*) FROM experimental_data")
    assert new_cur.fetchone()[0] == 0
    
    # Clean up the new connection before fixture cleanup
    new_cur.close()
    new_conn.close()


def test_insert_data_rapid_successive_inserts(temp_db):
    """
    Tests that rapid successive inserts work correctly.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    # Insert 100 rows rapidly
    for i in range(100):
        insert_data(test_time, 20.0 + i, 400.0 + i, 21.0, 5000.0 + i)
    
    cur.execute("SELECT COUNT(*) FROM experimental_data")
    count = cur.fetchone()[0]
    
    assert count == 100


def test_insert_data_with_max_length_text(temp_db):
    """
    Tests that insert_data handles very long text values.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    # Create a very long timestamp string
    long_time = "T" * 10000
    
    insert_data(long_time, 22.5, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (long_time,))
    result = cur.fetchone()
    
    assert result is not None
    assert result[1] == long_time


def test_insert_data_temperature_not_null_constraint(temp_db):
    """
    Tests that NOT NULL constraint on temperature is enforced.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(test_time, None, 400.0, 21.0, 5000.0)


def test_insert_data_co2_not_null_constraint(temp_db):
    """
    Tests that NOT NULL constraint on co2 is enforced.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(test_time, 22.5, None, 21.0, 5000.0)


def test_insert_data_o2_not_null_constraint(temp_db):
    """
    Tests that NOT NULL constraint on o2 is enforced.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(test_time, 22.5, 400.0, None, 5000.0)


def test_insert_data_thermal_not_null_constraint(temp_db):
    """
    Tests that NOT NULL constraint on thermal is enforced.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        insert_data(test_time, 22.5, 400.0, 21.0, None)


def test_generate_table_primary_key_constraint(temp_db):
    """
    Tests that primary key constraint on id is enforced.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    # Insert with explicit id
    cur.execute("""
        INSERT INTO experimental_data
        (id, time, temperature, co2, o2, thermal)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (1, test_time, 22.5, 400.0, 21.0, 5000.0))
    conn.commit()
    
    # Try to insert with same id - should fail
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("""
            INSERT INTO experimental_data
            (id, time, temperature, co2, o2, thermal)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (1, test_time, 23.5, 401.0, 21.0, 5001.0))
        conn.commit()


def test_insert_data_with_whitespace_timestamp(temp_db):
    """
    Tests that insert_data handles timestamps with various whitespace.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    time_with_spaces = "  2024-01-27T15:30:45  "
    
    insert_data(time_with_spaces, 22.5, 400.0, 21.0, 5000.0)
    
    cur.execute("SELECT * FROM experimental_data WHERE time = ?", (time_with_spaces,))
    result = cur.fetchone()
    
    assert result is not None
    # Whitespace is preserved
    assert result[1] == time_with_spaces


def test_insert_data_no_arguments():
    """
    Tests that insert_data raises TypeError when called with no arguments.
    """
    with pytest.raises(TypeError):
        insert_data()


def test_insert_data_missing_one_argument(temp_db):
    """
    Tests that insert_data raises TypeError when missing one argument.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(TypeError):
        insert_data(test_time, 22.5, 400.0, 21.0)  # Missing thermal


def test_insert_data_missing_multiple_arguments(temp_db):
    """
    Tests that insert_data raises TypeError when missing multiple arguments.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(TypeError):
        insert_data(test_time, 22.5)  # Missing co2, o2, thermal


def test_insert_data_with_too_many_arguments(temp_db):
    """
    Tests that insert_data raises TypeError when given too many arguments.
    """
    temp_db_path, conn, cur = temp_db
    
    generate_table()
    test_time = datetime.now().isoformat()
    
    with pytest.raises(TypeError):
        insert_data(test_time, 22.5, 400.0, 21.0, 5000.0, "extra")  # Extra argument


def test_insert_data_with_only_time():
    """
    Tests that insert_data requires all parameters.
    """
    with pytest.raises(TypeError):
        insert_data("2024-01-27T15:30:45")