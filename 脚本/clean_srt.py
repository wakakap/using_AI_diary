def process_srt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 用于存储更新过的行
        updated_lines = []
        for i, line in enumerate(lines):
            if line.strip().isdigit():  # 检查是否为序号
                current_index = int(line.strip())
                next_index = str(current_index + 1)  # 下一个序号
                updated_index = str(len(updated_lines) // 4 + 1)  # 正确的序号
                updated_lines.append(updated_index + '\n')  # 添加更新后的序号

            elif '-->' in line:  # 时间行
                parts = line.split('-->')
                start_time = parts[0].strip()
                # 尝试获取下一序列的开始时间作为结束时间
                if i + 4 < len(lines) and '-->' in lines[i + 4]:
                    end_time = lines[i + 4].split('-->')[0].strip()
                else:
                    end_time = parts[1].strip()  # 如果没有下一行，使用原来的结束时间
                updated_lines.append(f"{start_time} --> {end_time}\n")
            else:
                updated_lines.append(line)  # 其它行直接添加

        # 将更新过的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)

        print(f"File '{file_path}' has been processed successfully.")

    except Exception as e:
        print(f"Error processing file '{file_path}': {e}")

if __name__ == "__main__":
    path = "audio.ja-jp.srt"  # 指定文件路径
    process_srt_file(path)
