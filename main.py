import logging
import asyncio
from agents import AgentBase, AgentType, Message
from tasks import Task, TaskStatus, TaskPriority
from storage import save_state, load_state
from gui import run_gui
import uuid
import time
from typing import Dict, Any, Optional
import heapq

# Logging configuration - disable terminal logs
logging.basicConfig(level=logging.WARNING, format='%(asctime)s [%(levelname)s] %(message)s')

class CommunicationBus:
    def __init__(self, office):
        self.office = office
        self.queue = asyncio.Queue()
        self.running = False

    async def publish(self, message: Message):
        await self.queue.put(message)
        if self.office.gui:
            sender = self.office.agents[message.sender_id].name
            recipient = self.office.agents[message.recipient_id].name
            self.office.gui.update_communication_log(f"Message from {sender} to {recipient}: {message.content}")

    async def start(self):
        self.running = True
        while self.running:
            message = await self.queue.get()
            recipient = self.office.agents.get(message.recipient_id)
            if recipient:
                await recipient.receive_message(message, self.office)
            self.queue.task_done()

class TaskQueue:
    def __init__(self):
        self._queue = []  # (priority, time, task_id)
        self._counter = 0

    def put(self, task: Task):
        # Im wyższy priorytet, tym niższa wartość (CRITICAL=1, LOW=4)
        heapq.heappush(self._queue, (task.priority.value, task.created_at, task.id))
        self._counter += 1

    def get(self):
        if self._queue:
            return heapq.heappop(self._queue)[2]  # Zwraca task_id
        return None

    def empty(self):
        return len(self._queue) == 0

class OfficeSimulation:
    def __init__(self):
        self.agents: Dict[str, AgentBase] = {}
        self.tasks: Dict[str, Task] = {}
        self.gui = None
        self.boss_agent_id: Optional[str] = None
        self.bus = CommunicationBus(self)
        self.task_queue = TaskQueue()

    def add_agent(self, agent: AgentBase, is_boss: bool = False):
        self.agents[agent.id] = agent
        if is_boss:
            self.boss_agent_id = agent.id
        if self.gui:
            self.gui.update_task_status(f"👤 Added agent: {agent.name} ({agent.role})")
            self.gui.update_communication_log(f"[SYSTEM] 👤 Added agent: {agent.name} ({agent.role})")
            self.gui.update_communication_log(f"[SYSTEM] 📋 {agent.name} - Skills: {', '.join(agent.skills)}")
        logging.info(f"Added agent: {agent.name} ({agent.role})")

    def create_task(self, title: str, description: str, creator_id: str, priority: TaskPriority = TaskPriority.MEDIUM) -> Task:
        task = Task(title=title, description=description, creator_id=creator_id, priority=priority)
        self.tasks[task.id] = task
        self.task_queue.put(task)
        if self.gui:
            self.gui.update_task_status(f"📝 Created task: {title} (priority: {priority.name})")
            self.gui.update_communication_log(f"[SYSTEM] 📝 Created task: {title} (priority: {priority.name})")
            self.gui.update_communication_log(f"[SYSTEM] 📄 Task description: {task.description[:100]}...")
        logging.info(f"Created task: {title} (id={task.id})")
        return task

    def assign_task(self, task_id: str, agent_id: str):
        if task_id in self.tasks and agent_id in self.agents:
            self.tasks[task_id].assignee_id = agent_id
            self.tasks[task_id].status = TaskStatus.IN_PROGRESS
            self.tasks[task_id].updated_at = time.time()
            agent_name = self.agents[agent_id].name
            task_title = self.tasks[task_id].title
            if self.gui:
                self.gui.update_task_status(f"📋 Assigned task '{task_title}' to {agent_name}")
                self.gui.update_communication_log(f"[SYSTEM] 📋 Assigned task '{task_title}' to {agent_name}")
            logging.info(f"Assigned task {task_id} to agent {agent_id}")
            return True
        return False

    def _find_agent_by_role(self, role: str) -> Optional[AgentBase]:
        for agent in self.agents.values():
            if agent.role.lower() == role.lower():
                return agent
        return None

    async def submit_task(self, title: str, description: str, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        debug_msg = f"DEBUG: submit_task - Tworzenie taska: {title} | {description} | {priority}"
        print(debug_msg)
        # 1. Client Advisor analyzes and creates a brief/spec
        client_advisor = self._find_agent_by_role("Client Advisor")
        brief_task = Task(title=f"Client Brief: {title}", description=description, creator_id="user", priority=priority)
        self.tasks[brief_task.id] = brief_task
        self.assign_task(brief_task.id, client_advisor.id)
        if self.gui:
            self.gui.start_agent_work(client_advisor.name)
        brief_result = await client_advisor.process_task(brief_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(client_advisor.name)

        # 2. Project Manager plans and splits tasks
        pm = self._find_agent_by_role("Project Manager")
        pm_task = Task(title=f"Project Plan: {title}", description=brief_result.results[client_advisor.id], creator_id=client_advisor.id, priority=priority)
        self.tasks[pm_task.id] = pm_task
        self.assign_task(pm_task.id, pm.id)
        if self.gui:
            self.gui.start_agent_work(pm.name)
        pm_result = await pm.process_task(pm_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(pm.name)

        # 3. Subtasks for Web Dev, UX/UI, Copywriter, Graphic Designer (parallel)
        sub_results = {}
        creative_roles = [
            ("Web Developer", "Website Skeleton"),
            ("UX/UI Designer", "UI/UX Layout"),
            ("Copywriter", "Website Content"),
            ("AI Graphic Designer", "Website Graphics")
        ]
        for role, sub_title in creative_roles:
            agent = self._find_agent_by_role(role)
            if agent:
                sub_task = Task(title=f"{sub_title} for: {title}", description=pm_result.results[pm.id], creator_id=pm.id, parent_task_id=pm_task.id, priority=priority)
                self.tasks[sub_task.id] = sub_task
                self.assign_task(sub_task.id, agent.id)
                if self.gui:
                    self.gui.start_agent_work(agent.name)
                result = await agent.process_task(sub_task, office=self)
                if self.gui:
                    self.gui.stop_agent_work(agent.name)
                sub_results[agent.id] = result.results[agent.id]

        # 4. Integrator collects, tests, and publishes
        integrator = self._find_agent_by_role("Integrator (Coordinator)")
        integration_task = Task(title=f"Integration & Testing: {title}", description=str(sub_results), creator_id=pm.id, parent_task_id=pm_task.id, priority=priority)
        self.tasks[integration_task.id] = integration_task
        self.assign_task(integration_task.id, integrator.id)
        if self.gui:
            self.gui.start_agent_work(integrator.name)
        integration_result = await integrator.process_task(integration_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(integrator.name)

        # 4.5 Hosting/DevOps Agent
        devops = self._find_agent_by_role("Hosting/DevOps")
        devops_task = Task(title=f"Hosting & Deployment: {title}", description=integration_result.results[integrator.id], creator_id=integrator.id, parent_task_id=integration_task.id, priority=priority)
        self.tasks[devops_task.id] = devops_task
        self.assign_task(devops_task.id, devops.id)
        if self.gui:
            self.gui.start_agent_work(devops.name)
        devops_result = await devops.process_task(devops_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(devops.name)

        # 5. Mobile Responsiveness & Testing Agent
        mobile = self._find_agent_by_role("Mobile Responsiveness & Testing Agent")
        mobile_task = Task(title=f"Mobile Testing: {title}", description=integration_result.results[integrator.id], creator_id=integrator.id, parent_task_id=integration_task.id, priority=priority)
        self.tasks[mobile_task.id] = mobile_task
        self.assign_task(mobile_task.id, mobile.id)
        if self.gui:
            self.gui.start_agent_work(mobile.name)
        mobile_result = await mobile.process_task(mobile_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(mobile.name)

                # 6. Feedback & QA Agent
        feedback = self._find_agent_by_role("Feedback & QA Agent")
        feedback_task = Task(title=f"Feedback & QA: {title}", description=mobile_result.results[mobile.id], creator_id=mobile.id, parent_task_id=mobile_task.id, priority=priority)
        self.tasks[feedback_task.id] = feedback_task
        self.assign_task(feedback_task.id, feedback.id)
        if self.gui:
            self.gui.start_agent_work(feedback.name)
        feedback_result = await feedback.process_task(feedback_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(feedback.name)

        # 7. Marketing Strategist plans and monitors campaign
        marketing = self._find_agent_by_role("Marketing Strategist")
        marketing_task = Task(title=f"Marketing Campaign: {title}", description=feedback_result.results[feedback.id], creator_id=feedback.id, parent_task_id=feedback_task.id, priority=priority)
        self.tasks[marketing_task.id] = marketing_task
        self.assign_task(marketing_task.id, marketing.id)
        if self.gui:
            self.gui.start_agent_work(marketing.name)
        marketing_result = await marketing.process_task(marketing_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(marketing.name)

        # 8. Data Analyst analyzes effectiveness
        data_analyst = self._find_agent_by_role("Data Analyst")
        data_task = Task(title=f"Data Analysis: {title}", description=marketing_result.results[marketing.id], creator_id=marketing.id, parent_task_id=marketing_task.id, priority=priority)
        self.tasks[data_task.id] = data_task
        self.assign_task(data_task.id, data_analyst.id)
        if self.gui:
            self.gui.start_agent_work(data_analyst.name)
        data_result = await data_analyst.process_task(data_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(data_analyst.name)

        # 9. AI Chatbot is ready to answer questions (simulate deployment)
        chatbot = self._find_agent_by_role("AI Chatbot")
        chatbot_task = Task(title=f"Chatbot Deployment: {title}", description="The website is live. Start answering visitor questions!", creator_id=integrator.id, parent_task_id=integration_task.id, priority=priority)
        self.tasks[chatbot_task.id] = chatbot_task
        self.assign_task(chatbot_task.id, chatbot.id)
        if self.gui:
            self.gui.start_agent_work(chatbot.name)
        chatbot_result = await chatbot.process_task(chatbot_task, office=self)
        if self.gui:
            self.gui.stop_agent_work(chatbot.name)

        # Final summary (Integrator + all results)
        final_summary = f"=== FINAL PRODUCT ===\n\n{integration_result.results[integrator.id]}\n\n=== HOSTING & DEPLOYMENT ===\n{devops_result.results[devops.id]}\n\n=== MOBILE TESTING ===\n{mobile_result.results[mobile.id]}\n\n=== FEEDBACK & QA ===\n{feedback_result.results[feedback.id]}\n\n=== MARKETING CAMPAIGN ===\n{marketing_result.results[marketing.id]}\n\n=== DATA ANALYSIS ===\n{data_result.results[data_analyst.id]}\n\n=== CHATBOT STATUS ===\n{chatbot_result.results[chatbot.id]}"
        return final_summary

    async def _create_task_plan(self, task: Task, boss: AgentBase) -> str:
        """CEO creates task plan based on description"""
        if self.gui:
            self.gui.update_task_status(f"📝 {boss.name} analyzing task requirements...")
            self.gui.update_communication_log(f"[{boss.name}] 📝 Analyzing task: {task.title}")
        
        description_lower = task.description.lower()
        plan = f"=== TASK PLAN BY {boss.name.upper()} ===\n\n"
        plan += f"Project: {task.title}\n"
        plan += f"Description: {task.description}\n"
        plan += f"Priority: {task.priority.name}\n\n"
        
        # Requirements analysis
        requirements = []
        if any(word in description_lower for word in ["kod", "code", "webpage", "strona", "menu"]):
            requirements.append("✅ Website development (HTML/CSS/JavaScript)")
        if any(word in description_lower for word in ["analiz", "dane", "data", "statystyki"]):
            requirements.append("✅ Data analysis and reporting")
        if any(word in description_lower for word in ["obraz", "image", "picture", "zdjęcia", "pictures"]):
            requirements.append("✅ Image generation and DALL-E prompts")
        if any(word in description_lower for word in ["tekst", "text", "artykuł", "article", "content"]):
            requirements.append("✅ Content creation and articles")
        
        plan += "REQUIREMENTS ANALYSIS:\n" + "\n".join(requirements) + "\n\n"
        
        # Team assignment plan
        plan += "TEAM ASSIGNMENT PLAN:\n"
        if any(word in description_lower for word in ["kod", "code", "webpage", "strona", "menu"]):
            plan += "👨‍💻 Jan Nowak (Web Developer) - HTML/CSS/JavaScript coding\n"
        if any(word in description_lower for word in ["analiz", "dane", "data", "statystyki"]):
            plan += "📊 Anna Kowalska (Data Analyst) - Data analysis and programming\n"
        if any(word in description_lower for word in ["obraz", "image", "picture", "zdjęcia", "pictures"]):
            plan += "🎨 Piotr Malinowski (AI Image Generator) - DALL-E prompts and graphics\n"
        if any(word in description_lower for word in ["tekst", "text", "artykuł", "article", "content"]):
            plan += "📝 Katarzyna Wiśniewska (Text Analyst) - Content creation\n"
        
        plan += "\nEXECUTION STRATEGY:\n"
        plan += "1. 📋 Task analysis and requirements breakdown\n"
        plan += "2. 👥 Team coordination and task delegation\n"
        plan += "3. ⚡ Parallel development by specialists\n"
        plan += "4. 🔄 Continuous communication and collaboration\n"
        plan += "5. 📊 Results consolidation and quality review\n"
        plan += "6. ✅ Final project delivery and documentation\n\n"
        
        if self.gui:
            self.gui.update_task_status(f"📋 Plan created by {boss.name}:")
            self.gui.update_task_status(plan)
            self.gui.update_communication_log(f"[{boss.name}] 📋 Task plan completed for: {task.title}")
        
        return plan

    async def _delegate_to_team(self, task: Task, boss: AgentBase) -> Dict[str, str]:
        """Boss delegates subtasks to different agents"""
        team_results = {}
        
        if self.gui:
            self.gui.update_task_status(f"👥 {boss.name} starting team coordination...")
            self.gui.update_communication_log(f"[{boss.name}] 👥 Coordinating team for task: {task.title}")
        
        # Analyze task description and find appropriate agents
        description_lower = task.description.lower()
        
        # Delegate to programmer if coding is needed
        if any(word in description_lower for word in ["kod", "code", "webpage", "strona", "menu"]):
            coder = self._find_agent_by_type(AgentType.CODER)
            if coder:
                coder_task = Task(
                    title=f"Coding for: {task.title}",
                    description=task.description,
                    creator_id=boss.id,
                    parent_task_id=task.id
                )
                self.tasks[coder_task.id] = coder_task
                self.assign_task(coder_task.id, coder.id)
                
                if self.gui:
                    self.gui.update_task_status(f"👨‍💻 {boss.name} delegates coding to {coder.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 👨‍💻 Delegating coding to {coder.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📋 Task: {coder_task.title}")
                    self.gui.start_agent_work(coder.name)
                
                updated_coder_task = await coder.process_task(coder_task, office=self)
                team_results[coder.id] = updated_coder_task.results.get(coder.id, "")
                
                if self.gui:
                    self.gui.stop_agent_work(coder.name)
                    self.gui.update_agent_activity(coder.name)
        
        # Delegate to data analyst
        if any(word in description_lower for word in ["analiz", "dane", "data", "statystyki"]):
            analyst = self._find_agent_by_type(AgentType.ANALYST)
            if analyst:
                analyst_task = Task(
                    title=f"Analysis for: {task.title}",
                    description="Analyze data and prepare report",
                    creator_id=boss.id,
                    parent_task_id=task.id
                )
                self.tasks[analyst_task.id] = analyst_task
                self.assign_task(analyst_task.id, analyst.id)
                
                if self.gui:
                    self.gui.update_task_status(f"📊 {boss.name} delegates analysis to {analyst.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📊 Delegating analysis to {analyst.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📋 Task: {analyst_task.title}")
                    self.gui.start_agent_work(analyst.name)
                
                updated_analyst_task = await analyst.process_task(analyst_task, office=self)
                team_results[analyst.id] = updated_analyst_task.results.get(analyst.id, "")
                
                if self.gui:
                    self.gui.stop_agent_work(analyst.name)
                    self.gui.update_agent_activity(analyst.name)
        
        # Delegate to image generator
        if any(word in description_lower for word in ["obraz", "image", "picture", "zdjęcia", "pictures"]):
            image_gen = self._find_agent_by_type(AgentType.IMAGE_GEN)
            if image_gen:
                image_task = Task(
                    title=f"Image generation for: {task.title}",
                    description="Find and prepare appropriate images",
                    creator_id=boss.id,
                    parent_task_id=task.id
                )
                self.tasks[image_task.id] = image_task
                self.assign_task(image_task.id, image_gen.id)
                
                if self.gui:
                    self.gui.update_task_status(f"🎨 {boss.name} delegates image generation to {image_gen.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 🎨 Delegating image generation to {image_gen.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📋 Task: {image_task.title}")
                    self.gui.start_agent_work(image_gen.name)
                
                updated_image_task = await image_gen.process_task(image_task, office=self)
                team_results[image_gen.id] = updated_image_task.results.get(image_gen.id, "")
                
                if self.gui:
                    self.gui.stop_agent_work(image_gen.name)
                    self.gui.update_agent_activity(image_gen.name)
        
        # Delegate to text analyst
        if any(word in description_lower for word in ["tekst", "text", "artykuł", "article", "content"]):
            text_analyst = self._find_agent_by_type(AgentType.TEXT_ANALYST)
            if text_analyst:
                text_task = Task(
                    title=f"Text analysis for: {task.title}",
                    description="Write articles and content",
                    creator_id=boss.id,
                    parent_task_id=task.id
                )
                self.tasks[text_task.id] = text_task
                self.assign_task(text_task.id, text_analyst.id)
                
                if self.gui:
                    self.gui.update_task_status(f"📝 {boss.name} delegates text analysis to {text_analyst.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📝 Delegating text analysis to {text_analyst.name}")
                    self.gui.update_communication_log(f"[{boss.name}] 📋 Task: {text_task.title}")
                    self.gui.start_agent_work(text_analyst.name)
                
                updated_text_task = await text_analyst.process_task(text_task, office=self)
                team_results[text_analyst.id] = updated_text_task.results.get(text_analyst.id, "")
                
                if self.gui:
                    self.gui.stop_agent_work(text_analyst.name)
                    self.gui.update_agent_activity(text_analyst.name)
        
        if self.gui:
            self.gui.update_task_status(f"✅ {boss.name} completed team delegation")
            self.gui.update_communication_log(f"[{boss.name}] ✅ Team delegation completed")
        
        return team_results

    def _find_agent_by_type(self, agent_type: AgentType) -> Optional[AgentBase]:
        """Find agent by type"""
        for agent in self.agents.values():
            if agent.agent_type == agent_type:
                return agent
        return None

    async def _consolidate_results(self, task: Task, team_results: Dict[str, str], boss: AgentBase) -> str:
        debug_msg = f"DEBUG: _consolidate_results - Konsolidacja wyników przez {boss.name}"
        print(debug_msg)
        if self.gui:
            self.gui.update_task_status(f"📊 {boss.name} consolidating team results...")
            self.gui.update_communication_log(f"[{boss.name}] 📊 Consolidating team results...")
            self.gui.start_agent_work(boss.name)
        
        # DEBUG: sprawdź czy boss to Integrator
        debug_msg1 = f"DEBUG: _consolidate_results - Boss role: {boss.role}"
        debug_msg2 = f"DEBUG: _consolidate_results - Boss id: {boss.id}"
        print(debug_msg1)
        print(debug_msg2)
        
        final_report = await boss.process_task(task, office=self)
        debug_msg = f"DEBUG: _consolidate_results - Wynik Integratora: {final_report[:200]}..."
        print(debug_msg)
        
        # DEBUG: sprawdź czy wynik jest w task.results
        debug_msg1 = f"DEBUG: _consolidate_results - task.results keys: {list(task.results.keys())}"
        debug_msg2 = f"DEBUG: _consolidate_results - Integrator wynik w task.results: {'=== QWEN3 FINAL CODE ===' in task.results[boss.id]}" if boss.id in task.results else "DEBUG: _consolidate_results - Integrator wynik NIE w task.results"
        print(debug_msg1)
        print(debug_msg2)
        
        if self.gui:
            self.gui.stop_agent_work(boss.name)
            self.gui.update_task_status(f"🎉 {boss.name} completed project: {task.title}")
            self.gui.update_communication_log(f"[{boss.name}] 🎉 Completed project: {task.title}")
            self.gui.update_communication_log(f"[{boss.name}] 📊 Final report prepared")
        
        return final_report

    async def handle_message(self, message: Message):
        await self.bus.publish(message)

    def save_all(self, filename: str):
        data = {
            'agents': [agent.__dict__ for agent in self.agents.values()],
            'tasks': [task.__dict__ for task in self.tasks.values()]
        }
        save_state(filename, data)
        logging.info(f"Zapisano stan do pliku {filename}")

    def load_all(self, filename: str):
        data = load_state(filename)
        # Odtwarzanie agentów i tasków (uproszczone)
        self.agents = {a['id']: AgentBase(**a) for a in data['agents']}
        self.tasks = {t['id']: Task(**t) for t in data['tasks']}
        logging.info(f"Wczytano stan z pliku {filename}")

    async def process_tasks(self):
        while True:
            if self.task_queue.empty():
                await asyncio.sleep(0.5)
                continue
            task_id = self.task_queue.get()
            task = self.tasks[task_id]
            if task.status != TaskStatus.PENDING:
                continue
            # Automatyczne przydzielanie do agenta
            agent = self.find_suitable_agent(task)
            if agent:
                self.assign_task(task.id, agent.id)
                if self.gui:
                    self.gui.update_task_status(f"📋 Assigned task {task.title} to agent {agent.name}")
                    self.gui.update_agent_activity(agent.name)  # Update agent activity
                    self.gui.update_communication_log(f"👤 {agent.name} starting work on task: {task.title}")
                    self.gui.start_agent_work(agent.name)
                updated_task = await agent.process_task(task, office=self)
                self.tasks[task.id] = updated_task
                if self.gui:
                    self.gui.stop_agent_work(agent.name)  # Stop counting work time
                    self.gui.update_task_status(f"✅ Task {task.title} completed by {agent.name}")
                    self.gui.update_communication_log(f"✅ {agent.name} completed task: {task.title}")
                self.show_final_report(updated_task)
            else:
                if self.gui:
                    self.gui.update_task_status(f"❌ No suitable agent for task {task.title}")
                    self.gui.update_communication_log(f"❌ No suitable agent found for: {task.title}")
                logging.warning(f"No suitable agent for task {task.title}")

    def find_suitable_agent(self, task: Task) -> Optional[AgentBase]:
        # More flexible selection: by keyword in description and task type
        description_lower = task.description.lower()
        title_lower = task.title.lower()
        
        # Check for coding-related keywords
        coding_keywords = ["kod", "code", "program", "website", "web", "html", "css", "javascript", "react", "vue", "app", "application", "site", "strona"]
        if any(keyword in description_lower or keyword in title_lower for keyword in coding_keywords):
            for agent in self.agents.values():
                if agent.agent_type == AgentType.CODER:
                    return agent
        
        # Check for analysis-related keywords
        analysis_keywords = ["analiz", "data", "dane", "statistics", "statystyki", "report", "raport", "dashboard", "analytics"]
        if any(keyword in description_lower or keyword in title_lower for keyword in analysis_keywords):
            for agent in self.agents.values():
                if agent.agent_type == AgentType.ANALYST:
                    return agent
        
        # Check for image-related keywords
        image_keywords = ["obraz", "image", "picture", "photo", "graphic", "design", "logo", "banner", "mockup"]
        if any(keyword in description_lower or keyword in title_lower for keyword in image_keywords):
            for agent in self.agents.values():
                if agent.agent_type == AgentType.IMAGE_GEN:
                    return agent
        
        # Check for text-related keywords
        text_keywords = ["tekst", "text", "content", "copy", "writing", "article", "blog", "seo", "copywriting"]
        if any(keyword in description_lower or keyword in title_lower for keyword in text_keywords):
            for agent in self.agents.values():
                if agent.agent_type == AgentType.TEXT_ANALYST:
                    return agent
        
        # Default: try to find any available agent based on task type
        # For website-related tasks, prefer CODER
        if "website" in description_lower or "web" in description_lower or "site" in description_lower:
            for agent in self.agents.values():
                if agent.agent_type == AgentType.CODER:
                    return agent
        
        # For general tasks, prefer BOSS type agents
        for agent in self.agents.values():
            if agent.agent_type == AgentType.BOSS:
                return agent
        
        # If no specific match, return the first available agent
        if self.agents:
            return list(self.agents.values())[0]
        
        return None

    def show_final_report(self, task: Task):
        report = f"\n=== FINAL REPORT ===\nTask: {task.title}\nDescription: {task.description}\nStatus: {task.status.name}\nResults:\n"
        for agent_id, result in task.results.items():
            agent_name = self.agents[agent_id].name if agent_id in self.agents else agent_id
            report += f"- {agent_name}: {result}\n"
        if self.gui:
            self.gui.update_task_status(report)
            self.gui.update_communication_log(f"📊 Final report for task: {task.title}")
        logging.info(report)

office = None

async def main():
    global office
    office = OfficeSimulation()
    # New company agents (ENGLISH, matching business descriptions)
    web_dev = AgentBase(
        id="web_dev1",
        name="Alex Carter",
        role="Web Developer",
        agent_type=AgentType.CODER,
        skills=["HTML", "CSS", "JavaScript", "React", "Vue.js", "Next.js", "responsive layouts", "prototyping"],
        personality_traits=["precise", "innovative"],
        preferred_tools=["AI code assistant", "Codex", "GPT-4 Turbo", "low-code", "no-code"],
        collaborators=["ux_ui1", "copywriter1"]
    )
    ux_ui = AgentBase(
        id="ux_ui1",
        name="Taylor Kim",
        role="UX/UI Designer",
        agent_type=AgentType.IMAGE_GEN,
        skills=["wireframing", "UI design", "user flow", "color theory", "mockups"],
        personality_traits=["creative", "empathetic"],
        preferred_tools=["Figma AI", "Galileo AI", "GPT-4 Vision"],
        collaborators=["web_dev1", "copywriter1"]
    )
    copywriter = AgentBase(
        id="copywriter1",
        name="Morgan Lee",
        role="Copywriter",
        agent_type=AgentType.TEXT_ANALYST,
        skills=["SEO writing", "blog articles", "product descriptions", "headlines", "CTA"],
        personality_traits=["communicative", "persuasive"],
        preferred_tools=["ChatGPT", "Jasper", "Copy.ai"],
        collaborators=["marketing1", "ux_ui1"]
    )
    marketing = AgentBase(
        id="marketing1",
        name="Jordan Smith",
        role="Marketing Strategist",
        agent_type=AgentType.BOSS,
        skills=["campaign planning", "SEO/SEM", "social media", "content strategy", "targeting"],
        personality_traits=["strategic", "dynamic"],
        preferred_tools=["HubSpot AI", "GPT-4 Marketing"],
        collaborators=["copywriter1", "data_analyst1"]
    )
    data_analyst = AgentBase(
        id="data_analyst1",
        name="Casey Brown",
        role="Data Analyst",
        agent_type=AgentType.ANALYST,
        skills=["user data analysis", "traffic analysis", "ROI", "KPI dashboards", "Power BI", "Python", "Pandas"],
        personality_traits=["analytical", "detail-oriented"],
        preferred_tools=["Power BI Copilot", "Python", "AI dashboards"],
        collaborators=["marketing1", "pm1"]
    )
    chatbot = AgentBase(
        id="chatbot1",
        name="RoboAssist",
        role="AI Chatbot",
        agent_type=AgentType.TEXT_ANALYST,
        skills=["customer support", "FAQ", "offer presentation", "lead generation"],
        personality_traits=["helpful", "responsive"],
        preferred_tools=["ChatGPT", "Rasa", "Botpress"],
        collaborators=["web_dev1"]
    )
    graphic = AgentBase(
        id="graphic1",
        name="Samira Patel",
        role="AI Graphic Designer",
        agent_type=AgentType.IMAGE_GEN,
        skills=["social media graphics", "banners", "mockups", "logos", "ad creatives"],
        personality_traits=["visual", "imaginative"],
        preferred_tools=["DALL·E", "Midjourney", "Canva AI"],
        collaborators=["ux_ui1", "marketing1"]
    )
    devops = AgentBase(
        id="devops1",
        name="Chris Nguyen",
        role="Hosting/DevOps",
        agent_type=AgentType.CODER,
        skills=["hosting setup", "CI/CD", "security", "backups", "cloud platforms"],
        personality_traits=["reliable", "systematic"],
        preferred_tools=["GitHub Copilot", "Ansible AI", "Vercel AI"],
        collaborators=["pm1"]
    )
    pm = AgentBase(
        id="pm1",
        name="Jamie Evans",
        role="Project Manager",
        agent_type=AgentType.BOSS,
        skills=["project management", "task assignment", "progress tracking", "prioritization"],
        personality_traits=["organized", "leadership"],
        preferred_tools=["Notion AI", "Asana AI", "ChatGPT PM"],
        collaborators=["client1", "devops1", "data_analyst1"]
    )
    client = AgentBase(
        id="client1",
        name="Avery Green",
        role="Client Advisor",
        agent_type=AgentType.TEXT_ANALYST,
        skills=["client consulting", "requirements gathering", "offer creation", "briefing"],
        personality_traits=["advisory", "insightful"],
        preferred_tools=["ChatGPT Domain", "dynamic forms"],
        collaborators=["pm1"]
    )
    integrator = AgentBase(
        id="integrator1",
        name="Pat Morgan",
        role="Integrator (Coordinator)",
        agent_type=AgentType.BOSS,
        skills=["coordination", "quality control", "final reporting", "team management"],
        personality_traits=["coordinative", "meticulous"],
        preferred_tools=["GPT-4 Central"],
        collaborators=["pm1", "marketing1", "web_dev1", "ux_ui1", "copywriter1", "graphic1", "devops1", "data_analyst1", "chatbot1", "client1"]
    )
    mobile = AgentBase(
        id="mobile1",
        name="Riley Fox",
        role="Mobile Responsiveness & Testing Agent",
        agent_type=AgentType.CODER,
        skills=["mobile views", "tablet views", "desktop views", "automated testing", "PWA", "App Manifest"],
        personality_traits=["thorough", "tech-savvy"],
        preferred_tools=["Playwright", "Cypress", "Lighthouse"],
        collaborators=["web_dev1", "ux_ui1"]
    )
    feedback = AgentBase(
        id="feedback1",
        name="Dana White",
        role="Feedback & QA Agent",
        agent_type=AgentType.BOSS,
        skills=["regression testing", "feedback collection", "checklists", "repo archiving"],
        personality_traits=["meticulous", "user-focused"],
        preferred_tools=["Percy.io", "Notion AI", "custom forms"],
        collaborators=["pm1", "client1"]
    )
    # Dodaj agentów do biura
    office.add_agent(web_dev)
    office.add_agent(ux_ui)
    office.add_agent(copywriter)
    office.add_agent(marketing)
    office.add_agent(data_analyst)
    office.add_agent(chatbot)
    office.add_agent(graphic)
    office.add_agent(devops)
    office.add_agent(pm)
    office.add_agent(client)
    office.add_agent(integrator, is_boss=True)
    office.add_agent(mobile)
    office.add_agent(feedback)
    bus_task = asyncio.create_task(office.bus.start())
    process_task_task = asyncio.create_task(office.process_tasks())
    office.gui = run_gui(office, AgentBase, TaskPriority, asyncio, TaskStatus)
    if office.gui:
        office.gui.bring_to_front()
    # Upewnij się, że office.gui jest przypisane
    if office.gui is not None:
        office.gui.office_simulation = office
    bus_task.cancel()
    process_task_task.cancel()
    try:
        await bus_task
        await process_task_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())