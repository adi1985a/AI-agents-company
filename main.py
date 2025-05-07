import uuid
import time
import random
import asyncio
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from gui import run_gui # Removing circular import

# Enums for task status and priority
class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    BLOCKED = auto()
    COMPLETED = auto()
    FAILED = auto()

class TaskPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

# Data structures
@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    creator_id: str = ""
    assignee_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: Set[str] = field(default_factory=set)
    subtasks: List[str] = field(default_factory=list)
    parent_task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    content: str = ""
    task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    read_at: Optional[float] = None

@dataclass
class Agent:
    id: str
    name: str
    role: str
    skills: List[str]
    personality_traits: List[str]
    preferred_tools: List[str]
    collaborators: List[str]
    reports_to: Optional[str] = None
    receives_from: List[str] = field(default_factory=list)
    current_task_id: Optional[str] = None
    task_history: List[str] = field(default_factory=list)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)

    async def process_task(self, task: Task) -> Task:
        """Process the assigned task and return the updated task with results"""
        # Log task processing
        if office and office.gui:
            office.gui.update_task_status(f"{self.name} is processing task {task.id}...")
        
        # Simulate processing time
        processing_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(processing_time)
        # Generate result based on agent's role and skills
        result = f"Result from {self.name} ({self.role}): Analysis complete"
        task.results[self.id] = result
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.updated_at = time.time()
        
        # Log task completion
        if office and office.gui:
             office.gui.update_task_status(f"{self.name} completed task {task.id} with result: {result}")
        
        return task

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Process incoming message and optionally respond"""
        # Simply acknowledge receipt
        if message.content.startswith("REQUEST:"):
            response_content = f"ACKNOWLEDGE: {message.content[8:]} - From {self.name}"
            
            # Log the communication
            if office and office.gui:
                office.gui.update_communication_log(f"Message from {self.name} to {office.agents[message.recipient_id].name}: {response_content}")
            
            return Message(
                sender_id=self.id,
                recipient_id=message.sender_id,
                content=response_content,
                task_id=message.task_id
            )
        return None

class CommunicationBus:
    def __init__(self):
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, Agent] = {}

    def subscribe(self, agent: Agent):
        """Register an agent to receive messages"""
        self.subscribers[agent.id] = agent

    async def publish(self, message: Message):
        """Publish a message to the communication bus"""
        # Log the communication
        if office and office.gui and message.sender_id in self.subscribers and message.recipient_id in self.subscribers:
            sender_name = self.subscribers[message.sender_id].name
            recipient_name = self.subscribers[message.recipient_id].name
            office.gui.update_communication_log(f"Message from {sender_name} to {recipient_name}: {message.content}")
        
        await self.message_queue.put(message)

    async def start(self):
        """Start processing messages"""
        while True:
            message = await self.message_queue.get()
            if message.recipient_id in self.subscribers:
                agent = self.subscribers[message.recipient_id]
                response = await agent.handle_message(message)
                if response:
                    await self.publish(response)
            self.message_queue.task_done()

class TaskManager:
    def __init__(self, communication_bus: CommunicationBus):
        self.tasks: Dict[str, Task] = {}
        self.agent_skills: Dict[str, List[str]] = {}
        self.communication_bus = communication_bus

    def register_agent(self, agent: Agent):
        """Register an agent's skills for task assignment"""
        self.agent_skills[agent.id] = agent.skills

    def create_task(self, title: str, description: str, creator_id: str, 
                   priority: TaskPriority = TaskPriority.MEDIUM) -> Task:
        """Create a new task"""
        task = Task(
            title=title,
            description=description,
            creator_id=creator_id,
            priority=priority
        )
        self.tasks[task.id] = task
        return task

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent"""
        if task_id not in self.tasks or agent_id not in self.agent_skills:
            return False
        task = self.tasks[task_id]
        task.assignee_id = agent_id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = time.time()
        
        # Log task assignment
        if office and office.gui:
             office.gui.update_task_status(f"Task {task_id} assigned to {office.agents[agent_id].name}")
        
        return True

    def find_suitable_agent(self, task: Task) -> Optional[str]:
        """Find the most suitable agent for a task based on skills"""
        required_skills = self._extract_skills_from_description(task.description)
        best_match = None
        best_match_score = 0
        for agent_id, skills in self.agent_skills.items():
            score = sum(1 for skill in required_skills if skill in skills)
            if score > best_match_score:
                best_match_score = score
                best_match = agent_id
        return best_match

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract required skills from task description"""
        # This would be more sophisticated in a real implementation
        # using NLP techniques to extract relevant skills
        keywords = ["analyze", "research", "design", "write", "code", 
                   "test", "support", "evaluate", "market", "legal"]
        return [keyword for keyword in keywords if keyword in description.lower()]

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a task"""
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        task.status = status
        task.updated_at = time.time()
        if status == TaskStatus.COMPLETED:
            task.completed_at = time.time()
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to an agent"""
        return [task for task in self.tasks.values() if task.assignee_id == agent_id]

class KnowledgeBase:
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def store(self, key: str, value: Any):
        """Store information in the knowledge base"""
        self.data[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve information from the knowledge base"""
        return self.data.get(key)

    def update(self, key: str, value: Any) -> bool:
        """Update existing information"""
        if key not in self.data:
            return False
        self.data[key] = value
        return True

    def delete(self, key: str) -> bool:
        """Delete information from the knowledge base"""
        if key not in self.data:
            return False
        del self.data[key]
        return True

class AIManager:
    def __init__(self, office_simulation: 'OfficeSimulation'):
        self.office_simulation = office_simulation
        self.task_manager = office_simulation.task_manager
        self.communication_bus = office_simulation.communication_bus
        self.agents = office_simulation.agents
    
    async def delegate_task(self, task: Task):
        """Delegate the task to a suitable agent based on skills and priority"""
        suitable_agent_id = self.task_manager.find_suitable_agent(task)
        
        if suitable_agent_id:
            agent = self.agents[suitable_agent_id]
            
            # Consider agent's current task and priority
            if agent.current_task_id:
                current_task = self.task_manager.get_task(agent.current_task_id)
                if current_task and current_task.priority == TaskPriority.CRITICAL:
                    # Agent is busy with a critical task, don't interrupt
                    return
            
            # Assign the task
            self.task_manager.assign_task(task.id, suitable_agent_id)
            
            # Notify the agent
            await self.communication_bus.publish(
                Message(
                    sender_id=self.office_simulation.boss_agent_id,
                    recipient_id=suitable_agent_id,
                    content=f"REQUEST: Please handle task {task.id}",
                    task_id=task.id
                )
            )

class OfficeSimulation:
    def __init__(self):
        self.communication_bus = CommunicationBus()
        self.task_manager = TaskManager(self.communication_bus)
        self.knowledge_base = KnowledgeBase()
        self.agents: Dict[str, Agent] = {}
        self.boss_agent_id: Optional[str] = None
        self.gui = None # Reference to the GUI
        self.ai_manager = AIManager(self) # Add AIManager instance

    def add_agent(self, agent: Agent, is_boss: bool = False):
        """Add an agent to the simulation"""
        self.agents[agent.id] = agent
        self.communication_bus.subscribe(agent)
        self.task_manager.register_agent(agent)
        if is_boss:
            self.boss_agent_id = agent.id

    async def submit_task(self, title: str, description: str) -> str:
        """Submit a new task to the office"""
        # Create the task
        user_id = "user"  # The external user
        task = self.task_manager.create_task(title, description, user_id)
        
        # Log task creation
        if self.gui:
            self.gui.update_task_status(f"Task {task.id} created: {title}")
        
        # First, assign to the boss for delegation
        if self.boss_agent_id:
            self.task_manager.assign_task(task.id, self.boss_agent_id)
            # The boss will delegate to appropriate team members
            await self.ai_manager.delegate_task(task)
            # Wait for completion and consolidate results
            await self._monitor_task_completion(task.id)
            # Get the final result from the boss
            final_result = await self._get_boss_summary(task.id)
            
            # Log final result
            if self.gui:
                self.gui.update_task_status(f"Final Result for Task {task.id}: {final_result}")
            
            return final_result
        return "No boss agent configured to handle this task."

    async def _delegate_task(self, task: Task):
        """Boss delegates the task to team members"""
        # This would involve breaking down the task and assigning subtasks
        # For simplicity, we'll have the boss assign it to a single team member
        pass

    async def _monitor_task_completion(self, task_id: str):
        """Monitor completion of a task and its subtasks"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return
        
        # Log monitoring start
        if self.gui:
            self.gui.update_task_status(f"Monitoring task {task_id} completion...")
        
        # Wait for all subtasks to complete
        for subtask_id in task.subtasks:
            subtask = self.task_manager.get_task(subtask_id)
            if not subtask:
                continue
            
            # Log subtask processing
            if self.gui:
                self.gui.update_task_status(f"Processing subtask {subtask_id}...")
            
            # Process the subtask with the assigned agent
            agent = self.agents.get(subtask.assignee_id)
            if agent:
                # Ensure the agent processes the task
                if subtask.status != TaskStatus.COMPLETED:
                    updated_subtask = await agent.process_task(subtask)
                    self.task_manager.tasks[subtask_id] = updated_subtask
                    
                    # Log subtask completion
                    if self.gui:
                        self.gui.update_task_status(f"Subtask {subtask_id} completed by {agent.name}: {updated_subtask.results.get(agent.id, 'No result')}")
                else:
                    if self.gui:
                        self.gui.update_task_status(f"Subtask {subtask_id} already completed.")
            else:
                if self.gui:
                    self.gui.update_task_status(f"No agent found for subtask {subtask_id}.")

        # Update the parent task status
        all_completed = all(
            self.task_manager.get_task(subtask_id).status == TaskStatus.COMPLETED
            for subtask_id in task.subtasks
        )
        if all_completed:
            task.status = TaskStatus.COMPLETED
            task.updated_at = time.time()
            task.completed_at = time.time()
            
            # Log task completion
            if self.gui:
                self.gui.update_task_status(f"Task {task_id} completed.")

    async def _get_boss_summary(self, task_id: str) -> str:
        """Get the final summary from the boss"""
        task = self.task_manager.get_task(task_id)
        if not task or not self.boss_agent_id:
            return "Task not found or no boss configured."
        boss = self.agents[self.boss_agent_id]
        # Collect all subtask results
        subtask_results = []
        for subtask_id in task.subtasks:
            subtask = self.task_manager.get_task(subtask_id)
            if subtask and subtask.assignee_id:
                agent_name = self.agents[subtask.assignee_id].name
                subtask_results.append(f"{agent_name}: {subtask.results.get(subtask.assignee_id, 'No result')}")
        # Create a summary task for the boss
        summary_task = Task(
            title=f"Summary of {task.title}",
            description=f"Original task: {task.description}\n\nResults:\n" + "\n".join(subtask_results),
            creator_id=task.creator_id,
            assignee_id=self.boss_agent_id
        )
        # Let the boss process the summary
        processed_summary = await boss.process_task(summary_task)
        return processed_summary.results.get(self.boss_agent_id, "No summary available.")

# Example usage
office = None # Define office outside main to be accessible in Agent.handle_message

async def main():
    global office
    # Create the simulation
    office = OfficeSimulation()
    
    # Add agents (simplified example)
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
    
    # Add agents to simulation
    office.add_agent(boss, is_boss=True)
    office.add_agent(analyst)
    office.add_agent(researcher)
    
    # Start the communication bus in a separate task
    communication_task = asyncio.create_task(office.communication_bus.start())
    
    # Run the GUI
    office.gui = run_gui(office, Agent, TaskPriority, asyncio, TaskStatus)
    
    # Clean up: Cancel the communication task when the GUI is closed
    communication_task.cancel()
    try:
        await communication_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())