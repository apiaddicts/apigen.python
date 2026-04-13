import os
import zipfile
from typing import Optional

class ZipService:
    @staticmethod
    def compress_directory(source_dir: str, output_filename: Optional[str] = None) -> str:

        if not os.path.isdir(source_dir):
            raise ValueError(f"El directorio fuente no existe: {source_dir}")

        if not output_filename:
            output_filename = os.path.basename(source_dir.rstrip(os.sep))
            
        if output_filename.lower().endswith('.zip'):
            output_filename = output_filename[:-4]

        output_path = os.path.join(os.path.dirname(source_dir), f"{output_filename}.zip")

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    
        return output_path
