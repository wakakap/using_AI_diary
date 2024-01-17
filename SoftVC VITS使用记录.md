# SoftVC VITS使用记录

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

