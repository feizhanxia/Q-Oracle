# Q-Oracle

以量子随机起卦，以《周易》读卦。项目采用单动爻规则：先用六个随机位确定本卦，再均匀抽取一爻翻转，得到之卦。

「心诚不息 · 神气归一 · 六根澄明 · 持念所问」是项目保留的起卦仪式。以卦象寻求指引属于文化和信念层面的解释。量子随机数在程序里用于抽样，项目未验证卦象与占问内容或未来结果之间的关系。

## 随机源

程序优先请求 LFDR 的量子随机服务，失败后尝试 ANU Quantum Numbers。ANU 需要配置 API Key。只有启用 `QRNG_ALLOW_FALLBACK` 时，两家服务都失败后才使用本机系统随机数。页面会显示本次起卦实际使用的随机源。

## 运行

```sh
python -m pip install -r requirements.txt
python -m ui.cli
streamlit run ui/app.py
```

CLI 每次运行起一卦，原有 `--once` 参数仍可使用。网页可在起卦后选择 AI 解读并继续追问。

## 配置

CLI 和网页都支持项目根目录的 `.env`。网页也支持 `.streamlit/secrets.toml` 中的顶层配置。

| 变量 | 用途 |
| --- | --- |
| `ANU_API_KEY` | 启用 ANU 备用随机源 |
| `LFDR_URL`、`ANU_URL` | 覆盖各随机服务地址 |
| `QRNG_TIMEOUT_S` | 单次随机服务请求的超时秒数，默认 `8` |
| `QRNG_ALLOW_FALLBACK` | 设为 `true` 时允许回退到系统随机，默认关闭 |
| `TONGJI_API_KEY` | 首选模型的密钥。模型为 `Kimi-K3.1-Pro`，服务地址为 `https://agi.tongji.edu.cn/v1` |
| `LLM_API_KEY` | 备用模型的密钥，沿用现有配置 |
| `LLM_BASE_URL` | 备用服务地址，默认 `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | 备用模型名称，默认 `deepseek-ai/DeepSeek-V3.2` |

每轮 AI 解读先尝试已配置的同济模型。如果请求失败、流式回复中断或没有返回正文，程序会尝试已配置的备用模型，并以备用回复替换本轮未完成的输出。只配置 `LLM_API_KEY` 时直接使用备用服务。

`prompts/llm_prompt.txt` 用于编辑系统提示词。占问、卦象和追问由程序组装成单独的消息，点击 AI 解读后发送给所用的模型服务。
