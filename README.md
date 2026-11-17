Master Yoda vs. Kuro — Linear Regression Boss Battle
An interactive Python desktop game that teaches the fundamentals of Linear Regression through a four-world platform adventure. Play as Master Yoda, complete learning challenges, and defeat the four-armed robot Kuro by applying regression concepts.

Project overview
Instead of learning regression only from notes, players explore the ideas through game missions, interactive graphs, model-fitting activities, and a final knowledge check.

The game is built as a single-file Python application using Tkinter for its graphical interface. It uses Python's standard library for the game, numerical calculations, timing, and local progress storage.

Learning objectives
World	Topic	What the player practises
1. Crystal Valley	Data collection and variables	Identify independent variable X and dependent variable Y, collect samples, and recognise a positive linear trend.
2. Equation Temple	Slope and intercept	Understand ŷ = m*x + c and fit a line by adjusting its parameters.
3. Noise Factory	Residuals, MSE and OLS	Calculate residuals, understand Mean Squared Error, compare a manual fit with Ordinary Least Squares, and run Gradient Descent.
4. Future Zone	Extrapolation	Predict unseen X values and understand why predictions beyond the training range are less certain.
Features
Four themed worlds, each connected to a Linear Regression learning objective.
Platform-game mechanics including movement, jumping, collectibles, hazards, health, score, and boss encounters.
Interactive regression graph and model-fitting controls.
Residual visualisation and Mean Squared Error (MSE) feedback.
Ordinary Least Squares (OLS) reference solution.
A Learning Droid that performs real batch Gradient Descent on the generated dataset.
Learning-rate experiments that demonstrate convergence and divergence.
Extrapolation challenge using the fitted regression model.
Player name entry, elapsed-time tracking, and a five-question end-of-game check-up.
Full-window fade transitions and a laptop-fitted two-column interface.
Local history for attempts, scores, stages completed, MSE values, and check-up evidence.
Technology
Language: Python 3
GUI: Tkinter
Math: Python math and numerical routines implemented in the project
Persistence: JSON
Timing: time.perf_counter()
No third-party Python packages are required. Tkinter must be available in your Python installation.

Requirements
Python 3.9 or newer recommended.
Tkinter support.
Windows: Tkinter is normally included with the official Python installer.
Linux: install the system Tk package if it is missing (for example, python3-tk on Debian/Ubuntu).
macOS: use a Python distribution that includes Tk support.
Run the game
Download or clone this repository.
Open a terminal in the project folder.
Run:
python master_yoda_vs_kuro_final.py
On some systems, use python3 instead.

Controls
Key	Action
Left / Right or A / D	Move
Space / Up / W	Jump
F or X	Lightsaber swing
C	Collect the next sample in World 1
H	Ask the Learning Droid for a hint
Enter	Start, confirm, or retry
P	Pause or resume
T	Open tutorial
K	Open the knowledge check-up
R	Restart
Esc	Close the tutorial or resume from pause
Run the built-in tests
The project includes a self-test mode for its regression mathematics and learning-data checks. It does not open the game window.

python master_yoda_vs_kuro_final.py --selftest
The checks cover OLS slope and intercept, MSE, gradients, Gradient Descent convergence and divergence, random-data tests, degenerate input handling, evidence statistics, quiz structure, and learning objectives.

View saved learning history
During play, the game stores history in yoda_kuro_history.json next to the Python file when possible. It falls back to a hidden file in the user's home folder if the project directory is not writable.

To print a summary report:

python master_yoda_vs_kuro_final.py --report
To report on a specific history JSON file:

python master_yoda_vs_kuro_final.py --report path/to/yoda_kuro_history.json
The history file is generated locally when the game is run; it does not need to be committed to GitHub.

Suggested repository structure
.
├── master_yoda_vs_kuro_final.py  # Main game application
├── README.md                     # Project documentation
├── GITHUB_DESCRIPTION.md         # Repository and presentation descriptions
└── yoda_kuro_history.json        # Generated locally after playing
Project presentation
The accompanying PowerPoint introduces the project, explains its learning objectives and four-world structure, outlines the Linear Regression concepts, describes the gameplay and technology, and summarises the educational value of the application.

Notes
Each new game generates fresh data; saved history is used to compare progress and performance, not to reuse old model parameters.
The game is an educational demonstration and is not intended as a production regression-analysis package.
The title uses familiar Star Wars-inspired characters as a theme for the learning game.
Project team
Team member	Student ID
Siddhant Gupta	EC24B1120
Lokesh Sobale	EC24B1116
License
No license is specified in this repository. Add a license file if you intend to define permissions for reuse and redistribution.
