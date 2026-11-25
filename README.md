# LWB-261125

LWB 的个人工作仓库：随手脚本、学习笔记与技术实验。内容以「能直接跑起来」为准，不追求工程完备。

## 目录

| 路径 | 内容 | 说明 |
|---|---|---|
| `scripts/riemann-lucky/` | 黎曼幸运数 | 用 ζ 函数非平凡零点生成大乐透 / 双色球号码（纯娱乐，不能预测开奖） |

## 仓库约定

1. **不存凭据**：API key、token、密码、客户名单一律不进仓库；上传前可先跑一次 secret scan。
2. **每个子目录自带 README**：写清用途、依赖、运行方式，别人（和未来的自己）打开就能跑。
3. **脚本保持单文件可运行**：尽量零外部依赖，必须依赖的在 README 首行写明安装命令。

## 快速开始

```bash
git clone https://github.com/Binluiwan/LWB-261125.git
cd LWB-261125/scripts/riemann-lucky
python -m pip install mpmath
python riemann_lucky.py --trace
```

## 许可

个人仓库，未声明开源许可；如需引用请先联系作者。
