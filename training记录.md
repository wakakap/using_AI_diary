# 第一次人物LoRA训练记录

## 训练环境搭建

+ 失败经历
  
  先试用了GitHub[sd-scripts](https://github.com/kohya-ss/sd-scripts) 和 b站教程 [BV1fs4y1x7p2](https://www.bilibili.com/video/BV1fs4y1x7p2)前者是一些git和python版本vevn的操作，后者是在前者的操作下搞了一个lora部分的训练配置集成。由于我先按前者做，到后来不会了才按后者做的，所以改了后者的一些脚本，以适应不同的目录结构。（因为vevn好像设置了就不能随便改目录了）最后运行时也出现了很多错误，慢慢改掉可以运行了，花了好几个小时，但最后得出的lora并没有效果！！！我也不知道问题出在哪里。

+ COLAB

  试了[colab代码](https://home.gamer.com.tw/artwork.php?sn=5652683) 。主要是目录要按照提示放好，没有其他难度。很快，而且得到的模型效果极好！

+ 一些训练参数说明


## 训练目标

- 性癖背景
  
  我训练的人物出自[吸奶娃](https://ja.wikipedia.org/wiki/%E8%81%96%E7%97%95%E3%81%AE%E3%82%AF%E3%82%A7%E3%82%A4%E3%82%B5%E3%83%BC)，动画有点年代，角色的同人图在网上很少，我以前一直幻想高高在上的Lolita女王被吸奶的样子，但原作没有这样的桥段，我一直恋恋不舍。（性欲是我强大的生产力）

## 训练过程

  + 训练参数：

    多数的我不清楚底层原理

    <div align=center><img src="media\learning_para.jpg" height="200px" /></div>

    据写教程的人说，max epochs和文件夹里`num_xx`中的重复训练数`num`相乘为200左右效果比较好。

    LoRA模型大学32和64都还行的样子。原理不清楚。

  + 第一次训练kacya03
    
    训练集：17张512x512，是根据1980x1280动画视频截图用sai调整画布大小512x512，再缩放到合适位置一张张改的，其中全身图有3张，其他都是集中在面部的图。
    
    步骤：

    1. 预处理打上tag
    2. 保存到谷歌云盘，按colab运行。

    之后发现图片改变大小有锯齿，这可能是出图模糊的原因。

  + 第二次训练kacya240

    训练集：240张1920X1080，全是视频源截图，没有拼接，有大量人物半身，无头图片。看看效果如何。（跑了下发现太久改成了800x450）

    用这种方法抗锯齿：

    ```
    res = cv2.resize(src,target_size,interpolation=cv2.INTER_AREA)
    ```
    
    后来在chatgpt帮助下写了个脚本，自动把目标图片放到一个指定宽高的透明png画框里，达成最大的放置方法。要放在图片目录运行。

  + 第三次训练kacya04

    第二次训练流产了，想了下还是用512x512，40张，抗锯齿缩小。有完整身子也有局部部位。成功训练完，大概4小时。

    步骤：
  
    1. 预处理打上tag
    2. 安装[dataset-tag-editor](https://github.com/toshiaki1729/stable-diffusion-webui-dataset-tag-editor)：可以批量增减标签。（我git安装失败了直接下载zip解压到extension里重启webui.bat）
    3. 删除人物风格的眼睛、头发、服饰等描述词，修改错误的描述词，加入对应服饰下的触发词（好像只能一个个判断手动添加，没有更优方法），所有txt里加入整体触发词（kacya）。注意每次改完要保存，重新load一下列表，可以选不备份。
    4. 之后步骤一样。

  + 第四次训练kacya07

    之所以编号不对应，是因为有些小问题以及没跑完的我就没写在这里了。colab会有使用时限，曾经使用5x40参数跑大图就没跑完。后来转为5x30参数，跑完了。

    kacya07我综合了之前的所有经验，23张图,1024x576，其中有近一半是我手动拼接的全身图，另一些横向截图我把它们旋转放置，尽可能地大，争取最清晰效果。后来我用预处理测试这些旋转的图，发现txt里并没有 `关于旋转的描述` ，说明这一点不是提示词，会影响训练吗？（可能出图大概率也有翻着的，后面试用再说）

    <div align=center><img src="media\kacya07_tag.jpg" height="300px" /></div>

    ……


## 试用

+ kacya03:

  使用[AbyssOrangeMix3](https://civitai.com/models/9942/abyssorangemix3-aom3)，仅使用1girl, kacya03（easynegative）参数的效果：

  <div align=center><img src="txt2img-images\2023-03-02\00089-435665421.png" height="400px" /></div>

  我当场晕厥！这效果也太好了吧，不仅完美地对应截图里的衣服，而且这个脸部在orangemix地修饰下变得富有光泽，妖艳无比。性癖的狂欢！

  多加些参数，试了下，虽然不是百分比的还原（我太贪婪了），但比我下载的别人的Lora感觉好用好多！

  <div align=center><img src="txt2img-images\2023-03-02\00095-452901.png" height="400px" />
  <img src="txt2img-images\2023-03-02\00097-7453745.png" height="400px" /></div>


  <details>
    <summary>左参数</summary>
    <pre><code>1girl, kacya03,full body, silvery white hair, sit on a armchair, lift one foot in front of camera,(from_below:1.3),(masterpiece, best quality, extremely detailed CG, beautiful detailed eyes, ultra-detailed, intricate details:1.2)
  Negative prompt: EasyNegative, extra fingers, fewer fingers, (worst quality, low quality:1.4), (malformed hands:1.4),(poorly drawn hands:1.4),(mutated fingers:1.4),(extra limbs:1.35),(poorly drawn face:1.4), ugly, huge eyes, fat, indoor, worst face,(close shot:1.1), watermark
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 10, Seed: 452901, Face restoration: CodeFormer, Size: 256x512, Model hash: eb4099ba9c, Model: aom3a3.1FSE, Denoising strength: 0.65, Clip skip: 2, Hires upscale: 1.25, Hires steps: 15, Hires upscaler: Latent, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 1, AddNet Weight B 1: 1
  Used embeddings: easynegative [119b]
  Time taken: 41.55sTorch active/reserved: 3338/3780 MiB, Sys VRAM: 5599/6144 MiB (91.13%)</code></pre>
  </details>

  <details>
    <summary>右参数</summary>
    <pre><code>1girl, kacya03,full body, silvery white hair, blue_eyes, sit on a armchair, Both hands on the arm of the chair, lift one foot in front of camera,(from_below:1.5),(masterpiece, best quality, extremely detailed CG, beautiful detailed eyes, ultra-detailed, intricate details:1.2)
  Negative prompt: EasyNegative, extra fingers, fewer fingers, (worst quality, low quality:1.4), (malformed hands:1.4),(poorly drawn hands:1.4),(mutated fingers:1.4),(extra limbs:1.35),(poorly drawn face:1.4), ugly, huge eyes, fat, indoor, worst face,(close shot:1.1), watermark
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 10, Seed: 7453745, Face restoration: CodeFormer, Size: 256x512, Model hash: eb4099ba9c, Model: aom3a3.1FSE, Denoising strength: 0.65, Clip skip: 2, Hires upscale: 1.25, Hires steps: 15, Hires upscaler: Latent, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 1, AddNet Weight B 1: 1</code></pre>
  </details>

  <div align=center><img src="txt2img-images\2023-03-02\00098-843531.png" height="400px" />
  <img src="txt2img-images\2023-03-02\00105-546431.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>1girl, kacya03,full body, silvery white hair, blue_eyes, sit on a armchair, Both hands on the arm of the chair, lift one foot in front of camera,(from_below:1.5),(masterpiece, best quality, extremely detailed CG, beautiful detailed eyes, ultra-detailed, intricate details:1.2)
  Negative prompt: EasyNegative, extra fingers, fewer fingers, fewer legs,extra legs
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 10, Seed: 843531, Face restoration: CodeFormer, Size: 256x512, Model hash: eb4099ba9c, Model: aom3a3.1FSE, Denoising strength: 0.65, Clip skip: 2, Hires upscale: 1.25, Hires steps: 15, Hires upscaler: Latent, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 1, AddNet Weight B 1: 1</code></pre>
  </details>

  <details>
    <summary>参数</summary>
    <pre><code>1girl, kacya03,full body, silvery white hair, blue_eyes, sit on a armchair, Both hands on the arm of the chair,looking_at_viewer, (from_below:1.5),(masterpiece, best quality)
  Negative prompt: EasyNegative, extra fingers, fewer fingers, fewer legs,extra legs
  Steps: 40, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 546431, Face restoration: CodeFormer, Size: 256x512, Model hash: eb4099ba9c, Model: aom3a3.1FSE, Denoising strength: 0.7, Clip skip: 2, Hires upscale: 1.25, Hires steps: 20, Hires upscaler: Latent, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 0.75, AddNet Weight B 1: 0.75</code></pre>
  </details>


  不同视角： (from_above:1.3), (from_below:1.3),(from_side:1.3),(from_behind:1.3) 可能我的训练集没有描写屁股的镜头，所以会变成其他的样子。

  <div align=center><img src="txt2img-images\2023-03-02\00107-742643.png" height="400px" />
  <img src="txt2img-images\2023-03-02\00108-742643.png" height="400px" /></div>


  很奇怪的是我出的第一张图貌似是最好的了。。另外这种毛糙感是因为orangemix和动画画风不符的原因么？

  <div align=center><img src="txt2img-images\2023-03-02\00111-936579.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>1girl, kacya03, face, best quality
  Negative prompt: EasyNegative, extra fingers, fewer fingers, fewer legs,extra legs
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 936579, Face restoration: CodeFormer, Size: 512x512, Model hash: eb4099ba9c, Model: aom3a3.1FSE, Denoising strength: 0.7, Clip skip: 2, Hires upscale: 1.1, Hires steps: 20, Hires upscaler: Latent, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 1, AddNet Weight B 1: 1</code></pre>
  </details>

  ---

  让我换个模型counterfeit试试，效果还是不好，头发依旧毛糙，可能和我训练集有3张全身图里头发缩放后有锯齿有关，下个版本修复一下。

  <div align=center><img src="txt2img-images\2023-03-02\00115-927653.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>1girl, kacya03, best quality
  Negative prompt: EasyNegative
  Steps: 50, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 927653, Face restoration: CodeFormer, Size: 512x512, Model hash: a074b8864e, Model: CounterfeitV25_25, Clip skip: 2, AddNet Enabled: True, AddNet Module 1: LoRA, AddNet Model 1: kacya03(b6a7c44b00b2), AddNet Weight A 1: 1.5, AddNet Weight B 1: 1.5</code></pre>
  </details>

  ---

  换了个模型 cetusmixversion3.LNRv，变好了一点：
  <div align=center><img src="txt2img-images\2023-03-06\00044-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code> < lora:kacya03:0.9 >,1girl,twotails, staring into the camera,stained glass,zettai ryouiki, night,
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Denoising strength: 0.6, Clip skip: 2, Hires upscale: 1.25, Hires steps: 20, Hires upscaler: Latent</code></pre>
  </details>

  ---

  脸部有点崩，其他还不错，打算再训练下人物lora

  <div align=center><img src="txt2img-images\2023-03-06\00045-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code> < lora:kacya03:0.8 >,1girl,full body,twotails, staring into the camera,stained glass,zettai ryouiki, night,Fisheye lens
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Denoising strength: 0.6, Clip skip: 2, Hires upscale: 1.25, Hires steps: 20, Hires upscaler: Latent</code></pre>
  </details>

  ---

  <div align=center><img src="txt2img-images\2023-03-06\00046-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:studioGhibliStyle_offset:0.1>< lora:kacya03:0.8>,1girl,full body,twotails, staring into the camera,stained glass,zettai ryouiki, night
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Denoising strength: 0.6, Clip skip: 2, Hires upscale: 1.25, Hires steps: 20, Hires upscaler: Latent </code></pre>
  </details>

  ---

  <div align=center><img src="txt2img-images\2023-03-06\00050-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>
  < lora:kacya03:0.8>,1girl,full body,twotails,staring into the camera,stained glass,zettai ryouiki, night,(Focal length:fisheye)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Denoising strength: 0.6, Clip skip: 2, Hires upscale: 1.25, Hires steps: 20, Hires upscaler: Latent</code></pre>
  </details>

  后来加了VAE:

  <div align=center><img src="txt2img-images\2023-03-13\00083-3159738835.png" height="400px" /></div>
  ---

  ## kacya04试用

  注意`<lora:kacya04:0.8> `这种表达中间不能有空格，我这里记录参数时避免格式所以加了空格，使用时必须无空格。

  发现画风倒是很还原了，但是头发残疾，估计是我没能提供完整头发的图片比较多，它对不上。。

  <div align=center><img src="txt2img-images\2023-03-07\00016-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya04:0.8>,1girl,full body,blackdress_kacya,staring into the camera,stained glass,zettai ryouiki, night,(Focal length:fisheye)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2
  Used embeddings: easynegative [119b]
  Time taken: 1m 4.02sTorch active/reserved: 3869/4050 MiB, Sys VRAM: 5869/6144 MiB (95.52%)
  </code></pre>
  </details>

  ---

  <div align=center><img src="txt2img-images\2023-03-07\00017-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya04:0.8>,1girl,full body,bdsm_kacya,staring into the camera,stained glass,zettai ryouiki, night,(Focal length:fisheye)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2
  Used embeddings: easynegative [119b]
  Time taken: 1m 3.79sTorch active/reserved: 3869/4050 MiB, Sys VRAM: 5869/6144 MiB (95.52%)
  </code></pre>
  </details>

  ---

  这个不错哦

  <div align=center><img src="txt2img-images\2023-03-07\00019-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya04:0.8>,1girl,full body,bdsm_kacya,staring into the camera,stained glass,night,(from behind:1.3)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,dress
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2
  Used embeddings: easynegative [119b]
  Time taken: 1m 22.07sTorch active/reserved: 3869/4050 MiB, Sys VRAM: 5869/6144 MiB (95.52%)
  </code></pre>
  </details>

  加了VAE:

  <div align=center><img src="txt2img-images\2023-03-13\00084-3159738835.png" height="400px" /></div>
  ---

  除了头发真的很棒

  <div align=center><img src="txt2img-images\2023-03-07\00021-3159738835.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya04:0.8>,1girl,full body,bdsm_kacya,staring into the camera,stained glass,night,(from below:1.3)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,dress
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 3159738835, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2
  Used embeddings: easynegative [119b]
  Time taken: 1m 22.19sTorch active/reserved: 3869/4050 MiB, Sys VRAM: 5869/6144 MiB (95.52%)
  </code></pre>
  </details>

  ---

+ kacya06试用

  这个版本在上个版本04的基础上多合成了几张全身图，少了几张只有部分身体让头发单独露出来的图，希望能避免头发接不上的情况。

  结果是，头发正常了很多，但是由于全身照和横向照混合，导致清晰度不高，出图很糊，让我再调整一次。

+ kacya07-000025试用

  图片太大，练了一半colab到上限了

  <div align=center><img src="txt2img-images\2023-03-10\00008-1426578133.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya07-000025:0.95>,1girl, blackdress_kacya, looking_at_viewer,stained glass,zettai ryouiki, night,(Focal length:fisheye)
  Negative prompt: (worst quality:1.6),(low quality:1.6), easynegative,
  Steps: 25, Sampler: DPM++ 2M Karras, CFG scale: 9, Seed: 1426578133, Face restoration: CodeFormer, Size: 400x600, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2
  </code></pre>
  </details>

  ---

+ kacya07
  
  值得说明的是，这是我使用了 VAE：`pastel-waifu-diffusion.vae.pt` 后跑的图，可以明显发现颜色鲜亮了很多。

  <div align=center><img src="txt2img-images\2023-03-13\00056-907844496.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya07:0.9>, full body, blackdress_kacya, (((1girl))),ray tracing, (dim light), [realistic] ((detailed background(ominous bedroom))), show off delicate svelte figure and lissome curvaceous beautie,correct limbs
    Negative prompt: easynegative
    Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 907844496, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2</code></pre>
  </details>

  图片质量上升了很多，但这个头发如果是原始样子的话，还是很容易连不上。看来这个稳定难度还是太大了，我就不追求了。

  <div align=center><img src="txt2img-images\2023-03-13\00069-2707737483.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya07:0.9>, full body, blackdress_kacya,kacya, (((1girl))),ray tracing, (dim light), [realistic] ((detailed background(ominous room))), show off delicate svelte figure and lissome curvaceous beautie,correct limbs
    Negative prompt: easynegative
    Steps: 21, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 2707737483, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2</code></pre>
  </details>


  <div align=center><img src="txt2img-images\2023-03-13\00060-2817579164.png" height="400px" /></div>

  <details>
    <summary>参数</summary>
    <pre><code>< lora:kacya07:0.9>, full body, bdsm_kacya,kacya, (((1girl))),ray tracing, (dim light), [realistic] ((detailed background(ominous room))), show off delicate svelte figure and lissome curvaceous beautie,correct limbs
    Negative prompt: easynegative
    Steps: 21, Sampler: DPM++ 2M Karras, CFG scale: 7, Seed: 2707737483, Face restoration: CodeFormer, Size: 512x768, Model hash: 59ea4aa1d8, Model: cetusmixversion3.LNRv, Clip skip: 2</code></pre>
  </details>









