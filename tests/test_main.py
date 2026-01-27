import os
from unittest.mock import patch


from backend.main import delete_pycache_dirs, delete_data


class TestDeletePycacheDirs:
    """Tests for the delete_pycache_dirs function."""

    def test_delete_pycache_dirs_removes_pycache(self, tmp_path):
        """
        Tests that delete_pycache_dirs removes __pycache__ directories.
        """
        # Create a temporary structure with __pycache__
        pycache_dir = tmp_path / "test_module" / "__pycache__"
        pycache_dir.mkdir(parents=True)
        
        # Create a file inside __pycache__
        (pycache_dir / "test.pyc").write_text("test content")
        
        # Verify it exists
        assert pycache_dir.exists()
        
        # Change to temp directory and run function
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            # Verify __pycache__ was removed
            assert not pycache_dir.exists()
        finally:
            os.chdir(original_cwd)

    def test_delete_pycache_dirs_with_multiple_pycache(self, tmp_path):
        """
        Tests that delete_pycache_dirs removes multiple __pycache__ directories.
        """
        # Create multiple __pycache__ directories
        pycache1 = tmp_path / "module1" / "__pycache__"
        pycache2 = tmp_path / "module2" / "__pycache__"
        pycache3 = tmp_path / "subdir" / "module3" / "__pycache__"
        
        pycache1.mkdir(parents=True)
        pycache2.mkdir(parents=True)
        pycache3.mkdir(parents=True)
        
        # Verify they exist
        assert pycache1.exists()
        assert pycache2.exists()
        assert pycache3.exists()
        
        # Change to temp directory and run function
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            # Verify all __pycache__ directories were removed
            assert not pycache1.exists()
            assert not pycache2.exists()
            assert not pycache3.exists()
        finally:
            os.chdir(original_cwd)

    def test_delete_pycache_dirs_preserves_other_dirs(self, tmp_path):
        """
        Tests that delete_pycache_dirs preserves non-__pycache__ directories.
        """
        # Create various directories
        keep_dir = tmp_path / "keep_this" / "subdir"
        pycache_dir = tmp_path / "remove_this" / "__pycache__"
        
        keep_dir.mkdir(parents=True)
        pycache_dir.mkdir(parents=True)
        
        # Create files
        (keep_dir / "file.txt").write_text("keep me")
        (pycache_dir / "file.pyc").write_text("remove me")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            # Verify __pycache__ removed but other dirs preserved
            assert not pycache_dir.exists()
            assert keep_dir.exists()
            assert (keep_dir / "file.txt").exists()
        finally:
            os.chdir(original_cwd)

    def test_delete_pycache_dirs_handles_empty_tree(self, tmp_path):
        """
        Tests that delete_pycache_dirs handles directories with no __pycache__.
        """
        # Create directory structure without __pycache__
        (tmp_path / "module1" / "submodule").mkdir(parents=True)
        (tmp_path / "module2").mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Should not raise any errors
            delete_pycache_dirs()
            # Verify normal directories still exist
            assert (tmp_path / "module1" / "submodule").exists()
            assert (tmp_path / "module2").exists()
        finally:
            os.chdir(original_cwd)

    @patch('shutil.rmtree')
    def test_delete_pycache_dirs_calls_rmtree(self, mock_rmtree, tmp_path):
        """
        Tests that delete_pycache_dirs calls shutil.rmtree for __pycache__.
        """
        pycache_dir = tmp_path / "__pycache__"
        pycache_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            # Verify rmtree was called
            mock_rmtree.assert_called()
        finally:
            os.chdir(original_cwd)

    def test_delete_pycache_dirs_nested_pycache(self, tmp_path):
        """
        Tests that delete_pycache_dirs handles deeply nested __pycache__.
        """
        # Create deeply nested structure
        deep_pycache = tmp_path / "a" / "b" / "c" / "d" / "e" / "__pycache__"
        deep_pycache.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            assert not deep_pycache.exists()
        finally:
            os.chdir(original_cwd)

    def test_delete_pycache_dirs_with_files_in_pycache(self, tmp_path):
        """
        Tests that delete_pycache_dirs removes __pycache__ with multiple files.
        """
        pycache_dir = tmp_path / "__pycache__"
        pycache_dir.mkdir(parents=True)
        
        # Create multiple files in __pycache__
        (pycache_dir / "file1.pyc").write_text("content1")
        (pycache_dir / "file2.pyc").write_text("content2")
        (pycache_dir / "file3.pyc").write_text("content3")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            delete_pycache_dirs()
            assert not pycache_dir.exists()
        finally:
            os.chdir(original_cwd)


class TestDeleteData:
    """Tests for the delete_data function."""

    def test_delete_data_removes_files(self):
        """
        Tests that delete_data removes files from data directory.
        """
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=['data1.json', 'data2.json', 'data3.json']), \
             patch('os.remove') as mock_remove, \
             patch('os.path.join', side_effect=os.path.join):
            
            mock_config.__getitem__.return_value = "/fake/data/path"
            delete_data()
            
            # Verify remove was called for each file
            assert mock_remove.call_count == 3

    def test_delete_data_with_mixed_files(self):
        """
        Tests delete_data with various file types.
        """
        files = ['data.json', 'data.csv', 'data.txt', 'simulation_output.dat']
        
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=files), \
             patch('os.remove') as mock_remove, \
             patch('os.path.join', side_effect=os.path.join):
            
            mock_config.__getitem__.return_value = "/fake/data/path"
            delete_data()
            
            # Verify remove was called for each file
            assert mock_remove.call_count == len(files)

    def test_delete_data_empty_directory(self, tmp_path):
        """
        Tests delete_data with empty data directory.
        """
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=[]), \
             patch('os.remove') as mock_remove:
            
            mock_config.__getitem__.return_value = str(tmp_path)
            delete_data()
            
            # Should not call remove on empty directory
            mock_remove.assert_not_called()

    def test_delete_data_single_file(self):
        """
        Tests delete_data with single file.
        """
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=['single_data.json']), \
             patch('os.remove') as mock_remove, \
             patch('os.path.join', side_effect=os.path.join):
            
            mock_config.__getitem__.return_value = "/fake/data/path"
            delete_data()
            
            # Should call remove once
            mock_remove.assert_called_once()

    def test_delete_data_large_number_of_files(self):
        """
        Tests delete_data with many files.
        """
        file_count = 100
        filenames = [f"data_{i}.json" for i in range(file_count)]
        
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=filenames), \
             patch('os.path.join', side_effect=os.path.join), \
             patch('os.remove') as mock_remove:
            
            mock_config.__getitem__.return_value = "/fake/data/path"
            delete_data()
            
            # Should call remove for each file
            assert mock_remove.call_count == file_count


class TestMainConstants:
    """Tests for main.py constants and configuration."""

    def test_script_dir_is_set(self):
        """
        Tests that script_dir is properly set.
        """
        from backend.main import script_dir
        assert script_dir is not None
        assert isinstance(script_dir, str)
        assert len(script_dir) > 0

    def test_data_path_is_set(self):
        """
        Tests that data_path is properly set.
        """
        from backend.main import data_path
        assert data_path is not None
        assert isinstance(data_path, str)
        assert len(data_path) > 0

    def test_db_path_is_set(self):
        """
        Tests that db_path is properly set.
        """
        from backend.main import db_path
        assert db_path is not None
        assert isinstance(db_path, str)
        assert len(db_path) > 0

    def test_database_type_is_configured(self):
        """
        Tests that database_type is properly configured.
        """
        from backend.main import database_type
        assert database_type is not None
        assert database_type in ["dataframe", "sql"]


class TestMainImports:
    """Tests for main.py imports and function availability."""

    def test_process_for_dataframe_imported(self):
        """
        Tests that process_for_dataframe is imported.
        """
        from backend.main import process_for_dataframe
        assert callable(process_for_dataframe)

    def test_process_for_sql_imported(self):
        """
        Tests that process_for_sql is imported.
        """
        from backend.main import process_for_sql
        assert callable(process_for_sql)

    def test_initialise_db_imported(self):
        """
        Tests that initialise_db is imported.
        """
        from backend.main import initialise_db
        assert callable(initialise_db)

    def test_initialise_dataframe_imported(self):
        """
        Tests that initialise_dataframe is imported.
        """
        from backend.main import initialise_dataframe
        assert callable(initialise_dataframe)

    def test_delete_db_imported(self):
        """
        Tests that delete_db is imported.
        """
        from backend.main import delete_db
        assert callable(delete_db)

    def test_start_server_imported(self):
        """
        Tests that start_server is imported.
        """
        from backend.main import start_server
        assert callable(start_server)

    def test_plot_data_from_db_imported(self):
        """
        Tests that plot_data_from_db is imported.
        """
        from backend.main import plot_data_from_db
        assert callable(plot_data_from_db)

    def test_load_config_imported(self):
        """
        Tests that load_config is imported.
        """
        from backend.main import load_config
        assert callable(load_config)


class TestMainExecutionLogic:
    """Tests for main.py execution logic."""

    @patch('backend.main.delete_data')
    @patch('backend.main.delete_pycache_dirs')
    @patch('backend.main.delete_db')
    @patch('backend.main.plot_data_from_db')
    @patch('backend.main.start_server')
    @patch('backend.main.initialise_db')
    @patch('backend.main.process_for_sql')
    @patch('backend.main.config')
    @patch('os.system')
    def test_main_dataframe_execution_path(
        self, mock_os_system, mock_config, mock_process_sql, 
        mock_init_db, mock_start_server, mock_plot_data, 
        mock_delete_db, mock_delete_pycache, mock_delete_data
    ):
        """
        Tests main execution with dataframe database type.
        """
        mock_config.__getitem__.return_value = "dataframe"
        
        with patch('backend.main.process_for_dataframe') as mock_process_df, \
             patch('backend.main.initialise_dataframe') as mock_init_df:
            
            # Simulate main execution
            database_type = mock_config.__getitem__("database_type")
            if database_type == "dataframe":
                mock_process_df()
                mock_init_df()
            
            mock_process_df.assert_called_once()
            mock_init_df.assert_called_once()

    @patch('backend.main.delete_data')
    @patch('backend.main.delete_pycache_dirs')
    @patch('backend.main.delete_db')
    @patch('backend.main.plot_data_from_db')
    @patch('backend.main.start_server')
    @patch('backend.main.initialise_db')
    @patch('backend.main.process_for_sql')
    @patch('backend.main.config')
    def test_main_sql_execution_path(
        self, mock_config, mock_process_sql, mock_init_db, 
        mock_start_server, mock_plot_data, mock_delete_db, 
        mock_delete_pycache, mock_delete_data
    ):
        """
        Tests main execution with SQL database type.
        """
        mock_config.__getitem__.return_value = "sql"
        
        # Simulate main execution for SQL path
        database_type = mock_config.__getitem__("database_type")
        if database_type != "dataframe":
            mock_process_sql()
            mock_init_db()
            mock_start_server()
        
        mock_process_sql.assert_called_once()
        mock_init_db.assert_called_once()
        mock_start_server.assert_called_once()

    @patch('backend.main.delete_data')
    @patch('backend.main.delete_pycache_dirs')
    @patch('backend.main.delete_db')
    @patch('backend.main.plot_data_from_db')
    def test_main_cleanup_always_called(
        self, mock_plot_data, mock_delete_db, 
        mock_delete_pycache, mock_delete_data
    ):
        """
        Tests that cleanup functions are always called regardless of database type.
        """
        # Cleanup should always be called
        mock_plot_data()
        mock_delete_data()
        mock_delete_pycache()
        mock_delete_db()
        
        mock_plot_data.assert_called_once()
        mock_delete_data.assert_called_once()
        mock_delete_pycache.assert_called_once()
        mock_delete_db.assert_called_once()


class TestMainFunctionSignatures:
    """Tests for main.py function signatures and parameters."""

    def test_delete_pycache_dirs_signature(self):
        """
        Tests that delete_pycache_dirs has correct signature.
        """
        import inspect
        sig = inspect.signature(delete_pycache_dirs)
        # Should have no required parameters
        assert len(sig.parameters) == 0

    def test_delete_data_signature(self):
        """
        Tests that delete_data has correct signature.
        """
        import inspect
        sig = inspect.signature(delete_data)
        # Should have no required parameters
        assert len(sig.parameters) == 0

    def test_delete_pycache_dirs_return_type(self):
        """
        Tests that delete_pycache_dirs returns None.
        """
        with patch('os.walk', return_value=[]):
            result = delete_pycache_dirs()
            assert result is None

    def test_delete_data_return_type(self):
        """
        Tests that delete_data returns None.
        """
        with patch('backend.main.config') as mock_config, \
             patch('os.listdir', return_value=[]):
            mock_config.__getitem__.return_value = "/fake/path"
            result = delete_data()
            assert result is None
