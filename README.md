Zach Crozier, Hayden Dennis, Matt Heeter

## About
The files for the webserver are in `/webserver` and the files for the client are in `/src`.
The client is in java and uses `javax.swing` to build a GUI. The server is in python and uses `socket` to communicate with the client.
The messages are not sent in json or xml. They are just sent as strings.

## How to run
1. CD to the root directory of the project. Bash scripts are provided to run the server and client.
2. Run the server with the command listed below.
3. Run one (or both) of the clients with the commands underneath it.

#### Server
To start the server:
```sh
bash run_server.sh
```

#### CLI
To use the application from the command-line interface:
```sh
bash run_cli.sh
```

#### GUI
To use the application from the graphical-user interface:
```sh
bash run_gui.sh
```

## Issues
#### Getting Java and python to work together
It was rather trivial to build a python server and have a java client connect to it. We did, however, have some pretty 
annoying issues when it came to actually sending messages between these two. Python was find sending and receiving any
message you sent, with no special formatting required. Java, on the other hand, took newline characters (of which
there are lot) to mean that was the end of the message. As such, before our solution, any message sent from the server
to the client that contained a newline character would only send until that character. To get around this, we built a 
custom function to read messages from the server, and only consider it to be the end of the message if "<END>" was 
encountered. We figured this string is highly unlikely to be exist anywhere except for where we put it, and it is 
readable to developers to understand that is the end of the message. The function that handles this is in 
`src/SocketClient.java` as `readMessage()`.

#### Getting the client to post announcements
There are a few events that trigger calling the `_announce()` method within `webserver/helpers.py`. These include when 
a user joins and leaves a group, and when a user posts. This method sends a message to all clients in the group in 
which these events occur, and are designed such that the client is interrupted to display the message, then carries on.
The way that we had to do this was a bit tricky, and it is implemented as `serverListener` in `src/SocketClient.java`.
This is a thread that handles messages from the client, allowing for expected messages to be shown to the user
(responses to commands, for example) as well as announcements that are not expected.
