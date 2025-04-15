import os
import requests

def save_image(image_url, file_base_name, images_folder="../images/posts"):
    os.makedirs(images_folder, exist_ok=True)
    image_name = f"{file_base_name}.jpg"
    image_path = os.path.join(images_folder, image_name)

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image saved: {image_path}")
        else:
            print(f"Failed to fetch image: {image_url}")
    except Exception as e:
        print(f"Error fetching image: {e}")
    return image_path
