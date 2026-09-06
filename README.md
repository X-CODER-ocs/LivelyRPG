# LivelyRPG PBR 材质包

基于 Minecraft 原版方块纹理生成的 **PBR 材质包**，专为 [Lively 光影](https://github.com/) 优化。

## 特性

- 覆盖全部 **1038 个**原版方块纹理
- 自动生成法线贴图（Normal Map）和高光贴图（Specular Map）
- 适配 Lively 光影的 **seuspbr / labPBR** 通道格式
- 法线贴图 Alpha 通道内置高度图，支持 **POM 视差遮蔽映射**
- 金属方块（铁、金、钻石等）自动识别金属度

## PBR 贴图格式

### 法线贴图 `xxx_n.png`（RGBA）

| 通道 | 含义 |
|------|------|
| R | 法线 X |
| G | 法线 Y |
| B | 法线 Z |
| A | 高度图（供 POM 视差使用） |

### 高光贴图 `xxx_s.png`（RGBA）

| 通道 | 含义 |
|------|------|
| R | 光滑度 Smoothness（0=粗糙，1=光滑） |
| G | 材质掩码（0-229=非金属，230-240=金属） |
| B | 自发光 Emissive（seuspbr 模式） |
| A | 自发光 Emissive（labPBR 模式） |

## 安装

1. 将本仓库打包为 zip（或下载 Releases 中的 zip）
2. 放入 `.minecraft/resourcepacks/` 目录
3. 启动 Minecraft → 选项 → 资源包 → 启用 LivelyRPG
4. 启用 Lively 光影，将 **RP支持** 设为 `seuspbr` 或 `labPBR`

## 光影设置建议

| 设置项 | 推荐值 |
|--------|--------|
| RP 支持 | seuspbr 或 labPBR |
| 法线贴图强度 | 80 - 120 |
| POM 深度 | 1.0 - 1.5 |

## 目录结构

```
LivelyRPG/
├── pack.mcmeta                          # 资源包配置
├── generate_pbr.py                      # 原始 PBR 生成脚本
├── regen_s_lively.py                    # Lively 格式高光贴图生成脚本
├── regen_n_height.py                    # 含高度通道的法线贴图生成脚本
└── assets/minecraft/textures/block/
    ├── xxx.png                          # 基础色（原版）
    ├── xxx_n.png                        # 法线贴图（含高度 Alpha）
    └── xxx_s.png                        # 高光贴图
```

## 重新生成 PBR 贴图

修改基础色纹理后，重新生成对应 PBR 贴图：

```bash
# 生成法线贴图（含高度通道）
python3 regen_n_height.py

# 生成 Lively 格式高光贴图
python3 regen_s_lively.py
```

## 兼容版本

- Minecraft Java Edition **1.21.2 - 1.21.4**（pack_format: 35）
- Lively 光影（Cinematic / Magic / Nature / Nightmare）

## License

本项目的 PBR 贴图生成脚本为开源。原版 Minecraft 纹理版权归 Mojang Studios 所有。
