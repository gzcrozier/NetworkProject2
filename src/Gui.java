import javax.swing.*;
import java.awt.*;
import javax.swing.event.ChangeListener;
import javax.swing.event.ChangeEvent;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.HashMap;

public class Gui {
    private JFrame frame;
    private JPanel centralPanel;
    private int width;
    private int height;

    private JMenuBar menuBar;
    private JMenu groupMenu;
    private JCheckBoxMenuItem[] groupCheckBoxMenuItems;

    private JTabbedPane tabSelector;
    private JPanel[] groupPanels;
    private String[][] groupMessages;

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

            item.addActionListener(new ActionListener() {
                @Override
                public void actionPerformed(ActionEvent e) {
                    // If we get to this point in code some change was made to the menu and we need to update displayed tabs.
                    if (item.isSelected()) {
                        tabSelector.add(index + ": " + name, panel);
                        client.communicate("groupjoin" + index);
                    }
                    else {
                        tabSelector.remove(panel);
                        client.communicate("groupleave" + index);
                    }
                }
            });

            JPanel[] currentPanels = this.groupPanels;
            this.tabSelector.addChangeListener(new ChangeListener() {
                @Override
                public void stateChanged(ChangeEvent e) {
                    JPanel selectedPanel = (JPanel) tabSelector.getSelectedComponent();
                    int selectedIndex = -1;
                    for (int i = 0; i < currentPanels.length; i++) {
                        if (currentPanels[i] == selectedPanel) {
                            selectedIndex = i;
                            break;
                        }
                    }
                    if (selectedIndex == -1) {
                        System.err.println("Selected index: " + selectedIndex + " Unable to parse");
                    }
                    System.out.println(client.communicate("usergroupinfo " + index));
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
