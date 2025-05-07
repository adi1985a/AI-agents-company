# Office Simulation

## Overview
Office Simulation is a Python-based AI-driven tool that simulates a workplace environment. It manages tasks, assigns them to agents based on skills, and facilitates communication via a message bus. Built with asyncio for asynchronous operations, it includes a GUI for real-time monitoring of tasks and communications.

## Features
- **Task Management**: Create, assign, and track tasks with statuses (Pending, In Progress, Blocked, Completed, Failed) and priorities (Low, Medium, High, Critical).
- **Agent Collaboration**: Agents with defined roles, skills, and personalities process tasks and communicate.
- **Communication Bus**: Asynchronous message passing between agents for task coordination.
- **GUI**: Visual interface to monitor task progress, agent activities, and communication logs.
- **Skill-Based Assignment**: Automatically assigns tasks to agents based on required skills.

## Requirements
- Python 3.8+ (due to asyncio usage)
- Libraries:
  - None (assumes `gui` module is provided)
- Module: `gui.py` with `run_gui` function for the graphical interface.

## Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Ensure `gui.py` is in the project directory with the required `run_gui` function.
3. Run the application:
   ```bash
   python main.py
   ```

## Usage
1. Launch the app to start the office simulation.
2. **Simulation**:
   - **Agents**: Predefined agents (e.g., CEO, Data Analyst, Research Specialist) with skills and roles.
   - **Tasks**: Submit tasks via the GUI or programmatically, which are assigned to suitable agents.
   - **Communication**: Agents exchange messages for task coordination, logged in the GUI.
   - **Monitoring**: Track task statuses, agent activities, and results in real-time.
3. **Example**:
   - The simulation creates a boss (Eleanor Wells) and team members (David Chen, Maria Rodriguez).
   - Tasks are delegated by the boss to agents based on skills, with results consolidated and displayed.

## File Structure
- `main.py`: Main script with simulation logic, agent definitions, and task management.
- `gui.py`: (Assumed) GUI module providing the `run_gui` function for visualization.
- `README.md`: This file, providing project documentation.

## Notes
- The `gui.py` module is not provided but assumed to implement a GUI for task and communication monitoring.
- Task processing is simulated with random delays (1-3 seconds); real implementations could integrate actual workflows.
- The app uses in-memory data; persistent storage (e.g., database) could be added for production use.
- asyncio ensures non-blocking task processing and communication.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make changes and commit (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or feedback, open an issue on GitHub or contact the repository owner.