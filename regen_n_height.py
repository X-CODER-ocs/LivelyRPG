#!/usr/bin/env python3
"""
重新生成 _n.png 法线贴图，加入高度(Alpha)通道供 POM 视差使用

Lively 光影 _n.png 格式:
  RGB = 法线 XYZ (标准编码: (n+1)/2 * 255)
  A   = 高度图 (供 POM 视差遮蔽映射, 越亮越高)
"""

import numpy as np
from PIL import Image
from pathlib import Path

BLOCK_DIR = Path("/Users/cangcang/code/LivelyRPG/assets/minecraft/textures/block")
NORMAL_STRENGTH = 0.6


def luminance(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def generate_normal_and_height(rgb, strength=NORMAL_STRENGTH):
    """同时生成法线(RGB)和高度(A)"""
    h, w = rgb.shape[:2]
    height = luminance(rgb) / 255.0

    # Sobel 梯度
    gx = np.zeros_like(height, dtype=np.float64)
    gy = np.zeros_like(height, dtype=np.float64)
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
    # Alpha = 高度图: 大幅压缩范围，视差非常轻微
    height_norm = np.clip((height - height.min()) / (height.max() - height.min() + 1e-6), 0, 1)
    height_enhanced = 0.9 + height_norm * 0.1  # 限制在 0.9-1.0，10%起伏
    normal[..., 3] = (height_enhanced * 255).astype(np.uint8)
    return normal


def process_texture(png_path):
    try:
        img = Image.open(png_path).convert('RGBA')
        arr = np.array(img)
        rgb = arr[..., :3].astype(np.float64)
        alpha = arr[..., 3]
        if alpha.max() == 0 or arr.shape[0] < 4 or arr.shape[1] < 4:
            return False
        normal = generate_normal_and_height(rgb)
        n_img = Image.fromarray(normal, mode='RGBA')
        n_path = png_path.with_name(png_path.stem + '_n.png')
        n_img.save(n_path)
        return True
    except Exception as e:
        print(f"  错误 {png_path.name}: {e}")
        return False


def main():
    png_files = sorted(BLOCK_DIR.glob("*.png"))
    png_files = [f for f in png_files if not f.stem.endswith('_n') and not f.stem.endswith('_s')]
    total = len(png_files)
    print(f"重新生成 {total} 个 _n.png (含高度Alpha通道)...")
    success = 0
    for i, png in enumerate(png_files, 1):
        if process_texture(png):
            success += 1
        if i % 100 == 0 or i == total:
            print(f"  进度: {i}/{total}  (成功 {success})")
    print(f"\n完成！成功重新生成 {success}/{total} 个 _n.png")


if __name__ == '__main__':
    main()
