#!/usr/bin/env python3
"""
增强铁轨纹理的立体感

铁轨结构:
  - 两条平行金属轨道 (高亮度像素) → 高度最高
  - 中间连接枕木 (中等亮度) → 中等高度
  - 空隙/透明区域 → 不处理

增强方式:
  - Height: 金属轨道=1.0, 枕木=0.7, 其他=0.3
  - Normal: 加大轨道边缘的法线偏移
  - Specular: 金属轨道=光滑+金属, 枕木=粗糙+非金属
"""

import numpy as np
from PIL import Image
from pathlib import Path

BLOCK_DIR = Path("/Users/cangcang/code/LivelyRPG/assets/minecraft/textures/block")

# 所有铁轨相关纹理
RAIL_TEXTURES = [
    "rail",
    "rail_corner",
    "powered_rail",
    "powered_rail_on",
    "detector_rail",
    "detector_rail_on",
    "activator_rail",
    "activator_rail_on",
]


def luminance(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def generate_enhanced_normal(rgb, alpha):
    """为铁轨生成增强的法线贴图，加大轨道边缘的立体感"""
    h, w = rgb.shape[:2]
    lum = luminance(rgb) / 255.0

    # 高度图: 亮像素(金属轨道)高，暗像素(空隙)低
    height = np.where(lum > 0.4, lum, lum * 0.3)

    # 只处理有 alpha 的像素
    height = np.where(alpha > 0, height, 0)

    # Sobel 梯度 - 用更大的核增强边缘
    strength = 1.5
    gx = np.zeros_like(height)
    gy = np.zeros_like(height)

    # 3x3 Sobel
    gx[:, 1:-1] = height[:, 2:] - height[:, :-2]
    gy[1:-1, :] = height[2:, :] - height[:-2, :]
    gx[:, 0] = height[:, 1] - height[:, 0]
    gx[:, -1] = height[:, -1] - height[:, -2]
    gy[0, :] = height[1, :] - height[0, :]
    gy[-1, :] = height[-1, :] - height[-2, :]

    gx = gx * strength
    gy = gy * strength

    nz = np.ones_like(height)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx = -gx / length
    ny = -gy / length
    nz = nz / length

    normal = np.zeros((h, w, 4), dtype=np.uint8)
    normal[..., 0] = np.clip((nx + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    normal[..., 1] = np.clip((ny + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    normal[..., 2] = np.clip((nz + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)

    # Alpha = 增强高度图: 轨道高，枕木中等，空隙低
    height_norm = np.clip(height / (height.max() + 1e-6), 0, 1)
    # 增强对比: 轨道(亮)→0.95-1.0, 枕木(中)→0.5-0.7, 空隙→0.2
    height_enhanced = np.where(height_norm > 0.5, 0.85 + height_norm * 0.15,
                              np.where(height_norm > 0.1, 0.4 + height_norm * 0.4,
                                       height_norm * 0.3))
    # 只在有内容的区域应用高度，透明区域设为0
    height_enhanced = np.where(alpha > 0, height_enhanced, 0)
    normal[..., 3] = (height_enhanced * 255).astype(np.uint8)

    return normal


def generate_enhanced_specular(rgb, alpha):
    """为铁轨生成增强的高光贴图: 金属轨道=光滑+金属, 枕木=粗糙+非金属"""
    h, w = rgb.shape[:2]
    lum = luminance(rgb) / 255.0

    # 光滑度: 亮像素(金属)→高, 暗像素(枕木/空隙)→低
    smoothness = np.where(lum > 0.4, 0.7 + lum * 0.3, 0.3 + lum * 0.3)
    smoothness = np.where(alpha > 0, smoothness, 0)

    # 材质掩码: 金属轨道=235(金属), 其他=4(非金属)
    is_metal = (lum > 0.4) & (alpha > 0)
    material_mask = np.where(is_metal, 235, 4)

    # 自发光: powered_rail 的黄色部分可以有轻微发光
    emissive = np.zeros_like(smoothness)

    s_arr = np.zeros((h, w, 4), dtype=np.uint8)
    s_arr[..., 0] = (smoothness * 255).astype(np.uint8)
    s_arr[..., 1] = material_mask.astype(np.uint8)
    s_arr[..., 2] = emissive.astype(np.uint8)
    s_arr[..., 3] = emissive.astype(np.uint8)
    return s_arr


def main():
    print("增强铁轨纹理立体感...")
    for name in RAIL_TEXTURES:
        base_path = BLOCK_DIR / f"{name}.png"
        if not base_path.exists():
            print(f"  跳过 {name} (不存在)")
            continue

        img = Image.open(base_path).convert("RGBA")
        arr = np.array(img)
        rgb = arr[..., :3].astype(np.float64)
        alpha = arr[..., 3]

        # 生成增强的法线贴图
        normal = generate_enhanced_normal(rgb, alpha)
        n_img = Image.fromarray(normal, mode="RGBA")
        n_img.save(base_path.with_name(f"{name}_n.png"))

        # 生成增强的高光贴图
        specular = generate_enhanced_specular(rgb, alpha)
        s_img = Image.fromarray(specular, mode="RGBA")
        s_img.save(base_path.with_name(f"{name}_s.png"))

        print(f"  {name} ✓")

    print("\n完成！铁轨纹理已增强")


if __name__ == "__main__":
    main()
