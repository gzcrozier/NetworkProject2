Zach Crozier, Hayden Dennis, Matt Heeter

## About
The files for the webserver are in `/webserver` and the files for the client are in `/src`.
The client is in java and uses `javax.swing` to build a GUI. The server is in python and uses `socket` to communicate with the client.
The messages are not sent in json or xml. They are just sent as strings.

### How to run
The following commands assume you are in the root directory of the project. Bash scripts are provided to run the server and client together. The following instructions are for running the server and client manually. Use `bash run_cli.sh` and `bash run_gui.sh` to run the applications.
1. Run the server using `python3 ./webserver/server.py &`.

#### CLI
2. Run `java ./src/SocketClient.java` to compile and run the client.

#### GUI
2. Compile the java classes using `javac "./src/App.java" "./src/SocketClient.java" "./src/Gui.java"`.
3. `cd src`.
4. Run the GUI using `java App`.

