import tkinter as tk
from tkinter import ttk, scrolledtext

class OfficeGUI:
    def __init__(self, master, office_simulation, Agent, TaskPriority, asyncio, TaskStatus):
        self.master = master
        self.master.title("AI Agents Company Simulation")
        self.office_simulation = office_simulation
        self.Agent = Agent
        self.TaskPriority = TaskPriority
        self.asyncio = asyncio
        self.TaskStatus = TaskStatus
        
        self.setup_ui()
        
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
        self.master.rowconfigure(2, weight=1) # Add weight for communication frame
    
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
        agent_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.agent_info_text = scrolledtext.ScrolledText(agent_frame, width=50, height=10, state="disabled")
        self.agent_info_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Task Status Frame
        task_status_frame = ttk.LabelFrame(self.master, text="Task Status")
        task_status_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        self.task_status_text = scrolledtext.ScrolledText(task_status_frame, width=50, height=20, state="disabled")
        self.task_status_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        task_frame.columnconfigure(1, weight=1)
        agent_frame.columnconfigure(0, weight=1)
        task_status_frame.columnconfigure(0, weight=1)
        task_status_frame.rowconfigure(0, weight=1)
    
    def submit_task(self):
        title = self.task_title_entry.get()
        description = self.task_description_text.get("1.0", tk.END)
        priority = self.TaskPriority[self.task_priority_combo.get()]
        
        self.asyncio.run(self.submit_task_async(title, description, priority))
    
    async def submit_task_async(self, title, description, priority):
        result = await self.office_simulation.submit_task(title, description)
        self.update_task_status(f"Task Submission Result: {result}")
    
    def update_agent_info(self, info):
        self.agent_info_text.config(state="normal")
        self.agent_info_text.delete("1.0", tk.END)
        self.agent_info_text.insert(tk.END, info)
        self.agent_info_text.config(state="disabled")
    
    def update_task_status(self, status):
        self.task_status_text.config(state="normal")
        self.task_status_text.delete("1.0", tk.END)
        self.task_status_text.insert(tk.END, status)
        self.task_status_text.config(state="disabled")
    
    def update_communication_log(self, message):
        self.communication_text.config(state="normal")
        self.communication_text.insert(tk.END, message + "\n")
        self.communication_text.config(state="disabled")
        self.communication_text.see(tk.END)

def run_gui(office_simulation, Agent, TaskPriority, asyncio, TaskStatus):
    root = tk.Tk()
    gui = OfficeGUI(root, office_simulation, Agent, TaskPriority, asyncio, TaskStatus)
    
    # Example agent info (replace with actual data)
    agent_info = "\n".join([f"{agent.name} ({agent.role}): {agent.skills}" for agent in office_simulation.agents.values()])
    gui.update_agent_info(agent_info)
    
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
