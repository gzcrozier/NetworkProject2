from datetime import datetime
from functools import partialmethod
from typing import List, Optional, Set, Dict, Tuple, Sequence
from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler, BaseServer
import threading
from socket import socket as Socket


class Group:
    """Class that holds information about a messaging group."""
    def __init__(self, name):
        self.name = name
        self.bulletin: List[str] = []
        self.users: Set[str] = set()

    def add_user(self, username: str):
        # Adds a user to the group
        self.users.add(username)

    def add_message(self, message: str):
        # Adds a message to the bulletin
        self.bulletin.append(message)

    def __getitem__(self, message_idx: int) -> str:
        # Gets a message from the bulletin
        return self.bulletin[message_idx]

    def __len__(self) -> int:
        return len(self.bulletin)

    def max_idx(self) -> int:
        # Gets the index of the last message in the bulletin, useful for user only being able to access 2 most recent
        # messages upon joining
        return max(len(self) - 1, 0)


class GroupError(Exception):
    # Custom exception to be raised and handled when the user does something with a group that does not exist.
    pass


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
    group_ids = {str(i): k for i, k in enumerate(available_groups)}

    available_groups["public"].add_message("Message 1 Body")
    available_groups["public"].add_message("Message 2 Body")
    available_groups["public"].add_message("Message 3 Body")
    available_groups["group2"].add_message("Message 1 Body")
    available_groups["group2"].add_message("Message 2 Body")
    available_groups["group2"].add_message("Message 3 Body")

    # Define the list to store our server's users. This lock will be used to ensure no simultaneous access.
    user_lock = threading.Lock()
    server_users: Set[str] = set()

    # Type hint these here so the LSP can see it.
    request: Socket
    server: BaseServer
    client_address: Tuple[str, int]
    username: Optional[str]
    clients: Dict[str, "ThreadedTCPRequestHandler"] = {}
    client_lock = threading.Lock()

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
                    if "_" in method or method == "handle":
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
                except GroupError:
                    self.request.sendall(f"Group does not exist!<END>".encode())
                except Exception:
                    # If some other error occurred (typically inside the command's function)
                    self.request.sendall("An error has occurred, please try again.<END>".encode())

        except Exception as e:
            # For the client leaving the server for any reason
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

    def get_group(self, groupname: str) -> Tuple[Group, str]:
        try:
            # Try to use groupname to index into available_groups
            group = self.available_groups[groupname]
        except KeyError:
            try:
                # The name is an ID, indexing into IDs then available
                groupname = self.group_ids[groupname]
                # Make sure this name actually exists, otherwise error
                group = self.available_groups[groupname]
            except KeyError:
                raise GroupError

        return group, groupname

    def groupjoin(self, groupname: str):
        # TODO: Logic for if group does not exist
        # Joining a group
        group, groupname = self.get_group(groupname)
        if self.username in group.users:
            self.request.sendall(f"You are already in {groupname}!<END>".encode())
            return

        with self.group_lock:
            group.add_user(self.username)

            # Allowing the user to access the last and second to last most recently added bulletin messages
            self.my_groups.add(groupname)
            self.message_cutoff[groupname] = group.max_idx() - 1
            self.request.sendall(f"You have joined {groupname}! <END>".encode())

        self._announce(f"{self.username} has joined {groupname}!", group.users, self.username)

    join = partialmethod(groupjoin, groupname="public")
        
    def groupmessage(self, groupname: str, message_idx: int):
        # Displaying messages
        group, groupname = self.get_group(groupname)
        message_idx = int(message_idx)
        if self.username not in group.users:
            # The user is not a part of the group
            self.request.sendall(f"Cannot access messages from {groupname}. Consider joining the group?<END>".encode())
            return
        if not message_idx >= self.message_cutoff[groupname]:
            # The user is trying to access a message that was added more than 2 posts ago
            self.request.sendall(f"Sorry, message {message_idx} cannot be accessed.<END>".encode())
            return
        if message_idx >= len(group.bulletin):
            # The user is trying to access messages with indices that do not yet exist
            self.request.sendall(f"Message {message_idx} does not exist.<END>".encode())
            return
        body = group[message_idx]
        self.request.send(f"{body}<END>".encode())

    message = partialmethod(groupmessage, "public")

    def grouppost(self, groupname: str):
        # Posting to a bulletin
        group, groupname = self.get_group(groupname)
        # TODO: Find out all how to send all necessary broadcast info to all users
        if self.username not in group.users:
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
            group.add_message(message_body)
            message_idx = group.max_idx()
        self.request.sendall("Message posted!<END>".encode())
        # Announcing the message to all group members
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        announcement = (f"Message ID: {message_idx}\n"
                        f"Group : {group}\n"
                        f"From: {self.username}\n"
                        f"Time: {now}\n"
                        f"Subject: {message_subject}\n"
                        f"Group: {groupname}\n"
                        f"<END>")
        self._announce(announcement, group.users, self.username)

    post = partialmethod(grouppost, "public")

    def groupusers(self, groupname: str):
        # TODO: This sends nothing if the user is in no groups
        group, groupname = self.get_group(groupname)

        # Displaying the users within a group
        users = ("\n".join(group.users))
        users = users + "<END>"
        if users:
            self.request.sendall(users.encode())
            return

    users = partialmethod(groupusers, "public")

    def groups(self):
        message = []
        for g_key, g_id in zip(self.available_groups, self.group_ids):
            message.append(f"Group name: {g_key}, Group ID: {g_id}")

        message = "\n".join(message)
        message += "<END>"
        self.request.sendall(message.encode())

    def groupleave(self, groupname: str):
        group, groupname = self.get_group(groupname)
        # Leaving a group
        self._leave(groupname)
        self.request.sendall(f"Successfully left '{groupname}'<END>".encode())
        announcement = f"{self.username} has left the {groupname} group!\n"
        self._announce(announcement, group.users, self.username)

    def usergroupinfo(self, groupname: str):
        # Gets the group info specific to the user.
        with self.group_lock:
            group, groupname = self.get_group(groupname)
            message: str = (
                f"Group: {groupname}\n"\
                f"Users: [{', '.join(group.users)}]\n"\
                f"Messages: {len(group)}\n"\
                f"Cutoff: {self.message_cutoff[groupname]}\n<END>"
            )
            self.request.sendall(message.encode())

    leave = partialmethod(groupleave, "public")

    def _leave(self, groupname: str):
        group, groupname = self.get_group(groupname)
        # Leaving a group
        if self.username not in group.users:
            return
        with self.group_lock:
            group.users.remove(self.username)
        self.message_cutoff[groupname] = -2
