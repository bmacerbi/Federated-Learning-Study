import os
import sys

def flip_all_folders_not_coordenate(base_dir, shift_amount):
    folder_names = [str(i) for i in range(10)]
    
    temp_folder = os.path.join(base_dir, 'temp_folder')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    missing_folders = [f for f in folder_names if not os.path.exists(os.path.join(base_dir, f))]
    if missing_folders:
        print(f"Missing folders: {', '.join(missing_folders)}. Shift operation aborted.")
        return

    temp_names = {folder: f"{folder}_temp" for folder in folder_names}
    for folder in folder_names:
        os.rename(os.path.join(base_dir, folder), os.path.join(base_dir, temp_names[folder]))

    for i in range(10):
        new_index = (i + shift_amount) % 10
        os.rename(os.path.join(base_dir, temp_names[str(i)]), os.path.join(base_dir, str(new_index)))

    print(f"Successfully shifted folders by {shift_amount} positions in {base_dir}")

def flip_all_folders_coordenate(base_dir):
    folder_names = [str(i) for i in range(10)]
    temp_folder = os.path.join(base_dir, 'temp_folder')

    missing_folders = [f for f in folder_names if not os.path.exists(os.path.join(base_dir, f))]
    if missing_folders:
        print(f"Missing folders: {', '.join(missing_folders)}. Flip operation aborted.")
        return

    folder = os.path.join(base_dir, '9')
    os.rename(folder, temp_folder)

    for i in range(8, -1, -1):
        os.rename(os.path.join(base_dir, str(i)), os.path.join(base_dir, str(i + 1)))

    os.rename(temp_folder, os.path.join(base_dir, '0'))

    print(f"Successfully flipped all folders in {base_dir}")

def flip_folders_in_range(base_path, num_clients, use_coordenate):
    for i in range(num_clients + 1):
        client_dir = os.path.join(base_path, f'client_{i}')
        if os.path.exists(client_dir):
            if use_coordenate:
                flip_all_folders_coordenate(client_dir)
            else:
                flip_all_folders_not_coordenate(client_dir, i + 1)
        else:
            print(f"{client_dir} does not exist")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script_name.py <base_directory> <num_clients> <use_coordenate>")
        print("<use_coordenate> should be 'true' or 'false'")
        sys.exit(1)
    
    base_directory = sys.argv[1]
    num_clients = int(sys.argv[2])
    use_coordenate = sys.argv[3].lower() == 'true'

    flip_folders_in_range(base_directory, num_clients, use_coordenate)