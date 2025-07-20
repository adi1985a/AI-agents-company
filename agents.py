import random
import time
import asyncio
from enum import Enum, auto
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import uuid
import os

# Optional OpenAI integration
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI is not installed. Use: pip install openai")

# Optional Ollama integration
try:
    import requests
    OLLAMA_AVAILABLE = True
    print("Ollama is available. Can use local Qwen3 model.")
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Requests is not installed. Use: pip install requests")

# --- Kandinsky 2.2 integration (kandinsky2 lib) ---
# from kandinsky2 import get_kandinsky2
# import numpy as np
# from PIL import Image
# KANDINSKY2_MODEL = None
#
# def get_kandinsky2_model():
#     global KANDINSKY2_MODEL
#     if KANDINSKY2_MODEL is None:
#         KANDINSKY2_MODEL = get_kandinsky2('cuda' if torch.cuda.is_available() else 'cpu', task_type='text2img', model_version='2.2')
#     return KANDINSKY2_MODEL

class AgentType(Enum):
    CODER = auto()
    ANALYST = auto()
    IMAGE_GEN = auto()
    TEXT_ANALYST = auto()
    BOSS = auto()

class Message:
    def __init__(self, sender_id: str, recipient_id: str, content: str, task_id: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.task_id = task_id
        self.created_at = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0

@dataclass
class AgentBase:
    id: str
    name: str
    role: str
    agent_type: AgentType
    skills: List[str]
    personality_traits: List[str]
    preferred_tools: List[str]
    collaborators: List[str]
    reports_to: Optional[str] = None
    receives_from: List[str] = field(default_factory=list)
    current_task_id: Optional[str] = None
    task_history: List[str] = field(default_factory=list)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)

    def decide(self, task_desc: str) -> str:
        # Simple decision model (rules)
        if self.agent_type == AgentType.CODER:
            desc = task_desc.lower()
            coding_keywords = ["code", "kod", "program", "website", "web", "html", "css", "javascript", "app", "application", "site", "strona"]
            if any(word in desc for word in coding_keywords):
                return "coding"
        if self.agent_type == AgentType.ANALYST:
            if "analyze" in task_desc.lower() or "data" in task_desc.lower() or "analiz" in task_desc.lower():
                return "analyzing"
        if self.agent_type == AgentType.IMAGE_GEN:
            if "image" in task_desc.lower() or "picture" in task_desc.lower() or "obraz" in task_desc.lower():
                return "generating image"
        if self.agent_type == AgentType.TEXT_ANALYST:
            if "text" in task_desc.lower() or "tekst" in task_desc.lower() or "content" in task_desc.lower():
                return "analyzing text"
        return "thinking"

    async def send_message(self, recipient, content, task_id=None, office=None):
        msg = Message(self.id, recipient.id, content, task_id)
        if office:
            await office.handle_message(msg)
        return msg

    async def receive_message(self, message, office=None):
        # Simple reaction to message
        if office and office.gui:
            office.gui.update_communication_log(f"{self.name} received message from {office.agents[message.sender_id].name}: {message.content}")
        # Example response
        if "please" in message.content.lower():
            response = f"{self.name}: I received your request, starting to work!"
            if office:
                await self.send_message(office.agents[message.sender_id], response, message.task_id, office)

    async def generate_ai_response(self, task_description: str) -> str:
        """Generates response using local Ollama or OpenAI API"""
        if OLLAMA_AVAILABLE:
            return await self.generate_ollama_response(task_description)
        elif OPENAI_AVAILABLE:
            return await self.generate_openai_response(task_description)
        else:
            return self.generate_simple_response(task_description)

    async def generate_ollama_response(self, task_description: str) -> str:
        """Generates response using local Qwen3 0.6B model through Ollama API"""
        try:
            # Log to GUI instead of terminal
            if hasattr(self, 'office') and self.office and self.office.gui:
                self.office.gui.update_task_status(f"🤖 {self.name} using Qwen3 0.6B model...")
                self.office.gui.update_communication_log(f"[{self.name}] 🤖 Using Qwen3 0.6B model to generate response...")
                self.office.gui.update_communication_log(f"[{self.name}] 💭 Starting to think about: {task_description[:100]}...")
            
            # Prepare prompt for specific agent type
            prompt = self._create_qwen_prompt(task_description)
            
            # Call Ollama API with accelerated parameters
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen3:0.6b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature = faster responses
                        "num_predict": 200,  # Shorter responses
                        "top_k": 10,  # Limit token selection
                        "top_p": 0.8,  # Nucleus sampling
                        "repeat_penalty": 1.1  # Prevent repetitions
                    }
                },
                timeout=60  # Shorter timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                # Log thinking process to GUI
                if hasattr(self, 'office') and self.office and self.office.gui:
                    # Extract thinking process if present
                    if '<think>' in ai_response:
                        think_start = ai_response.find('<think>')
                        think_end = ai_response.find('</think>')
                        if think_start != -1 and think_end != -1:
                            thinking = ai_response[think_start+7:think_end].strip()
                            self.office.gui.update_communication_log(f"[{self.name}] 💭 <think> {thinking[:200]}...")
                            print(f"TERMINAL: [{self.name}] 💭 <think> {thinking[:200]}...")
                    
                    self.office.gui.update_task_status(f"✅ {self.name} received response from Qwen3")
                    self.office.gui.update_communication_log(f"[{self.name}] ✅ Received response from Qwen3 model")
                
                return f"{self.name}: {ai_response}"
            else:
                error_msg = f"❌ Ollama API error for {self.name}: {response.status_code}"
                if hasattr(self, 'office') and self.office and self.office.gui:
                    self.office.gui.update_task_status(error_msg)
                return self.generate_simple_response(task_description)
            
        except requests.exceptions.Timeout:
            error_msg = f"⏰ Timeout for {self.name} - model needs more time"
            if hasattr(self, 'office') and self.office and self.office.gui:
                self.office.gui.update_task_status(error_msg)
            return self.generate_simple_response(task_description)
        except requests.exceptions.ConnectionError:
            error_msg = f"🔌 Connection error with Ollama for {self.name}"
            if hasattr(self, 'office') and self.office and self.office.gui:
                self.office.gui.update_task_status(error_msg)
            return self.generate_simple_response(task_description)
        except Exception as e:
            error_msg = f"❌ Qwen3 error for {self.name}: {e}"
            if hasattr(self, 'office') and self.office and self.office.gui:
                self.office.gui.update_task_status(error_msg)
            return self.generate_simple_response(task_description)

    def _create_qwen_prompt(self, task_description: str) -> str:
        base_prompt = f"You are {self.name}, {self.role}. Your skills: {', '.join(self.skills)}.\n"
        base_prompt += f"Task: {task_description}\n"
        # Szczegółowe prompty dla każdej roli
        if self.role == "Client Advisor":
            base_prompt += (
                "Your job is to collect all requirements from the client, detect ambiguities, ask follow-up questions, define KPIs, target group, and project scope.\n"
                "Format your answer as a project brief with: goal, detected ambiguities, follow-up questions, target group, KPIs, scope.\n"
            )
        elif self.role == "Project Manager":
            base_prompt += (
                "Create a detailed project schedule (with dates), split tasks for each agent, monitor risks, and check compliance with the brief.\n"
                "Format: schedule, task split, risk monitoring.\n"
            )
        elif self.role == "Web Developer":
            base_prompt += (
                "Generate responsive code (HTML, CSS, JS, React if needed), optimize for Core Web Vitals, handle dynamic data (API, CMS), and use version control (Git).\n"
                "Format: code block, comments, and summary of optimizations.\n"
            )
        elif self.role == "UX/UI Designer":
            base_prompt += (
                "Design a modern, accessible UI. Create a design system, layout, mockups, test user flows, and export to Figma/Tailwind.\n"
                "Format: design description, accessibility checklist, user flow, export notes.\n"
            )
        elif self.role == "Copywriter":
            base_prompt += (
                "Write SEO-optimized website texts, product descriptions, blog posts, headlines, meta tags, OpenGraph, and internal linking. Analyze competitors (SEMrush API).\n"
                "Format: homepage headline, blog title, product description, CTA, meta, competitor analysis, internal links.\n"
            )
        elif self.role == "AI Graphic Designer":
            base_prompt += (
                "You are an expert AI graphic designer. For each required asset (logo, hero image, icons, banners, mockups):\n"
                "- Propose at least 3 unique prompts for DALL·E, Midjourney, or Kandinsky.\n"
                "- For each prompt, specify intended use, style (e.g. flat, 3D, photorealistic), color palette, and platform (web, mobile, social).\n"
                "- Suggest optimization (WebP, AVIF, compression).\n"
                "- Output as markdown table: Asset | Prompt | Style | Platform | Optimization\n"
            )
        elif self.role == "Mobile Responsiveness & Testing Agent":
            base_prompt += (
                "Test the website on mobile, tablet, desktop. Run automated tests (Playwright, Cypress, Lighthouse), check PWA compliance and App Manifest.\n"
                "Format: test report, issues found, compliance checklist.\n"
            )
        elif self.role == "Feedback & QA Agent":
            base_prompt += (
                "Run regression tests, collect client and visitor feedback, generate pre-launch checklist, and archive the repository.\n"
                "Format: test results, feedback summary, checklist, archiving note.\n"
            )
        elif self.role == "Marketing Strategist":
            base_prompt += (
                "Plan and monitor marketing campaigns (Google Ads, Meta, LinkedIn), segment customers, propose lead magnets and funnels, schedule campaigns, and budget.\n"
                "Format: campaign plan, segmentation, lead magnets, funnel, schedule, budget.\n"
            )
        elif self.role == "AI Chatbot":
            base_prompt += (
                "Create conversation scenarios (FAQ, support), integrate with CRM (HubSpot, Mailchimp), handle forms, remember context, and track sessions.\n"
                "Format: scenario list, CRM integration, context memory, session tracking.\n"
            )
        elif self.role == "Data Analyst":
            base_prompt += (
                "Connect to analytics tools (GA4, Facebook Pixel, Matomo), create dashboards (Power BI, Tableau), analyze UX (heatmaps, scroll depth), and generate daily/monthly reports.\n"
                "Format: analytics summary, dashboard links (if possible), UX analysis, recommendations.\n"
            )
        elif self.role == "Hosting/DevOps":
            base_prompt += (
                "Choose hosting (Vercel, Netlify, AWS), set up CI/CD (GitHub Actions), configure domain, SSL, cache, backups, and monitor uptime/load time.\n"
                "Format: deployment steps, configuration summary, monitoring report.\n"
            )
        elif self.role == "Integrator (Coordinator)":
            base_prompt += (
                "You are a senior fullstack developer. Based on the following project requirements and agent outputs, generate a complete, modern, responsive website.\n"
                "CRITICAL: Generate ONLY actual HTML, CSS, and JavaScript code. Do NOT use <think> tags or any thinking process. Output ONLY the code blocks.\n"
                "PROJECT: {task_description}\n"
                "DESCRIPTION: {task_description}\n"
                "AGENT OUTPUTS:\n{chr(10).join(agent_outputs)}\n"
                "Format your response EXACTLY as:\n"
                "=== HTML CODE ===\n"
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>Your Website</title>\n"
                "</head>\n"
                "<body>\n"
                "    <!-- Your HTML content here -->\n"
                "</body>\n"
                "</html>\n"
                "\n=== CSS CODE ===\n"
                "/* Your CSS styles here */\n"
                "body {\n"
                "    margin: 0;\n"
                "    padding: 0;\n"
                "    font-family: Arial, sans-serif;\n"
                "}\n"
                "\n=== JAVASCRIPT CODE ===\n"
                "// Your JavaScript code here\n"
                "document.addEventListener('DOMContentLoaded', function() {\n"
                "    // Your code here\n"
                "});\n"
                "\nIMPORTANT: Do NOT include any <think> tags or thinking process. Generate ONLY the actual code blocks."
            )
        else:
            base_prompt += "Respond as a professional agent."
        return base_prompt

    async def generate_openai_response(self, task_description: str) -> str:
        """Generuje odpowiedź używając OpenAI API (jeśli dostępne)"""
        try:
            # Tutaj byłaby integracja z OpenAI API
            # client = openai.OpenAI(api_key="your-api-key")
            # response = client.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[{"role": "user", "content": task_description}]
            # )
            # return response.choices[0].message.content
            
            # Na razie symulujemy odpowiedź AI
            return self.generate_simple_response(task_description)
        except Exception as e:
            print(f"Błąd OpenAI: {e}")
            return self.generate_simple_response(task_description)

    def generate_simple_response(self, task_description: str) -> str:
        """Generates simple response based on agent type"""
        if self.agent_type == AgentType.CODER:
            description_lower = task_description.lower()
            # Rozpoznawanie tematu strony
            if "cooking" in description_lower or "kuchnia" in description_lower or "kulinarn" in description_lower:
                title = "Cooking Website"
                theme = "cooking"
                hero_title = "Discover Delicious Recipes!"
                hero_subtitle = "Your source for cooking inspiration and tips"
                nav_items = ["Home", "Recipes", "Blog", "Gallery", "Contact"]
                about_cards = [
                    ("Tasty Recipes", "Explore a variety of delicious recipes from around the world."),
                    ("Cooking Tips", "Get expert tips and tricks to improve your cooking skills."),
                    ("Healthy Eating", "Find healthy and nutritious meal ideas for every day.")
                ]
                services_cards = [
                    ("Recipe Database", "Thousands of recipes with step-by-step instructions."),
                    ("Cooking Blog", "Articles, tips, and stories from passionate cooks."),
                    ("Photo Gallery", "Beautiful images of dishes and ingredients.")
                ]
            elif "kosmos" in description_lower or "space" in description_lower:
                title = "Space Website"
                theme = "space"
                hero_title = "Discover the Secrets of Space!"
                hero_subtitle = "Your source of information about the universe"
                nav_items = ["Home", "Planets", "Galaxies", "Exploration", "Contact"]
                about_cards = [
                    ("Space Exploration", "Learn about missions and discoveries in space."),
                    ("Planets", "Explore the planets of our solar system."),
                    ("Astronomy", "Understand the science behind the stars.")
                ]
                services_cards = [
                    ("Telescope Guide", "How to choose and use a telescope."),
                    ("Space News", "Latest news from the cosmos."),
                    ("Astrophotography", "Tips for photographing the night sky.")
                ]
            elif "football" in description_lower or "piłka" in description_lower:
                title = "Football Website"
                theme = "football"
                hero_title = "Welcome to the World of Football!"
                hero_subtitle = "Your source of football information"
                nav_items = ["Home", "News", "Teams", "Contact"]
                about_cards = [
                    ("Football News", "Latest updates from the world of football."),
                    ("Teams", "Information about top football teams."),
                    ("Match Analysis", "In-depth analysis of recent matches.")
                ]
                services_cards = [
                    ("Live Scores", "Up-to-date scores from all leagues."),
                    ("Player Stats", "Statistics and profiles of players."),
                    ("Fan Zone", "Community for football fans.")
                ]
            else:
                # Uniwersalny motyw na podstawie tytułu/tematu z opisu
                import re
                match = re.search(r'(?:about|for|on|titled|temat|o) ([a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ ]+)[.\n]', description_lower)
                if match:
                    theme = match.group(1).strip().capitalize()

                    title = f"{theme} Website"
                    hero_title = f"Welcome to our {theme} website!"
                    hero_subtitle = f"All about {theme.lower()} in one place."
                    nav_items = ["Home", "About", "Services", "Contact"]
                else:
                    title = "Modern Website"
                    theme = "modern"
                    hero_title = "Welcome to our website!"
                    hero_subtitle = "Modern internet solutions"
                    nav_items = ["Home", "About", "Services", "Contact"]
                about_cards = [
                    ("Innovative Solutions", "We create modern websites using the latest web technologies."),
                    ("Responsive Design", "Our websites look perfect on all devices - from phones to large monitors."),
                    ("SEO Optimization", "We ensure the best visibility in search engines and maximum marketing effectiveness.")
                ]
                services_cards = [
                    ("Website Design", "Professional design and implementation of websites."),
                    ("E-commerce", "Online stores with full sales functionality."),
                    ("Technical Support", "24/7 technical support and website maintenance.")
                ]
            # Dalej generuj kod HTML jak poprzednio, ale użyj powyższych zmiennych
            about_cards_html = "".join([
                f'<div class="card"><h3>{title}</h3><p>{desc}</p></div>' for title, desc in about_cards
            ])
            services_cards_html = "".join([
                f'<div class="card"><h3>{title}</h3><p>{desc}</p></div>' for title, desc in services_cards
            ])
            return f"""{self.name}: I have generated complete website code!

=== HTML/CSS/JavaScript CODE ===

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        /* Navigation */
        nav {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 0;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        nav .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
        }}
        
        nav .logo {{
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
        }}
        
        nav ul {{
            display: flex;
            list-style: none;
        }}
        
        nav ul li {{
            margin-left: 2rem;
        }}
        
        nav ul li a {{
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }}
        
        nav ul li a:hover {{
            color: #ffd700;
        }}
        
        /* Hero Section */
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8rem 2rem 4rem;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .hero h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: fadeInUp 1s ease;
        }}
        
        .hero p {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }}
        
        .cta-button {{
            background: #ffd700;
            color: #333;
            padding: 1rem 2rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        
        .cta-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        /* Container */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}
        
        .section {{
            margin-bottom: 4rem;
        }}
        
        .section h2 {{
            font-size: 2.5rem;
            margin-bottom: 2rem;
            text-align: center;
            color: #333;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}
        
        .card {{
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h3 {{
            color: #667eea;
            margin-bottom: 1rem;
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            nav .nav-container {{
                flex-direction: column;
                padding: 1rem;
            }}
            
            nav ul {{
                margin-top: 1rem;
            }}
            
            nav ul li {{
                margin-left: 1rem;
                margin-right: 1rem;
            }}
            
            .hero h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 2rem 1rem;
            }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <div class="logo">{title}</div>
            <ul>
                {''.join([f'<li><a href="#{item.lower().replace(" ", "-")}">{item}</a></li>' for item in nav_items])}
            </ul>
        </div>
    </nav>
    
    <div class="hero">
        <h1>{hero_title}</h1>
        <p>{hero_subtitle}</p>
        <a href="#content" class="cta-button">Learn More</a>
    </div>
    
    <div class="container" id="content">
        <div class="section">
            <h2>About Us</h2>
            <div class="grid">{about_cards_html}</div>
        </div>
        
        <div class="section">
            <h2>Our Services</h2>
            <div class="grid">{services_cards_html}</div>
        </div>
    </div>
    
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
        
        // Navigation animation on scroll
        window.addEventListener('scroll', function() {{
            const nav = document.querySelector('nav');
            if (window.scrollY > 100) {{
                nav.style.background = 'rgba(102, 126, 234, 0.95)';
            }} else {{
                nav.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }}
        }});
        
        // Add animations for cards on scroll
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};
        
        const observer = new IntersectionObserver(function(entries) {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.card').forEach(card => {{
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        }});
    </script>
</body>
</html>

=== TECHNICAL INFORMATION ===
✅ Code is fully responsive
✅ Contains CSS and JavaScript animations
✅ SEO optimized
✅ Compatible with all modern browsers
✅ Ready for server deployment

Code has been generated by {self.name} and is ready to use!"""
        elif self.agent_type == AgentType.ANALYST:
            return f"""{self.name}: I have analyzed data and prepared a comprehensive report:

=== DATA ANALYSIS REPORT ===

PROJECT: {task_description}

ANALYSIS RESULTS:
📊 Data Processing: Completed
📈 Statistical Analysis: Completed
📋 Report Generation: Completed

KEY FINDINGS:
- Most popular teams: Real Madrid, Barcelona, Manchester United
- Season statistics: 380 matches, average 2.7 goals per match
- Trends: 15% increase in popularity among young viewers
- Market analysis: Growing interest in online streaming

RECOMMENDATIONS:
1. Focus on content marketing and social media
2. Implement data-driven decision making
3. Optimize user engagement metrics
4. Develop mobile-first strategies

TECHNICAL DETAILS:
✅ Python pandas for data processing
✅ Statistical analysis with scikit-learn
✅ Data visualization with matplotlib
✅ SQL database integration
✅ Machine learning insights

Report prepared by {self.name} - Data Analyst & Programmer"""
        elif self.agent_type == AgentType.IMAGE_GEN:
            return f"""{self.name}: I have prepared DALL-E prompts and image specifications:

=== DALL-E PROMPTS FOR WEBSITE ===

PROJECT: {task_description}

DETAILED PROMPTS:

1. "Professional football stadium with modern architecture, wide angle view, photorealistic, high quality, 4K"
   - Use for: Hero background image
   - Style: Photorealistic, dramatic lighting
   - Dimensions: 1920x1080px

2. "Football player in action, dynamic pose, professional sports photography, sharp focus, vibrant colors"
   - Use for: Player showcase section
   - Style: Sports photography, action shot
   - Dimensions: 800x600px

3. "Football team logo design, modern minimalist style, clean lines, professional branding, vector style"
   - Use for: Team logos
   - Style: Modern, minimalist, professional
   - Format: PNG with transparency

4. "Football field from above, green grass, white lines, aerial view, professional sports photography"
   - Use for: Background elements
   - Style: Aerial photography, natural lighting
   - Dimensions: 1920x1080px

5. "Football equipment collection, ball, boots, gloves, professional sports gear, studio lighting"
   - Use for: Equipment section
   - Style: Product photography, clean background
   - Dimensions: 600x400px

TECHNICAL SPECIFICATIONS:
✅ All images optimized for web (1920x1080px)
✅ PNG format for logos, JPG for photos
✅ Color palette: Green (#1a5f1a), White (#ffffff), Gold (#ffd700)
✅ Responsive design compatible
✅ SEO optimized with alt tags
✅ WebP format for better compression

IMAGE GENERATION WORKFLOW:
1. DALL-E prompt creation
2. Image generation and refinement
3. Quality optimization
4. Format conversion
5. Web optimization

All prompts are ready for DALL-E generation and will create professional website imagery.

Prepared by {self.name} - AI Image Generator"""
        elif self.agent_type == AgentType.TEXT_ANALYST:
            return f"""{self.name}: I have written articles and content:

=== CONTENT CREATION REPORT ===

PROJECT: {task_description}

ARTICLES CREATED:

1. "History of Football in Poland"
   - Word count: 1500 words
   - SEO optimized: ✅
   - Keywords: football history, Polish football, sports heritage
   - Structure: Introduction, Historical periods, Modern era, Conclusion
   - Target audience: Sports enthusiasts, History buffs

2. "Guide to the Biggest Leagues"
   - Word count: 2000 words
   - SEO optimized: ✅
   - Keywords: Premier League, La Liga, Serie A, football leagues
   - Structure: League overview, Team analysis, Style comparison, Statistics
   - Includes: Infographics, Data visualization

3. "Football World News"
   - Word count: 500 words (daily)
   - SEO optimized: ✅
   - Keywords: football news, transfers, matches, updates
   - Structure: Breaking news, Transfer updates, Match reports
   - Frequency: Daily updates

CONTENT STRATEGY:
✅ SEO optimization for all articles
✅ Mobile-friendly content structure
✅ Social media sharing optimization
✅ Internal linking strategy
✅ Call-to-action integration

TECHNICAL FEATURES:
✅ Responsive text formatting
✅ Image alt text optimization
✅ Meta descriptions
✅ Schema markup
✅ Social media meta tags

All texts are ready for publication and SEO optimized.

Created by {self.name} - Text Analyst"""
        else:
            return f"{self.name}: Task has been processed and completed successfully."

    async def process_task(self, task, office=None):
        self.office = office
        action = self.decide(task.description)
        if office and office.gui:
            office.gui.update_communication_log(f"[{self.name}] 🚀 Starting work on task: {task.title}")
            office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about: {task.description[:100]}...")
            office.gui.update_task_status(f"🔄 {self.name} working on task: {task.title}")
        if office:
            await self._communicate_with_team(task, office)
        await asyncio.sleep(2.0)  # Wydłużony czas symulacji pracy agenta
        
        # AI Graphic Designer: Qwen3 + Kandinsky 2.2 (kandinsky2 lib)
        if self.role == "AI Graphic Designer":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about graphic design for: {task.description[:100]}...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about graphic design for: {task.description[:100]}...")
            qwen_prompt = self._create_qwen_prompt(task.description)
            qwen_response = await self.generate_ollama_response(qwen_prompt)
            prompts = []
            for line in qwen_response.splitlines():
                if "|" in line and not line.strip().startswith("|"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        prompts.append(parts[1])
            # model = get_kandinsky2_model()
            image_paths = []
            for i, prompt in enumerate(prompts):
                try:
                    # images = model.generate_text2img(prompt, decoder_steps=50, batch_size=1, h=1024, w=768)
                    # img = images[0] if isinstance(images, (list, tuple, np.ndarray)) else images
                    image_path = f"kandinsky2_img_{self.id}_{i}.png"
                    # if isinstance(img, np.ndarray):
                    #     img = Image.fromarray(img)
                    # img.save(image_path)
                    image_paths.append((prompt, image_path))
                except Exception as e:
                    image_paths.append((prompt, f"[ERROR: {e}]") )
            result = "=== GRAPHIC DESIGN REPORT ===\n"
            result += "Prompts and generated images:\n"
            for prompt, path in image_paths:
                result += f"- Prompt: {prompt}\n  Image: {path}\n"
            result += "\nQwen3 table:\n" + qwen_response
        # Chatbot: komunikacja z użytkownikiem i override
        if self.role == "AI Chatbot":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about user interaction and chatbot responses...")
            # Jeśli użytkownik podał komendę 'Override: ...', nadpisz wynik
            if task.description.strip().lower().startswith("override:"):
                override_content = task.description.strip()[9:].strip()
                result = f"[USER OVERRIDE] {override_content}"
            else:
                # Symulacja rozmowy z użytkownikiem i agentami
                result = (
                    "=== CHATBOT SESSION ===\n"
                    "Hello! I am your AI assistant.\n"
                    "You can ask me to override any part of the project (plan, code, content, design).\n"
                    "Type: 'Override: <your change>' to update the final output.\n"
                    "I will communicate your wishes to the team and update the project accordingly.\n"
                )
        elif self.role == "Copywriter":
            # Generowanie profesjonalnych tekstów
            result = (
                "=== COPYWRITING DELIVERABLES ===\n"
                "- SEO-optimized homepage headline: 'Discover the Art of Cooking with Us!'\n"
                "- Blog post title: '10 Quick & Healthy Recipes for Busy People'\n"
                "- Product description: 'Our kitchen tools are designed for both amateur cooks and professionals.'\n"
                "- Call-to-action: 'Start Your Culinary Journey Today!'\n"
                "- Meta description: 'Explore delicious recipes, expert tips, and a vibrant cooking community.'\n"
            )
        elif self.role == "UX/UI Designer":
            # Makiety, user flow, rekomendacje UI
            result = (
                "=== UX/UI DESIGN DELIVERABLES ===\n"
                "- Wireframe: Homepage with hero section, featured recipes, blog, gallery, contact form\n"
                "- User flow: Easy navigation from homepage to recipes, blog, and contact\n"
                "- Color palette: Warm tones (orange, cream, green)\n"
                "- Typography: Modern, readable sans-serif\n"
                "- UI style: Clean, lots of white space, large images\n"
                "- Accessibility: High contrast, keyboard navigation, alt text for images\n"
            )
        # Rozbudowane zachowania dla wybranych ról
        elif self.role == "Project Manager":
            import datetime
            today = datetime.date.today()
            schedule = f"=== PROJECT SCHEDULE ===\n"
            schedule += f"Start date: {today}\n"
            schedule += f"1. Website Skeleton (Web Developer): {today + datetime.timedelta(days=1)}\n"
            schedule += f"2. UI/UX Layout (UX/UI Designer): {today + datetime.timedelta(days=2)}\n"
            schedule += f"3. Content Writing (Copywriter): {today + datetime.timedelta(days=3)}\n"
            schedule += f"4. Website Graphics (AI Graphic Designer): {today + datetime.timedelta(days=4)}\n"
            schedule += f"5. Integration & Testing (Integrator): {today + datetime.timedelta(days=5)}\n"
            schedule += f"6. Marketing Campaign (Marketing Strategist): {today + datetime.timedelta(days=6)}\n"
            schedule += f"7. Data Analysis (Data Analyst): {today + datetime.timedelta(days=7)}\n"
            schedule += f"8. Chatbot Deployment (AI Chatbot): {today + datetime.timedelta(days=8)}\n"
            schedule += f"\n=== TASK SPLIT ===\n- Web Developer: Build website skeleton\n- UX/UI Designer: Design layout and user flow\n- Copywriter: Write SEO content\n- AI Graphic Designer: Prepare graphics\n- Integrator: Integrate, test, publish\n- Marketing Strategist: Plan and monitor campaign\n- Data Analyst: Analyze campaign effectiveness\n- AI Chatbot: Handle visitor questions\n"
            result = schedule
        elif self.role == "Marketing Strategist":
            result = (
                "=== MARKETING CAMPAIGN PLAN ===\n"
                "- Platform: Google Ads, Facebook, Instagram, LinkedIn\n"
                "- Target groups: Cooking enthusiasts, foodies, home cooks\n"
                "- Content: Blog posts, video recipes, social media banners\n"
                "- Budget: $2000/month\n"
                "- KPIs: Click-through rate, conversion rate, engagement\n"
                "\n=== MONITORING ===\n"
                "- Daily performance tracking\n"
                "- Weekly optimization meetings\n"
                "- A/B testing of ads and landing pages\n"
                "- Real-time dashboard (Power BI)\n"
            )
        elif self.role == "Data Analyst":
            result = (
                "=== DATA ANALYSIS REPORT ===\n"
                "- Google Analytics: 12,000 visits, 3.5% conversion\n"
                "- Facebook Pixel: 2,000 ad clicks, 1,200 signups\n"
                "- ROI: 350%\n"
                "- Top sources: Google Search, Facebook Ads\n"
                "- User engagement: Avg. time on site 3:45 min\n"
                "- Recommendations: Increase video content, optimize mobile UX, retarget high-value users\n"
                "- KPI charts and trends attached (see dashboard)\n"
            )
        elif self.role == "Integrator (Coordinator)":
            # Zbierz wyniki od wszystkich agentów
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about integrating all agent outputs...")
                office.gui.update_communication_log(f"[{self.name}] 💭 Analyzing project requirements and agent results...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about integrating all agent outputs...")
            print(f"TERMINAL: [{self.name}] 💭 Analyzing project requirements and agent results...")
            
            summary = (
                "=== INTEGRATOR MASTER REPORT ===\n"
                "- Quality control: All modules checked\n"
                "- Dependencies: Layout changes trigger SEO/content updates\n"
                "- Strategic decisions: Approved\n"
                "- Final product: Ready for client presentation\n"
            )
            # Jeśli office i task.parent_task_id istnieje, zbierz wyniki podzadań
            agent_outputs = []
            if office and task.parent_task_id:
                parent_task = office.tasks.get(task.parent_task_id)
                if parent_task:
                    for sub_id in parent_task.results:
                        agent_name = office.agents[sub_id].name if sub_id in office.agents else sub_id
                        agent_result = parent_task.results[sub_id]
                        agent_outputs.append(f"--- {agent_name} ---\n{agent_result}")
            
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Collected outputs from {len(agent_outputs)} agents")
                office.gui.update_communication_log(f"[{self.name}] 💭 Preparing to generate final website code...")
            
            # Buduj prompt dla Qwen3
            prompt = (
                "You are a senior fullstack developer. Generate a complete, modern, responsive cooking website.\n"
                f"PROJECT: {task.title}\n"
                f"DESCRIPTION: {task.description}\n"
                "CRITICAL: Generate ONLY actual HTML, CSS, and JavaScript code. Do NOT use <think> tags or any thinking process. Output ONLY the code blocks.\n"
                "Format your response EXACTLY as:\n"
                "=== HTML CODE ===\n"
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>Cooking Website</title>\n"
                "</head>\n"
                "<body>\n"
                "    <nav>\n"
                "        <div class=\"nav-container\">\n"
                "            <div class=\"logo\">Cooking Delights</div>\n"
                "            <ul>\n"
                "                <li><a href=\"#home\">Home</a></li>\n"
                "                <li><a href=\"#recipes\">Recipes</a></li>\n"
                "                <li><a href=\"#blog\">Blog</a></li>\n"
                "                <li><a href=\"#contact\">Contact</a></li>\n"
                "            </ul>\n"
                "        </div>\n"
                "    </nav>\n"
                "    <div class=\"hero\">\n"
                "        <h1>Discover Delicious Recipes!</h1>\n"
                "        <p>Your source for cooking inspiration and tips</p>\n"
                "        <a href=\"#recipes\" class=\"cta-button\">Explore Recipes</a>\n"
                "    </div>\n"
                "    <div class=\"container\">\n"
                "        <div class=\"section\">\n"
                "            <h2>About Us</h2>\n"
                "            <div class=\"grid\">\n"
                "                <div class=\"card\">\n"
                "                    <h3>Tasty Recipes</h3>\n"
                "                    <p>Explore a variety of delicious recipes from around the world.</p>\n"
                "                </div>\n"
                "                <div class=\"card\">\n"
                "                    <h3>Cooking Tips</h3>\n"
                "                    <p>Get expert tips and tricks to improve your cooking skills.</p>\n"
                "                </div>\n"
                "                <div class=\"card\">\n"
                "                    <h3>Healthy Eating</h3>\n"
                "                    <p>Find healthy and nutritious meal ideas for every day.</p>\n"
                "                </div>\n"
                "            </div>\n"
                "        </div>\n"
                "    </div>\n"
                "</body>\n"
                "</html>\n"
                "\n=== CSS CODE ===\n"
                "* {\n"
                "    margin: 0;\n"
                "    padding: 0;\n"
                "    box-sizing: border-box;\n"
                "}\n"
                "body {\n"
                "    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n"
                "    line-height: 1.6;\n"
                "    color: #333;\n"
                "}\n"
                "nav {\n"
                "    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n"
                "    padding: 1rem 0;\n"
                "    position: fixed;\n"
                "    width: 100%;\n"
                "    top: 0;\n"
                "    z-index: 1000;\n"
                "}\n"
                ".hero {\n"
                "    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n"
                "    color: white;\n"
                "    padding: 8rem 2rem 4rem;\n"
                "    text-align: center;\n"
                "    min-height: 100vh;\n"
                "    display: flex;\n"
                "    flex-direction: column;\n"
                "    justify-content: center;\n"
                "    align-items: center;\n"
                "}\n"
                ".cta-button {\n"
                "    background: #ffd700;\n"
                "    color: #333;\n"
                "    padding: 1rem 2rem;\n"
                "    border: none;\n"
                "    border-radius: 50px;\n"
                "    font-size: 1.1rem;\n"
                "    font-weight: bold;\n"
                "    cursor: pointer;\n"
                "    text-decoration: none;\n"
                "    display: inline-block;\n"
                "}\n"
                "\n=== JAVASCRIPT CODE ===\n"
                "document.addEventListener('DOMContentLoaded', function() {\n"
                "    // Smooth scrolling for navigation links\n"
                "    document.querySelectorAll('a[href^=\"#\"]').forEach(anchor => {\n"
                "        anchor.addEventListener('click', function (e) {\n"
                "            e.preventDefault();\n"
                "            const target = document.querySelector(this.getAttribute('href'));\n"
                "            if (target) {\n"
                "                target.scrollIntoView({\n"
                "                    behavior: 'smooth',\n"
                "                    block: 'start'\n"
                "                });\n"
                "            }\n"
                "        });\n"
                "    });\n"
                "});\n"
            )
            # Wywołaj Qwen3 (Ollama)
            if OLLAMA_AVAILABLE:
                qwen_code = await self.generate_ollama_response(prompt)
            else:
                qwen_code = self.generate_simple_response(prompt)
            result = summary + "\n\n=== QWEN3 FINAL CODE ===\n" + qwen_code

        # Mobile Responsiveness & Testing Agent
        elif self.role == "Mobile Responsiveness & Testing Agent":
            result = (
                "=== MOBILE RESPONSIVENESS & TESTING REPORT ===\n"
                "- Mobile view: PASSED\n"
                "- Tablet view: PASSED\n"
                "- Desktop view: PASSED\n"
                "- Automated tests: Playwright, Cypress, Lighthouse\n"
                "- PWA compliance: YES\n"
                "- App Manifest: Configured\n"
                "- Issues found: None\n"
            )
        # Feedback & QA Agent
        elif self.role == "Feedback & QA Agent":
            result = (
                "=== FEEDBACK & QA REPORT ===\n"
                "- Regression tests: PASSED\n"
                "- Client feedback: 'Great usability and design!'\n"
                "- Visitor feedback: 'Loads fast, easy to use.'\n"
                "- Pre-launch checklist: All items checked\n"
                "- Repository archived\n"
                "- Ready for marketing\n"
            )
        # Client Briefing Agent (rozbudowany)
        elif self.role == "Client Advisor":
            # Wykrywanie nieścisłości, pytania, KPI, target group
            result = (
                "=== CLIENT BRIEF ===\n"
                "- Project goal: " + (task.description.split('\n')[0] if '\n' in task.description else task.description) + "\n"
                "- Detected ambiguities: None\n"
                "- Follow-up questions: What is your main target audience? What is your main KPI?\n"
                "- Target group: Cooking enthusiasts, home cooks\n"
                "- KPIs: Conversion rate, newsletter signups\n"
                "- Scope: Website, blog, gallery, contact\n"
            )
        # Project Manager (rozbudowany)
        elif self.role == "Project Manager":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about project planning and task coordination...")
                office.gui.update_communication_log(f"[{self.name}] 💭 Planning timeline, resource allocation, and risk management...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about project planning and task coordination...")
            print(f"TERMINAL: [{self.name}] 💭 Planning timeline, resource allocation, and risk management...")
            import datetime
            today = datetime.date.today()
            schedule = f"=== PROJECT SCHEDULE ===\n"
            schedule += f"Start date: {today}\n"
            schedule += f"1. Website Skeleton (Web Developer): {today + datetime.timedelta(days=1)}\n"
            schedule += f"2. UI/UX Layout (UX/UI Designer): {today + datetime.timedelta(days=2)}\n"
            schedule += f"3. Content Writing (Copywriter): {today + datetime.timedelta(days=3)}\n"
            schedule += f"4. Website Graphics (AI Graphic Designer): {today + datetime.timedelta(days=4)}\n"
            schedule += f"5. Integration & Testing (Integrator): {today + datetime.timedelta(days=5)}\n"
            schedule += f"6. Mobile Testing (Mobile Responsiveness & Testing Agent): {today + datetime.timedelta(days=6)}\n"
            schedule += f"7. Feedback & QA (Feedback & QA Agent): {today + datetime.timedelta(days=7)}\n"
            schedule += f"8. Marketing Campaign (Marketing Strategist): {today + datetime.timedelta(days=8)}\n"
            schedule += f"9. Data Analysis (Data Analyst): {today + datetime.timedelta(days=9)}\n"
            schedule += f"10. Chatbot Deployment (AI Chatbot): {today + datetime.timedelta(days=10)}\n"
            schedule += f"\n=== TASK SPLIT ===\n- Web Developer: Build website skeleton\n- UX/UI Designer: Design layout and user flow\n- Copywriter: Write SEO content\n- AI Graphic Designer: Prepare graphics\n- Integrator: Integrate, test, publish\n- Mobile Responsiveness & Testing Agent: Test all devices\n- Feedback & QA Agent: Collect feedback, run regression tests\n- Marketing Strategist: Plan and monitor campaign\n- Data Analyst: Analyze campaign effectiveness\n- AI Chatbot: Handle visitor questions\n"
            schedule += f"\n=== RISK MONITORING ===\n- Timeline delays: LOW\n- Resource availability: OK\n- Brief compliance: CHECKED\n"
            result = schedule
        # Web/App Developer (rozbudowany)
        elif self.role == "Web Developer":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about website structure and code architecture...")
                office.gui.update_communication_log(f"[{self.name}] 💭 Planning HTML structure, CSS styling, and JavaScript functionality...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about website structure and code architecture...")
            print(f"TERMINAL: [{self.name}] 💭 Planning HTML structure, CSS styling, and JavaScript functionality...")
            result = self.generate_simple_response(task.description)
        # UI/UX Designer (rozbudowany)
        elif self.role == "UX/UI Designer":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about user experience and interface design...")
                office.gui.update_communication_log(f"[{self.name}] 💭 Planning color schemes, typography, and user flow...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about user experience and interface design...")
            print(f"TERMINAL: [{self.name}] 💭 Planning color schemes, typography, and user flow...")
            result = (
                "=== UX/UI DESIGN DELIVERABLES ===\n"
                "- Design system: Figma, Tailwind export\n"
                "- Accessibility: WCAG 2.1 checked\n"
                "- User flow: Tested\n"
                "- Mockups: Exported\n"
                "- Style: Modern, clean\n"
            )
        # Copywriter & SEO Agent (rozbudowany)
        elif self.role == "Copywriter":
            if office and office.gui:
                office.gui.update_communication_log(f"[{self.name}] 💭 Thinking about content strategy and SEO optimization...")
                office.gui.update_communication_log(f"[{self.name}] 💭 Planning engaging headlines and compelling copy...")
            print(f"TERMINAL: [{self.name}] 💭 Thinking about content strategy and SEO optimization...")
            print(f"TERMINAL: [{self.name}] 💭 Planning engaging headlines and compelling copy...")
            result = (
                "=== COPYWRITING & SEO REPORT ===\n"
                "- SEO texts: Homepage, product, blog\n"
                "- Keywords: Cooking, recipes, healthy food\n"
                "- Headings: Structured (H1-H3)\n"
                "- Competitor analysis: SEMrush API\n"
                "- Meta tags: Generated\n"
                "- OpenGraph: Ready\n"
                "- Internal linking: Implemented\n"
            )
        # AI Graphic Agent (rozbudowany)
        elif self.role == "AI Graphic Designer":
            result = (
                "=== GRAPHIC DESIGN REPORT ===\n"
                "- Logo: DALL·E, Midjourney\n"
                "- Icons: Generated\n"
                "- Mockups: Ready\n"
                "- Visual consistency: Checked\n"
                "- Image compression: WebP, AVIF\n"
                "- Platform styles: Social, web, mobile\n"
            )
        # Marketing Strategy Agent (rozbudowany)
        elif self.role == "Marketing Strategist":
            result = (
                "=== MARKETING STRATEGY REPORT ===\n"
                "- Campaigns: Google Ads, Meta, LinkedIn\n"
                "- Segmentation: Retargeting, lookalike\n"
                "- Lead magnets: eBook, newsletter\n"
                "- Funnels: Multi-step\n"
                "- Schedule: 3 months\n"
                "- Budget: $2000/month\n"
            )
        # AI Chatbot Agent (rozbudowany)
        elif self.role == "AI Chatbot":
            if task.description.strip().lower().startswith("override:"):
                override_content = task.description.strip()[9:].strip()
                result = f"[USER OVERRIDE] {override_content}"
            else:
                result = (
                    "=== CHATBOT SESSION ===\n"
                    "- Conversation scenarios: FAQ, product info, support\n"
                    "- CRM integration: HubSpot, Mailchimp\n"
                    "- Forms: Contact, offer requests\n"
                    "- Context memory: Enabled\n"
                    "- Session tracking: Active\n"
                )
        # Data Analyst & Reporting Agent (rozbudowany)
        elif self.role == "Data Analyst":
            result = (
                "=== DATA ANALYSIS & REPORTING ===\n"
                "- Analytics: GA4, Facebook Pixel, Matomo\n"
                "- Dashboards: Power BI, Tableau\n"
                "- UX analysis: Heatmaps, scroll depth\n"
                "- Reports: Daily, monthly\n"
                "- Recommendations: CRO, UX improvements\n"
            )
        # Hosting & Deployment Agent (rozbudowany)
        elif self.role == "Hosting/DevOps":
            result = (
                "=== HOSTING & DEPLOYMENT REPORT ===\n"
                "- Hosting: Vercel, Netlify, AWS\n"
                "- CI/CD: GitHub Actions\n"
                "- Domain: Configured\n"
                "- SSL: Enabled\n"
                "- Cache: Optimized\n"
                "- Backups: Scheduled\n"
                "- Uptime: 99.99%\n"
            )


        if 'result' not in locals():
            result = f"{self.name}: Task has been processed and completed successfully."
        task.results[self.id] = result
        from tasks import TaskStatus
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.updated_at = time.time()
        if office and office.gui:
            office.gui.update_task_status(f"✅ {self.name} completed task {task.id} ({action})")
            office.gui.update_communication_log(f"[{self.name}] ✅ Completed task: {task.title}")
        return task

    async def _communicate_with_team(self, task, office):
        """Communicate with other agents about the task"""
        if not office or not office.gui:
            return
            
        # Find other agents to communicate with
        other_agents = [agent for agent in office.agents.values() if agent.id != self.id]
        
        for other_agent in other_agents:
            # Send message to other agent
            message_content = self._create_team_message(task, other_agent)
            if message_content:
                # Log conference room communication
                conference_msg = f"<talk {self.name} to {other_agent.name}> {message_content}"
                if office.gui:
                    office.gui.update_conference_room(conference_msg)
                    print(f"DEBUG: wysłano do Conference Room: {conference_msg}")
                
                await self.send_message(other_agent, message_content, task.id, office)
                
                # Simulate response from other agent
                await asyncio.sleep(0.5)
                response = other_agent._create_response_message(task, self)
                if response:
                    # Log conference room response
                    conference_response = f"<talk {other_agent.name} to {self.name}> {response}"
                    if office.gui:
                        office.gui.update_conference_room(conference_response)
                        print(f"DEBUG: wysłano do Conference Room: {conference_response}")
                    
                    await other_agent.send_message(self, response, task.id, office)

    def _create_team_message(self, task, other_agent):
        """Create appropriate message for team communication"""
        if self.agent_type == AgentType.CODER and other_agent.agent_type == AgentType.ANALYST:
            return f"Hey {other_agent.name}, I'm working on the website code. Do you have any data analysis results that should be integrated into the design?"
        elif self.agent_type == AgentType.ANALYST and other_agent.agent_type == AgentType.CODER:
            return f"Hi {other_agent.name}, I'm analyzing the data. What kind of visualizations would work best for the website?"
        elif self.agent_type == AgentType.IMAGE_GEN and other_agent.agent_type == AgentType.TEXT_ANALYST:
            return f"Hello {other_agent.name}, I'm preparing image prompts. What content themes should I focus on for the visuals?"
        elif self.agent_type == AgentType.TEXT_ANALYST and other_agent.agent_type == AgentType.IMAGE_GEN:
            return f"Hi {other_agent.name}, I'm writing content. What image styles would complement the articles best?"
        elif self.agent_type == AgentType.BOSS and other_agent.agent_type != AgentType.BOSS:
            return f"Hello {other_agent.name}, I'm coordinating the project. How is your part of the task progressing?"
        elif other_agent.agent_type == AgentType.BOSS and self.agent_type != AgentType.BOSS:
            return f"Hi {other_agent.name}, I'm working on my assigned task. Do you have any specific requirements or feedback?"
        elif self.role == "Web Developer" and other_agent.role == "UX/UI Designer":
            return f"Hey {other_agent.name}, I'm building the website structure. What design elements should I prioritize for the layout?"
        elif self.role == "UX/UI Designer" and other_agent.role == "Web Developer":
            return f"Hi {other_agent.name}, I'm designing the user interface. What technical constraints should I consider for the implementation?"
        elif self.role == "Copywriter" and other_agent.role == "AI Graphic Designer":
            return f"Hello {other_agent.name}, I'm writing the website content. What visual themes would work best with the text I'm creating?"
        elif self.role == "AI Graphic Designer" and other_agent.role == "Copywriter":
            return f"Hi {other_agent.name}, I'm creating graphics. What content themes should I focus on for the visual elements?"
        elif self.role == "Project Manager":
            return f"Hello {other_agent.name}, I'm managing the project timeline. How is your task progressing and do you need any resources?"
        elif self.role == "Marketing Strategist" and other_agent.role in ["Copywriter", "AI Graphic Designer"]:
            return f"Hey {other_agent.name}, I'm planning the marketing campaign. What content or visuals would work best for our target audience?"
        elif self.role == "Data Analyst" and other_agent.role in ["Web Developer", "UX/UI Designer"]:
            return f"Hi {other_agent.name}, I'm analyzing user data. What insights would be most valuable for improving the website design?"
        elif self.role == "Integrator (Coordinator)":
            return f"Hello {other_agent.name}, I'm coordinating the final integration. How is your component coming along and what should I know for the final assembly?"
        elif self.role == "Hosting/DevOps" and other_agent.role == "Web Developer":
            return f"Hey {other_agent.name}, I'm setting up the hosting environment. What technical requirements should I prepare for deployment?"
        elif self.role == "Mobile Responsiveness & Testing Agent":
            return f"Hi {other_agent.name}, I'm testing the mobile responsiveness. Are there any specific features or sections I should pay extra attention to?"
        elif self.role == "Feedback & QA Agent":
            return f"Hello {other_agent.name}, I'm conducting quality assurance. What aspects of your work should I focus on during testing?"
        elif self.role == "AI Chatbot":
            return f"Hi {other_agent.name}, I'm preparing the chatbot responses. What information should I have ready for visitor questions?"
        elif self.role == "Client Advisor":
            return f"Hello {other_agent.name}, I'm gathering client requirements. What specific needs should I communicate to the team?"
        return None

    def _create_response_message(self, task, other_agent):
        """Create response message for team communication"""
        if self.agent_type == AgentType.ANALYST and other_agent.agent_type == AgentType.CODER:
            return f"Thanks {other_agent.name}! I have some key insights that would work well as interactive charts on the website."
        elif self.agent_type == AgentType.CODER and other_agent.agent_type == AgentType.ANALYST:
            return f"Perfect {other_agent.name}! I'll make sure the website can display your data analysis results effectively."
        elif self.agent_type == AgentType.TEXT_ANALYST and other_agent.agent_type == AgentType.IMAGE_GEN:
            return f"Great {other_agent.name}! I'm writing about cooking recipes and culinary tips. Food photography and kitchen imagery would be perfect!"
        elif self.agent_type == AgentType.IMAGE_GEN and other_agent.agent_type == AgentType.TEXT_ANALYST:
            return f"Excellent {other_agent.name}! I'll focus on appetizing food photography and modern kitchen imagery to match your content."
        elif self.agent_type == AgentType.BOSS and other_agent.agent_type != AgentType.BOSS:
            return f"Good progress {other_agent.name}! Keep me updated on any challenges or if you need additional resources."
        elif other_agent.agent_type == AgentType.BOSS and self.agent_type != AgentType.BOSS:
            return f"Thanks {other_agent.name}! I'm making good progress and will let you know if I encounter any issues."
        elif self.role == "Web Developer" and other_agent.role == "UX/UI Designer":
            return f"Perfect {other_agent.name}! I'll implement the design with clean, semantic HTML and responsive CSS. Any specific animations or interactions you'd like me to focus on?"
        elif self.role == "UX/UI Designer" and other_agent.role == "Web Developer":
            return f"Thanks {other_agent.name}! I'm designing with mobile-first approach and accessibility in mind. The layout will be flexible for your implementation."
        elif self.role == "Copywriter" and other_agent.role == "AI Graphic Designer":
            return f"Great {other_agent.name}! I'm writing engaging content about recipes and cooking tips. High-quality food photography would complement the text perfectly."
        elif self.role == "AI Graphic Designer" and other_agent.role == "Copywriter":
            return f"Excellent {other_agent.name}! I'll create appetizing food photography and modern kitchen imagery that matches your engaging content."
        elif self.role == "Project Manager":
            return f"Thanks {other_agent.name}! I'm on track with the timeline. Let me know if you need any adjustments to the schedule or additional resources."
        elif self.role == "Marketing Strategist":
            return f"Perfect {other_agent.name}! I'm planning campaigns that will showcase your work effectively. The content and visuals will be optimized for our target audience."
        elif self.role == "Data Analyst":
            return f"Great {other_agent.name}! I'm analyzing user behavior patterns that will help optimize the design and user experience."
        elif self.role == "Integrator (Coordinator)":
            return f"Excellent {other_agent.name}! I'm ready to integrate your component into the final product. Everything looks good for the final assembly."
        elif self.role == "Hosting/DevOps":
            return f"Perfect {other_agent.name}! I'm preparing the deployment environment. The hosting setup will be optimized for your code requirements."
        elif self.role == "Mobile Responsiveness & Testing Agent":
            return f"Thanks {other_agent.name}! I'm testing across all devices and will ensure everything works perfectly on mobile, tablet, and desktop."
        elif self.role == "Feedback & QA Agent":
            return f"Great {other_agent.name}! I'm conducting thorough testing and will provide detailed feedback to ensure the highest quality."
        elif self.role == "AI Chatbot":
            return f"Perfect {other_agent.name}! I'm preparing helpful responses for visitor questions about recipes, cooking tips, and website features."
        elif self.role == "Client Advisor":
            return f"Excellent {other_agent.name}! I'm gathering all the client requirements and will ensure the final product meets their expectations perfectly."
        return None 