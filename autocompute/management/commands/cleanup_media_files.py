import os
import time
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Deletes old files from the media folder'

    def handle(self, *args, **kwargs):
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'AutoCompute/QcCompute/Uploads')
        download_dir = os.path.join(settings.MEDIA_ROOT, 'AutoCompute/QcCompute/Downloads')

        
        max_age = 7 * 24 * 60 * 60  

        self.cleanup_directory(upload_dir, max_age)
        self.cleanup_directory(download_dir, max_age)
        self.stdout.write(self.style.SUCCESS('Successfully cleaned up old files.'))

    def cleanup_directory(self, directory, max_age):
        
        current_time = time.time()

        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    os.remove(file_path)
                    self.stdout.write(f'Deleted {file_path}')
            elif os.path.isdir(file_path):
                
                self.cleanup_directory(file_path, max_age)