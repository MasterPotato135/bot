import random
import math
import ctypes
from ctypes import wintypes
import pygame


class Movement:

    def __init__(
        self,
        screen_width,
        screen_height,
        size,
        speed
    ):

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = size
        self.speed = speed

        self.x = (
            screen_width - size
        ) / 2

        self.y = (
            screen_height - size
        ) / 2

        self.angle = random.uniform(
            0,
            math.tau
        )

        self.next_change = (
            pygame.time.get_ticks()
            + random.randint(1000, 3000)
        )

        self.dragging = False

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.facing_left = False

        self.user32 = ctypes.windll.user32

        self.monitor_left = 0
        self.monitor_top = 0
        self.monitor_right = screen_width
        self.monitor_bottom = screen_height

        self.update_monitor()


    def get_mouse_position(self):

        point = wintypes.POINT()

        try:
            self.user32.GetCursorPos(
                ctypes.byref(point)
            )
        except Exception as error:
            print(f"Aviso: Erro ao obter posição do mouse: {error}")
            return 0, 0

        return point.x, point.y


    def get_monitor_from_point(self, x, y):

        MONITOR_DEFAULTTONEAREST = 2

        point = wintypes.POINT(
            int(x),
            int(y)
        )

        try:
            monitor = self.user32.MonitorFromPoint(
                point,
                MONITOR_DEFAULTTONEAREST
            )

            if not monitor:
                return None

            class MONITORINFO(ctypes.Structure):

                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD)
                ]

            info = MONITORINFO()

            info.cbSize = ctypes.sizeof(
                MONITORINFO
            )

            self.user32.GetMonitorInfoW(
                monitor,
                ctypes.byref(info)
            )

            return (
                info.rcMonitor.left,
                info.rcMonitor.top,
                info.rcMonitor.right,
                info.rcMonitor.bottom
            )

        except Exception as error:
            print(f"Aviso: Erro ao obter informações do monitor: {error}")
            return None


    def update_monitor(self):

        center_x = (
            self.x
            + self.size / 2
        )

        center_y = (
            self.y
            + self.size / 2
        )

        monitor = self.get_monitor_from_point(
            center_x,
            center_y
        )

        if monitor is None:
            return

        (
            self.monitor_left,
            self.monitor_top,
            self.monitor_right,
            self.monitor_bottom
        ) = monitor


    def start_drag(self):

        self.dragging = True

        mouse_x, mouse_y = (
            self.get_mouse_position()
        )

        self.drag_offset_x = (
            mouse_x - self.x
        )

        self.drag_offset_y = (
            mouse_y - self.y
        )


    def stop_drag(self):

        self.dragging = False

        self.update_monitor()

        max_x = (
            self.monitor_right
            - self.size
        )

        max_y = (
            self.monitor_bottom
            - self.size
        )

        if self.x < self.monitor_left:
            self.x = self.monitor_left

        if self.y < self.monitor_top:
            self.y = self.monitor_top

        if self.x > max_x:
            self.x = max_x

        if self.y > max_y:
            self.y = max_y


    def drag(self):

        mouse_x, mouse_y = (
            self.get_mouse_position()
        )

        self.x = (
            mouse_x
            - self.drag_offset_x
        )

        self.y = (
            mouse_y
            - self.drag_offset_y
        )


    def walk(self):

        now = pygame.time.get_ticks()

        if now >= self.next_change:

            self.angle = random.uniform(
                0,
                math.tau
            )

            self.next_change = (
                now
                + random.randint(1000, 3000)
            )

        dx = math.cos(
            self.angle
        )

        dy = math.sin(
            self.angle
        )

        self.x += (
            dx * self.speed
        )

        self.y += (
            dy * self.speed
        )


        # ==========================================
        # DIREÇÃO
        # ==========================================

        if dx < 0:

            self.facing_left = True

        elif dx > 0:

            self.facing_left = False


        # ==========================================
        # LIMITES
        # ==========================================

        left = self.monitor_left
        top = self.monitor_top

        right = (
            self.monitor_right
            - self.size
        )

        bottom = (
            self.monitor_bottom
            - self.size
        )


        if self.x <= left:

            self.x = left

            self.angle = random.uniform(
                -math.pi / 2,
                math.pi / 2
            )

            self.facing_left = False


        elif self.x >= right:

            self.x = right

            self.angle = random.uniform(
                math.pi / 2,
                3 * math.pi / 2
            )

            self.facing_left = True


        if self.y <= top:

            self.y = top

            self.angle = random.uniform(
                0,
                math.pi
            )


        elif self.y >= bottom:

            self.y = bottom

            self.angle = random.uniform(
                math.pi,
                math.tau
            )