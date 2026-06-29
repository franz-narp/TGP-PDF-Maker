using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class Launcher {
    static void Main() {
        string appDir = AppDomain.CurrentDomain.BaseDirectory;
        string appPyPath = Path.Combine(appDir, "app.py");

        if (!File.Exists(appPyPath)) {
            MessageBox.Show("Error: app.py not found in the current directory:\n" + appDir, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        Console.Title = "TGP PDF Maker Launcher";
        Console.WriteLine("==================================================");
        Console.WriteLine("          TGP PDF Maker Launcher");
        Console.WriteLine("==================================================");

        // Check if venv/Scripts/python.exe exists
        string pythonExePath = "python";
        string venvPythonPath = Path.Combine(appDir, "venv", "Scripts", "python.exe");
        if (File.Exists(venvPythonPath)) {
            pythonExePath = venvPythonPath;
            Console.WriteLine("Using virtual environment Python: " + pythonExePath);
        } else {
            Console.WriteLine("Using system Python...");
        }

        Console.WriteLine("Starting Python application (app.py)...");

        ProcessStartInfo startInfo = new ProcessStartInfo();
        startInfo.FileName = pythonExePath;
        startInfo.Arguments = "app.py";
        startInfo.WorkingDirectory = appDir;
        startInfo.UseShellExecute = false;
        startInfo.RedirectStandardError = false;
        startInfo.RedirectStandardOutput = false;

        try {
            using (Process process = Process.Start(startInfo)) {
                Console.WriteLine("Python app started successfully!");
                Console.WriteLine("Press Ctrl+C or close this window to stop the server.");
                process.WaitForExit();
            }
        }
        catch (Exception ex) {
            // If we were trying to run global python and it failed, try 'py' instead
            if (pythonExePath == "python") {
                Console.WriteLine("python command failed. Retrying with 'py' command...");
                startInfo.FileName = "py";
                try {
                    using (Process process = Process.Start(startInfo)) {
                        Console.WriteLine("Python app started successfully!");
                        Console.WriteLine("Press Ctrl+C or close this window to stop the server.");
                        process.WaitForExit();
                        return;
                    }
                }
                catch (Exception ex2) {
                    ShowErrorDialog(ex2.Message);
                }
            } else {
                ShowErrorDialog(ex.Message);
            }
        }
    }

    static void ShowErrorDialog(string errorDetails) {
        MessageBox.Show(
            "Error: Could not launch Python.\n\n" +
            "Please ensure:\n" +
            "1. Python is installed.\n" +
            "2. Python is added to your system PATH (or a 'venv' folder exists in the project root).\n\n" +
            "Details: " + errorDetails,
            "Python Launcher Error",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        );
    }
}
