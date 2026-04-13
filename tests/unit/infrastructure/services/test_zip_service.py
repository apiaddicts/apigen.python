import os
import tempfile
import zipfile
import shutil
import pytest
from src.infrastructure.services.zip_service import ZipService

class TestZipService:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        
        os.makedirs(os.path.join(temp_dir, "subdir"))
        
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("content1")
            
        with open(os.path.join(temp_dir, "subdir", "file2.txt"), "w") as f:
            f.write("content2")
            
        yield temp_dir
        
        shutil.rmtree(temp_dir)

    def test_compress_directory_success(self, temp_dir):
        zip_path = ZipService.compress_directory(temp_dir, "test_archive")
        
        try:
            assert os.path.exists(zip_path)
            assert zip_path.endswith("test_archive.zip")
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                assert "file1.txt" in file_list
                assert os.path.join("subdir", "file2.txt") in file_list
                
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def test_compress_directory_invalid_path(self):
        with pytest.raises(ValueError, match="El directorio fuente no existe"):
            ZipService.compress_directory("/path/that/does/not/exist")
