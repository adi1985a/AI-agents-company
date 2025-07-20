#!/usr/bin/env python3
"""
Test script for Conference Room functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import AgentBase, AgentType
from tasks import Task, TaskPriority
from gui import OfficeGUI
import tkinter as tk

class MockGUI:
    """Mock GUI for testing conference room functionality"""
    def __init__(self):
        self.conference_messages = []
        self.communication_messages = []
    
    def update_conference_room(self, message):
        self.conference_messages.append(message)
        print(f"CONFERENCE ROOM: {message}")
    
    def update_communication_log(self, message):
        self.communication_messages.append(message)
        print(f"COMMUNICATION LOG: {message}")

class MockOffice:
    """Mock office for testing"""
    def __init__(self):
        self.agents = {}
        self.gui = MockGUI()
        self.tasks = {}

async def test_agent_communication():
    """Test agent communication functionality"""
    print("🧪 Testing Conference Room functionality...")
    
    # Create mock office
    office = MockOffice()
    
    # Create test agents
    web_dev = AgentBase(
        id="web_dev1",
        name="Alex Carter",
        role="Web Developer",
        agent_type=AgentType.CODER,
        skills=["HTML", "CSS", "JavaScript"],
        personality_traits=["precise", "innovative"],
        preferred_tools=["AI code assistant"],
        collaborators=["ux_ui1"]
    )
    
    ux_designer = AgentBase(
        id="ux_ui1",
        name="Taylor Kim",
        role="UX/UI Designer",
        agent_type=AgentType.IMAGE_GEN,
        skills=["wireframing", "UI design"],
        personality_traits=["creative", "empathetic"],
        preferred_tools=["Figma AI"],
        collaborators=["web_dev1"]
    )
    
    # Add agents to office
    office.agents[web_dev.id] = web_dev
    office.agents[ux_designer.id] = ux_designer
    
    # Create test task
    task = Task(
        title="Test Website",
        description="Create a modern cooking website",
        creator_id="user",
        priority=TaskPriority.MEDIUM
    )
    
    print("\n📋 Testing communication between Web Developer and UX/UI Designer...")
    
    # Test communication
    await web_dev._communicate_with_team(task, office)
    
    print(f"\n✅ Conference Room messages: {len(office.gui.conference_messages)}")
    print(f"✅ Communication Log messages: {len(office.gui.communication_messages)}")
    
    print("\n🎉 Conference Room test completed successfully!")
    return True

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_agent_communication()) 