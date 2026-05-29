import os
import subprocess
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

if TYPE_CHECKING:
    from ..config import Parameter


class ZhipuAIProcessor:
    def __init__(self, parameter: "Parameter"):
        self.parameter = parameter
        self.api_key = parameter.mimo_api_key
        self.model = parameter.mimo_model or "mimo-2.5"
        self.base_url = parameter.mimo_base_url or "https://api.mimo.ai/v1"

        # 改进 ffmpeg 和 ffprobe 检测
        self.ffmpeg_path = self._find_executable(
            str(parameter.ffmpeg.path) if parameter.ffmpeg and parameter.ffmpeg.path else "ffmpeg"
        )
        self.ffprobe_path = self._find_ffprobe(self.ffmpeg_path)

        self.console = parameter.console
        self.logger = parameter.logger
        self.console.info(f"AI 视频分析已初始化: model={self.model}, ffmpeg={self.ffmpeg_path}, ffprobe={self.ffprobe_path}")

        # 预检查可执行文件
        if not shutil.which(self.ffmpeg_path):
            self.console.warning(f"警告: 找不到 ffmpeg ({self.ffmpeg_path})，视频处理可能会失败")
        if not shutil.which(self.ffprobe_path):
            self.console.warning(f"警告: 找不到 ffprobe ({self.ffprobe_path})，视频处理可能会失败")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if OpenAI and self.api_key else None

    def _find_executable(self, path: str) -> str:
        """查找可执行文件路径"""
        if path and Path(path).exists() and Path(path).is_file():
            return str(Path(path).resolve())
        found = shutil.which(path)
        return found if found else path

    def _find_ffprobe(self, ffmpeg_path: str) -> str:
        """根据 ffmpeg 路径推找 ffprobe"""
        if ffmpeg_path and Path(ffmpeg_path).is_absolute():
            p = Path(ffmpeg_path)
            probe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
            probe_path = p.parent / probe_name
            if probe_path.exists():
                return str(probe_path.resolve())

        found = shutil.which("ffprobe")
        return found if found else "ffprobe"

    def extract_collage(self, video_path: Path, num_frames: int = 4) -> str:
        """
        从视频中提取关键帧并合成一张宫格图，返回 base64 编码
        """
        import base64
        import tempfile

        duration = self.get_video_duration(video_path)
        if duration <= 0:
            return ""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / "collage.jpg"

            # 计算间隔
            interval = duration / (num_frames + 1)

            # 构造 ffmpeg 滤镜指令，将 4 个画面合成 2x2 宫格
            select_filter = "+".join([f"eq(n,0)"] + [f"gt(t,{interval * i})" for i in range(1, num_frames)])
            filter_complex = (
                f"select='{select_filter}',"
                f"scale=320:-1,tile=2x2"
            )

            command = [
                self.ffmpeg_path, "-y",
                "-i", str(video_path),
                "-frames:v", "1",
                "-vf", filter_complex,
                "-q:v", "10",
                str(output_path)
            ]

            try:
                subprocess.run(command, capture_output=True, check=True)
                if output_path.exists():
                    with open(output_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                        return f"data:image/jpeg;base64,{encoded}"
            except FileNotFoundError:
                self.logger.error(f"提取帧失败: 找不到 ffmpeg: {self.ffmpeg_path}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"生成宫格图失败: {e}")

        return ""

    def get_video_duration(self, video_path: Path) -> float:
        """获取视频时长"""
        command = [
            self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except FileNotFoundError:
            self.console.error(f"找不到 ffprobe: {self.ffprobe_path}，请检查是否正确安装 FFmpeg")
            return 0.0
        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.error(f"获取视频时长失败: {e}")
            return 0.0

    async def process_video(self, video_path: Path):
        if not self.client:
            if not OpenAI:
                self.console.warning("未安装 openai SDK，请运行 'pip install openai' 安装")
            if not self.api_key:
                self.console.warning("未配置 AI API Key，请在 settings.json 中配置 mimo_api_key")
            return

        self.console.info(f"正在使用 {self.model} 处理视频: {video_path.name}")

        # 提取宫格图（4 帧合一）
        collage_base64 = self.extract_collage(video_path, num_frames=4)
        if not collage_base64:
            self.logger.error("无法从视频中提取帧并生成宫格图")
            return

        # 构造提示词
        prompt_reverse = (
            "你是一个专业的视频分析师。提供给你的是一张从视频中提取的 2x2 宫格关键帧合集图。"
            "请根据这张图展示的视频内容，反推该视频的提示词（Prompt）和分镜（Storyboard）。"
            "输出格式为 Markdown。"
        )
        prompt_game = "请基于上述视频内容，将其改写为一个具有游戏风格的故事或剧本。突出游戏感、任务、属性等元素。输出格式为 Markdown。"

        try:
            # 第一次调用：反推提示词和分镜（多模态请求）
            messages_reverse = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_reverse},
                        {"type": "image_url", "image_url": {"url": collage_base64}},
                    ]
                }
            ]

            response_reverse = self.client.chat.completions.create(
                model=self.model,
                messages=messages_reverse,
                max_tokens=1024,
            )
            reverse_content = response_reverse.choices[0].message.content

            # 第二次调用：游戏向改写（纯文本请求）
            messages_game = [
                {
                    "role": "user",
                    "content": f"以下是视频的内容分析：\n{reverse_content}\n\n{prompt_game}"
                }
            ]

            response_game = self.client.chat.completions.create(
                model=self.model,
                messages=messages_game,
                max_tokens=1536,
            )
            game_content = response_game.choices[0].message.content

            # 保存结果
            self.save_results(video_path, reverse_content, game_content)
            self.console.info(f"AI 处理完成: {video_path.name}")

        except Exception as e:
            self.logger.error(f"AI 处理失败: {e}")

    def save_results(self, video_path: Path, reverse_content: str, game_content: str):
        # 确保 mark 文件夹存在
        mark_dir = self.parameter.ROOT.joinpath("mark")
        mark_dir.mkdir(exist_ok=True)

        # 保存反推内容
        reverse_file = mark_dir / f"{video_path.stem}_反推.md"
        with open(reverse_file, "w", encoding="utf-8") as f:
            f.write(reverse_content)

        # 保存改写内容
        game_file = mark_dir / f"{video_path.stem}_改写.md"
        with open(game_file, "w", encoding="utf-8") as f:
            f.write(game_content)

        self.logger.info(f"结果已保存至: {reverse_file} 和 {game_file}")
