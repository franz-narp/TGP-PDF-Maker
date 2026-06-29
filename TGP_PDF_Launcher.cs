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

        string pythonExePath = "";
        string venvDir = Path.Combine(appDir, "venv");
        string venvPythonPath = Path.Combine(venvDir, "Scripts", "python.exe");

        if (File.Exists(venvPythonPath)) {
            pythonExePath = venvPythonPath;
            Console.WriteLine("Using virtual environment Python: " + pythonExePath);
        } else {
            Console.WriteLine("Virtual environment (venv) not found.");
            Console.WriteLine("Checking system Python for automatic dependency setup...");
            
            string sysPython = "";
            if (CheckCommandExists("python", appDir)) {
                sysPython = "python";
            } else if (CheckCommandExists("py", appDir)) {
                sysPython = "py";
            }

            if (!string.IsNullOrEmpty(sysPython)) {
                Console.WriteLine("System Python detected: " + sysPython);
                Console.WriteLine("Creating local virtual environment (venv) in: " + venvDir);
                Console.WriteLine("This setup runs only once on the first launch.");
                Console.WriteLine("Please wait...");
                Console.WriteLine("--------------------------------------------------");
                
                bool venvCreated = RunCommand(sysPython, "-m venv venv", appDir);
                if (venvCreated && File.Exists(venvPythonPath)) {
                    Console.WriteLine("--------------------------------------------------");
                    Console.WriteLine("Virtual environment created successfully.");
                    Console.WriteLine("Installing required libraries from requirements.txt...");
                    Console.WriteLine("--------------------------------------------------");
                    
                    bool pipInstalled = RunCommand(venvPythonPath, "-m pip install -r requirements.txt", appDir);
                    Console.WriteLine("--------------------------------------------------");
                    
                    if (pipInstalled) {
                        Console.WriteLine("Dependencies installed successfully!");
                        pythonExePath = venvPythonPath;
                    } else {
                        Console.WriteLine("Warning: Failed to install libraries. Trying global fallback...");
                    }
                } else {
                    Console.WriteLine("Warning: Failed to create virtual environment.");
                }
            } else {
                Console.WriteLine("No system Python detected in PATH.");
            }
        }

        if (string.IsNullOrEmpty(pythonExePath)) {
            pythonExePath = "python";
            Console.WriteLine("Using system Python fallback...");
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

    static bool CheckCommandExists(string command, string workingDir) {
        try {
            ProcessStartInfo startInfo = new ProcessStartInfo();
            startInfo.FileName = command;
            startInfo.Arguments = "--version";
            startInfo.WorkingDirectory = workingDir;
            startInfo.UseShellExecute = false;
            startInfo.RedirectStandardOutput = true;
            startInfo.RedirectStandardError = true;
            startInfo.CreateNoWindow = true;
            
            using (Process process = Process.Start(startInfo)) {
                if (process == null) return false;
                process.WaitForExit();
                return process.ExitCode == 0;
            }
        }
        catch {
            return false;
        }
    }

    static bool RunCommand(string fileName, string arguments, string workingDir) {
        try {
            ProcessStartInfo startInfo = new ProcessStartInfo();
            startInfo.FileName = fileName;
            startInfo.Arguments = arguments;
            startInfo.WorkingDirectory = workingDir;
            startInfo.UseShellExecute = false;
            startInfo.RedirectStandardOutput = false;
            startInfo.RedirectStandardError = false;
            
            using (Process process = Process.Start(startInfo)) {
                if (process == null) return false;
                process.WaitForExit();
                return process.ExitCode == 0;
            }
        }
        catch {
            return false;
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

