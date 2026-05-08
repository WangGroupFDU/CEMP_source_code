import os
import glob
from PIL import Image

def resize_and_convert_to_png(input_image_path, output_image_path):
    with Image.open(input_image_path) as img:
        
        original_width, original_height = img.size
        aspect_ratio = original_height / original_width
        new_height = int(105 * aspect_ratio)
        
        
        img_resized = img.resize((105, new_height), Image.Resampling.LANCZOS)
        img_resized.save(output_image_path, format='PNG')

def process_images_in_directory(directory):
    
    extensions = ['jpg', 'jpeg', 'png']
    
    for extension in extensions:
        for image_path in glob.glob(f'{directory}/*.{extension}'):
            
            output_image_path = os.path.splitext(image_path)[0] + '.png'
            print(f'Processing {image_path}...')
            resize_and_convert_to_png(image_path, output_image_path)
            print(f'Saved to {output_image_path}')


current_directory = '.'
process_images_in_directory(current_directory)
