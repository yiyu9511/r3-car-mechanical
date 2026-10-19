#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STP 零件名乱码修复：GBK 原始字节 -> UTF-8（或 \\X2\\ 转义）

背景：中望3D (ZW3D) 等国产 CAD 导出的 STEP 文件，非 ASCII 字符直接写
GBK 原始字节，FreeCAD 按 UTF-8 读取即乱码。

两种修复模式：
  utf8（默认）— 直接把文本按 UTF-8 写回。★FreeCAD 用这个：
      FreeCAD/OCCT 导入时按 UTF-8 读字符串，中文名正常显示。
      （FreeCAD 不解析 \\X2\\ 转义，会原样显示，导 FreeCAD 别用 x2 模式）
  x2          — 非 ASCII 转为标准 \\X2\\XXXX\\X0\\ 转义（纯 ASCII）。
      适合发给别人用 SolidWorks / UG 等严格按标准实现的商业 CAD 打开的场合。

用法：
    python stp_gbk_to_utf8.py 输入.stp [输出.stp] [--mode utf8|x2]
不指定输出时生成 <原名>_utf8.stp。
"""

import argparse
import re
import sys
from pathlib import Path


def encode_x2(text: str) -> str:
    """把字符串中的非 ASCII 字符转为 \\X2\\ 转义序列（UTF-16BE hex）。"""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ord(ch) < 128:
            out.append(ch)
            i += 1
        else:
            # 收集连续的非 ASCII 段，整段包在一个 \X2\...\X0\ 里
            j = i
            while j < len(text) and ord(text[j]) >= 128:
                j += 1
            hex_part = text[i:j].encode('utf-16-be').hex().upper()
            out.append('\\X2\\' + hex_part + '\\X0\\')
            i = j
    return ''.join(out)


def decode_x2(t: str) -> str:
    def repl(m):
        return bytes.fromhex(m.group(1)).decode('utf-16-be')
    return re.sub(r'\\X2\\([0-9A-F]+)\\X0\\', repl, t)


def convert(src: Path, dst: Path, mode: str) -> None:
    raw = src.read_bytes()
    try:
        text = raw.decode('gbk')
    except UnicodeDecodeError as e:
        sys.exit(f'按 GBK 解码失败（文件可能不是 GBK）：{e}')

    if mode == 'x2':
        converted = encode_x2(text)
        assert decode_x2(converted) == text, 'X2 转换结果不可逆，中止'
        dst.write_bytes(converted.encode('ascii'))
    else:
        dst.write_bytes(text.encode('utf-8'))

    print(f'完成 ({mode}): {dst}  {len(raw)} -> {dst.stat().st_size} 字节')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='STP GBK 零件名乱码修复')
    ap.add_argument('src', type=Path, help='输入 STP 文件')
    ap.add_argument('dst', type=Path, nargs='?', help='输出文件（默认同名加 _utf8）')
    ap.add_argument('--mode', choices=['utf8', 'x2'], default='utf8',
                    help='utf8=FreeCAD 用（默认）；x2=发给别人用商业 CAD 打开时用')
    args = ap.parse_args()
    dst = args.dst or args.src.with_name(args.src.stem + '_utf8' + args.src.suffix)
    convert(args.src, dst, args.mode)
