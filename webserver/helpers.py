from datetime import datetime
from functools import partial
from typing import List, Optional, Set, Dict, Tuple, Sequence
from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler, BaseServer
import threading
from socket import socket as Socket


class Group:
    def __init__(self, name):
        self.name = name
        self.bulletin: List[str] = []
        self.users: Set[str] = set()

    def add_user(self, username):
        self.users.add(username)

    def add_message(self, message: str):
        self.bulletin.append(message)

    def __getitem__(self, message_idx: int) -> str:
        return self.bulletin[message_idx]

    def __len__(self) -> int:
        return len(self.bulletin)

    def max_idx(self) -> int:
        return max(len(self) - 1, 0)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


class ThreadedTCPRequestHandler(BaseRequestHandler):
    # Define the groups available to users on the server. This lock will be used to ensure no simultaneous access.
    group_lock = threading.Lock()
    available_groups: Dict[str, Group] = {
        "public": Group("public"),
        "group1": Group("group1"),
        "group2": Group("group2"),
        "group3": Group("group3"),
        "group4": Group("group4"),
        "group5": Group("group5"),
    }
    # Adding IDs as keys to the group dict, pointing to the same groups
    group_ids = {str(i): v for i, (_, v) in enumerate(available_groups.items())}
    available_groups |= group_ids

    # Define the list to store our server's users. This lock will be used to ensure no simultaneous access.
    user_lock = threading.Lock()
    server_users: Set[str] = set()

    # Type hint these here so the LSP can see it.
    request: Socket
    server: BaseServer
    client_address: Tuple[str, int]
    username: Optional[str]
    clients = {}  # Holds all clients for broadcasting
    client_lock = threading.Lock()

    # TODO: Remove these, they are used for testing
    available_groups["public"].add_message("Message 0 Body")
    available_groups["public"].add_message("Message 1 Body")
    available_groups["public"].add_message("Message 2 Body")

    def __init__(self, request: Socket, client_address, server: BaseServer):
        super().__init__(request, client_address, server)
        self.username = None  # The username for the connected client
        self.message_cutoff = None  # Used to keep track of the "last two message" aspect
        self.my_groups = None

    def handle(self):
        while True:
            # Loop to have every user choose a unique username
            self.request.sendall("Enter username:<END>".encode())
            username = self.request.recv(1024).strip().decode()
            with self.user_lock:
                if username not in self.server_users:
                    self.server_users.add(username)
                    self.request.sendall(f"Welcome to the server, {username}<END>".encode())
                    break
                else:
                    self.request.sendall(f"{username} is already in the server, please choose another username.\n<END>".encode())

        # Ensures that a user may not access any message in a group that they are not a part of
        self.message_cutoff = {g: -2 for g in self.available_groups}
        self.username = username
        self.my_groups = set()

        with self.client_lock:
            self.clients[self.username] = self

        try:
            while True:
                # Loop to accept and serve commands from clients
                command: str = self.request.recv(1024).decode()

                # Splitting the command into the named command and the arguments passed to it
                method, *args = command.replace("\n", "").split(" ")
                try:
                    if "_" in method:
                        # Client cannot run internal commands
                        raise AttributeError
                    # Try to use the command with the arguments provided
                    getattr(self, method)(*args)
                except AttributeError:
                    # If the provided command does not exist
                    self.request.sendall("Invalid command!<END>".encode())
                except TypeError:
                    # If the arguments to the command are invalid
                    self.request.sendall(f"Invalid arguments for {method}!<END>".encode())
                except Exception:
                    # If some other error occurred (typically inside the command's function)
                    # TODO: Provide a more useful error message to help the client out?
                    self.request.sendall("An error has occurred, please try again.<END>".encode())

        except Exception as e:
            # For the client leaving the server for any other reason
            for g in self.available_groups:
                self._leave(g)
            with self.user_lock:
                self.server_users.remove(self.username)
            with self.client_lock:
                self.clients.pop(self.username)

    def _announce(self, message: str, users: Set[str], sender: str):
        # Sending messages to users
        for user in users:
            if user == sender:
                # Don't really need to announce it to the user who sends it
                continue
            self.clients[user].request.sendall(f"{message}<END>".encode())

    # join = partial(lf.groupjoin)
    def join(self):
        # Joining the public group
        self.groupjoin("public")

    def groupjoin(self, groupname: str):
        # Joining a group
        with self.group_lock:
            self.available_groups[groupname].add_user(self.username)

        # Allowing the user to access the last and second to last most recently added bulletin messages
        self.my_groups.add(groupname)
        self.message_cutoff[groupname] = self.available_groups[groupname].max_idx() - 1
        self.request.sendall(f"You have joined {groupname}! <END>".encode())

        self._announce(f"{self.username} has joined {groupname}!",
                       self.available_groups[groupname].users,
                       self.username)
        
    def message(self, message_idx: int):
        # Displaying messages for the public group
        self.groupmessage("public", message_idx)

    def groupmessage(self, groupname: str, message_idx: int):
        # Displaying messages
        message_idx = int(message_idx)
        if self.message_cutoff[groupname] < -1:
            # The user is not a part of the group
            self.request.sendall(f"Cannot access messages from {groupname}. Consider joining the group?<END>".encode())
            return
        if not message_idx >= self.message_cutoff[groupname]:
            # The user is trying to access a message that was added more than 2 posts ago
            self.request.sendall(f"Sorry, message {message_idx} cannot be accessed.<END>".encode())
            return
        if message_idx >= len(self.available_groups[groupname].bulletin):
            # The user is trying to access messages with indices that do not yet exist
            self.request.sendall(f"Message {message_idx} does not exist.<END>".encode())
            return
        body = self.available_groups[groupname][message_idx]
        self.request.send(f"{body}<END>".encode())

    def post(self):
        # Posting to the public bulletin
        self.grouppost("public")

    def grouppost(self, groupname: str):
        # Posting to a bulletin
        # TODO: Find out all how to send all necessary broadcast info to all users
        if self.username not in self.available_groups[groupname].users:
            # The user is not in the group
            self.request.sendall(f"Cannot post to group {groupname}. Consider joining the group?<END>".encode())
            return
        # Providing separate prompts for subject and body
        self.request.sendall("Enter message subject:<END>".encode())
        message_subject = self.request.recv(1024).decode()
        message_subject = message_subject.replace("\n", "")  # Java client adds newlines to everything, removing them

        self.request.sendall("Enter message body:<END>".encode())
        message_body = self.request.recv(1024).decode()
        message_body = message_body.replace("\n", "")

        with self.group_lock:
            # Adding the message
            self.available_groups[groupname].add_message(message_body)
        self.request.sendall("Message posted!<END>".encode())
        # Announcing the message to all group members
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        announcement = (f"Message ID: {self.available_groups[groupname].max_idx()}\n"
                        f"From: {self.username}\n"
                        f"Time: {now}\n"
                        f"Subject: {message_subject}\n"
                        f"<END>")
        self._announce(announcement, self.available_groups[groupname].users, self.username)

    def users(self):
        self.groupusers("public")

    def groupusers(self, groupname: str):
        # TODO: This sends nothing if the user is in no groups

        # Displaying the users within a group
        users = ("\n".join(self.available_groups[groupname].users))
        users = users + "<END>"
        if users:
            self.request.sendall(users.encode())
            return

    def leave(self):
        self.groupleave("public")

    def groupleave(self, groupname: str):
        # Leaving a group
        self._leave(groupname)
        self.request.sendall(f"Successfully left '{groupname}'<END>".encode())
        announcement = f"{self.username} has left the public group!\n"
        self._announce(announcement, self.available_groups[groupname].users, self.username)

    def _leave(self, groupname: str):
        # Leaving a group
        if self.username not in self.available_groups[groupname].users:
            return
        with self.group_lock:
            for g in self.my_groups:
                self.available_groups[g].users.remove(self.username)
        self.message_cutoff[groupname] = -2
