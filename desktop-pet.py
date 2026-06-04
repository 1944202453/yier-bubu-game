"""
一二布布 桌面宠物
- 一二在桌面上走动
- 布布偶尔出现
- 可拖拽移动、双击切换角色
- 托盘图标右键退出
"""
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import random
import time
import threading
import os
import sys

# ═══════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CHARACTERS = {
    '一二': {
        'gifs': ['一二1.gif', '一二二.gif'],
        'size': (100, 110),
        'speed': (1, 3),
    },
    '布布': {
        'gifs': ['布布1.gif', '布布2.gif'],
        'size': (100, 110),
        'speed': (0.8, 2.5),
    }
}

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('一二布布桌宠')

        # Window setup
        self.root.overrideredirect(True)  # No titlebar
        self.root.wm_attributes('-topmost', True)  # Always on top

        # Use chroma key transparency
        self.transparent_color = '#010101'
        self.root.config(bg=self.transparent_color)
        self.root.wm_attributes('-transparentcolor', self.transparent_color)

        # Initial position
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = random.randint(100, self.screen_w - 200)
        self.y = random.randint(100, self.screen_h - 300)

        # Character state
        self.current_char = '一二'
        self.char_size = CHARACTERS[self.current_char]['size']
        self.root.geometry(f'{self.char_size[0]}x{self.char_size[1]}+{self.x}+{self.y}')

        # Load GIF frames
        self.frames = {}  # char_name -> [PhotoImage, ...]
        self.load_all_frames()

        # Animation state
        self.current_frame = 0
        self.frame_delay = 120  # ms between frames
        self.facing_right = True
        self.animating = True

        # Movement
        self.vel_x = random.choice([-1, 1]) * random.uniform(1, 2.5)
        self.vel_y = 0
        self.walking = True
        self.walk_timer = 0
        self.walk_direction_change = random.randint(50, 150)

        # Drag state
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.was_moved = False  # distinguish click from drag

        # Create label for the pet
        self.label = tk.Label(
            self.root, bg=self.transparent_color,
            borderwidth=0, highlightthickness=0
        )
        self.label.pack()

        # Bind events
        self.label.bind('<Button-1>', self.on_mouse_down)
        self.label.bind('<B1-Motion>', self.on_mouse_drag)
        self.label.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.label.bind('<Double-Button-1>', self.on_double_click)
        self.label.bind('<Button-3>', self.on_right_click)  # Right click

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label='🔄 切换角色 (一二 ↔ 布布)', command=self.switch_character)
        self.menu.add_command(label='🏃 速度: 普通', command=self.toggle_speed)
        self.menu.add_separator()
        self.menu.add_command(label='🚪 退出桌宠', command=self.quit_pet)

        self.speed_level = 1  # 0=slow, 1=normal, 2=fast

        # Start loops
        self.animate()
        self.walk_loop()

    def load_all_frames(self):
        """Load all GIF frames for all characters."""
        for char_name, char_data in CHARACTERS.items():
            all_frames = []
            for gif_name in char_data['gifs']:
                gif_path = os.path.join(SCRIPT_DIR, gif_name)
                if not os.path.exists(gif_path):
                    print(f'Warning: {gif_path} not found')
                    continue
                img = Image.open(gif_path)
                target_w, target_h = char_data['size']
                for frame in ImageSequence.Iterator(img):
                    frame = frame.convert('RGBA')
                    # Resize maintaining aspect ratio
                    frame.thumbnail((target_w, target_h), Image.LANCZOS)
                    # Create new image with padding to center
                    new_frame = Image.new('RGBA', (target_w, target_h), (1, 1, 1, 0))
                    offset_x = (target_w - frame.width) // 2
                    offset_y = (target_h - frame.height) // 2
                    new_frame.paste(frame, (offset_x, offset_y), frame)
                    # Convert to tkinter format
                    photo = ImageTk.PhotoImage(new_frame)
                    all_frames.append(photo)
            if all_frames:
                self.frames[char_name] = all_frames
                print(f'Loaded {len(all_frames)} frames for {char_name}')
            else:
                print(f'Warning: No frames loaded for {char_name}')

    def switch_character(self):
        """Toggle between 一二 and 布布."""
        if self.current_char == '一二':
            self.current_char = '布布'
        else:
            self.current_char = '一二'
        self.current_frame = 0
        self.char_size = CHARACTERS[self.current_char]['size']
        self.root.geometry(f'{self.char_size[0]}x{self.char_size[1]}+{self.x}+{self.y}')
        print(f'Switched to {self.current_char}')

    def toggle_speed(self):
        """Cycle through speed levels."""
        self.speed_level = (self.speed_level + 1) % 3
        labels = {0: '🏃 速度: 慢速', 1: '🏃 速度: 普通', 2: '🏃 速度: 快速'}
        self.menu.entryconfigure(1, label=labels[self.speed_level])

    def animate(self):
        """Cycle through GIF frames."""
        if not self.animating:
            return
        frames = self.frames.get(self.current_char, [])
        if frames:
            self.current_frame = (self.current_frame + 1) % len(frames)
            photo = frames[self.current_frame]

            # Flip if facing left
            if not self.facing_right:
                # Create mirrored version
                pil_img = ImageTk.getimage(photo)
                mirrored = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                photo = ImageTk.PhotoImage(mirrored)

            self.label.config(image=photo)
            self.label.image = photo  # Keep reference

        delay = self.frame_delay
        if self.speed_level == 0:
            delay = int(delay * 1.5)
        elif self.speed_level == 2:
            delay = int(delay * 0.6)

        self.root.after(delay, self.animate)

    def walk_loop(self):
        """Autonomous walking behavior."""
        if self.walking and not self.dragging:
            self.walk_timer += 1

            # Change direction periodically
            if self.walk_timer >= self.walk_direction_change:
                self.walk_timer = 0
                self.walk_direction_change = random.randint(40, 180)
                # Sometimes stop briefly
                if random.random() < 0.15:
                    self.vel_x = 0
                    self.root.after(800, self.resume_walking)
                else:
                    speed_range = CHARACTERS[self.current_char]['speed']
                    base_speed = random.uniform(*speed_range)
                    if self.speed_level == 0:
                        base_speed *= 0.5
                    elif self.speed_level == 2:
                        base_speed *= 1.8
                    self.vel_x = random.choice([-1, 1]) * base_speed
                    self.vel_y = random.choice([-1, 0, 0, 1]) * random.uniform(0, 1)

            # Update position
            self.x += int(self.vel_x)
            self.y += int(self.vel_y)

            # Face direction
            if self.vel_x > 0.3:
                self.facing_right = True
            elif self.vel_x < -0.3:
                self.facing_right = False

            # Screen boundary bounce
            margin = 20
            if self.x < -margin:
                self.x = -margin
                self.vel_x = abs(self.vel_x)
            if self.x > self.screen_w - self.char_size[0] + margin:
                self.x = self.screen_w - self.char_size[0] + margin
                self.vel_x = -abs(self.vel_x)
            if self.y < -margin:
                self.y = -margin
                self.vel_y = abs(self.vel_y)
            if self.y > self.screen_h - self.char_size[1] + margin:
                self.y = self.screen_h - self.char_size[1] + margin
                self.vel_y = -abs(self.vel_y)

            # Occasional vertical drift down (gravity feel)
            if random.random() < 0.02 and self.y < self.screen_h * 0.8:
                self.vel_y += 0.5

            # Update window position
            self.root.geometry(f'{self.char_size[0]}x{self.char_size[1]}+{self.x}+{self.y}')

        self.root.after(30, self.walk_loop)

    def resume_walking(self):
        speed_range = CHARACTERS[self.current_char]['speed']
        self.vel_x = random.choice([-1, 1]) * random.uniform(*speed_range)

    # ── Mouse events ──
    def on_mouse_down(self, event):
        self.dragging = True
        self.was_moved = False
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.vel_x = 0
        self.vel_y = 0

    def on_mouse_drag(self, event):
        if self.dragging:
            dx = event.x - self.drag_offset_x
            dy = event.y - self.drag_offset_y
            if abs(dx) > 3 or abs(dy) > 3:
                self.was_moved = True
            self.x = self.root.winfo_x() + dx
            self.y = self.root.winfo_y() + dy
            self.root.geometry(f'{self.char_size[0]}x{self.char_size[1]}+{self.x}+{self.y}')

    def on_mouse_up(self, event):
        self.dragging = False
        if not self.was_moved:
            # It was a click (not drag) - do a little jump
            self.do_jump()

    def on_double_click(self, event):
        self.dragging = False
        self.switch_character()

    def on_right_click(self, event):
        self.dragging = False
        self.vel_x = 0
        self.vel_y = 0
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def do_jump(self):
        """Little jump animation on click."""
        orig_y = self.y
        jump_height = 30
        steps = 8

        def animate_jump(step):
            if step < steps // 2:
                # Going up
                self.y = orig_y - int(jump_height * (step / (steps // 2)))
            else:
                # Coming down
                progress = (step - steps // 2) / (steps // 2)
                self.y = orig_y - int(jump_height * (1 - progress))

            self.root.geometry(f'{self.char_size[0]}x{self.char_size[1]}+{self.x}+{self.y}')

            if step < steps:
                self.root.after(25, lambda: animate_jump(step + 1))
            else:
                self.resume_walking()

        animate_jump(0)

    def quit_pet(self):
        self.animating = False
        self.walking = False
        self.root.destroy()
        sys.exit(0)

    def run(self):
        print(f'一二布布桌宠已启动! 当前角色: {self.current_char}')
        print('  - 拖拽移动 | 双击切换角色 | 右键菜单')
        self.root.mainloop()


if __name__ == '__main__':
    pet = DesktopPet()
    pet.run()
