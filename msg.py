import subprocess
import random
import re
import os
import json
import tempfile
from pathlib import Path


SUCCESS_MESSAGES = [
    "Mestre, compilou. Eu não estava preparado para isso.",
    "Mestre, deu certo. Vou fingir que sempre confiei em você.",
    "Compilou sem erro. Anotem a data.",
    "Mestre... funcionou. Estou começando a acreditar em milagres.",
    "Sem erros. Eu estou genuinamente assustado.",
]


WARNING_MESSAGES = [
    "Mestre, compilou... mas o compilador está desconfiado.",
    "Mestre, tecnicamente funcionou. Eu não faria isso de novo.",
    "Só uns warnings. Nada que possa destruir sua autoestima.",
    "O código compilou, mas algumas linhas estão pedindo socorro.",
    "Compilou. O compilador viu os warnings e decidiu não se envolver.",
]


LOW_ERROR_MESSAGES = [
    "Mestre, me desculpe pelo erro. Foi só um pequeno acidente.",
    "Mestre, desculpa. O C++ decidiu complicar uma coisa simples.",
    "Perdão, mestre. Tem um errinho aí.",
    "Mestre, acho que o código não gostou muito dessa parte.",
    "Desculpa pelo erro, mestre. Podemos fingir que isso nunca aconteceu?",
]


MEDIUM_ERROR_MESSAGES = [
    "Mestre, me desculpe pelo erro. Mas acho que você esqueceu como C++ funciona.",
    "Mestre, desculpa, mas o compilador está começando a perder a paciência.",
    "Tem alguns problemas aí, mestre. Eu não sei se devo corrigir ou chamar ajuda.",
    "Mestre... são vários erros. Talvez seja melhor começar de novo.",
    "Eu encontrei alguns erros. O problema é que eles encontraram você primeiro.",
]


HIGH_ERROR_MESSAGES = [
    "Mestre, desculpa te acordar, porque você aparentemente dormiu no teclado.",
    "Mestre, eu respeito muito você. Mas esse código está testando os limites dessa relação.",
    "Mestre, me desculpe pelo erro, mas tu não sabe nem português, imagine C++.",
    "Mestre, encontrei tantos erros que comecei a contar e esqueci onde estava.",
    "Mestre, o compilador pediu para eu parar de olhar esse código.",
    "Isso não é mais um programa. É um pedido de socorro em C++.",
    "Mestre, o código compilou na minha cabeça. Infelizmente a realidade discorda.",
]


ABSURD_ERROR_MESSAGES = [
    "Mestre, eu tentei entender o código. Agora preciso de férias.",
    "Mestre, o compilador viu isso e considerou trocar de profissão.",
    "Mestre, isso não é um erro de compilação. É uma ameaça.",
    "Mestre, encontrei tantos erros que o g++ pediu reforços.",
    "Mestre, acho que você acabou de inventar uma nova linguagem de programação.",
    "Mestre, eu abriria um chamado no suporte, mas acho que o suporte abriria um chamado contra você.",
    "Mestre, esse código está tão errado que o compilador está questionando as próprias leis da física.",
    "Mestre, eu poderia explicar o erro, mas nem eu quero ser responsabilizado por isso.",
    "Mestre... sinceramente? Apaga tudo e vamos tomar um café.",
    "Mestre, o compilador não recusou seu código. Ele recusou a realidade.",
]


GXX_NOT_FOUND_MESSAGES = [
    "Mestre, eu não encontrei o g++. Você instalou o compilador ou só acreditou que ele existia?",
    "Mestre, o g++ não está no PATH. Até o compilador desistiu de participar.",
    "Mestre, cadê o MinGW? Eu não consigo compilar com força de vontade.",
]


FILE_NOT_FOUND_MESSAGES = [
    "Mestre, tu mandou compilar um arquivo que nem existe. Quer que eu invente o main.cpp também?",
    "Mestre, desculpa, mas cadê o arquivo? Eu procurei até onde não devia.",
    "Mestre, o g++ não encontrou esse arquivo. Você criou o código ou só imaginou ele?",
    "Mestre, você pediu para compilar um arquivo e ele respondeu: 'quem?'",
    "Mestre, o arquivo não existe. Nem o compilador conseguiu encontrar sua imaginação.",
    "Mestre, parabéns. Você conseguiu compilar um arquivo inexistente.",
    "Mestre, eu procurei o arquivo. Depois procurei de novo. Depois aceitei que você esqueceu de criar.",
    "Mestre, não tem esse arquivo aqui. Talvez ele esteja no mesmo lugar que sua memória.",
]


def count_errors(output):

    patterns = [
        r"error:",
        r"fatal error:",
        r"undefined reference",
        r"collect2:",
        r"ld returned",
    ]

    count = 0

    for pattern in patterns:

        count += len(
            re.findall(
                pattern,
                output,
                re.IGNORECASE
            )
        )

    return count


def count_warnings(output):

    return len(
        re.findall(
            r"warning:",
            output,
            re.IGNORECASE
        )
    )


def choose_message(
    output,
    return_code
):

    lower_output = output.lower()


    if (
        "not recognized"
        in lower_output
        or
        "is not recognized as an internal"
        in lower_output
    ):

        return random.choice(
            GXX_NOT_FOUND_MESSAGES
        )


    if (
        "no such file or directory"
        in lower_output
        or
        "cannot open input file"
        in lower_output
        or
        "fatal error: no input files"
        in lower_output
    ):

        return random.choice(
            FILE_NOT_FOUND_MESSAGES
        )


    errors = count_errors(
        output
    )

    warnings = count_warnings(
        output
    )


    if return_code == 0:

        if warnings > 0:

            return random.choice(
                WARNING_MESSAGES
            )

        return random.choice(
            SUCCESS_MESSAGES
        )


    if errors <= 1:

        return random.choice(
            LOW_ERROR_MESSAGES
        )


    if errors <= 3:

        return random.choice(
            MEDIUM_ERROR_MESSAGES
        )


    if errors <= 7:

        return random.choice(
            HIGH_ERROR_MESSAGES
        )


    return random.choice(
        ABSURD_ERROR_MESSAGES
    )


def minimize_console():
    """
    Minimiza a janela do console/terminal
    """
    try:
        import ctypes
        
        # Constantes
        SW_MINIMIZE = 6
        
        # Obtém o handle da janela do console atual
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        hwnd = kernel32.GetConsoleWindow()
        
        if hwnd:
            # Minimiza a janela
            user32.ShowWindow(hwnd, SW_MINIMIZE)
    except Exception as e:
        pass  # Falha silenciosa se não conseguir minimizar


def send_message_to_bot(message):
    """
    Envia uma mensagem para o bot exibir no balão de fala
    """
    try:
        # Cria um arquivo temporário com a mensagem
        temp_dir = Path(tempfile.gettempdir())
        message_file = temp_dir / "flork_message.json"
        
        with open(message_file, "w", encoding="utf-8") as f:
            json.dump({"message": message, "timestamp": str(Path.cwd())}, f, ensure_ascii=False)
    except Exception as e:
        pass  # Falha silenciosa


def validate_command(command):
    """
    Validação básica do comando (bem permissiva)
    """
    
    parts = command.split()
    
    if not parts:
        return False, "Comando vazio"
    
    # Aceita comandos de compiladores conhecidos
    compiler = parts[0].lower()
    if compiler not in ["g++", "gcc", "clang", "clang++", "cl.exe", "cc"]:
        return False, "Comando não parece ser um compilador"
    
    return True, ""


def compile_code(command):

    print()
    print("========================================")
    print("              COMPILANDO")
    print("========================================")
    print()

    # Validação do comando
    is_valid, error_msg = validate_command(command)
    
    if not is_valid:
        print()
        print("❌ VALIDAÇÃO FALHOU:")
        print(error_msg)
        print()
        return

    print(
        ">",
        command
    )

    print()

    try:

        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    except Exception as error:

        print()
        print("========================================")
        print("              ERRO DO PYTHON")
        print("========================================")
        print()

        print(
            "Mestre, o problema aconteceu antes mesmo"
        )

        print(
            "do compilador conseguir trabalhar."
        )

        print()

        print(
            "Tipo do erro:"
        )

        print(
            type(error).__name__
        )

        print()

        print(
            "Detalhes:"
        )

        print(
            error
        )

        print()

        print("========================================")
        print()

        return


    stdout = result.stdout or ""
    stderr = result.stderr or ""

    output = (
        stdout
        + stderr
    )


    if stdout.strip():

        print(stdout)


    if stderr.strip():

        print(stderr)


    print()
    print(
        "Código de retorno:",
        result.returncode
    )


    message = choose_message(
        output,
        result.returncode
    )

    # Envia a mensagem para o bot
    send_message_to_bot(message)

    print()
    print("----------------------------------------")
    print("🤖 FLORK:")
    print()
    print(message)
    print("----------------------------------------")
    print()
    
    # Minimiza o console se houve erro
    if result.returncode != 0:
        import time
        time.sleep(1)  # Aguarda 1 segundo para o bot receber a mensagem
        minimize_console()


if __name__ == "__main__":

    print("========================================")
    print("             FLORK COMPILER")
    print("========================================")
    print()

    print(
        "Digite o comando do MinGW64."
    )

    print()

    print("Exemplo:")
    print(
        "g++ main.cpp -o main"
    )

    print()

    print(
        "Digite 'sair' para fechar."
    )

    print()


    while True:

        try:

            command = input(
                "Mestre > "
            ).strip()

        except KeyboardInterrupt:

            print()

            print(
                "Mestre, tudo bem. Pode ir."
            )

            break

        except EOFError:

            break


        if not command:

            continue


        if command.lower() in (
            "sair",
            "exit",
            "quit"
        ):

            print()

            print(
                "Até depois, mestre."
            )

            break


        compile_code(
            command
        )