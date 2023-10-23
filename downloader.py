import time as tm
import requests
import re
import os
import traceback
from tqdm import tqdm
import threading

def download_part(url, headers, output_path, part_num, part_size, chunk_size):
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60)

        with open(output_path, 'wb') as part_file:
            progress_bar = tqdm(total=part_size, unit='B', unit_scale=True, unit_divisor=1024)
            for data in response.iter_content(chunk_size=chunk_size):
                part_file.write(data)
                progress_bar.update(len(data))
            progress_bar.close()
    except Exception as err:
        print(f"Error while downloading part {part_num}: {err}")

def download_file(url, output_folder=".", num_parts=3):
    try:
        response = requests.head(url)
        total_size = int(response.headers.get('content-length', 0))

        if total_size == 0:
            print("File size is not available. Cannot download.")
            return None

        chunk_size = 1024  # 1 KB
        part_size = total_size // num_parts

        # Create or clear the output file
        save_path = os.path.join(output_folder, url.split('/')[-1])
        with open(save_path, 'wb') as output_file:
            output_file.seek(total_size - 1)
            output_file.write(b'\0')

        threads = []

        for part_num in range(num_parts):
            start_byte = part_num * part_size
            end_byte = start_byte + part_size if part_num < num_parts - 1 else total_size

            headers = {'Range': f'bytes={start_byte}-{end_byte}'}
            part_output_path = save_path + f'.part{part_num + 1}'
            
            thread = threading.Thread(target=download_part, args=(url, headers, part_output_path, part_num, part_size, chunk_size))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Combine all parts into the final file
        with open(save_path, 'wb') as output_file:
            for part_num in range(num_parts):
                part_output_path = save_path + f'.part{part_num + 1}'
                with open(part_output_path, 'rb') as part_file:
                    output_file.write(part_file.read())
                os.remove(part_output_path)

        print("Download complete!")
        return save_path
    except Exception as err:
        print(f"Error: {err}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    while True:
        file_url = input("\nFile URL (or 'exit' to quit): ")
        if file_url.lower() == 'exit':
            break
        output_folder = input("Output folder (default is current directory): ")

        if not output_folder:
            output_folder = "."

        num_parts = int(input("Number of parts to download (default is 3): ") or 3)
        downloaded_file = download_file(file_url, output_folder, num_parts)
        if downloaded_file:
            print(f"File saved as: {downloaded_file}")

tm.sleep(30)
