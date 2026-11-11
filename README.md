# Q-Oracle

以量子随机起卦，以《周易》读卦。项目采用单动爻规则：先用六个随机位确定本卦，再均匀抽取一爻翻转，得到之卦。

「心诚不息 · 神气归一 · 六根澄明 · 持念所问」是项目保留的起卦仪式。以卦象寻求指引属于文化和信念层面的解释。量子随机数在程序里用于抽样，项目未验证卦象与占问内容或未来结果之间的关系。

## 随机源

程序优先请求 LFDR 的量子随机服务，失败后尝试 ANU Quantum Numbers。ANU 需要配置 API Key。只有启用 `QRNG_ALLOW_FALLBACK` 时，两家服务都失败后才使用本机系统随机数。CLI 会显示本次起卦实际使用的随机源。

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
| `LLM_API_KEY` | 模型服务密钥，默认接入硅基流动 |
| `LLM_BASE_URL` | 模型服务地址，默认 `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | 模型名称，默认 `deepseek-ai/DeepSeek-V4.1-Flash` |

`prompts/llm_prompt.txt` 是 AI 解读的提示词模板。程序按原模板填入占问、本卦、动爻和之卦，将其作为本次解读的系统消息。追问作为后续用户消息发送给所用的模型服务。
