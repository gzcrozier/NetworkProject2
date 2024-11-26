from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler
import threading


class Group:
    def __init__(self, name):
        self.name = name
        self.bulletin = []
        self.users = set()

    def add_user(self, username):
        self.users.add(username)

    def add_message(self, message):
        self.bulletin.append(message)

    def __getitem__(self, message_idx):
        return self.bulletin[message_idx]

    def __len__(self):
        return len(self.bulletin)

    def max_idx(self):
        return len(self) - 1


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


class ThreadedTCPRequestHandler(BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    groups = {"public": Group("public")}

    groups["public"].add_message(("Message 0 Subject", "Message 0 Body"))
    groups["public"].add_message(("Message 1 Subject", "Message 1 Body"))
    groups["public"].add_message(("Message 2 Subject", "Message 2 Body"))

    group_lock = threading.Lock()
    server_users = set()
    user_lock = threading.Lock()

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.username = None
        self.message_cutoff = None

    def handle(self):
        while True:
            self.request.sendall("Enter username:".encode())
            username = self.request.recv(1024).strip().decode()
            if username not in self.server_users:
                self.request.sendall(f"Welcome to the server, {username}".encode())
                break
            else:
                self.request.sendall(f"{username} is already in the server, please choose another username.".encode())

        self.message_cutoff = {"public": -2}
        self.username = username

        with self.user_lock:
            self.server_users.add(username)
            print(self.server_users)

        try:
            while True:
                command = self.request.recv(1024).decode()
                if command.strip() == "exit":
                    self.server_users.remove(self.username)
                    raise KeyboardInterrupt

                method = command.split(" ")[0]
                args = command.split(" ")[1:]
                try:
                    getattr(self, method)(*args)
                except AttributeError:
                    self.request.sendall("Invalid command!".encode())
                except TypeError:
                    self.request.sendall(f"Invalid arguments for {method}!".encode())
                except Exception:
                    self.request.sendall("An error has occurred, please try again.".encode())

        except Exception as e:
            self.server_users.remove(username)
            pass

    def join(self, group_name):
        with self.group_lock:
            self.groups["public"].add_user(self.username)
            self.message_cutoff["public"] = self.groups["public"].max_idx() - 1
        self.request.sendall(f"You have joined the {group_name} group!".encode())

    def message(self, message_idx):
        message_idx = int(message_idx)
        if self.message_cutoff["public"] < 0:
            self.request.sendall(f"Cannot access messages from group 'public'. Consider joining the group?".encode())
            return
        if not message_idx >= self.message_cutoff["public"]:
            self.request.sendall(f"Sorry, message {message_idx} cannot be accessed.".encode())
            return
        if message_idx >= len(self.groups["public"].bulletin):
            self.request.sendall(f"Message {message_idx} does not exist.".encode())
            return
        with self.group_lock:
            subject, body = self.groups['public'][message_idx]
        self.request.send(f"{subject}\n{body}".encode())

    def post(self):
        if self.username not in self.groups["public"].users:
            self.request.sendall("Cannot post to group 'public'. Consider joining the group?".encode())
            return
        self.request.sendall("Enter message subject:".encode())
        message_subject = self.request.recv(1024).decode()
        self.request.sendall("Enter message body:".encode())
        message_body = self.request.recv(1024).decode()
        with self.group_lock:
            self.groups["public"].add_message((message_subject, message_body))
        self.request.sendall("Message posted!".encode())

    def users(self):
        with self.user_lock:
            users = ("\n".join(self.groups["public"].users))
        if users:
            self.request.sendall(users.encode())
            return
        self.request.sendall("No users in public.".encode())

    def leave(self):
        with self.group_lock:
            self.groups["public"].users.remove(self.username)
        self.message_cutoff["public"] = -2
        self.request.sendall("Successfully left group 'public'".encode())

    # TODO: Add clean-up method to remove users not in the server from all groups (I think?)

