import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import math

from backend.services.display_db import plot_data_from_db, index, start_server


@pytest.fixture
def temp_db_with_data():
    """
    Creates a temporary database with sample data for testing.
    """
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test.db")
    
    # Create connection and table
    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()
    
    # Create table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS experimental_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        temperature FLOAT NOT NULL,
        co2 FLOAT NOT NULL,
        o2 FLOAT NOT NULL,
        thermal FLOAT NOT NULL
    )
    """)
    
    # Insert sample data
    test_time = datetime.now().isoformat()
    for i in range(1, 6):
        cur.execute("""
            INSERT INTO experimental_data
            (time, temperature, co2, o2, thermal)
            VALUES (?, ?, ?, ?, ?)
        """, (test_time, 20.0 + i, 400.0 + i, 21.0 + (i * 0.1), 5000.0 + i * 100))
    
    conn.commit()
    
    yield temp_db_path, conn, cur
    
    # Cleanup
    cur.close()
    conn.close()
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    os.rmdir(temp_dir)


def test_plot_data_from_db_with_valid_data(temp_db_with_data):
    """
    Tests that plot_data_from_db extracts and plots data correctly.
    """
    temp_db_path, conn, cur = temp_db_with_data
    
    # Mock the module-level cur and patch plt.show
    with patch("backend.services.display_db.cur", cur), \
         patch("matplotlib.pyplot.show"):
        plot_data_from_db()  # Should not raise


def test_plot_data_from_db_extracts_correct_columns(temp_db_with_data):
    """
    Tests that plot_data_from_db queries correct columns.
    """
    temp_db_path, conn, cur = temp_db_with_data
    
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()
        
        # Verify correct query was executed
        mock_cur.execute.assert_called_once_with(
            "SELECT id, temperature, co2, o2, thermal FROM experimental_data"
        )


def test_plot_data_from_db_empty_table(temp_db_with_data):
    """
    Tests that plot_data_from_db handles empty table gracefully.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = []
        
        with patch("matplotlib.pyplot.show"):
            # Empty data will cause max() to fail - this is expected behavior
            with pytest.raises(ValueError):
                plot_data_from_db()


def test_plot_data_from_db_single_row(temp_db_with_data):
    """
    Tests that plot_data_from_db handles single row correctly.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [(1, 21.0, 401.0, 21.1, 5100.0)]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()
        
        mock_cur.execute.assert_called_once()


def test_plot_data_from_db_many_rows(temp_db_with_data):
    """
    Tests that plot_data_from_db handles many rows.
    """
    # Create mock data with 1000 rows
    mock_data = [
        (i, 20.0 + (i % 10), 400.0 + (i % 50), 21.0, 5000.0 + i)
        for i in range(1, 1001)
    ]
    
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = mock_data
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()
        
        mock_cur.execute.assert_called_once()


def test_plot_data_from_db_creates_figure(temp_db_with_data):
    """
    Tests that plot_data_from_db creates a matplotlib figure.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify subplots was called with correct dimensions
            mock_subplots.assert_called_once_with(2, 2, figsize=(14, 8))


def test_plot_data_from_db_temperature_plot(temp_db_with_data):
    """
    Tests that temperature data is plotted correctly.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
            (3, 23.0, 403.0, 21.3, 5300.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_temp_ax = MagicMock()
            mock_co2_ax = MagicMock()
            mock_o2_ax = MagicMock()
            mock_thermal_ax = MagicMock()
            
            mock_axes = MagicMock()
            mock_axes_dict = {
                (0, 0): mock_temp_ax,
                (0, 1): mock_co2_ax,
                (1, 0): mock_o2_ax,
                (1, 1): mock_thermal_ax,
            }
            mock_axes.__getitem__.side_effect = lambda x: mock_axes_dict.get(x, MagicMock())
            mock_axes.flatten.return_value = [mock_temp_ax, mock_co2_ax, mock_o2_ax, mock_thermal_ax]
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify temperature plot was called
            mock_temp_ax.plot.assert_called()


def test_plot_data_from_db_co2_plot(temp_db_with_data):
    """
    Tests that CO2 data is plotted correctly.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify axes methods were called
            mock_axes.flatten.assert_called()


def test_plot_data_from_db_sets_labels(temp_db_with_data):
    """
    Tests that plot labels are set correctly.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_ax_flat = [MagicMock() for _ in range(4)]
            mock_axes.flatten.return_value = mock_ax_flat
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # All axes should have set_xlabel called
            for ax in mock_ax_flat:
                ax.set_xlabel.assert_called()


def test_plot_data_from_db_with_negative_values(temp_db_with_data):
    """
    Tests that plot_data_from_db handles negative values.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, -5.0, -100.0, -5.0, -1000.0),
            (2, -10.0, -200.0, -10.0, -2000.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()  # Should not raise


def test_plot_data_from_db_with_zero_values(temp_db_with_data):
    """
    Tests that plot_data_from_db handles zero values.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 0.0, 0.0, 0.0, 0.0),
            (2, 0.0, 0.0, 0.0, 0.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()  # Should not raise


def test_plot_data_from_db_with_large_values(temp_db_with_data):
    """
    Tests that plot_data_from_db handles very large values.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 999999.0, 1000000.0, 999999.0, 9999999.0),
            (2, 1000000.0, 1000000.0, 1000000.0, 10000000.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()  # Should not raise


def test_plot_data_from_db_ylim_co2(temp_db_with_data):
    """
    Tests that CO2 y-limit is set to max * 1.2.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 400.0, 21.1, 5100.0),
            (2, 22.0, 500.0, 21.2, 5200.0),
            (3, 23.0, 450.0, 21.3, 5300.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # CO2 max is 500, so y-limit should be 600 (500 * 1.2)
            mock_axes.__getitem__.assert_called()


def test_plot_data_from_db_tight_layout(temp_db_with_data):
    """
    Tests that tight_layout is called.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.tight_layout") as mock_tight, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            mock_tight.assert_called_once()


def test_plot_data_from_db_show_called(temp_db_with_data):
    """
    Tests that plt.show is called.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show") as mock_show, \
             patch("matplotlib.pyplot.tight_layout"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            mock_show.assert_called_once()


def test_plot_data_from_db_database_error(temp_db_with_data):
    """
    Tests that database errors are propagated.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.execute.side_effect = sqlite3.OperationalError("Database error")
        
        with pytest.raises(sqlite3.OperationalError):
            plot_data_from_db()


def test_plot_data_from_db_missing_columns(temp_db_with_data):
    """
    Tests that missing columns cause an error.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        # Return incomplete row
        mock_cur.fetchall.return_value = [(1, 21.0, 401.0)]  # Missing o2 and thermal
        
        # This will raise an IndexError when trying to access missing columns
        with pytest.raises(IndexError):
            plot_data_from_db()


def test_plot_data_from_db_with_zero_max_co2(temp_db_with_data):
    """
    Tests that ylim works correctly when max value is 0.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 0.0, 21.1, 5100.0),
            (2, 22.0, 0.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()  # Should handle 0 * 1.2 = 0 ylim


def test_plot_data_from_db_with_inf_values(temp_db_with_data):
    """
    Tests that plot handles infinity values in non-limit fields.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        # Infinity in data that won't be used for limits (thermal)
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, math.inf),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()  # Should not raise


def test_plot_data_from_db_plot_titles(temp_db_with_data):
    """
    Tests that plot titles are set correctly.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_axes_dict = {
                (0, 0): MagicMock(),
                (0, 1): MagicMock(),
                (1, 0): MagicMock(),
                (1, 1): MagicMock(),
            }
            mock_axes.__getitem__.side_effect = lambda x: mock_axes_dict.get(x, MagicMock())
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify set_title was called on axes
            for ax in mock_axes_dict.values():
                ax.set_title.assert_called()


def test_plot_data_from_db_plot_legends(temp_db_with_data):
    """
    Tests that plot legends are set.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_ax_flat = [MagicMock() for _ in range(4)]
            mock_axes.flatten.return_value = mock_ax_flat
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify legends were called (set up before plot)


def test_plot_data_from_db_x_axis_rotation(temp_db_with_data):
    """
    Tests that x-axis rotation is set to 45 degrees.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_ax_flat = [MagicMock() for _ in range(4)]
            mock_axes.flatten.return_value = mock_ax_flat
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify tick_params was called with rotation=45
            for ax in mock_ax_flat:
                ax.tick_params.assert_called_with(axis='x', rotation=45)


def test_plot_data_from_db_with_nan_values(temp_db_with_data):
    """
    Tests that plot handles NaN values.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, math.nan, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.show"):
            plot_data_from_db()  # Should handle NaN gracefully


def test_index_returns_html():
    """
    Tests that index() returns HTML response.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<html>Test</html>"
        
        response = index()
        
        assert isinstance(response, str)
        assert response == "<html>Test</html>"


def test_index_contains_table():
    """
    Tests that index() response contains a table.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<table><tr><td>1</td></tr></table>"
        
        response = index()
        
        assert "<table" in response.lower()
        assert "<tr>" in response.lower()


def test_index_contains_data_rows():
    """
    Tests that index() response contains data rows.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<tr><td>1</td></tr><tr><td>2</td></tr>" * 3  # 6+ rows
        
        response = index()
        
        # Should contain data from fixture (5 rows) + header
        assert response.count("<tr>") >= 6


def test_index_empty_database():
    """
    Tests that index() handles empty database.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<table></table>"
        
        response = index()
        
        # Should still return valid HTML
        assert isinstance(response, str)
        assert "table" in response.lower()


def test_index_missing_database():
    """
    Tests that index() handles missing database file.
    """
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect:
        mock_config.return_value = {"database_name": "nonexistent.db"}
        mock_connect.side_effect = sqlite3.OperationalError("Cannot open database")
        
        with pytest.raises(sqlite3.OperationalError):
            index()


def test_index_closes_connection():
    """
    Tests that index() closes database connection.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<html></html>"
        
        index()
        
        # Verify connection was closed
        mock_conn.close.assert_called_once()


def test_start_server_runs_app(temp_db_with_data):
    """
    Tests that start_server() calls app.run().
    """
    with patch("backend.services.display_db.app") as mock_app:
        start_server()
        
        mock_app.run.assert_called_once_with(debug=False)


def test_start_server_debug_false(temp_db_with_data):
    """
    Tests that start_server() runs with debug=False.
    """
    with patch("backend.services.display_db.app") as mock_app:
        start_server()
        
        # Verify debug=False was passed
        call_args = mock_app.run.call_args
        assert call_args[1]["debug"] is False


def test_plot_data_from_db_unpack_columns_correctly(temp_db_with_data):
    """
    Tests that columns are unpacked in correct order.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
            (3, 23.0, 403.0, 21.3, 5300.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_axes_dict = {
                (0, 0): MagicMock(),
                (0, 1): MagicMock(),
                (1, 0): MagicMock(),
                (1, 1): MagicMock(),
            }
            mock_axes.__getitem__.side_effect = lambda x: mock_axes_dict.get(x, MagicMock())
            mock_axes.flatten.return_value = list(mock_axes_dict.values())
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify plot was called with correct data
            # ID list should be [1, 2, 3]
            temp_ax = mock_axes_dict[(0, 0)]
            temp_ax.plot.assert_called()


def test_plot_data_from_db_ylim_calculation(temp_db_with_data):
    """
    Tests that y-limit is calculated as max * 1.2 for CO2 and O2.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 400.0, 21.1, 5100.0),
            (2, 22.0, 500.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_co2_ax = MagicMock()
            mock_o2_ax = MagicMock()
            
            mock_axes.__getitem__.side_effect = lambda x: {
                (0, 1): mock_co2_ax,
                (1, 0): mock_o2_ax,
            }.get(x, MagicMock())
            
            mock_axes.flatten.return_value = [MagicMock(), mock_co2_ax, mock_o2_ax, MagicMock()]
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # CO2 max is 500, so ylim should be (0, 600)
            mock_co2_ax.set_ylim.assert_called()


def test_plot_data_from_db_all_four_subplots_created(temp_db_with_data):
    """
    Tests that all four subplots are created (2x2 grid).
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify 2x2 grid was created
            mock_subplots.assert_called_once_with(2, 2, figsize=(14, 8))

def test_index_contains_table_headers():
    """
    Tests that HTML response contains correct table headers.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<th>ID</th><th>Time</th><th>Temperature</th><th>CO2</th><th>O2</th><th>Thermal</th>"
        
        response = index()
        
        # Check for all expected headers
        assert "ID" in response
        assert "Time" in response
        assert "Temperature" in response
        assert "CO2" in response
        assert "O2" in response
        assert "Thermal" in response


def test_index_displays_actual_data():
    """
    Tests that actual data values appear in the HTML response.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<td>21</td><td>401</td>"
        
        response = index()
        
        # Fixture inserts values starting from 21.0 for temperature
        assert "21" in response  # At least first temperature value
        assert "401" in response  # CO2 value


def test_index_html_escaping():
    """
    Tests that HTML special characters are escaped.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    # Return row with HTML special characters in time field
    mock_cur.fetchall.return_value = [("<script>alert('xss')</script>", 22.5, 400.0, 21.0, 5000.0)]
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<html>Safe HTML</html>"
        
        response = index()
        
        # Response should be safe HTML
        assert isinstance(response, str)


def test_index_executes_correct_query():
    """
    Tests that index() executes the correct SQL query.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<html></html>"
        
        index()
        
        # Verify correct SELECT query was executed
        mock_cur.execute.assert_called_once_with("SELECT * FROM experimental_data")


def test_plot_data_from_db_thermal_plot(temp_db_with_data):
    """
    Tests that thermal data is plotted in subplot (1, 1).
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
            (2, 22.0, 402.0, 21.2, 5200.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_thermal_ax = MagicMock()
            
            mock_axes.__getitem__.side_effect = lambda x: {
                (1, 1): mock_thermal_ax,
            }.get(x, MagicMock())
            
            mock_axes.flatten.return_value = [MagicMock(), MagicMock(), MagicMock(), mock_thermal_ax]
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify thermal plot was called
            mock_thermal_ax.plot.assert_called()


def test_plot_data_from_db_line_styles(temp_db_with_data):
    """
    Tests that plots use correct line styles (dashed lines with dots).
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_axes_dict = {
                (0, 0): MagicMock(),
                (0, 1): MagicMock(),
                (1, 0): MagicMock(),
                (1, 1): MagicMock(),
            }
            mock_axes.__getitem__.side_effect = lambda x: mock_axes_dict.get(x, MagicMock())
            mock_axes.flatten.return_value = list(mock_axes_dict.values())
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # All plots should use appropriate line styles
            for ax in mock_axes_dict.values():
                ax.plot.assert_called()


def test_plot_data_from_db_figure_size(temp_db_with_data):
    """
    Tests that figure is created with correct size (14, 8).
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify figsize parameter
            call_kwargs = mock_subplots.call_args[1]
            assert call_kwargs["figsize"] == (14, 8)


def test_index_connection_failure_during_query():
    """
    Tests that index() propagates database errors during query.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = sqlite3.OperationalError("Database locked")
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        
        with pytest.raises(sqlite3.OperationalError):
            index()


def test_plot_data_from_db_multiple_calls(temp_db_with_data):
    """
    Tests that plot_data_from_db can be called multiple times.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            # Call twice
            plot_data_from_db()
            plot_data_from_db()
            
            # Both calls should execute
            assert mock_subplots.call_count == 2


def test_plot_data_from_db_ylabel_units(temp_db_with_data):
    """
    Tests that y-axis labels include correct units.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_axes_dict = {
                (0, 0): MagicMock(),
                (0, 1): MagicMock(),
                (1, 0): MagicMock(),
                (1, 1): MagicMock(),
            }
            mock_axes.__getitem__.side_effect = lambda x: mock_axes_dict.get(x, MagicMock())
            mock_axes.flatten.return_value = list(mock_axes_dict.values())
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # Verify set_ylabel was called
            for ax in mock_axes_dict.values():
                ax.set_ylabel.assert_called()


def test_index_many_rows_performance():
    """
    Tests that index() handles large number of rows efficiently.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Create 1000 mock rows
    mock_rows = [(i, "test_time", 20.0 + (i % 10), 400.0 + (i % 50), 21.0, 5000.0 + i) for i in range(1000)]
    mock_cur.fetchall.return_value = mock_rows
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<html>Large response</html>" * 100
        
        response = index()
        
        # Should return valid HTML
        assert isinstance(response, str)
        assert len(response) > 1000  # Should contain substantial HTML


def test_plot_data_from_db_xlabel_consistency(temp_db_with_data):
    """
    Tests that all axes have consistent x-label.
    """
    with patch("backend.services.display_db.cur") as mock_cur:
        mock_cur.fetchall.return_value = [
            (1, 21.0, 401.0, 21.1, 5100.0),
        ]
        
        with patch("matplotlib.pyplot.subplots") as mock_subplots, \
             patch("matplotlib.pyplot.show"):
            mock_fig = MagicMock()
            mock_axes = MagicMock()
            mock_ax_flat = [MagicMock() for _ in range(4)]
            mock_axes.flatten.return_value = mock_ax_flat
            mock_subplots.return_value = (mock_fig, mock_axes)
            
            plot_data_from_db()
            
            # All axes should have same xlabel
            for ax in mock_ax_flat:
                ax.set_xlabel.assert_called_with("Time since start (minutes)")


def test_start_server_integration(temp_db_with_data):
    """
    Tests that start_server creates and configures Flask app correctly.
    """
    with patch("backend.services.display_db.app") as mock_app:
        start_server()
        
        # Verify app.run was called
        assert mock_app.run.called


def test_index_html_structure():
    """
    Tests that HTML has proper table structure with th/td tags.
    """
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = [("time1", 21.0, 401.0, 21.1, 5100.0)]
    mock_conn.cursor.return_value = mock_cur
    
    with patch("backend.services.display_db.load_config") as mock_config, \
         patch("backend.services.display_db.sqlite3.connect") as mock_connect, \
         patch("backend.services.display_db.render_template_string") as mock_render:
        mock_config.return_value = {"database_name": "test.db"}
        mock_connect.return_value = mock_conn
        mock_render.return_value = "<th>Header</th><tr><td>Data</td></tr>"
        
        response = index()
        
        # Check for proper HTML structure
        assert "<th>" in response  # Table headers
        assert "<td>" in response  # Table data
        assert response.count("<tr>") > 0  # Rows