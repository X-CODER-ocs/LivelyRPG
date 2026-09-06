#!/usr/bin/env python3
"""
重新生成 Lively 光影专用的 _s.png 高光贴图

Lively 光影 _s.png 通道格式:
  R = Smoothness (光滑度, 0=粗糙 1=光滑)
  G = Material Mask (0-229=非金属F0递增, 230-240=金属)
  B = Emissive (自发光, SEUS模式)
  A = Emissive (自发光, labPBR模式)
"""

import os
import numpy as np
from PIL import Image
from pathlib import Path

BLOCK_DIR = Path("/Users/cangcang/code/LivelyRPG/assets/minecraft/textures/block")

ROUGHNESS_BASE = 0.6


def luminance(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def generate_smoothness(rgb):
    """生成光滑度 = 1 - 粗糙度"""
    h, w = rgb.shape[:2]
    lum = luminance(rgb)
    kernel_size = 3
    pad = kernel_size // 2
    padded = np.pad(lum, pad, mode='edge')
    local_var = np.zeros_like(lum)
    for i in range(kernel_size):
        for j in range(kernel_size):
            local_var += (padded[i:i+h, j:j+w] - lum) ** 2
    local_var /= (kernel_size * kernel_size)
    var_norm = np.clip(local_var / (local_var.max() + 1e-6), 0, 1)
    roughness = np.clip(ROUGHNESS_BASE + var_norm * 0.4, 0, 1)
    smoothness = 1.0 - roughness
    return (smoothness * 255).astype(np.uint8)


def generate_material_mask(rgb):
    """生成材质掩码: 非金属低F0(0-4), 金属高值(230-240)"""
    r = rgb[..., 0].astype(np.float64) / 255
    g = rgb[..., 1].astype(np.float64) / 255
    b = rgb[..., 2].astype(np.float64) / 255
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c
    saturation = np.where(max_c > 0, delta / (max_c + 1e-6), 0)
    # 金属判定: 高饱和度 或 低饱和高亮度(灰色金属如铁)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    is_metal = (saturation > 0.55) | ((saturation < 0.05) & (lum > 0.7))
    # 非金属: F0 ≈ 0.04, 映射到 G≈4; 金属: G = 235 + saturation*5 (确保>=230)
    mask = np.where(is_metal, 235.0 + np.minimum(saturation, 1.0) * 5.0, 4.0)
    return np.clip(mask, 0, 255).astype(np.uint8)


def process_texture(png_path):
    try:
        img = Image.open(png_path).convert('RGBA')
        arr = np.array(img)
        rgb = arr[..., :3].astype(np.float64)
        alpha = arr[..., 3]
        if alpha.max() == 0 or arr.shape[0] < 4 or arr.shape[1] < 4:
            return False

        smoothness = generate_smoothness(rgb)
        material_mask = generate_material_mask(rgb)
        emissive = np.zeros_like(smoothness)

        # R=smoothness, G=materialMask, B=emissive, A=emissive
        s_arr = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
        s_arr[..., 0] = smoothness
        s_arr[..., 1] = material_mask
        s_arr[..., 2] = emissive
        s_arr[..., 3] = emissive
        s_img = Image.fromarray(s_arr, mode='RGBA')
        s_path = png_path.with_name(png_path.stem + '_s.png')
        s_img.save(s_path)
        return True
    except Exception as e:
        print(f"  错误 {png_path.name}: {e}")
        return False


def main():
    png_files = sorted(BLOCK_DIR.glob("*.png"))
    png_files = [f for f in png_files if not f.stem.endswith('_n') and not f.stem.endswith('_s')]
    total = len(png_files)
    print(f"重新生成 {total} 个 _s.png (Lively 光影格式)...")
    success = 0
    for i, png in enumerate(png_files, 1):
        if process_texture(png):
            success += 1
        if i % 100 == 0 or i == total:
            print(f"  进度: {i}/{total}  (成功 {success})")
    print(f"\n完成！成功重新生成 {success}/{total} 个 _s.png")


if __name__ == '__main__':
    main()
