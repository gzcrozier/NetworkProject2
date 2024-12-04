import java.io.*;
import java.net.*;

public class SocketClient {
    private Socket socket;
    private BufferedInputStream in;
    private PrintWriter out;

    public SocketClient(String ip, int port, boolean doInitialRead) {
        // Connect to the server
        try {
            this.socket = new Socket(ip, port);
            this.in = new BufferedInputStream(this.socket.getInputStream());
            this.out = new PrintWriter(this.socket.getOutputStream(), true);
        } catch (IOException e) {
            System.err.println("Connection error: " + e.getMessage());
            this.close();
        }
        // Read the initial message from the server
        if (doInitialRead) {
            try {
                System.out.println(readMessage());
            } catch (IOException e) {
                System.err.println("Connection error: " + e.getMessage());
            }
        }
    }

    public String readMessage() throws IOException {
        // Create a StringBuilder to store chunks of the message
        StringBuilder message = new StringBuilder();
        byte[] buffer = new byte[1024];
        int bytesRead;
        String chunk;

        // Read the message in chunks until the <END> delimiter is found
        while ((bytesRead = this.in.read(buffer)) != -1) {
            // Add the chunk to the message
            chunk = new String(buffer, 0, bytesRead);
            message.append(chunk);

            // Check if the <END> delimiter is present
            if (message.toString().contains("<END>")) break;
        }

        // Remove the <END> delimiter before returning
        return message.toString().replace("<END>", "");
    }

    public void sendMessage(String s) throws IOException {
        this.out.println(s);
    }

    public void loop() {
        // Main processing loop for sending and receiving messages with the server
        String message;
        BufferedReader consoleReader = new BufferedReader((new InputStreamReader(System.in)));

        Thread serverListener = new Thread(() -> {
            // Thread to listen for announcments, interrupt exectuion, display them, and continue
            try {
                while (true) {
                    String serverMessage = readMessage();
                    if (serverMessage == null) continue; 
                    System.out.println("\n" + serverMessage);
                    System.out.print("> "); // Reprint prompt for user input
                }
            } catch (IOException e) {
                System.err.println("You left the server.");
                System.out.print("> ");
            }
        });

        serverListener.start();

        try {
            System.out.print("> "); // Prompt for user to enter commands
            while (true) {
                // Read a line (command) from the terminal.
                message = consoleReader.readLine();
                
                // Check that the use gave a command.
                if (message.isBlank()) continue;

                // User calls exit
                if (message.equalsIgnoreCase("exit")) {
                    break;
                }

                // If we get to this point the user gave a command we need to send to the server, sending.
                this.sendMessage(message);
            }
        } catch (IOException e) {
            System.err.println("Error reading the message from the terminal: " + e.getMessage());
        }
    }

    public void close() {
        // Close the connection
        try {
            this.in.close();
        } catch (IOException e) {
            System.err.println("Error closing the connection: " + e.getMessage());
        }
        this.out.close();
        try {
            this.socket.close();
        } catch (IOException e) {
            System.err.println("Error closing the connection: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        while (true) {
        String message = "";
        String ip = "";
        int port = 0;
        SocketClient client = null;

        BufferedReader consoleReader = new BufferedReader((new InputStreamReader(System.in)));
        while (!(message.split(" ")[0].equalsIgnoreCase("connect"))) {
            // Waiting for the user to input "connect"
            try {
                System.out.print("> "); // Prompt for user to connect to the server
                message = consoleReader.readLine();
            }
            catch (IOException e) {
                System.err.println("Could not read command: " + e.getMessage());
                message = "";
                continue;
            }

            try {    
                // Try to extract the ip and port number from the connect command
                ip = message.split(" ")[1];
                port = Integer.parseInt(message.split(" ")[2]);
            }
            catch (IndexOutOfBoundsException e) {
                System.err.println("'connect' expects IP address and port number.");
                message = "";
                continue;
            }

            try {
                // Try to instantiate the client
                client = new SocketClient(ip, port, true);
            } 
            catch (Exception e) {
                client = null;
                System.err.println("Could not connect to the server!");
                message = "";
            }
        }
        client.loop();
        client.close();
    }
    }
}
