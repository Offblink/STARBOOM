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

# 创建游戏窗口 - 回退到窗口模式
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("STARBOOM")
clock = pygame.time.Clock()

# 音频初始化
SAMPLE_RATE = 44100
CHANNELS = 2
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=CHANNELS, buffer=1024)

# 音效生成器类
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
                pygame.mixer.music.play(loops=-1, start=2.0)  # 循环播放
            else:
                print("警告: 未找到bgm.mp3文件，背景音乐将不会播放")
        except Exception as e:
            print(f"加载背景音乐时出错: {e}")

# 加载中文字体
try:
    # 尝试加载系统中文字体
    font = pygame.font.SysFont('simhei', 24)
    small_font = pygame.font.SysFont('simhei', 18)
    score_font = pygame.font.SysFont('simhei', 28, bold=True)
except:
    # 如果失败，使用默认字体
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)
    score_font = pygame.font.SysFont("Arial", 28, bold=True)
    print("警告: 未找到中文字体，使用默认字体")

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

# 新增：得分飘字效果类
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

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2  # 玩家初始X坐标
        self.y = SCREEN_HEIGHT // 2  # 玩家初始Y坐标
        self.radius = PLAYER_RADIUS  # 玩家半径
        self.color = BLUE  # 玩家颜色
        self.base_speed = PLAYER_SPEED  # 玩家基础移动速度
        self.speed = self.base_speed  # 当前移动速度
        self.in_crater = False  # 是否在弹坑中
        self.shield_active = False  # 护盾是否激活
        self.shield_start_time = 0  # 护盾激活开始时间
        self.use_mouse_control = True  # 默认使用鼠标控制
        self.direction = [0, 0]  # 移动方向 (x, y)
        self.trail_particles = []  # 尾焰粒子
        self.max_trail_particles = 20  # 最大尾焰粒子数
        
        # 新增：受伤效果相关属性
        self.hit_effect_active = False  # 受伤效果是否激活
        self.hit_effect_start_time = 0  # 受伤效果开始时间
        self.hit_flash_visible = True  # 受伤闪烁是否可见
        self.last_flash_toggle = 0  # 上次闪烁切换时间
        self.hit_particles = []  # 受伤粒子效果
        self.max_hit_particles = 30  # 最大受伤粒子数
        
    def move_with_mouse(self, mouse_x, mouse_y):
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
        # 根据按键移动
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
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
        # 更新尾焰粒子
        i = 0
        while i < len(self.trail_particles):
            particle = self.trail_particles[i]
            particle['life'] -= 0.05  # 粒子生命周期减少
            if particle['life'] <= 0:
                self.trail_particles.pop(i)
            else:
                i += 1
    
    def update_speed(self, craters):
        # 检查是否在弹坑内
        self.in_crater = False
        for crater in craters:
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
        self.shield_active = True  # 激活护盾
        self.shield_start_time = time.time()  # 记录护盾激活时间
    
    def update_shield(self):
        # 检查护盾是否应该消失
        if self.shield_active and time.time() - self.shield_start_time >= SHIELD_DURATION:
            self.shield_active = False  # 护盾失效
    
    # 新增：激活受伤效果
    def activate_hit_effect(self):
        self.hit_effect_active = True
        self.hit_effect_start_time = time.time()
        self.hit_flash_visible = True
        self.last_flash_toggle = time.time()
        
        # 创建受伤粒子效果
        self.create_hit_particles()
    
    # 新增：创建受伤粒子
    def create_hit_particles(self):
        for _ in range(min(20, self.max_hit_particles - len(self.hit_particles))):  # 限制粒子数量
            angle = random.uniform(0, PI_2)
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
    
    # 新增：更新受伤效果
    def update_hit_effect(self):
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
        # 绘制尾焰粒子
        for particle in self.trail_particles:
            alpha = int(255 * particle['life'])
            size = particle['size'] * particle['life']
            s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, alpha), (int(size), int(size)), int(size))
            screen.blit(s, (particle['x'] - size, particle['y'] - size))
        
        # 新增：绘制受伤粒子
        for particle in self.hit_particles:
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            size = particle['size'] * (particle['lifetime'] / particle['max_lifetime'])
            color = (*particle['color'], alpha)
            
            s = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(size), int(size)), int(size))
            screen.blit(s, (particle['x'] - size, particle['y'] - size))
        
        # 新增：受伤闪烁效果 - 只在可见时绘制玩家
        if not self.hit_effect_active or self.hit_flash_visible:
            # 绘制玩家
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            
            # 添加玩家细节
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius - 5, 2)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius - 10, 1)
            
            # 绘制玩家光泽效果
            pygame.draw.circle(screen, (100, 255, 255), (int(self.x - 4), int(self.y - 4)), self.radius // 3)
            
            # 绘制护盾效果
            if self.shield_active:
                shield_radius = self.radius + 10
                for i in range(3):
                    pygame.draw.circle(screen, (CYAN[0], CYAN[1], CYAN[2], 100 - i*30), 
                                     (int(self.x), int(self.y)), shield_radius + i*2, 2)
            
            # 如果在弹坑中，显示减速效果
            if self.in_crater:
                pygame.draw.circle(screen, (GRAY[0], GRAY[1], GRAY[2], 100), 
                                 (int(self.x), int(self.y)), self.radius + 5, 2)
        
    def get_pos(self):
        return (self.x, self.y)

class Item:
    def __init__(self, item_type):
        self.type = item_type  # 物品类型："star", "heart" 或 "shield"
        
        # 根据物品类型设置属性
        if self.type == "star":
            # 修复：确保每次初始化时都随机大小
            self.size = random.choice(["small", "medium", "large"])  # 星星大小
            if self.size == "small":
                self.radius = ITEM_RADIUS  # 小星星半径
                self.value = 1  # 小星星分值
                self.color = YELLOW  # 小星星颜色
            elif self.size == "medium":
                self.radius = ITEM_RADIUS + 3  # 中星星半径
                self.value = 2  # 中星星分值
                self.color = (255, 200, 0)  # 中星星颜色
            else:  # large
                self.radius = ITEM_RADIUS + 6  # 大星星半径
                self.value = 3  # 大星星分值
                self.color = (255, 150, 0)  # 大星星颜色
        elif self.type == "heart":
            self.color = RED  # 爱心颜色
            self.value = 1  # 爱心分值（增加生命值）
            self.radius = ITEM_RADIUS  # 爱心半径
        else:  # shield
            self.color = CYAN  # 护盾颜色
            self.value = 0  # 护盾分值（不增加分数）
            self.radius = ITEM_RADIUS  # 护盾半径
        
        self.respawn()  # 初始化物品位置
        self.pulse_value = 0  # 脉冲效果值
        self.pulse_speed = 0.05  # 脉冲速度
            
    def respawn(self, items=None):
        # 修复：星星重新生成时也重新随机大小
        if self.type == "star":
            self.size = random.choice(["small", "medium", "large"])  # 重新随机星星大小
            if self.size == "small":
                self.radius = ITEM_RADIUS  # 小星星半径
                self.value = 1  # 小星星分值
                self.color = YELLOW  # 小星星颜色
            elif self.size == "medium":
                self.radius = ITEM_RADIUS + 3  # 中星星半径
                self.value = 2  # 中星星分值
                self.color = (255, 200, 0)  # 中星星颜色
            else:  # large
                self.radius = ITEM_RADIUS + 6  # 大星星半径
                self.value = 3  # 大星星分值
                self.color = (255, 150, 0)  # 大星星颜色
        
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
            if items:
                for item in items:
                    if item is not self and item.active:
                        # 使用平方距离避免开方运算
                        distance_sq = (self.x - item.x)**2 + (self.y - item.y)**2
                        min_distance_sq = (self.radius + item.radius + 20)**2
                        if distance_sq < min_distance_sq:
                            overlap = True
                            break
            
            # 如果没有重叠，则接受这个位置
            if not overlap:
                break
            
        self.active = True  # 设置物品为激活状态
        
    def update(self):
        # 物品脉冲效果
        self.pulse_value += self.pulse_speed
        if self.pulse_value >= PI_2:
            self.pulse_value -= PI_2
        
    def draw(self):
        if not self.active:
            return
            
        # 计算脉冲大小
        pulse_factor = 0.9 + 0.1 * math.sin(self.pulse_value)
        current_radius = self.radius * pulse_factor
        
        if self.type == "star":
            # 绘制星形（五角星）
            self.draw_star(current_radius)
        elif self.type == "heart":
            # 绘制爱心
            self.draw_heart(current_radius)
        else:  # shield
            # 绘制护盾
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(current_radius))
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(current_radius), 2)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(current_radius - 3), 2)
    
    def draw_star(self, radius):
        # 绘制五角星
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
    
    def draw_heart(self, radius):
        # 绘制爱心形状 - 修复版，确保完全显示
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

class Bomb:
    def __init__(self, score, craters):
        # 先初始化属性
        self.score = score
        self.expansion_speed = min(MAX_EXPANSION_SPEED, 50 + score * 0.5)
        self.plant_time = time.time()
        self.exploding = False
        self.explosion_start_time = 0
        self.explosion_shape = random.choice(["circle", "rectangle"])
        self.warning_visible = True
        self.last_warning_toggle = time.time()
        self.warning_time = max(MIN_WARNING_TIME, BASE_WARNING_TIME - score * 0.02)
        self.particles = []
        self.max_particles = 100  # 最大粒子数
        
        # 然后调用respawn
        self.respawn(craters)
        
    def respawn(self, craters):
        # 尝试生成不与弹坑重叠的炸弹位置
        max_attempts = 50  # 最大尝试次数
        for attempt in range(max_attempts):
            # 随机生成炸弹位置
            self.x = random.randint(BOMB_RADIUS, SCREEN_WIDTH - BOMB_RADIUS)
            self.y = random.randint(BOMB_RADIUS, SCREEN_HEIGHT - BOMB_RADIUS)
            
            # 检查是否与现有弹坑重叠
            overlap = False
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
        
        self.radius = BOMB_RADIUS
        self.active = True
        self.plant_time = time.time()
        self.exploding = False
        
    def create_particles(self):
        # 创建爆炸粒子（性能优化：限制粒子数量）
        for _ in range(min(50, self.max_particles - len(self.particles))):
            angle = random.uniform(0, PI_2)
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
        # 更新爆炸粒子
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
        current_time = time.time()  # 当前时间
        
        # 预警闪烁效果
        if current_time - self.last_warning_toggle > 0.2:  # 每0.2秒切换一次
            self.warning_visible = not self.warning_visible
            self.last_warning_toggle = current_time
            
        # 检查是否应该爆炸（考虑预警时间）
        if not self.exploding and current_time - self.plant_time >= (BOMB_TIMER - self.warning_time):
            self.exploding = True  # 开始爆炸
            self.explosion_start_time = current_time  # 记录爆炸开始时间
            self.create_particles()  # 创建爆炸粒子
            
        # 更新爆炸粒子
        if self.exploding:
            self.update_particles()
            
        # 检查爆炸是否结束
        if self.exploding and current_time - self.explosion_start_time >= EXPLOSION_DURATION:
            self.active = False  # 爆炸结束
            
    def draw(self):
        if not self.active:
            return
            
        if not self.exploding:
            # 绘制炸弹
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 80, 0), (int(self.x), int(self.y)), self.radius, 2)
            
            # 绘制引线
            fuse_length = 5
            pygame.draw.line(screen, (100, 40, 0), (self.x, self.y - self.radius), 
                            (self.x, self.y - self.radius - fuse_length), 2)
            
            # 绘制十字准心
            self.draw_crosshair()
            
            # 绘制预警标志（覆盖整个爆炸范围）
            if self.warning_visible:
                # 计算最大爆炸半径（速度×时间）
                max_explosion_radius = int(self.expansion_speed * EXPLOSION_DURATION)
                if self.explosion_shape == "circle":
                    # 圆形预警 - 覆盖整个爆炸范围
                    pygame.draw.circle(screen, (255, 0, 0, 80), (int(self.x), int(self.y)), 
                                     max_explosion_radius, 2)
                else:
                    # 矩形预警 - 覆盖整个爆炸范围
                    rect_width = max_explosion_radius * 2
                    rect_height = max_explosion_radius * 2
                    rect_x = self.x - rect_width // 2
                    rect_y = self.y - rect_height // 2
                    pygame.draw.rect(screen, (255, 0, 0, 80), 
                                   (rect_x, rect_y, rect_width, rect_height), 2)
        else:
            # 修改点：使用时间×速度计算爆炸半径，而不是进度×速度
            current_time = time.time()
            time_elapsed = current_time - self.explosion_start_time
            current_explosion_radius = int(self.expansion_speed * time_elapsed)
            max_possible_radius = int(self.expansion_speed * EXPLOSION_DURATION)
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
    
    # 新增：绘制十字准心
    def draw_crosshair(self):
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
        if not self.exploding:
            return False
            
        player_x, player_y = player_pos
        # 修改点：使用时间×速度计算爆炸半径
        current_time = time.time()
        time_elapsed = current_time - self.explosion_start_time
        current_explosion_radius = int(self.expansion_speed * time_elapsed)
        max_possible_radius = int(self.expansion_speed * EXPLOSION_DURATION)
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
        if not self.exploding:
            return
            
        # 修改点：使用时间×速度计算爆炸半径
        current_time = time.time()
        time_elapsed = current_time - self.explosion_start_time
        current_explosion_radius = int(self.expansion_speed * time_elapsed)
        max_possible_radius = int(self.expansion_speed * EXPLOSION_DURATION)
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

class Crater:
    def __init__(self, x, y, radius, explosion_shape):
        self.x = x  # 弹坑X坐标
        self.y = y  # 弹坑Y坐标
        self.radius = radius  # 弹坑半径（与爆炸最大范围一致）
        self.explosion_shape = explosion_shape  # 弹坑形状（与爆炸形状一致）
        self.create_time = time.time()  # 弹坑创建时间
        self.active = True  # 弹坑是否活跃
        
    def update(self):
        # 检查弹坑是否应该消失
        if time.time() - self.create_time >= CRATER_DURATION:
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
                    pygame.draw.circle(s, (*GRAY, alpha), (radius, radius), radius)
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
                    s.fill((*GRAY, alpha))
                    screen.blit(s, (rect_x, rect_y))
            
            # 弹坑边框
            rect_x = self.x - self.radius
            rect_y = self.y - self.radius
            rect_width = self.radius * 2
            rect_height = self.radius * 2
            pygame.draw.rect(screen, (50, 50, 50), (rect_x, rect_y, rect_width, rect_height), 2)

def calculate_bomb_spawn_time(score):
    # 炸弹生成速度有上限和下限，使用更平缓的增长曲线
    base_time = max(MIN_BOMB_SPAWN_RATE, min(MAX_BOMB_SPAWN_RATE, 6.0 - score * 0.05))
    return base_time

def calculate_heart_spawn_rate(lives):
    # 爱心出现概率随生命值增加而减小
    return BASE_HEART_SPAWN_RATE + (3 - lives) / 10

def main():
    game_over_sound_played = False  # 添加这行
    show_exit_dialog = False  # 新增：控制是否显示退出确认对话框
    music_paused_before_dialog = False  # 新增：记录对话框显示前的音乐状态
    
    # 创建音效管理器
    sound_manager = SoundManager()
    sound_manager.play_bgm()  # 播放背景音乐
    
    # 加载最高分
    high_score = load_highscore()
    new_high_score = False  # 标记是否创造了新纪录
    
    player = Player()
    stars = [Item("star") for _ in range(5)]  # 创建5个星星
    hearts = [Item("heart") for _ in range(1)]  # 创建1个爱心
    shields = [Item("shield") for _ in range(1)]  # 创建1个护盾
    bombs = []  # 炸弹列表
    craters = []  # 弹坑列表
    score_popups = []  # 新增：得分飘字效果列表
    
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
        # 在事件处理部分，找到按键检测代码，修改如下：
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
                        
                if event.key == pygame.K_SPACE and not game_over and not show_exit_dialog:
                    # 空格键暂停/继续
                    paused = not paused
                    if paused:
                        # 暂停背景音乐
                        pygame.mixer.music.pause()
                        pygame.mouse.set_visible(True)
                    else:
                        # 继续播放背景音乐
                        pygame.mixer.music.unpause()
                        pygame.mouse.set_visible(False)
                        
                # 新增：Ctrl键切换控制模式（支持左右Ctrl键）
                elif (event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL) and not game_over and not show_exit_dialog:
                    # Ctrl键切换控制方式
                    player.use_mouse_control = not player.use_mouse_control
                    
                # 新增：Alt键重新开始游戏（在暂停和游戏结束状态都可用）
                elif (event.key == pygame.K_LALT or event.key == pygame.K_RALT) and (game_over or paused) and not show_exit_dialog:
                    
                    pygame.mouse.set_visible(False)
                    
                    # 重新开始游戏
                    player = Player()
                    stars = [Item("star") for _ in range(5)]
                    hearts = [Item("heart") for _ in range(2)]
                    shields = [Item("shield") for _ in range(2)]
                    bombs = []
                    craters = []
                    score_popups = []  # 清空得分飘字
                    score = 0
                    lives = 3
                    last_bomb_spawn = time.time()
                    last_heart_spawn_check = time.time()
                    last_shield_spawn_check = time.time()
                    game_over = False
                    game_over_sound_played = False
                    new_high_score = False
                    paused = False  # 确保退出暂停状态
                    show_exit_dialog = False  # 确保退出对话框状态
                    
                    # 重新播放背景音乐
                    sound_manager.play_bgm()
                    
                    # 重新初始化所有物品的位置
                    all_items = stars + hearts + shields
                    for item in all_items:
                        item.respawn(all_items)
        
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
                    # 隐藏鼠标光标
                    pygame.mouse.set_visible(False)
            
            pygame.display.flip()
            clock.tick(60)
            continue

        # 游戏结束状态处理
        if game_over:
            
            pygame.mouse.set_visible(True)
            
            # 检查是否创造了新纪录
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
            
            game_over_text = font.render("游戏结束", True, (255, 100, 100))
            score_text = font.render(f"最终得分: {score}", True, TEXT_COLOR)
            high_score_text = font.render(f"最高分: {high_score}", True, YELLOW)
            restart_text = font.render("按 Alt 键重新开始", True, (150, 255, 150))
            
            # 如果创造了新纪录，显示特殊消息
            if new_high_score:
                new_record_text = font.render("新纪录!", True, (255, 215, 0))  # 金色
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
            control_text = font.render(f"控制方式: {'鼠标' if player.use_mouse_control else '键盘'}", True, CYAN)
            switch_text = font.render("按 Ctrl 键切换控制方式", True, CYAN)
            restart_text = font.render("按 Alt 键重新开始游戏", True, (150, 255, 150))
            
            screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
            screen.blit(control_text, (SCREEN_WIDTH//2 - control_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
            screen.blit(switch_text, (SCREEN_WIDTH//2 - switch_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 100))

            pygame.display.flip()
            clock.tick(60)
            continue
        
        # 更新玩家位置
        if player.use_mouse_control:
            # 使用鼠标控制
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player.move_with_mouse(mouse_x, mouse_y)
        else:
            # 使用键盘控制
            keys = pygame.key.get_pressed()
            player.move_with_keyboard(keys)
        
        # 更新玩家尾焰
        player.update_trail()
        
        # 更新护盾状态
        player.update_shield()
        
        # 新增：更新玩家受伤效果
        player.update_hit_effect()
        
        # 新增：更新得分飘字效果
        for popup in score_popups[:]:
            if popup.update():
                score_popups.remove(popup)
        
        # 根据分数调整炸弹生成频率
        base_spawn_time = calculate_bomb_spawn_time(score)
        
        # 同时存在的炸弹数量有上限
        max_bombs = min(15, 1 + int(score / 20))
        
        current_time = time.time()
        if current_time - last_bomb_spawn >= base_spawn_time and len(bombs) < max_bombs:
            bombs.append(Bomb(score, craters))
            last_bomb_spawn = current_time
        
        # 更新炸弹状态
        for bomb in bombs[:]:
            bomb.update()
            
            # 爆炸时销毁范围内的物品
            bomb.destroy_items_in_explosion(stars)
            bomb.destroy_items_in_explosion(hearts)
            bomb.destroy_items_in_explosion(shields)
            
            # 爆炸结束后创建弹坑（只有分数达到阈值才创建）
            if bomb.exploding and not bomb.active and score >= CRATER_SCORE_THRESHOLD:
                # 创建与爆炸形状和范围一致的弹坑
                crater_radius = int(bomb.expansion_speed * EXPLOSION_DURATION)  # 弹坑半径等于爆炸最大半径
                craters.append(Crater(bomb.x, bomb.y, crater_radius, bomb.explosion_shape))
                bombs.remove(bomb)
            elif bomb.exploding and not bomb.active:
                bombs.remove(bomb)
        
        # 更新弹坑状态
        for crater in craters[:]:
            crater.update()
            if not crater.active:
                craters.remove(crater)
        
        # 更新玩家速度（考虑弹坑影响）
        player.update_speed(craters)
        
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
                    # 新增：创建得分飘字效果
                    score_popup = ScorePopup(star.x, star.y, star.value, star.color)
                    score_popups.append(score_popup)
                    # 重新生成星星，确保不相交
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
                # 新增：触发玩家受伤效果
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
        
        # 绘制游戏界面
        screen.fill(BG_COLOR)
        draw_stars_bg()  # 绘制星空背景
        
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
        
        # 绘制玩家
        player.draw()
        
        # 新增：绘制得分飘字效果
        for popup in score_popups:
            popup.draw()
        
        # 显示UI - 完全去除背景，只显示文字（中文）
        score_text = font.render(f"得分: {score}", True, TEXT_COLOR)
        lives_text = font.render(f"生命: {lives}", True, GREEN)
        high_score_text = font.render(f"最高分: {high_score}", True, YELLOW)
        control_text = small_font.render(f"控制: {'鼠标' if player.use_mouse_control else '键盘'}", True, TEXT_COLOR)
        switch_text = small_font.render("按 Ctrl 键切换", True, TEXT_COLOR)
        
        # 直接绘制文字，没有背景
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, 10))
        screen.blit(control_text, (10, SCREEN_HEIGHT - 40))
        screen.blit(switch_text, (10, SCREEN_HEIGHT - 20))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()