import pygame
import sys
import random
import math
import time
import os
import numpy as np

# 初始化 Pygame
pygame.init()

# 游戏常量 - 回退到窗口模式
SCREEN_WIDTH = 1400  # 屏幕宽度
SCREEN_HEIGHT = 820  # 屏幕高度
PLAYER_RADIUS = 30  # 玩家半径
ITEM_RADIUS = 20  # 物品基础半径
BOMB_RADIUS = 20  # 炸弹半径
EXPLOSION_DURATION = 2.0  # 固定爆炸扩张时间为2秒
BOMB_TIMER = 3.0  # 炸弹3秒后爆炸
BASE_WARNING_TIME = 2.5  # 基础预警时间
MIN_WARNING_TIME = 1.0  # 最小预警时间
PLAYER_SPEED = 10  # 玩家基础移动速度
CRATER_DURATION = 3.0  # 弹坑保留时间
CRATER_SLOW_FACTOR = 0.7  # 弹坑内移动速度减半比例
CRATER_SCORE_THRESHOLD = 200  # 分数达到此值后出现弹坑
BASE_HEART_SPAWN_RATE = 0.4  # 基础爱心出现概率
SHIELD_DURATION = 5.0  # 护盾持续时间
MAX_EXPANSION_SPEED = 800  # 最大爆炸扩张速度（像素/秒）
MAX_BOMB_SPAWN_RATE = 0.3  # 炸弹生成速度上限（秒/个）
MIN_BOMB_SPAWN_RATE = 3.0  # 炸弹生成速度下限（秒/个）
HIT_EFFECT_DURATION = 1.0  # 受伤效果持续时间（秒）
HIGHSCORE_FILE = "highscore.txt"  # 最高分记录文件

# AI相关常量
AI_UPDATE_RATE = 0.01  # AI决策频率（秒）
AI_VISION_RADIUS = 1623  # AI视野半径
AI_SAFE_DISTANCE = 250 # AI安全距离

AI_EXPLOSION_PREDICTION_STEPS = 20  # 爆炸预测步数
AI_CRATER_WEIGHT = -50  # 弹坑权重惩罚
AI_EXPLOSION_AVOIDANCE_WEIGHT = -1000  # 爆炸规避基础权重
AI_TARGET_COMMITMENT_THRESHOLD = 30  # 目标锁定阈值（权重差小于此值时不切换目标）
AI_TARGET_LOCK_DURATION = 2.0  # 目标锁定最短持续时间（秒）
AI_ESCAPE_TARGET_CONFLICT_THRESHOLD = 90  # 规避与目标冲突阈值（度）
AI_MAX_TARGET_SWITCH_ATTEMPTS = 5  # 最大目标切换尝试次数
AI_BOUNDARY_SAFETY_THRESHOLD = 0.6  # 边界安全阈值

# 双人模式相关常量
PLAYER2_COLOR = (255, 100, 100)  # 玩家2颜色（粉红色）
PLAYER2_START_POS = (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)  # 玩家2起始位置
PLAYER1_START_POS = (SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2)  # 玩家1起始位置

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255)
WARNING_RED = (255, 0, 0, 150)
BG_COLOR = (10, 5, 20)  # 深蓝色星空背景
TEXT_COLOR = (230, 230, 255)  # 淡紫色文本

# 设置窗口图标
try:
    # 优先尝试加载ICO文件
    icon = pygame.image.load('icon.ico')
    pygame.display.set_icon(icon)
    print("窗口图标设置成功")
except:
    # 如果都没有，创建动态图标
    def create_icon():
        # 创建32x32的图标表面
        icon_surface = pygame.Surface((32, 32))
        icon_surface.fill((30, 60, 120))  # 深蓝色背景
        
        # 绘制星星图案
        pygame.draw.polygon(icon_surface, YELLOW, [
            (16, 4), (19, 12), (28, 12), (21, 17),
            (24, 26), (16, 20), (8, 26), (11, 17),
            (4, 12), (13, 12)
        ])
        
        # 绘制爆炸效果
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            end_x = 16 + math.cos(rad) * 12
            end_y = 16 + math.sin(rad) * 12
            pygame.draw.line(icon_surface, ORANGE, (16, 16), (end_x, end_y), 2)
        
        return icon_surface
    
    icon = create_icon()
    pygame.display.set_icon(icon)
    print("使用动态生成的窗口图标")

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("STARBOOM")
clock = pygame.time.Clock()

# 音频初始化
SAMPLE_RATE = 44100
CHANNELS = 2
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=CHANNELS, buffer=1024)

# 加载中文字体
font = pygame.font.SysFont('simhei', 24)
small_font = pygame.font.SysFont('simhei', 18)
score_font = pygame.font.SysFont('simhei', 28, bold=True)


# 性能优化：预计算常用值
SQRT_2 = math.sqrt(2)
PI_2 = math.pi * 2

# 最高分记录功能
def load_highscore():
    """加载最高分记录"""
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def save_highscore(score):
    """保存最高分记录"""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))
    except:
        pass

# 创建星空背景
def draw_stars_bg():
    # 在背景中绘制静态星星
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.random() * 1.5
        brightness = random.randint(100, 220)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)

# 性能优化：使用对象池管理粒子
class ParticlePool:
    def __init__(self, max_particles=1000):
        self.max_particles = max_particles
        self.particles = []
        self.active_count = 0
        
    def get_particle(self):
        """获取一个可用的粒子对象"""
        if self.active_count < self.max_particles:
            if len(self.particles) <= self.active_count:
                # 需要创建新粒子
                self.particles.append({})
            self.active_count += 1
            return self.particles[self.active_count - 1]
        return None
        
    def release_particle(self, index):
        """释放粒子回池"""
        if index < self.active_count - 1:
            # 交换位置，将释放的粒子移到末尾
            self.particles[index], self.particles[self.active_count - 1] = \
                self.particles[self.active_count - 1], self.particles[index]
        self.active_count -= 1
        
    def update(self):
        """更新所有粒子"""
        i = 0
        while i < self.active_count:
            particle = self.particles[i]
            if particle.get('active', True):
                # 更新粒子逻辑
                if callable(particle.get('update')):
                    particle['update']()
                i += 1
            else:
                self.release_particle(i)
                
    def draw(self):
        """绘制所有粒子"""
        for i in range(self.active_count):
            particle = self.particles[i]
            if callable(particle.get('draw')):
                particle['draw']()
                
    def reset(self):
        """重置粒子池"""
        self.active_count = 0

# 全局粒子池
particle_pool = ParticlePool(2000)

# 辅助函数
def calculate_bomb_spawn_time(score):
    """计算炸弹生成时间（基于分数）"""
    # 炸弹生成速度有上限和下限，使用更平缓的增长曲线
    base_time = max(MIN_BOMB_SPAWN_RATE, min(MAX_BOMB_SPAWN_RATE, 6.0 - score * 0.05))
    return base_time

def calculate_heart_spawn_rate(lives):
    """计算爱心出现概率（基于生命值）"""
    # 爱心出现概率随生命值增加而减小
    return BASE_HEART_SPAWN_RATE + (3 - lives) / 10
    
# 音频生成器类
class AudioGenerator:
    @staticmethod
    def _to_stereo(mono_array):
        """将单声道数组转换为立体声"""
        if len(mono_array.shape) == 1:
            return np.column_stack((mono_array, mono_array))
        return mono_array

    @staticmethod
    def collect_star():
        """收集星星音效"""
        duration = 0.3
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 清脆的高频音效
        freq1 = 800
        freq2 = 1200
        wave1 = 0.6 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.4 * np.sin(2 * np.pi * freq2 * t)
        
        # 包络
        envelope = np.exp(-4 * t) * (1 - np.exp(-30 * t))
        wave = (wave1 + wave2) * envelope
        wave = 32767 * wave
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

    @staticmethod
    def collect_heart():
        """收集爱心音效"""
        duration = 0.4
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 温暖的中频音效
        freq = 440
        wave = 0.7 * np.sin(2 * np.pi * freq * t)
        
        # 缓慢衰减的包络
        envelope = np.exp(-2 * t) * (1 - np.exp(-15 * t))
        wave = 32767 * wave * envelope
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

    @staticmethod
    def collect_shield():
        """收集护盾音效"""
        duration = 0.5
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 科幻感的音效
        freq = 600 * np.exp(-2 * t)
        wave = 0.5 * np.sin(2 * np.pi * freq * t)
        
        # 添加滤波效果
        filter_env = np.exp(-3 * t)
        wave = wave * filter_env
        
        # 包络
        envelope = np.exp(-2 * t) * (1 - np.exp(-20 * t))
        wave = 32767 * wave * envelope
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

    @staticmethod
    def explosion():
        """爆炸音效"""
        duration = 1.0
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 低频噪声
        wave = np.random.uniform(-1, 1, samples) * 0.5
        wave += 0.3 * np.sin(2 * np.pi * 60 * t)
        
        # 爆炸包络
        envelope = np.exp(-6 * t) * (1 - np.exp(-50 * t))
        
        # 高频衰减
        high_freq = np.random.uniform(-0.5, 0.5, samples) * np.exp(-20 * t)
        wave = wave + high_freq
        
        wave = 32767 * wave * envelope
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

    @staticmethod
    def player_hit():
        """玩家受伤音效"""
        duration = 0.3
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 不和谐的音效
        freq1 = 300
        freq2 = 450
        wave1 = 0.5 * np.sin(2 * np.pi * freq1 * t)
        wave2 = 0.3 * np.sin(2 * np.pi * freq2 * t)
        
        # 快速衰减
        envelope = np.exp(-8 * t) * (1 - np.exp(-40 * t))
        wave = (wave1 + wave2) * envelope
        wave = 32767 * wave
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

    @staticmethod
    def game_over():
        """游戏结束音效 - 增强版，包含多个频率的渐低失落感"""
        duration = 2.0  # 延长音效持续时间
        samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)
        
        # 多频率叠加，但不重叠，依次出现
        # 第一段：中高频，表达惊讶/震惊
        freq1 = 600 * np.exp(-3 * t[:len(t)//3])  # 快速下降
        wave1 = 0.5 * np.sin(2 * np.pi * freq1 * t[:len(t)//3])
        
        # 第二段：中频，表达失落
        freq2 = 400 * np.exp(-1.5 * (t[len(t)//3:len(t)*2//3] - t[len(t)//3]))
        wave2 = 0.6 * np.sin(2 * np.pi * freq2 * (t[len(t)//3:len(t)*2//3] - t[len(t)//3]))
        
        # 第三段：低频，表达终结感
        freq3 = 200 * np.exp(-2 * (t[len(t)*2//3:] - t[len(t)*2//3]))
        wave3 = 0.7 * np.sin(2 * np.pi * freq3 * (t[len(t)*2//3:] - t[len(t)*2//3]))
        
        # 组合波形，确保平滑过渡
        wave = np.zeros(samples)
        wave[:len(t)//3] = wave1
        wave[len(t)//3:len(t)*2//3] = wave2
        wave[len(t)*2//3:] = wave3
        
        # 整体包络，营造渐弱效果
        envelope = np.exp(-2 * t) * (1 - np.exp(-10 * t))
        wave = 32767 * wave * envelope
        wave = wave.astype(np.int16)
        return AudioGenerator._to_stereo(wave)

# 音效管理器
class SoundManager:
    def __init__(self):
        self.audio_gen = AudioGenerator()
        self.sounds = {}
        self.load_sounds()
        
    def load_sounds(self):
        """预生成所有音效"""
        self.sounds = {
            'collect_star': pygame.sndarray.make_sound(self.audio_gen.collect_star()),
            'collect_heart': pygame.sndarray.make_sound(self.audio_gen.collect_heart()),
            'collect_shield': pygame.sndarray.make_sound(self.audio_gen.collect_shield()),
            'explosion': pygame.sndarray.make_sound(self.audio_gen.explosion()),
            'player_hit': pygame.sndarray.make_sound(self.audio_gen.player_hit()),
            'game_over': pygame.sndarray.make_sound(self.audio_gen.game_over())
        }
        
    def play(self, sound_name, volume=0.5):
        """播放指定音效"""
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            sound.set_volume(volume)
            sound.play()
            
    def play_bgm(self):
        """播放背景音乐"""
        try:
            if os.path.exists("bgm.mp3"):
                pygame.mixer.music.load("bgm.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(loops=-1, start=2.0)  # 循环播放，从2.0s开始
            else:
                print("警告: 未找到bgm.mp3文件，背景音乐将不会播放")
        except Exception as e:
            print(f"加载背景音乐时出错: {e}")

# 得分飘字效果类
class ScorePopup:
    def __init__(self, x, y, value, color=YELLOW):
        self.x = x
        self.y = y
        self.value = value
        self.color = color
        self.lifetime = 1.5  # 飘字显示时间（秒）
        self.start_time = time.time()
        self.velocity_y = -50  # 向上飘动速度
        self.alpha = 255  # 透明度
        
    def update(self):
        # 更新位置和透明度
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 向上移动
        self.y += self.velocity_y * 0.016  # 假设60FPS
        
        # 逐渐淡出
        progress = elapsed / self.lifetime
        self.alpha = int(255 * (1 - progress))
        
        # 检查是否应该消失
        return elapsed >= self.lifetime or self.alpha <= 0
        
    def draw(self):
        if self.alpha <= 0:
            return
            
        # 创建带透明度的文本表面
        score_text = f"+{self.value}"
        text_surface = score_font.render(score_text, True, self.color)
        
        # 创建带透明度的表面
        alpha_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        alpha_surface.fill((0, 0, 0, 0))
        
        # 绘制带透明度的文本
        text_rect = text_surface.get_rect(center=(text_surface.get_width()//2, text_surface.get_height()//2))
        alpha_surface.blit(text_surface, text_rect)
        
        # 设置透明度
        alpha_surface.set_alpha(self.alpha)
        
        # 绘制到屏幕
        screen.blit(alpha_surface, (self.x - text_surface.get_width()//2, self.y - text_surface.get_height()//2))
        
# 游戏物品基类
class GameObject:
    def __init__(self, x, y, radius, color, active=True):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.active = active
        self.pulse_value = 0
        self.pulse_speed = 0.05
        
    def update(self):
        """更新物品状态"""
        if not self.active:
            return
            
        # 物品脉冲效果
        self.pulse_value += self.pulse_speed
        if self.pulse_value >= 2 * math.pi:
            self.pulse_value -= 2 * math.pi
            
    def respawn(self, objects=None):
        """重新生成物品位置"""
        # 确保坐标不会超出屏幕边界
        min_x = self.radius
        max_x = SCREEN_WIDTH - self.radius
        min_y = self.radius
        max_y = SCREEN_HEIGHT - self.radius
        
        # 确保边界有效
        if min_x >= max_x:
            min_x = 0
            max_x = SCREEN_WIDTH
        if min_y >= max_y:
            min_y = 0
            max_y = SCREEN_HEIGHT
            
        # 尝试生成不相交的位置
        max_attempts = 50
        for attempt in range(max_attempts):
            # 随机生成位置
            self.x = random.randint(min_x, max_x)
            self.y = random.randint(min_y, max_y)
            
            # 检查是否与其他物品重叠
            overlap = False
            if objects:
                for obj in objects:
                    if obj is not self and obj.active:
                        # 使用平方距离避免开方运算
                        distance_sq = (self.x - obj.x)**2 + (self.y - obj.y)**2
                        min_distance_sq = (self.radius + obj.radius + 20)**2
                        if distance_sq < min_distance_sq:
                            overlap = True
                            break
            
            # 如果没有重叠，则接受这个位置
            if not overlap:
                break
            
        self.active = True
        
    def distance_to(self, other):
        """计算到另一个对象的距离"""
        if hasattr(other, 'x') and hasattr(other, 'y'):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return math.sqrt((self.x - other[0])**2 + (self.y - other[1])**2)
        return float('inf')

# 物品类（星星、爱心、护盾）
class Item(GameObject):
    def __init__(self, item_type, two_player_mode=False):
        self.type = item_type  # 物品类型："star", "heart" 或 "shield"
        self.two_player_mode = two_player_mode  # 双人模式标志
        
        # 根据物品类型设置属性
        if self.type == "star":
            # 随机大小
            self.size = random.choice(["small", "medium", "large"])
            if self.size == "small":
                radius = ITEM_RADIUS
                self.value = 1
                color = YELLOW
            elif self.size == "medium":
                radius = ITEM_RADIUS + 3
                self.value = 2
                color = (255, 200, 0)
            else:  # large
                radius = ITEM_RADIUS + 6
                self.value = 3
                color = (255, 150, 0)
        elif self.type == "heart":
            radius = ITEM_RADIUS
            self.value = 1  # 增加生命值
            color = RED
        else:  # shield
            radius = ITEM_RADIUS
            self.value = 0  # 不增加分数，提供护盾
            color = CYAN
        
        super().__init__(0, 0, radius, color)
        self.respawn()
            
    def draw(self):
        if not self.active:
            return
            
        # 计算脉冲大小
        pulse_factor = 0.9 + 0.1 * math.sin(self.pulse_value)
        current_radius = self.radius * pulse_factor
        
        if self.type == "star":
            self._draw_star(current_radius)
        elif self.type == "heart":
            self._draw_heart(current_radius)
        else:  # shield
            self._draw_shield(current_radius)
    
    def _draw_star(self, radius):
        """绘制五角星"""
        points = []
        for i in range(5):
            # 外角点
            outer_angle = math.pi/2 + i * 2*math.pi/5
            points.append((self.x + radius * math.cos(outer_angle), 
                         self.y + radius * math.sin(outer_angle)))
            
            # 内角点
            inner_angle = math.pi/2 + (i + 0.5) * 2*math.pi/5
            points.append((self.x + radius/2 * math.cos(inner_angle), 
                         self.y + radius/2 * math.sin(inner_angle)))
        
        # 绘制五角星填充
        pygame.draw.polygon(screen, self.color, points)
        
        # 绘制五角星边框
        pygame.draw.polygon(screen, WHITE, points, 1)
        
        # 绘制星星光点
        for angle in range(0, 360, 45):
            rad = math.radians(angle + self.pulse_value * 10)
            dx = math.cos(rad) * radius * 0.5
            dy = math.sin(rad) * radius * 0.5
            pygame.draw.line(screen, WHITE, 
                             (self.x - dx, self.y - dy),
                             (self.x + dx, self.y + dy), 1)
    
    def _draw_heart(self, radius):
        """绘制爱心形状"""
        # 使用数学公式绘制爱心
        scale = radius / 12  # 调整缩放因子
        
        # 创建表面用于绘制爱心
        heart_size = int(radius * 3)  # 扩大爱心显示区域
        heart_surface = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
        
        # 绘制爱心主体
        points = []
        for t in range(0, 360, 5):  # 增加采样点使爱心更平滑
            t_rad = math.radians(t)
            # 爱心参数方程
            x = 16 * (math.sin(t_rad) ** 3)
            y = 13 * math.cos(t_rad) - 5 * math.cos(2*t_rad) - 2 * math.cos(3*t_rad) - math.cos(4*t_rad)
            # 缩放并移动到中心
            x = x * scale + heart_size/2
            y = -y * scale + heart_size/2  # 负号是因为y轴向下
            points.append((x, y))
        
        # 绘制爱心填充
        if len(points) > 2:
            pygame.draw.polygon(heart_surface, self.color, points)
            # 绘制爱心边框
            pygame.draw.polygon(heart_surface, WHITE, points, 1)
        
        # 将爱心绘制到屏幕上
        screen.blit(heart_surface, (self.x - heart_size/2, self.y - heart_size/2))
    
    def _draw_shield(self, radius):
        """绘制护盾"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(radius))
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(radius), 2)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(radius - 3), 2)
        
        # 绘制护盾内部图案
        inner_radius = radius * 0.6
        pygame.draw.circle(screen, (200, 255, 255), (int(self.x), int(self.y)), int(inner_radius))
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(inner_radius), 1)

# 炸弹类
class Bomb(GameObject):
    def __init__(self, score, craters, two_player_mode=False):
        self.score = score
        self.two_player_mode = two_player_mode
        self.expansion_speed = min(800, 50 + score * 0.5)  # 使用平均分数
            
        self.plant_time = time.time()
        self.exploding = False
        self.explosion_start_time = 0
        self.explosion_shape = random.choice(["circle", "rectangle"])
        self.warning_visible = True
        self.last_warning_toggle = time.time()
        self.warning_time = max(1.0, 2.5 - score * 0.02)  # 使用平均分数
        self.particles = []
        self.max_particles = 100  # 最大粒子数
        
        # 调用父类初始化
        super().__init__(0, 0, BOMB_RADIUS, ORANGE)
        self.respawn(craters)
        
    def respawn(self, craters=None):
        # 尝试生成不与弹坑重叠的炸弹位置
        max_attempts = 50  # 最大尝试次数
        for attempt in range(max_attempts):
            # 随机生成炸弹位置
            self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
            self.y = random.randint(self.radius, SCREEN_HEIGHT - self.radius)
            
            # 检查是否与现有弹坑重叠
            overlap = False
            if craters:
                for crater in craters:
                    if crater.explosion_shape == "circle":
                        # 圆形弹坑检测 - 使用平方距离避免开方
                        distance_sq = (self.x - crater.x)**2 + (self.y - crater.y)**2
                        min_distance_sq = (crater.radius + self.expansion_speed)**2
                        if distance_sq < min_distance_sq:
                            overlap = True
                            break
                    else:
                        # 矩形弹坑检测
                        rect_x = crater.x - crater.radius
                        rect_y = crater.y - crater.radius
                        rect_width = crater.radius * 2
                        rect_height = crater.radius * 2
                        
                        # 检查炸弹爆炸范围是否与矩形弹坑重叠
                        bomb_rect_x = self.x - self.expansion_speed
                        bomb_rect_y = self.y - self.expansion_speed
                        bomb_rect_width = self.expansion_speed * 2
                        bomb_rect_height = self.expansion_speed * 2
                        
                        if (rect_x < bomb_rect_x + bomb_rect_width and
                            rect_x + rect_width > bomb_rect_x and
                            rect_y < bomb_rect_y + bomb_rect_height and
                            rect_y + rect_height > bomb_rect_y):
                            overlap = True
                            break
            
            # 如果没有重叠，则接受这个位置
            if not overlap:
                break
        
        self.active = True
        self.plant_time = time.time()
        self.exploding = False
        
    def create_particles(self):
        """创建爆炸粒子"""
        for _ in range(min(50, self.max_particles - len(self.particles))):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            lifetime = random.uniform(0.5, 1.5)
            size = random.uniform(2, 6)
            color = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 0), (255, 50, 0)])
            
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'size': size,
                'color': color
            })
    
    def update_particles(self):
        """更新爆炸粒子"""
        i = 0
        while i < len(self.particles):
            particle = self.particles[i]
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['lifetime'] -= 0.016  # 假设60FPS
            
            # 移除生命周期结束的粒子
            if particle['lifetime'] <= 0:
                self.particles.pop(i)
            else:
                i += 1
        
    def update(self):
        """更新炸弹状态"""
        current_time = time.time()
        
        if not self.active:
            return
            
        # 预警闪烁效果
        if current_time - self.last_warning_toggle > 0.2:  # 每0.2秒切换一次
            self.warning_visible = not self.warning_visible
            self.last_warning_toggle = current_time
            
        # 检查是否应该爆炸（考虑预警时间）
        if not self.exploding and current_time - self.plant_time >= (3.0 - self.warning_time):
            self.exploding = True  # 开始爆炸
            self.explosion_start_time = current_time  # 记录爆炸开始时间
            self.create_particles()  # 创建爆炸粒子
            
        # 更新爆炸粒子
        if self.exploding:
            self.update_particles()
            
        # 检查爆炸是否结束
        if self.exploding and current_time - self.explosion_start_time >= 2.0:  # 爆炸持续时间
            self.active = False  # 爆炸结束
            
    def draw(self):
        if not self.active:
            return
            
        if not self.exploding:
            # 绘制炸弹
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 80, 0), (int(self.x), int(self.y)), self.radius, 2)
            
            # 绘制引线
            fuse_length = 5
            pygame.draw.line(screen, (100, 40, 0), (self.x, self.y - self.radius), 
                            (self.x, self.y - self.radius - fuse_length), 2)
            
            # 绘制十字准心
            self._draw_crosshair()
            
            # 绘制预警标志（覆盖整个爆炸范围）
            if self.warning_visible:
                # 计算最大爆炸半径（速度×时间）
                max_explosion_radius = int(self.expansion_speed * 2.0)
                if self.explosion_shape == "circle":
                    # 圆形预警 - 覆盖整个爆炸范围
                    s = pygame.Surface((max_explosion_radius*2, max_explosion_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 0, 0, 80), (max_explosion_radius, max_explosion_radius), max_explosion_radius, 2)
                    screen.blit(s, (self.x - max_explosion_radius, self.y - max_explosion_radius))
                else:
                    # 矩形预警 - 覆盖整个爆炸范围
                    rect_width = max_explosion_radius * 2
                    rect_height = max_explosion_radius * 2
                    rect_x = self.x - rect_width // 2
                    rect_y = self.y - rect_height // 2
                    s = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
                    pygame.draw.rect(s, (255, 0, 0, 80), (0, 0, rect_width, rect_height), 2)
                    screen.blit(s, (rect_x, rect_y))
        else:
            # 绘制爆炸效果
            current_time = time.time()
            time_elapsed = current_time - self.explosion_start_time
            current_explosion_radius = int(self.expansion_speed * time_elapsed)
            max_possible_radius = int(self.expansion_speed * 2.0)
            current_explosion_radius = min(current_explosion_radius, max_possible_radius)
            
            # 绘制爆炸粒子
            for particle in self.particles:
                alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
                size = particle['size'] * (particle['lifetime'] / particle['max_lifetime'])
                color = (*particle['color'], alpha)
                
                s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (int(size), int(size)), int(size))
                screen.blit(s, (particle['x'] - size, particle['y'] - size))
            
            if self.explosion_shape == "circle":
                # 圆形爆炸 - 多层效果
                for i in range(3):
                    radius = current_explosion_radius - i * 30
                    if radius > 0:
                        alpha = 200 - i * 60
                        s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                        pygame.draw.circle(s, (255, 165, 0, alpha), (radius, radius), radius)
                        screen.blit(s, (self.x - radius, self.y - radius))
                
                # 爆炸中心
                pygame.draw.circle(screen, (255, 100, 0), (int(self.x), int(self.y)), current_explosion_radius // 4)
            else:
                # 矩形爆炸 - 多层效果
                for i in range(3):
                    width = current_explosion_radius - i * 30
                    height = current_explosion_radius - i * 30
                    if width > 0 and height > 0:
                        alpha = 200 - i * 60
                        rect_x = self.x - width // 2
                        rect_y = self.y - height // 2
                        s = pygame.Surface((width, height), pygame.SRCALPHA)
                        s.fill((255, 165, 0, alpha))
                        screen.blit(s, (rect_x, rect_y))
                
                # 爆炸中心
                rect_width = current_explosion_radius // 2
                rect_height = current_explosion_radius // 2
                rect_x = self.x - rect_width // 2
                rect_y = self.y - rect_height // 2
                pygame.draw.rect(screen, (255, 100, 0), (rect_x, rect_y, rect_width, rect_height))
    
    def _draw_crosshair(self):
        """绘制十字准心"""
        # 十字准心长度和宽度
        crosshair_length = 15
        crosshair_width = 2
        
        # 十字准心颜色（使用醒目的红色）
        crosshair_color = (255, 50, 50)
        
        # 绘制水平线
        pygame.draw.line(screen, crosshair_color, 
                        (self.x - crosshair_length, self.y), 
                        (self.x + crosshair_length, self.y), crosshair_width)
        
        # 绘制垂直线
        pygame.draw.line(screen, crosshair_color, 
                        (self.x, self.y - crosshair_length), 
                        (self.x, self.y + crosshair_length), crosshair_width)
        
        # 绘制外圈圆环
        pygame.draw.circle(screen, crosshair_color, (int(self.x), int(self.y)), crosshair_length, 1)
            
    def is_player_in_explosion(self, player_pos):
        """检查玩家是否在爆炸范围内"""
        if not self.exploding:
            return False
            
        player_x, player_y = player_pos
        # 使用时间×速度计算爆炸半径
        current_time = time.time()
        time_elapsed = current_time - self.explosion_start_time
        current_explosion_radius = int(self.expansion_speed * time_elapsed)
        max_possible_radius = int(self.expansion_speed * 2.0)
        current_explosion_radius = min(current_explosion_radius, max_possible_radius)
        
        if self.explosion_shape == "circle":
            # 圆形爆炸检测 - 使用平方距离避免开方
            distance_sq = (player_x - self.x)**2 + (player_y - self.y)**2
            return distance_sq <= current_explosion_radius**2
        else:
            # 矩形爆炸检测
            rect_x = self.x - current_explosion_radius // 2
            rect_y = self.y - current_explosion_radius // 2
            return (rect_x <= player_x <= rect_x + current_explosion_radius and
                    rect_y <= player_y <= rect_y + current_explosion_radius)
    
    def destroy_items_in_explosion(self, items):
        """爆炸时销毁范围内的物品"""
        if not self.exploding:
            return
            
        # 使用时间×速度计算爆炸半径
        current_time = time.time()
        time_elapsed = current_time - self.explosion_start_time
        current_explosion_radius = int(self.expansion_speed * time_elapsed)
        max_possible_radius = int(self.expansion_speed * 2.0)
        current_explosion_radius = min(current_explosion_radius, max_possible_radius)
        
        for item in items:
            if not item.active:
                continue
                
            if self.explosion_shape == "circle":
                # 圆形爆炸检测 - 使用平方距离避免开方
                distance_sq = (item.x - self.x)**2 + (item.y - self.y)**2
                if distance_sq <= current_explosion_radius**2:
                    item.active = False
            else:
                # 矩形爆炸检测
                rect_x = self.x - current_explosion_radius // 2
                rect_y = self.y - current_explosion_radius // 2
                if (rect_x <= item.x <= rect_x + current_explosion_radius and
                    rect_y <= item.y <= rect_y + current_explosion_radius):
                    item.active = False

# 弹坑类
class Crater(GameObject):
    def __init__(self, x, y, radius, explosion_shape):
        self.explosion_shape = explosion_shape  # 弹坑形状（与爆炸形状一致）
        self.create_time = time.time()  # 弹坑创建时间
        
        # 调用父类初始化
        super().__init__(x, y, radius, GRAY)
        
    def update(self):
        """更新弹坑状态"""
        if not self.active:
            return
            
        # 检查弹坑是否应该消失
        if time.time() - self.create_time >= CRATER_DURATION:  # 弹坑保留时间
            self.active = False
            
    def draw(self):
        if not self.active:
            return
            
        if self.explosion_shape == "circle":
            # 绘制圆形弹坑 - 多层效果
            for i in range(3):
                radius = self.radius - i * 10
                if radius > 0:
                    alpha = 150 - i * 40
                    s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
                    screen.blit(s, (self.x - radius, self.y - radius))
            
            # 弹坑边框
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x), int(self.y)), self.radius, 2)
        else:
            # 绘制矩形弹坑 - 多层效果
            for i in range(3):
                width = self.radius * 2 - i * 20
                height = self.radius * 2 - i * 20
                if width > 0 and height > 0:
                    alpha = 150 - i * 40
                    rect_x = self.x - width // 2
                    rect_y = self.y - height // 2
                    s = pygame.Surface((width, height), pygame.SRCALPHA)
                    s.fill((*self.color, alpha))
                    screen.blit(s, (rect_x, rect_y))
            
            # 弹坑边框
            rect_x = self.x - self.radius
            rect_y = self.y - self.radius
            rect_width = self.radius * 2
            rect_height = self.radius * 2
            pygame.draw.rect(screen, (50, 50, 50), (rect_x, rect_y, rect_width, rect_height), 2)
            
# 玩家类
class Player:
    def __init__(self, player_id=1, start_pos=None, two_player_mode=False):
        self.player_id = player_id  # 玩家ID：1或2
        self.two_player_mode = two_player_mode  # 双人模式标志
        self.score = 0
        self.lives = 3  # 每个玩家有自己的生命值
        self.active = True  # 玩家是否活跃（生命值>0）
        
        # 设置起始位置
        if start_pos:
            self.x, self.y = start_pos
        else:
            if player_id == 1:
                self.x, self.y = PLAYER1_START_POS
            else:
                self.x, self.y = PLAYER2_START_POS
                
        self.radius = PLAYER_RADIUS
        # 根据玩家ID设置颜色
        self.color = BLUE if player_id == 1 else PLAYER2_COLOR
        self.base_speed = PLAYER_SPEED
        self.speed = self.base_speed
        self.in_crater = False
        self.shield_active = False
        self.shield_start_time = 0
        
        # 控制方式设置
        self.use_mouse_control = (player_id == 1)  # 玩家1默认鼠标，玩家2默认键盘
        self.keyboard_controls = {
            'up': [pygame.K_w, pygame.K_UP] if player_id == 1 else [pygame.K_i],
            'down': [pygame.K_s, pygame.K_DOWN] if player_id == 1 else [pygame.K_k],
            'left': [pygame.K_a, pygame.K_LEFT] if player_id == 1 else [pygame.K_j],
            'right': [pygame.K_d, pygame.K_RIGHT] if player_id == 1 else [pygame.K_l]
        }
        
        self.direction = [0, 0]
        self.trail_particles = []
        self.max_trail_particles = 20
        
        # AI相关属性
        self.ai_enabled = False  # 默认关闭AI
        self.ai_last_update = 0
        self.ai_target_pos = None
        self.ai_target_type = None
        self.ai_debug_info = []
        
        # 目标锁定机制
        self.locked_target = None
        self.lock_start_time = 0
        self.lock_duration = 0
        self.last_target_switch = 0
        self.target_commitment = True
        
        # 边界感知
        self.boundary_awareness = True
        self.safe_directions = []
        self.boundary_distances = {}
        
        # 受伤效果相关属性
        self.hit_effect_active = False
        self.hit_effect_start_time = 0
        self.hit_flash_visible = True
        self.last_flash_toggle = 0
        self.hit_particles = []
        self.max_hit_particles = 30
        
    def switch_control_mode(self):
        """切换控制方式（鼠标/键盘）"""
        self.use_mouse_control = not self.use_mouse_control
        
    def move_with_mouse(self, mouse_x, mouse_y):
        """鼠标控制移动"""
        if self.ai_enabled:
            return  # AI模式下忽略鼠标控制
            
        # 计算鼠标位置与玩家位置的向量
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        
        # 计算距离
        distance = math.hypot(dx, dy)
        
        # 如果距离很小，直接设置位置到鼠标位置
        if distance < self.speed:
            self.x = mouse_x
            self.y = mouse_y
            self.direction = [0, 0]
        else:
            # 归一化向量
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                
            # 更新位置
            self.x += dx * self.speed
            self.y += dy * self.speed
            
            # 更新方向
            self.direction = [dx, dy]
            
        # 确保玩家不会移出屏幕
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
        # 添加尾焰粒子（性能优化：限制粒子数量）
        if self.direction != [0, 0] and len(self.trail_particles) < self.max_trail_particles:
            self.trail_particles.append({
                'x': self.x - self.direction[0] * 20,
                'y': self.y - self.direction[1] * 20,
                'size': random.uniform(4, 10),
                'life': 1.0
            })
    
    def move_with_keyboard(self, keys):
        """键盘控制移动"""
        if self.ai_enabled:
            return  # AI模式下忽略键盘控制
            
        # 根据按键移动
        dx, dy = 0, 0
        
        # 上移
        if any(keys[key] for key in self.keyboard_controls['up']):
            dy -= 1
        # 下移
        if any(keys[key] for key in self.keyboard_controls['down']):
            dy += 1
        # 左移
        if any(keys[key] for key in self.keyboard_controls['left']):
            dx -= 1
        # 右移
        if any(keys[key] for key in self.keyboard_controls['right']):
            dx += 1
            
        # 归一化对角线移动
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/sqrt(2)
            dy *= 0.7071
            
        if dx != 0 or dy != 0:
            self.direction = [dx, dy]
        else:
            self.direction = [0, 0]
            
        # 更新位置
        self.x += dx * self.speed
        self.y += dy * self.speed
            
        # 边界检查
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
        # 添加尾焰粒子（性能优化：限制粒子数量）
        if self.direction != [0, 0] and len(self.trail_particles) < self.max_trail_particles:
            self.trail_particles.append({
                'x': self.x - self.direction[0] * 20,
                'y': self.y - self.direction[1] * 20,
                'size': random.uniform(2, 5),
                'life': 1.0
            })
    
    def update_trail(self):
        """更新尾焰粒子"""
        i = 0
        while i < len(self.trail_particles):
            particle = self.trail_particles[i]
            particle['life'] -= 0.05  # 粒子生命周期减少
            if particle['life'] <= 0:
                self.trail_particles.pop(i)
            else:
                i += 1
    
    def update_speed(self, craters):
        """更新玩家速度（考虑弹坑影响）"""
        # 检查是否在弹坑内
        self.in_crater = False
        for crater in craters:
            if not crater.active:
                continue
                
            if crater.explosion_shape == "circle":
                # 圆形弹坑检测
                distance_sq = (self.x - crater.x)**2 + (self.y - crater.y)**2
                if distance_sq <= crater.radius**2:  # 使用平方避免开方
                    self.in_crater = True
                    break
            else:
                # 矩形弹坑检测
                rect_x = crater.x - crater.radius
                rect_y = crater.y - crater.radius
                rect_width = crater.radius * 2
                rect_height = crater.radius * 2
                if (rect_x <= self.x <= rect_x + rect_width and
                    rect_y <= self.y <= rect_y + rect_height):
                    self.in_crater = True
                    break
        
        # 根据是否在弹坑内调整速度
        self.speed = self.base_speed * (CRATER_SLOW_FACTOR if self.in_crater else 1.0)
    
    def activate_shield(self):
        """激活护盾"""
        self.shield_active = True
        self.shield_start_time = time.time()
    
    def update_shield(self):
        """更新护盾状态"""
        # 检查护盾是否应该消失
        if self.shield_active and time.time() - self.shield_start_time >= SHIELD_DURATION:
            self.shield_active = False
    
    def activate_hit_effect(self):
        """激活受伤效果"""
        self.hit_effect_active = True
        self.hit_effect_start_time = time.time()
        self.hit_flash_visible = True
        self.last_flash_toggle = time.time()
        
        # 创建受伤粒子效果
        self.create_hit_particles()
    
    def create_hit_particles(self):
        """创建受伤粒子"""
        for _ in range(min(20, self.max_hit_particles - len(self.hit_particles))):  # 限制粒子数量
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            lifetime = random.uniform(0.5, 1.0)
            size = random.uniform(3, 6)
            color = random.choice([(255, 100, 100), (255, 150, 150), (255, 200, 200)])
            
            self.hit_particles.append({
                'x': self.x,
                'y': self.y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'size': size,
                'color': color
            })
    
    def update_hit_effect(self):
        """更新受伤效果"""
        if not self.hit_effect_active:
            return
            
        current_time = time.time()
        
        # 更新闪烁效果
        if current_time - self.last_flash_toggle > 0.1:  # 每0.1秒切换一次
            self.hit_flash_visible = not self.hit_flash_visible
            self.last_flash_toggle = current_time
        
        # 检查受伤效果是否应该结束
        if current_time - self.hit_effect_start_time >= HIT_EFFECT_DURATION:
            self.hit_effect_active = False
        
        # 更新受伤粒子
        i = 0
        while i < len(self.hit_particles):
            particle = self.hit_particles[i]
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['lifetime'] -= 0.016  # 假设60FPS
            
            # 移除生命周期结束的粒子
            if particle['lifetime'] <= 0:
                self.hit_particles.pop(i)
            else:
                i += 1
    
    def draw(self):
        """绘制玩家 - 增强差异化版本"""
        # 绘制尾焰粒子 - 根据玩家ID差异化
        for particle in self.trail_particles:
            alpha = int(255 * particle['life'])
            size = particle['size'] * particle['life']
            
            if self.player_id == 1:
                # 玩家1：蓝色渐变尾焰
                flame_color = (100, 150, 255, alpha)  # 深蓝色
            else:
                # 玩家2：粉色渐变尾焰
                flame_color = (255, 100, 150, alpha)  # 粉红色
                
            s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, flame_color, (int(size), int(size)), int(size))
            screen.blit(s, (particle['x'] - size, particle['y'] - size))
        
        # 绘制受伤粒子 - 根据玩家ID差异化
        for particle in self.hit_particles:
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            size = particle['size'] * (particle['lifetime'] / particle['max_lifetime'])
            
            if self.player_id == 1:
                # 玩家1：蓝色系受伤粒子
                hit_colors = [(100, 100, 255), (150, 150, 255), (200, 200, 255)]
            else:
                # 玩家2：红色系受伤粒子
                hit_colors = [(255, 100, 100), (255, 150, 150), (255, 200, 200)]
                
            color = (*random.choice(hit_colors), alpha)
            
            s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(size), int(size)), int(size))
            screen.blit(s, (particle['x'] - size, particle['y'] - size))
        
        # 新增：受伤闪烁效果 - 只在可见时绘制玩家
        if not self.hit_effect_active or self.hit_flash_visible:
            # 绘制玩家主体
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            
            # 添加玩家细节边框 - 根据玩家ID差异化
            if self.player_id == 1:
                border_color = (0, 100, 255)  # 深蓝色边框
            else:
                border_color = (255, 50, 100)  # 深粉色边框
                
            pygame.draw.circle(screen, border_color, (int(self.x), int(self.y)), self.radius, 3)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius - 5, 2)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius - 10, 1)
            
            # 修改：根据玩家ID设置不同的光泽效果
            if self.player_id == 1:
                # 玩家1：蓝色渐变光泽效果
                highlight_colors = [
                    (100, 255, 255),  # 主高光 - 青蓝色
                    (150, 255, 255),  # 次高光 - 浅青蓝
                    (200, 255, 255)   # 边缘高光 - 很浅的青蓝
                ]
            else:
                # 玩家2：粉色渐变光泽效果
                highlight_colors = [
                    (255, 200, 255),  # 主高光 - 粉红色
                    (255, 220, 255),  # 次高光 - 浅粉红
                    (255, 240, 255)   # 边缘高光 - 很浅的粉红
                ]
            
            # 绘制多层光泽效果
            for i, color in enumerate(highlight_colors):
                glow_size = self.radius // (3 + i)  # 不同层次的大小
                pygame.draw.circle(screen, color, 
                                 (int(self.x - 3 + i), int(self.y - 3 + i)), glow_size)
            
            # 绘制护盾效果 - 根据玩家ID差异化
            if self.shield_active:
                shield_radius = self.radius + 10
                if self.player_id == 1:
                    # 玩家1：蓝色系护盾
                    shield_color = (0, 200, 255)  # 青蓝色护盾
                else:
                    # 玩家2：粉色系护盾
                    shield_color = (255, 100, 200)  # 粉红色护盾
                    
                for i in range(3):
                    alpha = 100 - i * 30
                    s = pygame.Surface((shield_radius*2, shield_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*shield_color, alpha), 
                                     (shield_radius, shield_radius), shield_radius + i*2, 2)
                    screen.blit(s, (self.x - shield_radius, self.y - shield_radius))
            
            # 如果在弹坑中，显示减速效果 - 根据玩家ID差异化
            if self.in_crater:
                if self.player_id == 1:
                    crater_color = (100, 100, 200, 100)  # 蓝色系减速效果
                else:
                    crater_color = (200, 100, 100, 100)  # 红色系减速效果
                    
                pygame.draw.circle(screen, crater_color, 
                                 (int(self.x), int(self.y)), self.radius + 5, 3)
   
    def get_pos(self):
        """获取玩家位置"""
        return (self.x, self.y)
    
    def distance_to(self, position):
        """计算到指定位置的距离"""
        pos_x, pos_y = position
        return math.sqrt((self.x - pos_x)**2 + (self.y - pos_y)**2)
    
    def toggle_ai(self):
        """切换AI控制"""
        self.ai_enabled = not self.ai_enabled
        
    def ai_control(self, stars, hearts, shields, bombs, craters, current_score=0):
        """增强版AI决策系统 - 整合智能规避策略"""
        # 更新玩家分数
        self.score = current_score
        
        current_time = time.time()
        if current_time - self.ai_last_update < AI_UPDATE_RATE:
            return
                
        self.ai_last_update = current_time
        self.ai_debug_info = []
        
        # 检查当前锁定目标是否仍然有效
        if self.locked_target and not self.is_target_valid(self.locked_target):
            self.locked_target = None
            self.ai_debug_info.append("目标失效，解除锁定")
        
        # 如果当前有锁定目标且在锁定期内，优先处理锁定目标
        if (self.locked_target and 
            current_time - self.lock_start_time < self.lock_duration and
            self.target_commitment):
            
            # 检查是否需要紧急规避
            need_evasion, evasion_direction = self.check_immediate_danger(bombs)
            
            if need_evasion:
                # 检查规避方向与目标方向是否冲突
                target_direction = self.calculate_direction_to_target(self.locked_target)
                conflict_angle = self.calculate_angle_between_directions(evasion_direction, target_direction)
                
                if conflict_angle > AI_ESCAPE_TARGET_CONFLICT_THRESHOLD:
                    # 冲突严重，执行智能规避
                    nearest_bomb = self.find_most_dangerous_bomb(bombs)
                    if nearest_bomb:
                        self.smart_escape_from_bomb(nearest_bomb, bombs)
                        self.ai_debug_info.append("规避冲突，优先生存")
                        return
                else:
                    # 冲突不大，可以兼顾规避和收集
                    self.balanced_evasion_and_collection(evasion_direction, self.locked_target, bombs)
                    return
            else:
                # 没有立即危险，正常处理锁定目标
                if self.is_target_reachable(self.locked_target, bombs):
                    self.process_locked_target()
                    return
                else:
                    # 目标不可达，解除锁定
                    self.locked_target = None
                    self.ai_debug_info.append("目标不可达，解除锁定")
        
        # 收集视野范围内的所有对象
        visible_objects = self.get_visible_objects(stars, hearts, shields, bombs, craters)
        
        # 计算每个对象的权重（考虑目标锁定机制）
        weighted_objects = []
        for obj in visible_objects:
            weight = self.calculate_enhanced_object_weight(obj, bombs, craters)
            
            # 如果是当前锁定目标，给予额外权重奖励
            if obj == self.locked_target:
                weight += AI_TARGET_COMMITMENT_THRESHOLD * 2
                
            weighted_objects.append((obj, weight))
        
        # 按权重排序（从高到低）
        weighted_objects.sort(key=lambda x: x[1], reverse=True)
        
        if not weighted_objects:
            # 没有可见目标，执行安全待机
            self.safe_idle_movement(bombs)
            return
        
        # 选择最佳目标（考虑目标锁定阈值）
        best_obj, best_weight = weighted_objects[0]
        
        # 检查是否需要切换目标（考虑锁定阈值）
        should_switch = self.should_switch_target(best_obj, best_weight, weighted_objects)
        
        if should_switch:
            # 切换目标前检查规避冲突
            need_evasion, evasion_direction = self.check_immediate_danger(bombs)
            
            if need_evasion:
                # 检查新目标是否与规避方向冲突
                target_direction = self.calculate_direction_to_target(best_obj)
                conflict_angle = self.calculate_angle_between_directions(evasion_direction, target_direction)
                
                if conflict_angle > AI_ESCAPE_TARGET_CONFLICT_THRESHOLD:
                    # 冲突严重，执行智能规避
                    nearest_bomb = self.find_most_dangerous_bomb(bombs)
                    if nearest_bomb:
                        self.smart_escape_from_bomb(nearest_bomb, bombs)
                        self.ai_debug_info.append("目标冲突，优先规避")
                        return
            
            # 切换目标并锁定
            self.locked_target = best_obj
            self.lock_start_time = current_time
            self.lock_duration = AI_TARGET_LOCK_DURATION
            self.last_target_switch = current_time
            
            self.ai_debug_info.append(f"锁定新目标: {self.get_object_type(best_obj)}")
            self.ai_debug_info.append(f"目标权重: {best_weight:.1f}")
        else:
            # 保持当前目标或选择最佳目标
            if not self.locked_target:
                self.locked_target = best_obj
                self.lock_start_time = current_time
                self.lock_duration = AI_TARGET_LOCK_DURATION
            
            best_obj = self.locked_target
            self.ai_debug_info.append(f"保持目标: {self.get_object_type(best_obj)}")
            self.ai_debug_info.append("目标锁定中...")
        
        # 处理选定的目标
        self.ai_target_pos = (best_obj.x, best_obj.y)
        self.ai_target_type = self.get_object_type(best_obj)
        
        # 如果是炸弹，执行智能逃离策略
        if hasattr(best_obj, 'type') and best_obj.type == "bomb":
            self.smart_escape_from_bomb(best_obj, bombs)
        else:
            # 安全移动至目标（考虑规避）
            need_evasion, evasion_direction = self.check_immediate_danger(bombs)
            
            if need_evasion:
                # 有立即危险，执行平衡策略
                self.balanced_evasion_and_collection(evasion_direction, best_obj, bombs)
            else:
                # 安全移动
                self.safe_move_toward_target(best_obj, bombs)
                
    def get_visible_objects(self, stars, hearts, shields, bombs, craters):
        """获取视野范围内的所有对象"""
        visible_objects = []
        
        # 检查星星
        for star in stars:
            if star.active and self.distance_to((star.x, star.y)) <= AI_VISION_RADIUS:
                visible_objects.append(star)
        
        # 检查爱心
        for heart in hearts:
            if heart.active and self.distance_to((heart.x, heart.y)) <= AI_VISION_RADIUS:
                visible_objects.append(heart)
        
        # 检查护盾
        for shield in shields:
            if shield.active and self.distance_to((shield.x, shield.y)) <= AI_VISION_RADIUS:
                visible_objects.append(shield)
        
        # 检查炸弹（始终可见，但权重为负）
        for bomb in bombs:
            if bomb.active and self.distance_to((bomb.x, bomb.y)) <= AI_VISION_RADIUS:
                bomb.type = "bomb"  # 标记为炸弹类型
                visible_objects.append(bomb)
        
        return visible_objects

    def calculate_enhanced_object_weight(self, obj, bombs, craters):
        """增强版权重计算 - 考虑爆炸风险和弹坑影响"""
        distance = self.distance_to((obj.x, obj.y))
        base_weight = 0
        
        # 基础权重（原有逻辑）
        if hasattr(obj, 'type'):
            if obj.type == "shield":
                base_weight = 1000  # 护盾最高优先级
            elif obj.type == "heart":
                base_weight = 800   # 爱心次高优先级
            elif obj.type == "star":
                # 根据星星大小设置权重
                if hasattr(obj, 'size'):
                    if obj.size == "large":
                        base_weight = 600
                    elif obj.size == "medium":
                        base_weight = 400
                    else:  # small
                        base_weight = 200
            elif obj.type == "bomb":
                base_weight = -1000  # 炸弹为负权重
        
        # 距离权重（距离越近权重越高）
        distance_weight = max(0, AI_VISION_RADIUS - distance) / AI_VISION_RADIUS * 200
        
        # 爆炸风险权重
        explosion_risk = self.calculate_explosion_risk((obj.x, obj.y), bombs)
        explosion_weight = explosion_risk * (-500)  # 风险越高，权重越低
        
        # 弹坑影响权重
        crater_penalty = self.calculate_crater_penalty((obj.x, obj.y), craters) * (-100)
        
        # 护盾保护权重（如果有护盾，免疫爆炸风险影响）
        if self.shield_active:
            explosion_weight *= 0  # 护盾状态下爆炸风险影响降低为0
        
        total_weight = base_weight + distance_weight + explosion_weight + crater_penalty
        
        return total_weight

    def calculate_explosion_risk(self, target_pos, bombs):
        """计算目标位置的爆炸风险"""
        total_risk = 0
        target_x, target_y = target_pos
        
        for bomb in bombs:
            if not bomb.active:
                continue
                
            # 计算炸弹到目标的距离
            bomb_distance = math.sqrt((target_x - bomb.x)**2 + (target_y - bomb.y)**2)
            
            # 预测爆炸风险
            if bomb.exploding:
                # 正在爆炸的炸弹
                time_elapsed = time.time() - bomb.explosion_start_time
                current_radius = bomb.expansion_speed * time_elapsed
                max_radius = bomb.expansion_speed * EXPLOSION_DURATION
                
                if bomb_distance <= max_radius:
                    # 在爆炸范围内
                    risk_factor = 1.0 - (bomb_distance / max_radius)
                    total_risk += risk_factor
            else:
                # 未爆炸的炸弹 - 预测爆炸时间
                time_to_explosion = (bomb.plant_time + BOMB_TIMER - bomb.warning_time) - time.time()
                if time_to_explosion > 0:
                    # 预测爆炸时的半径
                    predicted_radius = bomb.expansion_speed * min(EXPLOSION_DURATION, time_to_explosion * 2)
                    
                    if bomb_distance <= predicted_radius:
                        risk_factor = 1.0 - (bomb_distance / predicted_radius)
                        # 时间因素：爆炸时间越近风险越高
                        time_factor = max(0, 1.0 - time_to_explosion / 3.0)
                        total_risk += risk_factor * (0.3 + 0.7 * time_factor)
        
        return min(total_risk, 2.0)  # 限制最大风险值为2.0

    def calculate_crater_penalty(self, target_pos, craters):
        """计算路径上的弹坑惩罚"""
        start_pos = (self.x, self.y)
        target_x, target_y = target_pos
        
        # 计算路径方向
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return 0
        
        # 归一化方向
        dx /= distance
        dy /= distance
        
        # 检查路径上的弹坑
        crater_count = 0
        step_size = 20  # 检查步长
        steps = int(distance / step_size) + 1
        
        for i in range(steps):
            check_x = self.x + dx * i * step_size
            check_y = self.y + dy * i * step_size
            
            for crater in craters:
                if not crater.active:
                    continue
                    
                if crater.explosion_shape == "circle":
                    # 圆形弹坑检测
                    crater_distance = math.sqrt((check_x - crater.x)**2 + (check_y - crater.y)**2)
                    if crater_distance <= crater.radius:
                        crater_count += 1
                        break
                else:
                    # 矩形弹坑检测
                    rect_x = crater.x - crater.radius
                    rect_y = crater.y - crater.radius
                    rect_width = crater.radius * 2
                    rect_height = crater.radius * 2
                    
                    if (rect_x <= check_x <= rect_x + rect_width and
                        rect_y <= check_y <= rect_y + rect_height):
                        crater_count += 1
                        break
        
        # 返回弹坑密度（路径上弹坑的比例）
        return crater_count / max(1, steps)

    def should_switch_target(self, best_obj, best_weight, weighted_objects):
        """判断是否应该切换目标（考虑锁定阈值）"""
        if not self.locked_target:
            return True  # 没有当前目标，需要切换
        
        # 找到当前锁定目标的权重
        current_weight = None
        for obj, weight in weighted_objects:
            if obj == self.locked_target:
                current_weight = weight
                break
        
        # 如果当前目标不在可见列表中，需要切换
        if current_weight is None:
            return True
        
        # 计算权重差
        weight_diff = best_weight - current_weight
        
        # 如果最佳目标权重显著高于当前目标，则切换
        if weight_diff > AI_TARGET_COMMITMENT_THRESHOLD:
            return True
        
        # 如果当前目标已经完成或失效，切换
        if not self.is_target_valid(self.locked_target):
            return True
        
        # 否则保持当前目标
        return False

    def is_target_valid(self, target):
        """检查目标是否仍然有效"""
        if not hasattr(target, 'active'):
            return False
        return target.active

    def is_target_reachable(self, target, bombs):
        """检查目标是否可达（考虑爆炸风险）"""
        if not self.is_target_valid(target):
            return False
        
        # 计算路径安全性
        path_safety = self.calculate_path_safety((self.x, self.y), (target.x, target.y), bombs)
        
        # 如果有护盾，降低安全阈值
        safety_threshold = 0.3 if self.shield_active else 0.6
        
        return path_safety > safety_threshold and self.distance_to((target.x, target.y)) < AI_VISION_RADIUS * 1.5

    def calculate_path_safety(self, start_pos, end_pos, bombs):
        """计算路径安全性系数（0.0-1.0）"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 计算路径方向和长度
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return 1.0
        
        # 归一化方向
        dx /= distance
        dy /= distance
        
        # 预测路径安全性
        safety_score = 1.0
        step_size = distance / AI_EXPLOSION_PREDICTION_STEPS
        move_time_per_step = step_size / self.speed
        
        for step in range(AI_EXPLOSION_PREDICTION_STEPS):
            # 预测当前位置
            predict_x = start_x + dx * step * step_size
            predict_y = start_y + dy * step * step_size
            predict_time = step * move_time_per_step
            
            # 检查每个炸弹对该位置的风险
            for bomb in bombs:
                if not bomb.active:
                    continue
                    
                bomb_risk = self.calculate_position_risk((predict_x, predict_y), bomb, predict_time)
                safety_score *= (1.0 - bomb_risk * 0.3)  # 每个炸弹最多降低30%安全性
        
        return max(0.0, min(1.0, safety_score))

    def calculate_position_risk(self, position, bomb, predict_time):
        """计算特定位置在特定时间点的炸弹风险"""
        pos_x, pos_y = position
        bomb_distance = math.sqrt((pos_x - bomb.x)**2 + (pos_y - bomb.y)**2)
        
        current_time = time.time()
        risk = 0
        
        if bomb.exploding:
            # 正在爆炸的炸弹
            explosion_elapsed = current_time - bomb.explosion_start_time + predict_time
            if explosion_elapsed < 0:
                return 0
                
            current_radius = bomb.expansion_speed * min(explosion_elapsed, EXPLOSION_DURATION)
            
            if bomb_distance <= current_radius:
                risk = 1.0 - (bomb_distance / current_radius)
        else:
            # 未爆炸的炸弹
            time_to_explosion = (bomb.plant_time + BOMB_TIMER - bomb.warning_time) - current_time
            if time_to_explosion > 0:
                # 预测到达时间点的爆炸状态
                arrival_explosion_time = time_to_explosion - predict_time
                
                if arrival_explosion_time <= 0:
                    # 到达时炸弹已经爆炸
                    explosion_elapsed = -arrival_explosion_time
                    current_radius = bomb.expansion_speed * min(explosion_elapsed, EXPLOSION_DURATION)
                    
                    if bomb_distance <= current_radius:
                        risk = 1.0 - (bomb_distance / current_radius)
                else:
                    # 到达时炸弹尚未爆炸，但可能很快爆炸
                    if arrival_explosion_time < 1.0:  # 1秒内会爆炸
                        # 计算爆炸风险（时间越近风险越高）
                        risk = (1.0 - arrival_explosion_time) * 0.5
        
        return risk

    def get_object_type(self, obj):
        """获取对象类型"""
        if hasattr(obj, 'type'):
            if obj.type == "heart":
                return "爱心"
            elif obj.type == "shield":
                return "护盾"
            elif obj.type == "star":
                if hasattr(obj, 'size'):
                    return f"{obj.size}型星星"
            elif obj.type == "bomb":
                return "炸弹"
        return "未知"
   
    def check_immediate_danger(self, bombs):
        """检查是否需要立即规避"""
        immediate_danger = False
        evasion_direction = None
        highest_risk = 0
        
        for bomb in bombs:
            if not bomb.active:
                continue
                
            risk, direction = self.assess_bomb_risk(bomb)
            
            if risk > highest_risk:
                highest_risk = risk
                evasion_direction = direction
                immediate_danger = risk > 0.3  # 风险阈值
        
        return immediate_danger, evasion_direction

    def assess_bomb_risk(self, bomb):
        """评估单个炸弹的风险和规避方向"""
        current_time = time.time()
        risk = 0
        evasion_direction = None
        
        if bomb.exploding:
            # 正在爆炸的炸弹
            time_elapsed = current_time - bomb.explosion_start_time
            current_radius = bomb.expansion_speed * min(time_elapsed, EXPLOSION_DURATION)
            
            distance = self.distance_to((bomb.x, bomb.y))
            
            if distance <= current_radius:
                # 已经在爆炸范围内
                risk = 1.0
                # 远离爆炸中心
                dx = self.x - bomb.x
                dy = self.y - bomb.y
                if dx == 0 and dy == 0:
                    # 如果在中心，随机方向
                    angle = random.uniform(0, 2 * math.pi)
                    evasion_direction = (math.cos(angle), math.sin(angle))
                else:
                    # 归一化逃离方向
                    length = math.sqrt(dx*dx + dy*dy)
                    evasion_direction = (dx/length, dy/length)
            elif distance <= current_radius + 50:  # 安全边际
                # 接近爆炸边缘
                risk = 0.7
                # 预判规避方向
                time_to_reach = (distance - current_radius) / self.speed
                explosion_growth = bomb.expansion_speed * time_to_reach
                
                if distance <= current_radius + explosion_growth:
                    # 会与爆炸相遇，需要规避
                    dx = self.x - bomb.x
                    dy = self.y - bomb.y
                    if dx != 0 or dy != 0:
                        length = math.sqrt(dx*dx + dy*dy)
                        evasion_direction = (dx/length, dy/length)
                    else:
                        angle = random.uniform(0, 2 * math.pi)
                        evasion_direction = (math.cos(angle), math.sin(angle))
        else:
            # 未爆炸的炸弹，预测风险
            time_to_explosion = (bomb.plant_time + BOMB_TIMER - bomb.warning_time) - current_time
            
            if time_to_explosion <= 2.0:  # 2秒内爆炸
                distance = self.distance_to((bomb.x, bomb.y))
                predicted_radius = bomb.expansion_speed * min(EXPLOSION_DURATION, 2.0)
                
                if distance <= predicted_radius:
                    risk = 0.8 - (time_to_explosion / 2.0) * 0.3
                    
                    # 计算规避方向（远离炸弹）
                    dx = self.x - bomb.x
                    dy = self.y - bomb.y
                    if dx != 0 or dy != 0:
                        length = math.sqrt(dx*dx + dy*dy)
                        evasion_direction = (dx/length, dy/length)
        
        return risk, evasion_direction

    def smart_escape_from_bomb(self, bomb, bombs):
        """智能炸弹逃离 - 集成新的规避策略"""
        if hasattr(bomb, 'explosion_shape'):
            if bomb.explosion_shape == "circle":
                # 使用增强的圆形炸弹规避策略
                escape_direction = self.enhanced_circular_bomb_escape(bomb)
                self.ai_debug_info.append("圆形炸弹:泥石流算法")
            else:
                # 矩形炸弹使用原有策略
                escape_direction = self.enhanced_rectangular_bomb_escape(bomb)
                self.ai_debug_info.append("矩形炸弹:边界感知")
        else:
            # 默认使用基础规避
            escape_direction = self.basic_bomb_escape(bomb)
            self.ai_debug_info.append("未知炸弹:基础规避")
        
        # 应用规避移动
        if escape_direction:
            dx, dy = escape_direction
            
            # 根据危险程度调整速度
            if bomb.exploding:
                escape_speed = self.speed * (1.8 if not self.shield_active else 1.3)
                self.ai_debug_info.append("紧急规避!")
            else:
                escape_speed = self.speed * (1.5 if not self.shield_active else 1.2)
            
            self.x += dx * escape_speed
            self.y += dy * escape_speed
            self.direction = [dx, dy]
            
            # 添加详细的策略信息
            self.add_escape_strategy_debug(bomb, escape_direction)
        else:
            # 备用方案
            self.move_away_from((bomb.x, bomb.y))
            self.ai_debug_info.append("执行备用规避方案")

    def enhanced_circular_bomb_escape(self, bomb):
        """增强版圆形炸弹逃离策略 - 泥石流算法 + 角落逃生"""
        # 计算基础逃离方向（远离炸弹中心）
        base_dx = self.x - bomb.x
        base_dy = self.y - bomb.y
        
        # 如果正好在炸弹中心，随机方向
        if base_dx == 0 and base_dy == 0:
            angle = random.uniform(0, 2 * math.pi)
            base_dx = math.cos(angle)
            base_dy = math.sin(angle)
        
        # 归一化基础方向
        length = math.sqrt(base_dx*base_dx + base_dy*base_dy)
        if length > 0:
            base_dx /= length
            base_dy /= length
        
        # 计算爆炸最大半径
        max_explosion_radius = bomb.expansion_speed * EXPLOSION_DURATION
        
        # 定义四个角落
        corners = [
            (0, 0),                    # 左上角
            (SCREEN_WIDTH, 0),         # 右上角  
            (0, SCREEN_HEIGHT),        # 左下角
            (SCREEN_WIDTH, SCREEN_HEIGHT)  # 右下角
        ]
        
        # 分析爆炸范围与边界的关系
        left_boundary_affected = bomb.x - max_explosion_radius <= 30
        right_boundary_affected = bomb.x + max_explosion_radius >= SCREEN_WIDTH - 30
        top_boundary_affected = bomb.y - max_explosion_radius <= 30
        bottom_boundary_affected = bomb.y + max_explosion_radius >= SCREEN_HEIGHT - 30
        
        # 检查每个角落的情况
        corner_analysis = []
        for i, (corner_x, corner_y) in enumerate(corners):
            # 计算角落到炸弹的距离
            distance_to_corner = math.sqrt((corner_x - bomb.x)**2 + (corner_y - bomb.y)**2)
            
            # 判断爆炸是否会触及这个角落
            explosion_reaches_corner = distance_to_corner <= max_explosion_radius + 73
            
            # 判断与几条边界相交
            boundaries_touched = 0
            if (i == 0 or i == 2) and left_boundary_affected:  # 左边界
                boundaries_touched += 1
            if (i == 1 or i == 3) and right_boundary_affected:  # 右边界
                boundaries_touched += 1
            if (i == 0 or i == 1) and top_boundary_affected:  # 上边界
                boundaries_touched += 1
            if (i == 2 or i == 3) and bottom_boundary_affected:  # 下边界
                boundaries_touched += 1
            
            corner_analysis.append({
                'position': (corner_x, corner_y),
                'distance': distance_to_corner,
                'explosion_reaches': explosion_reaches_corner,
                'boundaries_touched': boundaries_touched,
                'safe': not explosion_reaches_corner
            })
        
        # 选择最佳规避策略
        best_direction = self.select_circular_escape_strategy(bomb, base_dx, base_dy, corner_analysis, max_explosion_radius)
        
        return best_direction

    def select_circular_escape_strategy(self, bomb, base_dx, base_dy, corner_analysis, max_explosion_radius):
        """选择圆形炸弹的逃离策略"""
        # 寻找安全的角落（爆炸不会触及的）
        safe_corners = [corner for corner in corner_analysis if corner['safe']]
        
        if safe_corners:
            # 有安全角落，优先逃向最近的安全角落
            closest_safe_corner = min(safe_corners, key=lambda c: math.sqrt(
                (c['position'][0] - self.x)**2 + (c['position'][1] - self.y)**2
            ))
            
            dx = closest_safe_corner['position'][0] - self.x
            dy = closest_safe_corner['position'][1] - self.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                return (dx/length, dy/length)
        
        # 没有安全角落，分析边界情况
        dangerous_corners = [corner for corner in corner_analysis if not corner['safe']]
        
        # 按边界触及数量分类
        single_boundary_corners = [c for c in dangerous_corners if c['boundaries_touched'] == 1]
        double_boundary_corners = [c for c in dangerous_corners if c['boundaries_touched'] == 2]
        
        if single_boundary_corners:
            # 使用泥石流算法 - 沿着边界垂直方向逃离
            return self.mudflow_algorithm(bomb, single_boundary_corners[0], base_dx, base_dy)
        elif double_boundary_corners:
            # 死亡角落逃生策略
            return self.death_corner_escape(bomb, double_boundary_corners[0], max_explosion_radius)
        else:
            # 备用方案：基础逃离方向
            return (base_dx, base_dy)

    def mudflow_algorithm(self, bomb, corner, base_dx, base_dy):
        """泥石流算法 - 沿着边界垂直方向逃离"""
        corner_x, corner_y = corner['position']
        
        # 确定受影响的是哪条边界
        boundaries = []
        if corner_x == 0:  # 左边界
            boundaries.append('left')
        elif corner_x == SCREEN_WIDTH:  # 右边界
            boundaries.append('right')
        if corner_y == 0:  # 上边界
            boundaries.append('top')
        elif corner_y == SCREEN_HEIGHT:  # 下边界
            boundaries.append('bottom')
        
        # 选择与边界垂直的方向
        if 'left' in boundaries or 'right' in boundaries:
            # 水平边界，垂直方向逃离（上下）
            if self.y < SCREEN_HEIGHT / 2:
                return (0, 1)  # 向下
            else:
                return (0, -1)  # 向上
        else:
            # 垂直边界，水平方向逃离（左右）
            if self.x < SCREEN_WIDTH / 2:
                return (1, 0)  # 向右
            else:
                return (-1, 0)  # 向左

    def death_corner_escape(self, bomb, corner, max_explosion_radius):
        """死亡角落逃生策略"""
        corner_x, corner_y = corner['position']
        
        # 计算爆炸范围是否能完全覆盖角落
        distance_to_corner = math.sqrt((corner_x - bomb.x)**2 + (corner_y - bomb.y)**2)
        explosion_can_reach_corner = distance_to_corner <= max_explosion_radius
        
        if not explosion_can_reach_corner:
            # 爆炸无法触及角落，躲在这里
            dx = corner_x - self.x
            dy = corner_y - self.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                return (dx/length, dy/length)
        else:
            # 爆炸能触及角落，拼死一搏冲向对角方向
            if corner_x == 0 and corner_y == 0:  # 左上角 -> 右下角
                target_x, target_y = SCREEN_WIDTH, SCREEN_HEIGHT
            elif corner_x == SCREEN_WIDTH and corner_y == 0:  # 右上角 -> 左下角
                target_x, target_y = 0, SCREEN_HEIGHT
            elif corner_x == 0 and corner_y == SCREEN_HEIGHT:  # 左下角 -> 右上角
                target_x, target_y = SCREEN_WIDTH, 0
            else:  # 右下角 -> 左上角
                target_x, target_y = 0, 0
            
            dx = target_x - self.x
            dy = target_y - self.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                return (dx/length, dy/length)
        
        # 备用方案：直接远离炸弹
        dx = self.x - bomb.x
        dy = self.y - bomb.y
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            return (dx/length, dy/length)
        
        return (1, 0)  # 最终备用

    def enhanced_rectangular_bomb_escape(self, bomb):
        """增强版矩形炸弹逃离策略 - 考虑边界爆炸范围"""
        # 计算爆炸最大范围
        max_explosion_size = bomb.expansion_speed * EXPLOSION_DURATION
        
        # 计算到四条边界的距离和安全性
        boundaries = [
            {'type': 'left', 'distance': self.x, 'direction': (-1, 0)},
            {'type': 'right', 'distance': SCREEN_WIDTH - self.x, 'direction': (1, 0)},
            {'type': 'top', 'distance': self.y, 'direction': (0, -1)},
            {'type': 'bottom', 'distance': SCREEN_HEIGHT - self.y, 'direction': (0, 1)}
        ]
        
        # 评估每个边界方向的安全性
        safe_directions = []
        danger_directions = []
        
        for boundary in boundaries:
            boundary_type = boundary['type']
            boundary_distance = boundary['distance']
            direction = boundary['direction']
            
            # 检查这个边界是否会被爆炸影响
            boundary_affected = False
            boundary_safety = 1.0  # 初始安全性
            
            if boundary_type == 'left':
                # 左边界：检查炸弹右边界是否会影响左边界
                bomb_left_effect = bomb.x - max_explosion_size <= 30
                boundary_affected = bomb_left_effect
                if bomb_left_effect:
                    # 计算安全性（距离炸弹影响区域越远越安全）
                    safety_distance = max(0, self.x - max_explosion_size)
                    boundary_safety = min(1.0, safety_distance / AI_SAFE_DISTANCE)
            
            elif boundary_type == 'right':
                # 右边界：检查炸弹左边界是否会影响右边界
                bomb_right_effect = bomb.x + max_explosion_size >= SCREEN_WIDTH - 30
                boundary_affected = bomb_right_effect
                if bomb_right_effect:
                    safety_distance = max(0, (SCREEN_WIDTH - self.x) - max_explosion_size)
                    boundary_safety = min(1.0, safety_distance / AI_SAFE_DISTANCE)
            
            elif boundary_type == 'top':
                # 上边界：检查炸弹下边界是否会影响上边界
                bomb_top_effect = bomb.y - max_explosion_size <= 30
                boundary_affected = bomb_top_effect
                if bomb_top_effect:
                    safety_distance = max(0, self.y - max_explosion_size)
                    boundary_safety = min(1.0, safety_distance / AI_SAFE_DISTANCE)
            
            else:  # bottom
                # 下边界：检查炸弹上边界是否会影响下边界
                bomb_bottom_effect = bomb.y + max_explosion_size >= SCREEN_HEIGHT - 30
                boundary_affected = bomb_bottom_effect
                if bomb_bottom_effect:
                    safety_distance = max(0, (SCREEN_HEIGHT - self.y) - max_explosion_size)
                    boundary_safety = min(1.0, safety_distance / AI_SAFE_DISTANCE)
            
            # 计算基础逃离方向（远离炸弹）
            base_dx = self.x - bomb.x
            base_dy = self.y - bomb.y
            base_length = math.sqrt(base_dx*base_dx + base_dy*base_dy)
            if base_length > 0:
                base_dx /= base_length
                base_dy /= base_length
            
            # 计算与基础方向的一致性
            alignment = base_dx * direction[0] + base_dy * direction[1]
            
            boundary_info = {
                'direction': direction,
                'safety_score': boundary_safety,
                'alignment': alignment,
                'distance': boundary_distance,
                'affected': boundary_affected
            }
            
            if boundary_safety >= AI_BOUNDARY_SAFETY_THRESHOLD:
                safe_directions.append(boundary_info)
            else:
                danger_directions.append(boundary_info)
        
        # 选择最佳逃离方向
        if safe_directions:
            # 从安全方向中选择
            best_direction_info = None
            best_score = -float('inf')
            
            for direction_info in safe_directions:
                # 安全性分数
                safety_score = direction_info['safety_score'] * 0.5
                
                # 方向一致性分数
                alignment_score = direction_info['alignment'] * 0.3
                
                # 距离分数（距离边界越远越好）
                distance_score = (1.0 - direction_info['distance'] / AI_SAFE_DISTANCE) * 0.2
                
                total_score = safety_score + alignment_score + distance_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_direction_info = direction_info
        else:
            # 没有安全方向，从危险方向中选择相对最安全的
            best_direction_info = None
            best_score = -float('inf')
            
            for direction_info in danger_directions:
                # 安全性分数（权重更高）
                safety_score = direction_info['safety_score'] * 0.6
                
                # 方向一致性分数
                alignment_score = direction_info['alignment'] * 0.2
                
                # 距离惩罚（危险方向距离越近惩罚越大）
                distance_penalty = (direction_info['distance'] / AI_SAFE_DISTANCE) * 0.2
                
                total_score = safety_score + alignment_score - distance_penalty
                
                if total_score > best_score:
                    best_score = total_score
                    best_direction_info = direction_info
        
        # 如果有最佳方向，使用它；否则使用基础逃离方向
        if best_direction_info:
            escape_dx, escape_dy = best_direction_info['direction']
            
            # 根据安全性调整基础方向的混合权重
            safety_weight = best_direction_info['safety_score']
            base_weight = 0.7  # 基础方向权重
            boundary_weight = 0.3 * safety_weight  # 边界方向权重（受安全性影响）
            
            # 计算最终方向
            final_dx = base_dx * base_weight + escape_dx * boundary_weight
            final_dy = base_dy * base_weight + escape_dy * boundary_weight
            
            # 归一化
            length = math.sqrt(final_dx*final_dx + final_dy*final_dy)
            if length > 0:
                final_dx /= length
                final_dy /= length
            
            return (final_dx, final_dy)
        
        # 备用方案：直接远离炸弹
        return (base_dx, base_dy)

    def basic_bomb_escape(self, bomb):
        """基础炸弹逃离策略 - 简单远离炸弹中心"""
        # 计算远离炸弹的方向
        dx = self.x - bomb.x
        dy = self.y - bomb.y
        
        # 如果正好在炸弹中心，随机方向
        if dx == 0 and dy == 0:
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
        
        # 归一化方向向量
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        return (dx, dy)

    def balanced_evasion_and_collection(self, evasion_direction, target, bombs):
        """平衡规避与收集的策略"""
        if not target:
            self.execute_evasion(evasion_direction, bombs)
            return
        
        # 计算混合方向（规避为主，稍微偏向目标）
        evade_dx, evade_dy = evasion_direction
        
        # 计算目标方向
        target_x, target_y = target.x, target.y
        target_dx = target_x - self.x
        target_dy = target_y - self.y
        target_length = math.sqrt(target_dx*target_dx + target_dy*target_dy)
        if target_length > 0:
            target_dx /= target_length
            target_dy /= target_length
        else:
            target_dx, target_dy = 0, 0
        
        # 混合权重：规避占70%，目标占30%
        blend_dx = evade_dx * 0.7 + target_dx * 0.3
        blend_dy = evade_dy * 0.7 + target_dy * 0.3
        
        # 归一化
        length = math.sqrt(blend_dx*blend_dx + blend_dy*blend_dy)
        if length > 0:
            blend_dx /= length
            blend_dy /= length
        
        # 应用移动
        self.direction = [blend_dx, blend_dy]
        move_speed = self.speed * (1.2 if not self.shield_active else 1.0)
        self.x += blend_dx * move_speed
        self.y += blend_dy * move_speed
        
        self.ai_debug_info.append("平衡规避与收集")

    def execute_evasion(self, evasion_direction, bombs):
        """执行纯规避机动"""
        evade_dx, evade_dy = evasion_direction
        
        # 应用规避移动
        self.direction = [evade_dx, evade_dy]
        evade_speed = self.speed * (1.5 if not self.shield_active else 1.2)
        self.x += evade_dx * evade_speed
        self.y += evade_dy * evade_speed
        
        # 清除当前目标（专注规避）
        self.locked_target = None
        self.ai_target_pos = None
        self.ai_target_type = None
        
        self.ai_debug_info.append("执行纯规避机动")

    def add_escape_strategy_debug(self, bomb, escape_direction):
        """添加规避策略的调试信息"""
        if hasattr(bomb, 'explosion_shape') and bomb.explosion_shape == "circle":
            # 分析当前策略类型
            dx, dy = escape_direction
            
            # 判断策略类型
            if abs(dx) < 0.1:  # 主要垂直移动
                strategy = "泥石流算法-垂直逃离"
            elif abs(dy) < 0.1:  # 主要水平移动
                strategy = "泥石流算法-水平逃离"
            else:
                # 检查是否朝向角落
                target_x = self.x + dx * 100
                target_y = self.y + dy * 100
                
                # 判断目标方向是否接近某个角落
                corners = [
                    (0, 0), (SCREEN_WIDTH, 0),
                    (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT)
                ]
                
                min_distance = float('inf')
                for corner_x, corner_y in corners:
                    distance = math.sqrt((target_x - corner_x)**2 + (target_y - corner_y)**2)
                    if distance < min_distance:
                        min_distance = distance
                
                if min_distance < 50:  # 接近某个角落
                    strategy = "死亡角落-对角冲刺"
                else:
                    strategy = "基础远离策略"
            
            self.ai_debug_info.append(f"策略: {strategy}")

    def safe_move_toward_target(self, target, bombs):
        """安全移动至目标 - 能够处理位置元组或Item对象"""
        # 提取目标位置
        if hasattr(target, 'x') and hasattr(target, 'y'):
            # 如果是Item对象，提取其位置
            target_x, target_y = target.x, target.y
        elif isinstance(target, (tuple, list)) and len(target) == 2:
            # 如果是位置元组
            target_x, target_y = target
        else:
            # 无效的目标，执行安全待机
            self.safe_idle_movement(bombs)
            return
        
        # 基础移动方向
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
        
        dx /= distance
        dy /= distance
        
        # 检查前方是否有立即危险
        immediate_danger = False
        look_ahead_distance = 50  # 前瞻距离
        
        for bomb in bombs:
            if not bomb.active:
                continue
                
            # 检查前方位置
            ahead_x = self.x + dx * look_ahead_distance
            ahead_y = self.y + dy * look_ahead_distance
            
            if self.calculate_position_risk((ahead_x, ahead_y), bomb, look_ahead_distance/self.speed) > 0.3:
                immediate_danger = True
                break
        
        if immediate_danger and not self.shield_active:
            # 有立即危险且无护盾，执行规避
            self.evade_danger(bombs)
        else:
            # 安全移动
            self.direction = [dx, dy]
            self.x += dx * self.speed
            self.y += dy * self.speed

    def evade_danger(self, bombs):
        """危险规避机动"""
        # 寻找最安全的方向
        best_direction = None
        best_safety = -1
        
        # 测试8个主要方向
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            test_dx = math.cos(rad)
            test_dy = math.sin(rad)
            
            # 评估该方向的安全性
            safety_score = 1.0
            look_ahead = 100  # 评估距离
            
            for bomb in bombs:
                test_x = self.x + test_dx * look_ahead
                test_y = self.y + test_dy * look_ahead
                risk = self.calculate_position_risk((test_x, test_y), bomb, look_ahead/self.speed)
                safety_score *= (1.0 - risk)
            
            if safety_score > best_safety:
                best_safety = safety_score
                best_direction = (test_dx, test_dy)
        
        if best_direction:
            self.direction = [best_direction[0], best_direction[1]]
            self.x += best_direction[0] * self.speed
            self.y += best_direction[1] * self.speed
            self.ai_debug_info.append("执行规避机动!")

    def safe_idle_movement(self, bombs):
        """安全待机移动 - 在没有目标时保持安全"""
        # 检查当前位置的安全性
        current_risk = 0
        for bomb in bombs:
            current_risk += self.calculate_position_risk((self.x, self.y), bomb, 0)
        
        if current_risk > 0.2 and not self.shield_active:
            # 当前位置有风险，移动到安全区域
            self.move_to_safe_zone(bombs)
        else:
            # 执行随机但安全的移动
            if random.random() < 0.1:
                self.random_safe_movement(bombs)

    def move_to_safe_zone(self, bombs):
        """移动到安全区域"""
        # 简单实现：远离最近的炸弹
        nearest_bomb = None
        min_distance = float('inf')
        
        for bomb in bombs:
            distance = self.distance_to((bomb.x, bomb.y))
            if distance < min_distance:
                min_distance = distance
                nearest_bomb = bomb
        
        if nearest_bomb:
            self.move_away_from((nearest_bomb.x, nearest_bomb.y))
            self.ai_debug_info.append("寻找安全区域...")

    def random_safe_movement(self, bombs):
        """随机安全移动"""
        # 生成随机方向，但避免危险方向
        safe_angle = random.uniform(0, 2 * math.pi)
        safe_dx = math.cos(safe_angle)
        safe_dy = math.sin(safe_angle)
        
        # 轻微调整以避免炸弹
        for bomb in bombs:
            bomb_dx = self.x - bomb.x
            bomb_dy = self.y - bomb.y
            bomb_distance = math.sqrt(bomb_dx*bomb_dx + bomb_dy*bomb_dy)
            
            if bomb_distance < AI_SAFE_DISTANCE:
                # 调整方向远离炸弹
                if bomb_distance > 0:
                    bomb_dx /= bomb_distance
                    bomb_dy /= bomb_dy
                    safe_dx = safe_dx * 0.7 + bomb_dx * 0.3
                    safe_dy = safe_dy * 0.7 + bomb_dy * 0.3
        
        # 归一化方向
        length = math.sqrt(safe_dx*safe_dx + safe_dy*safe_dy)
        if length > 0:
            safe_dx /= length
            safe_dy /= length
        
        self.direction = [safe_dx, safe_dy]
        self.x += safe_dx * self.speed * 0.3
        self.y += safe_dy * self.speed * 0.3

    def move_to_safe_zone_enhanced(self, bombs):
        """增强版移动到安全区域 - 考虑边界"""
        # 寻找安全位置（远离炸弹和边界）
        safe_positions = []
        
        # 测试几个候选位置
        candidate_positions = [
            (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.2),  # 左上区域
            (SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.2),  # 右上区域
            (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.8),  # 左下区域
            (SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.8),  # 右下区域
            (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5),  # 中心区域
        ]
        
        # 评估每个位置的安全性
        for pos_x, pos_y in candidate_positions:
            safety_score = 1.0
            
            # 评估炸弹风险
            for bomb in bombs:
                risk = self.calculate_position_risk((pos_x, pos_y), bomb, 0)
                safety_score *= (1.0 - risk)
            
            # 评估边界安全性（距离边界越远越好）
            boundary_dist = min(
                pos_x, SCREEN_WIDTH - pos_x,
                pos_y, SCREEN_HEIGHT - pos_y
            )
            boundary_safety = min(1.0, boundary_dist / AI_SAFE_DISTANCE)
            safety_score *= boundary_safety
            
            safe_positions.append(((pos_x, pos_y), safety_score))
        
        # 选择最安全的位置
        safe_positions.sort(key=lambda x: x[1], reverse=True)
        if safe_positions:
            best_pos, best_score = safe_positions[0]
            self.move_toward_target(best_pos)
            self.ai_debug_info.append(f"前往安全区域: {best_score:.2f}")

    def move_toward_target(self, target_pos):
        """朝目标位置移动"""
        target_x, target_y = target_pos
        dx = target_x - self.x
        dy = target_y - self.y
        
        # 归一化方向向量
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        # 设置移动方向
        self.direction = [dx, dy]
        self.x += dx * self.speed
        self.y += dy * self.speed

    def move_away_from(self, position):
        """远离指定位置"""
        pos_x, pos_y = position
        dx = self.x - pos_x
        dy = self.y - pos_y
        
        # 归一化方向向量
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        # 设置移动方向
        self.direction = [dx, dy]
        self.x += dx * self.speed
        self.y += dy * self.speed

    def distance_to(self, position):
        """计算到指定位置的距离"""
        pos_x, pos_y = position
        return math.sqrt((self.x - pos_x)**2 + (self.y - pos_y)**2)

    def calculate_direction_safety(self, dx, dy, bombs, craters, current_time):
        """计算移动方向的安全性"""
        safety_score = 1.0
        
        # 预测移动路径
        predict_steps = 10
        step_distance = self.speed * 0.1  # 每步移动距离
        move_time_per_step = 0.1  # 每步移动时间
        
        for step in range(1, predict_steps + 1):
            # 预测位置
            predict_x = self.x + dx * step * step_distance
            predict_y = self.y + dy * step * step_distance
            predict_time = step * move_time_per_step
            
            # 检查炸弹风险
            for bomb in bombs:
                if not bomb.active:
                    continue
                    
                risk = self.calculate_position_risk((predict_x, predict_y), bomb, predict_time)
                safety_score *= (1.0 - risk * 0.5)  # 每个炸弹最多降低50%安全性
            
            # 检查弹坑风险
            crater_risk = self.calculate_crater_risk((predict_x, predict_y), craters)
            safety_score *= (1.0 - crater_risk * 0.3)  # 每个弹坑最多降低30%安全性
            
            # 检查边界风险
            boundary_risk = self.calculate_boundary_risk(predict_x, predict_y)
            safety_score *= (1.0 - boundary_risk * 0.2)  # 边界风险最多降低20%安全性
        
        return safety_score

    def calculate_crater_risk(self, position, craters):
        """计算位置上的弹坑风险"""
        pos_x, pos_y = position
        risk = 0
        
        for crater in craters:
            if not crater.active:
                continue
                
            if crater.explosion_shape == "circle":
                # 圆形弹坑
                distance = math.sqrt((pos_x - crater.x)**2 + (pos_y - crater.y)**2)
                if distance <= crater.radius:
                    risk = max(risk, 0.7)  # 在弹坑内风险较高
            else:
                # 矩形弹坑
                rect_x = crater.x - crater.radius
                rect_y = crater.y - crater.radius
                rect_width = crater.radius * 2
                rect_height = crater.radius * 2
                
                if (rect_x <= pos_x <= rect_x + rect_width and
                    rect_y <= pos_y <= rect_y + rect_height):
                    risk = max(risk, 0.7)  # 在弹坑内风险较高
        
        return risk

    def calculate_boundary_risk(self, x, y):
        """计算边界风险"""
        # 计算到边界的距离
        left_dist = x
        right_dist = SCREEN_WIDTH - x
        top_dist = y
        bottom_dist = SCREEN_HEIGHT - y
        
        # 找到最近边界
        min_dist = min(left_dist, right_dist, top_dist, bottom_dist)
        
        # 距离边界越近风险越高
        if min_dist < 50:  # 距离边界50像素内
            return 1.0 - (min_dist / 50)
        return 0.0

    def calculate_boundary_safety(self, dx, dy):
        """计算边界安全性"""
        # 预测移动后的位置
        predict_x = self.x + dx * AI_SAFE_DISTANCE
        predict_y = self.y + dy * AI_SAFE_DISTANCE
        
        # 检查是否会接近边界
        boundary_dist = min(
            predict_x, SCREEN_WIDTH - predict_x,
            predict_y, SCREEN_HEIGHT - predict_y
        )
        
        # 距离边界越远越安全
        return min(1.0, boundary_dist / AI_SAFE_DISTANCE)

    def process_locked_target(self):
        """处理锁定的目标"""
        if not self.locked_target:
            return
        
        # 如果是炸弹，执行逃离
        if hasattr(self.locked_target, 'type') and self.locked_target.type == "bomb":
            self.enhanced_boundary_aware_escape(self.locked_target, [self.locked_target])
        else:
            # 朝锁定目标移动
            self.boundary_aware_move_to_target((self.locked_target.x, self.locked_target.y), [])

    def enhanced_boundary_aware_escape(self, bomb, all_bombs):
        """增强版边界感知逃离策略"""
        # 计算到边界的距离
        self.calculate_boundary_distances()
        
        # 根据炸弹形状选择不同的逃离策略
        if hasattr(bomb, 'explosion_shape'):
            if bomb.explosion_shape == "circle":
                escape_direction = self.calculate_circular_bomb_escape(bomb)
            else:
                escape_direction = self.calculate_rectangular_bomb_escape(bomb)
        else:
            # 默认使用基础逃离
            escape_direction = self.basic_bomb_escape(bomb)
        
        # 考虑其他炸弹的影响
        escape_direction = self.adjust_escape_for_multiple_bombs(escape_direction, all_bombs)
        
        # 应用移动
        if escape_direction:
            dx, dy = escape_direction
            escape_speed = self.speed * (1.5 if not self.shield_active else 1.2)
            self.x += dx * escape_speed
            self.y += dy * escape_speed
            self.direction = [dx, dy]
            
            self.ai_debug_info.append("边界感知逃离!")
        else:
            # 备用方案：简单远离炸弹
            self.move_away_from((bomb.x, bomb.y))
            self.ai_debug_info.append("备用逃离方案!")

    def calculate_boundary_distances(self):
        """计算到各方向边界的距离"""
        self.boundary_distances = {
            'left': self.x,
            'right': SCREEN_WIDTH - self.x,
            'up': self.y,
            'down': SCREEN_HEIGHT - self.y
        }

    def boundary_aware_move_to_target(self, target, bombs):
        """边界感知的目标移动"""
        # 提取目标位置
        if hasattr(target, 'x') and hasattr(target, 'y'):
            target_x, target_y = target.x, target.y
        elif isinstance(target, (tuple, list)) and len(target) == 2:
            target_x, target_y = target
        else:
            self.safe_idle_movement(bombs)
            return
        
        # 计算基础移动方向
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return
        
        dx /= distance
        dy /= distance
        
        # 边界调整
        boundary_adjustment = self.calculate_boundary_adjustment(dx, dy)
        
        # 结合基础方向和边界调整方向
        if boundary_adjustment:
            adj_dx, adj_dy = boundary_adjustment
            # 混合基础方向和边界调整方向
            blend_factor = 0.7  # 基础方向权重
            final_dx = dx * blend_factor + adj_dx * (1 - blend_factor)
            final_dy = dy * blend_factor + adj_dy * (1 - blend_factor)
            
            # 归一化
            length = math.sqrt(final_dx*final_dx + final_dy*final_dy)
            if length > 0:
                final_dx /= length
                final_dy /= length
            
            dx, dy = final_dx, final_dy
        
        # 检查前方是否有立即危险
        immediate_danger = False
        look_ahead_distance = 50
        
        for bomb in bombs:
            if not bomb.active:
                continue
                
            ahead_x = self.x + dx * look_ahead_distance
            ahead_y = self.y + dy * look_ahead_distance
            
            if self.calculate_position_risk((ahead_x, ahead_y), bomb, look_ahead_distance/self.speed) > 0.3:
                immediate_danger = True
                break
        
        if immediate_danger and not self.shield_active:
            self.evade_danger(bombs)
        else:
            self.direction = [dx, dy]
            self.x += dx * self.speed
            self.y += dy * self.speed

    def calculate_boundary_adjustment(self, dx, dy):
        """计算边界调整方向"""
        # 检查当前移动方向是否会导致很快碰到边界
        time_to_boundary = float('inf')
        
        if dx > 0:  # 向右移动
            time_to_boundary = (SCREEN_WIDTH - self.x - self.radius) / (dx * self.speed)
        elif dx < 0:  # 向左移动
            time_to_boundary = (self.x - self.radius) / (-dx * self.speed)
        
        if dy > 0:  # 向下移动
            time_y = (SCREEN_HEIGHT - self.y - self.radius) / (dy * self.speed)
            time_to_boundary = min(time_to_boundary, time_y)
        elif dy < 0:  # 向上移动
            time_y = (self.y - self.radius) / (-dy * self.speed)
            time_to_boundary = min(time_to_boundary, time_y)
        
        # 如果很快会碰到边界，调整方向
        if time_to_boundary < 2.0:  # 2秒内会碰到边界
            # 计算避免边界的调整方向
            adjustment_dx, adjustment_dy = 0, 0
            
            if self.x < SCREEN_WIDTH / 2:
                adjustment_dx += 0.5  # 偏向右边
            else:
                adjustment_dx -= 0.5  # 偏向左边
                
            if self.y < SCREEN_HEIGHT / 2:
                adjustment_dy += 0.5  # 偏向下边
            else:
                adjustment_dy -= 0.5  # 偏向上边
            
            # 归一化调整方向
            length = math.sqrt(adjustment_dx*adjustment_dx + adjustment_dy*adjustment_dy)
            if length > 0:
                adjustment_dx /= length
                adjustment_dy /= length
            
            return (adjustment_dx, adjustment_dy)
        
        return None

    def simple_boundary_adjustment(self, dx, dy):
        """简化的边界调整（移除复杂的边界回避逻辑）"""
        # 检查当前移动方向是否会导致很快碰到边界
        time_to_boundary = float('inf')
        
        if dx > 0:  # 向右移动
            time_to_boundary = (SCREEN_WIDTH - self.x - self.radius) / (dx * self.speed)
        elif dx < 0:  # 向左移动
            time_to_boundary = (self.x - self.radius) / (-dx * self.speed)
        
        if dy > 0:  # 向下移动
            time_y = (SCREEN_HEIGHT - self.y - self.radius) / (dy * self.speed)
            time_to_boundary = min(time_to_boundary, time_y)
        elif dy < 0:  # 向上移动
            time_y = (self.y - self.radius) / (-dy * self.speed)
            time_to_boundary = min(time_to_boundary, time_y)
        
        # 如果很快会碰到边界，轻微调整方向
        if time_to_boundary < 2.0:  # 2秒内会碰到边界
            # 简单的边界回避：稍微远离最近边界的方向
            adjustment_dx, adjustment_dy = 0, 0
            
            if self.x < SCREEN_WIDTH / 2:
                adjustment_dx += 0.3  # 轻微偏向右边
            else:
                adjustment_dx -= 0.3  # 轻微偏向左边
                
            if self.y < SCREEN_HEIGHT / 2:
                adjustment_dy += 0.3  # 轻微偏向下边
            else:
                adjustment_dy -= 0.3  # 轻微偏向上边
            
            # 归一化调整方向
            length = math.sqrt(adjustment_dx*adjustment_dx + adjustment_dy*adjustment_dy)
            if length > 0:
                adjustment_dx /= length
                adjustment_dy /= length
            
            return (adjustment_dx, adjustment_dy)
        
        return None

    def update_hit_effect(self):
        """更新受伤效果"""
        if not self.hit_effect_active:
            return
            
        current_time = time.time()
        
        # 更新闪烁效果
        if current_time - self.last_flash_toggle > 0.1:  # 每0.1秒切换一次
            self.hit_flash_visible = not self.hit_flash_visible
            self.last_flash_toggle = current_time
        
        # 检查受伤效果是否应该结束
        if current_time - self.hit_effect_start_time >= HIT_EFFECT_DURATION:
            self.hit_effect_active = False
        
        # 更新受伤粒子
        i = 0
        while i < len(self.hit_particles):
            particle = self.hit_particles[i]
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['lifetime'] -= 0.016  # 假设60FPS
            
            # 移除生命周期结束的粒子
            if particle['lifetime'] <= 0:
                self.hit_particles.pop(i)
            else:
                i += 1

    def activate_hit_effect(self):
        """激活受伤效果"""
        self.hit_effect_active = True
        self.hit_effect_start_time = time.time()
        self.hit_flash_visible = True
        self.last_flash_toggle = time.time()
        
        # 创建受伤粒子效果
        self.create_hit_particles()

    def create_hit_particles(self):
        """创建受伤粒子"""
        for _ in range(min(20, self.max_hit_particles - len(self.hit_particles))):  # 限制粒子数量
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            lifetime = random.uniform(0.5, 1.0)
            size = random.uniform(3, 6)
            color = random.choice([(255, 100, 100), (255, 150, 150), (255, 200, 200)])
            
            self.hit_particles.append({
                'x': self.x,
                'y': self.y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'size': size,
                'color': color
            })

    def update_shield(self):
        """更新护盾状态"""
        # 检查护盾是否应该消失
        if self.shield_active and time.time() - self.shield_start_time >= SHIELD_DURATION:
            self.shield_active = False  # 护盾失效

    def activate_shield(self):
        """激活护盾"""
        self.shield_active = True
        self.shield_start_time = time.time()

    def update_speed(self, craters):
        """更新玩家速度（考虑弹坑影响）"""
        # 检查是否在弹坑内
        self.in_crater = False
        for crater in craters:
            if not crater.active:
                continue
                
            if crater.explosion_shape == "circle":
                # 圆形弹坑检测
                distance_sq = (self.x - crater.x)**2 + (self.y - crater.y)**2
                if distance_sq <= crater.radius**2:  # 使用平方避免开方
                    self.in_crater = True
                    break
            else:
                # 矩形弹坑检测
                rect_x = crater.x - crater.radius
                rect_y = crater.y - crater.radius
                rect_width = crater.radius * 2
                rect_height = crater.radius * 2
                if (rect_x <= self.x <= rect_x + rect_width and
                    rect_y <= self.y <= rect_y + rect_height):
                    self.in_crater = True
                    break
        
        # 根据是否在弹坑内调整速度
        self.speed = self.base_speed * (CRATER_SLOW_FACTOR if self.in_crater else 1.0)

    def update_trail(self):
        """更新尾焰粒子"""
        i = 0
        while i < len(self.trail_particles):
            particle = self.trail_particles[i]
            particle['life'] -= 0.05  # 粒子生命周期减少
            if particle['life'] <= 0:
                self.trail_particles.pop(i)
            else:
                i += 1
                
    def calculate_angle_between_directions(self, dir1, dir2):
        """计算两个方向之间的夹角（度）"""
        if not dir1 or not dir2:
            return 180  # 默认最大冲突
        
        dx1, dy1 = dir1
        dx2, dy2 = dir2
        
        # 计算点积
        dot_product = dx1 * dx2 + dy1 * dy2
        
        # 确保点积在有效范围内
        dot_product = max(-1.0, min(1.0, dot_product))
        
        # 计算夹角（弧度）
        angle_rad = math.acos(dot_product)
        
        # 转换为度
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg

    def calculate_direction_to_target(self, target):
        """计算到目标的方向向量"""
        if not target or not hasattr(target, 'x') or not hasattr(target, 'y'):
            return (0, 0)
        
        dx = target.x - self.x
        dy = target.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return (0, 0)
        
        return (dx/distance, dy/distance)

    def find_most_dangerous_bomb(self, bombs):
        """找到最危险的炸弹"""
        most_dangerous = None
        highest_danger = 0
        
        for bomb in bombs:
            if not bomb.active:
                continue
                
            danger_level = self.calculate_bomb_danger_level(bomb)
            
            if danger_level > highest_danger:
                highest_danger = danger_level
                most_dangerous = bomb
        
        return most_dangerous

    def calculate_bomb_danger_level(self, bomb):
        """计算炸弹的危险等级"""
        current_time = time.time()
        danger = 0
        
        if bomb.exploding:
            # 正在爆炸的炸弹
            time_elapsed = current_time - bomb.explosion_start_time
            current_radius = bomb.expansion_speed * min(time_elapsed, EXPLOSION_DURATION)
            
            distance = self.distance_to((bomb.x, bomb.y))
            
            if distance <= current_radius:
                # 已经在爆炸范围内
                danger = 1.0
            else:
                # 计算到达爆炸边缘的时间
                time_to_reach = (distance - current_radius) / self.speed
                explosion_growth = bomb.expansion_speed * time_to_reach
                
                if distance <= current_radius + explosion_growth:
                    # 会与爆炸相遇
                    danger = 0.8
                elif distance <= current_radius + 100:  # 安全边际
                    danger = 0.6
        else:
            # 未爆炸的炸弹
            time_to_explosion = (bomb.plant_time + BOMB_TIMER - bomb.warning_time) - current_time
            
            if time_to_explosion <= 2.0:  # 2秒内爆炸
                distance = self.distance_to((bomb.x, bomb.y))
                predicted_radius = bomb.expansion_speed * min(EXPLOSION_DURATION, 
                    time_to_explosion if time_to_explosion > 0 else 0)
                
                if distance <= predicted_radius:
                    # 在预测爆炸范围内
                    danger = 0.7 - (time_to_explosion / 2.0) * 0.2
                elif distance <= predicted_radius + 50:  # 接近爆炸范围
                    danger = 0.4
        
        return danger

    def smart_escape_from_bomb(self, bomb, bombs):
        """智能炸弹逃离 - 集成新的规避策略"""
        if hasattr(bomb, 'explosion_shape'):
            if bomb.explosion_shape == "circle":
                # 使用增强的圆形炸弹规避策略
                escape_direction = self.enhanced_circular_bomb_escape(bomb)
                self.ai_debug_info.append("圆形炸弹:泥石流算法")
            else:
                # 矩形炸弹使用原有策略
                escape_direction = self.enhanced_rectangular_bomb_escape(bomb)
                self.ai_debug_info.append("矩形炸弹:边界感知")
        else:
            # 默认使用基础规避
            escape_direction = self.basic_bomb_escape(bomb)
            self.ai_debug_info.append("未知炸弹:基础规避")
        
        # 应用规避移动
        if escape_direction:
            dx, dy = escape_direction
            
            # 根据危险程度调整速度
            if bomb.exploding:
                escape_speed = self.speed * (1.8 if not self.shield_active else 1.3)
                self.ai_debug_info.append("紧急规避!")
            else:
                escape_speed = self.speed * (1.5 if not self.shield_active else 1.2)
            
            self.x += dx * escape_speed
            self.y += dy * escape_speed
            self.direction = [dx, dy]
            
            # 添加详细的策略信息
            self.add_escape_strategy_debug(bomb, escape_direction)
        else:
            # 备用方案
            self.move_away_from((bomb.x, bomb.y))
            self.ai_debug_info.append("执行备用规避方案")

    def find_non_conflicting_target(self, stars, hearts, shields, bombs, craters, evasion_direction):
        """寻找与规避方向不冲突的目标"""
        # 收集所有可见对象
        visible_objects = self.get_visible_objects(stars, hearts, shields, bombs, craters)
        
        if not visible_objects or not evasion_direction:
            return None
            
        # 计算每个对象的权重
        weighted_objects = []
        for obj in visible_objects:
            weight = self.calculate_enhanced_object_weight(obj, bombs, craters)
            weighted_objects.append((obj, weight))
        
        # 按权重排序（从高到低）
        weighted_objects.sort(key=lambda x: x[1], reverse=True)
        
        best_alternative = None
        best_score = -float('inf')
        
        for i in range(min(AI_MAX_TARGET_SWITCH_ATTEMPTS, len(weighted_objects))):
            obj, weight = weighted_objects[i]
            
            # 计算目标方向与规避方向的冲突角度
            target_direction = self.calculate_direction_to_target(obj)
            conflict_angle = self.calculate_angle_between_directions(evasion_direction, target_direction)
            
            # 冲突惩罚（角度越大惩罚越大）
            conflict_penalty = max(0, conflict_angle - AI_ESCAPE_TARGET_CONFLICT_THRESHOLD) * 2
            adjusted_score = weight - conflict_penalty
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_alternative = obj
        
        return best_alternative

    def get_object_type(self, obj):
        """获取对象类型"""
        if hasattr(obj, 'type'):
            if obj.type == "heart":
                return "爱心"
            elif obj.type == "shield":
                return "护盾"
            elif obj.type == "star":
                if hasattr(obj, 'size'):
                    return f"{obj.size}型星星"
            elif obj.type == "bomb":
                return "炸弹"
        return "未知"

    def is_target_reachable(self, target, bombs):
        """检查目标是否可达（考虑爆炸风险）"""
        if not self.is_target_valid(target):
            return False
        
        # 计算路径安全性
        path_safety = self.calculate_path_safety((self.x, self.y), (target.x, target.y), bombs)
        
        # 如果有护盾，降低安全阈值
        safety_threshold = 0.3 if self.shield_active else 0.6
        
        return path_safety > safety_threshold and self.distance_to((target.x, target.y)) < AI_VISION_RADIUS * 1.5

    def calculate_path_safety(self, start_pos, end_pos, bombs):
        """计算路径安全性系数（0.0-1.0）"""
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        # 计算路径方向和长度
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return 1.0
        
        # 归一化方向
        dx /= distance
        dy /= distance
        
        # 预测路径安全性
        safety_score = 1.0
        step_size = distance / AI_EXPLOSION_PREDICTION_STEPS
        move_time_per_step = step_size / self.speed
        
        for step in range(AI_EXPLOSION_PREDICTION_STEPS):
            # 预测当前位置
            predict_x = start_x + dx * step * step_size
            predict_y = start_y + dy * step * step_size
            predict_time = step * move_time_per_step
            
            # 检查每个炸弹对该位置的风险
            for bomb in bombs:
                if not bomb.active:
                    continue
                    
                bomb_risk = self.calculate_position_risk((predict_x, predict_y), bomb, predict_time)
                safety_score *= (1.0 - bomb_risk * 0.3)  # 每个炸弹最多降低30%安全性
        
        return max(0.0, min(1.0, safety_score))

    def calculate_position_risk(self, position, bomb, predict_time):
        """计算特定位置在特定时间点的炸弹风险"""
        pos_x, pos_y = position
        bomb_distance = math.sqrt((pos_x - bomb.x)**2 + (pos_y - bomb.y)**2)
        
        current_time = time.time()
        risk = 0
        
        if bomb.exploding:
            # 正在爆炸的炸弹
            explosion_elapsed = current_time - bomb.explosion_start_time + predict_time
            if explosion_elapsed < 0:
                return 0
                
            current_radius = bomb.expansion_speed * min(explosion_elapsed, EXPLOSION_DURATION)
            
            if bomb_distance <= current_radius:
                risk = 1.0 - (bomb_distance / current_radius)
        else:
            # 未爆炸的炸弹
            time_to_explosion = (bomb.plant_time + BOMB_TIMER - bomb.warning_time) - current_time
            if time_to_explosion > 0:
                # 预测到达时间点的爆炸状态
                arrival_explosion_time = time_to_explosion - predict_time
                
                if arrival_explosion_time <= 0:
                    # 到达时炸弹已经爆炸
                    explosion_elapsed = -arrival_explosion_time
                    current_radius = bomb.expansion_speed * min(explosion_elapsed, EXPLOSION_DURATION)
                    
                    if bomb_distance <= current_radius:
                        risk = 1.0 - (bomb_distance / current_radius)
                else:
                    # 到达时炸弹尚未爆炸，但可能很快爆炸
                    if arrival_explosion_time < 1.0:  # 1秒内会爆炸
                        # 计算爆炸风险（时间越近风险越高）
                        risk = (1.0 - arrival_explosion_time) * 0.5
        
        return risk
   
    def draw_ai_debug(self):
        """绘制AI调试信息"""
        if not self.ai_enabled or not self.ai_debug_info:
            return
        
        # 绘制目标连线
        if self.ai_target_pos:
            pygame.draw.line(screen, (0, 255, 0), (int(self.x), int(self.y)), 
                            (int(self.ai_target_pos[0]), int(self.ai_target_pos[1])), 2)
            
            # 绘制目标标记
            pygame.draw.circle(screen, (0, 255, 0), 
                            (int(self.ai_target_pos[0]), int(self.ai_target_pos[1])), 10, 2)
        
        # 绘制调试文本
        debug_y = 50 + (self.player_id - 1) * 100
        for info in self.ai_debug_info:
            debug_text = small_font.render(f"玩家{self.player_id}: {info}", True, (200, 255, 200))
            screen.blit(debug_text, (10, debug_y))
            debug_y += 20

# 双人模式管理器
class TwoPlayerManager:
    def __init__(self):
        self.active = False  # 双人模式是否激活
        self.players = []    # 玩家列表
        self.scores = [0, 0]     # 玩家分数列表
        self.lives = [3, 3]      # 玩家生命值列表
        self.high_scores = [0, 0]  # 玩家最高分
        self.load_highscores()  # 加载历史最高分
        
    def update_high_scores(self):
        """更新双人模式的最高分记录"""
        for i, score in enumerate(self.scores):
            if score > self.high_scores[i]:
                self.high_scores[i] = score
                # 保存到文件
                self.save_highscores()

    def save_highscores(self):
        """保存双人模式的最高分到文件"""
        try:
            with open("highscores_2player.txt", 'w') as f:
                for i, high_score in enumerate(self.high_scores):
                    f.write(f"Player{i+1}:{high_score}\n")
        except:
            pass

    def load_highscores(self):
        """加载双人模式的最高分记录"""
        try:
            if os.path.exists("highscores_2player.txt"):
                with open("highscores_2player.txt", 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if i < len(self.high_scores):
                            parts = line.strip().split(':')
                            if len(parts) == 2 and parts[0].startswith("Player"):
                                self.high_scores[i] = int(parts[1])
        except:
            pass    
        
    def get_alive_players_count(self):
        """获取存活玩家数量"""
        if not self.active:
            return 0
        return sum(1 for player_obj in self.players if player_obj.active and player_obj.lives > 0)

    def get_highest_alive_player_score(self):
        """获取存活玩家的最高分数"""
        if not self.active:
            return 0
        
        max_score = 0
        for i, player_obj in enumerate(self.players):
            if player_obj.active and player_obj.lives > 0:
                max_score = max(max_score, self.scores[i])
        
        return max_score

    def get_highest_alive_player_lives(self):
        """获取存活玩家的最高生命值"""
        if not self.active:
            return 0
        
        max_lives = 0
        for player_obj in self.players:
            if player_obj.active and player_obj.lives > 0:
                max_lives = max(max_lives, player_obj.lives)
        
        return max_lives
        
    def activate(self, mode="human"):
        """激活双人模式
        mode: "human" - 玩家1+玩家2, "ai" - 玩家1+AI玩家2
        """
        self.active = True
        # 创建两个玩家
        self.players = [
            Player(player_id=1, start_pos=PLAYER1_START_POS, two_player_mode=True),
            Player(player_id=2, start_pos=PLAYER2_START_POS, two_player_mode=True)
        ]
        
        # 设置玩家控制方式
        if mode == "human":
            # 玩家1使用鼠标，玩家2使用键盘
            self.players[0].use_mouse_control = True
            self.players[1].use_mouse_control = False
            self.players[1].ai_enabled = False
        else:  # AI模式
            # 玩家1使用鼠标，玩家2使用AI
            self.players[0].use_mouse_control = True
            self.players[1].ai_enabled = True
        
        # 初始化分数和生命值
        self.scores = [0, 0]
        self.lives = [3, 3]
        
    def deactivate(self):
        """停用双人模式"""
        self.active = False
        self.players = []
        self.scores = [0, 0]
        self.lives = [3, 3]
        
    def switch_player_control(self, player_id, control_type):
        """切换玩家控制方式
        player_id: 1或2
        control_type: "human" 或 "ai"
        """
        if player_id < 1 or player_id > len(self.players):
            return
            
        player = self.players[player_id-1]
        if control_type == "human":
            player.ai_enabled = False
        elif control_type == "ai":
            player.ai_enabled = True
    
    def get_active_players_count(self):
        """获取活跃玩家数量"""
        if not self.active:
            return 0
        return sum(1 for life in self.lives if life > 0)
    
    def is_game_over(self):
        """检查游戏是否结束（所有玩家生命值为0）"""
        if not self.active:
            return False
        return all(life <= 0 for life in self.lives)
    
    def update_high_scores(self):
        """更新最高分记录"""
        for i, score in enumerate(self.scores):
            if score > self.high_scores[i]:
                self.high_scores[i] = score
                
    def get_player_status(self, player_id):
        """获取玩家状态"""
        if player_id < 1 or player_id > len(self.players):
            return None
        return {
            'score': self.scores[player_id-1],
            'lives': self.lives[player_id-1],
            'high_score': self.high_scores[player_id-1],
            'active': self.players[player_id-1].active if player_id-1 < len(self.players) else False
        }
    
    def update_player_lives(self, player_id, lives):
        """更新玩家生命值"""
        if player_id < 1 or player_id > len(self.lives):
            return
        self.lives[player_id-1] = lives
        
    def update_player_score(self, player_id, score):
        """更新玩家分数"""
        if player_id < 1 or player_id > len(self.scores):
            return
        self.scores[player_id-1] = score

# 主游戏逻辑
def main():
    # 初始化游戏状态
    game_over_sound_played = False
    show_exit_dialog = False
    music_paused_before_dialog = False
    high_score = load_highscore()
    new_high_score = False
    
    # 创建音效管理器
    sound_manager = SoundManager()
    sound_manager.play_bgm()  # 播放背景音乐
    
    # 创建双人模式管理器
    two_player_manager = TwoPlayerManager()
    
    # 初始化游戏对象
    player = Player(player_id=1, start_pos=PLAYER1_START_POS)
    
    # 单人模式物品数量
    single_player_items = {
        'stars': 5,
        'hearts': 1,
        'shields': 1
    }
    
    # 双人模式物品数量（双倍）
    two_player_items = {
        'stars': 10,
        'hearts': 2,
        'shields': 2
    }
    
    # 根据当前模式初始化物品
    current_items = two_player_items if two_player_manager.active else single_player_items
    stars = [Item("star", two_player_manager.active) for _ in range(current_items['stars'])]
    hearts = [Item("heart", two_player_manager.active) for _ in range(current_items['hearts'])]
    shields = [Item("shield", two_player_manager.active) for _ in range(current_items['shields'])]
    
    bombs = []  # 炸弹列表
    craters = []  # 弹坑列表
    score_popups = []  # 得分飘字效果列表
    
    score = 0  # 游戏分数
    lives = 3  # 玩家生命值
    last_bomb_spawn = time.time()  # 上次生成炸弹的时间
    last_heart_spawn_check = time.time()  # 上次检查爱心生成的时间
    last_shield_spawn_check = time.time()  # 上次检查护盾生成的时间
    game_over = False  # 游戏是否结束
    paused = False  # 游戏是否暂停
    
    # 初始化所有物品的位置，确保它们相离
    all_items = stars + hearts + shields
    for item in all_items:
        item.respawn(all_items)
    
    # 隐藏鼠标光标
    pygame.mouse.set_visible(False)
    
    # 游戏主循环
    while True:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 如果是游戏结束状态，直接退出
                if game_over:
                    pygame.quit()
                    sys.exit()
                else:
                    # 显示退出确认对话框
                    show_exit_dialog = True
                    paused = True
                    # 记录对话框显示前的音乐状态
                    music_paused_before_dialog = pygame.mixer.music.get_busy()
                    # 暂停背景音乐
                    pygame.mixer.music.pause()
                    # 显示鼠标光标
                    pygame.mouse.set_visible(True)
                    
            if event.type == pygame.KEYDOWN:
                # 回车键切换AI模式
                if event.key == pygame.K_RETURN and not game_over and not show_exit_dialog:
                    if two_player_manager.active:
                        # 双人模式下，切换玩家2的AI控制
                        for player_obj in two_player_manager.players:
                            if player_obj.player_id == 2:
                                player_obj.toggle_ai()
                                break
                    else:
                        # 单人模式下切换玩家AI
                        player.toggle_ai()
                    
                # 1键激活双人模式（玩家1+AI玩家2）
                elif event.key == pygame.K_1 and not game_over and not show_exit_dialog and not two_player_manager.active:
                    two_player_manager.activate(mode="ai")
                    # 重新初始化物品数量为双倍
                    current_items = two_player_items
                    stars = [Item("star", True) for _ in range(current_items['stars'])]
                    hearts = [Item("heart", True) for _ in range(current_items['hearts'])]
                    shields = [Item("shield", True) for _ in range(current_items['shields'])]
                    # 重新生成物品位置
                    all_items = stars + hearts + shields
                    for item in all_items:
                        item.respawn(all_items)
                    print("双人模式已激活：玩家1 + AI玩家2")
                
                # 2键激活双人模式（玩家1+玩家2）
                elif event.key == pygame.K_2 and not game_over and not show_exit_dialog and not two_player_manager.active:
                    two_player_manager.activate(mode="human")
                    # 重新初始化物品数量为双倍
                    current_items = two_player_items
                    stars = [Item("star", True) for _ in range(current_items['stars'])]
                    hearts = [Item("heart", True) for _ in range(current_items['hearts'])]
                    shields = [Item("shield", True) for _ in range(current_items['shields'])]
                    # 重新生成物品位置
                    all_items = stars + hearts + shields
                    for item in all_items:
                        item.respawn(all_items)
                    print("双人模式已激活：玩家1 + 玩家2")
                
                # 0键退出双人模式
                elif event.key == pygame.K_0 and two_player_manager.active and not game_over and not show_exit_dialog:
                    two_player_manager.deactivate()
                    # 重新初始化物品数量为单人模式
                    current_items = single_player_items
                    stars = [Item("star", False) for _ in range(current_items['stars'])]
                    hearts = [Item("heart", False) for _ in range(current_items['hearts'])]
                    shields = [Item("shield", False) for _ in range(current_items['shields'])]
                    # 重新生成物品位置
                    all_items = stars + hearts + shields
                    for item in all_items:
                        item.respawn(all_items)
                    print("双人模式已关闭")
                        
                # 空格键暂停/继续
                elif event.key == pygame.K_SPACE and not game_over and not show_exit_dialog:
                    paused = not paused
                    if paused:
                        # 暂停背景音乐
                        pygame.mixer.music.pause()
                        pygame.mouse.set_visible(True)
                    else:
                        # 继续播放背景音乐
                        pygame.mixer.music.unpause()
                        pygame.mouse.set_visible(False)
                        
                # Ctrl键切换控制模式
                elif (event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL) and not game_over and not show_exit_dialog:
                    if two_player_manager.active:
                        # 双人模式下切换玩家1的控制方式
                        for player_obj in two_player_manager.players:
                            if player_obj.player_id == 1:
                                player_obj.switch_control_mode()
                                break
                    else:
                        # 单人模式下切换控制方式
                        player.switch_control_mode()
                
                # Alt键重新开始游戏
                elif (event.key == pygame.K_LALT or event.key == pygame.K_RALT) and (game_over or paused) and not show_exit_dialog:
                    # 重新开始游戏
                    pygame.mouse.set_visible(False)
                    
                    # 保存当前的双人模式状态
                    was_two_player = two_player_manager.active
                    player2_was_ai = False
                    if was_two_player and len(two_player_manager.players) > 1:
                        player2_was_ai = two_player_manager.players[1].ai_enabled
                    
                    # 重置游戏状态
                    player = Player(player_id=1, start_pos=PLAYER1_START_POS)
                    
                    # 重置双人模式管理器
                    two_player_manager.deactivate()
                    two_player_manager = TwoPlayerManager()  # 重新创建
                    
                    # 如果之前是双人模式，重新激活
                    if was_two_player:
                        two_player_manager.activate(mode="ai" if player2_was_ai else "human")
                    
                    # 重新初始化物品
                    current_items = two_player_items if two_player_manager.active else single_player_items
                    stars = [Item("star", two_player_manager.active) for _ in range(current_items['stars'])]
                    hearts = [Item("heart", two_player_manager.active) for _ in range(current_items['hearts'])]
                    shields = [Item("shield", two_player_manager.active) for _ in range(current_items['shields'])]
                    
                    # 重置其他游戏状态
                    bombs = []
                    craters = []
                    score_popups = []
                    score = 0
                    lives = 3
                    last_bomb_spawn = time.time()
                    last_heart_spawn_check = time.time()
                    last_shield_spawn_check = time.time()
                    game_over = False
                    game_over_sound_played = False
                    new_high_score = False
                    paused = False
                    show_exit_dialog = False
                    
                    # 重新生成所有物品的位置
                    all_items = stars + hearts + shields
                    for item in all_items:
                        item.respawn(all_items)
                    
                    # 重新播放背景音乐
                    sound_manager.play_bgm()
        
        # 处理退出确认对话框
        if show_exit_dialog:
            # 绘制半透明背景遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # 绘制对话框
            dialog_width, dialog_height = 500, 250
            dialog_x = (SCREEN_WIDTH - dialog_width) // 2
            dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
            
            # 对话框背景
            pygame.draw.rect(screen, (40, 40, 60), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(screen, (80, 80, 100), (dialog_x, dialog_y, dialog_width, dialog_height), width=3, border_radius=15)
            
            # 对话框标题
            title_text = font.render("退出游戏", True, (255, 100, 100))
            screen.blit(title_text, (dialog_x + (dialog_width - title_text.get_width()) // 2, dialog_y + 30))
            
            # 对话框内容
            message_text1 = font.render("确定要退出游戏吗？", True, TEXT_COLOR)
            message_text2 = font.render("游戏进度将不会保存！", True, TEXT_COLOR)
            screen.blit(message_text1, (dialog_x + (dialog_width - message_text1.get_width()) // 2, dialog_y + 80))
            screen.blit(message_text2, (dialog_x + (dialog_width - message_text2.get_width()) // 2, dialog_y + 110))
            
            # 确定按钮
            confirm_button = pygame.Rect(dialog_x + 100, dialog_y + 160, 120, 50)
            pygame.draw.rect(screen, (200, 60, 60), confirm_button, border_radius=10)
            pygame.draw.rect(screen, (255, 100, 100), confirm_button, width=2, border_radius=10)
            confirm_text = font.render("确定退出", True, WHITE)
            screen.blit(confirm_text, (confirm_button.x + (confirm_button.width - confirm_text.get_width()) // 2, 
                                      confirm_button.y + (confirm_button.height - confirm_text.get_height()) // 2))
            
            # 取消按钮
            cancel_button = pygame.Rect(dialog_x + 280, dialog_y + 160, 120, 50)
            pygame.draw.rect(screen, (60, 160, 60), cancel_button, border_radius=10)
            pygame.draw.rect(screen, (100, 255, 100), cancel_button, width=2, border_radius=10)
            cancel_text = font.render("取消", True, WHITE)
            screen.blit(cancel_text, (cancel_button.x + (cancel_button.width - cancel_text.get_width()) // 2, 
                                    cancel_button.y + (cancel_button.height - cancel_text.get_height()) // 2))
            
            # 处理鼠标点击
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = pygame.mouse.get_pressed()[0]
            
            # 按钮悬停效果
            if confirm_button.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (220, 80, 80), confirm_button, border_radius=10)
                screen.blit(confirm_text, (confirm_button.x + (confirm_button.width - confirm_text.get_width()) // 2, 
                                         confirm_button.y + (confirm_button.height - confirm_text.get_height()) // 2))
                
            if cancel_button.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (80, 180, 80), cancel_button, border_radius=10)
                screen.blit(cancel_text, (cancel_button.x + (cancel_button.width - cancel_text.get_width()) // 2, 
                                        cancel_button.y + (cancel_button.height - cancel_text.get_height()) // 2))
            
            # 处理按钮点击
            if mouse_clicked:
                if confirm_button.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                elif cancel_button.collidepoint(mouse_pos):
                    show_exit_dialog = False
                    paused = True
                    # 隐藏鼠标光标
                    pygame.mouse.set_visible(False)
            
            pygame.display.flip()
            clock.tick(60)
            continue

        # 游戏结束状态处理
        if game_over:
            pygame.mouse.set_visible(True)
            
            # 检查是否创造了新纪录
            if two_player_manager.active:
                # 双人模式下取两个玩家的最高分
                current_max_score = max(two_player_manager.scores) if two_player_manager.scores else 0
                if current_max_score > high_score:
                    high_score = current_max_score
                    new_high_score = True
                    save_highscore(high_score)
            else:
                # 单人模式
                if score > high_score:
                    high_score = score
                    new_high_score = True
                    save_highscore(high_score)
                
            # 只在第一次进入游戏结束状态时播放音效和停止背景音乐
            if not game_over_sound_played:
                # 播放游戏结束音效
                sound_manager.play('game_over', 0.9)
                # 停止背景音乐
                pygame.mixer.music.stop()
                game_over_sound_played = True
            
            # 显示游戏结束画面
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # 双人模式游戏结束界面
            if two_player_manager.active:
                # 双人模式游戏结束界面
                game_over_text = font.render("游戏结束", True, (255, 100, 100))
                player1_score = font.render(f"玩家1得分: {two_player_manager.scores[0]}", True, BLUE)
                player2_score = font.render(f"玩家2得分: {two_player_manager.scores[1]}", True, PLAYER2_COLOR)
                high_score_text = font.render(f"最高分: {high_score}", True, YELLOW)
                restart_text = font.render("按 Alt 键重新开始", True, (150, 255, 150))
                
                # 如果创造了新纪录，显示特殊消息
                if new_high_score:
                    new_record_text = font.render("新纪录!", True, (255, 215, 0))
                    screen.blit(new_record_text, (SCREEN_WIDTH//2 - new_record_text.get_width()//2, SCREEN_HEIGHT//2 - 120))
                
                screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
                screen.blit(player1_score, (SCREEN_WIDTH//2 - player1_score.get_width()//2, SCREEN_HEIGHT//2))
                screen.blit(player2_score, (SCREEN_WIDTH//2 - player2_score.get_width()//2, SCREEN_HEIGHT//2 + 30))
                screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, SCREEN_HEIGHT//2 + 60))
                screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 120))
            else:
                # 单人模式游戏结束界面
                game_over_text = font.render("游戏结束", True, (255, 100, 100))
                score_text = font.render(f"最终得分: {score}", True, TEXT_COLOR)
                high_score_text = font.render(f"最高分: {high_score}", True, YELLOW)
                restart_text = font.render("按 Alt 键重新开始", True, (150, 255, 150))
                
                # 如果创造了新纪录，显示特殊消息
                if new_high_score:
                    new_record_text = font.render("新纪录!", True, (255, 215, 0))
                    screen.blit(new_record_text, (SCREEN_WIDTH//2 - new_record_text.get_width()//2, SCREEN_HEIGHT//2 - 120))
                
                screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
                screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
                screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, SCREEN_HEIGHT//2 + 30))
                screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 90))
            
            pygame.display.flip()
            clock.tick(60)
            continue
        
        # 暂停状态处理
        if paused:
            # 显示暂停画面
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            pause_text = font.render("游戏暂停  按 空格键 继续", True, WHITE)
            
            # 控制方式显示
            if two_player_manager.active:
                control_text1 = font.render(f"玩家1控制: {'鼠标' if two_player_manager.players[0].use_mouse_control else '键盘'}", True, CYAN)
                control_text2 = font.render(f"玩家2控制: {'AI' if two_player_manager.players[1].ai_enabled else '键盘'}", True, CYAN)
                switch_text = font.render("按 Ctrl 键切换玩家1控制方式", True, CYAN)
            else:
                control_text = font.render(f"控制方式: {'鼠标' if player.use_mouse_control else '键盘'}", True, CYAN)
                switch_text = font.render("按 Ctrl 键切换控制方式", True, CYAN)
            
            restart_text = font.render("按 Alt 键重新开始游戏", True, (150, 255, 150))
            
            # AI状态显示
            if two_player_manager.active:
                ai_status1 = "AI" if two_player_manager.players[0].ai_enabled else "人类"
                ai_status2 = "AI" if two_player_manager.players[1].ai_enabled else "人类"
                ai_text = font.render(f"玩家1:{ai_status1} 玩家2:{ai_status2} (回车键切换玩家2)", True, (255, 200, 100))
            else:
                ai_status = "开启" if player.ai_enabled else "关闭"
                ai_text = font.render(f"AI模式: {ai_status} (按回车键切换)", True, (255, 200, 100))
            
            # 双人模式提示
            if two_player_manager.active:
                two_player_text = font.render("双人模式已激活 (按0键退出)", True, (100, 255, 100))
                screen.blit(two_player_text, (SCREEN_WIDTH//2 - two_player_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            else:
                two_player_text = font.render("1键添加AI玩家 2键添加人类玩家", True, (200, 200, 255))
                screen.blit(two_player_text, (SCREEN_WIDTH//2 - two_player_text.get_width()//2, SCREEN_HEIGHT//2 - 53))
            
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
            
            if two_player_manager.active:
                screen.blit(control_text1, (SCREEN_WIDTH//2 - control_text1.get_width()//2, SCREEN_HEIGHT//2 - 20))
                screen.blit(control_text2, (SCREEN_WIDTH//2 - control_text2.get_width()//2, SCREEN_HEIGHT//2 + 10))
            else:
                screen.blit(control_text, (SCREEN_WIDTH//2 - control_text.get_width()//2, SCREEN_HEIGHT//2 - 7))
            
            screen.blit(switch_text, (SCREEN_WIDTH//2 - switch_text.get_width()//2, SCREEN_HEIGHT//2 + 40))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 100))
            screen.blit(ai_text, (SCREEN_WIDTH//2 - ai_text.get_width()//2, SCREEN_HEIGHT//2 + 160))

            pygame.display.flip()
            clock.tick(60)
            continue

        # 双人模式游戏逻辑
        if two_player_manager.active:
            # 双人模式更新
            current_time = time.time()
            
            # 更新所有玩家
            for i, player_obj in enumerate(two_player_manager.players):
                if player_obj.lives <= 0:
                    player_obj.active = False
                    continue
                
                # 更新玩家位置
                if player_obj.ai_enabled:
                    # AI控制
                    player_obj.ai_control(stars, hearts, shields, bombs, craters, two_player_manager.scores[i])
                else:
                    # 玩家控制
                    if player_obj.player_id == 1:  # 玩家1
                        if player_obj.use_mouse_control:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            player_obj.move_with_mouse(mouse_x, mouse_y)
                        else:
                            keys = pygame.key.get_pressed()
                            player_obj.move_with_keyboard(keys)
                    else:  # 玩家2
                        keys = pygame.key.get_pressed()
                        player_obj.move_with_keyboard(keys)
                
                # 边界检查
                player_obj.x = max(player_obj.radius, min(SCREEN_WIDTH - player_obj.radius, player_obj.x))
                player_obj.y = max(player_obj.radius, min(SCREEN_HEIGHT - player_obj.radius, player_obj.y))
                
                # 更新玩家尾焰
                player_obj.update_trail()
                
                # 更新护盾状态
                player_obj.update_shield()
                
                # 更新受伤效果
                player_obj.update_hit_effect()
                
                # 更新玩家速度（考虑弹坑影响）
                player_obj.update_speed(craters)
                
                # 检测玩家与物品的碰撞
                player_pos = player_obj.get_pos()
                player_x, player_y = player_pos
                
                for star in stars:
                    if star.active:
                        # 使用平方距离优化性能
                        distance_sq = (player_x - star.x)**2 + (player_y - star.y)**2
                        min_distance_sq = (player_obj.radius + star.radius)**2
                        if distance_sq <= min_distance_sq:
                            two_player_manager.scores[i] += star.value
                            # 播放收集星星音效
                            sound_manager.play('collect_star', 0.7)
                            # 创建得分飘字效果
                            score_popup = ScorePopup(star.x, star.y, star.value, star.color)
                            score_popups.append(score_popup)
                            # 重新生成星星
                            all_items = stars + hearts + shields
                            star.respawn(all_items)
                
                for heart in hearts:
                    if heart.active:
                        distance_sq = (player_x - heart.x)**2 + (player_y - heart.y)**2
                        min_distance_sq = (player_obj.radius + heart.radius)**2
                        if distance_sq <= min_distance_sq:
                            player_obj.lives += heart.value
                            two_player_manager.lives[i] = player_obj.lives
                            # 播放收集爱心音效
                            sound_manager.play('collect_heart', 0.7)
                            # 爱心出现概率
                            current_heart_spawn_rate = calculate_heart_spawn_rate(player_obj.lives)
                            if random.random() < current_heart_spawn_rate:
                                all_items = stars + hearts + shields
                                heart.respawn(all_items)
                            else:
                                heart.active = False
                
                for shield in shields:
                    if shield.active:
                        distance_sq = (player_x - shield.x)**2 + (player_y - shield.y)**2
                        min_distance_sq = (player_obj.radius + shield.radius)**2
                        if distance_sq <= min_distance_sq:
                            player_obj.activate_shield()
                            # 播放收集护盾音效
                            sound_manager.play('collect_shield', 0.7)
                            shield.active = False
                
                # 检测玩家与炸弹爆炸的碰撞
                for bomb in bombs:
                    if bomb.is_player_in_explosion(player_pos) and not player_obj.shield_active:
                        player_obj.lives -= 1
                        two_player_manager.lives[i] = player_obj.lives
                        # 播放玩家受伤音效
                        sound_manager.play('player_hit', 0.8)
                        # 触发玩家受伤效果
                        player_obj.activate_hit_effect()
                        bomb.exploding = False
                        bomb.active = False
                        if player_obj.lives <= 0:
                            player_obj.active = False
                            # 检查游戏是否结束
                            if two_player_manager.is_game_over():
                                game_over = True
                                two_player_manager.update_high_scores()
            
            if two_player_manager.active:
                # 使用存活玩家的最高分数
                if two_player_manager.get_alive_players_count() > 0:
                    highest_score = two_player_manager.get_highest_alive_player_score()
                    base_spawn_time = calculate_bomb_spawn_time(highest_score)
                    max_bombs = min(15, 1 + int(highest_score / 20))
            else:
                # 单人模式
                base_spawn_time = calculate_bomb_spawn_time(score)
                max_bombs = min(15, 1 + int(score / 20))
            
            if current_time - last_bomb_spawn >= base_spawn_time and len(bombs) < max_bombs:
                last_bomb_spawn = current_time
                if two_player_manager.get_alive_players_count() > 0:
                    highest_score = two_player_manager.get_highest_alive_player_score()
                    bombs.append(Bomb(highest_score, craters, True))
                
            
            # 更新炸弹状态
            for bomb in bombs[:]:
                bomb.update()
                
                # 爆炸时销毁范围内的物品
                bomb.destroy_items_in_explosion(stars)
                bomb.destroy_items_in_explosion(hearts)
                bomb.destroy_items_in_explosion(shields)
                            
                # 爆炸结束后创建弹坑
                if bomb.exploding and not bomb.active and highest_score >= CRATER_SCORE_THRESHOLD:
                    # 创建与爆炸形状和范围一致的弹坑
                    crater_radius = int(bomb.expansion_speed * 2.0)  # 弹坑半径等于爆炸最大半径
                    craters.append(Crater(bomb.x, bomb.y, crater_radius, bomb.explosion_shape))
                    bombs.remove(bomb)
                elif bomb.exploding and not bomb.active:
                    bombs.remove(bomb)
            
            # 更新弹坑状态
            for crater in craters[:]:
                crater.update()
                if not crater.active:
                    craters.remove(crater)
            
            # 定期检查是否需要生成新爱心
            heart_check_interval = 3.0 + math.sqrt(highest_score)
            if two_player_manager.active:
                # 使用存活玩家的最高生命值
                if two_player_manager.get_alive_players_count() > 0:
                    highest_lives = two_player_manager.get_highest_alive_player_lives()
                    current_heart_spawn_rate = calculate_heart_spawn_rate(highest_lives)
            else:
                # 单人模式
                current_heart_spawn_rate = calculate_heart_spawn_rate(lives)
            
            if current_time - last_heart_spawn_check >= heart_check_interval:
                last_heart_spawn_check = current_time
                active_hearts = sum(1 for heart in hearts if heart.active)
                if active_hearts < 1 and random.random() < current_heart_spawn_rate:
                    for heart in hearts:
                        if not heart.active:
                            all_items = stars + hearts + shields
                            heart.respawn(all_items)
                            break
            
            # 增加护盾生成频率
            shield_check_interval = 5.0
            if current_time - last_shield_spawn_check >= shield_check_interval:
                last_shield_spawn_check = current_time
                active_shields = sum(1 for shield in shields if shield.active)
                if active_shields < 1 and random.random() < 0.5:
                    for shield in shields:
                        if not shield.active:
                            all_items = stars + hearts + shields
                            shield.respawn(all_items)
                            break
            
            # 确保有足够的星星
            active_stars = sum(1 for star in stars if star.active)
            if active_stars < 3:
                for star in stars:
                    if not star.active:
                        all_items = stars + hearts + shields
                        star.respawn(all_items)
                        break
            
            # 更新物品状态
            for star in stars:
                star.update()
            for heart in hearts:
                heart.update()
            for shield in shields:
                shield.update()
            
            # 更新得分飘字效果
            for popup in score_popups[:]:
                if popup.update():
                    score_popups.remove(popup)
        else:
            # 单人模式游戏逻辑
            # 更新玩家位置
            if player.ai_enabled:
                # AI控制模式
                player.ai_control(stars, hearts, shields, bombs, craters, score)
            else:
                # 玩家控制模式
                if player.use_mouse_control:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    player.move_with_mouse(mouse_x, mouse_y)
                else:
                    keys = pygame.key.get_pressed()
                    player.move_with_keyboard(keys)
            
            # 边界检查
            player.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.x))
            player.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.y))
            
            # 更新玩家尾焰
            player.update_trail()
            
            # 更新护盾状态
            player.update_shield()
            
            # 更新受伤效果
            player.update_hit_effect()
            
            # 更新玩家速度（考虑弹坑影响）
            player.update_speed(craters)
            
            # 根据分数调整炸弹生成频率
            base_spawn_time = calculate_bomb_spawn_time(score)
            max_bombs = min(15, 1 + int(score / 20))
            
            current_time = time.time()
            if current_time - last_bomb_spawn >= base_spawn_time and len(bombs) < max_bombs:
                bombs.append(Bomb(score, craters, False))
                last_bomb_spawn = current_time
            
            # 更新炸弹状态
            for bomb in bombs[:]:
                bomb.update()
                
                # 爆炸时销毁范围内的物品
                bomb.destroy_items_in_explosion(stars)
                bomb.destroy_items_in_explosion(hearts)
                bomb.destroy_items_in_explosion(shields)
                
                # 爆炸结束后创建弹坑
                if bomb.exploding and not bomb.active and score >= CRATER_SCORE_THRESHOLD:
                    # 创建与爆炸形状和范围一致的弹坑
                    crater_radius = int(bomb.expansion_speed * 2.0)  # 弹坑半径等于爆炸最大半径
                    craters.append(Crater(bomb.x, bomb.y, crater_radius, bomb.explosion_shape))
                    bombs.remove(bomb)
                elif bomb.exploding and not bomb.active:
                    bombs.remove(bomb)
            
            # 更新弹坑状态
            for crater in craters[:]:
                crater.update()
                if not crater.active:
                    craters.remove(crater)
            
            # 更新物品状态
            for star in stars:
                star.update()
            for heart in hearts:
                heart.update()
            for shield in shields:
                shield.update()
            
            # 检测玩家与物品的碰撞
            player_pos = player.get_pos()
            player_x, player_y = player_pos
            
            for star in stars:
                if star.active:
                    # 使用平方距离优化性能
                    distance_sq = (player_x - star.x)**2 + (player_y - star.y)**2
                    min_distance_sq = (player.radius + star.radius)**2
                    if distance_sq <= min_distance_sq:
                        score += star.value
                        # 播放收集星星音效
                        sound_manager.play('collect_star', 0.7)
                        # 创建得分飘字效果
                        score_popup = ScorePopup(star.x, star.y, star.value, star.color)
                        score_popups.append(score_popup)
                        # 重新生成星星
                        all_items = stars + hearts + shields
                        star.respawn(all_items)
            
            # 爱心出现概率
            current_heart_spawn_rate = calculate_heart_spawn_rate(lives)
            
            for heart in hearts:
                if heart.active:
                    # 使用平方距离优化性能
                    distance_sq = (player_x - heart.x)**2 + (player_y - heart.y)**2
                    min_distance_sq = (player.radius + heart.radius)**2
                    if distance_sq <= min_distance_sq:
                        lives += heart.value
                        # 播放收集爱心音效
                        sound_manager.play('collect_heart', 0.7)
                        if random.random() < current_heart_spawn_rate:
                            # 重新生成爱心，确保不相交
                            all_items = stars + hearts + shields
                            heart.respawn(all_items)
                        else:
                            heart.active = False
            
            # 护盾道具
            for shield in shields:
                if shield.active:
                    # 使用平方距离优化性能
                    distance_sq = (player_x - shield.x)**2 + (player_y - shield.y)**2
                    min_distance_sq = (player.radius + shield.radius)**2
                    if distance_sq <= min_distance_sq:
                        player.activate_shield()
                        # 播放收集护盾音效
                        sound_manager.play('collect_shield', 0.7)
                        shield.active = False
            
            # 定期检查是否需要生成新爱心
            heart_check_interval = 3.0 + math.sqrt(score)
            if current_time - last_heart_spawn_check >= heart_check_interval:
                last_heart_spawn_check = current_time
                active_hearts = sum(1 for heart in hearts if heart.active)
                if active_hearts < 1 and random.random() < current_heart_spawn_rate:
                    for heart in hearts:
                        if not heart.active:
                            # 重新生成爱心，确保不相交
                            all_items = stars + hearts + shields
                            heart.respawn(all_items)
                            break
            
            # 增加护盾生成频率
            shield_check_interval = 5.0
            if current_time - last_shield_spawn_check >= shield_check_interval:
                last_shield_spawn_check = current_time
                active_shields = sum(1 for shield in shields if shield.active)
                if active_shields < 1 and random.random() < 0.5:
                    for shield in shields:
                        if not shield.active:
                            # 重新生成护盾，确保不相交
                            all_items = stars + hearts + shields
                            shield.respawn(all_items)
                            break
            
            # 检测玩家与炸弹爆炸的碰撞
            for bomb in bombs:
                if bomb.is_player_in_explosion(player_pos) and not player.shield_active:
                    lives -= 1
                    # 播放玩家受伤音效
                    sound_manager.play('player_hit', 0.8)
                    # 触发玩家受伤效果
                    player.activate_hit_effect()
                    bomb.exploding = False
                    bomb.active = False
                    if lives <= 0:
                        game_over = True
            
            # 确保有足够的星星
            active_stars = sum(1 for star in stars if star.active)
            if active_stars < 3:
                for star in stars:
                    if not star.active:
                        # 重新生成星星，确保不相交
                        all_items = stars + hearts + shields
                        star.respawn(all_items)
                        break
            
            # 更新得分飘字效果
            for popup in score_popups[:]:
                if popup.update():
                    score_popups.remove(popup)
        
        # 绘制游戏界面
        screen.fill(BG_COLOR)
        draw_stars_bg()  # 绘制星空背景
        
        # 隐藏鼠标光标
        pygame.mouse.set_visible(False)
        
        # 绘制弹坑
        for crater in craters:
            crater.draw()
        
        # 绘制星星
        for star in stars:
            star.draw()
        
        # 绘制爱心
        for heart in hearts:
            heart.draw()
        
        # 绘制护盾
        for shield in shields:
            shield.draw()
        
        # 绘制炸弹
        for bomb in bombs:
            bomb.draw()
        
        # 双人模式绘制
        if two_player_manager.active:
            for player_obj in two_player_manager.players:
                if player_obj.active:
                    player_obj.draw()
                # 绘制AI调试信息
                player_obj.draw_ai_debug()
        else:
            # 单人模式绘制
            player.draw()
            # 绘制AI调试信息
            player.draw_ai_debug()
        
        # 绘制得分飘字效果
        for popup in score_popups:
            popup.draw()
        
        # 显示UI
        if two_player_manager.active:
            # 双人模式UI
            player1_score_text = font.render(f"玩家1: {two_player_manager.scores[0]}", True, BLUE)
            player2_score_text = font.render(f"玩家2: {two_player_manager.scores[1]}", True, PLAYER2_COLOR)
            player1_lives_text = font.render(f"生命: {two_player_manager.lives[0]}", True, GREEN)
            player2_lives_text = font.render(f"生命: {two_player_manager.lives[1]}", True, GREEN)
            high_score_text = font.render(f"最高分: {max(two_player_manager.high_scores)}", True, YELLOW)
            control_text = small_font.render(f"控制: 玩家1-{'鼠标' if two_player_manager.players[0].use_mouse_control else '键盘'}/玩家2-{'AI' if two_player_manager.players[1].ai_enabled else '键盘'}", True, TEXT_COLOR)
            switch_text = small_font.render("按 Ctrl 键切换控制方式", True, TEXT_COLOR)
            ai_status1 = "AI" if two_player_manager.players[0].ai_enabled else "人类"
            ai_status2 = "AI" if two_player_manager.players[1].ai_enabled else "人类"
            ai_text = small_font.render(f"玩家1:{ai_status1}/玩家2:{ai_status2} (回车键切换)", True, (255, 200, 100))
            
            screen.blit(player1_score_text, (10, 10))
            screen.blit(player1_lives_text, (SCREEN_WIDTH - 120, 10))
            screen.blit(player2_score_text, (10, 40))
            screen.blit(player2_lives_text, (SCREEN_WIDTH - 120, 40))
            screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, 10))
            screen.blit(control_text, (10, SCREEN_HEIGHT - 40))
            screen.blit(switch_text, (10, SCREEN_HEIGHT - 20))
            screen.blit(ai_text, (SCREEN_WIDTH - 350, SCREEN_HEIGHT - 20))
        else:
            # 单人模式UI
            score_text = font.render(f"得分: {score}", True, TEXT_COLOR)
            lives_text = font.render(f"生命: {lives}", True, GREEN)
            high_score_text = font.render(f"最高分: {high_score}", True, YELLOW)
            control_text = small_font.render(f"控制: {'鼠标' if player.use_mouse_control else '键盘'}", True, TEXT_COLOR)
            switch_text = small_font.render("按 Ctrl 键切换", True, TEXT_COLOR)
            ai_status = "AI模式: 开启" if player.ai_enabled else "AI模式: 关闭"
            ai_text = small_font.render(f"{ai_status} (回车键切换)", True, (255, 200, 100))
            two_player_hint = small_font.render("1键添加AI玩家 2键添加人类玩家", True, (200, 200, 255))
            
            screen.blit(score_text, (10, 10))
            screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
            screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, 10))
            screen.blit(control_text, (10, SCREEN_HEIGHT - 40))
            screen.blit(switch_text, (10, SCREEN_HEIGHT - 20))
            screen.blit(ai_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 20))
            screen.blit(two_player_hint, (SCREEN_WIDTH//2 - two_player_hint.get_width()//2, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(60)

# 辅助函数
def calculate_bomb_spawn_time(score):
    """计算炸弹生成时间（基于分数）"""
    # 炸弹生成速度有上限和下限，使用更平缓的增长曲线
    base_time = max(MIN_BOMB_SPAWN_RATE, min(MAX_BOMB_SPAWN_RATE, 6.0 - score * 0.05))
    return base_time

def calculate_heart_spawn_rate(lives):
    """计算爱心出现概率（基于生命值）"""
    # 爱心出现概率随生命值增加而减小
    return BASE_HEART_SPAWN_RATE + (3 - lives) / 10

def draw_stars_bg():
    """绘制星空背景"""
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.random() * 1.5
        brightness = random.randint(100, 220)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)

# 物品生成常量
single_player_items = {
    'stars': 5,
    'hearts': 1,
    'shields': 1
}

two_player_items = {
    'stars': 10,  # 双人模式下星星数量翻倍
    'hearts': 2,  # 双人模式下爱心数量翻倍
    'shields': 2  # 双人模式下护盾数量翻倍
}

# 主程序入口
if __name__ == "__main__":
    main()
                