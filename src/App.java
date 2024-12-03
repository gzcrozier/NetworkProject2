import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;


public class App {
    public static void main(String[] args) {
        // Create an instance of the client.
        SocketClient client = new SocketClient("localhost", 9999, false);

        // Create a new instance of the GUI and put it on the screen.
        Gui gui = new Gui(1280, 720);
        gui.show();

        // Get the prompt message from the server.
        String promptMessage, name;
        do {
            try {
                promptMessage = client.readMessage();
            } catch (IOException e) {
                System.err.println("Error reading the message from the server: " + e.getMessage());
                promptMessage = null;
            }
        } while (promptMessage == null || promptMessage.isBlank());

        // Setup and get our username to answer the server.
        do {
            name = gui.getUsername(promptMessage);
        } while (name == null || name.isBlank() || name.endsWith("please choose another username"));

        // Send the username to the server.
        try {
            client.sendMessage(name);
        } catch (IOException e) {
            System.err.println("Error sending the message to the server: " + e.getMessage());
        }

        // Get the welcome message from the server.
        try {
            gui.setWelcome(client.readMessage());
        } catch (IOException e) {
            System.err.println("Error reading the message from the server: " + e.getMessage());
        }

        // Get the groups from the server and parse them.
        ArrayList<HashMap<String, Object>> groupDicts = getGroups(client.communicate("groups"));

        // Set the application groups.
        gui.setGroups(groupDicts, client);
    }

    public static ArrayList<HashMap<String, Object>> getGroups(String response) {
        ArrayList<HashMap<String, Object>> groups = new ArrayList<>();
        String[] lines = response.split("\n");
        // Loop through all the lines of the response and store the information in dictionaries.
        for (String line : lines) {
            HashMap<String, Object> group = new HashMap<>();
            int nameStartIndex = line.indexOf(":") + 1;            
            int nameEndIndex = line.indexOf(",");
            String name = line.substring(nameStartIndex, nameEndIndex);
            group.put("name", name);
            int index = Character.getNumericValue(line.charAt(line.length() - 1));
            group.put("index", index);
            groups.add(group);
        }
        return groups;
    }
}
