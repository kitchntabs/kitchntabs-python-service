# asset.py
from pdf2image import convert_from_path
from pinoywok.config import config
import os


def pdf2png(id, pdf_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    print(pdf_path)
    images = convert_from_path(pdf_path,300,poppler_path=config.get_poppler_path())
    saved_files = []

    for i, image in enumerate(images):
        file_name = f"{output_folder}/{id}_{i}.png"
        image.save(file_name, "PNG")
        saved_files.append(file_name)
        print("appending file")
        print(file_name)
    print("Images from pdf")
    print(saved_files)
    return saved_files