import json
import tempfile
from typing import Dict, Any


class TempFileService:

    @staticmethod
    def create_json_temp_file(data: Dict[str, Any], filename_prefix: str = "temp") -> str:
       
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8',
            prefix=filename_prefix
        )
        json.dump(data, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()

        return temp_file.name

    @staticmethod
    def create_text_temp_file(content: str, suffix: str = ".txt", filename_prefix: str = "temp") -> str:
       
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding='utf-8',
            prefix=filename_prefix
        )
        temp_file.write(content)
        temp_file.close()

        return temp_file.name
