# SoftVC VITS使用记录

## GPT-SoVITS

[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 这个项目做了web，并且有整合[下载套装](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md)，很方便使用。

过程：
 - 语音切分工具：output\slicer_opt中会产生切割好的slide
 - 中文批量离线ASR工具：也支持日文，英文等。运行在output\asr_opt产生.list文件
 - 开启打标webui，对于不完整的句子处理等。效果好不用处理。
 - 1-GPT-SoVITS-TTS：
   - 训练集格式化工具：只用选择.list文件路径，就可一键三连
   - 微调训练：两个依次点，就能生成模型了
   - 推理：选择ckpt和pth文件模型，点击开启，就会产生新界面。
- 使用：选择一个样例（可以查看list中的文字识别）输入转语音的文字。

## 本地配置运行

+ resample错误

    删除了一个local里的参数NONE解决。


+ CPU错误

    ```
    assert torch.cuda.is_available(), "CPU training is not allowed." AssertionError: CPU training is not allowed.

    ```
    默认pip安装torch时装成了CPU版本，可以用一下py脚本检查：
    ```
    import torch
    print(torch.__version__)、
    ```
    然后去[官网](https://pytorch.org/get-started/locally/)寻找正确的下载指令。
    ```
    pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117
    ```

+ 显存不够

    ```
    torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 28.00 MiB (GPU 0; 6.00 GiB total capacity; 4.38 GiB already allocated; 0 bytes free; 4.48 GiB reserved in total by PyTorch) If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.  See documentation for Memory Management and PYTORCH_CUDA_ALLOC_CONF
    ```

## colab使用记录

## MoeGoe

训练好的模型合集：[by CjangCjengh](https://github.com/CjangCjengh/TTSModels)，[其他模型](https://huggingface.co/spaces/skytnt/moe-tts)

跑模型的项目：[MoeGoe](https://github.com/CjangCjengh/MoeGoe)

使用方法注意：
    
+ 下载release里MoeGoe和gui，然后如下设置：

<div align=center><img src="media\moegoe_config.jpg" height="300px" /></div>

+ 注意选择哪种模式（VITS,HuBERT-VITS,W2V2-VITS）是由json文件决定的，作者竟然没有再readme文件说明这一点。让我查看 `MoeGoe.py` 文件才发现的：

    ```
    emotion_embedding = hps_ms.data.emotion_embedding if 'emotion_embedding' in hps_ms.data.keys() else False
    ```

    所以要在data里手动添加`emotion_embedding`来使用W2V2-VITS，重新命名保存。

    ```
    "data": {
        "text_cleaners":["japanese_cleaners2"],
        "max_wav_value": 32768.0,
        "sampling_rate": 22050,
        "filter_length": 1024,
        "hop_length": 256,
        "win_length": 1024,
        "add_blank": true,
        "n_speakers": 29,
        "emotion_embedding": true
    },
    ```

    这种模式下先选择原版某音频文件，跑一次后会出现npy文件，之后再使用npy会提高效果。

    同理HuBERT-VITS对应于：

    ```
    n_symbols = len(hps_ms.symbols) if 'symbols' in hps_ms.keys() else 0
    ```
    我还没看怎么用。