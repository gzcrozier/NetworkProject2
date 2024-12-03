import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class Gui {
    private JFrame frame;
    private int width;
    private int height;

    private JMenu groupMenu;
    private JCheckBoxMenuItem[] groupCheckboxItems;

    private JTextField input;
    private JTextArea prompt;
    private JButton sendButton;

    public Gui(int width, int height) {
        this.width = width;
        this.height = height;

        this.frame = new JFrame("The best chat app ever!");
        this.frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.frame.setLayout(new BorderLayout());

        JMenuBar menuBar = new JMenuBar();
        this.groupMenu = new JMenu("Groups");
        menuBar.add(this.groupMenu);
        this.frame.setJMenuBar(menuBar);

        JPanel centralPanel = new JPanel();
        centralPanel.setLayout(new BoxLayout(centralPanel, BoxLayout.Y_AXIS));

        this.prompt = new JTextArea(3, 20);
        this.prompt.setEditable(false);
        this.prompt.setLineWrap(true);
        this.prompt.setWrapStyleWord(true);
        this.prompt.setVisible(false);

        this.input = new JTextField();
        this.input.setVisible(false);

        this.sendButton = new JButton("Send");
        this.sendButton.setVisible(false);

        centralPanel.add(this.prompt);
        centralPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        centralPanel.add(this.input);
        centralPanel.add(Box.createRigidArea(new Dimension(0, 10)));
        centralPanel.add(this.sendButton);

        this.frame.add(centralPanel, BorderLayout.CENTER);
    }

    public void show() {
        this.frame.setSize(this.width, this.height);
        this.frame.setVisible(true);
    }

    public String getUsername(String promptMessage) {
        this.prompt.setText(promptMessage);
        this.prompt.setVisible(true);
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

        this.prompt.setVisible(false);
        this.input.setVisible(false);
        this.sendButton.setVisible(false);

        return username[0];
    }
}
