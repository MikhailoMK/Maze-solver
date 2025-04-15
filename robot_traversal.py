import tkinter as tk
from tkinter import messagebox, filedialog
import json
from maze_solver import MazeSolver
from maze_generator import MazeGenerator

class RobotTraversal:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Traversal")
        self.default_rows = 20
        self.default_cols = 20
        self.default_density = 100
        self.rows = self.default_rows
        self.cols = self.default_cols
        self.cell_size = 20
        self.walls = {}
        self.robot_pos = (self.cols // 2, self.rows // 2)
        self.start_pos = self.robot_pos
        self.robot_dir = 'NORTH'
        self.visited = {}
        self.possible_moves = set()
        self.persistent_moves = set()
        self.auto_mode_moves = set()
        self.speed = 150
        self.traversal_path = []
        self.current_step = 0
        self.steps_count = 0
        self.turns_count = 0
        self.is_paused = False
        self.auto_traverse_id = None
        self.in_auto_mode = False
        self.auto_mode_started = False
        self.manual_move_mode = False
        self.density = self.default_density
        self.has_maze = False
        self.offset_x = 0
        self.offset_y = 0
        self.create_widgets()
        self.initialize_game()
        self.create_border_walls()

    def create_border_walls(self):
        self.walls = {k: v for k, v in self.walls.items() if not self.is_border_wall(k)}
        for x in range(self.cols):
            self.walls[((x, -1), (x, 0))] = True
            self.walls[((x, self.rows-1), (x, self.rows))] = True
        for y in range(self.rows):
            self.walls[((-1, y), (0, y))] = True
            self.walls[((self.cols-1, y), (self.cols, y))] = True

    def is_border_wall(self, wall):
        (x1, y1), (x2, y2) = wall
        return (x1 == x2 and (y1 < 0 or y2 < 0 or y1 >= self.rows or y2 >= self.rows)) or \
               (y1 == y2 and (x1 < 0 or x2 < 0 or x1 >= self.cols or x2 >= self.cols))

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.main_frame, width=150)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.button_panel = tk.Frame(self.right_frame)
        self.button_panel.pack(fill=tk.X, padx=5, pady=5)

        buttons = [
            ("Лабиринт", self.generate_maze),
            ("Очистить", self.clear_field),
            ("Сброс", self.reset_field),
            ("Сохранить", self.save_maze),
            ("Загрузить", self.load_maze),
            ("Влево", lambda: self.turn_robot("LEFT")),
            ("Вправо", lambda: self.turn_robot("RIGHT")),
            ("Шаг", self.manual_move),
            ("Авто", self.toggle_auto_traverse),
            ("Пауза", self.toggle_pause),
            ("Быстрее", self.speed_up),
            ("Медленнее", self.slow_down),
        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(self.button_panel, text=text, command=command)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")

        self.settings_panel = tk.Frame(self.right_frame)
        self.settings_panel.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.settings_panel, text="Верт:").grid(row=0, column=0, sticky=tk.W)
        self.rows_entry = tk.Entry(self.settings_panel, width=5)
        self.rows_entry.grid(row=0, column=1, sticky=tk.W)
        self.rows_entry.insert(0, str(self.default_rows))

        tk.Label(self.settings_panel, text="Гор:").grid(row=1, column=0, sticky=tk.W)
        self.cols_entry = tk.Entry(self.settings_panel, width=5)
        self.cols_entry.grid(row=1, column=1, sticky=tk.W)
        self.cols_entry.insert(0, str(self.default_cols))

        tk.Label(self.settings_panel, text="Плотность (%):").grid(row=2, column=0, sticky=tk.W)
        self.density_entry = tk.Entry(self.settings_panel, width=5)
        self.density_entry.grid(row=2, column=1, sticky=tk.W)
        self.density_entry.insert(0, str(self.default_density))

        self.apply_btn = tk.Button(self.settings_panel, text="Применить", command=self.apply_settings)
        self.apply_btn.grid(row=3, column=0, columnspan=2, pady=5)

        self.status_panel = tk.Frame(self.right_frame)
        self.status_panel.pack(fill=tk.X, padx=5, pady=5)

        self.status_row1 = tk.Frame(self.status_panel)
        self.status_row1.pack(fill=tk.X)
        self.steps_label = tk.Label(self.status_row1, text="Шаги: 0")
        self.steps_label.pack(side=tk.LEFT, padx=5)
        self.turns_label = tk.Label(self.status_row1, text="Повороты: 0")
        self.turns_label.pack(side=tk.LEFT, padx=5)

        self.status_row2 = tk.Frame(self.status_panel)
        self.status_row2.pack(fill=tk.X)
        self.speed_label = tk.Label(self.status_row2, text=f"Скорость: {self.speed}")
        self.speed_label.pack(side=tk.LEFT, padx=5)

        self.status_row3 = tk.Frame(self.status_panel)
        self.status_row3.pack(fill=tk.X)
        self.paths_label = tk.Label(self.status_row3, text="Пути: 0")
        self.paths_label.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.left_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.toggle_wall)
        self.canvas.bind("<Button-3>", self.move_robot_to_cell)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        canvas_width = event.width
        canvas_height = event.height
        if canvas_width > 10 and canvas_height > 10:
            self.cell_size = min(
                (canvas_width - 40) // max(1, self.cols),
                (canvas_height - 40) // max(1, self.rows)
            )
            self.cell_size = max(5, self.cell_size)
            self.draw_field()

    def apply_settings(self):
        try:
            new_rows = int(self.rows_entry.get())
            new_cols = int(self.cols_entry.get())
            new_density = int(self.density_entry.get())
            
            if new_rows < 1 or new_cols < 1 or new_density < 0 or new_density > 100:
                raise ValueError
            
            old_rows = self.rows
            old_cols = self.cols
            self.rows = new_rows
            self.cols = new_cols
            self.density = new_density
            
            row_diff = new_rows - old_rows
            col_diff = new_cols - old_cols
            row_shift = row_diff // 2
            col_shift = col_diff // 2
            
            rx, ry = self.robot_pos
            new_rx = rx + col_shift
            new_ry = ry + row_shift
            if new_rx < 0 or new_rx >= self.cols or new_ry < 0 or new_ry >= self.rows:
                new_rx = self.cols // 2
                new_ry = self.rows // 2
            self.robot_pos = (new_rx, new_ry)
            self.start_pos = self.robot_pos
            
            new_walls = {}
            for wall, state in self.walls.items():
                if self.is_border_wall(wall):
                    continue
                (x1, y1), (x2, y2) = wall
                new_x1 = x1 + col_shift
                new_y1 = y1 + row_shift
                new_x2 = x2 + col_shift
                new_y2 = y2 + row_shift
                if (0 <= new_x1 < self.cols and 0 <= new_y1 < self.rows and
                    0 <= new_x2 < self.cols and 0 <= new_y2 < self.rows):
                    new_walls[((new_x1, new_y1), (new_x2, new_y2))] = state
            self.walls = new_walls
            self.create_border_walls()
            
            self.visited = {self.robot_pos: 1}
            self.possible_moves = set()
            self.persistent_moves = set()
            self.auto_mode_moves = set()
            self.steps_count = 0
            self.turns_count = 0
            self.has_maze = True if new_walls else False
            self.auto_mode_started = False
            self.update_status()
            self.update_possible_moves()
            self.draw_field()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения\n(Верт. и Гор. - целые > 0, Плотность 0-100)")
            self.rows_entry.delete(0, tk.END)
            self.rows_entry.insert(0, str(self.rows))
            self.cols_entry.delete(0, tk.END)
            self.cols_entry.insert(0, str(self.cols))
            self.density_entry.delete(0, tk.END)
            self.density_entry.insert(0, str(self.density))

    def initialize_game(self):
        self.visited[self.robot_pos] = 1
        self.update_possible_moves()
        self.draw_field()

    def get_exits_count(self, x, y):
        exits = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
                if not self.walls.get(wall_key, False):
                    exits += 1
        return exits

    def draw_field(self):
        self.canvas.delete("all")
        
        field_width = self.cols * self.cell_size
        field_height = self.rows * self.cell_size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.offset_x = (canvas_width - field_width) // 2 if canvas_width > field_width else 0
        self.offset_y = (canvas_height - field_height) // 2 if canvas_height > field_height else 0
        
        for y in range(self.rows):
            for x in range(self.cols):
                visit_count = self.visited.get((x, y), 0)
                
                if (x, y) == self.robot_pos:
                    base_color = "blue"
                elif self.auto_mode_started and visit_count > 0:
                    base_color = "#00FF00" if visit_count == 1 else \
                                "#FFA500" if visit_count == 2 else \
                                "#800080" if visit_count == 3 else \
                                "#FF0000"
                elif (x, y) in self.persistent_moves:
                    base_color = "yellow"
                else:
                    base_color = "white"
                    
                self.canvas.create_rectangle(
                    self.offset_x + x * self.cell_size, self.offset_y + y * self.cell_size,
                    self.offset_x + (x + 1) * self.cell_size, self.offset_y + (y + 1) * self.cell_size,
                    fill=base_color, outline="gray"
                )
                
                if self.auto_mode_started and visit_count > 0:
                    self.canvas.create_text(
                        self.offset_x + x * self.cell_size + self.cell_size//2,
                        self.offset_y + y * self.cell_size + self.cell_size//2,
                        text=str(visit_count),
                        fill="black" if visit_count <= 2 else "white"
                    )
        
        for (x1, y1), (x2, y2) in self.walls:
            if self.walls[((x1, y1), (x2, y2))]:
                if x1 == x2:
                    y = max(y1, y2)
                    self.canvas.create_line(
                        self.offset_x + x1 * self.cell_size, self.offset_y + y * self.cell_size,
                        self.offset_x + (x1 + 1) * self.cell_size, self.offset_y + y * self.cell_size,
                        width=3, fill="black"
                    )
                else:
                    x = max(x1, x2)
                    self.canvas.create_line(
                        self.offset_x + x * self.cell_size, self.offset_y + y1 * self.cell_size,
                        self.offset_x + x * self.cell_size, self.offset_y + (y1 + 1) * self.cell_size,
                        width=3, fill="black"
                    )
        
        self.draw_robot()
        self.update_status()

    def draw_robot(self):
        x, y = self.robot_pos
        size = self.cell_size
        half = size // 2
        quarter = size // 4
        
        directions = {
            'NORTH': [
                self.offset_x + x * size + half, self.offset_y + y * size + quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + 3 * quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + 3 * quarter
            ],
            'EAST': [
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + half,
                self.offset_x + x * size + quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + 3 * quarter
            ],
            'SOUTH': [
                self.offset_x + x * size + half, self.offset_y + y * size + 3 * quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + quarter
            ],
            'WEST': [
                self.offset_x + x * size + quarter, self.offset_y + y * size + half,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + 3 * quarter
            ]
        }
        
        self.canvas.create_polygon(
            directions[self.robot_dir], 
            fill="white", 
            outline="black"
        )

    def update_possible_moves(self):
        x, y = self.robot_pos
        new_moves = set()
        
        for dx, dy, direction in [(-1, 0, 'WEST'), (1, 0, 'EAST'), (0, -1, 'NORTH'), (0, 1, 'SOUTH')]:
            nx, ny = x + dx, y + dy
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            
            if (0 <= nx < self.cols and 0 <= ny < self.rows and 
                not self.walls.get(wall_key, False)):
                new_moves.add((nx, ny))
        
        self.possible_moves = new_moves
        self.persistent_moves.update(new_moves)
        
        if self.auto_mode_started:
            self.persistent_moves = {pos for pos in self.persistent_moves if self.visited.get(pos, 0) == 0}
        
        unvisited_yellow = len(self.persistent_moves)
        self.paths_label.config(text=f"Пути: {unvisited_yellow}")

    def update_status(self):
        self.steps_label.config(text=f"Шаги: {self.steps_count}")
        self.turns_label.config(text=f"Повороты: {self.turns_count}")
        self.speed_label.config(text=f"Скорость: {self.speed}")
        unvisited_yellow = len(self.persistent_moves)
        self.paths_label.config(text=f"Пути: {unvisited_yellow}")

    def generate_maze(self):
        self.clear_field()
        try:
            density = int(self.density_entry.get()) / 100
        except ValueError:
            density = self.density / 100
        
        density = max(0, min(1, density))
        
        generator = MazeGenerator(self.rows, self.cols, density)
        generator.generate_maze_kruskal()
        self.walls = generator.get_walls()
        self.create_border_walls()
        self.has_maze = True
        self.update_possible_moves()
        self.draw_field()

    def clear_field(self):
        self.walls = {}
        self.create_border_walls()
        self.visited = {self.robot_pos: 1}
        self.possible_moves = set()
        self.persistent_moves = set()
        self.auto_mode_moves = set()
        self.steps_count = 0
        self.turns_count = 0
        self.has_maze = False
        self.auto_mode_started = False
        self.update_status()
        self.update_possible_moves()
        self.draw_field()

    def reset_field(self):
        self.clear_field()
        self.robot_pos = (self.cols // 2, self.rows // 2)
        self.start_pos = self.robot_pos
        self.robot_dir = 'NORTH'
        self.visited = {self.robot_pos: 1}
        if self.auto_traverse_id:
            self.root.after_cancel(self.auto_traverse_id)
            self.auto_traverse_id = None
        self.traversal_path = []
        self.current_step = 0
        self.is_paused = False
        self.in_auto_mode = False
        self.auto_mode_started = False
        self.update_status()
        self.update_possible_moves()
        self.draw_field()

    def toggle_wall(self, event):
        x = int((event.x - self.offset_x) // self.cell_size)
        y = int((event.y - self.offset_y) // self.cell_size)
        
        rel_x = ((event.x - self.offset_x) % self.cell_size) / self.cell_size
        rel_y = ((event.y - self.offset_y) % self.cell_size) / self.cell_size
        
        if rel_x < 0.2 and x > 0:
            wall_key = ((x-1, y), (x, y))
        elif rel_x > 0.8 and x < self.cols - 1:
            wall_key = ((x, y), (x+1, y))
        elif rel_y < 0.2 and y > 0:
            wall_key = ((x, y-1), (x, y))
        elif rel_y > 0.8 and y < self.rows - 1:
            wall_key = ((x, y), (x, y+1))
        else:
            return
        
        self.walls[wall_key] = not self.walls.get(wall_key, False)
        self.update_possible_moves()
        self.draw_field()

    def move_robot_to_cell(self, event):
        x = int((event.x - self.offset_x) // self.cell_size)
        y = int((event.y - self.offset_y) // self.cell_size)
        
        if 0 <= x < self.cols and 0 <= y < self.rows:
            path = self.find_path(self.robot_pos, (x, y))
            if path:
                self.manual_move_mode = True
                self.robot_pos = (x, y)
                self.visited[(x, y)] = self.visited.get((x, y), 0) + 1
                self.steps_count += len(path) - 1
                self.update_possible_moves()
                self.draw_field()
                self.manual_move_mode = False
            else:
                messagebox.showinfo("Ошибка", "Невозможно переместить робота - путь заблокирован стенами")

    def find_path(self, start, end):
        queue = [(start, [start])]
        visited = set()
        
        while queue:
            (x, y), path = queue.pop(0)
            if (x, y) == end:
                return path
                
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
                    if not self.walls.get(wall_key, False) and (nx, ny) not in visited:
                        queue.append(((nx, ny), path + [(nx, ny)]))
        return None

    def turn_robot(self, direction):
        directions = {
            'NORTH': {'LEFT': 'WEST', 'RIGHT': 'EAST'},
            'EAST': {'LEFT': 'NORTH', 'RIGHT': 'SOUTH'},
            'SOUTH': {'LEFT': 'EAST', 'RIGHT': 'WEST'},
            'WEST': {'LEFT': 'SOUTH', 'RIGHT': 'NORTH'}
        }
        self.robot_dir = directions[self.robot_dir][direction]
        self.turns_count += 1
        self.update_status()
        self.update_possible_moves()
        self.draw_field()

    def manual_move(self):
        x, y = self.robot_pos
        direction_offsets = {
            'NORTH': (0, -1),
            'EAST': (1, 0),
            'SOUTH': (0, 1),
            'WEST': (-1, 0)
        }
        dx, dy = direction_offsets[self.robot_dir]
        new_x, new_y = x + dx, y + dy

        wall_key = ((x, y), (new_x, new_y)) if (x, y) < (new_x, new_y) else ((new_x, new_y), (x, y))
        
        if (0 <= new_x < self.cols and 0 <= new_y < self.rows and 
            not self.walls.get(wall_key, False)):
            self.robot_pos = (new_x, new_y)
            self.visited[(new_x, new_y)] = self.visited.get((new_x, new_y), 0) + 1
            self.steps_count += 1
            self.update_possible_moves()
        else:
            messagebox.showinfo("Препятствие", "Невозможно двигаться вперёд. Обнаружена стена.")

        self.update_status()
        self.draw_field()

    def toggle_auto_traverse(self):
        if not self.in_auto_mode:
            self.start_auto_traverse()
        elif self.is_paused:
            self.resume_auto_traverse()
        else:
            self.pause_auto_traverse()

    def start_auto_traverse(self):
        self.in_auto_mode = True
        self.auto_mode_started = True
        self.traversal_path = []
        self.current_step = 0
        self.is_paused = False
        self.auto_traverse_step()

    def auto_traverse_step(self):
        if not self.in_auto_mode:
            return

        if self.is_paused:
            return

        solver = MazeSolver(self.walls, self.rows, self.cols, self.robot_pos, self.robot_dir, self.visited, self.start_pos)
        next_step = solver.get_next_step()
        
        if not next_step:
            self.in_auto_mode = False
            messagebox.showinfo("Завершено", "Путешествие завершено.")
            return
        
        x, y, direction = next_step
        
        if direction != self.robot_dir:
            self.robot_dir = direction
            self.turns_count += 1
        else:
            self.robot_pos = (x, y)
            self.visited[(x, y)] = self.visited.get((x, y), 0) + 1
            self.steps_count += 1
            self.auto_mode_moves.add((x, y))
        
        self.update_status()
        self.update_possible_moves()
        self.draw_field()
        self.auto_traverse_id = self.root.after(self.speed, self.auto_traverse_step)

    def toggle_pause(self):
        if self.is_paused:
            self.resume_auto_traverse()
        else:
            self.pause_auto_traverse()

    def pause_auto_traverse(self):
        if self.auto_traverse_id:
            self.is_paused = True
            self.root.after_cancel(self.auto_traverse_id)
            self.auto_traverse_id = None

    def resume_auto_traverse(self):
        if self.is_paused:
            self.is_paused = False
            self.auto_traverse_step()

    def speed_up(self):
        self.speed = max(50, self.speed - 50)
        self.speed_label.config(text=f"Скорость: {self.speed}")

    def slow_down(self):
        self.speed = min(300, self.speed + 50)
        self.speed_label.config(text=f"Скорость: {self.speed}")

    def save_maze(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            data = {
                "rows": self.rows,
                "cols": self.cols,
                "walls": [list(pair) for pair in self.walls.items()],
                "robot_pos": self.robot_pos,
                "start_pos": self.start_pos,
                "robot_dir": self.robot_dir,
                "visited": list(self.visited.items()),
                "steps": self.steps_count,
                "turns": self.turns_count,
                "persistent_moves": list(self.persistent_moves),
                "density": self.density
            }
            with open(filename, "w") as f:
                json.dump(data, f)

    def load_maze(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                self.rows = data["rows"]
                self.cols = data["cols"]
                self.walls = {tuple(tuple(p) for p in k): v for k, v in data["walls"]}
                self.robot_pos = tuple(data["robot_pos"])
                self.start_pos = tuple(data["start_pos"])
                self.robot_dir = data["robot_dir"]
                self.visited = dict(tuple(item) for item in data.get("visited", []))
                self.steps_count = data.get("steps", 0)
                self.turns_count = data.get("turns", 0)
                self.persistent_moves = set(tuple(item) for item in data.get("persistent_moves", []))
                self.density = data.get("density", self.default_density)
                
                self.rows_entry.delete(0, tk.END)
                self.rows_entry.insert(0, str(self.rows))
                self.cols_entry.delete(0, tk.END)
                self.cols_entry.insert(0, str(self.cols))
                self.density_entry.delete(0, tk.END)
                self.density_entry.insert(0, str(self.density))
                
                self.has_maze = True
                self.auto_mode_started = False
                self.update_possible_moves()
                self.update_status()
                self.draw_field()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = RobotTraversal(root)
    root.mainloop()