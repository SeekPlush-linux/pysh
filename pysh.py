from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import Completer, Completion
import os
import socket
import sys

VERSION = "1.0.0"
PY_VER = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

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
        if text.startswith("cd "):
            path = text[3:]
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

# @bindings.add("c-c")
# def _(event):
#     pass

while True:
    try:
        user_input: str = session.prompt(
            f"[{os.getlogin()}@{socket.gethostname()} {('~' if os.getcwd() == os.environ["HOME"] else '') or os.path.basename(os.getcwd()) or '/'}]$ ",
            key_bindings=bindings,
        ).strip()
        if user_input == "":
            continue
        elif user_input == "help" or user_input.startswith("help "):
            print(f"""pysh, version {VERSION}(1)-release (python-{PY_VER})
These shell commands are defined internally.  Type `help' to see this list.

 cd [dir]
 echo [arg ...]
 exit [n]
 false
 help
 la [dir]
 ls [dir]
 true""")
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
                    print(f"bash: cd: {new_dir}: No such file or directory")
                except Exception as e:
                    print(f"bash: cd: {e}")
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
                    print(f"bash: ls: cannot access '{path}': No such file or directory")
                except NotADirectoryError:
                    print(f"bash: ls: cannot access '{path}': Not a directory")
                except Exception as e:
                    print(f"bash: ls: {e}")
            else:
                try:
                    for item in os.listdir(os.getcwd()):
                        if not item.startswith("."):
                            print(item)
                except Exception as e:
                    print(f"bash: ls: {e}")
        elif user_input == "la" or user_input.startswith("la "):
            if user_input.startswith("la "):
                try:
                    path = user_input.split(" ", 1)[1]
                    for item in os.listdir(path):
                        print(item)
                except FileNotFoundError:
                    print(f"bash: la: cannot access '{path}': No such file or directory")
                except NotADirectoryError:
                    print(f"bash: la: cannot access '{path}': Not a directory")
                except Exception as e:
                    print(f"bash: la: {e}")
            else:
                try:
                    for item in os.listdir(os.getcwd()):
                        print(item)
                except Exception as e:
                    print(f"bash: la: {e}")
        elif user_input == "echo" or user_input.startswith("echo "):
            if user_input.startswith("echo "):
                echo = user_input.split(" ", 1)[1]
                print(echo)
            else:
                print()
        elif user_input == "true" or user_input.startswith("true ") or user_input == "false" or user_input.startswith("false "):
            continue
        else:
            print(f"bash: {user_input.split()[0]}: command not found")
    except KeyboardInterrupt:
        print("^C")
    except EOFError:
        print("exit")
        break
