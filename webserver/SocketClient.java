import java.io.*;
import java.net.*;

public class SocketClient {
    private Socket socket;
    private BufferedInputStream in;
    private PrintWriter out;

    public SocketClient(String ip, int port) {
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
        try {
            System.out.println(readMessage());
        } catch (IOException e) {
            System.err.println("Connection error: " + e.getMessage());
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
        String message, response;
        BufferedReader consoleReader = new BufferedReader((new InputStreamReader(System.in)));

        Thread serverListener = new Thread(() -> {
            // Thread to listen for announcments and display them, then continue
            try {
                while (true) {
                    String serverMessage = readMessage();
                    if (serverMessage == null) continue; 
                    System.out.println("\n" + serverMessage);
                    System.out.print("> "); // Reprint prompt for user input
                }
            } catch (IOException e) {
                System.err.println("Error reading from server: " + e.getMessage());
            }
        });

        serverListener.start();

        try {
            System.out.print("> ");
            while (true) {
                // Read a line (command) from the terminal.
                message = consoleReader.readLine();
                
                // Check that the use gave a command.
                if (message.isBlank()) continue;

                // If we get to this point the user gave a command we need to send to the server.
                this.sendMessage(message);

                // // Read updates from the server.
                // response = this.readMessage();
                // System.out.println(response);
            }
        } catch (IOException e) {
            System.err.println("Error reading the message from the terminal: " + e.getMessage());
        }
    }

    public void close() {
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
        SocketClient client = new SocketClient("localhost", 9999);
        client.loop();
        client.close();
    }
}
