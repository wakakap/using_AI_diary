def modify_srt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        if '-->' in line:
            # Check line for '-->', then change the last character before the newline to '0'
            modified_line = line[:-2] + '0' + '\n'  # Assuming the original line ends with '\n'
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)

    new_file_path = file_path[:-4] + '_modified.srt'
    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)
    
    print(f"Modified file has been saved as {new_file_path}")

# Calling the function with the path to your .srt file
modify_srt_file('audio.ja-jp.srt')