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
