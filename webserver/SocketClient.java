import java.io.*;
import java.net.*;

public class SocketClient {
    public static void main(String[] args) {
        try (
            Socket socket = new Socket("localhost", 9999);
            BufferedInputStream in = new BufferedInputStream(socket.getInputStream());
            PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
            BufferedReader console = new BufferedReader(new InputStreamReader(System.in))
        ) {
            // Read the initial message from the server
            System.out.println(readFullMessage(in));

            // Main loop
            while (true) {
                System.out.print("> ");
                String command = console.readLine();
                out.println(command);
                System.out.println(readFullMessage(in)); // Read server response
            }
        } catch (IOException e) {
            System.err.println("Connection error: " + e.getMessage());
        }
    }

    // Helper method to read a full message until <END>
    private static String readFullMessage(BufferedInputStream in) throws IOException {
        StringBuilder message = new StringBuilder();
        byte[] buffer = new byte[1024];
        int bytesRead;
        String chunk;

        while ((bytesRead = in.read(buffer)) != -1) {
            chunk = new String(buffer, 0, bytesRead);
            message.append(chunk);

            // Check if the <END> delimiter is present
            if (message.toString().contains("<END>")) {
                break;
            }
        }

        // Remove the <END> delimiter before returning
        String result = message.toString();
        return result.substring(0, result.indexOf("<END>"));
    }
}
