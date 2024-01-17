# vits使用记录

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