# Start the web server if it is not already running.
(pgrep -f "python3 ./webserver/server.py" > /dev/null && echo "Server already running.") || (python3 ./webserver/server.py &);

# Java compile the code for the GUI.
javac "./src/App.java" "./src/SocketClient.java" "./src/Gui.java";
(cd "src" && java "App" && cd "..");

# Kill the web server once bash receives execution again (i.e. when the Java GUI is closed).
kill $(ps aux | grep "python3 ./webserver/server.py" | sed -n "1p" | grep -Eo "[0-9]+" | sed -n "1 p");
