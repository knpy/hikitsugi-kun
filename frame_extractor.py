"""
動画フレーム抽出モジュール

FFmpegを使用して動画から定期的にフレームを抽出し、
引継ぎドキュメント用のタイムスタンプ付き画像を生成する。
"""

import os
import tempfile
import base64
from pathlib import Path
from typing import List, Tuple

import ffmpeg
from PIL import Image


def format_timestamp(seconds: float) -> str:
    """秒数をMM:SS形式に変換"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_video_duration(video_path: str) -> float:
    """動画の長さを秒数で取得"""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe["format"]["duration"])
        return duration
    except Exception as e:
        raise RuntimeError(f"動画情報の取得に失敗しました: {e}")


def resize_image(image_path: str, max_width: int = 800) -> None:
    """画像を指定幅にリサイズ（アスペクト比維持）"""
    with Image.open(image_path) as img:
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            resized = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            resized.save(image_path, optimize=True, quality=85)


def extract_frames(
    video_path: str,
    interval_seconds: int = 5,
    max_width: int = 800
) -> List[Tuple[float, str, str]]:
    """
    FFmpegでフレーム抽出

    Args:
        video_path: 動画ファイルのパス
        interval_seconds: フレーム抽出間隔（秒）
        max_width: 画像の最大幅（ピクセル）

    Returns:
        List of (timestamp_seconds, timestamp_str, base64_image)
    """
    duration = get_video_duration(video_path)
    frames = []

    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp(prefix="hikitsugi_frames_")

    try:
        # 抽出するタイムスタンプを計算
        timestamps = []
        current_time = 0.0
        while current_time < duration:
            timestamps.append(current_time)
            current_time += interval_seconds

        # 各タイムスタンプでフレームを抽出
        for ts in timestamps:
            output_path = os.path.join(temp_dir, f"frame_{ts:.0f}.jpg")

            try:
                (
                    ffmpeg
                    .input(video_path, ss=ts)
                    .output(output_path, vframes=1, format="image2", vcodec="mjpeg")
                    .overwrite_output()
                    .run(quiet=True)
                )

                # 画像リサイズ
                resize_image(output_path, max_width)

                # Base64変換
                with open(output_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")

                frames.append((ts, format_timestamp(ts), b64_data))

            except Exception as e:
                # 個別フレームの抽出失敗はスキップ
                print(f"Warning: フレーム抽出失敗 (ts={ts}): {e}")
                continue

    finally:
        # 一時ファイルを削除
        cleanup_temp_dir(temp_dir)

    return frames


def cleanup_temp_dir(temp_dir: str) -> None:
    """一時ディレクトリを削除"""
    import shutil
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: 一時ディレクトリ削除失敗: {e}")


def cleanup_frames(frames: List[Tuple[float, str, str]]) -> None:
    """フレームデータをクリア（メモリ解放用）"""
    frames.clear()


def generate_markdown_table(frames: List[Tuple[float, str, str]]) -> str:
    """
    フレームからMarkdownテーブルを生成

    Args:
        frames: List of (timestamp_seconds, timestamp_str, base64_image)

    Returns:
        Markdown形式のテーブル文字列
    """
    if not frames:
        return ""

    lines = [
        "| タイムスタンプ | 画面キャプチャ |",
        "|:-------------:|:-------------:|"
    ]

    for ts_sec, ts_str, b64_img in frames:
        # インライン画像（Base64埋め込み）
        img_tag = f"![{ts_str}](data:image/jpeg;base64,{b64_img})"
        lines.append(f"| {ts_str} | {img_tag} |")

    return "\n".join(lines)


def generate_frames_summary(frames: List[Tuple[float, str, str]]) -> str:
    """フレーム抽出のサマリーを生成"""
    if not frames:
        return "フレームが抽出されていません。"

    total_frames = len(frames)
    first_ts = frames[0][1]
    last_ts = frames[-1][1]

    return f"抽出フレーム数: {total_frames}枚 ({first_ts} ～ {last_ts})"


def parse_timestamp_str(time_str: str) -> float:
    """MM:SS形式の文字列を秒数（float）に変換"""
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    return 0.0


def find_closest_frame(target_time_str: str, frames: List[Tuple[float, str, str]]) -> Tuple[float, str, str]:
    """
    指定された時刻文字列に最も近いフレームを探す
    
    Args:
        target_time_str: "MM:SS" 形式の文字列
        frames: List of (timestamp_seconds, timestamp_str, base64_image)
        
    Returns:
        最も近いフレームのデータタプル
    """
    if not frames:
        return None
        
    target_seconds = parse_timestamp_str(target_time_str)
    
    # 時間差が最小のフレームを探す
    closest_frame = min(frames, key=lambda x: abs(x[0] - target_seconds))
    return closest_frame


def replace_image_placeholders(markdown_text: str, frames: List[Tuple[float, str, str]]) -> str:
    """
    Markdown内の [IMAGE: MM:SS] プレースホルダーを実際の画像(Base64)に置換する
    """
    if not frames:
        return markdown_text
        
    import re
    
    def replacer(match):
        time_str = match.group(1)
        # 最も近いフレームを探す
        frame = find_closest_frame(time_str, frames)
        if frame:
            ts_str = frame[1]
            b64_data = frame[2]
            # Markdown画像形式に置換
            return f"\n\n![{ts_str}](data:image/jpeg;base64,{b64_data})\n*（{ts_str}の画面）*\n"
        else:
            return f"(画像が見つかりませんでした: {time_str})"

    # [IMAGE: MM:SS] のパターンを検索して置換
    # コロンの前後にスペースが入っていても許容する
    pattern = r'\[IMAGE:\s*(\d{1,2}:\d{2})\]'
    
    new_text = re.sub(pattern, replacer, markdown_text)
    return new_text


def clip_video_head(video_path: str, output_path: str, duration: int = 300) -> None:
    """
    動画の冒頭N秒を切り出す（再エンコードなしで高速処理）

    Args:
        video_path: 入力動画パス
        output_path: 出力動画パス
        duration: 切り出す秒数（デフォルト300秒=5分）
    """
    try:
        (
            ffmpeg
            .input(video_path, ss=0, t=duration)
            .output(output_path, c="copy")
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error:
        # copyで失敗した場合は再エンコードを試みる（安全策）
        try:
            (
                ffmpeg
                .input(video_path, ss=0, t=duration)
                .output(output_path)
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as e2:
            raise RuntimeError(f"動画クリッピング失敗: {e2}")
