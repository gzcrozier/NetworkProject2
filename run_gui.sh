# Java compile the code for the GUI.
javac "./src/App.java" "./src/SocketClient.java" "./src/Gui.java";
(cd "src" && java "App" && cd "..");
