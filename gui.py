import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import asyncio
import threading
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Matplotlib nie jest zainstalowany. Wykresy będą wyłączone.")
    MATPLOTLIB_AVAILABLE = False
from collections import defaultdict
import time

class TaskListFrame(ttk.Frame):
    def __init__(self, parent, office_simulation):
        super().__init__(parent)
        self.office_simulation = office_simulation
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        ttk.Label(self, text="Task List", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Treeview for tasks
        columns = ("ID", "Title", "Status", "Agent", "Priority")
        self.task_tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        
        # Column configuration
        self.task_tree.heading("ID", text="ID")
        self.task_tree.heading("Title", text="Title")
        self.task_tree.heading("Status", text="Status")
        self.task_tree.heading("Agent", text="Agent")
        self.task_tree.heading("Priority", text="Priority")
        
        self.task_tree.column("ID", width=100)
        self.task_tree.column("Title", width=200)
        self.task_tree.column("Status", width=100)
        self.task_tree.column("Agent", width=150)
        self.task_tree.column("Priority", width=100)
        
        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Automatyczne odświeżanie listy zadań co 1 sekundę
        def auto_refresh_task_list():
            self.refresh_tasks()
            self.master.after(1000, auto_refresh_task_list)
        auto_refresh_task_list()
    
    def refresh_tasks(self):
        # Clear the list
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Add tasks
        for task in self.office_simulation.tasks.values():
            agent_name = "None"
            if task.assignee_id and task.assignee_id in self.office_simulation.agents:
                agent_name = self.office_simulation.agents[task.assignee_id].name
            
            # Status icons
            status_icons = {
                "PENDING": "⏳",
                "IN_PROGRESS": "🔄", 
                "COMPLETED": "✅",
                "FAILED": "❌",
                "BLOCKED": "🚫"
            }
            
            status_display = f"{status_icons.get(task.status.name, '❓')} {task.status.name}"
            
            self.task_tree.insert("", "end", values=(
                task.id[:8] + "...",
                task.title,
                status_display,
                agent_name,
                task.priority.name
            ))

class ResultsWindow:
    def __init__(self, parent, office_simulation):
        self.window = tk.Toplevel(parent)
        self.window.title("Final Results")
        self.window.geometry("800x600")
        self.office_simulation = office_simulation
        
        # Notebook for different result types
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Code tab
        self.code_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.code_frame, text="Code")
        self.code_text = scrolledtext.ScrolledText(self.code_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text tab
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="Text")
        self.text_widget = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save Code", command=self.save_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Text", command=self.save_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def show_results(self, task):
        try:
            # Sprawdź czy okno istnieje i jest aktywne
            if not hasattr(self, 'text_widget') or not self.text_widget.winfo_exists():
                return
            
            # Wyczyść poprzednie wyniki
            if hasattr(self, 'code_text') and self.code_text.winfo_exists():
                self.code_text.delete("1.0", tk.END)
            if hasattr(self, 'text_widget') and self.text_widget.winfo_exists():
                self.text_widget.delete("1.0", tk.END)
            
            # Show results
            results_text = f"=== TASK RESULTS: {task.title} ===\n\n"
            code_found = False
            
            for agent_id, result in task.results.items():
                agent_name = "Unknown agent"
                if agent_id in self.office_simulation.agents:
                    agent_name = self.office_simulation.agents[agent_id].name
                results_text += f"--- {agent_name} ---\n{result}\n\n"
                
                # Check if this is programmer's code (Alex Carter - Web Developer)
                if agent_name == "Alex Carter" and ("code" in result.lower() or "html" in result.lower() or "<!DOCTYPE" in result):
                    code_found = True
                    # Extract code from response - look for HTML code block
                    code_start = result.find("<!DOCTYPE")
                    if code_start == -1:
                        code_start = result.find("<html")
                    if code_start == -1:
                        code_start = result.find("=== HTML/CSS/JavaScript CODE ===")
                        if code_start != -1:
                            code_start = result.find("<!DOCTYPE", code_start)
                    
                    if code_start != -1:
                        # Find the end of the code block
                        code_end = result.find("=== TECHNICAL INFORMATION ===", code_start)
                        if code_end == -1:
                            code_end = result.find("Code has been generated by", code_start)
                        if code_end == -1:
                            code_end = len(result)
                        
                        actual_code = result[code_start:code_end].strip()
                        if hasattr(self, 'code_text') and self.code_text.winfo_exists():
                            self.code_text.insert("1.0", f"=== CODE GENERATED BY {agent_name} ===\n\n{actual_code}")
                    else:
                        # If no HTML found, show the entire result
                        if hasattr(self, 'code_text') and self.code_text.winfo_exists():
                            self.code_text.insert("1.0", f"=== CODE GENERATED BY {agent_name} ===\n\n{result}")
            
            if hasattr(self, 'text_widget') and self.text_widget.winfo_exists():
                self.text_widget.insert("1.0", results_text)
            
            # If no code found but this is a coding task, show default code
            if not code_found and ("code" in task.description.lower() or "html" in task.description.lower()):
                if hasattr(self, 'code_text') and self.code_text.winfo_exists():
                    self.code_text.insert("1.0", f"=== NO CODE FOUND ===\n\nThis task should have generated code but none was found.\n\n{results_text}")
        except Exception as e:
            print(f"Error displaying results: {e}")
    
    def save_code(self):
        filename = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.code_text.get("1.0", tk.END))
            messagebox.showinfo("Saved", f"Code saved to {filename}")
    
    def save_text(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.text_widget.get("1.0", tk.END))
            messagebox.showinfo("Saved", f"Text saved to {filename}")

class CodeResultsWindow:
    def __init__(self, parent, office_simulation):
        self.window = tk.Toplevel(parent)
        self.window.title("Generated Code")
        self.window.geometry("1000x700")
        self.office_simulation = office_simulation
        
        # Notebook for different code types
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # HTML tab
        self.html_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.html_frame, text="HTML")
        self.html_text = scrolledtext.ScrolledText(self.html_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.html_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CSS tab
        self.css_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.css_frame, text="CSS")
        self.css_text = scrolledtext.ScrolledText(self.css_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.css_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # JavaScript tab
        self.js_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.js_frame, text="JavaScript")
        self.js_text = scrolledtext.ScrolledText(self.js_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.js_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save HTML", command=lambda: self.save_code("html")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save CSS", command=lambda: self.save_code("css")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save JS", command=lambda: self.save_code("js")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def show_code(self, task):
        """Extract and display code from QWEN3 FINAL CODE (Integrator) if available, w przeciwnym razie z agentów CODER."""
        try:
            # Clear previous code
            if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                self.html_text.delete("1.0", tk.END)
            if hasattr(self, 'css_text') and self.css_text.winfo_exists():
                self.css_text.delete("1.0", tk.END)
            if hasattr(self, 'js_text') and self.js_text.winfo_exists():
                self.js_text.delete("1.0", tk.END)
            
            # Debug info
            print(f"DEBUG: show_code - task.results keys: {list(task.results.keys())}")
            print(f"DEBUG: show_code - task.results: {task.results}")
            
            # Szukaj kodu QWEN3 FINAL CODE od Integratora
            integrator_id = None
            for agent_id, agent in self.office_simulation.agents.items():
                if agent.role == "Integrator (Coordinator)":
                    integrator_id = agent_id
                    break
            
            print(f"DEBUG: show_code - integrator_id: {integrator_id}")
            
            qwen3_code = None
            if integrator_id and integrator_id in task.results:
                result = task.results[integrator_id]
                print(f"DEBUG: show_code - Integrator result: {result[:500]}...")  # First 500 chars
                if "=== QWEN3 FINAL CODE ===" in result:
                    qwen3_code = result.split("=== QWEN3 FINAL CODE ===", 1)[1]
                    print(f"DEBUG: show_code - Found QWEN3 code block: {qwen3_code[:200]}...")  # First 200 chars
                else:
                    print(f"DEBUG: show_code - No QWEN3 FINAL CODE block found in Integrator result")
            else:
                print(f"DEBUG: show_code - No Integrator result found")
            if qwen3_code:
                html = self._extract_qwen3_block(qwen3_code, "HTML CODE")
                css = self._extract_qwen3_block(qwen3_code, "CSS CODE")
                js = self._extract_qwen3_block(qwen3_code, "JAVASCRIPT CODE")
                if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                    self.html_text.insert("1.0", html or "<!-- No HTML code found in Qwen3 output -->")
                if hasattr(self, 'css_text') and self.css_text.winfo_exists():
                    self.css_text.insert("1.0", css or "/* No CSS code found in Qwen3 output */")
                if hasattr(self, 'js_text') and self.js_text.winfo_exists():
                    self.js_text.insert("1.0", js or "// No JavaScript code found in Qwen3 output")
                return
            # Jeśli nie ma QWEN3 FINAL CODE, wyświetl kod od agentów CODER
            coder_responses = []
            for agent_id, result in task.results.items():
                if agent_id in self.office_simulation.agents:
                    agent = self.office_simulation.agents[agent_id]
                    if hasattr(agent, 'agent_type') and agent.agent_type.name == 'CODER':
                        coder_responses.append((agent.name, result))
            if not coder_responses:
                if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                    self.html_text.insert("1.0", "No code found from any CODER agents (Alex Carter, Chris Nguyen, Riley Fox)")
                return
            combined_response = "\n\n".join([f"=== {name} ===\n{result}" for name, result in coder_responses])
            html_code = self._extract_html(combined_response)
            if html_code and html_code != "<!-- HTML code not found -->":
                if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                    self.html_text.insert("1.0", html_code)
            else:
                if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                    self.html_text.insert("1.0", "<!-- HTML code not found in CODER responses -->")
            css_code = self._extract_css(combined_response)
            if css_code and css_code != "/* CSS code not found */":
                if hasattr(self, 'css_text') and self.css_text.winfo_exists():
                    self.css_text.insert("1.0", css_code)
            else:
                if hasattr(self, 'css_text') and self.css_text.winfo_exists():
                    self.css_text.insert("1.0", "/* CSS code not found in CODER responses */")
            js_code = self._extract_js(combined_response)
            if js_code and js_code != "// JavaScript code not found":
                if hasattr(self, 'js_text') and self.js_text.winfo_exists():
                    self.js_text.insert("1.0", js_code)
            else:
                if hasattr(self, 'js_text') and self.js_text.winfo_exists():
                    self.js_text.insert("1.0", "// JavaScript code not found in CODER responses")
        except Exception as e:
            try:
                if hasattr(self, 'html_text') and self.html_text.winfo_exists():
                    self.html_text.insert("1.0", f"Error: {e}")
            except Exception:
                pass

    def _extract_qwen3_block(self, response, block_name):
        """Wyodrębnia blok kodu (HTML CODE, CSS CODE, JAVASCRIPT CODE) z odpowiedzi Qwen3"""
        import re
        pattern = rf"=== {block_name} ===\s*([\s\S]*?)(?===|$)"
        match = re.search(pattern, response)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_html(self, response):
        """Extract HTML code from response"""
        try:
            # Look for HTML code block - multiple patterns
            html_start = -1
            
            # Try different patterns
            patterns = [
                "=== HTML/CSS/JavaScript CODE ===",
                "<!DOCTYPE",
                "<html",
                "=== CODE GENERATED BY",
                "HTML/CSS/JavaScript CODE"
            ]
            
            for pattern in patterns:
                html_start = response.find(pattern)
                if html_start != -1:
                    break
            
            if html_start != -1:
                # Find the end of HTML (before CSS starts or end of response)
                html_end = response.find("<style>", html_start)
                if html_end == -1:
                    html_end = response.find("=== TECHNICAL INFORMATION ===", html_start)
                if html_end == -1:
                    html_end = response.find("Code has been generated by", html_start)
                if html_end == -1:
                    html_end = response.find("</html>", html_start)
                    if html_end != -1:
                        html_end += 7
                
                if html_end == -1:
                    html_end = len(response)
                
                html_code = response[html_start:html_end].strip()
                
                # If we found the marker but no actual HTML, look for HTML after it
                if "=== HTML/CSS/JavaScript CODE ===" in html_code:
                    # Find actual HTML after the marker
                    actual_html_start = html_code.find("<!DOCTYPE")
                    if actual_html_start == -1:
                        actual_html_start = html_code.find("<html")
                    if actual_html_start != -1:
                        html_code = html_code[actual_html_start:]
                
                return html_code
            return "<!-- HTML code not found -->"
        except Exception as e:
            return f"<!-- Error extracting HTML: {e} -->"
    
    def _extract_css(self, response):
        """Extract CSS code from response"""
        try:
            # Look for CSS code block - multiple patterns
            css_start = -1
            
            # Try different patterns
            patterns = [
                "<style>",
                "/* CSS */",
                "CSS code",
                "style {"
            ]
            
            for pattern in patterns:
                css_start = response.find(pattern)
                if css_start != -1:
                    break
            
            if css_start != -1:
                if response.find("<style>") != -1:
                    css_start = response.find("<style>") + 7
                    css_end = response.find("</style>", css_start)
                    if css_end == -1:
                        css_end = len(response)
                else:
                    # Look for end of CSS section
                    css_end = response.find("/* JavaScript */", css_start)
                    if css_end == -1:
                        css_end = response.find("<script>", css_start)
                    if css_end == -1:
                        css_end = response.find("</style>", css_start)
                    if css_end == -1:
                        css_end = len(response)
                
                css_code = response[css_start:css_end].strip()
                return css_code
            return "/* CSS code not found */"
        except Exception as e:
            return f"/* Error extracting CSS: {e} */"
    
    def _extract_js(self, response):
        """Extract JavaScript code from response"""
        try:
            # Look for JavaScript code block - multiple patterns
            js_start = -1
            
            # Try different patterns
            patterns = [
                "<script>",
                "/* JavaScript */",
                "JavaScript code",
                "// Smooth scrolling"
            ]
            
            for pattern in patterns:
                js_start = response.find(pattern)
                if js_start != -1:
                    break
            
            if js_start != -1:
                if response.find("<script>") != -1:
                    js_start = response.find("<script>") + 8
                    js_end = response.find("</script>", js_start)
                    if js_end == -1:
                        js_end = len(response)
                else:
                    # Look for end of JS section
                    js_end = response.find("</body>", js_start)
                    if js_end == -1:
                        js_end = response.find("</script>", js_start)
                    if js_end == -1:
                        js_end = response.find("</html>", js_start)
                    if js_end == -1:
                        js_end = len(response)
                
                js_code = response[js_start:js_end].strip()
                return js_code
            return "// JavaScript code not found"
        except Exception as e:
            return f"// Error extracting JavaScript: {e}"
    
    def save_code(self, code_type):
        """Save specific code type to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{code_type}", 
            filetypes=[(f"{code_type.upper()} files", f"*.{code_type}")]
        )
        if filename:
            try:
                if code_type == "html":
                    content = self.html_text.get("1.0", tk.END)
                elif code_type == "css":
                    content = self.css_text.get("1.0", tk.END)
                elif code_type == "js":
                    content = self.js_text.get("1.0", tk.END)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Saved", f"{code_type.upper()} code saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")

class OfficeGUI:
    def __init__(self, master, office_simulation, Agent, TaskPriority, asyncio, TaskStatus):
        self.master = master
        self.master.title("AI Agents Company Simulation")
        self.office_simulation = office_simulation
        self.Agent = Agent
        self.TaskPriority = TaskPriority
        self.asyncio = asyncio
        self.TaskStatus = TaskStatus
        self.agent_activity = defaultdict(int)
        self.task_status_counts = defaultdict(int)
        
        # System liczenia czasu pracy agentów
        self.agent_work_time = defaultdict(float)  # Całkowity czas pracy każdego agenta (w sekundach)
        self.agent_start_time = {}  # Czas rozpoczęcia pracy dla każdego agenta
        self.working_agents = set()  # Zbiór aktualnie pracujących agentów
        self.last_update_time = time.time()  # Ostatni czas aktualizacji
        
        self.results_window = None
        self.code_results_window = None
        self.setup_ui()
        if MATPLOTLIB_AVAILABLE:
            self.setup_charts()
            self.setup_task_status_chart() # Initialize the new chart window
        else:
            self.chart_window = None
        
        # Communication Log Frame
        self.communication_frame = ttk.LabelFrame(self.master, text="Communication Log")
        self.communication_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.communication_text = scrolledtext.ScrolledText(self.communication_frame, width=100, height=10, state="disabled")
        self.communication_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.communication_frame.columnconfigure(0, weight=1)
        self.communication_frame.rowconfigure(0, weight=1)
        
        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.rowconfigure(2, weight=1)
        
        # Add startup message to Communication Log
        self.update_communication_log("🚀 AI Agents Company program has been started")
        self.update_communication_log("👥 Initializing agents...")
    
    def setup_charts(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        # Charts window - initially hidden
        self.chart_window = tk.Toplevel(self.master)
        self.chart_window.title("Agent Work Time Distribution")
        self.chart_window.geometry("600x500")
        # Tylko wykres kołowy czasu pracy agentów
        self.fig, self.ax1 = plt.subplots(1, 1, figsize=(7, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ani = animation.FuncAnimation(self.fig, self.update_charts, interval=2000, save_count=100)
        try:
            self.update_charts(0)
            self.master.update()
        except Exception as e:
            print(f"Chart error: {e}")
        self.chart_window.withdraw()

    def update_charts(self, frame):
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'ax1'):
            return
        self.update_work_time()
        self.ax1.clear()
        agent_names = list(self.agent_work_time.keys())
        agent_times = list(self.agent_work_time.values())
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94']
        
        # Debug info
        print(f"DEBUG: update_charts - agent_names: {agent_names}")
        print(f"DEBUG: update_charts - agent_times: {agent_times}")
        print(f"DEBUG: update_charts - sum(agent_times): {sum(agent_times)}")
        
        if agent_names and sum(agent_times) > 0:
            total_time = sum(agent_times)
            wedges, texts, autotexts = self.ax1.pie(agent_times, labels=None, autopct='%1.1f%%', colors=colors[:len(agent_names)], startangle=90)
            self.ax1.set_title('Agent Work Time Distribution (%)', fontsize=14, fontweight='bold')
            self.ax1.legend(wedges, agent_names, title="Agents", loc="center left", bbox_to_anchor=(1, 0.5))
            for autotext in autotexts:
                autotext.set_fontweight('bold')
            total_minutes = total_time / 60
            working_count = len(self.working_agents)
            info_text = f'Total Work Time: {total_minutes:.1f} min\nCurrently Working: {working_count} agents'
            self.ax1.text(0.02, 0.98, info_text, transform=self.ax1.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        else:
            self.ax1.text(0.5, 0.5, 'No agent work time yet', ha='center', va='center', transform=self.ax1.transAxes, fontsize=12)
            self.ax1.set_title('Agent Work Time Distribution (%)', fontsize=14, fontweight='bold')
        self.fig.tight_layout()
        self.canvas.draw()

    def setup_task_status_chart(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        self.task_status_chart_window = tk.Toplevel(self.master)
        self.task_status_chart_window.title("Task Status Distribution")
        self.task_status_chart_window.geometry("600x400")
        self.status_fig, self.status_ax = plt.subplots(1, 1, figsize=(7, 4))
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, self.task_status_chart_window)
        self.status_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_task_status_chart()
        self.task_status_chart_window.withdraw()

    def update_task_status_chart(self):
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'status_ax'):
            return
        self.status_ax.clear()
        status_names = list(self.task_status_counts.keys())
        status_counts = list(self.task_status_counts.values())
        if status_names and sum(status_counts) > 0:
            total_status = sum(status_counts)
            percentages = [(count / total_status) * 100 for count in status_counts]
            bars = self.status_ax.bar(status_names, status_counts, color='#ff9999')
            self.status_ax.set_title('Task Status Distribution', fontsize=14, fontweight='bold')
            self.status_ax.set_ylabel('Number of Tasks', fontsize=12)
            self.status_ax.set_xlabel('Status', fontsize=12)
            for i, (bar, percentage) in enumerate(zip(bars, percentages)):
                height = bar.get_height()
                self.status_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{percentage:.1f}%', ha='center', va='bottom', fontweight='bold')
            self.status_ax.tick_params(axis='x', rotation=45)
        else:
            self.status_ax.text(0.5, 0.5, 'No tasks yet', ha='center', va='center', transform=self.status_ax.transAxes, fontsize=12)
            self.status_ax.set_title('Task Status Distribution', fontsize=14, fontweight='bold')
        self.status_fig.tight_layout()
        self.status_canvas.draw()

    def update_agent_activity(self, agent_name):
        """Aktualizuje licznik aktywności agenta i rozpoczyna liczenie czasu pracy"""
        self.agent_activity[agent_name] += 1
        self.start_agent_work(agent_name)
    
    def start_agent_work(self, agent_name):
        """Rozpoczyna liczenie czasu pracy dla agenta"""
        if agent_name not in self.working_agents:
            self.agent_start_time[agent_name] = time.time()
            self.working_agents.add(agent_name)
            msg = f"🟢 START: {agent_name} rozpoczął pracę o {self.agent_start_time[agent_name]:.2f}"
            print(msg)
            self.update_task_status(msg)
            # Debug info
            print(f"DEBUG: start_agent_work - {agent_name} added to working_agents: {self.working_agents}")
            print(f"DEBUG: start_agent_work - agent_start_time: {self.agent_start_time}")
    
    def stop_agent_work(self, agent_name):
        """Kończy liczenie czasu pracy dla agenta"""
        if agent_name in self.working_agents:
            if agent_name in self.agent_start_time:
                work_duration = time.time() - self.agent_start_time[agent_name]
                self.agent_work_time[agent_name] += work_duration
                msg = f"🔴 STOP: {agent_name} zakończył pracę, czas: {work_duration:.2f}s, suma: {self.agent_work_time[agent_name]:.2f}s"
                print(msg)
                self.update_task_status(msg)
            self.working_agents.discard(agent_name)
            if agent_name in self.agent_start_time:
                del self.agent_start_time[agent_name]
            # Debug info
            print(f"DEBUG: stop_agent_work - {agent_name} removed from working_agents: {self.working_agents}")
            print(f"DEBUG: stop_agent_work - agent_work_time: {self.agent_work_time}")
    
    def update_work_time(self):
        """Aktualizuje czas pracy dla aktualnie pracujących agentów"""
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        # Aktualizuj czas pracy dla pracujących agentów
        for agent_name in list(self.working_agents):
            if agent_name in self.agent_start_time:
                self.agent_work_time[agent_name] += time_diff
        
        self.last_update_time = current_time
        
        # Debug info
        if self.working_agents:
            print(f"DEBUG: update_work_time - working_agents: {self.working_agents}")
            print(f"DEBUG: update_work_time - agent_work_time: {self.agent_work_time}")
    
    def get_agent_work_time_percentage(self):
        """Oblicza procent czasu pracy każdego agenta"""
        self.update_work_time()  # Aktualizuj czas przed obliczeniami
        
        total_time = sum(self.agent_work_time.values())
        if total_time == 0:
            return {}
        
        percentages = {}
        for agent_name, work_time in self.agent_work_time.items():
            percentages[agent_name] = (work_time / total_time) * 100
        return percentages
    
    def update_task_status_counts(self):
        self.task_status_counts.clear()
        for task in self.office_simulation.tasks.values():
            self.task_status_counts[task.status.name] += 1
    
    def get_agent_work_percentage(self):
        """Calculate percentage of work done by each agent"""
        total_tasks = sum(self.agent_activity.values())
        if total_tasks == 0:
            return {}
        
        percentages = {}
        for agent_name, count in self.agent_activity.items():
            percentages[agent_name] = (count / total_tasks) * 100
        return percentages

    def setup_ui(self):
        # Task Submission Frame
        task_frame = ttk.LabelFrame(self.master, text="Task Submission")
        task_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(task_frame, text="Title:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.task_title_entry = ttk.Entry(task_frame, width=40)
        self.task_title_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(task_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.task_description_text = scrolledtext.ScrolledText(task_frame, width=40, height=5)
        self.task_description_text.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(task_frame, text="Priority:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.task_priority_combo = ttk.Combobox(task_frame, values=[e.name for e in self.TaskPriority], state="readonly")
        self.task_priority_combo.set(self.TaskPriority.MEDIUM.name)
        self.task_priority_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.submit_button = ttk.Button(task_frame, text="Submit Task", command=self.submit_task)
        self.submit_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")
        
        # Agent Information Frame
        agent_frame = ttk.LabelFrame(self.master, text="Agent Information")
        agent_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        agent_frame.columnconfigure(0, weight=1)
        agent_frame.columnconfigure(1, weight=2)
        agent_frame.rowconfigure(2, weight=1)

        # Lista agentów
        self.agent_listbox = tk.Listbox(agent_frame, width=25, font=("Arial", 11), exportselection=False)
        self.agent_listbox.grid(row=0, column=0, rowspan=3, padx=(8, 8), pady=8, sticky="ns")

        # Etykieta roli agenta (na środku nad umiejętnościami)
        self.agent_role_label = tk.Label(agent_frame, text="", font=("Arial", 12, "bold"), bg="#f0f4ff", anchor="center")
        self.agent_role_label.grid(row=0, column=1, padx=5, pady=(10, 2), sticky="ew")

        # Ramka na umiejętności
        skills_frame = tk.Frame(agent_frame, bg="#e6e6e6", bd=1, relief="solid")
        skills_frame.grid(row=1, column=1, padx=5, pady=(0, 8), sticky="nsew")
        skills_frame.rowconfigure(0, weight=1)
        skills_frame.columnconfigure(0, weight=1)

        self.skills_listbox = tk.Listbox(skills_frame, width=35, font=("Arial", 11), bd=0, highlightthickness=0)
        self.skills_listbox.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        agent_frame.rowconfigure(1, weight=1)
        agent_frame.rowconfigure(2, weight=1)

        # Kolory dla ról
        self.agent_colors = {}
        for agent in self.office_simulation.agents.values():
            if agent.role.lower() in ["ceo", "boss", "szef"]:
                self.agent_colors[agent.name] = "#FFD700"  # złoty
            elif "web" in agent.role.lower() or "developer" in agent.role.lower():
                self.agent_colors[agent.name] = "#87CEEB"  # niebieski
            elif "analyst" in agent.role.lower() or "programmer" in agent.role.lower():
                self.agent_colors[agent.name] = "#90EE90"  # zielony
            elif "image" in agent.role.lower() or "generator" in agent.role.lower():
                self.agent_colors[agent.name] = "#FFB6C1"  # różowy
            elif "text" in agent.role.lower():
                self.agent_colors[agent.name] = "#E6E6FA"  # fioletowy
            else:
                self.agent_colors[agent.name] = "#F0F0F0"  # szary

        # Wypełnij listę agentów
        self.agent_names = [agent.name for agent in self.office_simulation.agents.values()]
        for name in self.agent_names:
            self.agent_listbox.insert(tk.END, name)

        def show_skills(event):
            selection = self.agent_listbox.curselection()
            if selection:
                idx = selection[0]
                agent_name = self.agent_names[idx]
                agent = next(a for a in self.office_simulation.agents.values() if a.name == agent_name)
                self.skills_listbox.delete(0, tk.END)
                for skill in agent.skills:
                    self.skills_listbox.insert(tk.END, skill)
                self.skills_listbox.config(bg=self.agent_colors[agent_name])
                # Rola na środku, pogrubiona
                self.agent_role_label.config(text=f"Rola: {agent.role}")
        self.agent_listbox.bind("<<ListboxSelect>>", show_skills)

        # Domyślnie pokaż umiejętności pierwszego agenta
        if self.agent_names:
            self.agent_listbox.selection_set(0)
            self.agent_listbox.event_generate("<<ListboxSelect>>")

        # Usuwam stary widget agent_info_text
        # self.agent_info_text = scrolledtext.ScrolledText(agent_frame, width=50, height=10, state="disabled")
        # self.agent_info_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Task Status Frame
        task_status_frame = ttk.LabelFrame(self.master, text="Task Status")
        task_status_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        # Task Status Text with improved scrollbar configuration
        self.task_status_text = scrolledtext.ScrolledText(
            task_status_frame, 
            width=50, 
            height=20, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.task_status_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Grid configuration for better scrolling
        task_status_frame.columnconfigure(0, weight=1)
        task_status_frame.rowconfigure(0, weight=1)
        
        # Task List Frame
        task_list_frame = ttk.LabelFrame(self.master, text="Task List")
        task_list_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        self.task_list = TaskListFrame(task_list_frame, self.office_simulation)
        self.task_list.pack(fill=tk.BOTH, expand=True)
        
        # Save/Load state buttons
        button_frame = ttk.Frame(self.master)
        button_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        save_btn = ttk.Button(button_frame, text="Save State", command=self.save_state)
        save_btn.grid(row=0, column=0, padx=5)
        load_btn = ttk.Button(button_frame, text="Load State", command=self.load_state)
        load_btn.grid(row=0, column=1, padx=5)
        results_btn = ttk.Button(button_frame, text="Show Results", command=self.show_results)
        results_btn.grid(row=0, column=2, padx=5)
        code_btn = ttk.Button(button_frame, text="Show Code", command=self.show_code)
        code_btn.grid(row=0, column=3, padx=5)
        charts_btn = ttk.Button(button_frame, text="Show Charts", command=self.show_charts)
        charts_btn.grid(row=0, column=4, padx=5)
        task_status_btn = ttk.Button(button_frame, text="Show Task Status Chart", command=self.show_task_status_chart)
        task_status_btn.grid(row=0, column=6, padx=5)
        reset_btn = ttk.Button(button_frame, text="Reset Work Time", command=self.reset_work_time)
        reset_btn.grid(row=0, column=5, padx=5)
        
        # Przyciski agentów
        agent_buttons_frame = ttk.Frame(self.master)
        agent_buttons_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")
        
        # Przyciski dla każdego agenta z odpowiednimi ikonami
        self.agent_buttons = {}
        for i, (agent_id, agent) in enumerate(self.office_simulation.agents.items()):
            # Wybierz ikonę na podstawie roli agenta
            if agent.role.lower() in ["ceo", "boss", "szef", "integrator", "coordinator"]:
                icon = "👑"
            elif agent.role.lower() in ["web developer", "developer", "coder", "programista", "hosting", "devops", "mobile"]:
                icon = "💻"
            elif agent.role.lower() in ["data analyst", "analyst", "analityk"]:
                icon = "📊"
            elif agent.role.lower() in ["ux/ui designer", "designer", "ai graphic designer", "graphic"]:
                icon = "🎨"
            elif agent.role.lower() in ["copywriter", "writer", "text analyst", "analityk tekstu", "client advisor"]:
                icon = "📝"
            elif agent.role.lower() in ["marketing strategist", "marketing"]:
                icon = "📈"
            elif agent.role.lower() in ["project manager", "pm"]:
                icon = "📋"
            elif agent.role.lower() in ["ai chatbot", "chatbot"]:
                icon = "🤖"
            elif agent.role.lower() in ["feedback", "qa", "testing"]:
                icon = "🔍"
            else:
                icon = "👤"
            
            btn = ttk.Button(agent_buttons_frame, text=f"{icon} {agent.name}", 
                           command=lambda a=agent: self.show_agent_view(a))
            btn.grid(row=0, column=i, padx=5)
            self.agent_buttons[agent_id] = btn
        
        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.rowconfigure(2, weight=1)
        task_frame.columnconfigure(1, weight=1)
        agent_frame.columnconfigure(0, weight=1)
        task_status_frame.columnconfigure(0, weight=1)
        task_status_frame.rowconfigure(0, weight=1)
        
        # Dodaj obsługę resize dla lepszego scrollowania
        self.master.bind('<Configure>', self.on_resize)
    
    def submit_task(self):
        title = self.task_title_entry.get()
        description = self.task_description_text.get("1.0", tk.END)
        priority = self.TaskPriority[self.task_priority_combo.get()]
        
        # Create a new event loop in a separate thread
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.submit_task_async(title, description, priority))
        
        thread = threading.Thread(target=run_async)
        thread.start()
        
        # Bring window to front and focus
        self.master.lift()
        self.master.focus_force()
        
        # Odśwież listę tasków
        self.task_list.refresh_tasks()
    
    async def submit_task_async(self, title, description, priority):
        result = await self.office_simulation.submit_task(title, description, priority)
        self.update_task_status(f"Task Submission Result: {result}")
        # Odśwież listę tasków po dodaniu
        self.task_list.refresh_tasks()
    
    def update_task_status(self, status):
        # Enable text widget for editing
        self.task_status_text.config(state="normal")
        self.task_status_text.insert(tk.END, status + "\n")
        # Dodaj graficzne podsumowanie pracy agentów, jeśli status dotyczy zakończonego zadania
        if status.startswith("✅ Task") or status.startswith("\n=== FINAL REPORT ==="):
            summary = self._generate_agents_summary()
            if summary:
                self.task_status_text.insert(tk.END, summary + "\n")
        # Disable text widget to prevent user editing
        self.task_status_text.config(state="disabled")
        # Ensure we can see the latest text
        self.task_status_text.see(tk.END)
        # Force update of scrollbar
        self._refresh_scrollbars()
        # Aktualizuj wykresy
        self.update_task_status_counts()
        # Animacja przy aktualizacji statusu
        self.animate_status_update()
        # Odśwież listę tasków
        self.task_list.refresh_tasks()
        # Przewiń na dół
        self.task_status_text.yview_moveto(1.0)
        # Odśwież wykresy
        if hasattr(self, 'update_charts'):
            self.update_charts(0)
        if hasattr(self, 'update_task_status_chart'):
            self.update_task_status_chart()

    def _generate_agents_summary(self):
        """Tworzy krótkie, graficzne podsumowanie pracy agentów (RoboAssist)"""
        if not hasattr(self, 'office_simulation') or not self.office_simulation:
            return ""
        completed_tasks = [task for task in self.office_simulation.tasks.values() if task.status.name == "COMPLETED"]
        if not completed_tasks:
            return ""
        latest_task = max(completed_tasks, key=lambda t: t.completed_at or 0)
        summary = "\n🤖 RoboAssist: Podsumowanie pracy zespołu:\n"
        agent_icons = {
            "Web Developer": "💻",
            "Hosting/DevOps": "💻",
            "Mobile Responsiveness & Testing Agent": "💻",
            "UX/UI Designer": "🎨",
            "AI Graphic Designer": "🎨",
            "Copywriter": "📝",
            "Client Advisor": "📝",
            "Marketing Strategist": "📈",
            "Project Manager": "📋",
            "Integrator (Coordinator)": "👑",
            "Data Analyst": "📊",
            "AI Chatbot": "🤖",
            "Feedback & QA Agent": "🔍"
        }
        for agent_id, result in latest_task.results.items():
            agent = self.office_simulation.agents.get(agent_id)
            if not agent:
                continue
            icon = agent_icons.get(agent.role, "👤")
            short = result.split("\n")[0][:60]  # Pierwsza linia wyniku
            summary += f"{icon} {agent.name} ({agent.role}): {short}...\n"
        summary += "\n"
        return summary

    def animate_status_update(self):
        # Prosta animacja - zmiana koloru tła
        original_bg = self.task_status_text.cget("bg")
        self.task_status_text.config(bg="lightgreen")
        self.master.after(200, lambda: self.task_status_text.config(bg=original_bg))
    
    def update_communication_log(self, message):
        try:
            # Dodaj timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            self.communication_text.config(state="normal")
            self.communication_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.communication_text.config(state="disabled")
            self.communication_text.see(tk.END)
            
            # Animacja przy komunikacji
            self.animate_communication()
            
        except Exception as e:
            print(f"Błąd podczas aktualizacji Communication Log: {e}")
    
    def animate_communication(self):
        # Animacja - podświetlenie komunikacji
        original_bg = self.communication_text.cget("bg")
        self.communication_text.config(bg="lightblue")
        self.master.after(300, lambda: self.communication_text.config(bg=original_bg))

    def save_state(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            self.office_simulation.save_all(filename)
            self.update_task_status(f"Stan zapisany do pliku: {filename}")

    def load_state(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.office_simulation.load_all(filename)
            self.update_task_status(f"Stan wczytany z pliku: {filename}")
            # Odśwież info o agentach
            agent_info = "\n".join([f"{agent.name} ({agent.role}): {agent.skills}" for agent in self.office_simulation.agents.values()])
            self.update_agent_info(agent_info)
            # Odśwież listę tasków
            self.task_list.refresh_tasks()
    
    def show_results(self):
        # Show window with results of the latest completed task
        completed_tasks = [task for task in self.office_simulation.tasks.values() if task.status == self.TaskStatus.COMPLETED]
        if completed_tasks:
            latest_task = max(completed_tasks, key=lambda t: t.completed_at or 0)
            if not self.results_window:
                self.results_window = ResultsWindow(self.master, self.office_simulation)
            self.results_window.show_results(latest_task)
        else:
            messagebox.showinfo("No Results", "There are no completed tasks yet.")
    
    def show_charts(self):
        # Show activity charts window
        if not self.chart_window or not self.chart_window.winfo_exists():
            self.setup_charts()
        self.chart_window.deiconify()
        self.chart_window.lift()
        # Force update charts
        if hasattr(self, 'update_charts'):
            self.update_charts(0)

    def show_task_status_chart(self):
        if not self.task_status_chart_window or not self.task_status_chart_window.winfo_exists():
            self.setup_task_status_chart()
        self.task_status_chart_window.deiconify()
        self.task_status_chart_window.lift()

    def show_code(self):
        # Show window with code generated by CODER agents
        completed_tasks = [task for task in self.office_simulation.tasks.values() if task.status == self.TaskStatus.COMPLETED]
        if completed_tasks:
            latest_task = max(completed_tasks, key=lambda t: t.completed_at or 0)
            # Twórz nowe okno jeśli nie istnieje lub zostało zamknięte
            if not self.code_results_window or not self.code_results_window.html_text.winfo_exists():
                self.code_results_window = CodeResultsWindow(self.master, self.office_simulation)
            self.code_results_window.show_code(latest_task)
        else:
            messagebox.showinfo("No Code", "There are no completed tasks with code yet.")

    def reset_work_time(self):
        """Reset the work time for all agents to 0."""
        self.agent_work_time.clear()
        self.working_agents.clear()
        self.agent_start_time.clear()
        self.last_update_time = time.time()
        self.update_task_status("⏰ Work time reset for all agents.")
        if hasattr(self, 'update_charts'):
            self.update_charts(0)  # Update charts to reflect reset
        if hasattr(self, 'update_task_status_chart'):
            self.update_task_status_chart()

    def bring_to_front(self):
        """Bring the main window to front and focus"""
        try:
            self.master.lift()
            self.master.focus_force()
            self.master.attributes('-topmost', True)
            self.master.after(1000, lambda: self.master.attributes('-topmost', False))
        except Exception as e:
            print(f"Error bringing window to front: {e}")
    
    def show_agent_view(self, agent):
        """Show specific agent view"""
        try:
            # Create new window for agent
            agent_window = tk.Toplevel(self.master)
            agent_window.title(f"Agent View: {agent.name}")
            agent_window.geometry("800x600")
            
            # Agent information
            info_frame = ttk.LabelFrame(agent_window, text="Agent Information")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            info_text = f"Name: {agent.name}\n"
            info_text += f"Role: {agent.role}\n"
            info_text += f"Skills: {', '.join(agent.skills)}\n"
            info_text += f"Traits: {', '.join(agent.personality_traits)}\n"
            info_text += f"Tools: {', '.join(agent.preferred_tools)}"
            
            ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=5, pady=5)
            
            # Special view for CEO/Integrator
            if agent.name == "Pat Morgan":
                self._show_ceo_view(agent_window, agent)
            else:
                # Regular agent tasks view
                self._show_regular_agent_view(agent_window, agent)
            
        except Exception as e:
            print(f"Error creating agent view: {e}")
            messagebox.showerror("Error", f"Cannot display agent view: {e}")
    
    def _show_ceo_view(self, window, agent):
        """Show special Integrator view with coordination work"""
        # Integrator Coordination Frame
        coordination_frame = ttk.LabelFrame(window, text="Integrator Coordination Work")
        coordination_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        coordination_text = scrolledtext.ScrolledText(coordination_frame, wrap=tk.WORD, font=("Consolas", 10))
        coordination_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Find Integrator's work (tasks where he is the creator or has results)
        integrator_work = []
        for task in self.office_simulation.tasks.values():
            if task.creator_id == agent.id or agent.id in task.results:
                integrator_work.append(task)
        
        if integrator_work:
            coordination_text.insert(tk.END, f"=== {agent.name} - INTEGRATOR COORDINATION WORK ===\n\n")
            
            for task in integrator_work:
                coordination_text.insert(tk.END, f"📋 PROJECT: {task.title}\n")
                coordination_text.insert(tk.END, f"📄 Description: {task.description}\n")
                coordination_text.insert(tk.END, f"🎯 Priority: {task.priority.name}\n")
                coordination_text.insert(tk.END, f"📊 Status: {task.status.name}\n")
                
                if agent.id in task.results:
                    coordination_text.insert(tk.END, f"\n📝 INTEGRATOR SUMMARY:\n{task.results[agent.id]}\n")
                
                coordination_text.insert(tk.END, "\n" + "="*50 + "\n\n")
        else:
            coordination_text.insert(tk.END, f"No coordination work found for {agent.name} yet.\n")
            coordination_text.insert(tk.END, "Integrator will coordinate tasks when projects are submitted.\n")
        
        coordination_text.config(state="disabled")
    
    def _show_regular_agent_view(self, window, agent):
        """Show regular agent view with their tasks"""
        # Agent tasks
        tasks_frame = ttk.LabelFrame(window, text="Agent Tasks")
        tasks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tasks_text = scrolledtext.ScrolledText(tasks_frame, wrap=tk.WORD)
        tasks_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Find tasks for this agent
        agent_tasks = []
        for task in self.office_simulation.tasks.values():
            if task.assignee_id == agent.id:
                agent_tasks.append(task)
        
        if agent_tasks:
            for task in agent_tasks:
                tasks_text.insert(tk.END, f"Task: {task.title}\n")
                tasks_text.insert(tk.END, f"Status: {task.status.name}\n")
                tasks_text.insert(tk.END, f"Description: {task.description}\n")
                if task.results and agent.id in task.results:
                    tasks_text.insert(tk.END, f"Result: {task.results[agent.id]}\n")
                tasks_text.insert(tk.END, "-" * 50 + "\n\n")
        else:
            tasks_text.insert(tk.END, "No tasks for this agent.")
        
        tasks_text.config(state="disabled")
    
    def on_resize(self, event):
        """Handle window resize"""
        try:
            # Wait a bit for the resize to complete
            self.master.after(100, self._refresh_scrollbars)
        except Exception as e:
            print(f"Error handling resize: {e}")
    
    def _refresh_scrollbars(self):
        """Refresh all scrollbars after resize"""
        try:
            # Refresh Task Status scrollbar
            if hasattr(self, 'task_status_text'):
                self.task_status_text.update_idletasks()
                self.task_status_text.see(tk.END)
                # Force scrollbar to update
                self.task_status_text.yview_moveto(1.0)
            
            # Refresh Communication Log scrollbar
            if hasattr(self, 'communication_text'):
                self.communication_text.update_idletasks()
                self.communication_text.see(tk.END)
                self.communication_text.yview_moveto(1.0)
                
        except Exception as e:
            print(f"Error refreshing scrollbars: {e}")

def run_gui(office_simulation, Agent, TaskPriority, asyncio, TaskStatus):
    root = tk.Tk()
    gui = OfficeGUI(root, office_simulation, Agent, TaskPriority, asyncio, TaskStatus)
    
    # Example agent info (replace with actual data)
    
    # Set up periodic task status updates
    def update_gui():
        # Aktualizuj czas pracy agentów
        if hasattr(gui, 'update_work_time'):
            gui.update_work_time()
        root.after(100, update_gui)  # Schedule next update
    
    update_gui()  # Start the update loop
    root.mainloop()

if __name__ == '__main__':
    # Example Usage (for testing the GUI)
    from main import OfficeSimulation, Agent, TaskPriority, asyncio, TaskStatus
    office = OfficeSimulation()
    
    boss = Agent(
        id="boss1",
        name="Eleanor Wells",
        role="CEO",
        skills=["leadership", "decision-making", "critical thinking"],
        personality_traits=["decisive", "strategic"],
        preferred_tools=["executive dashboard", "communication platform"],
        collaborators=[]
    )
    
    analyst = Agent(
        id="analyst1",
        name="David Chen",
        role="Data Analyst",
        skills=["data analysis", "statistics", "python"],
        personality_traits=["analytical", "detail-oriented"],
        preferred_tools=["pandas", "scikit-learn", "tableau"],
        collaborators=["researcher1"],
        reports_to="boss1"
    )
    
    researcher = Agent(
        id="researcher1",
        name="Maria Rodriguez",
        role="Research Specialist",
        skills=["research", "literature review", "trend analysis"],
        personality_traits=["curious", "thorough"],
        preferred_tools=["academic databases", "research tools"],
        collaborators=["analyst1"],
        reports_to="boss1"
    )
    
    office.add_agent(boss, is_boss=True)
    office.add_agent(analyst)
    office.add_agent(researcher)
    
    run_gui(office, Agent, TaskPriority, asyncio, TaskStatus)
