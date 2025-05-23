import os
print("pysh: Imported `os'")
import sys
print("pysh: Imported `sys'")
import re
print("pysh: Imported `re'")
import socket
print("pysh: Imported `socket'")
import json
print("pysh: Imported `json'")
import time
print("pysh: Imported `time'")
import getpass
print("pysh: Imported `getpass'")
from prompt_toolkit import PromptSession
print("pysh: Imported `PromptSession' from `prompt_toolkit'")
from prompt_toolkit.key_binding import KeyBindings
print("pysh: Imported `KeyBindings' from `prompt_toolkit.key_binding'")
from prompt_toolkit.completion import Completer, Completion
print("pysh: Imported `Completer' from `prompt_toolkit.completion'")
print("pysh: Imported `Completion' from `prompt_toolkit.completion'")

VERSION = "1.3.0"
PY_VER = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
print("pysh: Internal variables set")

if len(sys.argv) > 1:
    if sys.argv[1] == "--version":
        print("\u001b[12A\u001b[0J", end="")
        print(f"pysh, version {VERSION}(1)-release (python-{PY_VER})")
        sys.exit(0)
    elif sys.argv[1] == "--help":
        print("\u001b[12A\u001b[0J", end="")
        print(f"""Usage: pysh [OPTION]
Options:
  --login    Launch pysh as a login shell
  --help     Display this help and exit
  --version  Output version information and exit""")
        sys.exit(0)
    elif sys.argv[1] == "--login":
        pass
    else:
        print(f"pysh: unrecognized option '{sys.argv[1]}'")
        print("Try '--help' for more information.")
        sys.exit(1)

with open("users.json", "r") as f:
    users: dict = json.load(f)

print("pysh: Loaded users")

# class PathCompleter(Completer):
#     def get_completions(self, document, complete_event):
#         text = document.text_before_cursor
#         if text.startswith("cd "):
#             path = text[3:]
#             if not path:
#                 path = "."
#             try:
#                 for item in os.listdir(path):
#                     full_path = os.path.join(path, item)
#                     if os.path.isdir(full_path):
#                         yield Completion(item, start_position=-len(path))
#             except FileNotFoundError:
#                 pass

class BashLikePathCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        cmds = ["cd ", "cat ", "rm ", "mkdir ", "rmdir "]
        if any(text.startswith(cmd) for cmd in cmds):
            for cmd in cmds:
                if text.startswith(cmd):
                    path = text[len(cmd):]
            if not path:
                path = "."
            else:
                path = os.path.expanduser(path)

            dir_to_list = os.path.dirname(path) if os.path.dirname(path) else "."
            partial_input = os.path.basename(path)

            try:
                for item in os.listdir(dir_to_list):
                    if item.startswith(partial_input):
                        full_path = os.path.join(dir_to_list, item)
                        if os.path.isdir(full_path):
                            yield Completion(
                                item + "/",
                                start_position=-len(partial_input),
                            )
                        else:
                            yield Completion(
                                item,
                                start_position=-len(partial_input),
                            )
            except FileNotFoundError:
                pass
            except NotADirectoryError:
                pass

session = PromptSession(completer=BashLikePathCompleter())
bindings = KeyBindings()

def get_distro_info():
    with open("/etc/os-release") as f:
        lines = f.readlines()
    info = {}
    for line in lines:
        key, value = line.strip().split("=", 1)
        info[key] = value.strip('"')
    return info.get("NAME", "Linux")

os_name = get_distro_info()
os_version = os.uname().release

# @bindings.add("c-c")
# def _(event):
#     pass

def expand_variables(text):
    pattern = r'\${([a-zA-Z0-9_]+)}'
    while re.search(pattern, text):
        match = re.search(pattern, text)
        var_name = match.group(1)
        var_value = globals().get(f'bashvar_{var_name}', os.environ.get(var_name, ''))
        text = text[:match.start()] + var_value + text[match.end():]

    pattern = r'\$([a-zA-Z0-9_]+)'
    while re.search(pattern, text):
        match = re.search(pattern, text)
        var_name = match.group(1)
        var_value = globals().get(f'bashvar_{var_name}', os.environ.get(var_name, ''))
        text = text[:match.start()] + var_value + text[match.end():]

    return text

print("pysh: Optional settings and features loaded")

if len(sys.argv) > 1 and sys.argv[1] == "--login":
    print("pysh: All started correctly.  Launching login shell...")
    time.sleep(0.05)
    print("\u001b[10000A\u001b[2J", end="")
    time.sleep(0.2)
    login = ""
    print(f"\n{os_name} {os_version} (pytty)\n")
    is_logged_in = False
    while is_logged_in == False:
        try:
            while login == "":
                print(f"{socket.gethostname()} login: ", end="")
                login = input()
            password = getpass.getpass()
            for user, user_password in users.items():
                if login == user and password == user_password:
                    if login == "root":
                        print("Please provide your password to continue.")
                        os.execvp("sudo", ["sudo", "python", sys.argv[0]])
                    is_logged_in = True
                    break
            else:
                time.sleep(2)
                print("Login incorrect\n")
                login = ""
        except KeyboardInterrupt:
            exit(1)
else:
    login = os.getlogin()
    print("pysh: All started correctly.  Launching shell...")
    time.sleep(0.05)
    print("\u001b[15A", end="")

while True:
    try:
        if os.geteuid() == 0:
            user_input: str = session.prompt(
                f"[root@{socket.gethostname()} {('~' if os.getcwd() == os.environ["HOME"] else '') or os.path.basename(os.getcwd()) or '/'}]# ",
                key_bindings=bindings,
            ).strip()
        else:
            user_input: str = session.prompt(
                f"[{login}@{socket.gethostname()} {('~' if os.getcwd() == os.environ["HOME"] else '') or os.path.basename(os.getcwd()) or '/'}]$ ",
                key_bindings=bindings,
            ).strip()
        for input_command in user_input.split(";"):
            user_input = input_command
            user_input = expand_variables(user_input.strip())
            if user_input == "":
                continue
            elif user_input.strip().find(" > ") > 0:
                command, output_file = user_input.split(" > ", 1)
                try:
                    with open(output_file.strip(), "w") as f:
                        if command.startswith("echo "):
                            echo = command.split(" ", 1)[1]
                            f.write(echo + "\n")
                        elif command.startswith("cat "):
                            filename = command.split(" ", 1)[1]
                            with open(filename, "r") as infile:
                                f.write(infile.read())
                        else:
                            print(f"pysh: {command.split()[0]}: command not found")
                except Exception as e:
                    print(f"pysh: {e}")
            elif re.search(r'[a-zA-Z0-9_]+=.*', user_input):
                var_name, var_value = user_input.split('=', 1)
                globals()[f'bashvar_{var_name}'] = var_value
            elif user_input == "help" or user_input.startswith("help "):
                print(f"""pysh, version {VERSION}(1)-release (python-{PY_VER})
These shell commands are defined internally.  Type `help' to see this list.

 cat [file | -]
 cd [dir]
 command command [arg ...]
 echo [arg ...]
 exit [n]
 false
 help
 la [dir]
 ls [dir]
 mkdir dir
 rm file
 rmdir dir
 sleep n
 touch file
 true
 variables - Names and meanings of some shell variables
 whoami""")
            elif user_input == "exit" or user_input.startswith("exit "):
                if user_input.startswith("exit "):
                    exit(int(user_input.split()[1]))
                else:
                    exit(0)
            elif user_input == "cd" or user_input.startswith("cd "):
                if user_input.startswith("cd "):
                    try:
                        new_dir = user_input.split(" ", 1)[1]
                        new_dir = new_dir.replace("~", os.environ["HOME"])
                        os.chdir(new_dir)
                    except FileNotFoundError:
                        print(f"pysh: cd: {new_dir}: No such file or directory")
                    except Exception as e:
                        print(f"pysh: cd: {e}")
                else:
                    os.chdir(os.path.expanduser("~"))
            elif user_input == "ls" or user_input.startswith("ls "):
                if user_input.startswith("ls "):
                    try:
                        path = user_input.split(" ", 1)[1]
                        for item in os.listdir(path):
                            if not item.startswith("."):
                                print(item)
                    except FileNotFoundError:
                        print(f"pysh: ls: cannot access '{path}': No such file or directory")
                    except NotADirectoryError:
                        print(f"pysh: ls: cannot access '{path}': Not a directory")
                    except Exception as e:
                        print(f"pysh: ls: {e}")
                else:
                    try:
                        for item in os.listdir(os.getcwd()):
                            if not item.startswith("."):
                                print(item)
                    except Exception as e:
                        print(f"pysh: ls: {e}")
            elif user_input == "la" or user_input.startswith("la "):
                if user_input.startswith("la "):
                    try:
                        path = user_input.split(" ", 1)[1]
                        for item in os.listdir(path):
                            print(item)
                    except FileNotFoundError:
                        print(f"pysh: la: cannot access '{path}': No such file or directory")
                    except NotADirectoryError:
                        print(f"pysh: la: cannot access '{path}': Not a directory")
                    except Exception as e:
                        print(f"pysh: la: {e}")
                else:
                    try:
                        for item in os.listdir(os.getcwd()):
                            print(item)
                    except Exception as e:
                        print(f"pysh: la: {e}")
            elif user_input == "echo" or user_input.startswith("echo "):
                if user_input.startswith("echo "):
                    echo = user_input.split(" ", 1)[1]
                    print(echo)
                else:
                    print()
            elif user_input == "true" or user_input.startswith("true ") or user_input == "false" or user_input.startswith("false "):
                continue
            elif user_input == "whoami" or user_input.startswith("whoami "):
                if os.geteuid() == 0:
                    print("root")
                else:
                    print(os.getlogin())
            elif user_input == "sleep" or user_input.startswith("sleep "):
                if user_input.startswith("sleep "):
                    sleep_time = user_input.split(" ", 1)[1]
                    time.sleep(int(sleep_time))
                else:
                    print("""sleep: missing operand
Try 'sleep n'.""")
            elif user_input == "touch" or user_input.startswith("touch "):
                if user_input.startswith("touch "):
                    new_file = user_input.split(" ", 1)[1]
                    try:
                        with open(new_file, "w") as f:
                            pass
                    except Exception as e:
                        print(f"pysh: touch: {e}")
                else:
                    print("""pysh: touch: missing file operand
Try 'touch file'.""")
            elif user_input == "cat" or user_input.startswith("cat "):
                filename = user_input.split(" ", 1)[1] if user_input.startswith("cat ") else None
                if filename == "-" or user_input.strip() == "cat":
                    while True:
                        print(input())
                else:
                    with open(filename, "r") as f:
                        print(f.read(), end="")
            elif user_input == "rm" or user_input.startswith("rm "):
                if user_input.startswith("rm "):
                    target = user_input.split(" ", 1)[1]
                    try:
                        if os.path.isdir(target):
                            print(f"pysh: rm: cannot remove '{target}': Is a directory")
                        else:
                            os.remove(target)
                    except FileNotFoundError:
                        print(f"pysh: rm: cannot remove '{target}': No such file or directory")
                    except Exception as e:
                        print(f"pysh: rm: {e}")
                else:
                    print("""pysh: rm: missing operand
Try 'rm file'.""")
            elif user_input == "mkdir" or user_input.startswith("mkdir "):
                if user_input.startswith("mkdir "):
                    dir_name = user_input.split(" ", 1)[1]
                    try:
                        os.mkdir(dir_name)
                    except FileExistsError:
                        print(f"pysh: mkdir: cannot create directory '{dir_name}': File exists")
                    except Exception as e:
                        print(f"pysh: mkdir: {e}")
                else:
                    print("""pysh: mkdir: missing operand
Try 'mkdir dir'.""")
            elif user_input == "rmdir" or user_input.startswith("rmdir "):
                if user_input.startswith("rmdir "):
                    dir_name = user_input.split(" ", 1)[1]
                    try:
                        os.rmdir(dir_name)
                    except FileNotFoundError:
                        print(f"pysh: rmdir: failed to remove '{dir_name}': No such file or directory")
                    except OSError:
                        print(f"pysh: rmdir: failed to remove '{dir_name}': Directory not empty")
                    except Exception as e:
                        print(f"pysh: rmdir: {e}")
                else:
                    print("""pysh: rmdir: missing operand
Try 'rmdir dir'.""")
            elif user_input == "command" or user_input.startswith("command "):
                if user_input.startswith("command "):
                    exec_cmd = user_input.split(" ", 1)[1]
                    os.system(exec_cmd)
                else:
                    pass
            else:
                print(f"pysh: {user_input.split()[0]}: command not found")
    except KeyboardInterrupt:
        pass
    except EOFError:
        print("exit")
        break
