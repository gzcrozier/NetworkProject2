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
        return max(len(self) - 1, 0)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


class ThreadedTCPRequestHandler(BaseRequestHandler):
    """
    """
    groups = {"public": Group("public")}  # Defining all groups up-front
    group_lock = threading.Lock()  # Need to use locks to make any writes to groups or users
    server_users = set()  # Set of users currently on the server
    user_lock = threading.Lock()
    clients = []  # Holds all clients for broadcasting
    client_lock = threading.Lock()

    # TODO: Remove these, they are used for testing
    groups["public"].add_message(("Message 0 Subject", "Message 0 Body"))
    groups["public"].add_message(("Message 1 Subject", "Message 1 Body"))
    groups["public"].add_message(("Message 2 Subject", "Message 2 Body"))

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.username = None  # The username for the connected client
        self.message_cutoff = None  # Used to keep track of the "last two message" aspect

    def handle(self):
        with self.client_lock:
            self.clients.append(self)
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
                    self.request.sendall(f"{username} is already in the server, please choose another username.<END>".encode())

        # Ensures that a user may not access any message in a group that they are not a part of
        # TODO: extend to all groups
        self.message_cutoff = {"public": -2}
        self.username = username

        try:
            while True:
                # Loop to accept and serve commands from clients
                command = self.request.recv(1024).decode()
                if command.strip() == "exit":
                    # Command to exit the server
                    with self.user_lock:
                        self.server_users.remove(self.username)
                    self._leave()
                    raise KeyboardInterrupt

                # Splitting the command into the named command and the arguments passed to it
                method = command.split(" ")[0]
                method = method.replace("\n", "")
                args = command.split(" ")[1:]
                args = [arg.replace("\n", "") for arg in args]
                try:
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
            self._leave()
            with self.user_lock:
                self.server_users.remove(username)
            pass

    def join(self, group_name):
        # Joining a group
        # TODO: Extend to multiple groups
        with self.group_lock:
            # Adding the username to the group
            self.groups["public"].add_user(self.username)
        # Allowing the user to access the last and second to last most recently added bulletin messages
        self.message_cutoff["public"] = self.groups["public"].max_idx() - 1
        self.request.sendall(f"You have joined the {group_name} group! <END>".encode())

    def message(self, message_idx):
        # Displaying messages
        # TODO: Extend to multiple groups
        message_idx = int(message_idx)
        if self.message_cutoff["public"] < -1:
            # The user is not a part of the group
            self.request.sendall(f"Cannot access messages from group 'public'. Consider joining the group?<END>".encode())
            return
        if not message_idx >= self.message_cutoff["public"]:
            # The user is trying to access a message that was added more than 2 posts ago
            self.request.sendall(f"Sorry, message {message_idx} cannot be accessed.<END>".encode())
            return
        if message_idx >= len(self.groups["public"].bulletin):
            # The user is trying to access messages with indices that do not yet exist
            self.request.sendall(f"Message {message_idx} does not exist.<END>".encode())
            return
        subject, body = self.groups['public'][message_idx]
        self.request.send(f"{subject}\n{body}<END>".encode())

    def post(self):
        # Posting to a bulletin
        # TODO: Extend to multiple groups
        # TODO: Find out all how to send all necessary broadcast info to all users
        if self.username not in self.groups["public"].users:
            # The user is not in the group
            self.request.sendall("Cannot post to group 'public'. Consider joining the group?<END>".encode())
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
            self.groups["public"].add_message((message_subject, message_body))
        self.request.sendall("Message posted!<END>".encode())

    def users(self):
        # Displaying the users within a group
        # TODO: Extend to multiple groups
        users = ("\n".join(self.groups["public"].users))
        users = users + "<END>"
        if users:
            self.request.sendall(users.encode())
            return
        # Case for there being no users
        self.request.sendall("No users in public.<END>".encode())

    def leave(self):
        # Leaving a group
        # TODO: Extend to multiple groups
        self._leave()
        self.request.sendall("Successfully left group 'public'<END>".encode())

    def _leave(self):
        # Leaving a group (internal method)
        # TODO: Extend to multiple groups
        with self.group_lock:
            self.groups["public"].users.remove(self.username)
        self.message_cutoff["public"] = -2

    # TODO: Add clean-up method to remove users not in the server from all groups (I think?)

