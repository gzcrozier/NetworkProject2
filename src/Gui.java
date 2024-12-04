import javax.swing.*;
import java.awt.*;
import java.util.Scanner;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Vector;

public class Gui {
    private JFrame frame;
    private JPanel centralPanel;
    private int width;
    private int height;

    private JMenuBar menuBar;
    private JMenu groupMenu;
    private JCheckBoxMenuItem[] groupCheckBoxMenuItems;

    private int selectedGroupIndex;
    private JTabbedPane tabSelector;
    private JPanel[] groupPanels;
    private HashMap<String, Vector<String>> groupMessageDict;

    private JTextField input;
    private JTextArea primaryTextArea;
    private JButton sendButton;

    public Gui(int width, int height) {
        this.width = width;
        this.height = height;

        this.frame = new JFrame("");
        this.frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.frame.setLayout(new BorderLayout());

        this.menuBar = new JMenuBar();
        this.groupMenu = new JMenu("Groups");

        this.menuBar.add(this.groupMenu);
        this.frame.setJMenuBar(menuBar);

        this.tabSelector = new JTabbedPane();
        this.groupMessageDict = new HashMap<String, Vector<String>>();

        this.centralPanel = new JPanel();
        this.centralPanel.setLayout(new BoxLayout(centralPanel, BoxLayout.Y_AXIS));

        this.primaryTextArea = new JTextArea(3, 20);
        this.primaryTextArea.setEditable(false);
        this.primaryTextArea.setLineWrap(true);
        this.primaryTextArea.setWrapStyleWord(true);
        this.primaryTextArea.setVisible(false);

        this.input = new JTextField();
        this.input.setVisible(false);

        this.sendButton = new JButton("Send");
        this.sendButton.setVisible(false);

        this.centralPanel.add(this.primaryTextArea);
        this.centralPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        this.centralPanel.add(this.input);
        this.centralPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        this.centralPanel.add(this.sendButton);
        this.centralPanel.add(this.tabSelector);

        this.frame.add(centralPanel, BorderLayout.CENTER);
    }

    public void startListenerThread(SocketClient client) {
        Thread serverListener = new Thread(() -> {
            // Thread to listen for announcments and display them, then continue
            try {
                while (true) {
                    String serverMessage = client.readMessage();
                    if (serverMessage == null) continue; 
                    if (serverMessage.startsWith("You have joined ")) client.sendMessage("usergroupinfo " + serverMessage.substring(16, serverMessage.indexOf("!")));
                    else if (serverMessage.startsWith("Group: ")) {
                        String[] parts = serverMessage.split("\n");
                        String group = parts[0].split(": ")[1];
                        String usersString = parts[1].split(": ")[1];
                        String[] users = usersString.substring(1, usersString.length() - 1).split(", ");
                        int numMessages = Integer.parseInt(parts[2].split(": ")[1].strip());
                        int cutoff = Integer.parseInt(parts[3].split(": ")[1].strip());
                        
                        for (int i = cutoff; i < numMessages; i++) client.sendMessage("groupmessage " + group + " " + Integer.toString(i));
                    }
                    else System.out.println("====================" + serverMessage);
                }
            } catch (IOException e) {
                System.err.println("Error reading from server: " + e.getMessage());
            }
        });
        serverListener.start();
    }

    public void show() {
        this.frame.setSize(this.width, this.height);
        this.frame.setVisible(true);
    }

    public void setWelcome(String message) {
        this.frame.setTitle(message);
    }

    public void setGroups(ArrayList<HashMap<String, Object>> groups, SocketClient client) {
        int size = groups.size();
        this.groupCheckBoxMenuItems = new JCheckBoxMenuItem[size];
        this.groupPanels = new JPanel[size];

        for (int i = 0; i < groups.size(); i++) {
            HashMap<String, Object> group = groups.get(i);
            String name = (String) group.get("name");
            String index = group.get("index").toString();
            JCheckBoxMenuItem item = new JCheckBoxMenuItem(index + ": " + name);
            this.groupCheckBoxMenuItems[i] = item;
            this.groupMenu.add(item);

            JPanel panel = new JPanel();
            panel.setVisible(false);
            this.groupPanels[i] = panel;
            this.groupMessageDict.put(name, new Vector<String>());

            item.addActionListener(new ActionListener() {
                @Override
                public void actionPerformed(ActionEvent e) {
                    // If we get to this point in code some change was made to the menu and we need to update displayed tabs.
                    try {
                        if (item.isSelected()) {
                            tabSelector.add(index + ": " + name, panel);
                            client.sendMessage("groupjoin " + index);
                        }
                        else {
                            tabSelector.remove(panel);
                            client.sendMessage("groupleave " + index);
                        }
                    } catch (IOException d) {
                        System.err.println("Error sending server group change. " + d.getMessage());
                    }
                }
            });
        }
    }

    public String getUsername(String promptMessage) {
        this.primaryTextArea.setText(promptMessage);
        this.primaryTextArea.setVisible(true);
        this.input.setVisible(true);
        this.sendButton.setVisible(true);

        final String[] username = {null};

        this.sendButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                username[0] = input.getText();
                synchronized (Gui.this) {
                    Gui.this.notify();
                }
            }
        });

        synchronized (this) {
            try {
                while (username[0] == null) {
                    this.wait();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        this.primaryTextArea.setVisible(false);
        this.input.setVisible(false);
        this.sendButton.setVisible(false);

        return username[0];
    }
}
