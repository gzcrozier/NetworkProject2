import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;


public class App {
    public static void main(String[] args) {
        // Create an instance of the client.
        SocketClient client = new SocketClient("localhost", 9998, false);

        // Create a new instance of the GUI and put it on the screen.
        Gui gui = new Gui(1280, 720);
        gui.show();

        // Get the prompt message from the server.
        String promptMessage, name, response = null;
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
            try {
                client.sendMessage(name);
                response = client.readMessage();
            } catch (IOException e) {
                System.err.println("Error sending the message to the server: " + e.getMessage());
            }
        } while (name == null || name.isBlank() || response == null || response.contains("please choose another username"));
        gui.setWelcome(response);

        // Get the groups before the user joins any of them so there is no chance of them recieving any other message in the meantine.
        try {
            client.sendMessage("groups");
            ArrayList<HashMap<String, Object>> groupDicts = parseGroups(client.readMessage());
            gui.setGroups(groupDicts, client);
        } catch (IOException e) {
            System.err.println("Unable to get groups" + e.getMessage());
        }

        // Active the listening thread to handle the remaining application behavior.
        gui.startListenerThread(client, gui);
    }

    public static ArrayList<HashMap<String, Object>> parseGroups(String response) {
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
