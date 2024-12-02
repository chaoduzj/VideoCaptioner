import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from app.config import CACHE_PATH, RESOURCE_PATH
from .logger import setup_logger

logger = setup_logger("subtitle_preview")

SCRIPT_INFO_TEMPLATE = """[Script Info]
; Script generated by VideoSubtitleEditor
; https://github.com/WEIFENG2333
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

{style_str}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{dialogue}
"""

ASS_TEMP_FILENAME = CACHE_PATH / "preview.ass"  # 预览的临时 ASS 文件路径
PREVIEW_IMAGE_FILENAME = CACHE_PATH / "preview.png"  # 预览的图片路径
DEFAULT_BG_PATH = RESOURCE_PATH / "assets" / "default_bg.png"

def run_subprocess(command: list):
    """运行子进程命令，并处理异常"""
    try:
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error: {e.stderr}")

def generate_ass_file(style_str: str, preview_text: Tuple[str, Optional[str]]) -> str:
    """生成临时 ASS 文件"""
    original_text, translate_text = preview_text
    dialogue = [
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Secondary,,0,0,0,,{translate_text}",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{original_text}"
    ] if translate_text else [
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{original_text}"
    ]

    ass_content = SCRIPT_INFO_TEMPLATE.format(
        style_str=style_str,
        dialogue=os.linesep.join(dialogue)
    )
    ASS_TEMP_FILENAME.parent.mkdir(parents=True, exist_ok=True)
    ASS_TEMP_FILENAME.write_text(ass_content, encoding="utf-8")
    return str(ASS_TEMP_FILENAME)

def ensure_background(bg_path: Path) -> Path:
    """确保背景图片存在，若不存在则创建默认黑色背景"""
    if not bg_path.is_file() or not bg_path.exists():
        if not Path(DEFAULT_BG_PATH).exists():
            DEFAULT_BG_PATH.parent.mkdir(parents=True, exist_ok=True)
            run_subprocess([
                'ffmpeg', 
                '-f', 'lavfi', 
                '-i', 'color=c=black:s=1920x1080', 
                '-frames:v', '1', 
                str(DEFAULT_BG_PATH)
            ])
        return Path(DEFAULT_BG_PATH)
    return bg_path

def generate_preview(style_str: str, preview_text: Tuple[str, Optional[str]], bg_path: str) -> str:
    """生成预览图片"""
    ass_file = generate_ass_file(style_str, preview_text)
    bg_path = ensure_background(Path(bg_path))

    output_path = PREVIEW_IMAGE_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ass_file_processed = ass_file.replace('\\', '/').replace(':', r'\\:')
    cmd = [
        'ffmpeg', 
        '-y',
        '-i', str(bg_path),
        '-vf', f"ass={ass_file_processed}",
        '-frames:v', '1',
        str(output_path)
    ]
    run_subprocess(cmd)
    return str(output_path)

if __name__ == "__main__":
    style_str = """[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,微软雅黑,70,&H00eb7f33,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2.0,0,1,2.0,0,2,10,10,10,1
Style: Translate,微软雅黑,40,&H00eff0f3,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0.0,0,1,1.0,0,2,10,10,10,1
"""
    bg_path = r"C:\Users\weifeng\Pictures\Animated_character_spraying_liquid.jpg"
    preview_text = ("Hello, world!", "你好，世界！")
    print(generate_preview(style_str, preview_text, bg_path))
