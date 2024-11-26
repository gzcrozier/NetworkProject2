import java.io.*;
import java.net.*;

public class SocketClient {
    public static void main(String[] args) {
        try (
            Socket socket = new Socket("localhost", 9999);
            BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
            BufferedReader console = new BufferedReader(new InputStreamReader(System.in))
        ){
            //Read the initial message from the server
            System.out.println(in.readLine());

            //Main loop
            while(true){
                System.out.print("> ");
                //Read the command from the user's input
                String command = console.readLine();
                //Sent the command to the server
                out.println(command);
                //Print the server's response
                System.out.println(in.readLine());
            }
        } catch (IOException e){
            System.err.println("Connection error: " + e.getMessage());
        }
    }
}
