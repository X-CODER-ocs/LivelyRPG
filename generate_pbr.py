#!/usr/bin/env python3
"""
批量为 Minecraft 方块纹理生成 PBR 贴图（LabPBR 标准）

输入:  assets/minecraft/textures/block/*.png  (Albedo 基础色)
输出:  assets/minecraft/textures/block/*_n.png  (法线贴图)
       assets/minecraft/textures/block/*_s.png  (高光贴图: R=金属度 G=粗糙度 B=自发光 A=AO)

原理与 GenPBR 类似，全部本地计算，无需上传。
"""

import os
import sys
import numpy as np
from PIL import Image
from pathlib import Path

BLOCK_DIR = Path("/Users/cangcang/code/LivelyRPG/assets/minecraft/textures/block")

# PBR 参数（可调整）
NORMAL_STRENGTH = 2.0      # 法线强度
ROUGHNESS_BASE = 0.6       # 基础粗糙度 (0=光滑 1=粗糙)
METAL_THRESHOLD = 0.6      # 金属判定饱和度阈值


def luminance(rgb):
    """计算亮度"""
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def generate_normal(height, strength=NORMAL_STRENGTH):
    """从高度图生成法线贴图 (Sobel 算子)"""
    h, w = height.shape
    # Sobel 梯度
    gx = np.zeros_like(height, dtype=np.float64)
    gy = np.zeros_like(height, dtype=np.float64)
    gx[:, 1:-1] = height[:, 2:] - height[:, :-2]
    gy[1:-1, :] = height[2:, :] - height[:-2, :]
    # 边界处理
    gx[:, 0] = height[:, 1] - height[:, 0]
    gx[:, -1] = height[:, -1] - height[:, -2]
    gy[0, :] = height[1, :] - height[0, :]
    gy[-1, :] = height[-1, :] - height[-2, :]

    gx = gx * strength
    gy = gy * strength

    # 法线方向: (-gx, -gy, 1) 归一化
    nz = np.ones_like(height)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx = -gx / length
    ny = -gy / length
    nz = nz / length

    # 编码到 0-255 (128 = 0)
    normal = np.zeros((h, w, 3), dtype=np.uint8)
    normal[..., 0] = np.clip((nx + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    normal[..., 1] = np.clip((ny + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    normal[..., 2] = np.clip((nz + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    return normal


def generate_roughness(rgb):
    """生成粗糙度贴图：细节越多越粗糙"""
    h, w = rgb.shape[:2]
    lum = luminance(rgb)
    # 局部方差作为粗糙度依据
    kernel_size = 3
    pad = kernel_size // 2
    padded = np.pad(lum, pad, mode='edge')
    local_var = np.zeros_like(lum)
    for i in range(kernel_size):
        for j in range(kernel_size):
            local_var += (padded[i:i+h, j:j+w] - lum) ** 2
    local_var /= (kernel_size * kernel_size)
    # 归一化并混合基础粗糙度
    var_norm = np.clip(local_var / (local_var.max() + 1e-6), 0, 1)
    roughness = np.clip(ROUGHNESS_BASE + var_norm * 0.4, 0, 1)
    return (roughness * 255).astype(np.uint8)


def generate_metallic(rgb):
    """生成金属度贴图：高饱和度+特定色调判定为金属"""
    r = rgb[..., 0].astype(np.float64) / 255
    g = rgb[..., 1].astype(np.float64) / 255
    b = rgb[..., 2].astype(np.float64) / 255
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c
    saturation = np.where(max_c > 0, delta / (max_c + 1e-6), 0)
    # 金属通常饱和度高且偏灰/黄/白
    is_metal = saturation > METAL_THRESHOLD
    metallic = np.where(is_metal, 255, 0).astype(np.uint8)
    return metallic


def generate_ao(height):
    """生成环境光遮蔽贴图：凹陷处变暗"""
    h, w = height.shape
    # 简单的高度差 AO：周围比中心高则遮蔽
    kernel_size = 3
    pad = kernel_size // 2
    padded = np.pad(height, pad, mode='edge')
    ao = np.ones_like(height)
    for i in range(kernel_size):
        for j in range(kernel_size):
            if i == pad and j == pad:
                continue
            neighbor = padded[i:i+h, j:j+w]
            ao = np.minimum(ao, 1.0 - np.clip(neighbor - height, 0, 1) * 0.5)
    ao = np.clip(ao * 0.7 + 0.3, 0, 1)
    return (ao * 255).astype(np.uint8)


def process_texture(png_path):
    """处理单个纹理，生成 _n.png 和 _s.png"""
    try:
        img = Image.open(png_path).convert('RGBA')
        arr = np.array(img)
        rgb = arr[..., :3].astype(np.float64)
        alpha = arr[..., 3]

        # 跳过全透明或极小的纹理
        if alpha.max() == 0 or arr.shape[0] < 4 or arr.shape[1] < 4:
            return False

        height = luminance(rgb) / 255.0

        # 生成各通道
        normal = generate_normal(height)
        roughness = generate_roughness(rgb)
        metallic = generate_metallic(rgb)
        ao = generate_ao(height)
        emissive = np.zeros_like(roughness)  # 自发光默认关闭

        # 保存法线贴图 _n.png
        n_img = Image.fromarray(normal, mode='RGB')
        n_path = png_path.with_name(png_path.stem + '_n.png')
        n_img.save(n_path)

        # 保存高光贴图 _s.png (R=金属度 G=粗糙度 B=自发光 A=AO)
        s_arr = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
        s_arr[..., 0] = metallic
        s_arr[..., 1] = roughness
        s_arr[..., 2] = emissive
        s_arr[..., 3] = ao
        s_img = Image.fromarray(s_arr, mode='RGBA')
        s_path = png_path.with_name(png_path.stem + '_s.png')
        s_img.save(s_path)

        return True
    except Exception as e:
        print(f"  错误 {png_path.name}: {e}")
        return False


def main():
    png_files = sorted(BLOCK_DIR.glob("*.png"))
    # 排除已经生成的 _n.png 和 _s.png
    png_files = [f for f in png_files if not f.stem.endswith('_n') and not f.stem.endswith('_s')]

    total = len(png_files)
    print(f"找到 {total} 个基础纹理，开始生成 PBR 贴图...")

    success = 0
    for i, png in enumerate(png_files, 1):
        if process_texture(png):
            success += 1
        if i % 50 == 0 or i == total:
            print(f"  进度: {i}/{total}  (成功 {success})")

    print(f"\n完成！成功生成 {success}/{total} 组 PBR 贴图")
    print(f"输出位置: {BLOCK_DIR}")
    print(f"  *_n.png = 法线贴图")
    print(f"  *_s.png = 高光贴图 (R=金属度 G=粗糙度 B=自发光 A=AO)")


if __name__ == '__main__':
    main()
