import os
import cv2
from typing import List


class VideoPlayer:
    def __init__(self, video_dir: str = "video"):
        """
        初始化视频播放器
        
        Args:
            video_dir (str): 视频文件夹路径，默认为"video"
        """
        self.video_dir = video_dir
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    def get_video_files(self) -> List[str]:
        """
        获取视频文件夹下的所有视频文件
        
        Returns:
            List[str]: 视频文件路径列表
        """
        if not os.path.exists(self.video_dir):
            print(f"视频目录 {self.video_dir} 不存在")
            return []
        
        video_files = []
        for file in os.listdir(self.video_dir):
            file_path = os.path.join(self.video_dir, file)
            if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in self.supported_formats:
                video_files.append(file_path)
        
        return video_files
    
    def play_video(self, video_path: str):
        """
        播放指定视频文件
        
        Args:
            video_path (str): 视频文件路径
            
        Returns:
            bool: 如果用户按'q'键退出则返回True，否则返回False
        """
        if not os.path.exists(video_path):
            print(f"视频文件 {video_path} 不存在")
            return False
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"无法打开视频文件 {video_path}")
            return False
        
        print(f"正在播放: {video_path}")
        print("按 'q' 键退出播放，按空格键暂停/继续")
        
        paused = False
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("视频播放完毕")
                    break
                
                cv2.imshow('Video Player', frame)
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return True  # 返回True表示用户主动退出
            elif key == ord(' '):
                paused = not paused
                if paused:
                    print("已暂停")
                else:
                    print("继续播放")
        
        cap.release()
        cv2.destroyAllWindows()
        return False  # 返回False表示正常播放完毕

    def play_all_videos(self):
        """
        播放视频目录下的所有视频文件，按顺序播放一次
        """
        video_files = self.get_video_files()
        
        if not video_files:
            print(f"在目录 {self.video_dir} 中未找到支持的视频文件")
            return
        
        print(f"找到 {len(video_files)} 个视频文件:")
        for i, video_file in enumerate(video_files):
            print(f"{i + 1}. {os.path.basename(video_file)}")
        
        for video_file in video_files:
            user_quit = self.play_video(video_file)
            if user_quit:  # 如果用户按'q'退出，则停止播放
                return
    
    def play_all_videos_loop(self):
        """
        循环播放视频目录下的所有视频文件，直到用户按下'q'键退出
        """
        video_files = self.get_video_files()
        
        if not video_files:
            print(f"在目录 {self.video_dir} 中未找到支持的视频文件")
            return
        
        print(f"找到 {len(video_files)} 个视频文件:")
        for i, video_file in enumerate(video_files):
            print(f"{i + 1}. {os.path.basename(video_file)}")
        
        print("\n开始循环播放所有视频，按 'q' 键退出...")
        
        while True:  # 无限循环播放所有视频
            for video_file in video_files:
                print(f"\n即将播放: {video_file}")
                user_quit = self.play_video(video_file)
                if user_quit:  # 如果用户按'q'退出，则停止循环
                    return


def main():
    """
    主函数，用于演示视频播放器的使用
    """
    player = VideoPlayer()
    player.play_all_videos_loop()  # 使用无限循环播放模式


if __name__ == "__main__":
    main()