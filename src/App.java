import java.io.IOException;

public class App {
    public static void main(String[] args) {
        // Create an instance of the client
        SocketClient client = new SocketClient("localhost", 9999, false);

        // Create a new instance of the GUI
        Gui gui = new Gui(1280, 720);

        gui.show();
        String promptMessage, name;
        do {
            try {
                promptMessage = client.readMessage();
            } catch (IOException e) {
                System.err.println("Error reading the message from the server: " + e.getMessage());
                promptMessage = null;
            }
        } while (promptMessage == null || promptMessage.isBlank());
        
        name = gui.getUsername(promptMessage);

        try {
            client.sendMessage(name);
        } catch (IOException e) {
            System.err.println("Error sending the message to the server: " + e.getMessage());
        }

        try {
            String welcome = client.readMessage();
            System.out.println(welcome);
        } catch (IOException e) {
            System.err.println("Error reading the message from the server: " + e.getMessage());
        }

        try {
            client.sendMessage("groups");
        } catch (IOException e) {
            System.err.println("Error sending the message to the server: " + e.getMessage());
        }

        try {
            String groups = client.readMessage();
            System.out.println(groups);
        } catch (IOException e) {
            System.err.println("Error reading the message from the server: " + e.getMessage());
        }


        

    }
}
