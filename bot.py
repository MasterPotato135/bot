import pygame
import ctypes
from ctypes import wintypes
import subprocess
import os
import sys
import json
import tempfile
from pathlib import Path
from threading import Thread
import time

from move import Movement


SIZE = 128
SPEED = 2


pygame.init()

pygame.display.set_caption(
    "Flork Bot"
)

screen = pygame.display.set_mode(
    (SIZE, SIZE),
    pygame.NOFRAME
)

clock = pygame.time.Clock()


hwnd = pygame.display.get_wm_info()["window"]


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

GWL_EXSTYLE = -20

WS_EX_LAYERED = 0x00080000
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080

style = user32.GetWindowLongW(
    hwnd,
    GWL_EXSTYLE
)

style |= WS_EX_LAYERED
style |= WS_EX_APPWINDOW
style &= ~WS_EX_TOOLWINDOW

user32.SetWindowLongW(
    hwnd,
    GWL_EXSTYLE,
    style
)


# ==========================================
# CARREGAMENTO DE IMAGEM COM VALIDAÇÃO
# ==========================================

try:
    flork = pygame.image.load(
        "flork.png"
    ).convert_alpha()
except FileNotFoundError:
    print("❌ ERRO: Arquivo 'flork.png' não encontrado!")
    print("   Certifique-se de que 'flork.png' está no mesmo diretório de bot.py")
    pygame.quit()
    sys.exit(1)
except Exception as error:
    print(f"❌ ERRO ao carregar imagem: {error}")
    pygame.quit()
    sys.exit(1)

flork = pygame.transform.smoothscale(
    flork,
    (SIZE, SIZE)
)

flork_right = flork

flork_left = pygame.transform.flip(
    flork,
    True,
    False
)


class BITMAPINFOHEADER(
    ctypes.Structure
):

    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]


class BITMAPINFO(
    ctypes.Structure
):

    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3)
    ]


class POINT(
    ctypes.Structure
):

    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]


class SIZE_STRUCT(
    ctypes.Structure
):

    _fields_ = [
        ("cx", wintypes.LONG),
        ("cy", wintypes.LONG)
    ]


class BLENDFUNCTION(
    ctypes.Structure
):

    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte)
    ]


BI_RGB = 0
AC_SRC_OVER = 0
AC_SRC_ALPHA = 1


# Variáveis globais para o bitmap atual
current_bitmap_width = SIZE
current_bitmap_height = SIZE
bitmap_info = None
screen_dc = None
mem_dc = None
bits = None
bitmap = None


def create_bitmap(width, height):
    """
    Cria um novo bitmap de tamanho especificado
    """
    global bitmap_info, screen_dc, mem_dc, bits, bitmap, current_bitmap_width, current_bitmap_height
    
    # Limpa o bitmap antigo se existir
    if bitmap is not None:
        gdi32.DeleteObject(bitmap)
    if mem_dc is not None and screen_dc is not None:
        gdi32.DeleteDC(mem_dc)
    
    current_bitmap_width = width
    current_bitmap_height = height
    
    bitmap_info = BITMAPINFO()
    bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmap_info.bmiHeader.biWidth = width
    bitmap_info.bmiHeader.biHeight = -height
    bitmap_info.bmiHeader.biPlanes = 1
    bitmap_info.bmiHeader.biBitCount = 32
    bitmap_info.bmiHeader.biCompression = BI_RGB
    
    screen_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(screen_dc)
    
    bits = ctypes.c_void_p()
    bitmap = gdi32.CreateDIBSection(
        mem_dc,
        ctypes.byref(bitmap_info),
        0,
        ctypes.byref(bits),
        None,
        0
    )
    
    gdi32.SelectObject(mem_dc, bitmap)


# Cria o bitmap inicial
create_bitmap(SIZE, SIZE)


screen_dc = user32.GetDC(
    hwnd
)

mem_dc = gdi32.CreateCompatibleDC(
    screen_dc
)

bits = ctypes.c_void_p()

bitmap = gdi32.CreateDIBSection(
    mem_dc,
    ctypes.byref(bitmap_info),
    0,
    ctypes.byref(bits),
    None,
    0
)

gdi32.SelectObject(
    mem_dc,
    bitmap
)


def set_image(image, width=SIZE, height=SIZE):
    
    global current_bitmap_width, current_bitmap_height
    
    # Recria o bitmap se o tamanho mudou
    if width != current_bitmap_width or height != current_bitmap_height:
        create_bitmap(width, height)

    raw = pygame.image.tostring(
        image,
        "RGBA",
        False
    )

    pixel_count = width * height

    bgra = bytearray(
        pixel_count * 4
    )

    for i in range(pixel_count):

        r = raw[i * 4 + 0]
        g = raw[i * 4 + 1]
        b = raw[i * 4 + 2]
        a = raw[i * 4 + 3]

        r = (
            r * a
            + 127
        ) // 255

        g = (
            g * a
            + 127
        ) // 255

        b = (
            b * a
            + 127
        ) // 255

        bgra[i * 4 + 0] = b
        bgra[i * 4 + 1] = g
        bgra[i * 4 + 2] = r
        bgra[i * 4 + 3] = a

    ctypes.memmove(
        bits,
        bytes(bgra),
        len(bgra)
    )


def update_layered_window(x, y, image_width=SIZE, image_height=SIZE):

    pt_pos = POINT(
        int(x),
        int(y)
    )

    size = SIZE_STRUCT(
        image_width,
        image_height
    )

    source_pos = POINT(
        0,
        0
    )

    blend = BLENDFUNCTION(
        AC_SRC_OVER,
        0,
        255,
        AC_SRC_ALPHA
    )

    user32.UpdateLayeredWindow(
        hwnd,
        screen_dc,
        ctypes.byref(pt_pos),
        ctypes.byref(size),
        mem_dc,
        ctypes.byref(source_pos),
        0,
        ctypes.byref(blend),
        2
    )


display_info = pygame.display.Info()

movement = Movement(
    display_info.current_w,
    display_info.current_h,
    SIZE,
    SPEED
)


# ==========================================
# VARIÁVEIS DO BALÃO DE FALA
# ==========================================

speech_bubble_text = ""
speech_bubble_time = 0
SPEECH_BUBBLE_DURATION = 8000  # 8 segundos em ms


def set_speech_bubble(text, duration=SPEECH_BUBBLE_DURATION):
    """Define o texto do balão de fala"""
    global speech_bubble_text, speech_bubble_time
    speech_bubble_text = text
    speech_bubble_time = pygame.time.get_ticks() + duration


def check_for_new_messages():
    """
    Monitora o arquivo de mensagens do compilador
    Roda em thread separada para não travar o jogo
    """
    last_timestamp = 0
    
    while True:
        try:
            temp_dir = Path(tempfile.gettempdir())
            message_file = temp_dir / "flork_message.json"
            
            if message_file.exists():
                # Obtém o timestamp do arquivo
                current_timestamp = message_file.stat().st_mtime
                
                # Se o arquivo foi modificado recentemente
                if current_timestamp > last_timestamp:
                    last_timestamp = current_timestamp
                    
                    try:
                        with open(message_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            message = data.get("message", "")
                            
                            if message:
                                print(f"[FLORK] Mensagem recebida: {message}")
                                # Define a mensagem no balão de fala
                                set_speech_bubble(message, SPEECH_BUBBLE_DURATION)
                    except Exception as e:
                        print(f"[FLORK] Erro ao ler mensagem: {e}")
            
            time.sleep(0.5)  # Verifica a cada 500ms
            
        except Exception as e:
            print(f"[FLORK] Erro no monitor: {e}")
            time.sleep(1)  # Se houver erro, aguarda mais


# Inicia a thread de monitoramento de mensagens
message_thread = Thread(target=check_for_new_messages, daemon=True)
message_thread.start()


def create_image_with_bubble(image, text):
    """
    Cria uma nova imagem com o balão de fala desenhado à direita
    Retorna (imagem, largura, altura)
    """
    
    if not text:
        return (image, SIZE, SIZE)
    
    # Fonte MAIOR
    font = pygame.font.Font(None, 20)
    
    # Quebra o texto em linhas se for muito longo
    max_width = 180
    lines = []
    current_line = ""
    
    for word in text.split():
        test_line = current_line + word + " "
        text_width = font.size(test_line)[0]
        
        if text_width > max_width:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line = test_line
    
    if current_line:
        lines.append(current_line.strip())
    
    if not lines:
        return (image, SIZE, SIZE)
    
    # Calcula dimensões do balão
    max_line_width = max([font.size(line)[0] for line in lines])
    line_height = font.get_height()
    
    # Balão MAIOR
    bubble_width = min(max_line_width + 30, 280)
    bubble_height = len(lines) * line_height + 30
    
    # Cria uma canvas maior para acomodar personagem + balão
    canvas_width = SIZE + bubble_width + 20
    canvas_height = max(SIZE, bubble_height + 20)
    canvas = pygame.Surface((canvas_width, canvas_height), pygame.SRCALPHA)
    
    # Blita a imagem original à esquerda
    img_y = (canvas_height - SIZE) // 2
    canvas.blit(image, (0, img_y))
    
    # Posição do balão (à direita da imagem)
    bubble_x = SIZE + 10
    bubble_y = (canvas_height - bubble_height) // 2
    
    # Cria uma surface para o balão com alpha
    bubble_surface = pygame.Surface((bubble_width, bubble_height), pygame.SRCALPHA)
    
    # Desenha o fundo do balão (branco com borda preta)
    pygame.draw.rect(bubble_surface, (250, 250, 250, 255), (0, 0, bubble_width, bubble_height), border_radius=12)
    pygame.draw.rect(bubble_surface, (20, 20, 20, 255), (0, 0, bubble_width, bubble_height), 3, border_radius=12)
    
    # Desenha um pequeno triângulo apontando para o personagem (rabo)
    tail_points = [
        (0, bubble_height // 2 - 8),
        (0, bubble_height // 2 + 8),
        (-12, bubble_height // 2)
    ]
    pygame.draw.polygon(bubble_surface, (250, 250, 250, 255), tail_points)
    pygame.draw.polygon(bubble_surface, (20, 20, 20, 255), tail_points, 2)
    
    # Desenha o texto dentro do balão
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, (0, 0, 0))
        text_x = 15
        text_y = 15 + i * line_height
        bubble_surface.blit(text_surface, (text_x, text_y))
    
    # Blita o balão no canvas
    canvas.blit(bubble_surface, (bubble_x, bubble_y))
    
    print(f"[FLORK] Balão desenhado: {len(lines)} linhas, {bubble_width}x{bubble_height}, canvas: {canvas_width}x{canvas_height}")
    
    return (canvas, canvas_width, canvas_height)


set_image(
    flork_right
)

update_layered_window(
    movement.x,
    movement.y
)


def compile_project():

    msg_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "msg.py"
    )

    try:
        subprocess.Popen(
            [
                "cmd.exe",
                "/k",
                sys.executable,
                msg_path
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as error:
        print(f"❌ Erro ao abrir compilador: {error}")


def show_menu():

    menu = user32.CreatePopupMenu()

    MF_STRING = 0x00000000
    MF_SEPARATOR = 0x00000800

    user32.AppendMenuW(
        menu,
        MF_STRING,
        1,
        "Compilar"
    )

    user32.AppendMenuW(
        menu,
        MF_SEPARATOR,
        0,
        None
    )

    user32.AppendMenuW(
        menu,
        MF_STRING,
        2,
        "Sair"
    )

    point = POINT()

    user32.GetCursorPos(
        ctypes.byref(point)
    )

    command = user32.TrackPopupMenu(
        menu,
        0x0100,
        point.x,
        point.y,
        0,
        hwnd,
        None
    )

    user32.DestroyMenu(
        menu
    )

    if command == 1:

        compile_project()

    elif command == 2:

        pygame.quit()

        os._exit(0)


running = True


while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                movement.start_drag()

            elif event.button == 3:

                show_menu()


        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:

                movement.stop_drag()


    if movement.dragging:

        movement.drag()

    else:

        movement.walk()


    if movement.facing_left:

        current_image = flork_left

    else:

        current_image = flork_right


    # Verifica se o balão de fala expirou
    current_time = pygame.time.get_ticks()
    if current_time > speech_bubble_time:
        speech_bubble_text = ""

    # Cria a imagem com o balão se houver texto
    if speech_bubble_text:
        final_image, img_width, img_height = create_image_with_bubble(current_image, speech_bubble_text)
    else:
        final_image = current_image
        img_width = SIZE
        img_height = SIZE

    set_image(final_image, img_width, img_height)

    update_layered_window(
        movement.x,
        movement.y,
        img_width,
        img_height
    )


    pygame.time.delay(
        10
    )


gdi32.DeleteObject(
    bitmap
)

gdi32.DeleteDC(
    mem_dc
)

user32.ReleaseDC(
    hwnd,
    screen_dc
)

pygame.quit()